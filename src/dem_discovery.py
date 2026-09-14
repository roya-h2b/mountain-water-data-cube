"""Discover Copernicus DEM GLO-30 tiles for the study area."""

import requests

from config import STUDY_AREA


STAC_SEARCH_URL = "https://stac.dataspace.copernicus.eu/v1/search"
DEM_COLLECTION = "cop-dem-glo-30-dged-cog"


def search_dem_tiles():
    """Find Copernicus DEM GLO-30 tiles intersecting the study area."""

    bbox = [
        STUDY_AREA["west"],
        STUDY_AREA["south"],
        STUDY_AREA["east"],
        STUDY_AREA["north"],
    ]

    payload = {
        "collections": [DEM_COLLECTION],
        "bbox": bbox,
        "limit": 100,
    }

    print("Searching Copernicus STAC catalogue...")
    print(f"Collection: {DEM_COLLECTION}")
    print(f"BBOX: {bbox}")

    response = requests.post(
        STAC_SEARCH_URL,
        json=payload,
        timeout=60,
    )

    response.raise_for_status()
    
    

    #data = response.json()
    features = response.json()["features"]

    print(f"\nDEM tiles found: {len(features)}")

    for feature in features:
        print(f"  - {feature['id']}")
    return features
    
    
    
def print_first_tile_metadata(features):

    """Print metadata for the first discovered DEM tile."""

    if not features:
        return

    first = features[0]

    print("\nFirst tile metadata:")
    print(f"ID: {first['id']}")

    print("\nAvailable assets:")

    for asset_name, asset_info in first.get("assets", {}).items():
        print(f"  - {asset_name}")
        print(f"    href: {asset_info.get('href')}")
        print(f"    type: {asset_info.get('type')}")



if __name__ == "__main__":
    features = search_dem_tiles()
    print_first_tile_metadata(features)