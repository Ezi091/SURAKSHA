"""
DEM API Endpoints

Provides HTTP endpoints for DEM queries and terrain information.
"""

import logging
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from pydantic import BaseModel
from app.services.dem_service import (
    get_dem_loader,
    get_terrain_at_location,
    get_terrain_batch,
    DEMMetadata,
    TerrainPoint
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/dem", tags=["dem"])


class TerrainPointResponse(BaseModel):
    """Response model for terrain point data."""
    latitude: float
    longitude: float
    elevation_m: float
    slope_degrees: float
    low_point_factor: float
    valid: bool
    reason: Optional[str] = None


class DEMMetadataResponse(BaseModel):
    """Response model for DEM metadata."""
    file_path: str
    crs: Optional[str]
    bounds: tuple  # (left, bottom, right, top)
    width: int
    height: int
    resolution: tuple  # (pixel_width, pixel_height)
    nodata_value: Optional[float]
    min_elevation: float
    max_elevation: float


class DEMStatusResponse(BaseModel):
    """Response model for DEM status."""
    loaded: bool
    metadata: Optional[DEMMetadataResponse] = None
    message: str


@router.get("/status", response_model=DEMStatusResponse)
async def get_dem_status():
    """
    Get DEM loading status and metadata.

    Returns:
        DEM status including whether it's loaded and its metadata
    """
    loader = get_dem_loader()

    if loader.is_loaded():
        metadata = loader.get_metadata()
        return DEMStatusResponse(
            loaded=True,
            metadata=DEMMetadataResponse(
                file_path=metadata.file_path,
                crs=metadata.crs,
                bounds=metadata.bounds,
                width=metadata.width,
                height=metadata.height,
                resolution=metadata.resolution,
                nodata_value=metadata.nodata_value,
                min_elevation=metadata.min_elevation,
                max_elevation=metadata.max_elevation
            ),
            message="DEM loaded successfully"
        )
    else:
        return DEMStatusResponse(
            loaded=False,
            message="DEM not available. Using simplified terrain model."
        )


@router.get("/terrain", response_model=TerrainPointResponse)
async def get_terrain(
    latitude: float = Query(..., ge=-90, le=90, description="Latitude in degrees"),
    longitude: float = Query(..., ge=-180, le=180, description="Longitude in degrees")
):
    """
    Get terrain information at a specific location.

    Uses real DEM if available, falls back to simplified model.

    Args:
        latitude: Location latitude (-90 to 90)
        longitude: Location longitude (-180 to 180)

    Returns:
        Terrain information including elevation, slope, and accumulation factor
    """
    point = get_terrain_at_location(latitude, longitude)

    return TerrainPointResponse(
        latitude=point.latitude,
        longitude=point.longitude,
        elevation_m=point.elevation_m,
        slope_degrees=point.slope_degrees,
        low_point_factor=point.low_point_factor,
        valid=point.valid,
        reason=point.reason
    )


class BatchTerrainRequest(BaseModel):
    """Request model for batch terrain queries."""
    locations: List[tuple]  # List of (latitude, longitude) tuples


@router.post("/terrain/batch")
async def get_terrain_batch_endpoint(request: BatchTerrainRequest):
    """
    Get terrain information for multiple locations.

    Args:
        request: BatchTerrainRequest with list of (lat, lon) tuples

    Returns:
        List of terrain points
    """
    if not request.locations:
        raise HTTPException(status_code=400, detail="locations list cannot be empty")

    if len(request.locations) > 100:
        raise HTTPException(status_code=400, detail="Maximum 100 locations allowed per request")

    points = get_terrain_batch(request.locations)

    return {
        "locations_count": len(points),
        "terrain_points": [
            TerrainPointResponse(
                latitude=p.latitude,
                longitude=p.longitude,
                elevation_m=p.elevation_m,
                slope_degrees=p.slope_degrees,
                low_point_factor=p.low_point_factor,
                valid=p.valid,
                reason=p.reason
            )
            for p in points
        ]
    }


@router.get("/bounds")
async def get_dem_bounds():
    """
    Get the geographic bounds of the loaded DEM.

    Returns:
        DEM bounds as (left, bottom, right, top) or null if not loaded
    """
    loader = get_dem_loader()

    if loader.is_loaded():
        metadata = loader.get_metadata()
        return {
            "bounds": metadata.bounds,
            "crs": metadata.crs,
            "description": f"DEM covers ({metadata.bounds[0]:.4f}°W to {metadata.bounds[2]:.4f}°E, "
                           f"{metadata.bounds[1]:.4f}°S to {metadata.bounds[3]:.4f}°N)"
        }
    else:
        return {
            "bounds": None,
            "crs": None,
            "description": "DEM not loaded"
        }


@router.get("/elevation")
async def get_elevation(
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180)
):
    """
    Get elevation at a specific location.

    Args:
        latitude: Location latitude
        longitude: Location longitude

    Returns:
        Elevation in meters, or null if unavailable
    """
    loader = get_dem_loader()
    elevation = loader.get_elevation(latitude, longitude)

    return {
        "latitude": latitude,
        "longitude": longitude,
        "elevation_m": elevation,
        "available": elevation is not None
    }
