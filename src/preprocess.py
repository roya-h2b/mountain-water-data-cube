"""Preprocessing utilities for glacier data."""

from pathlib import Path

import geopandas as gpd


RAW_PATH = Path("data/raw/rgi_central_europe_subset.geojson")
PROCESSED_PATH = Path("data/processed/glaciers_processed.geojson")


def preprocess_glaciers():
    """Prepare glacier outlines for analysis."""

    print("Loading raw glacier data...")

    glaciers = gpd.read_file(RAW_PATH)

    print(f"Input features: {len(glaciers)}")
    print(f"Input CRS: {glaciers.crs}")

    # Keep only relevant analysis fields
    selected_columns = [
        "rgi_id",
        "glac_name",
        "area_km2",
        "zmin_m",
        "zmax_m",
        "zmed_m",
        "zmean_m",
        "slope_deg",
        "aspect_deg",
        "lmax_m",
        "src_date",
        "dem_source",
        "geometry",
    ]

    glaciers = glaciers[selected_columns].copy()

    # Reproject to UTM Zone 32N for metric calculations
    glaciers_utm = glaciers.to_crs("EPSG:32632")

    # Calculate geometry-based area
    glaciers_utm["area_geom_km2"] = glaciers_utm.geometry.area / 1_000_000

    # Compare official RGI area with geometry-derived area
    glaciers_utm["area_diff_km2"] = (
        glaciers_utm["area_geom_km2"] - glaciers_utm["area_km2"]
    )

    # Convert back to geographic CRS for interoperability
    glaciers_out = glaciers_utm.to_crs("EPSG:4326")

    PROCESSED_PATH.parent.mkdir(parents=True, exist_ok=True)

    glaciers_out.to_file(
        PROCESSED_PATH,
        driver="GeoJSON",
    )

    print(f"Processed features: {len(glaciers_out)}")
    print(f"Output CRS: {glaciers_out.crs}")
    print(f"Saved to: {PROCESSED_PATH}")

    print("\nArea comparison summary:")
    print(
        glaciers_out[
            ["area_km2", "area_geom_km2", "area_diff_km2"]
        ].describe()
    )

    return glaciers_out


if __name__ == "__main__":
    preprocess_glaciers()