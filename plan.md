# OpenLayers Migration Plan

## Goal

Replace the current Google Maps dependency with an OpenLayers-based map engine while keeping the app useful for solar roof planning:

- high-quality roof/aerial imagery,
- accurate drawing/editing of roof zones,
- reliable area and distance measurement,
- panel placement inside roof polygons,
- no Google Drawing Library,
- no Google Maps JavaScript API requirement.

The main target is a static, simple, single-file-friendly implementation that can later be refactored into modules if needed.

---

## Recommended Stack

### Map Engine

Use **OpenLayers**.

Reasons:

- mature open-source mapping library,
- strong support for raster imagery layers: XYZ, WMS, WMTS,
- built-in vector drawing/editing interactions,
- good geometry support,
- works well without a build step via CDN,
- better suited than Leaflet for precise polygon editing and measurement-heavy workflows.

### Imagery Layers

Use multiple imagery sources with fallback support.

Recommended order:

1. **Croatian DGU orthophoto WMS**
   - Best candidate for Croatia/Zadar rooftop planning.
   - Official orthophoto imagery.
   - Better for measurement than generic map tiles.

2. **Esri World Imagery fallback**
   - Useful when DGU layer is unavailable or outside Croatia.
   - Good visual quality, but check terms before production use.

3. **Optional commercial fallback**
   - MapTiler Satellite, Mapbox, or similar.
   - Only if API-key dependency is acceptable.

4. **OpenStreetMap standard layer**
   - Use only as a navigation/base map fallback.
   - It is not satellite imagery and should not be used for roof measurement.

---

## Important Design Decision

Do **not** store roof geometry as screen pixels.

Store zones in real map coordinates and convert only when needed for drawing or panel placement.

Preferred internal model:

```js
const zones = [
  {
    id: 'zone-1',
    name: 'Zone 1',
    color: '#1A3A5C',
    coordinates: [
      [lon, lat],
      [lon, lat],
      [lon, lat]
    ],
    areaM2: 0,
    panelCount: 0,
    panels: []
  }
];
```

Panel placement can use a local meter coordinate system generated from the zone centroid.

---

## Target Architecture

Introduce a small map adapter layer so the rest of the app does not directly depend on OpenLayers internals.

```js
const mapAdapter = {
  initMap,
  setTool,
  searchAddress,
  addZone,
  updateZone,
  deleteZone,
  selectZone,
  renderPanels,
  clearPanels,
  fitToLocation
};
```

This keeps the app simple and avoids mixing UI state, panel logic, and map-library-specific code.

---

## Migration Phases

## Phase 1 — Remove Google Maps Dependency

Remove or disable:

- Google Maps script loading,
- `google.maps.Map`,
- `google.maps.Polygon`,
- `google.maps.Polyline`,
- `google.maps.Marker`,
- `google.maps.Geocoder`,
- `google.maps.geometry.spherical.computeArea`,
- `google.maps.drawing.DrawingManager`,
- all `libraries=drawing,geometry,geocoding` usage.

The app should no longer require a Google API key.

Acceptance criteria:

- app loads without any Google Maps key,
- no Google Maps script is requested,
- no Drawing Library warning appears,
- demo or OpenLayers map is visible.

---

## Phase 2 — Add OpenLayers Map

Add OpenLayers from CDN:

```html
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/ol@latest/ol.css">
<script src="https://cdn.jsdelivr.net/npm/ol@latest/dist/ol.js"></script>
```

Create the map:

```js
const map = new ol.Map({
  target: 'map-container',
  layers: [baseLayer],
  view: new ol.View({
    center: ol.proj.fromLonLat([15.2314, 44.1194]), // Zadar fallback
    zoom: 19
  })
});
```

Acceptance criteria:

- OpenLayers map renders,
- pan and zoom work,
- initial location is reasonable,
- existing sidebar layout remains usable.

---

## Phase 3 — Add Imagery Layers

