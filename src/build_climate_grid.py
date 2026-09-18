"""Build ERA5-Land grid-cell polygons from the local climate data cube."""

from pathlib import Path

import geopandas as gpd
import xarray as xr
from shapely.geometry import box


CLIMATE_CUBE_PATH = Path(
    "data/processed/era5_land_climate_cube_2024.zarr"
)

OUTPUT_PATH = Path(
    "data/processed/era5_land_grid.geojson"
)

CELL_SIZE = 0.1
HALF_CELL = CELL_SIZE / 2


def open_climate_cube():
    """Open the locally stored ERA5-Land climate data cube."""

    return xr.open_zarr(CLIMATE_CUBE_PATH)


def build_grid_polygons(dataset):
    """Create polygons representing ERA5-Land grid cells."""

    latitudes = dataset["latitude"].values
    longitudes = dataset["longitude"].values

    records = []

    cell_id = 0

    for latitude in latitudes:
        for longitude in longitudes:

            geometry = box(
                longitude - HALF_CELL,
                latitude - HALF_CELL,
                longitude + HALF_CELL,
                latitude + HALF_CELL,
            )

            records.append(
                {
                    "cell_id": cell_id,
                    "latitude": float(latitude),
                    "longitude": float(longitude),
                    "geometry": geometry,
                }
            )

            cell_id += 1

    grid = gpd.GeoDataFrame(
        records,
        geometry="geometry",
        crs="EPSG:4326",
    )

    return grid


def validate_grid(grid):
    """Print basic grid quality-control information."""

    print("\nNumber of ERA5-Land grid cells:")
    print(len(grid))

    print("\nCRS:")
    print(grid.crs)

    print("\nGrid bounds:")
    print(grid.total_bounds)

    print("\nFirst five cells:")
    print(
        grid[
            [
                "cell_id",
                "latitude",
                "longitude",
            ]
        ].head()
    )


def save_grid(grid):
    """Save ERA5-Land grid polygons as GeoJSON."""

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    grid.to_file(
        OUTPUT_PATH,
        driver="GeoJSON",
    )

    print("\nSaved ERA5-Land grid to:")
    print(OUTPUT_PATH)


if __name__ == "__main__":
    ds = open_climate_cube()

    try:
        climate_grid = build_grid_polygons(ds)

        validate_grid(climate_grid)

        save_grid(climate_grid)

    finally:
        ds.close()