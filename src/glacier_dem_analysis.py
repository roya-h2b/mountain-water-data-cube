"""Analyze glacier polygons against the processed study-area DEM."""

from pathlib import Path

import geopandas as gpd
import rasterio
from rasterio.mask import mask

import numpy as np

from shapely.geometry import box

import pandas as pd

GLACIER_PATH = Path("data/processed/glaciers_processed.geojson")
DEM_PATH = Path("data/processed/study_area_dem.tif")


def inspect_inputs():
    """Inspect CRS and spatial extent of glacier and DEM datasets."""

    glaciers = gpd.read_file(GLACIER_PATH)
    print("\nGlacier columns:")
    print(glaciers.columns.tolist())

    with rasterio.open(DEM_PATH) as dem:
        print("Glacier dataset:")
        print(f"  Features: {len(glaciers)}")
        print(f"  CRS: {glaciers.crs}")
        print(f"  Bounds: {glaciers.total_bounds}")

        print("\nDEM dataset:")
        print(f"  CRS: {dem.crs}")
        print(f"  Bounds: {dem.bounds}")
        print(f"  Shape: ({dem.height}, {dem.width})")
        print(f"  Resolution: {dem.res}")

def extract_glacier_dem_statistics():
    """Extract DEM elevation statistics for each glacier."""

    glaciers = gpd.read_file(GLACIER_PATH)

    results = []

    with rasterio.open(DEM_PATH) as dem:
        dem_bounds_geometry = box(*dem.bounds)

        for index, row in glaciers.iterrows():
            geometry = row.geometry

            if geometry is None or geometry.is_empty:
                continue

            if not geometry.intersects(dem_bounds_geometry):
                coverage = "none"

                results.append(
                    {
                        "index": index,
                        "dem_coverage": coverage,
                        "dem_min_m": np.nan,
                        "dem_max_m": np.nan,
                        "dem_mean_m": np.nan,
                        "dem_median_m": np.nan,
                        "dem_relief_m": np.nan,
                    }
                )

                continue

            if dem_bounds_geometry.covers(geometry):
                coverage = "full"
                analysis_geometry = geometry
            else:
                coverage = "partial"
                analysis_geometry = geometry.intersection(
                    dem_bounds_geometry
                )

            masked_dem, _ = mask(
                dem,
                [analysis_geometry],
                crop=True,
                filled=False,
            )

            values = masked_dem[0].compressed()
            values = values[np.isfinite(values)]

            if values.size == 0:
                dem_min = np.nan
                dem_max = np.nan
                dem_mean = np.nan
                dem_median = np.nan
                dem_relief = np.nan
            else:
                dem_min = float(values.min())
                dem_max = float(values.max())
                dem_mean = float(values.mean())
                dem_median = float(np.median(values))
                dem_relief = dem_max - dem_min

            results.append(
                {
                    "index": index,
                    "dem_coverage": coverage,
                    "dem_min_m": dem_min,
                    "dem_max_m": dem_max,
                    "dem_mean_m": dem_mean,
                    "dem_median_m": dem_median,
                    "dem_relief_m": dem_relief,
                }
            )

    statistics = pd.DataFrame(results).set_index("index")

    glaciers = glaciers.join(statistics)

    return glaciers


def print_analysis_summary(glaciers):
    """Print a summary of glacier DEM extraction."""

    print("\nDEM coverage:")
    print(glaciers["dem_coverage"].value_counts())

    valid = glaciers["dem_mean_m"].notna().sum()

    print(f"\nGlaciers with valid DEM statistics: {valid}")

    print("\nExtracted DEM elevation statistics:")
    print(
        glaciers[
            [
                "dem_min_m",
                "dem_max_m",
                "dem_mean_m",
                "dem_median_m",
                "dem_relief_m",
            ]
        ].describe()
    )


def compare_dem_with_rgi(glaciers):
    """Compare extracted DEM elevations with RGI elevation attributes."""

    full = glaciers[
        glaciers["dem_coverage"] == "full"
    ].copy()

    full["mean_diff_m"] = (
        full["dem_mean_m"] - full["zmean_m"]
    )

    full["min_diff_m"] = (
        full["dem_min_m"] - full["zmin_m"]
    )

    full["max_diff_m"] = (
        full["dem_max_m"] - full["zmax_m"]
    )

    print("\nDEM vs RGI comparison (full-coverage glaciers):")

    print(
        full[
            [
                "mean_diff_m",
                "min_diff_m",
                "max_diff_m",
            ]
        ].describe()
    )

    print("\nLargest DEM relief values:")

    columns = [
        "rgi_id",
        "glac_name",
        "area_km2",
        "zmin_m",
        "zmax_m",
        "dem_min_m",
        "dem_max_m",
        "dem_relief_m",
    ]

    print(
        full[
            columns
        ]
        .sort_values(
            "dem_relief_m",
            ascending=False,
        )
        .head(10)
        .to_string(index=False)
    )

    return full

def save_analysis_dataset(glaciers):
    """Save glacier attributes enriched with DEM statistics."""

    output_path = Path(
        "data/processed/glaciers_with_dem_stats.geojson"
    )

    glaciers.to_file(
        output_path,
        driver="GeoJSON",
    )

    print(f"\nSaved enriched glacier dataset to: {output_path}")

def add_rgi_comparison_fields(glaciers):
    """Add DEM-minus-RGI elevation differences."""

    glaciers = glaciers.copy()

    glaciers["mean_diff_m"] = np.where(
        glaciers["dem_coverage"] == "full",
        glaciers["dem_mean_m"] - glaciers["zmean_m"],
        np.nan,
    )

    glaciers["min_diff_m"] = np.where(
        glaciers["dem_coverage"] == "full",
        glaciers["dem_min_m"] - glaciers["zmin_m"],
        np.nan,
    )

    glaciers["max_diff_m"] = np.where(
        glaciers["dem_coverage"] == "full",
        glaciers["dem_max_m"] - glaciers["zmax_m"],
        np.nan,
    )

    return glaciers

if __name__ == "__main__":
    inspect_inputs()

    glaciers = extract_glacier_dem_statistics()

    print_analysis_summary(glaciers)
    glaciers = add_rgi_comparison_fields(glaciers)
    comparison = compare_dem_with_rgi(glaciers)
    save_analysis_dataset(glaciers)