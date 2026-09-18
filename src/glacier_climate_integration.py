from pathlib import Path

import geopandas as gpd
import pandas as pd
import xarray as xr


CLIMATE_CUBE_PATH = Path(
    "data/processed/era5_land_climate_cube_2024.zarr"
)

WEIGHTS_PATH = Path(
    "data/processed/glacier_climate_weights.geojson"
)

OUTPUT_CSV_PATH = Path(
    "data/processed/glacier_climate_monthly_2024.csv"
)

OUTPUT_ZARR_PATH = Path(
    "data/processed/glacier_climate_monthly_2024.zarr"
)
CLIMATE_GRID_PATH = Path(
    "data/processed/era5_land_grid.geojson"
)

def load_inputs():
    """Load the climate cube, climate grid, and glacier-grid area weights."""

    climate_cube = xr.open_zarr(CLIMATE_CUBE_PATH)
    climate_grid = gpd.read_file(CLIMATE_GRID_PATH)
    weights = gpd.read_file(WEIGHTS_PATH)

    return climate_cube, climate_grid, weights


def climate_cube_to_dataframe(climate_cube, climate_grid):
    """Convert the climate cube to tabular form and attach cell IDs."""

    climate_df = (
        climate_cube[["t2m", "tp"]]
        .to_dataframe()
        .reset_index()
    )

    grid_lookup = climate_grid[
        ["cell_id", "latitude", "longitude"]
    ].copy()

    climate_df["latitude_key"] = climate_df["latitude"].round(6)
    climate_df["longitude_key"] = climate_df["longitude"].round(6)

    grid_lookup["latitude_key"] = grid_lookup["latitude"].round(6)
    grid_lookup["longitude_key"] = grid_lookup["longitude"].round(6)

    climate_df = climate_df.merge(
        grid_lookup[
            ["cell_id", "latitude_key", "longitude_key"]
        ],
        on=["latitude_key", "longitude_key"],
        how="left",
        validate="many_to_one",
    )

    climate_df = climate_df.drop(
        columns=["latitude_key", "longitude_key"]
    )

    missing_cell_ids = climate_df["cell_id"].isna().sum()

    print(
        "Climate records without cell_id:",
        missing_cell_ids,
    )

    return climate_df


def attach_climate_to_weights(weights, climate_df):
    """Attach monthly climate values using stable climate-cell IDs."""

    weights_table = weights[
        [
            "rgi_id",
            "cell_id",
            "area_weight",
            "climate_coverage",
            "coverage_status",
        ]
    ].copy()

    merged = weights_table.merge(
        climate_df[
            ["cell_id", "time", "t2m", "tp"]
        ],
        on="cell_id",
        how="left",
        validate="many_to_many",
    )

    return merged


def calculate_weighted_climate(merged):
    """Calculate area-weighted monthly climate values for each glacier."""

    merged["weighted_t2m"] = (
        merged["area_weight"] * merged["t2m"]
    )

    merged["weighted_tp"] = (
        merged["area_weight"] * merged["tp"]
    )

    glacier_monthly = (
        merged.groupby(
            ["rgi_id", "time"],
            as_index=False,
        )
        .agg(
            t2m=("weighted_t2m", "sum"),
            tp=("weighted_tp", "sum"),
            climate_coverage=("climate_coverage", "first"),
            coverage_status=("coverage_status", "first"),
        )
    )

    return glacier_monthly


def run_qa(glacier_monthly):
    """Run quality-control checks on glacier-level climate data."""

    expected_glaciers = 834
    expected_months = 12
    expected_records = expected_glaciers * expected_months

    print("\nGlacier-climate integration QA:")

    print(
        "Unique glaciers:",
        glacier_monthly["rgi_id"].nunique(),
    )

    print(
        "Unique months:",
        glacier_monthly["time"].nunique(),
    )

    print(
        "Total glacier-month records:",
        len(glacier_monthly),
    )

    print(
        "Expected glacier-month records:",
        expected_records,
    )

    print(
        "Missing temperature values:",
        glacier_monthly["t2m"].isna().sum(),
    )

    print(
        "Missing precipitation values:",
        glacier_monthly["tp"].isna().sum(),
    )

    print("\nArea-weighted temperature statistics:")
    print(glacier_monthly["t2m"].describe())

    print("\nArea-weighted precipitation statistics:")
    print(glacier_monthly["tp"].describe())


def save_outputs(glacier_monthly):
    """Save glacier-level monthly climate data as CSV and Zarr."""

    OUTPUT_CSV_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    glacier_monthly.to_csv(
        OUTPUT_CSV_PATH,
        index=False,
    )

    glacier_dataset = (
        glacier_monthly[
            ["rgi_id", "time", "t2m", "tp", "climate_coverage"]
        ]
        .set_index(["rgi_id", "time"])
        .to_xarray()
    )

    glacier_dataset.attrs.update(
        {
            "title": "Area-weighted monthly glacier climate dataset",
            "study_area": "Upper Rhone - Swiss Alps",
            "year": 2024,
            "temporal_resolution": "monthly",
            "temperature_variable": "ERA5-Land 2 m temperature",
            "temperature_units": "degree Celsius",
            "precipitation_variable": "ERA5-Land total precipitation",
            "precipitation_units": "mm",
            "spatial_aggregation": (
                "glacier-grid intersection area weighting"
            ),
            "source": "ECMWF ERA5-Land ARCO",
        }
    )

    glacier_dataset.to_zarr(
        OUTPUT_ZARR_PATH,
        mode="w",
        zarr_format=2,
    )

    print("\nSaved glacier monthly climate CSV to:")
    print(OUTPUT_CSV_PATH)

    print("\nSaved glacier monthly climate Zarr to:")
    print(OUTPUT_ZARR_PATH)


def main():
    print("Loading local climate and glacier-weight datasets...")

    climate_cube, climate_grid, weights = load_inputs()

    print("Converting climate cube to tabular form...")
    climate_df = climate_cube_to_dataframe(
        climate_cube,
        climate_grid,
    )

    print("Attaching climate values to glacier-grid intersections...")
    merged = attach_climate_to_weights(
        weights,
        climate_df,
    )

    print("Calculating area-weighted glacier climate...")
    glacier_monthly = calculate_weighted_climate(
        merged
    )

    run_qa(glacier_monthly)

    save_outputs(glacier_monthly)


if __name__ == "__main__":
    main()