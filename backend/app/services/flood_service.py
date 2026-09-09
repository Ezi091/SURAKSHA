"""
Flood Service

Orchestrates the entire flood prediction pipeline.
Combines runoff, terrain, and drainage to predict final water depth and risk.

Pipeline:
1. Rainfall -> Runoff estimation
2. Terrain influence -> Modified accumulation
3. Drainage -> Capacity check and excess water
4. Excess water -> Depth estimation
5. Depth -> Risk classification

Assumptions:
- Depth is calculated as uniform spread over the area (simplified)
- Real systems would use ponding geometry of local depressions

Outputs form the core intelligence of the SURAKSHA system.
"""

from typing import List
from app.config import FloodConstants, RiskLevel
from app.models.schemas import (
    FloodForecastRequest,
    ForecastResult,
    ForecastInput,
    TerrainInput
)
from app.services.runoff_service import calculate_runoff_volume
from app.services.terrain_service import calculate_terrain_accumulation_factor
from app.services.drainage_service import process_drainage

def determine_flood_risk(depth_cm: float) -> RiskLevel:
    """Classify flood risk based on predicted depth."""
    if depth_cm < FloodConstants.DEPTH_THRESHOLD_LOW:
        return RiskLevel.LOW
    elif depth_cm < FloodConstants.DEPTH_THRESHOLD_MODERATE:
        return RiskLevel.MODERATE
    elif depth_cm < FloodConstants.DEPTH_THRESHOLD_HIGH:
        return RiskLevel.HIGH
    else:
        return RiskLevel.SEVERE

def calculate_water_depth(excess_volume_m3: float, area_sqm: float, terrain_factor: float) -> float:
    """
    Convert excess volume into a predicted water depth.

    Args:
        excess_volume_m3: Volume of water that didn't drain
        area_sqm: Area of coverage
        terrain_factor: Terrain influence modifier

    Returns:
        Predicted depth in centimeters
    """
    if area_sqm <= 0:
        return 0.0

    # Base depth in meters (uniform spread)
    base_depth_m = excess_volume_m3 / area_sqm

    # Apply terrain modification (e.g. pooling in depressions)
    modified_depth_m = base_depth_m * terrain_factor

    # Convert to cm
    depth_cm = modified_depth_m * 100.0

    return depth_cm

def predict_flood(request: FloodForecastRequest) -> List[ForecastResult]:
    """
    Execute the flood forecasting pipeline for multiple time horizons.

    We process horizons sequentially to accumulate water over time.
    """
    results = []

    # State variable for accumulated water across horizons
    accumulated_excess_water_m3 = 0.0

    for forecast in request.forecasts:
        # 1. Runoff estimation
        runoff_volume = calculate_runoff_volume(forecast.rainfall, request.terrain)

        # 2. Terrain influence
        terrain_factor = calculate_terrain_accumulation_factor(request.terrain)

        # 3. Drainage processing
        # Inflow includes current runoff + any water left from previous timestep
        total_inflow_m3_hr = (runoff_volume + accumulated_excess_water_m3) / forecast.rainfall.duration_hours

        excess_water_m3_hr, node_results, overloaded_nodes = process_drainage(
            request.drainage,
            total_inflow_m3_hr
        )

        # Total excess water for this timestep
        excess_volume = excess_water_m3_hr * forecast.rainfall.duration_hours

        # Update accumulated state for next timestep
        accumulated_excess_water_m3 = excess_volume

        # 4. Depth estimation
        depth_cm = calculate_water_depth(
            excess_volume,
            request.terrain.area_sqm,
            terrain_factor
        )

        # 5. Risk classification
        risk = determine_flood_risk(depth_cm)

        # Build result
        # Calculate utilization as peak utilization across nodes (simplified)
        utilization = max([n.utilization_pct for n in node_results]) if node_results else 0.0

        result = ForecastResult(
            timestamp_horizon=forecast.horizon,
            rainfall_intensity=forecast.rainfall.intensity_mm_hr,
            runoff_volume_m3=runoff_volume,
            drainage_utilization_pct=utilization,
            overloaded_nodes=overloaded_nodes,
            excess_water_volume_m3=excess_volume,
            predicted_water_depth_cm=depth_cm,
            flood_risk=risk.value,
            node_results=node_results
        )

        results.append(result)

    return results
