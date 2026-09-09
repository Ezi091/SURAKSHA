"""
Runoff Service

Implements the Rational Method for estimating stormwater runoff.

Q = C * i * A

Where:
- Q = Peak runoff rate (cubic meters per hour in our case)
- C = Runoff coefficient (dimensionless, 0 to 1)
- i = Rainfall intensity (mm/hr converted to meters)
- A = Drainage area (square meters)

For accumulated volume over time:
V = Q * duration

Assumptions:
- Uniform rainfall over the area
- Steady-state conditions during the event
- Coefficient represents imperviousness and infiltration losses
- No detailed soil moisture accounting

This is a simplified approach suitable for urban flood estimation.

NOTE: Historical BRIMSTOWAD (1993) reference indicates 25 mm/hr at low tide
as the old SWD system design capacity. The PDF does not provide node-level
capacities; this figure is a system-level historical calibration parameter,
not a per-drain capacity value. Node-level blockage/siltation/runoff adjustments
remain configurable model assumptions.
Real systems would include infiltration models, antecedent moisture, and spatial variation.
"""

from app.models.schemas import RainfallInput, TerrainInput

def calculate_runoff_volume(rainfall: RainfallInput, terrain: TerrainInput) -> float:
    """
    Calculate total runoff volume in cubic meters.

    Args:
        rainfall: Rainfall intensity and duration
        terrain: Area and runoff coefficient

    Returns:
        Volume of runoff in cubic meters
    """
    # Convert mm/hr to meters
    intensity_m_hr = rainfall.intensity_mm_hr / 1000.0

    # Rational Method: Q = C * i * A
    runoff_rate_m3_hr = terrain.runoff_coefficient * intensity_m_hr * terrain.area_sqm

    # Total volume over duration
    volume_m3 = runoff_rate_m3_hr * rainfall.duration_hours

    return volume_m3
