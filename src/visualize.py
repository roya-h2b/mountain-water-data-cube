"""Visualization utilities for glacier data."""

from pathlib import Path

import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np

DATA_PATH = Path("data/processed/glaciers_processed.geojson")
FIGURE_DIR = Path("outputs/figures")


def plot_glacier_map():
    """Create a map of glacier outlines in the study area."""

    glaciers = gpd.read_file(DATA_PATH)

    FIGURE_DIR.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(figsize=(9, 7))

    glaciers.plot(
        ax=ax,
        edgecolor="black",
        linewidth=0.3,
    )

    ax.set_title("RGI 7.0 Glaciers — Upper Rhône / Swiss Alps")
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")

    fig.tight_layout()

    output_path = FIGURE_DIR / "glacier_inventory_map.png"

    fig.savefig(
        output_path,
        dpi=300,
        bbox_inches="tight",
    )

    plt.close(fig)

    print(f"Map saved to: {output_path}")


def plot_area_distribution():
    """Plot the distribution of glacier areas."""

    glaciers = gpd.read_file(DATA_PATH)

    FIGURE_DIR.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(figsize=(8, 5))

    areas = glaciers["area_km2"].dropna()

    log_bins = np.logspace(
        np.log10(areas.min()),
        np.log10(areas.max()),
        30,
    )

    ax.hist(
        areas,
        bins=log_bins,
    )

    ax.set_xscale("log")
    ax.set_xlabel("Glacier area (km²)")
    ax.set_ylabel("Number of glaciers")
    ax.set_title("Glacier Area Distribution (Log-Spaced Bins)")

    fig.tight_layout()

    output_path = FIGURE_DIR / "glacier_area_distribution.png"

    fig.savefig(
        output_path,
        dpi=300,
        bbox_inches="tight",
    )

    plt.close(fig)

    print(f"Figure saved to: {output_path}")


if __name__ == "__main__":
    plot_glacier_map()
    plot_area_distribution()