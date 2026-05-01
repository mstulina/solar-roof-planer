# Solar Roof Planer

Draw roof zones on satellite imagery and estimate how many solar panels fit in real time.

## Features

- Draw editable roof polygons on Google Maps satellite view
- Close a zone by clicking near the start point
- Live panel-fit recalculation as zones or panel settings change
- Visual placement of panel rectangles inside each zone
- Demo mode included when Google Maps is not connected
- Export a simple planning report

## Run locally

You can open `index.html` directly, but a local server is recommended.

### Python

```bash
python -m http.server 8000
```

Then open `http://localhost:8000`.

## Google Maps API setup

This app asks for your Google Maps API key at runtime.

Enable:

- Maps JavaScript API
- Geocoding API

Recommended restrictions for the API key:

- Application restriction: HTTP referrers
- Allowed referrers:
  - `http://localhost/*`
  - your GitHub Pages URL
- API restrictions:
  - Maps JavaScript API
  - Geocoding API

## Deploy on GitHub Pages

1. Push this repo to GitHub
2. In GitHub, open **Settings → Pages**
3. Set the source to **Deploy from a branch**
4. Choose the `main` branch and the `/ (root)` folder

## Notes

- Do not commit a raw unrestricted Google Maps API key
- The old Google Maps Drawing Library is deprecated, so this app uses custom polygon drawing instead
