# Agent instructions

You are working on **Solar Roof Planer / SolarSketch**.

## Mission
Improve the app without breaking the current working flows:
- draw roof zones
- edit zones
- estimate solar panel fit
- show panel rectangles on Google Maps
- keep the app usable on phones

## Project shape
- This is a **static single-page app**.
- There is **no build system**.
- The source of truth is `index.html`.
- Keep dependencies minimal.
- Do not add a framework unless explicitly requested.

## Hard constraints
1. **Do not use the deprecated Google Maps Drawing Library.**
   - Do not add `libraries=drawing`.
   - Do not use `google.maps.drawing.DrawingManager`.

2. **Do not hardcode or commit a Google Maps API key.**
   - The app asks the user to paste a key at runtime.
   - Preserve that workflow unless the owner explicitly asks for a different approach.

3. **Keep demo mode working.**
   - If Google Maps is unavailable, the app must still run.
   - Changes to shared geometry logic must support both demo zones and Google Maps zones.

4. **Keep mobile usability intact.**
   - The sidebar must remain hideable/showable.
   - Avoid UI changes that make the map unusable on small screens.

5. **Do not silently mix canvas and map geometry assumptions.**
   - Canvas zones use `points[]`.
   - Map zones use `gmPoly` and `gmPanels`.

## Working assumptions about the code
- `zones` may contain a mix of canvas zones and Google Maps zones.
- `selectedZone` may point to either kind.
- `updateStats()` is the main refresh path after most state changes.
- `updateGmapZone(zone)` is responsible for recalculating area, panel count, and visual panel overlays for a map zone.
- `computePanelLayoutInPolygon(...)` is the current panel-fit engine for both modes.

## Preferred coding style
- Keep functions small and explicit.
- Prefer extending existing utilities over introducing parallel implementations.
- Reuse the same panel-fit logic in both demo and map modes where possible.
- Guard cross-mode code with clear checks like:
  - `Array.isArray(zone.points)`
  - `zone.gmPoly`
- Avoid hidden magic values; define constants when a threshold matters.

## When changing drawing behavior
- Test closing a polygon by clicking near the first point.
- Test double-click close as a secondary path.
- Test cancel paths.
- Make sure `draw` mode does not interfere with `select`, `erase`, or `pan`.

## When changing panel fitting
- Update both the **count** and the **visible overlays**.
- Do not leave Google Maps using a rough area estimate while demo mode uses real rectangle checks.
- If you introduce better packing, keep it deterministic and responsive enough for browser use.

## When changing mobile behavior
- Confirm sidebar toggling still triggers `notifyMapResize()`.
- Avoid controls that sit under the sidebar or block roof drawing.
- Prefer map-first interactions on narrow screens.

## Recommended manual regression checklist
Run through these before handing off:

### Demo mode
- Draw a zone.
- Close it.
- Change panel width/height/spacing/angle.
- Confirm panel count and stats update.
- Select and delete zones.

### Google Maps mode
- Load the map with a runtime API key.
- Search an address.
- Draw a roof zone.
- Close the zone by clicking near the start point.
- Select the zone and drag vertices.
- Confirm panel rectangles redraw.
- Change panel size/spacing/angle.
- Confirm counts update immediately.
- Use zoom controls on mobile/narrow layout.

### Responsive layout
- Desktop sidebar hide/show works.
- Mobile slide-over menu opens and closes.
- Tapping a tool on mobile returns focus to the map.

## If asked to restructure the project
A light restructure is acceptable:
- `index.html`
- `styles.css`
- `app.js`

But keep it static and GitHub Pages-friendly unless explicitly told otherwise.

## Good next tasks
These are good bets for future work:
- save/load project state as JSON
- obstacle / exclusion zone support
- per-zone angle controls
- better snapping to roof edges
- export to PDF/PNG
- import/export of project files
- clearer touch handles for phone editing

## Avoid these mistakes
- reintroducing duplicate map click listeners
- calling canvas renderers on Google Maps zones
- forgetting to clear old `gmPanels`
- updating counts without updating overlays
- changing sidebar layout without resizing the map afterward
- adding unpublished keys or secrets to the repo

## Handoff expectation
When you finish a change, summarize:
- what changed
- what files changed
- what behaviors were tested
- any remaining uncertainty or known limitation
