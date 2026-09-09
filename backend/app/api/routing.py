"""
Safe Routing API Endpoint

POST /api/routing/safe-route
Calculates flood-safe alternative routes
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional
from app.services.routing_service import RoutingService, create_demo_network

# Initialize demo network
demo_network = create_demo_network()
routing_service = RoutingService(demo_network)

router = APIRouter()


class SafeRouteRequest(BaseModel):
    """Request for safe route calculation"""
    origin: str = Field(..., description="Start node ID (e.g., 'n1')")
    destination: str = Field(..., description="End node ID (e.g., 'n5')")
    depth_threshold_cm: float = Field(15.0, description="Maximum water depth threshold in cm")


class RouteInfo(BaseModel):
    """Information about a calculated route"""
    origin: str
    destination: str
    distance_km: float
    segment_ids: List[str]
    risk_levels: List[str]
    water_depths: List[float]
    max_water_depth_cm: float
    has_high_risk: bool


class SafeRouteResponse(BaseModel):
    """Response with normal and safe routes"""
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
    Calculate flood-safe alternative routing.

    Takes origin and destination nodes, computes:
    1. Normal shortest route (ignoring flood risk)
    2. Safe route (avoiding HIGH/SEVERE risk roads)

    Returns both routes with comparison metrics.

    Demo Network:
    - Nodes: n1, n2, n3, n4, n5
    - Example: origin='n1', destination='n5'
    """
    try:
        result = routing_service.calculate_safe_route(
            origin=request.origin,
            destination=request.destination,
            depth_threshold_cm=request.depth_threshold_cm
        )

        if 'error' in result:
            raise HTTPException(status_code=404, detail=result['error'])

        return SafeRouteResponse(**result)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Routing error: {str(e)}")


@router.get("/demo-network")
async def get_demo_network():
    """
    Get information about the demo road network.

    Returns all nodes and segments for visualization and testing.
    """
    nodes = list(demo_network.adjacency.keys())

    segments = [
        {
            'id': seg.id,
            'start_node': seg.start_node,
            'end_node': seg.end_node,
            'distance_km': seg.distance_km,
            'risk_level': seg.risk_level.value,
            'water_depth_cm': seg.water_depth_cm
        }
        for seg in demo_network.segments.values()
    ]

    return {
        'nodes': nodes,
        'segments': segments,
        'total_segments': len(segments)
    }
