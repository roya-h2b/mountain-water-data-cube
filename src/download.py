"""Data acquisition utilities for the Mountain Water Data Cube project."""

from pathlib import Path

import geopandas as gpd
import requests

from config import STUDY_AREA


GLIMS_WFS_URL = "https://www.glims.org/geoserver/ows"

RGI_LAYER = "GLIMS:RGI2000-v7.0-G-11_central_europe_epsg3857"


def download_glaciers():
    """Download RGI glacier outlines intersecting the study area."""

    bbox = (
        f"{STUDY_AREA['west']},"
        f"{STUDY_AREA['south']},"
        f"{STUDY_AREA['east']},"
        f"{STUDY_AREA['north']},"
        "EPSG:4326"
    )

    params = {
        "service": "WFS",
        "version": "2.0.0",
        "request": "GetFeature",
        "typeNames": RGI_LAYER,
        "outputFormat": "application/json",
        "srsName": "EPSG:4326",
        "bbox": bbox,
    }

    print("Requesting glacier outlines from GLIMS...")

    response = requests.get(
        GLIMS_WFS_URL,
        params=params,
        timeout=60,
    )

    response.raise_for_status()

    data = response.json()

    print(f"Features returned: {len(data['features'])}")

    glaciers = gpd.GeoDataFrame.from_features(
        data["features"],
        crs="EPSG:4326",
    )

    output_dir = Path("data/raw")
    output_dir.mkdir(parents=True, exist_ok=True)

    output_path = output_dir / "rgi_central_europe_subset.geojson"

    glaciers.to_file(
        output_path,
        driver="GeoJSON",
    )

    print(f"Saved to: {output_path}")
    print(f"CRS: {glaciers.crs}")
    print(f"Number of glaciers: {len(glaciers)}")
    
    print(f"Bounds: {glaciers.total_bounds}")
    print("\nAvailable attributes:")
    for column in glaciers.columns:
        print(f"  - {column}")

    return glaciers


if __name__ == "__main__":
    download_glaciers()