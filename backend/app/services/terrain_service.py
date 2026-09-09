"""
Terrain Service

Provides terrain influence factors for flood accumulation.

Integrates real DEM (Digital Elevation Model) data when available,
with fallback to simplified model for testing and demo scenarios.

In a real system, this analyzes:
- Digital Elevation Model (DEM)
- Flow direction
- Flow accumulation
- Slope
- Depression storage

Implementation:
- When DEM is loaded: uses real elevation, slope, and low-point factors
- When DEM unavailable: uses simplified factors for backward compatibility
"""

import logging
from typing import Optional, Tuple, List
from app.models.schemas import TerrainInput

logger = logging.getLogger(__name__)

# Try to import DEM service, but allow graceful fallback if numpy/rasterio unavailable
try:
    from app.services.dem_service import get_terrain_at_location, get_terrain_batch
    DEM_AVAILABLE = True
except ImportError:
    DEM_AVAILABLE = False


def calculate_terrain_accumulation_factor(terrain: TerrainInput) -> float:
    """
    Calculate how terrain influences water accumulation.

    Returns a multiplier:
    - < 1.0: terrain helps drainage (steep slope)
    - = 1.0: neutral
    - > 1.0: terrain increases accumulation (flat/depression)

    Args:
        terrain: Terrain characteristics (with optional lat/lon for DEM lookup)

    Returns:
        Accumulation factor (dimensionless)
    """
    # If DEM service available and location provided, try to use real data
    if DEM_AVAILABLE and hasattr(terrain, 'latitude') and hasattr(terrain, 'longitude') and \
       terrain.latitude is not None and terrain.longitude is not None:
        try:
            terrain_point = get_terrain_at_location(terrain.latitude, terrain.longitude)

            if terrain_point.valid:
                # Use real DEM slope and low-point factor
                slope_factor = 1.0 - (terrain_point.slope_degrees / 90.0) * 0.5
                slope_factor = max(0.5, min(1.5, slope_factor))
                accumulation_factor = slope_factor * terrain_point.low_point_factor

                logger.debug(
                    f"Using real DEM data at ({terrain.latitude}, {terrain.longitude}): "
                    f"elevation={terrain_point.elevation_m:.1f}m, slope={terrain_point.slope_degrees:.1f}°, "
                    f"factor={accumulation_factor:.3f}"
                )
                return accumulation_factor
        except Exception as e:
            logger.debug(f"DEM lookup failed, falling back to simplified model: {e}")

    # Fallback to simplified model
    slope_factor = 1.0 - (terrain.slope * 0.5)  # slope 0 -> 1.0, slope 1 -> 0.5
    slope_factor = max(0.5, min(1.5, slope_factor))  # Clamp to reasonable range

    # Apply low point factor (depressions, bowls)
    accumulation_factor = slope_factor * terrain.low_point_factor

    # Clamp final result to valid range
    accumulation_factor = max(0.5, min(1.5, accumulation_factor))

    return accumulation_factor


def get_terrain_characteristics(
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    default_slope: float = 0.02,
    default_low_point_factor: float = 0.5
) -> Tuple[float, float, float]:
    """
    Get terrain characteristics at a location.

    Uses real DEM if available, falls back to simplified defaults.

    Args:
        latitude: Location latitude (optional)
        longitude: Location longitude (optional)
        default_slope: Default slope if DEM unavailable (0-1)
        default_low_point_factor: Default accumulation factor (0-1)

    Returns:
        Tuple of (elevation_m, slope_normalized, low_point_factor)
    """
    if DEM_AVAILABLE and latitude is not None and longitude is not None:
        try:
            terrain_point = get_terrain_at_location(latitude, longitude)

            if terrain_point.valid:
                # Normalize slope to 0-1 range
                slope_normalized = min(terrain_point.slope_degrees / 90.0, 1.0)
                return (
                    terrain_point.elevation_m,
                    slope_normalized,
                    terrain_point.low_point_factor
                )
        except Exception as e:
            logger.debug(f"DEM lookup failed, using defaults: {e}")

    # Fallback
    return (100.0, default_slope, default_low_point_factor)


def get_batch_terrain_characteristics(
    locations: List[Tuple[float, float]],
    default_slope: float = 0.02,
    default_low_point_factor: float = 0.5
) -> List[Tuple[float, float, float]]:
    """
    Get terrain characteristics for multiple locations.

    Args:
        locations: List of (latitude, longitude) tuples
        default_slope: Default slope if DEM unavailable
        default_low_point_factor: Default accumulation factor

    Returns:
        List of (elevation_m, slope_normalized, low_point_factor) tuples
    """
    if not DEM_AVAILABLE:
        # Return defaults for all locations
        return [(100.0, default_slope, default_low_point_factor) for _ in locations]

    results = []
    for lat, lon in locations:
        try:
            terrain_point = get_terrain_at_location(lat, lon)

            if terrain_point.valid:
                slope_normalized = min(terrain_point.slope_degrees / 90.0, 1.0)
                results.append((
                    terrain_point.elevation_m,
                    slope_normalized,
                    terrain_point.low_point_factor
                ))
            else:
                results.append((100.0, default_slope, default_low_point_factor))
        except Exception as e:
            logger.debug(f"DEM lookup failed for ({lat}, {lon}), using defaults: {e}")
            results.append((100.0, default_slope, default_low_point_factor))

    return results
