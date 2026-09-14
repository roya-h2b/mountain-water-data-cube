from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import rasterio


DEM_PATH = Path("data/processed/dem_test_window.tif")
OUTPUT_PATH = Path("outputs/figures/dem_test_window.png")


def main():
    """Create a quick-look elevation map from the processed DEM."""

    with rasterio.open(DEM_PATH) as dataset:
        elevation = dataset.read(1)

    valid = elevation[np.isfinite(elevation)]

    print(f"Minimum elevation: {valid.min():.2f} m")
    print(f"Maximum elevation: {valid.max():.2f} m")
    print(f"Mean elevation: {valid.mean():.2f} m")

    vmin = np.percentile(valid, 2)
    vmax = np.percentile(valid, 98)

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    fig, ax = plt.subplots(figsize=(8, 7))

    image = ax.imshow(
        elevation,
        vmin=vmin,
        vmax=vmax,
    )

    ax.set_title("Copernicus DEM – Test Window")
    ax.set_xlabel("Column")
    ax.set_ylabel("Row")

    colorbar = fig.colorbar(
        image,
        ax=ax,
    )

    colorbar.set_label("Elevation (m)")

    plt.tight_layout()

    plt.savefig(
        OUTPUT_PATH,
        dpi=200,
        bbox_inches="tight",
    )

    plt.show()

    print(f"Figure saved to: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()