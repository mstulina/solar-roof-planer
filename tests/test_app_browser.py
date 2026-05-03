import http.server
import socket
import socketserver
import threading
from urllib.parse import parse_qs, urlparse
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


def test_cadastral_layers_are_configured_and_toggleable(page):
    page, _ = page

    result = page.evaluate(
        """() => {
            const parcelSource = cadastralLayers.parcels.getSource();
            const zoningSource = cadastralLayers.zoning.getSource();
            document.getElementById('parcel-layer-toggle').checked = false;
            document.getElementById('zoning-layer-toggle').checked = true;
            setCadastralLayerVisibility();
            return {
              parcelUrl: parcelSource.getUrl(),
              parcelLayer: parcelSource.getParams().LAYERS,
              zoningLayer: zoningSource.getParams().LAYERS,
              parcelVisible: cadastralLayers.parcels.getVisible(),
              zoningVisible: cadastralLayers.zoning.getVisible()
            };
        }"""
    )

    assert result["parcelUrl"] == "https://api.uredjenazemlja.hr/services/inspire/cp_wms/wms"
    assert result["parcelLayer"] == "CP.CadastralParcel"
    assert result["zoningLayer"] == "CP.CadastralZoning"
    assert result["parcelVisible"] is False
    assert result["zoningVisible"] is True


def test_search_is_limited_to_croatia(page):
    page, _ = page
    requested_urls = []

    def handle_search(route):
        requested_urls.append(route.request.url)
        route.fulfill(
            status=200,
            content_type="application/json",
            body='[{"lon":"15.2314","lat":"44.1194","display_name":"Zadar, Croatia"}]',
        )

    page.route("https://nominatim.openstreetmap.org/search?**", handle_search)
    page.route("https://api.uredjenazemlja.hr/services/inspire/cp/wfs?**", lambda route: route.fulfill(status=200, body='{"features":[]}'))
    page.locator("#address-input").fill("Zadar")
    page.locator("button", has_text="Go").click()
    page.wait_for_function("() => document.getElementById('instructions').textContent.includes('Zadar')")

    parsed = parse_qs(urlparse(requested_urls[-1]).query)
    assert parsed["countrycodes"] == ["hr"]
    assert parsed["bounded"] == ["1"]
    assert "13.202" in parsed["viewbox"][0]

    page.locator("#address-input").fill("48.8566, 2.3522")
    page.locator("button", has_text="Go").click()
    assert "limited to Croatia" in page.locator("#instructions").text_content()