Create a layer switcher with at least:

- DGU orthophoto WMS,
- Esri World Imagery fallback,
- OpenStreetMap standard map fallback.

Example structure:

```js
const layers = {
  dguOrtho: new ol.layer.Tile({
    source: new ol.source.TileWMS({
      url: 'DGU_WMS_URL_HERE',
      params: {
        LAYERS: 'LAYER_NAME_HERE',
        TILED: true
      },
      serverType: 'geoserver',
      crossOrigin: 'anonymous'
    })
  }),

  osm: new ol.layer.Tile({
    source: new ol.source.OSM()
  }),

  esri: new ol.layer.Tile({
    source: new ol.source.XYZ({
      url: 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
      crossOrigin: 'anonymous'
    })
  })
};
```

Note: confirm the exact DGU WMS endpoint and layer name before final implementation.

Acceptance criteria:

- user can switch imagery layer,
- selected layer remains visible at roof-level zoom,
- no app crash if one layer fails.

---

## Phase 4 — Rebuild Drawing Tools With OpenLayers

Use OpenLayers vector layers:

```js
const zoneSource = new ol.source.Vector();
const zoneLayer = new ol.layer.Vector({ source: zoneSource });

const panelSource = new ol.source.Vector();
const panelLayer = new ol.layer.Vector({ source: panelSource });
```

Use interactions:

- `ol.interaction.Draw` for draw mode,
- `ol.interaction.Select` for select mode,
- `ol.interaction.Modify` for edit/resize mode,
- custom delete action for erase mode.

Tool behavior:

| Tool | Behavior |
|---|---|
| Draw Zone | Draw polygon on map |
| Select | Select existing zone |
| Edit | Move polygon vertices |
| Erase | Delete selected/clicked zone |
| Pan | Disable draw/edit interactions |

Acceptance criteria:

- polygon drawing works,
- double-click or OpenLayers default finish completes polygon,
- zone can be selected,
- zone can be edited by dragging vertices,
- zone can be deleted,
- no invisible zones are created.

---

## Phase 5 — Measurement System

Replace Google geometry with OpenLayers geometry helpers.

Area:

```js
const areaM2 = ol.sphere.getArea(polygonGeometry, {
  projection: map.getView().getProjection()
});
```

Length if needed:

```js
const lengthM = ol.sphere.getLength(lineGeometry, {
  projection: map.getView().getProjection()
});
```

Acceptance criteria:

- zone area updates after drawing,
- zone area updates after editing,
- area is shown in m²,
- result is stable across zoom levels.

---

## Phase 6 — Panel Placement

Panel placement should not depend on screen pixels.

Recommended approach:

1. Get polygon coordinates in lon/lat.
2. Find polygon centroid.
3. Convert every polygon point to local meters relative to centroid.
4. Run panel packing in local meters.
5. Convert placed panel rectangles back to lon/lat or map projection coordinates.
6. Render panels as vector polygons on the panel layer.

Simple local meter conversion:

```js
const EARTH_RADIUS = 6378137;

function lonLatToLocalMeters(lon, lat, originLon, originLat) {
  const x = (lon - originLon) * Math.PI / 180 * EARTH_RADIUS * Math.cos(originLat * Math.PI / 180);
  const y = (lat - originLat) * Math.PI / 180 * EARTH_RADIUS;
  return { x, y };
}

function localMetersToLonLat(x, y, originLon, originLat) {
  const lon = originLon + (x / (EARTH_RADIUS * Math.cos(originLat * Math.PI / 180))) * 180 / Math.PI;
  const lat = originLat + (y / EARTH_RADIUS) * 180 / Math.PI;
  return [lon, lat];
}
```

Panel fitting v1:

- axis-aligned panels,
- configurable panel width/height,
- configurable spacing,
- optional rotation angle later.

Panel fitting v2:

