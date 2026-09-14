"""Authenticated access utilities for Copernicus Data Space."""

from getpass import getpass
import numpy as np
import rasterio
import requests
import boto3
import s3fs
import time
from rasterio.windows import from_bounds

from rasterio.session import AWSSession
from pathlib import Path
from rasterio.windows import from_bounds

TOKEN_URL = (
    "https://identity.dataspace.copernicus.eu/"
    "auth/realms/CDSE/protocol/openid-connect/token"
)

S3_KEYS_URL = (
    "https://s3-keys-manager.cloudferro.com/api/user/credentials"
)

S3_ENDPOINT = "eodata.dataspace.copernicus.eu"

TEST_COG_PATH = (
    "eodata/auxdata/CopDEM_COG/copernicus-dem-30m/"
    "Copernicus_DSM_COG_10_N46_00_E008_00_DEM/"
    "Copernicus_DSM_COG_10_N46_00_E008_00_DEM.tif"
)

def get_access_token():
    """Request a temporary CDSE access token."""

    username = input("CDSE username: ")
    password = getpass("CDSE password: ")

    data = {
        "client_id": "cdse-public",
        "grant_type": "password",
        "username": username,
        "password": password,
    }

    response = requests.post(
        TOKEN_URL,
        data=data,
        timeout=60,
    )

    if response.status_code != 200:
        print(f"Authentication failed: HTTP {response.status_code}")
        print(response.text)
        return None

    token_data = response.json()

    print("Authentication successful.")

    return token_data["access_token"]


def create_s3_credentials(access_token):
    """Create temporary S3 credentials."""

    headers = {
        "Authorization": f"Bearer {access_token}",
    }

    response = requests.post(
        S3_KEYS_URL,
        headers=headers,
        timeout=60,
    )

    if response.status_code not in (200, 201):
        print(f"S3 credential creation failed: HTTP {response.status_code}")
        print(response.text)
        return None

    credentials = response.json()

    print("Temporary S3 credentials created.")

    return credentials
'''
def inspect_cog(credentials):
    """Open a remote Copernicus DEM COG and inspect its metadata."""

    print("\nOpening remote COG...")

    boto_session = boto3.Session(
        aws_access_key_id=credentials["access_id"],
        aws_secret_access_key=credentials["secret"],
        region_name="default",
    )

    rasterio_session = AWSSession(
        boto_session,
        endpoint_url="https://eodata.dataspace.copernicus.eu",
        aws_unsigned=False,
    )

    with rasterio.Env(
        session=rasterio_session,
        AWS_VIRTUAL_HOSTING=False,
        GDAL_DISABLE_READDIR_ON_OPEN="EMPTY_DIR",
        CPL_VSIL_CURL_ALLOWED_EXTENSIONS=".tif",
    ):
        with rasterio.open(TEST_COG_PATH) as dataset:
            print("COG opened successfully.")
            print(f"Driver: {dataset.driver}")
            print(f"CRS: {dataset.crs}")
            print(f"Width: {dataset.width}")
            print(f"Height: {dataset.height}")
            print(f"Bounds: {dataset.bounds}")
            print(f"Resolution: {dataset.res}")
            print(f"Data type: {dataset.dtypes}")
            print(f"NoData: {dataset.nodata}")
'''

def inspect_cog(credentials):
    """Open a remote Copernicus DEM COG using an S3 filesystem opener."""

    print("\nOpening remote COG...")

    fs = s3fs.S3FileSystem(
        key=credentials["access_id"],
        secret=credentials["secret"],
        client_kwargs={
            "endpoint_url": "https://eodata.dataspace.copernicus.eu"
        },
    )

    object_path = (
        "eodata/auxdata/CopDEM_COG/copernicus-dem-30m/"
        "Copernicus_DSM_COG_10_N45_00_E008_00_DEM/"
        "Copernicus_DSM_COG_10_N45_00_E008_00_DEM.tif"
    )

    with rasterio.open(
        object_path,
        opener=fs,
    ) as dataset:
        print("COG opened successfully.")
        print(f"Driver: {dataset.driver}")
        print(f"CRS: {dataset.crs}")
        print(f"Width: {dataset.width}")
        print(f"Height: {dataset.height}")
        print(f"Bounds: {dataset.bounds}")
        print(f"Resolution: {dataset.res}")
        print(f"Data type: {dataset.dtypes}")
        print(f"NoData: {dataset.nodata}")


def read_dem_window(credentials):
    """Read and save a small elevation window from Copernicus DEM."""

    fs = s3fs.S3FileSystem(
        key=credentials["access_id"],
        secret=credentials["secret"],
        client_kwargs={
            "endpoint_url": "https://eodata.dataspace.copernicus.eu"
        },
    )

    west = 8.10
    south = 46.10
    east = 8.20
    north = 46.20

    print("\nReading a real DEM window...")
    print(f"Bounds: {west}, {south}, {east}, {north}")

    with rasterio.open(
        TEST_COG_PATH,
        opener=fs,
    ) as dataset:

        window = from_bounds(
            west,
            south,
            east,
            north,
            transform=dataset.transform,
        )

        elevation = dataset.read(
            1,
            window=window,
            masked=True,
        )

        window_transform = dataset.window_transform(window)

        print(f"Window shape: {elevation.shape}")

        valid = elevation.compressed()
        valid = valid[np.isfinite(valid)]

        print(f"Valid pixels: {valid.size}")

        if valid.size > 0:
            print(f"Minimum elevation: {valid.min():.2f} m")
            print(f"Maximum elevation: {valid.max():.2f} m")
            print(f"Mean elevation: {valid.mean():.2f} m")

        output_path = Path(
            "data/processed/dem_test_window.tif"
        )

        output_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        output_data = elevation.filled(np.nan).astype(
            "float32"
        )

        profile = dataset.profile.copy()

        profile.update(
            driver="GTiff",
            height=output_data.shape[0],
            width=output_data.shape[1],
            count=1,
            dtype="float32",
            transform=window_transform,
            nodata=np.nan,
            compress="deflate",
        )

        with rasterio.open(
            output_path,
            "w",
            **profile,
        ) as output:
            output.write(output_data, 1)

    print(f"Saved DEM window to: {output_path}")

    return output_path
    

def delete_s3_credentials(access_token, access_id):
    """Delete temporary Copernicus S3 credentials."""

    headers = {
        "Authorization": f"Bearer {access_token}",
    }

    url = f"{S3_KEYS_URL}/access_id/{access_id}"

    response = requests.delete(
        url,
        headers=headers,
        timeout=60,
    )

    if response.status_code == 204:
        print("Temporary S3 credentials deleted.")
        return

    print(
        f"Warning: S3 credential cleanup failed "
        f"with HTTP {response.status_code}."
    )


if __name__ == "__main__":
    token = get_access_token()

    credentials = None

    try:
        credentials = create_s3_credentials(token)

        print("\nWaiting for S3 credentials to become active...")
        time.sleep(5)

        inspect_cog(credentials)

        read_dem_window(credentials)

    finally:
        if credentials is not None:
            print("\nCleaning up temporary S3 credentials...")

            delete_s3_credentials(
                token,
                credentials["access_id"],
            )