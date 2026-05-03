import http.server
import socket
import socketserver
import threading
from pathlib import Path

import pytest
from PIL import Image, ImageStat
from playwright.sync_api import sync_playwright


ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "test-artifacts"


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        pass


@pytest.fixture(scope="session")
def server_url():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]

    handler = lambda *args, **kwargs: QuietHandler(*args, directory=str(ROOT), **kwargs)
    with socketserver.TCPServer(("127.0.0.1", port), handler) as httpd:
        thread = threading.Thread(target=httpd.serve_forever, daemon=True)
        thread.start()
        yield f"http://127.0.0.1:{port}"
        httpd.shutdown()


@pytest.fixture(scope="session")
def chromium():
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        yield browser
        browser.close()


@pytest.fixture()
def page(chromium, server_url):
    errors = []
    page = chromium.new_page(viewport={"width": 1365, "height": 850}, device_scale_factor=1)
    page.on("console", lambda msg: errors.append(msg.text) if msg.type == "error" else None)
    page.goto(server_url, wait_until="domcontentloaded")
    page.wait_for_function("() => window.ol && document.querySelector('.ol-viewport')", timeout=15_000)
    yield page, errors
    page.close()


def screenshot_is_visually_nonblank(path: Path) -> bool:
    image = Image.open(path).convert("RGB")
    stat = ImageStat.Stat(image)
    extrema = image.getextrema()
    has_contrast = max(channel[1] - channel[0] for channel in extrema) > 35
    mean = sum(stat.mean) / 3
    return has_contrast and 15 < mean < 245


def test_app_boots_without_google_maps(page):
    page, errors = page

    assert page.title() == "SolarSketch - Roof Panel Planner"
    assert page.locator("#map .ol-viewport").count() == 1
    assert page.locator("script[src*='maps.googleapis']").count() == 0
    assert page.evaluate("() => typeof google === 'undefined'")
    assert not [error for error in errors if "ReferenceError" in error or "TypeError" in error]


def test_panel_layout_engine_is_deterministic(page):
    page, _ = page

    result = page.evaluate(
        """() => {
            const polygon = [{x:0,y:0},{x:6,y:0},{x:6,y:4},{x:0,y:4}];
            const first = computePanelLayoutInPolygon(polygon, 1.15, 1.8, 0.05, true, 0);
            const second = computePanelLayoutInPolygon(polygon, 1.15, 1.8, 0.05, true, 0);
            return {
              firstCount: first.count,
              secondCount: second.count,
              placements: first.placements.length,
              everyPanelHasFourCorners: first.placements.every(panel => panel.corners.length === 4)
            };
        }"""
    )

    assert result["firstCount"] > 0
    assert result["firstCount"] == result["secondCount"]
    assert result["placements"] == result["firstCount"]
    assert result["everyPanelHasFourCorners"]


def test_programmatic_zone_updates_stats_and_panel_overlays(page):
    page, _ = page

    result = page.evaluate(
        """() => {
            const center = map.getView().getCenter();
            const meters = 111319.49079327358;
            const lonLat = ol.proj.toLonLat(center);
            const dx = 0.00009;
            const dy = 0.00006;
            const ringLonLat = [
              [lonLat[0] - dx, lonLat[1] - dy],
              [lonLat[0] + dx, lonLat[1] - dy],
              [lonLat[0] + dx, lonLat[1] + dy],
              [lonLat[0] - dx, lonLat[1] + dy],
              [lonLat[0] - dx, lonLat[1] - dy]
            ];
            const ring = ringLonLat.map(coord => ol.proj.fromLonLat(coord));
            const feature = new ol.Feature(new ol.geom.Polygon([ring]));
            zoneSource.addFeature(feature);
            createZoneFromFeature(feature);
            updateStats();
            return {
              zones: zones.length,
              panels: panelSource.getFeatures().length,
              statPanels: Number(document.getElementById('stat-panels').textContent),
              area: zones[0].area
            };
        }"""
    )

    assert result["zones"] == 1
    assert result["panels"] > 0
    assert result["statPanels"] == result["panels"]
    assert result["area"] > 0


def test_osm_layer_screenshot_is_not_blank(page):
    page, _ = page

    page.locator("#imagery-layer").select_option("osm")
    page.wait_for_function(
        "() => [...document.querySelectorAll('.ol-layer canvas')].some(canvas => canvas.width > 0 && canvas.height > 0)",
        timeout=15_000,
    )

    ARTIFACTS.mkdir(exist_ok=True)
    screenshot = ARTIFACTS / "osm-layer-smoke.png"
    page.screenshot(path=str(screenshot), full_page=True)

    assert screenshot_is_visually_nonblank(screenshot)


def test_screenshot_after_zone_creation(page):
    page, _ = page

    page.evaluate(
        """() => {
            const center = map.getView().getCenter();
            const lonLat = ol.proj.toLonLat(center);
            const ring = [
              [lonLat[0] - 0.00008, lonLat[1] - 0.00005],
              [lonLat[0] + 0.00008, lonLat[1] - 0.00005],
              [lonLat[0] + 0.00008, lonLat[1] + 0.00005],
              [lonLat[0] - 0.00008, lonLat[1] + 0.00005],
              [lonLat[0] - 0.00008, lonLat[1] - 0.00005]
            ].map(coord => ol.proj.fromLonLat(coord));
            const feature = new ol.Feature(new ol.geom.Polygon([ring]));
            zoneSource.addFeature(feature);
            createZoneFromFeature(feature);
            updateStats();
        }"""
    )

    ARTIFACTS.mkdir(exist_ok=True)
    screenshot = ARTIFACTS / "zone-and-panels-smoke.png"
    page.screenshot(path=str(screenshot), full_page=True)

    assert screenshot.exists()
    assert screenshot_is_visually_nonblank(screenshot)
