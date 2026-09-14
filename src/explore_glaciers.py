"""Exploratory analysis of glacier and DEM data."""

from pathlib import Path

import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
from scipy.stats import linregress

DATA_PATH = Path(
    "data/processed/glaciers_with_dem_stats.geojson"
)

OUTPUT_DIR = Path("outputs/figures")


def plot_dem_vs_rgi(glaciers):
    """Compare RGI and Copernicus mean glacier elevations."""

    full = glaciers[
        glaciers["dem_coverage"] == "full"
    ].copy()

    x = full["zmean_m"]
    y = full["dem_mean_m"]

    minimum = min(x.min(), y.min())
    maximum = max(x.max(), y.max())

    fig, ax = plt.subplots(figsize=(7, 7))

    ax.scatter(
        x,
        y,
        alpha=0.5,
        s=18,
    )

    ax.plot(
        [minimum, maximum],
        [minimum, maximum],
        linestyle="--",
        linewidth=1.5,
        label="1:1 line",
    )

    ax.set_xlabel("RGI Mean Elevation (m)")
    ax.set_ylabel("Copernicus DEM Mean Elevation (m)")
    ax.set_title(
        "Glacier Mean Elevation: Copernicus DEM vs RGI"
    )

    ax.legend()

    ax.set_aspect(
        "equal",
        adjustable="box",
    )

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_path = OUTPUT_DIR / "dem_vs_rgi_mean_elevation.png"

    plt.tight_layout()

    plt.savefig(
        output_path,
        dpi=200,
        bbox_inches="tight",
    )

    plt.show()

    print(f"Figure saved to: {output_path}")


def calculate_validation_metrics(glaciers):
    """Calculate validation metrics between RGI and Copernicus elevations."""

    full = glaciers[
        glaciers["dem_coverage"] == "full"
    ].copy()

    observed = full["zmean_m"].to_numpy()
    estimated = full["dem_mean_m"].to_numpy()

    errors = estimated - observed

    bias = np.mean(errors)
    mae = np.mean(np.abs(errors))
    rmse = np.sqrt(np.mean(errors ** 2))
    correlation = np.corrcoef(observed, estimated)[0, 1]

    print("\nValidation metrics:")
    print(f"Glaciers: {len(full)}")
    print(f"Bias: {bias:.2f} m")
    print(f"MAE: {mae:.2f} m")
    print(f"RMSE: {rmse:.2f} m")
    print(f"Pearson correlation: {correlation:.4f}")


def plot_area_vs_relief(glaciers):
    """Explore the relationship between glacier area and vertical relief."""

    full = glaciers[
        glaciers["dem_coverage"] == "full"
    ].copy()
    
    valid = full[
        (full["area_km2"] > 0)
        & full["area_km2"].notna()
        & full["dem_relief_m"].notna()
    ].copy()

    log_area = np.log10(valid["area_km2"])

    regression = linregress(
        log_area,
        valid["dem_relief_m"],
    )

    area_range = np.logspace(
        np.log10(valid["area_km2"].min()),
        np.log10(valid["area_km2"].max()),
        200,
    )

    predicted_relief = (
        regression.intercept
        + regression.slope * np.log10(area_range)
    )

    fig, ax = plt.subplots(figsize=(8, 6))

    ax.scatter(
        full["area_km2"],
        full["dem_relief_m"],
        alpha=0.5,
        s=20,
    )
    
    ax.plot(
        area_range,
        predicted_relief,
        linewidth=2,
        label=(
            f"Log-area regression "
            f"(R² = {regression.rvalue ** 2:.2f})"
        ),
    )

    ax.legend()

    ax.set_xscale("log")

    ax.set_xlabel("Glacier Area (km²)")
    ax.set_ylabel("Vertical Relief (m)")
    ax.set_title("Glacier Area vs Vertical Relief")

    plt.tight_layout()

    output_path = OUTPUT_DIR / "glacier_area_vs_relief.png"

    plt.savefig(
        output_path,
        dpi=200,
        bbox_inches="tight",
    )

    plt.show()

    print(f"Figure saved to: {output_path}")


def analyze_area_relief_relationship(glaciers):
    """Analyze the relationship between glacier area and vertical relief."""

    full = glaciers[
        glaciers["dem_coverage"] == "full"
    ].copy()

    valid = full[
        (full["area_km2"] > 0)
        & full["area_km2"].notna()
        & full["dem_relief_m"].notna()
    ].copy()

    area = valid["area_km2"]
    log_area = np.log10(area)
    relief = valid["dem_relief_m"]

    pearson_raw = area.corr(
        relief,
        method="pearson",
    )

    pearson_log = log_area.corr(
        relief,
        method="pearson",
    )

    spearman = area.corr(
        relief,
        method="spearman",
    )

    print("\nArea-relief relationship:")
    print(f"Glaciers: {len(valid)}")
    print(
        f"Pearson correlation (raw area): "
        f"{pearson_raw:.4f}"
    )
    print(
        f"Pearson correlation (log10 area): "
        f"{pearson_log:.4f}"
    )
    print(
        f"Spearman correlation: "
        f"{spearman:.4f}"
    )
    
    regression = linregress(
        log_area,
        relief,
    )

    print("\nLog-area linear regression:")
    print(
        f"Slope: {regression.slope:.2f} "
        "m per log10(km²)"
    )
    print(
        f"Intercept: {regression.intercept:.2f} m"
    )
    print(
        f"R²: {regression.rvalue ** 2:.4f}"
    )
    print(
        f"p-value: {regression.pvalue:.3e}"
    )
    
    

def main():
    """Run exploratory glacier analysis."""

    glaciers = gpd.read_file(DATA_PATH)

    print(f"Glaciers loaded: {len(glaciers)}")

    calculate_validation_metrics(glaciers)

    plot_dem_vs_rgi(glaciers)
    
    plot_area_vs_relief(glaciers)
    analyze_area_relief_relationship(glaciers)

if __name__ == "__main__":
    main()