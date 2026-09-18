"""Build and validate area-weighted links between glaciers and ERA5-Land cells."""

from pathlib import Path

import geopandas as gpd


GLACIER_PATH = Path(
    "data/processed/glaciers_with_dem_stats.geojson"
)

CLIMATE_GRID_PATH = Path(
    "data/processed/era5_land_grid.geojson"
)

OUTPUT_PATH = Path(
    "data/processed/glacier_climate_weights.geojson"
)

METRIC_CRS = "EPSG:32632"

FULL_COVERAGE_THRESHOLD = 0.999


def load_inputs():
    """Load glacier polygons and ERA5-Land grid cells."""

    glaciers = gpd.read_file(GLACIER_PATH)
    climate_grid = gpd.read_file(CLIMATE_GRID_PATH)

    return glaciers, climate_grid


def prepare_inputs(glaciers, climate_grid):
    """Reproject both datasets to a metric CRS and calculate glacier areas."""

    glaciers_metric = glaciers.to_crs(METRIC_CRS).copy()
    grid_metric = climate_grid.to_crs(METRIC_CRS).copy()

    glaciers_metric["glacier_area_m2"] = (
        glaciers_metric.geometry.area
    )

    return glaciers_metric, grid_metric


def build_intersections(glaciers, climate_grid):
    """Intersect glacier polygons with ERA5-Land grid cells."""

    glacier_columns = [
        "rgi_id",
        "glacier_area_m2",
        "geometry",
    ]

    grid_columns = [
        "cell_id",
        "latitude",
        "longitude",
        "geometry",
    ]

    intersections = gpd.overlay(
        glaciers[glacier_columns],
        climate_grid[grid_columns],
        how="intersection",
        keep_geom_type=False,
    )

    intersections["intersection_area_m2"] = (
        intersections.geometry.area
    )

    return intersections


def calculate_weights_and_coverage(intersections):
    """Calculate normalized area weights and climate-grid coverage."""

    intersections = intersections.copy()

    intersections["covered_area_m2"] = (
        intersections.groupby("rgi_id")[
            "intersection_area_m2"
        ].transform("sum")
    )

    intersections["area_weight"] = (
        intersections["intersection_area_m2"]
        / intersections["covered_area_m2"]
    )

    intersections["climate_coverage"] = (
        intersections["covered_area_m2"]
        / intersections["glacier_area_m2"]
    )

    intersections["coverage_status"] = "partial"

    intersections.loc[
        intersections["climate_coverage"]
        >= FULL_COVERAGE_THRESHOLD,
        "coverage_status",
    ] = "full"

    return intersections


def validate_results(intersections, glaciers):
    """Print QA statistics for weights and spatial coverage."""

    total_glaciers = glaciers["rgi_id"].nunique()
    represented_glaciers = intersections["rgi_id"].nunique()
    outside_glaciers = total_glaciers - represented_glaciers

    print("\nTotal glaciers:")
    print(total_glaciers)

    print("\nNumber of glacier-grid intersections:")
    print(len(intersections))

    print("\nGlaciers represented in climate grid:")
    print(represented_glaciers)

    print("\nGlaciers outside climate grid:")
    print(outside_glaciers)

    cells_per_glacier = intersections.groupby(
        "rgi_id"
    )["cell_id"].nunique()

    print("\nERA5-Land cells per glacier:")
    print(cells_per_glacier.describe())

    weight_sums = intersections.groupby(
        "rgi_id"
    )["area_weight"].sum()

    print("\nMaximum absolute weight-sum deviation from 1:")
    print(
        (weight_sums - 1.0).abs().max()
    )

    glacier_coverage = (
        intersections[
            [
                "rgi_id",
                "climate_coverage",
                "coverage_status",
            ]
        ]
        .drop_duplicates("rgi_id")
    )

    print("\nClimate coverage statistics:")
    print(
        glacier_coverage[
            "climate_coverage"
        ].describe()
    )

    print("\nCoverage status:")
    print(
        glacier_coverage[
            "coverage_status"
        ].value_counts()
    )

    partial = glacier_coverage[
        glacier_coverage["coverage_status"] == "partial"
    ].sort_values("climate_coverage")

    if not partial.empty:
        print("\nLowest climate coverage values:")
        print(partial.head(10))


def save_weights(intersections):
    """Save glacier-grid weights and coverage information."""

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    output = intersections.to_crs("EPSG:4326")

    output.to_file(
        OUTPUT_PATH,
        driver="GeoJSON",
    )

    print("\nSaved glacier-climate weights to:")
    print(OUTPUT_PATH)


if __name__ == "__main__":
    glaciers, climate_grid = load_inputs()

    glaciers_metric, grid_metric = prepare_inputs(
        glaciers,
        climate_grid,
    )

    intersections = build_intersections(
        glaciers_metric,
        grid_metric,
    )

    weighted_intersections = calculate_weights_and_coverage(
        intersections
    )

    validate_results(
        weighted_intersections,
        glaciers_metric,
    )

    save_weights(
        weighted_intersections
    )