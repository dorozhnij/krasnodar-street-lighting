"""Prepare GeoJSON points for Krasnodar street-lighting map."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
CSV_PATH = ROOT / "освещенность_улиц_Краснодарский_край.csv"
OUT_DIR = Path(__file__).resolve().parent / "data"
OUT_PATH = OUT_DIR / "points.geojson"


def main() -> None:
    df = pd.read_csv(CSV_PATH, sep=";")
    df = df[df["долгота"].notna() & df["широта"].notna()].copy()

    pop = pd.to_numeric(df["численность_населения"], errors="coerce")
    approx = pd.to_numeric(df["население_приблизительно"], errors="coerce")
    df["pop"] = pop.fillna(0)
    mask = (df["pop"] <= 0) & approx.notna()
    df.loc[mask, "pop"] = approx[mask].fillna(1)

    df["light_pct"] = pd.to_numeric(df["доля_освещенности_проц"], errors="coerce").fillna(0)
    df["lit_km"] = pd.to_numeric(df["освещенная_протяженность_км"], errors="coerce")
    df["total_km"] = pd.to_numeric(df["общая_протяженность_км"], errors="coerce")

    features = []
    for _, row in df.iterrows():
        name = row["гео_название"] if pd.notna(row["гео_название"]) else row["населенный_пункт"]
        features.append(
            {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [float(row["долгота"]), float(row["широта"])],
                },
                "properties": {
                    "oktmo": str(row["октмо"]),
                    "name": str(name) if pd.notna(name) else "",
                    "np_label": str(row["населенный_пункт"]) if pd.notna(row["населенный_пункт"]) else "",
                    "rayon": str(row["район"]) if pd.notna(row["район"]) else "",
                    "pop": float(row["pop"]),
                    "light_pct": float(row["light_pct"]),
                    "lit_km": None if pd.isna(row["lit_km"]) else float(row["lit_km"]),
                    "total_km": None if pd.isna(row["total_km"]) else float(row["total_km"]),
                    "match": str(row["стыковка"]) if pd.notna(row["стыковка"]) else "",
                },
            }
        )

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    collection = {"type": "FeatureCollection", "features": features}
    OUT_PATH.write_text(json.dumps(collection, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote {len(features)} points -> {OUT_PATH}")


if __name__ == "__main__":
    main()
