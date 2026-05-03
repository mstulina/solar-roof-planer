# Solar Roof Planer

Draw roof zones on aerial imagery and estimate how many solar panels fit in real time.

## Features

- OpenLayers map with DGU orthophoto, Esri imagery, and OpenStreetMap layers
- Croatia-only map/search behavior with cadastral parcel and municipality overlays
- Confirmed cadastral parcel selection for keeping a project inside one plot
- Editable roof polygons with draw, select/edit, pan, and erase tools
- Real-world area measurement in square meters
- Stable panel-fit estimates that do not change when zooming
- Visual panel rectangle overlays inside each roof zone
- Independent panel width, height, spacing, wattage, Vmp, and angle controls per roof zone
- Global maximum string Vmp setting with per-zone string count recommendations
- Map settings gear for base layers, cadastral overlays, and parcel lookup control
- Responsive mobile layout with a toggleable planner menu
- Croatian address and coordinate search
- Export a simple planning report with cadastral plot, per-zone settings, and string guidance

## Run locally

A local server is recommended because browser security rules can limit map and geocoding behavior from `file://`.

```bash
python -m http.server 8000
```

Then open `http://localhost:8000`.

## Test

Create the local test environment:

```bash
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
.\.venv\Scripts\python -m playwright install chromium
```

Run the browser and geometry smoke suite:

```bash
.\.venv\Scripts\python -m pytest
```

The suite starts a local static server, verifies the app boots without Google Maps, checks cadastral controls and Croatian search limits, verifies mocked parcel confirmation/enforcement, checks the panel layout engine in the browser context, creates zones programmatically, verifies per-zone settings and string recommendations, and saves screenshot smoke artifacts under `test-artifacts/`.

## Map sources

The app does not require a Google Maps API key.

Available base layers:

- DGU Orthophoto 2024 WMS
- Esri World Imagery
- OpenStreetMap

Cadastral data:

- DGU/uredjenazemlja INSPIRE cadastral parcel WMS/WFS
- Parcel lookup is intentionally optional because the official WFS can be slow
- A clicked/searched parcel must be confirmed in the blocking modal before it becomes the active project plot

Public imagery, cadastral, and geocoding providers can have usage limits or license restrictions. Confirm the terms before production or commercial deployment.

## Deploy on GitHub Pages

1. Push this repo to GitHub.
2. In GitHub, open **Settings -> Pages**.
3. Set the source to **Deploy from a branch**.
4. Choose the `main` branch and the `/ (root)` folder.

## Notes

- This is a static single-page app.
- The source of truth is `index.html`.
- Current stable baseline: OpenLayers cadastral app plus 11 Python/Playwright regression tests.
- Panel placement is a planning estimate, not an engineering design.
- String recommendations and parcel containment are planning aids; verify module Voc at cold temperature, inverter MPPT/current limits, optimizer rules, setbacks, roof dimensions, cadastral/legal constraints, and local code requirements before engineering or installation.