def test_mock_wfs_selects_parcel_and_enforces_zone_containment(page):
    page, _ = page
    parcel_geojson = """{
      "type": "FeatureCollection",
      "features": [{
        "type": "Feature",
        "id": "parcel-1",
        "properties": {"localId": "KO Zadar 123/4"},
        "geometry": {
          "type": "Polygon",
          "coordinates": [[[15.2310,44.1190],[15.2320,44.1190],[15.2320,44.1200],[15.2310,44.1200],[15.2310,44.1190]]]
        }
      }]
    }"""

    page.route(
        "https://api.uredjenazemlja.hr/services/inspire/cp/wfs?**",
        lambda route: route.fulfill(status=200, content_type="application/json", body=parcel_geojson),
    )

    result = page.evaluate(
        """async () => {
            const coordinate = ol.proj.fromLonLat([15.2314, 44.1194]);
            map.dispatchEvent({
              type: 'singleclick',
              coordinate,
              pixel: map.getPixelFromCoordinate(coordinate)
            });
            await new Promise(resolve => setTimeout(resolve, 250));

            function addZone(coords) {
              const ring = coords.map(coord => ol.proj.fromLonLat(coord));
              ring.push(ring[0]);
              const feature = new ol.Feature(new ol.geom.Polygon([ring]));
              zoneSource.addFeature(feature);
              createZoneFromFeature(feature);
              return zones[zones.length - 1];
            }

            const inside = addZone([
              [15.2312,44.1192],
              [15.2314,44.1192],
              [15.2314,44.1194],
              [15.2312,44.1194]
            ]);
            const outside = addZone([
              [15.2318,44.1192],
              [15.2323,44.1192],
              [15.2323,44.1194],
              [15.2318,44.1194]
            ]);
            updateStats();
            exportReport();

            return {
              parcelId: selectedParcel.id,
              parcelFeatures: selectedParcelSource.getFeatures().length,
              insideValid: inside.parcelValid,
              outsideValid: outside.parcelValid,
              instructions: document.getElementById('instructions').textContent,
              status: document.getElementById('selected-plot-status').textContent,
              details: document.getElementById('selected-plot-details').textContent
            };
        }"""
    )

    assert result["parcelId"] == "KO Zadar 123/4"
    assert result["parcelFeatures"] == 1
    assert result["insideValid"] is True
    assert result["outsideValid"] is False
    assert "Export blocked" in result["instructions"]
    assert "KO Zadar 123/4" in result["status"]
    assert "Approx. area" in result["details"]
    assert "Center:" in result["details"]


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
              area: zones[0].area,
              settings: zones[0].settings
            };
        }"""
    )

    assert result["zones"] == 1
    assert result["panels"] > 0
    assert result["statPanels"] == result["panels"]
    assert result["area"] > 0
    assert result["settings"]["panelAngle"] == 0
    assert result["settings"]["panelVmp"] == 42


def test_zone_settings_are_independent_and_loaded_on_selection(page):
    page, _ = page

    result = page.evaluate(
        """() => {
            function addZone(offsetLon) {
              const center = map.getView().getCenter();
              const lonLat = ol.proj.toLonLat(center);
              const dx = 0.00014;
              const dy = 0.00004;
              const ring = [
                [lonLat[0] + offsetLon - dx, lonLat[1] - dy],
                [lonLat[0] + offsetLon + dx, lonLat[1] - dy],
                [lonLat[0] + offsetLon + dx, lonLat[1] + dy],
                [lonLat[0] + offsetLon - dx, lonLat[1] + dy],
                [lonLat[0] + offsetLon - dx, lonLat[1] - dy]
              ].map(coord => ol.proj.fromLonLat(coord));
              const feature = new ol.Feature(new ol.geom.Polygon([ring]));
              zoneSource.addFeature(feature);
              createZoneFromFeature(feature);
              return zones[zones.length - 1];
            }

            const first = addZone(-0.00025);
            document.getElementById('panel-angle').value = '0';
            document.getElementById('panel-watts').value = '400';
            document.getElementById('panel-vmp').value = '40';
            onSettingsInput();

            const second = addZone(0.00025);
            document.getElementById('panel-angle').value = '45';
            document.getElementById('panel-watts').value = '500';
            document.getElementById('panel-vmp').value = '50';
            onSettingsInput();

            const firstCountBefore = first.panelCount;
            const secondCountBefore = second.panelCount;
            selectZone(first.id);
            const loadedFirst = {
              angle: Number(document.getElementById('panel-angle').value),
              watts: Number(document.getElementById('panel-watts').value),
              vmp: Number(document.getElementById('panel-vmp').value)
            };
            selectZone(second.id);
            const loadedSecond = {
              angle: Number(document.getElementById('panel-angle').value),
              watts: Number(document.getElementById('panel-watts').value),
              vmp: Number(document.getElementById('panel-vmp').value)
            };

            return {
              firstAngle: first.settings.panelAngle,
              secondAngle: second.settings.panelAngle,
              firstCountBefore,
              secondCountBefore,
              loadedFirst,
              loadedSecond,
              kwp: Number(document.getElementById('stat-kwp').textContent)
            };
        }"""
    )

    assert result["firstAngle"] == 0
    assert result["secondAngle"] == 45
    assert result["loadedFirst"] == {"angle": 0, "watts": 400, "vmp": 40}
    assert result["loadedSecond"] == {"angle": 45, "watts": 500, "vmp": 50}
    assert result["firstCountBefore"] > 0
    assert result["secondCountBefore"] > 0
    expected_kwp = (
        result["firstCountBefore"] * 400 + result["secondCountBefore"] * 500
    ) / 1000
    assert abs(result["kwp"] - expected_kwp) < 0.051


def test_string_recommendation_uses_global_voltage_and_panel_vmp(page):
    page, _ = page

    result = page.evaluate(
        """() => {
            const center = map.getView().getCenter();
            const lonLat = ol.proj.toLonLat(center);
            const ring = [
              [lonLat[0] - 0.00012, lonLat[1] - 0.00006],
              [lonLat[0] + 0.00012, lonLat[1] - 0.00006],
              [lonLat[0] + 0.00012, lonLat[1] + 0.00006],
              [lonLat[0] - 0.00012, lonLat[1] + 0.00006],
              [lonLat[0] - 0.00012, lonLat[1] - 0.00006]
            ].map(coord => ol.proj.fromLonLat(coord));
            const feature = new ol.Feature(new ol.geom.Polygon([ring]));
            zoneSource.addFeature(feature);
            createZoneFromFeature(feature);

            document.getElementById('panel-vmp').value = '40';
            onSettingsInput();
            document.getElementById('max-string-vmp').value = '400';
            onStringSettingsInput();

            const recommendation = getStringRecommendation(zones[0]);
            return {
              panels: zones[0].panelCount,
              modulesPerString: recommendation.modulesPerString,
              strings: recommendation.strings,
              label: recommendation.label,
              listText: document.getElementById('zones-list').textContent
            };
        }"""
    )

    assert result["panels"] > 0
    assert result["modulesPerString"] == 10
    assert result["strings"] == -(-result["panels"] // 10)
    assert "up to 10 panels/string" in result["label"]
    assert "up to 10 panels/string" in result["listText"]


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


def test_dgu_layer_screenshot_is_not_blank(page):
    page, _ = page

    page.locator("#imagery-layer").select_option("dgu")
    page.wait_for_timeout(2_500)

    ARTIFACTS.mkdir(exist_ok=True)
    screenshot = ARTIFACTS / "dgu-layer-smoke.png"
    page.locator("#map").screenshot(path=str(screenshot))

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
