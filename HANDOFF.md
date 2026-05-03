# HANDOFF

## Project

Solar Roof Planer / SolarSketch

Static single-page app for drawing roof zones on aerial imagery and estimating solar panel fit in real time. The app runs as plain HTML/CSS/JavaScript with no build step.

## Current state

The current working app is `index.html`.

The OpenLayers migration is complete. The app uses OpenLayers instead of Google Maps and no longer requires a Google Maps API key. The migration plan has been executed and removed from the active project files.

It supports:

- DGU orthophoto WMS, Esri World Imagery, and OpenStreetMap base layers
- OpenLayers polygon drawing
- select/edit mode with draggable polygon vertices
- erase mode for clicked zones
- live area and panel-fit recalculation
- visual panel overlays as OpenLayers vector polygons
- independent per-zone panel width, height, wattage, Vmp, spacing, and angle
- global maximum string Vmp setting with per-zone string count recommendations
- address search through Nominatim plus direct coordinate search
- mobile layout with a hideable slide-over sidebar
- text report export with per-zone settings and string guidance

## Files

- `index.html` - whole application, including styles and scripts
- `README.md` - end-user setup and deploy notes
- `HANDOFF.md` - project state and technical context
- `agent.md` - instructions for future coding agents
- `requirements.txt`, `pytest.ini`, `tests/test_app_browser.py` - Python/Playwright regression baseline

## Architecture summary

The app is intentionally single-file for now.

### UI layers

- Header: branding, address search, export, sidebar toggle
- Sidebar: tools, imagery selector, panel settings, stats, zone list
- Main view: OpenLayers map, instruction toast, source badge, zoom controls

### Map model

Zones are stored in real map coordinates, not screen pixels:

```js
{
  id,
  name,
  color,
  coordinates: [[lon, lat], ...],
  area,
  panelCount,
  panels,
  settings: {
    panelWidth,
    panelHeight,
    panelWatts,
    panelSpacing,
    panelAngle,
    panelVmp
  },
  feature
}
```

`feature` is the OpenLayers polygon feature. `coordinates` is the serializable geometry source for panel calculations and future persistence. New zones copy `defaultZoneSettings`; selecting a zone loads its settings into the sidebar, and edits update only that selected zone. `maxStringVmp` is global and defaults to `800`.

### Important functions

- `initMap()` - creates OpenLayers map, base layers, vector layers, and click handlers
- `setBaseLayer(key)` - switches DGU, Esri, or OSM imagery
- `setTool(tool)` - central tool switch for draw, select/edit, pan, erase
- `createZoneFromFeature(feature)` - creates a new zone from an OpenLayers draw result
- `updateZoneFromFeature(feature)` - synchronizes lon/lat coordinates from a polygon feature
- `updateStats()` - recalculates area, panel layout, stats, zone list, and panel overlays
- `syncInputsFromSelection()` - loads selected-zone settings or default settings into the sidebar inputs
- `onSettingsInput()` - writes sidebar panel inputs to the selected zone, or to defaults when no zone is selected
- `getStringRecommendation(zone)` - calculates recommended string count from panel count, panel Vmp, and global max string Vmp
- `computePanelLayoutInPolygon(...)` - shared panel-fit engine in local meter coordinates
- `renderPanels(zone, placements, frame)` - renders panel overlays as vector polygons
- `searchAddress()` - Nominatim or coordinate search
- `exportReport()` - text planning report export
- `notifyMapResize()` - keeps OpenLayers sized after sidebar changes

## Panel-fit algorithm

The fit logic:

1. Converts zone lon/lat points into a local meter frame around the zone centroid.
2. Rotates the polygon by that zone's configured panel angle.
3. Tries portrait and landscape panel orientations.
4. Sweeps a deterministic placement grid with several offsets.
5. Accepts a panel when its corners and center are inside the polygon.
6. Converts accepted panel rectangles back to lon/lat and then map projection coordinates.

This is still a heuristic, not a full packing optimizer.

## Known limitations

- DGU WMS availability, projection support, and production terms should be verified before public use.
- Nominatim is appropriate for light development/testing, not heavy production geocoding.
- Panel fitting is approximate and does not handle setbacks, obstacles, roof pitch, fire paths, or manual panel movement.
- String recommendations are planning aids only and do not validate cold-weather Voc, inverter MPPT/current limits, optimizer rules, or local electrical code.
- Polygon self-intersections are not validated.
- No persistence layer exists yet. Reloading the page loses zones.
- Export is still a plain text report.

## Local run

Recommended:

```bash
python -m http.server 8000
```

Then open `http://localhost:8000`.

## Automated tests

The project now has a small Python/Playwright test harness:

```bash
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
.\.venv\Scripts\python -m playwright install chromium
.\.venv\Scripts\python -m pytest
```

The current baseline contains 8 tests. They cover:

- app boot without Google Maps
- panel layout determinism in the browser context
- programmatic zone creation, stats, and panel overlays
- copied per-zone default settings
- independent selected-zone panel settings and input reloading
- string recommendations from panel Vmp and global max string Vmp
- screenshot nonblank scan for OpenStreetMap
- screenshot nonblank scan after zone/panel rendering

Screenshot artifacts are written to `test-artifacts/` and intentionally ignored by Git.

Run the test suite after every code or behavior change before committing. If the checked-in `.venv` fails with a missing `Python310` path, recreate it with the setup commands above before running tests.

## Manual regression checklist

Run through these before handoff when possible:

- App loads without any Google Maps API key.
- No Google Maps script is requested.
- DGU, Esri, and OSM layer selector changes the visible source.
- Draw a roof polygon and finish it with double-click.
- Select the zone and drag vertices.
- Confirm area, stats, zone list, and panels update after editing.
- Change panel width, height, spacing, wattage, Vmp, and angle.
- Draw two zones, set different angles/settings, and confirm selection reloads each zone's values.
- Change global max string Vmp and confirm all zone string recommendations update.
- Confirm panel count remains stable across zoom/pan/resize.
- Delete a zone through erase mode and through the zone list.
- Search `Zadar, Croatia`.
- Search coordinates such as `44.1194, 15.2314`.
- Export report.
- Desktop sidebar hide/show works and map resizes.
- Mobile slide-over menu opens/closes and returns focus to the map.

## Good next tasks

- Save/load project JSON.
- Obstacle and exclusion zone support.
- Better snapping to roof edges.
- Export to PDF/PNG.
- Clearer touch handles for phone editing.
- Split `index.html` into `styles.css` and `app.js` once the implementation grows again.
