from fastapi import APIRouter
from app.models.schemas import FloodForecastRequest, FloodForecastResponse
from app.services.flood_service import predict_flood

router = APIRouter()

@router.post("/predict", response_model=FloodForecastResponse)
async def predict_flood_endpoint(request: FloodForecastRequest):
    """
    Run the SURAKSHA physics-inspired flood prediction pipeline.

    Inputs:
    - Terrain features (area, slope, lowest-point factor)
    - Drainage Network (capacities, blockage)
    - Rainfall forecasts for multiple horizons (T+0, T+1, etc.)

    Returns:
    - Predicted water depth (cm)
    - Flood risk classification
    - Intermediate values (runoff, drainage utilization)
    """
    predictions = predict_flood(request)
    return FloodForecastResponse(predictions=predictions)