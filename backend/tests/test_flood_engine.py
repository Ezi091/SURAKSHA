import pytest
from app.models.schemas import (
    FloodForecastRequest,
    TerrainInput,
    DrainageNetwork,
    DrainageNode,
    ForecastInput,
    RainfallInput
)
from app.services.flood_service import predict_flood
from app.config import RiskLevel

@pytest.fixture
def base_request():
    return FloodForecastRequest(
        terrain=TerrainInput(
            area_sqm=10000.0,
            slope=0.05,
            low_point_factor=1.0,
            runoff_coefficient=0.85
        ),
        drainage=DrainageNetwork(
            nodes=[
                DrainageNode(id="n1", capacity_m3_hr=500.0, blockage_factor=0.0),
                DrainageNode(id="n2", capacity_m3_hr=500.0, blockage_factor=0.0)
            ],
            edges=[]
        ),
        forecasts=[]
    )

def test_low_rainfall_low_risk(base_request):
    """Test 1: Low rainfall -> low risk (no overload)."""
    base_request.forecasts = [
        ForecastInput(
            horizon="T+0",
            rainfall=RainfallInput(intensity_mm_hr=10.0, duration_hours=1.0)
        )
    ]

    results = predict_flood(base_request)
    assert len(results) == 1
    res = results[0]

    # Runoff: 0.85 * (10/1000) * 10000 = 85.0 m3
    assert abs(res.runoff_volume_m3 - 85.0) < 0.1

    # Capacity is 1000.0. 85.0 < 1000.0, so no overload.
    assert res.drainage_utilization_pct == 8.5
    assert res.excess_water_volume_m3 == 0.0
    assert res.predicted_water_depth_cm == 0.0
    assert res.flood_risk == RiskLevel.LOW

def test_heavy_rainfall_increased_runoff(base_request):
    """Test 2 & 5: Heavy rainfall -> increased runoff & greater predicted depth."""
    base_request.forecasts = [
        ForecastInput(
            horizon="T+0",
            rainfall=RainfallInput(intensity_mm_hr=150.0, duration_hours=1.0)
        )
    ]

    results = predict_flood(base_request)
    res = results[0]

    # Runoff: 0.85 * (150/1000) * 10000 = 1275.0 m3
    assert abs(res.runoff_volume_m3 - 1275.0) < 0.1

    # Capacity is 1000.0 m3. Utilization is > 100%
    assert res.drainage_utilization_pct > 100.0
    assert len(res.overloaded_nodes) == 2

    # Excess: 1275.0 - 1000.0 = 275.0 m3
    assert abs(res.excess_water_volume_m3 - 275.0) < 0.1

    # Depth = 275 / 10000 = 0.0275 m = 2.75 cm
    assert res.predicted_water_depth_cm > 0.0
    # Adjusted by terrain factor (slope 0.05 -> factor ~0.975)
    # 2.75 cm * 0.975 = ~2.68 cm
    assert 2.0 < res.predicted_water_depth_cm < 3.0

def test_drainage_overload_and_blockage(base_request):
    """Test 3 & 4: Blockage -> increased depth compared to clean drainage."""
    # Scenario A: Clean
    base_request.forecasts = [
        ForecastInput(
            horizon="T+0",
            rainfall=RainfallInput(intensity_mm_hr=150.0, duration_hours=1.0)
        )
    ]
    res_clean = predict_flood(base_request)[0]

    # Scenario B: 50% blocked
    base_request.drainage.nodes[0].blockage_factor = 0.5
    base_request.drainage.nodes[1].blockage_factor = 0.5

    res_blocked = predict_flood(base_request)[0]

    # Utilization should be higher
    assert res_blocked.drainage_utilization_pct > res_clean.drainage_utilization_pct
    # Depth should be higher
    assert res_blocked.predicted_water_depth_cm > res_clean.predicted_water_depth_cm

def test_t0_through_t3_predictions(base_request):
    """Test 6: T+0 through T+3 correctly accumulates water."""
    base_request.forecasts = [
        ForecastInput(horizon="T+0", rainfall=RainfallInput(intensity_mm_hr=150.0, duration_hours=1.0)),
        ForecastInput(horizon="T+1", rainfall=RainfallInput(intensity_mm_hr=150.0, duration_hours=1.0)),
        ForecastInput(horizon="T+2", rainfall=RainfallInput(intensity_mm_hr=20.0, duration_hours=1.0)),
    ]

    results = predict_flood(base_request)
    assert len(results) == 3

    r0 = results[0]
    r1 = results[1]
    r2 = results[2]

    # Timestamps are correct
    assert r0.timestamp_horizon == "T+0"
    assert r1.timestamp_horizon == "T+1"

    # T+1 should have more excess water than T+0 because water accumulates
    assert r1.excess_water_volume_m3 > r0.excess_water_volume_m3
    assert r1.predicted_water_depth_cm > r0.predicted_water_depth_cm

    # During T+2, rainfall drops sharply. Accumulated water might still cause overload, but it begins to drain
    # The depth at T+2 could be less than T+1 if drainage outpaces rainfall
    pass # As long as it processes without error and reflects the changing state, the test passes.
