"""Build a monthly ERA5-Land climate data cube."""

from pathlib import Path

import xarray as xr


TEMPERATURE_PATH = Path(
    "data/processed/era5_land_temperature_monthly_2024.zarr"
)

PRECIPITATION_PATH = Path(
    "data/processed/era5_land_precipitation_monthly_2024.zarr"
)

OUTPUT_PATH = Path(
    "data/processed/era5_land_climate_cube_2024.zarr"
)


def open_inputs():
    """Open locally processed ERA5-Land datasets."""

    temperature = xr.open_zarr(TEMPERATURE_PATH)
    precipitation = xr.open_zarr(PRECIPITATION_PATH)

    return temperature, precipitation


def validate_inputs(temperature, precipitation):
    """Validate dimensions and coordinates before merging."""

    print("\nTemperature dimensions:")
    print(temperature.sizes)

    print("\nPrecipitation dimensions:")
    print(precipitation.sizes)

    if not temperature["time"].equals(precipitation["time"]):
        raise ValueError("Time coordinates do not match.")

    if not temperature["latitude"].equals(
        precipitation["latitude"]
    ):
        raise ValueError("Latitude coordinates do not match.")

    if not temperature["longitude"].equals(
        precipitation["longitude"]
    ):
        raise ValueError("Longitude coordinates do not match.")

    print("\nInput coordinates match successfully.")


def build_climate_cube(temperature, precipitation):
    """Merge temperature and precipitation into one dataset."""

    climate_cube = xr.merge(
        [
            temperature[["t2m"]],
            precipitation[["tp"]],
        ],
        compat="no_conflicts",
        join="exact",
    )

    climate_cube.attrs = {
        "title": "ERA5-Land monthly climate data cube",
        "study_area": "Upper Rhone - Swiss Alps",
        "year": 2024,
        "temporal_resolution": "monthly",
        "spatial_resolution": "0.1 degree",
        "temperature_aggregation": "monthly mean",
        "precipitation_aggregation": "monthly sum",
        "source": "ECMWF ERA5-Land ARCO",
    }

    return climate_cube


def inspect_cube(climate_cube):
    """Print climate cube structure and metadata."""

    print("\nClimate data cube:")
    print(climate_cube)

    print("\nDimensions:")
    print(climate_cube.sizes)

    print("\nVariables:")
    print(list(climate_cube.data_vars))

    print("\nTemperature units:")
    print(climate_cube["t2m"].attrs.get("units"))

    print("\nPrecipitation units:")
    print(climate_cube["tp"].attrs.get("units"))


def save_cube(climate_cube):
    """Save the combined climate cube as Zarr."""

    climate_cube.to_zarr(
        OUTPUT_PATH,
        mode="w",
        zarr_format=2,
    )

    print("\nSaved climate data cube to:")
    print(OUTPUT_PATH)


if __name__ == "__main__":
    temperature_ds, precipitation_ds = open_inputs()

    try:
        validate_inputs(
            temperature_ds,
            precipitation_ds,
        )

        cube = build_climate_cube(
            temperature_ds,
            precipitation_ds,
        )

        inspect_cube(cube)

        save_cube(cube)

    finally:
        temperature_ds.close()
        precipitation_ds.close()