"""QA check for glaciers outside the current ERA5-Land climate grid."""

from pathlib import Path

import geopandas as gpd
from shapely.geometry import box


GLACIER_PATH = Path(
    "data/processed/glaciers_with_dem_stats.geojson"
)

CLIMATE_GRID_PATH = Path(
    "data/processed/era5_land_grid.geojson"
)

WEIGHTS_PATH = Path(
    "data/processed/glacier_climate_weights.geojson"
)

STUDY_BBOX = {
    "west": 7.5,
    "south": 46.0,
    "east": 8.5,
    "north": 46.7,
}


def main():
    """Check why some selected glaciers do not intersect the climate grid."""

    glaciers = gpd.read_file(GLACIER_PATH)
    climate_grid = gpd.read_file(CLIMATE_GRID_PATH)
    weights = gpd.read_file(WEIGHTS_PATH)

    glaciers = glaciers.to_crs("EPSG:4326")
    climate_grid = climate_grid.to_crs("EPSG:4326")

    study_bbox = box(
        STUDY_BBOX["west"],
        STUDY_BBOX["south"],
        STUDY_BBOX["east"],
        STUDY_BBOX["north"],
    )

    represented_ids = set(weights["rgi_id"].unique())

    outside = glaciers[
        ~glaciers["rgi_id"].isin(represented_ids)
    ].copy()

    print("\nTotal glaciers:")
    print(len(glaciers))

    print("\nGlaciers represented in climate weights:")
    print(len(represented_ids))

    print("\nGlaciers outside current climate grid:")
    print(len(outside))

    outside["intersects_original_bbox"] = (
        outside.geometry.intersects(study_bbox)
    )

    print("\nDo outside glaciers intersect the original study bbox?")
    print(outside["intersects_original_bbox"].value_counts())

    climate_bounds = climate_grid.total_bounds

    print("\nOriginal study bbox:")
    print(
        [
            STUDY_BBOX["west"],
            STUDY_BBOX["south"],
            STUDY_BBOX["east"],
            STUDY_BBOX["north"],
        ]
    )

    print("\nCurrent climate-grid bounds:")
    print(climate_bounds)

    outside["min_lon"] = outside.geometry.bounds["minx"]
    outside["min_lat"] = outside.geometry.bounds["miny"]
    outside["max_lon"] = outside.geometry.bounds["maxx"]
    outside["max_lat"] = outside.geometry.bounds["maxy"]

    print("\nBounds of glaciers outside the climate grid:")
    print(
        outside[
            [
                "rgi_id",
                "min_lon",
                "min_lat",
                "max_lon",
                "max_lat",
                "intersects_original_bbox",
            ]
        ].to_string(index=False)
    )

    failed_bbox_test = outside[
        ~outside["intersects_original_bbox"]
    ]

    print("\nOutside glaciers that DO NOT intersect the original bbox:")
    print(len(failed_bbox_test))

    if not failed_bbox_test.empty:
        print(
            failed_bbox_test[
                [
                    "rgi_id",
                    "min_lon",
                    "min_lat",
                    "max_lon",
                    "max_lat",
                ]
            ].to_string(index=False)
        )


if __name__ == "__main__":
    main()