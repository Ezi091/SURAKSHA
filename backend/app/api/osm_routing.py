"""
OSM-based Routing API Endpoint

POST /api/routing/safe-route
Calculates flood-safe alternative routes using real OpenStreetMap data
"""

import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional

from app.services.osm_routing_service import OSMRoadNetwork, OSMRoutingService

logger = logging.getLogger(__name__)

# Initialize OSM network (load once at startup)
osm_network = OSMRoadNetwork()
osm_loaded = osm_network.load_from_geojson("data/roads/roads.geojson")

if osm_loaded:
    osm_routing_service = OSMRoutingService(osm_network)
    logger.info("OSM routing service initialized successfully")
else:
    osm_routing_service = None
    logger.error("Failed to initialize OSM routing service")

router = APIRouter()


class SafeRouteRequest(BaseModel):
    """Request for safe route calculation using coordinates."""
    origin_lat: float = Field(..., description="Origin latitude")
    origin_lon: float = Field(..., description="Origin longitude")
    destination_lat: float = Field(..., description="Destination latitude")
    destination_lon: float = Field(..., description="Destination longitude")
    depth_threshold_cm: float = Field(15.0, description="Maximum water depth threshold in cm")
    flood_zones: Optional[List[dict]] = Field(None, description="Flood zones from prediction")


class RouteGeometry(BaseModel):
    """Geometry for a route segment."""
    type: str = "LineString"
    coordinates: List[List[float]]


class RouteInfo(BaseModel):
    """Information about a calculated route."""
    origin: str
    destination: str
    origin_coords: List[float]  # [lat, lon]
    destination_coords: List[float]  # [lat, lon]
    distance_km: float
    segment_ids: List[str]
    risk_levels: List[str]
    water_depths: List[float]
    max_water_depth_cm: float
    has_high_risk: bool
    road_names: List[Optional[str]]
    geometry: List[List[List[float]]]  # List of LineString coordinates
    road_summary: str


class SafeRouteResponse(BaseModel):
    """Response with normal and safe routes."""
    normal_route: RouteInfo
    safe_route: RouteInfo
    needs_rerouting: bool
    distance_increase_km: float
    affected_segments: List[str] = Field(description="Segments in both normal and safe routes")
    avoided_segments: List[str] = Field(description="High/severe risk segments avoided in safe route")
    reason: str = Field(description="Explanation for rerouting decision")


@router.post("/safe-route", response_model=SafeRouteResponse)
async def calculate_safe_route(request: SafeRouteRequest):
    """
    Calculate flood-safe alternative routing using real OSM roads.

    Takes origin and destination coordinates, computes:
    1. Normal shortest route (ignoring flood risk)
    2. Safe route (avoiding HIGH/SEVERE risk roads)

    Returns both routes with comparison metrics and real road geometries.
    """
    if not osm_loaded or not osm_routing_service:
        raise HTTPException(
            status_code=503,
            detail="OSM road data not loaded. Check that data/roads/roads.geojson exists."
        )

    try:
        result = osm_routing_service.calculate_safe_route(
            origin_lat=request.origin_lat,
            origin_lon=request.origin_lon,
            dest_lat=request.destination_lat,
            dest_lon=request.destination_lon,
            depth_threshold_cm=request.depth_threshold_cm,
            flood_zones=request.flood_zones
        )

        if 'error' in result:
            raise HTTPException(status_code=404, detail=result['error'])

        return SafeRouteResponse(**result)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Routing error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Routing error: {str(e)}")


@router.get("/network-info")
async def get_network_info():
    """
    Get information about the loaded OSM road network.

    Returns summary statistics and status.
    """
    if not osm_loaded or not osm_network.loader:
        return {
            'loaded': False,
            'error': 'OSM road data not loaded'
        }

    summary = osm_network.loader.get_summary()
    summary['loaded'] = True

    return summary


@router.get("/landmarks")
async def get_landmarks():
    """
    Get recognizable landmarks/locations from the road network.

    Returns a list of named locations suitable for user selection.
    """
    if not osm_loaded or not osm_network.loader:
        raise HTTPException(
            status_code=503,
            detail="OSM road data not loaded"
        )

    # Extract unique named roads as landmarks
    landmarks = []
    seen_names = set()

    for feature in osm_network.loader.features:
        if feature.name and feature.name not in seen_names:
            # Use first coordinate as representative point
            if feature.coordinates:
                lat = feature.coordinates[0][1]
                lon = feature.coordinates[0][0]

                landmarks.append({
                    'name': feature.name,
                    'lat': lat,
                    'lon': lon,
                    'highway_type': feature.highway_type
                })

                seen_names.add(feature.name)

                # Limit to reasonable number
                if len(landmarks) >= 50:
                    break

    return {
        'total': len(landmarks),
        'landmarks': landmarks[:20]  # Return enough for new locations
    }
