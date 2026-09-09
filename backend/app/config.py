from enum import Enum

class RiskLevel(str, Enum):
    LOW = "LOW"
    MODERATE = "MODERATE"
    HIGH = "HIGH"
    SEVERE = "SEVERE"

class FloodConstants:
    """
    Configurable constants for the Hackathon MVP flood model.

    Depth thresholds calibrated for demo visibility and safe routing:
    - LOW: Safe for normal traffic
    - MODERATE: Caution advisable
    - HIGH: Most vehicles should avoid (typical 30cm blocks small cars)
    - SEVERE: Route avoidance mandatory (50cm+ blocks large vehicles)

    Based on BRIMSTOWAD (1993) system reference (25 mm/hr) and urban
    runoff coefficients. Synthetic demo network uses calibrated preset rainfall
    to achieve noticeable flooding for routing sensitivity testing.
    """
    # Depth thresholds in cm
    DEPTH_THRESHOLD_LOW = 10.0
    DEPTH_THRESHOLD_MODERATE = 20.0
    DEPTH_THRESHOLD_HIGH = 35.0

    # Runoff Defaults
    DEFAULT_RUNOFF_COEFFICIENT = 0.85  # Typical for dense urban area

    # Terrain defaults
    DEFAULT_SLOPE = 0.05
    DEFAULT_LOW_POINT_FACTOR = 1.2

    # Simple area constant for synthetic tests (sq meters)
    DEFAULT_AREA_SQM = 10000.0

    # --- Drainage calibration from BRIMSTOWAD (1993) historical report ---
    # OBSERVED/HISTORICAL from PDF (system-level design reference):
    HISTORICAL_REFERENCE_RAINFALL_MM_HR = 25.0  # System-level (low tide) reference only
    DEFAULT_DRAINAGE_BLOCKAGE_FACTOR = 0.15
    DEFAULT_DRAINAGE_SILTATION_FACTOR = 0.10
    DEFAULT_DRAINAGE_RUNOFF_ADJUSTMENT = 1.05