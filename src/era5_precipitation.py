"""Process ERA5-Land precipitation data for the study area."""

import os
from pathlib import Path

import xarray as xr
from obstore.store import HTTPStore
from zarr.storage import ObjectStore

from config import STUDY_AREA, CLIMATE_BUFFER_DEGREES


ERA5_LAND_PRECIPITATION_URL = (
    "https://arco.datastores.ecmwf.int/"
    "cadl-arco-geo-009/arco/"
    "reanalysis_era5_land/"
    "sfc-pressure-precipitation/"
    "geoChunked.zarr"
)

START_TIME = "2024-01-01T00:00:00"
END_TIME = "2024-12-31T23:00:00"

OUTPUT_PATH = Path(
    "data/processed/era5_land_precipitation_monthly_2024.zarr"
)


west = STUDY_AREA["west"] - CLIMATE_BUFFER_DEGREES
east = STUDY_AREA["east"] + CLIMATE_BUFFER_DEGREES
south = STUDY_AREA["south"] - CLIMATE_BUFFER_DEGREES
north = STUDY_AREA["north"] + CLIMATE_BUFFER_DEGREES

def open_precipitation_dataset():
    """Open the ERA5-Land precipitation ARCO Zarr store."""

    api_key = os.environ.get("CDSAPIKEY")

    if not api_key:
        raise RuntimeError(
            "CDSAPIKEY environment variable is not set."
        )

    http_store = HTTPStore(
        ERA5_LAND_PRECIPITATION_URL,
        client_options={
            "default_headers": {
                "Authorization": f"Bearer {api_key}"
            }
        },
    )

    store = ObjectStore(
        http_store,
        read_only=True,
    )

    dataset = xr.open_zarr(
        store,
        consolidated=True,
    )

    return dataset


def subset_precipitation(dataset):
    """Select total precipitation for the study area and analysis period."""

    subset = dataset["tp"].sel(
        time=slice(START_TIME, END_TIME),
        latitude=slice(
            south,
            north,
        ),
        longitude=slice(
            west,
            east,
        ),
    )
    print("\nClimate extraction extent:")
    print(
        {
            "west": west,
            "south": south,
            "east": east,
            "north": north,
        }
    )

    print("\nSelected latitude range:")
    print(
        float(subset.latitude.min()),
        float(subset.latitude.max()),
    )

    print("\nSelected longitude range:")
    print(
        float(subset.longitude.min()),
        float(subset.longitude.max()),
    )

    return subset


def convert_to_millimetres(precipitation):
    """Convert hourly precipitation from metres to millimetres."""

    precipitation_mm = precipitation * 1000.0

    precipitation_mm.attrs = precipitation.attrs.copy()
    precipitation_mm.attrs["units"] = "mm"
    precipitation_mm.attrs["long_name"] = "Hourly total precipitation"
    precipitation_mm.attrs[
        "processing"
    ] = "ERA5-Land ARCO hourly de-accumulated precipitation"

    return precipitation_mm


def print_hourly_qa(precipitation_mm):
    """Print quality-control statistics for hourly precipitation."""

    print("\nHourly precipitation statistics:")
    print(
        f"Minimum: {float(precipitation_mm.min()):.4f} mm"
    )
    print(
        f"Maximum: {float(precipitation_mm.max()):.2f} mm"
    )
    print(
        f"Mean: {float(precipitation_mm.mean()):.4f} mm"
    )

    negative_count = int(
        (precipitation_mm < 0).sum()
    )

    print(f"Negative values: {negative_count}")


def aggregate_monthly(precipitation_mm):
    """Calculate monthly accumulated precipitation."""

    monthly_precipitation = precipitation_mm.resample(
        time="MS"
    ).sum()

    monthly_precipitation.attrs = precipitation_mm.attrs.copy()
    monthly_precipitation.attrs[
        "aggregation"
    ] = "monthly sum of hourly ERA5-Land precipitation"

    return monthly_precipitation


def print_monthly_summary(monthly_precipitation):
    """Print spatially averaged monthly precipitation totals."""

    print("\nMonthly dataset dimensions:")
    print(monthly_precipitation.sizes)

    spatial_mean = monthly_precipitation.mean(
        dim=["latitude", "longitude"]
    )

    print("\nStudy-area monthly precipitation:")

    for time, value in zip(
        spatial_mean.time.values,
        spatial_mean.values,
    ):
        month = str(time)[:7]
        print(f"{month}: {float(value):.2f} mm")

    annual_total = spatial_mean.sum(dim="time")

    print(
        "\nStudy-area annual precipitation: "
        f"{float(annual_total):.2f} mm"
    )


def save_monthly_precipitation(monthly_precipitation):
    """Save monthly precipitation as a local Zarr dataset."""

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    dataset = monthly_precipitation.to_dataset(
        name="tp"
    )

    dataset.to_zarr(
        OUTPUT_PATH,
        mode="w",
        zarr_format=2,
    )

    print("\nSaved monthly precipitation to:")
    print(OUTPUT_PATH)


if __name__ == "__main__":
    ds = open_precipitation_dataset()

    try:
        print("\nSelecting ERA5-Land precipitation subset...")

        tp = subset_precipitation(ds)

        print("\nSubset dimensions:")
        print(tp.sizes)

        print("\nLoading the subset from the ARCO cloud store...")
        print("This is the only intentional cloud data read.")

        # Load once from the cloud.
        tp.load()

        print("\nERA5-Land precipitation subset loaded successfully.")

        # Everything below operates on data already held in memory.
        tp_mm = convert_to_millimetres(tp)

        print_hourly_qa(tp_mm)

        monthly_tp = aggregate_monthly(tp_mm)

        print_monthly_summary(monthly_tp)

        save_monthly_precipitation(monthly_tp)

    finally:
        ds.close()