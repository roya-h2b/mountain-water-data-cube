from pathlib import Path

import geopandas as gpd
import matplotlib.pyplot as plt
import pandas as pd


GLACIERS_PATH = Path(
    "data/processed/glaciers_with_dem_stats.geojson"
)

CLIMATE_PATH = Path(
    "data/processed/glacier_climate_monthly_2024.csv"
)

TEMPERATURE_OUTPUT_PATH = Path(
    "outputs/figures/largest_glacier_temperature_2024.png"
)

PRECIPITATION_OUTPUT_PATH = Path(
    "outputs/figures/largest_glacier_precipitation_2024.png"
)


def load_data():
    """Load glacier attributes and monthly glacier climate data."""

    glaciers = gpd.read_file(GLACIERS_PATH)

    climate = pd.read_csv(
        CLIMATE_PATH,
        parse_dates=["time"],
    )

    return glaciers, climate


def select_largest_glacier(glaciers):
    """Select the largest glacier using the RGI area attribute."""

    largest_glacier = glaciers.loc[
        glaciers["area_km2"].idxmax()
    ]

    return largest_glacier


def extract_glacier_timeseries(climate, rgi_id):
    """Extract and sort monthly climate data for one glacier."""

    glacier_climate = (
        climate.loc[
            climate["rgi_id"] == rgi_id
        ]
        .sort_values("time")
        .copy()
    )

    return glacier_climate


def run_qa(largest_glacier, glacier_climate):
    """Print quality-control information for the selected glacier."""

    print("\nSelected glacier:")
    print("RGI ID:", largest_glacier["rgi_id"])
    print("Name:", largest_glacier["glac_name"])
    print(
        "Area:",
        f"{largest_glacier['area_km2']:.2f} km²",
    )

    print("\nTime-series QA:")
    print("Number of months:", len(glacier_climate))

    print(
        "Missing temperature values:",
        glacier_climate["t2m"].isna().sum(),
    )

    print(
        "Missing precipitation values:",
        glacier_climate["tp"].isna().sum(),
    )

    print("\nMonthly climate data:")
    print(
        glacier_climate[
            ["time", "t2m", "tp"]
        ].to_string(index=False)
    )


def create_temperature_plot(glacier_climate, rgi_id):
    """Create monthly temperature time-series plot."""

    TEMPERATURE_OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    fig, ax = plt.subplots(figsize=(10, 5))

    ax.plot(
        glacier_climate["time"],
        glacier_climate["t2m"],
        marker="o",
        linewidth=2,
    )

    ax.axhline(
        0,
        linewidth=1,
        linestyle="--",
    )

    ax.set_title(
        f"Monthly Area-Weighted Temperature — {rgi_id}"
    )

    ax.set_xlabel("Month")
    ax.set_ylabel("2 m temperature (°C)")

    ax.grid(
        alpha=0.25,
        linewidth=0.5,
    )

    fig.autofmt_xdate()
    fig.tight_layout()

    fig.savefig(
        TEMPERATURE_OUTPUT_PATH,
        dpi=300,
        bbox_inches="tight",
    )

    plt.close(fig)

    print("\nSaved temperature time series to:")
    print(TEMPERATURE_OUTPUT_PATH)


def create_precipitation_plot(glacier_climate, rgi_id):
    """Create monthly precipitation plot."""

    fig, ax = plt.subplots(figsize=(10, 5))

    ax.bar(
        glacier_climate["time"],
        glacier_climate["tp"],
        width=20,
    )

    ax.set_title(
        f"Monthly Area-Weighted Precipitation — {rgi_id}"
    )

    ax.set_xlabel("Month")
    ax.set_ylabel("Total precipitation (mm)")

    ax.grid(
        axis="y",
        alpha=0.25,
        linewidth=0.5,
    )

    fig.autofmt_xdate()
    fig.tight_layout()

    fig.savefig(
        PRECIPITATION_OUTPUT_PATH,
        dpi=300,
        bbox_inches="tight",
    )

    plt.close(fig)

    print("\nSaved precipitation time series to:")
    print(PRECIPITATION_OUTPUT_PATH)


def main():
    print("Loading glacier and climate datasets...")

    glaciers, climate = load_data()

    largest_glacier = select_largest_glacier(
        glaciers
    )

    glacier_climate = extract_glacier_timeseries(
        climate,
        largest_glacier["rgi_id"],
    )

    run_qa(
        largest_glacier,
        glacier_climate,
    )

    create_temperature_plot(
        glacier_climate,
        largest_glacier["rgi_id"],
    )

    create_precipitation_plot(
        glacier_climate,
        largest_glacier["rgi_id"],
    )


if __name__ == "__main__":
    main()