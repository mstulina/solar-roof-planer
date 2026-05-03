# HANDOFF

## Project
Solar Roof Planer / SolarSketch

Static single-page app for drawing roof zones on satellite imagery and estimating solar panel fit in real time. The app runs as plain HTML/CSS/JavaScript with no build step.

## Current state
The current working app is `index.html`.

It supports:
- demo mode on a local canvas when Google Maps is not connected
- Google Maps satellite mode loaded at runtime from a user-entered API key
- custom polygon drawing without the deprecated Google Maps Drawing Library
- live panel-fit recalculation for both demo and Google Maps modes
- visual panel rectangle overlays on Google Maps
- editable roof zones
- mobile layout with a hideable slide-over sidebar
- manual panel rotation plus automatic angle suggestion from the selected roof edge
- extra zoom controls for better phone precision

## Why the custom drawing exists
This project originally depended on the Google Maps Drawing Library. That library is deprecated, so drawing is now implemented with native map events plus `google.maps.Polyline` and `google.maps.Polygon`.

Do not reintroduce `google.maps.drawing.DrawingManager`.

## Files
- `index.html` — whole application, including styles and scripts
- `README.md` — end-user setup and deploy notes
- `HANDOFF.md` — project state and technical context
- `agent.md` — instructions for future coding agents

## Architecture summary
This app is intentionally single-file.

### UI layers
- **Header**: branding, address search, mode badge, connect-maps button, sidebar toggle
- **Sidebar**: tools, panel settings, stats, zone list
- **Main view**:
  - demo canvas mode
  - Google Maps container
  - instructions toast
  - map zoom controls

### Two rendering modes
#### 1. Demo mode
Uses the `<canvas>` element and stores polygon coordinates as screen-space points:
- `zone.points = [{x, y}, ...]`
- panels are drawn directly on the canvas
- area is estimated via polygon area × map scale

#### 2. Google Maps mode
Uses Google Maps polygons and local meter coordinates derived from Lat/Lng:
- `zone.gmPoly` is the source geometry
- `zone.gmPanels` stores overlay polygons for visible panel rectangles
- a local coordinate frame is created from the polygon path for fit calculations
- area is computed with `google.maps.geometry.spherical.computeArea`

The app must keep both modes working. Canvas-only logic must not assume `zone.gmPoly`, and Google Maps logic must not assume `zone.points`.

## Important data structures
`zones` is the main collection.

A demo/canvas zone usually looks like:
```js
{
  id,
  name,
  color,
  points: [{ x, y }, ...],
  panelCount,
  area
}
```

A Google Maps zone usually looks like:
```js
{
  id,
  name,
  color,
  gmPoly,
  gmPanels: [],
  panelCount,
  area
}
```

`selectedZone` points to the currently selected zone in either mode.

## Important functions
### App / layout
- `syncResponsiveLayout()` — switches mobile vs desktop sidebar behavior
- `toggleSidebar()` / `openSidebar()` / `closeSidebar()` — sidebar control
- `notifyMapResize()` — keeps Google Maps rendering correctly after layout changes

### Drawing
- `setTool(tool)` — central tool switch
- `setupGmapDrawing()` — installs custom Google Maps drawing listeners
- `completeGmapDrawing()` — finishes a polygon
- `createGmapPolygon()` — creates a new map zone
- `cancelGmapDrawing()` — clears unfinished map drawing
- `syncGmapStartHandle()` / `isNearGmapStartPoint()` — start-point close interaction

### Selection / editing
- `attachPolygonEvents(zone)` — hooks selection, erase, and edit listeners
- `syncGmapSelection()` — keeps the selected polygon editable and highlighted
- `selectZone(id)` — sidebar selection handler

### Panel layout and geometry
- `getPanelAngleDegrees()`
- `normalizePanelAngle(angleDeg)`
- `getZoneSuggestedAngle(zone)`
- `autoAlignPanels()` / `resetPanelAngle()`
- `computePanelLayoutInPolygon(polygonPoints, panelWidth, panelHeight, panelSpacing, keepPlacements, angleDeg)`
- `buildPlacement(...)`
- `rotatePoint(...)`
- `rectSamplesInsidePolygon(...)`
- `getLatLngLocalFrame(pathLike)`
- `localMetersToLatLng(frame, x, y)`
- `updateGmapZone(zone)` — recomputes area, count, and visible map panel overlays
- `drawPanelsInZone(zone)` — demo-mode panel rendering
- `renderGmapPanels(zone, placements, frame)` — Google Maps visible panel rectangles

### Stats / search / export
- `updateStats()` — global refresh entry point after geometry or settings changes
- `searchAddress()` — geocoding-based map centering
- `exportReport()` — text export
- `zoomMap(step)` — map zoom buttons; in demo mode this adjusts scale

## Panel-fit algorithm
The current fit logic is simple but usable:
1. Convert the polygon to local coordinates.
2. Rotate the polygon by `-panelAngle` so the placement grid can stay axis-aligned internally.
3. Try both panel orientations if width and height differ.
4. Sweep a grid through the bounding box with several X/Y offsets.
5. Accept a panel if interior sample points all fall inside the polygon.
6. Keep the best count.
7. Rotate panel rectangles back for visible rendering.

This means panel placement is still a heuristic. It is not a full packing optimizer.

## Known limitations
- Panel fitting is approximate; it is not guaranteed to find the globally optimal packing.
- There is no obstacle handling yet for chimneys, skylights, vents, setbacks, or walkways.
- Polygon self-intersections are not validated.
- Multi-touch editing on phones is only as good as the browser + Google Maps interaction model.
- Export is still a plain text report.
- No persistence layer exists yet. Reloading the page loses zones.
- There is no snapping to roof edges except the user-driven angle controls.

## Regressions that were already fixed and should not return
- duplicate Google Maps click listeners causing doubled points
- relying only on double-click to close zones
- crashing canvas render when a Google Maps zone had no `points[]`
- rough area-based panel estimates for map zones
- panel overlays not updating after edits
- mobile sidebar blocking the map without a proper hide/show flow

## Local run
Recommended:
```bash
python -m http.server 8000
```
Then open `http://localhost:8000`.

Opening the file directly with `file://` can trigger browser security quirks.

## Google Maps requirements
The app asks for the API key at runtime. This is intentional.

Enable:
- Maps JavaScript API
- Geocoding API

The script loader uses:
- `libraries=geometry`
- `loading=async`
- `v=weekly`

## Deployment
This is designed to work well on GitHub Pages because it is a static site.

## Suggested next improvements
High-value next steps:
1. Save/load project JSON.
2. Obstacle drawing and exclusion zones.
3. Per-zone panel angle instead of one global angle.
4. Better mobile drawing handles.
5. Real-world roof edge snapping.
6. PDF/PNG export with a layout summary.
7. Production split into `index.html`, `styles.css`, and `app.js` when the single file becomes too hard to maintain.

## Safe change strategy
If modifying the panel logic, verify all of these before handoff:
- create zone in demo mode
- create zone in Google Maps mode
- close by clicking near start point
- move polygon vertices and confirm stats update
- change panel width/height/spacing/angle and confirm counts update
- mobile sidebar still opens/closes cleanly
- Google Maps still centers correctly after sidebar toggles
