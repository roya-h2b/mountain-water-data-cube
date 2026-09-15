"""Process ERA5-Land temperature data for the study area."""

from pathlib import Path

from config import STUDY_AREA
from era5_access import open_era5_land


START_TIME = "2024-01-01T00:00:00"
END_TIME = "2024-12-31T23:00:00"

OUTPUT_PATH = Path(
    "data/processed/era5_land_temperature_monthly_2024.zarr"
)


def subset_temperature(dataset):
    """Select 2 m temperature for the study area and analysis period."""

    temperature = dataset["t2m"].sel(
        time=slice(START_TIME, END_TIME),
        latitude=slice(
            STUDY_AREA["south"],
            STUDY_AREA["north"],
        ),
        longitude=slice(
            STUDY_AREA["west"],
            STUDY_AREA["east"],
        ),
    )

    return temperature


def convert_to_celsius(temperature):
    """Convert temperature from Kelvin to degrees Celsius."""

    temperature_c = temperature - 273.15

    temperature_c.attrs = temperature.attrs.copy()
    temperature_c.attrs["units"] = "degC"
    temperature_c.attrs["long_name"] = "2 metre temperature"

    return temperature_c


def print_hourly_qa(temperature_c):
    """Print quality-control statistics for hourly temperature."""

    print("\nHourly temperature statistics:")
    print(f"Minimum: {float(temperature_c.min()):.2f} °C")
    print(f"Maximum: {float(temperature_c.max()):.2f} °C")
    print(f"Mean: {float(temperature_c.mean()):.2f} °C")


def aggregate_monthly(temperature_c):
    """Calculate monthly mean 2 m temperature."""

    monthly_temperature = temperature_c.resample(
        time="MS"
    ).mean()

    monthly_temperature.attrs = temperature_c.attrs.copy()
    monthly_temperature.attrs[
        "aggregation"
    ] = "monthly mean from hourly ERA5-Land data"

    return monthly_temperature


def print_monthly_summary(monthly_temperature):
    """Print spatially averaged monthly temperatures."""

    print("\nMonthly dataset dimensions:")
    print(monthly_temperature.sizes)

    spatial_mean = monthly_temperature.mean(
        dim=["latitude", "longitude"]
    )

    print("\nStudy-area monthly mean temperature:")

    for time, value in zip(
        spatial_mean.time.values,
        spatial_mean.values,
    ):
        month = str(time)[:7]
        print(f"{month}: {float(value):.2f} °C")


def save_monthly_temperature(monthly_temperature):
    """Save monthly temperature as a local Zarr dataset."""

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    dataset = monthly_temperature.to_dataset(name="t2m")

    dataset.to_zarr(
        OUTPUT_PATH,
        mode="w",
        zarr_format=2,
    )

    print(f"\nSaved monthly temperature to:")
    print(OUTPUT_PATH)


if __name__ == "__main__":
    ds = open_era5_land()

    try:
        print("\nSelecting ERA5-Land temperature subset...")

        t2m = subset_temperature(ds)

        print("\nSubset dimensions:")
        print(t2m.sizes)

        print("\nLoading the subset from the ARCO cloud store...")
        print("This is the only intentional cloud data read.")

        # Load once from the cloud.
        t2m.load()

        print("\nERA5-Land temperature subset loaded successfully.")

        # Everything below operates on data already held in memory.
        t2m_c = convert_to_celsius(t2m)

        print_hourly_qa(t2m_c)

        monthly_t2m = aggregate_monthly(t2m_c)

        print_monthly_summary(monthly_t2m)

        save_monthly_temperature(monthly_t2m)

    finally:
        ds.close()