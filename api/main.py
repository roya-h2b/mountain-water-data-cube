from fastapi import FastAPI, HTTPException
from pathlib import Path
import pandas as pd
from fastapi.responses import FileResponse, JSONResponse

from fastapi.staticfiles import StaticFiles

import json

import geopandas as gpd
from fastapi import FastAPI

app = FastAPI(
    title="Mountain Water Data Cube API",
    description=(
        "API for accessing glacier, terrain, and "
        "ERA5-Land climate data."
    ),
    version="0.1.0",
)


app.mount(
    "/ui-static",
    StaticFiles(directory="ui"),
    name="ui-static",
)

GLACIERS_PATH = Path(
    "data/processed/glaciers_with_dem_stats.geojson"
)

CLIMATE_PATH = Path(
    "data/processed/glacier_climate_monthly_2024.csv"
)


def load_glaciers():
    """Load glacier attributes used by the API."""

    glaciers = gpd.read_file(GLACIERS_PATH)

    return glaciers


@app.get("/")
def root():
    """Return basic API information."""

    return {
        "name": "Mountain Water Data Cube API",
        "version": "0.1.0",
        "status": "running",
    }


@app.get("/health")
def health():
    """Return API health status."""

    return {
        "status": "healthy",
    }
 


@app.get("/ui", response_class=FileResponse)
def user_interface():
    """Serve the glacier climate user interface."""
    return FileResponse("ui/index.html")

 
@app.get("/glaciers")
def get_glaciers():
    """Return a summary of all glaciers in the study dataset."""

    glaciers = load_glaciers()

    columns = [
        "rgi_id",
        "glac_name",
        "area_km2",
        "dem_mean_m",
        "dem_relief_m",
    ]

    records = (
        glaciers[columns]
        .where(glaciers[columns].notna(), None)
        .to_dict(orient="records")
    )

    return {
        "count": len(records),
        "glaciers": records,
    }
    
 
@app.get("/glaciers/geojson")
def get_glaciers_geojson():
    """Return glacier geometries and selected attributes as GeoJSON."""

    glaciers = load_glaciers()

    columns = [
        "rgi_id",
        "glac_name",
        "area_km2",
        "dem_mean_m",
        "dem_relief_m",
        "geometry",
    ]

    glacier_map = glaciers[columns].copy()

    return JSONResponse(
        content=json.loads(glacier_map.to_json())
    )

 
@app.get("/glaciers/{rgi_id}")
def get_glacier(rgi_id: str):
    """Return information for one glacier."""

    glaciers = load_glaciers()

    glacier = glaciers.loc[
        glaciers["rgi_id"] == rgi_id
    ]

    if glacier.empty:
        raise HTTPException(
            status_code=404,
            detail=f"Glacier not found: {rgi_id}",
        )

    columns = [
        "rgi_id",
        "glac_name",
        "area_km2",
        "dem_min_m",
        "dem_max_m",
        "dem_mean_m",
        "dem_relief_m",
        "dem_coverage",
    ]

    record = (
        glacier[columns]
        .where(glacier[columns].notna(), None)
        .iloc[0]
        .to_dict()
    )

    return record
    
@app.get("/glaciers/{rgi_id}/climate")
def get_glacier_climate(rgi_id: str):
    """Return monthly climate data for one glacier."""

    climate = pd.read_csv(
        CLIMATE_PATH,
        parse_dates=["time"],
    )

    glacier_climate = (
        climate.loc[
            climate["rgi_id"] == rgi_id
        ]
        .sort_values("time")
        .copy()
    )

    if glacier_climate.empty:
        raise HTTPException(
            status_code=404,
            detail=f"Climate data not found: {rgi_id}",
        )
    monthly_data = []

    for _, row in glacier_climate.iterrows():
        monthly_data.append(
            {
                "month": row["time"].strftime("%Y-%m"),
                "temperature_c": float(row["t2m"]),
                "precipitation_mm": float(row["tp"]),
            }
        )

    return {
        "rgi_id": rgi_id,
        "year": 2024,
        "temporal_resolution": "monthly",
        "spatial_aggregation": (
            "glacier-grid intersection area weighting"
        ),
        "climate": monthly_data,
    }
    
    
