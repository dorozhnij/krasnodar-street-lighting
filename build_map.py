"""Interactive map: Krasnodar settlements — population (area) + lighting (ring arc)."""

from __future__ import annotations

import json
import math
from pathlib import Path

from llmaps import Map
from llmaps.components import Controls, Popup
from llmaps.layers import CircleLayer
from llmaps.sources import FileSource

DIR = Path(__file__).resolve().parent
DATA_PATH = DIR / "data" / "points.geojson"
OVERLAY_JS = DIR / "ring_overlay.js"
OUT_HTML = DIR / "index.html"

POP_MAX = 918_145


def load_points_meta() -> tuple[float, list[float], float]:
    with DATA_PATH.open(encoding="utf-8") as f:
        fc = json.load(f)
    pops = [float(ft["properties"]["pop"]) for ft in fc["features"] if ft["properties"].get("pop")]
    pop_max = max(pops) if pops else POP_MAX
    lons, lats = [], []
    for ft in fc["features"]:
        lon, lat = ft["geometry"]["coordinates"]
        lons.append(lon)
        lats.append(lat)
    pad_lon = (max(lons) - min(lons)) * 0.08 or 0.2
    pad_lat = (max(lats) - min(lats)) * 0.08 or 0.2
    center = [
        (min(lons) + max(lons)) / 2,
        (min(lats) + max(lats)) / 2,
    ]
    zoom = 6.8
    _ = (pad_lon, pad_lat)  # reserved for future fitBounds
    return pop_max, center, zoom


def main() -> None:
    if not DATA_PATH.is_file():
        raise SystemExit("Run prepare_data.py first.")

    pop_max, center, zoom = load_points_meta()
    sqrt_pop_max = math.sqrt(pop_max)
    radius_scale = 1 / math.sqrt(5)  # площадь кругов в 5 раз меньше
    radius_expr = [
        "interpolate",
        ["linear"],
        ["sqrt", ["max", ["get", "pop"], 1]],
        1,
        4 * radius_scale,
        sqrt_pop_max,
        52 * radius_scale,
    ]

    source = FileSource(id="settlements", path=str(DATA_PATH.resolve()), promote_id="oktmo")
    hit_layer = CircleLayer(
        id="settlements-hit",
        source=source,
        radius=radius_expr,
        color="#ffffff",
        opacity=0.01,
        stroke_width=0,
    )

    m = Map(
        center=center,
        zoom=zoom,
        title="Как освещаются улицы Краснодарского края",
        tiles="osm",
        style_url="https://tiles.openfreemap.org/styles/dark",
        custom_attribution=(
            '© <a href="https://www.openstreetmap.org/copyright" target="_blank">OpenStreetMap</a> '
            '© <a href="https://openfreemap.org/" target="_blank">OpenFreeMap</a> '
            '| <a href="https://github.com/greadr71/LLMaps" target="_blank">LLMaps</a>'
        ),
        embedded=True,
        locale="ru-RU",
    )

    m.add_layer(hit_layer)
    m.add_component(
        Popup(
            fields=["name", "np_label", "rayon", "pop", "light_pct", "total_km", "lit_km"],
            field_labels={
                "name": "Название",
                "np_label": "В реестре",
                "rayon": "Район",
                "pop": "Население",
                "light_pct": "Освещённость, %",
                "total_km": "Улицы, км",
                "lit_km": "С освещением, км",
            },
        )
    )
    m.add_component(Controls(zoom=True, scale=True, fullscreen=True, hash=True))

    with DATA_PATH.open(encoding="utf-8") as f:
        points_fc = json.load(f)
    m.embed_data("points", points_fc)
    m.embed_data("meta", {"pop_max": pop_max})

    m.add_custom_html(
        """
        <div id="krasnodar-ring-host" aria-hidden="true"></div>
        <aside class="krasnodar-intro" aria-label="О карте">
          <p class="krasnodar-kicker">Краснодарский край</p>
          <h1 class="krasnodar-title">Как освещаются улицы Краснодарского края</h1>
          <p class="krasnodar-lead">
            Площадь круга — численность населения. Длина светящегося кольца — доля освещённых улиц, %.
          </p>
        </aside>
        """
    )

    m.add_custom_css(
        """
        :root {
          --hse-bg: #0a0a0a;
          --hse-fg: #f5f5f5;
          --hse-muted: rgba(245, 245, 245, 0.55);
          --hse-accent: #ffcc08;
        }
        html, body {
          background: var(--hse-bg);
          color: var(--hse-fg);
          font-family: "Helvetica Neue", Arial, sans-serif;
          letter-spacing: 0.01em;
        }
        #krasnodar-ring-host {
          position: fixed;
          inset: 0;
          pointer-events: none;
          z-index: 5;
        }
        .krasnodar-ring-canvas {
          position: absolute;
          left: 0;
          top: 0;
          width: 100%;
          height: 100%;
          pointer-events: none;
        }
        .krasnodar-intro {
          position: absolute;
          top: 24px;
          left: 24px;
          max-width: min(420px, calc(100vw - 48px));
          z-index: 3;
          pointer-events: none;
          padding: 0;
          margin: 0;
        }
        .krasnodar-kicker {
          margin: 0 0 8px;
          font-size: 11px;
          font-weight: 500;
          text-transform: uppercase;
          letter-spacing: 0.14em;
          color: var(--hse-muted);
        }
        .krasnodar-title {
          margin: 0 0 12px;
          font-size: clamp(28px, 4vw, 40px);
          font-weight: 500;
          line-height: 1.05;
          color: var(--hse-fg);
        }
        .krasnodar-lead {
          margin: 0;
          font-size: 14px;
          line-height: 1.45;
          color: var(--hse-muted);
          border-left: 2px solid var(--hse-accent);
          padding-left: 12px;
        }
        .maplibregl-popup-content {
          background: rgba(12, 12, 12, 0.94);
          color: var(--hse-fg);
          border-radius: 2px;
          border: 1px solid rgba(255, 255, 255, 0.08);
          font-family: "Helvetica Neue", Arial, sans-serif;
          font-size: 13px;
        }
        .maplibregl-popup-close-button {
          color: var(--hse-muted);
        }
        .llmaps-legend {
          background: rgba(10, 10, 10, 0.85) !important;
          color: var(--hse-fg) !important;
          border: 1px solid rgba(255, 255, 255, 0.08) !important;
          border-radius: 2px !important;
          backdrop-filter: blur(8px);
        }
        """
    )

    m.add_custom_js(OVERLAY_JS)
    m.save(str(OUT_HTML))
    print(f"Saved {OUT_HTML}")


if __name__ == "__main__":
    main()