- add zone orientation/azimuth,
- rotate panel grid,
- support landscape/portrait toggle,
- support setbacks from polygon edge.

Acceptance criteria:

- panel count does not change when zooming,
- panel count updates after panel size/spacing change,
- panels remain visually inside the roof zone,
- panel count updates after zone edit.

---

## Phase 7 — Address Search

Replace Google Geocoder.

Simple development option:

- Nominatim search endpoint.

Production-safe options:

- self-hosted Nominatim,
- Photon,
- Pelias,
- MapTiler Geocoding,
- LocationIQ,
- another provider with clear production terms.

Keep geocoding behind one function:

```js
async function searchAddress(query) {
  // returns { lon, lat, label }
}
```

Acceptance criteria:

- searching `Zadar, Croatia` moves the map,
- searching coordinates works,
- failed searches show a friendly message,
- geocoding provider can be swapped later.

---

## Phase 8 — Export Report

Keep the current text export, but update source fields:

- total panels,
- kWp,
- total roof area,
- estimated annual kWh,
- zone list,
- imagery source name,
- warning that imagery and measurement must be checked on site.

Optional later:

- export JSON project file,
- import JSON project file,
- export screenshot/PDF.

Acceptance criteria:

- report export still works,
- no Google-specific wording remains,
- output includes area and panel count per zone.

---

## Phase 9 — Persistence

Add simple local persistence:

```js
localStorage.setItem('solarSketchProject', JSON.stringify(projectState));
```

Save:

- zones,
- panels,
- panel settings,
- map center/zoom,
- selected imagery layer.

Acceptance criteria:

- refresh does not lose project,
- user can clear/reset project,
- saved data is independent of screen size.

---

## Phase 10 — Cleanup And Hardening

Remove old Google UI:

- `Use Real Map` Google API key dialog,
- Google-specific mode badge,
- Google error messages.

Replace with:

- imagery layer selector,
- current source badge,
- loading/error state for layers.

Add guards:

- prevent closing tiny polygons,
- prevent zero-area zones,
- prevent duplicate accidental double-click zones,
- debounce expensive recalculations,
- make selected zone state explicit.

Acceptance criteria:

- no hidden/invisible zones,
- delete/select/edit are reliable,
- no console errors during normal use,
- app remains usable on resize.

---

## Suggested File Structure Later

For now, a single HTML file is acceptable.

Later refactor:

```txt
/src
  app.js
  map-openlayers.js
  geometry.js
  panel-layout.js
  geocoding.js
  export.js
  styles.css
index.html
```

Do not refactor too early. First get OpenLayers working end-to-end.

---

## Risks

### Imagery Terms

Some aerial imagery sources are free to view but not always free for production use, screenshots, or commercial use. Confirm licensing before public deployment.

### Imagery Accuracy

Orthophoto imagery may have offset, age, shadows, or roof distortion. Treat generated panel layouts as planning estimates, not final engineering drawings.

### Geocoding Limits

Free public geocoding services usually have strict rate limits. Use them only for development or low-volume manual use.

### Panel Packing Accuracy

Initial panel placement will be approximate. For better accuracy later, add:

- roof azimuth,
- roof pitch,
- setbacks,
- obstacles,
- landscape/portrait orientation,
- no-go zones,
- manual panel adjustment.

---

## First Implementation Milestone

Build a minimal OpenLayers version with:

- OpenLayers map,
- DGU/OSM/Esri layer switcher,
- draw polygon,
- select polygon,
- edit polygon,
- delete polygon,
- area calculation,
- simple panel count,
- export report.

Do not implement advanced panel rotation until the base map and geometry flow are stable.

---

## Done Definition

The migration is successful when:

- the app runs without Google Maps API,
- roof zones can be drawn and edited reliably,
- area is measured in real-world meters,
- panel count is stable across zoom/pan/resize,
- imagery quality is suitable for rooftop planning in Croatia,
- report export works,
- no Google Drawing Library code remains.
