"""
DEM (Digital Elevation Model) Service

Loads and provides access to real elevation data from GeoTIFF DEM files.
Integrates with the flood prediction system to provide real terrain factors.

Uses Rasterio for efficient geospatial raster access.
Provides caching and spatial query capabilities.
"""

import logging
import numpy as np
from pathlib import Path
from typing import Optional, Tuple, Dict, List
from dataclasses import dataclass

try:
    import rasterio
    from rasterio.coords import BoundingBox
    RASTERIO_AVAILABLE = True
except ImportError:
    RASTERIO_AVAILABLE = False

logger = logging.getLogger(__name__)


class PathString:
    """Wrapper that preserves the original string representation while acting like a Path."""
    def __init__(self, original_str: str):
        self.original_str = original_str
        self.path = Path(original_str)

    def __str__(self) -> str:
        return self.original_str

    def __fspath__(self) -> str:
        return str(self.path)

    def exists(self) -> bool:
        return self.path.exists()

    def __truediv__(self, other):
        return self.path / other

    def parent(self):
        return self.path.parent


@dataclass
class DEMMetadata:
    """Metadata about a loaded DEM."""
    file_path: str
    crs: Optional[str]
    bounds: Tuple[float, float, float, float]  # (left, bottom, right, top)
    width: int
    height: int
    resolution: Tuple[float, float]  # (pixel_width, pixel_height)
    nodata_value: Optional[float]
    min_elevation: float
    max_elevation: float


@dataclass
class TerrainPoint:
    """Terrain information at a single location."""
    latitude: float
    longitude: float
    elevation_m: float
    slope_degrees: float
    low_point_factor: float
    valid: bool
    reason: Optional[str] = None


