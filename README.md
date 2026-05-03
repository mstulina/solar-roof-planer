# Solar Roof Planer

Draw roof zones on aerial imagery and estimate how many solar panels fit in real time.

## Features

- OpenLayers map with DGU orthophoto, Esri imagery, and OpenStreetMap layers
- Editable roof polygons with draw, select/edit, pan, and erase tools
- Real-world area measurement in square meters
- Stable panel-fit estimates that do not change when zooming
- Visual panel rectangle overlays inside each roof zone
- Panel width, height, spacing, wattage, and angle controls
- Responsive mobile layout with a toggleable planner menu
- Address and coordinate search
- Export a simple planning report

## Run locally

A local server is recommended because browser security rules can limit map and geocoding behavior from `file://`.

```bash
python -m http.server 8000
```

Then open `http://localhost:8000`.

## Map sources

The app does not require a Google Maps API key.

Available base layers:

- DGU Orthophoto 2024 WMS
- Esri World Imagery
- OpenStreetMap

Public imagery and geocoding providers can have usage limits or license restrictions. Confirm the terms before production or commercial deployment.

## Deploy on GitHub Pages

1. Push this repo to GitHub.
2. In GitHub, open **Settings -> Pages**.
3. Set the source to **Deploy from a branch**.
4. Choose the `main` branch and the `/ (root)` folder.

## Notes

- This is a static single-page app.
- The source of truth is `index.html`.
- Panel placement is a planning estimate, not an engineering design.
- Verify imagery alignment, roof dimensions, setbacks, obstacles, and electrical design on site.
