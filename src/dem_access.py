"""Authenticated access utilities for Copernicus Data Space."""

from getpass import getpass

import rasterio
import requests
import boto3
import s3fs

from rasterio.session import AWSSession


TOKEN_URL = (
    "https://identity.dataspace.copernicus.eu/"
    "auth/realms/CDSE/protocol/openid-connect/token"
)

S3_KEYS_URL = (
    "https://s3-keys-manager.cloudferro.com/api/user/credentials"
)

S3_ENDPOINT = "eodata.dataspace.copernicus.eu"

TEST_COG_PATH = (
    "s3://eodata/auxdata/CopDEM_COG/copernicus-dem-30m/"
    "Copernicus_DSM_COG_10_N45_00_E008_00_DEM/"
    "Copernicus_DSM_COG_10_N45_00_E008_00_DEM.tif"
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

if __name__ == "__main__":
    token = get_access_token()

    if token:
        credentials = create_s3_credentials(token)

        if credentials:
            inspect_cog(credentials)