class DEMLoader:
    """Loads and manages Digital Elevation Model data."""

    def __init__(self, dem_path: Optional[str] = None):
        if dem_path is None:
            # Resolve to project root: backend/app/services/dem_service.py -> SURAKSHA/data/terrain/dem.tif
            this_file = Path(__file__)  # backend/app/services/dem_service.py
            backend_dir = this_file.parent.parent.parent  # -> backend
            project_root = backend_dir.parent  # -> SURAKSHA
            self.dem_path = project_root / "data" / "terrain" / "dem.tif"
        else:
            self.dem_path = PathString(dem_path)

        self.metadata: Optional[DEMMetadata] = None
        self.raster = None
        self.elevation_cache: Dict[Tuple[float, float], float] = {}

    def load(self) -> bool:
        """
        Load DEM from GeoTIFF file.

        Returns:
            True if successful, False otherwise
        """
        if not RASTERIO_AVAILABLE:
            logger.error("Rasterio not available. Install with: pip install rasterio")
            return False

        if not self.dem_path.exists():
            logger.warning(f"DEM file not found: {self.dem_path}")
            return False

        try:
            # Open the raster
            src = rasterio.open(self.dem_path)

            # Extract metadata
            bounds = src.bounds
            self.metadata = DEMMetadata(
                file_path=str(self.dem_path),
                crs=src.crs.to_string() if src.crs else None,
                bounds=(bounds.left, bounds.bottom, bounds.right, bounds.top),
                width=src.width,
                height=src.height,
                resolution=(src.res[0], src.res[1]),
                nodata_value=src.nodata,
                min_elevation=float(np.nanmin(src.read(1))),
                max_elevation=float(np.nanmax(src.read(1)))
            )

            self.raster = src
            logger.info(f"DEM loaded successfully: {self.dem_path}")
            logger.info(f"  CRS: {self.metadata.crs}")
            logger.info(f"  Bounds: {self.metadata.bounds}")
            logger.info(f"  Resolution: {self.metadata.resolution}")
            logger.info(f"  Elevation range: {self.metadata.min_elevation:.2f}m to {self.metadata.max_elevation:.2f}m")

            return True

        except Exception as e:
            logger.error(f"Failed to load DEM: {e}")
            return False

    def is_loaded(self) -> bool:
        """Check if DEM is loaded."""
        return self.raster is not None and self.metadata is not None

    def get_metadata(self) -> Optional[DEMMetadata]:
        """Get DEM metadata."""
        return self.metadata

    def is_in_bounds(self, lat: float, lon: float) -> bool:
        """Check if coordinates are within DEM bounds."""
        if not self.metadata:
            return False

        left, bottom, right, top = self.metadata.bounds
        return left <= lon <= right and bottom <= lat <= top

    def get_elevation(self, lat: float, lon: float) -> Optional[float]:
        """
        Get elevation at a latitude/longitude location.

        Args:
            lat: Latitude in degrees (EPSG:4326)
            lon: Longitude in degrees (EPSG:4326)

        Returns:
            Elevation in meters, or None if invalid
        """
        # Check cache first (works even without loaded DEM)
        cache_key = (round(lat, 6), round(lon, 6))
        if cache_key in self.elevation_cache:
            return self.elevation_cache[cache_key]

        if not self.is_loaded():
            return None

        if not self.is_in_bounds(lat, lon):
            logger.debug(f"Coordinates ({lat}, {lon}) outside DEM bounds")
            return None

        try:
            # Convert lat/lon to raster coordinates
            # Rasterio uses (row, col) indexing
            row, col = self.raster.index(lon, lat)

            # Read the pixel value
            if 0 <= row < self.metadata.height and 0 <= col < self.metadata.width:
                band = self.raster.read(1)
                elevation = float(band[int(row), int(col)])

                # Check for NoData
                if self.metadata.nodata_value is not None:
                    if elevation == self.metadata.nodata_value:
                        return None

                # Cache and return
                self.elevation_cache[cache_key] = elevation
                return elevation

            return None

        except Exception as e:
            logger.debug(f"Error reading elevation at ({lat}, {lon}): {e}")
            return None

    def get_elevations_batch(self, locations: List[Tuple[float, float]]) -> List[Optional[float]]:
        """
        Get elevations for multiple locations.

        Args:
            locations: List of (lat, lon) tuples

        Returns:
            List of elevations (None if invalid for that location)
        """
        return [self.get_elevation(lat, lon) for lat, lon in locations]

    def calculate_slope(self, lat: float, lon: float, window_size: int = 3) -> Optional[float]:
        """
        Calculate slope at a location using a moving window.

        Args:
            lat, lon: Coordinates
            window_size: Size of window for slope calculation (must be odd)

        Returns:
            Slope in degrees (0-90), or None if invalid
        """
        if not self.is_loaded():
            return None

        if not self.is_in_bounds(lat, lon):
            return None

        try:
            row, col = self.raster.index(lon, lat)
            row, col = int(row), int(col)

            half_window = window_size // 2

            # Get window of elevation values
            row_start = max(0, row - half_window)
            row_end = min(self.metadata.height, row + half_window + 1)
            col_start = max(0, col - half_window)
            col_end = min(self.metadata.width, col + half_window + 1)

            band = self.raster.read(1)
            window = band[row_start:row_end, col_start:col_end]

            # Filter out NoData
            if self.metadata.nodata_value is not None:
                window = np.where(window == self.metadata.nodata_value, np.nan, window)

            if np.all(np.isnan(window)):
                return None

            # Calculate slope using Sobel operator approximation
            gy, gx = np.gradient(window)

            # Cell size in degrees
            cell_size_deg = self.metadata.resolution[0]

            # Convert to meters (rough approximation at equator ~111km per degree)
            cell_size_m = abs(cell_size_deg) * 111000

            # Slopes in m/m
            slope_ew = gx / cell_size_m
            slope_ns = gy / cell_size_m

            # Maximum slope magnitude
            max_slope_ratio = np.nanmax(np.sqrt(slope_ew**2 + slope_ns**2))

            # Convert to degrees
            slope_degrees = np.degrees(np.arctan(max_slope_ratio))

            return float(np.clip(slope_degrees, 0, 90))

        except Exception as e:
            logger.debug(f"Error calculating slope at ({lat}, {lon}): {e}")
            return None

    def get_terrain_point(self, lat: float, lon: float) -> TerrainPoint:
        """
        Get complete terrain information at a location.

        Args:
            lat, lon: Coordinates

        Returns:
            TerrainPoint with elevation, slope, and low-point factor
        """
        if not self.metadata:
            return TerrainPoint(
                latitude=lat,
                longitude=lon,
                elevation_m=0,
                slope_degrees=0,
                low_point_factor=0.5,
                valid=False,
                reason="DEM not loaded"
            )

        if not self.is_in_bounds(lat, lon):
            return TerrainPoint(
                latitude=lat,
                longitude=lon,
                elevation_m=0,
                slope_degrees=0,
                low_point_factor=0.5,
                valid=False,
                reason="Coordinates outside DEM bounds"
            )

        # Get elevation
        elevation = self.get_elevation(lat, lon)
        if elevation is None:
            return TerrainPoint(
                latitude=lat,
                longitude=lon,
                elevation_m=0,
                slope_degrees=0,
                low_point_factor=0.5,
                valid=False,
                reason="No elevation data at location"
            )

        # Get slope
        slope = self.calculate_slope(lat, lon)
        if slope is None:
            slope = 1.0  # Default

        # Calculate low-point factor
        # Low areas (low slope) tend to accumulate water
        low_point_factor = 1.0 - (slope / 90.0) * 0.8  # Range: 0.2 to 1.0
        # Clamp to valid range to avoid floating-point precision issues
        low_point_factor = max(0.2, min(1.0, low_point_factor))

        return TerrainPoint(
            latitude=lat,
            longitude=lon,
            elevation_m=elevation,
            slope_degrees=slope,
            low_point_factor=low_point_factor,
            valid=True,
            reason=None
        )

    def close(self):
        """Close the raster."""
        if self.raster:
            self.raster.close()
            self.raster = None

    def __del__(self):
        """Cleanup on deletion."""
        self.close()


# Global DEM instance
_dem_loader: Optional[DEMLoader] = None


def get_dem_loader(dem_path: Optional[str] = None) -> DEMLoader:
    """Get or create the global DEM loader instance."""
    global _dem_loader
    if _dem_loader is None:
        _dem_loader = DEMLoader(dem_path)
        _dem_loader.load()
    return _dem_loader


def get_terrain_at_location(lat: float, lon: float) -> TerrainPoint:
    """
    Get terrain information at a specific location.

    Falls back to simplified model if DEM unavailable.
    """
    loader = get_dem_loader()

    if not loader.is_loaded():
        # Fallback to simplified model
        return TerrainPoint(
            latitude=lat,
            longitude=lon,
            elevation_m=100.0,  # Default elevation
            slope_degrees=2.0,  # Default slope
            low_point_factor=0.5,  # Default accumulation factor
            valid=False,
            reason="Using fallback model"
        )

    return loader.get_terrain_point(lat, lon)


def get_terrain_batch(locations: List[Tuple[float, float]]) -> List[TerrainPoint]:
    """Get terrain information for multiple locations."""
    return [get_terrain_at_location(lat, lon) for lat, lon in locations]
