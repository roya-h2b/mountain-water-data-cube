from pathlib import Path

import geopandas as gpd
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.colors import TwoSlopeNorm


GLACIERS_PATH = Path(
    "data/processed/glaciers_with_dem_stats.geojson"
)

CLIMATE_PATH = Path(
    "data/processed/glacier_climate_monthly_2024.csv"
)

OUTPUT_PATH = Path(
    "outputs/figures/glacier_mean_temperature_2024.png"
)


def load_data():
    """Load glacier geometries and glacier-level monthly climate data."""

    glaciers = gpd.read_file(GLACIERS_PATH)
    climate = pd.read_csv(
        CLIMATE_PATH,
        parse_dates=["time"],
    )

    return glaciers, climate


def calculate_annual_temperature(climate):
    """Calculate day-weighted mean temperature for each glacier."""

    climate = climate.copy()

    climate["days_in_month"] = climate["time"].dt.days_in_month

    climate["weighted_t2m"] = (
        climate["t2m"] * climate["days_in_month"]
    )

    annual_temperature = (
        climate.groupby("rgi_id")
        .apply(
            lambda group: (
                group["weighted_t2m"].sum()
                / group["days_in_month"].sum()
            ),
            include_groups=False,
        )
        .rename("mean_t2m_c")
        .reset_index()
    )

    return annual_temperature


def join_glacier_geometry(glaciers, annual_temperature):
    """Join annual climate statistics to glacier geometries."""

    glacier_map = glaciers.merge(
        annual_temperature,
        on="rgi_id",
        how="left",
        validate="one_to_one",
    )

    return glacier_map


def run_qa(glacier_map):
    """Print quality-control information for the mapped dataset."""

    print("\nVisualization QA:")
    print("Total glaciers:", len(glacier_map))

    print(
        "Glaciers with temperature:",
        glacier_map["mean_t2m_c"].notna().sum(),
    )

    print(
        "Glaciers without temperature:",
        glacier_map["mean_t2m_c"].isna().sum(),
    )

    print("\nAnnual mean temperature statistics:")
    print(glacier_map["mean_t2m_c"].describe())


def create_temperature_map(glacier_map):
    """Create a map of glacier-level mean annual temperature."""

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    fig, ax = plt.subplots(
        figsize=(10, 8)
    )
    
    norm = TwoSlopeNorm(
        vmin=glacier_map["mean_t2m_c"].min(),
        vcenter=0,
        vmax=glacier_map["mean_t2m_c"].max(),
    )

    glacier_map.plot(
        column="mean_t2m_c",
        cmap="coolwarm",
        norm=norm,
        linewidth=0.25,
        edgecolor="black",
        legend=True,
        legend_kwds={
            "label": "Mean 2 m temperature (°C)",
            "shrink": 0.75,
        },
        ax=ax,
    )

    ax.set_title(
        "Area-Weighted ERA5-Land Temperature by Glacier — 2024",
        fontsize=14,
    )

    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")

    ax.grid(
        alpha=0.2,
        linewidth=0.5,
    )

    fig.tight_layout()

    fig.savefig(
        OUTPUT_PATH,
        dpi=300,
        bbox_inches="tight",
    )

    plt.close(fig)

    print("\nSaved temperature map to:")
    print(OUTPUT_PATH)


def main():
    print("Loading glacier and climate datasets...")

    glaciers, climate = load_data()

    print("Calculating annual glacier temperature...")
    annual_temperature = calculate_annual_temperature(
        climate
    )

    print("Joining climate statistics to glacier geometries...")
    glacier_map = join_glacier_geometry(
        glaciers,
        annual_temperature,
    )

    run_qa(glacier_map)

    print("Creating glacier temperature map...")
    create_temperature_map(glacier_map)


if __name__ == "__main__":
    main()