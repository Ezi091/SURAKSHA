from pydantic import BaseModel, Field
from typing import List

class RainfallInput(BaseModel):
    intensity_mm_hr: float = Field(..., description="Rainfall intensity in mm/hr")
    duration_hours: float = Field(1.0, description="Duration of this rainfall period in hours")

class TerrainInput(BaseModel):
    area_sqm: float = Field(10000.0, description="Area of the region in square meters")
    slope: float = Field(0.05, description="Average terrain slope (0.0 flat to 1.0 steep)")
    low_point_factor: float = Field(1.0, description="1.0 is neutral. >1.0 means more pooling occurs in this area.")
    runoff_coefficient: float = Field(0.85, description="0.0 to 1.0 (Rational method coefficient)")

class DrainageNode(BaseModel):
    id: str = Field(..., description="Unique drainage node ID")
    capacity_m3_hr: float = Field(..., description="Maximum extraction volume per hour")
    blockage_factor: float = Field(0.0, description="0.0 (clean) to 1.0 (fully blocked)")

class DrainageEdge(BaseModel):
    from_node: str
    to_node: str
    capacity_m3_hr: float

class DrainageNetwork(BaseModel):
    nodes: List[DrainageNode]
    edges: List[DrainageEdge]

class ForecastInput(BaseModel):
    horizon: str = Field(..., description="e.g. T+0, T+1")
    rainfall: RainfallInput

class FloodForecastRequest(BaseModel):
    terrain: TerrainInput
    drainage: DrainageNetwork
    forecasts: List[ForecastInput] = Field(..., description="List of rainfall predictions over time")

# --- Outputs ---

class NodeResult(BaseModel):
    id: str
    effective_capacity: float
    utilization_pct: float
    is_overloaded: bool

class ForecastResult(BaseModel):
    timestamp_horizon: str
    rainfall_intensity: float
    runoff_volume_m3: float
    drainage_utilization_pct: float
    overloaded_nodes: List[str]
    excess_water_volume_m3: float
    predicted_water_depth_cm: float
    flood_risk: str
    node_results: List[NodeResult]

class FloodForecastResponse(BaseModel):
    predictions: List[ForecastResult]
