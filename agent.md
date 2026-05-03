# Agent instructions

You are working on **Solar Roof Planer / SolarSketch**.

## Mission

Improve the app without breaking the current working flows:

- draw roof zones
- select and edit zones
- estimate solar panel fit
- show panel rectangles on aerial imagery
- keep Croatian projects tied to a confirmed cadastral parcel
- keep the app usable on phones

## Project shape

- This is a static single-page app.
- There is no build system.
- The source of truth is `index.html`.
- Keep dependencies minimal.
- Do not add a framework unless explicitly requested.

## Current map stack

- The app uses OpenLayers from a CDN.
- The app registers EPSG:3765 with `proj4` for Croatian DGU/uredjenazemlja services.
- The app is currently Croatia-only for search and parcel workflows.
- Do not reintroduce Google Maps or the deprecated Google Maps Drawing Library.
- Do not add `libraries=drawing`.
- Do not use `google.maps.drawing.DrawingManager`.
- Do not hardcode or commit map API keys.

## Hard constraints

1. Keep OpenLayers drawing/editing reliable.
2. Store roof geometry in real coordinates, not screen pixels.
3. Keep panel counts stable across zoom, pan, and resize.
4. Update both the panel count and visible panel overlays after geometry or setting changes.
5. Keep mobile usability intact.
6. Confirm map resize after sidebar toggles with `notifyMapResize()`.
7. Keep parcel selection explicit: fetched parcel data must be confirmed in the modal before becoming `selectedParcel`.
8. Do not make slow WFS parcel lookup mandatory; preserve the map settings toggle.

## Working assumptions about the code

- `zones` is the main collection.
- `selectedZone` points to the currently selected zone or `null`.
- Zone geometry is stored as `coordinates: [[lon, lat], ...]`.
- The OpenLayers polygon feature is stored as `zone.feature`.
- Each zone owns a `settings` object for panel width, height, watts, spacing, angle, and Vmp.
- `defaultZoneSettings` is copied into newly drawn zones; sidebar edits apply to `selectedZone.settings` when a zone is selected.
- `maxStringVmp` is a global string-planning setting and defaults to 800 V.
- `selectedParcel` is the confirmed cadastral parcel for the project.
- `pendingParcel` is a fetched parcel awaiting modal confirmation.
- `parcelValid` / `parcelMessage` on each zone describe whether it fits inside `selectedParcel`.
- `updateStats()` is the main refresh path after most state changes.
- `computePanelLayoutInPolygon(...)` is the panel-fit engine.

## Preferred coding style

- Keep functions small and explicit.
- Prefer extending existing utilities over introducing parallel implementations.
- Guard map/geometry code clearly.
- Avoid hidden magic values; define constants when a threshold matters.
- Keep the app static and GitHub Pages-friendly.

## When changing drawing behavior

- Test polygon completion.
- Test select/edit vertex dragging.
- Test erase mode.
- Make sure draw mode does not interfere with select, erase, or pan.
- Avoid invisible zero-area zones.
- Confirm zone parcel-validity updates after drawing or editing when a parcel is selected.

## When changing cadastral behavior

- Keep base layer, cadastral overlays, and parcel lookup controls in the map settings gear.
- Keep parcel lookup optional because the official WFS can be slow.
- Show fetched parcel details in the blocking modal and require confirmation before updating `selectedParcel`.
- Do not silently replace the selected parcel from pan/zoom.
- Use the selected parcel only as a planning/legal aid; do not present it as authoritative engineering/legal advice.

## When changing panel fitting

- Use local meter coordinates for layout.
- Update counts and overlays together.
- Use each zone's own settings when recalculating panel layout.
- Keep selection/input synchronization intact when changing settings controls.
- Keep the algorithm deterministic and responsive enough for browser use.
- Confirm counts do not change from zooming alone.

## When changing mobile behavior

- Confirm sidebar toggling still triggers `notifyMapResize()`.
- Avoid controls that block roof drawing.
- Prefer map-first interactions on narrow screens.

## Recommended manual regression checklist

- App loads from `python -m http.server 8000`.
- DGU, Esri, and OSM imagery can be selected.
- Map settings gear opens and contains base layer, cadastral overlays, and parcel lookup.
- Cadastral parcel overlay can be shown over imagery.
- Parcel lookup can be toggled off.
- Clicking/searching a parcel opens a blocking confirmation modal.
- Confirmed parcel info appears and export blocks zones outside that parcel.
- Draw a zone.
- Select and edit it.
- Delete it.
- Change panel width, height, spacing, wattage, Vmp, and angle.
- Confirm two zones can have different settings and selecting each zone reloads the correct values.
- Confirm global max string Vmp updates string recommendations without changing zone panel settings.
- Confirm panel count and visible overlays update.
- Search an address and coordinates.
- Search results and coordinates are limited to Croatia.
- Export a report.
- Desktop sidebar hide/show works.
- Mobile slide-over menu opens and closes.

## Automated regression checklist

Run after every code or behavior change before committing. This is the stability gate for the project, especially when changing map, drawing, panel layout, imagery, search, export, or responsive layout behavior:

```bash
.\.venv\Scripts\python -m pytest
```

Do not commit a code change until the suite passes, unless the handoff explicitly documents the failure and why it is currently unavoidable.

If `.venv` does not exist, create it and install:

```bash
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
.\.venv\Scripts\python -m playwright install chromium
```

## Good next tasks

- save/load project state as JSON
- obstacle / exclusion zone support
- better snapping to roof edges
- export to PDF/PNG
- import/export of project files
- clearer touch handles for phone editing

## Avoid these mistakes

- reintroducing Google Maps code
- storing new roof geometry as pixels
- updating counts without updating overlays
- forgetting to clear old panel overlay features
- changing sidebar layout without resizing the map afterward
- adding unpublished keys or secrets to the repo
- bypassing the parcel confirmation modal
- making WFS lookup run on every pan or zoom

## Handoff expectation

When you finish a change, summarize:

- what changed
- what files changed
- what behaviors were tested
- any remaining uncertainty or known limitation
