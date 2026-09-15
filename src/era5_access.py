"""Test access to the ERA5-Land ARCO Zarr dataset."""

import os

import xarray as xr
import zarr
from obstore.store import HTTPStore


ERA5_LAND_ZARR_URL = (
    "https://arco.datastores.ecmwf.int/"
    "cadl-arco-geo-007/arco/"
    "reanalysis_era5_land/"
    "sfc-2m-temperature/"
    "geoChunked.zarr"
)


def open_era5_land():
    """Open the ERA5-Land 2m-temperature ARCO Zarr store."""

    api_key = os.environ.get("CDSAPIKEY")

    if not api_key:
        raise RuntimeError(
            "CDSAPIKEY environment variable is not set."
        )

    store = HTTPStore(
        ERA5_LAND_ZARR_URL,
        client_options={
            "default_headers": {
                "Authorization": f"Bearer {api_key}"
            }
        },
    )

    zarr_store = zarr.storage.ObjectStore(store)

    dataset = xr.open_zarr(
        zarr_store,
        consolidated=True,
    )

    return dataset


def inspect_dataset(dataset):
    """Print basic ERA5-Land dataset metadata."""

    print("\nERA5-Land dataset opened successfully.")

    print("\nDimensions:")
    print(dataset.sizes)

    print("\nCoordinates:")
    print(list(dataset.coords))

    print("\nData variables:")
    print(list(dataset.data_vars))

    print("\nDataset:")
    print(dataset)


if __name__ == "__main__":
    ds = open_era5_land()

    try:
        inspect_dataset(ds)
    finally:
        ds.close()