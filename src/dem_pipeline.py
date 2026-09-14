"""Build a study-area DEM from remote Copernicus DEM COG tiles."""

from contextlib import ExitStack
from pathlib import Path
import time

import numpy as np
import rasterio
import s3fs

from rasterio.merge import merge

from config import STUDY_AREA
from dem_access import (
    create_s3_credentials,
    delete_s3_credentials,
    get_access_token,
)
from dem_discovery import search_dem_tiles


OUTPUT_PATH = Path("data/processed/study_area_dem.tif")


def create_s3_filesystem(credentials):
    """Create an authenticated S3 filesystem."""

    return s3fs.S3FileSystem(
        key=credentials["access_id"],
        secret=credentials["secret"],
        client_kwargs={
            "endpoint_url": "https://eodata.dataspace.copernicus.eu"
        },
    )


def get_dem_paths(features):
    """Extract S3 object paths from STAC DEM features."""

    paths = []

    for feature in features:
        href = feature["assets"]["data"]["href"]

        if href.startswith("s3://"):
            href = href[5:]

        paths.append(href)

    return paths


def build_dem_mosaic(features, credentials):
    """Read remote DEM tiles and create a study-area mosaic."""

    fs = create_s3_filesystem(credentials)

    paths = get_dem_paths(features)

    bounds = (
        STUDY_AREA["west"],
        STUDY_AREA["south"],
        STUDY_AREA["east"],
        STUDY_AREA["north"],
    )

    print("\nOpening remote DEM tiles...")

    start = time.perf_counter()

    with ExitStack() as stack:
        datasets = []

        for path in paths:
            print(f"Opening: {Path(path).name}")

            dataset = stack.enter_context(
                rasterio.open(
                    path,
                    opener=fs,
                )
            )

            datasets.append(dataset)

        elapsed = time.perf_counter() - start

        print(
            f"Opened {len(datasets)} DEM tiles "
            f"in {elapsed:.1f} seconds."
        )

        print("\nBuilding study-area DEM mosaic...")

        start = time.perf_counter()

        mosaic, transform = merge(
            datasets,
            bounds=bounds,
            nodata=np.nan,
            dtype="float32",
        )

        elapsed = time.perf_counter() - start

        print(
            f"Mosaic created in {elapsed:.1f} seconds."
        )

        profile = datasets[0].profile.copy()

    return mosaic, transform, profile


def save_dem(mosaic, transform, profile):
    """Save the study-area DEM as a compressed GeoTIFF."""

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    profile.update(
        driver="GTiff",
        height=mosaic.shape[1],
        width=mosaic.shape[2],
        count=1,
        dtype="float32",
        transform=transform,
        nodata=np.nan,
        compress="deflate",
        tiled=True,
    )

    print("\nSaving study-area DEM...")

    start = time.perf_counter()

    with rasterio.open(
        OUTPUT_PATH,
        "w",
        **profile,
    ) as dataset:
        dataset.write(mosaic[0], 1)

    elapsed = time.perf_counter() - start

    print(
        f"DEM saved in {elapsed:.1f} seconds."
    )

    print(f"Output: {OUTPUT_PATH}")


def print_dem_statistics(mosaic):
    """Print basic DEM quality-control statistics."""

    elevation = mosaic[0]

    valid = elevation[np.isfinite(elevation)]

    print("\nDEM statistics:")
    print(f"Shape: {elevation.shape}")
    print(f"Valid pixels: {valid.size}")

    if valid.size > 0:
        print(
            f"Minimum elevation: "
            f"{valid.min():.2f} m"
        )
        print(
            f"Maximum elevation: "
            f"{valid.max():.2f} m"
        )
        print(
            f"Mean elevation: "
            f"{valid.mean():.2f} m"
        )


def main():
    """Run the Copernicus DEM processing workflow."""

    print("Discovering Copernicus DEM tiles...")

    features = search_dem_tiles()

    if not features:
        raise RuntimeError(
            "No Copernicus DEM tiles were found."
        )

    token = get_access_token()

    credentials = None

    try:
        credentials = create_s3_credentials(token)

        print(
            "\nWaiting for temporary S3 "
            "credentials to become active..."
        )

        time.sleep(5)

        mosaic, transform, profile = build_dem_mosaic(
            features,
            credentials,
        )

        print_dem_statistics(mosaic)

        save_dem(
            mosaic,
            transform,
            profile,
        )

    finally:
        if credentials is not None:
            print(
                "\nCleaning up temporary "
                "S3 credentials..."
            )

            delete_s3_credentials(
                token,
                credentials["access_id"],
            )


if __name__ == "__main__":
    main()