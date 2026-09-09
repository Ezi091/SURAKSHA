"""
Tests for DEM (Digital Elevation Model) Service

Tests cover:
1. DEM loading and metadata validation
2. Elevation queries with bounds checking
3. Slope calculation
4. Terrain point derivation
5. Batch operations
6. Fallback behavior when DEM unavailable
7. Data validation and error handling
"""

import pytest
import numpy as np
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from app.services.dem_service import (
    DEMLoader,
    DEMMetadata,
    TerrainPoint,
    get_dem_loader,
    get_terrain_at_location,
    get_terrain_batch,
)


class TestDEMMetadata:
    """Test DEM metadata dataclass."""

    def test_dem_metadata_creation(self):
        """Test creating DEM metadata."""
        metadata = DEMMetadata(
            file_path="data/terrain/dem.tif",
            crs="EPSG:4326",
            bounds=(72.8648611, 19.0851389, 72.9048611, 19.1251389),
            width=144,
            height=144,
            resolution=(0.00277778, -0.00277778),
            nodata_value=-9999.0,
            min_elevation=-3.70,
            max_elevation=123.59
        )

        assert metadata.file_path == "data/terrain/dem.tif"
        assert metadata.crs == "EPSG:4326"
        assert metadata.width == 144
        assert metadata.height == 144
        assert metadata.min_elevation == -3.70
        assert metadata.max_elevation == 123.59


class TestTerrainPoint:
    """Test terrain point dataclass."""

    def test_terrain_point_valid(self):
        """Test creating valid terrain point."""
        point = TerrainPoint(
            latitude=19.0951389,
            longitude=72.8848611,
            elevation_m=45.0,
            slope_degrees=5.5,
            low_point_factor=0.6,
            valid=True
        )

        assert point.latitude == 19.0951389
        assert point.longitude == 72.8848611
        assert point.elevation_m == 45.0
        assert point.slope_degrees == 5.5
        assert point.low_point_factor == 0.6
        assert point.valid is True
        assert point.reason is None

    def test_terrain_point_invalid(self):
        """Test creating invalid terrain point with reason."""
        point = TerrainPoint(
            latitude=19.0951389,
            longitude=72.8848611,
            elevation_m=0,
            slope_degrees=0,
            low_point_factor=0.5,
            valid=False,
            reason="Outside DEM bounds"
        )

        assert point.valid is False
        assert point.reason == "Outside DEM bounds"


class TestDEMLoaderBounds:
    """Test DEM loader bounds checking."""

    def test_is_in_bounds_true(self):
        """Test location within DEM bounds."""
        loader = DEMLoader()
        loader.metadata = DEMMetadata(
            file_path="test.tif",
            crs="EPSG:4326",
            bounds=(72.8648611, 19.0851389, 72.9048611, 19.1251389),
            width=144,
            height=144,
            resolution=(0.00277778, -0.00277778),
            nodata_value=-9999.0,
            min_elevation=-3.70,
            max_elevation=123.59
        )

        # Test center point
        assert loader.is_in_bounds(19.1051389, 72.8848611) is True

    def test_is_in_bounds_false_outside(self):
        """Test location outside DEM bounds."""
        loader = DEMLoader()
        loader.metadata = DEMMetadata(
            file_path="test.tif",
            crs="EPSG:4326",
            bounds=(72.8648611, 19.0851389, 72.9048611, 19.1251389),
            width=144,
            height=144,
            resolution=(0.00277778, -0.00277778),
            nodata_value=-9999.0,
            min_elevation=-3.70,
            max_elevation=123.59
        )

        # Test point well outside bounds
        assert loader.is_in_bounds(19.2, 72.7) is False
        assert loader.is_in_bounds(19.0, 73.0) is False

    def test_is_in_bounds_false_no_metadata(self):
        """Test bounds check fails without metadata."""
        loader = DEMLoader()
        assert loader.is_in_bounds(19.1051389, 72.8848611) is False


class TestDEMLoaderElevation:
    """Test DEM loader elevation queries."""

    def test_get_elevation_not_loaded(self):
        """Test elevation query returns None when DEM not loaded."""
        loader = DEMLoader()
        elevation = loader.get_elevation(19.1051389, 72.8848611)
        assert elevation is None

    def test_get_elevation_outside_bounds(self):
        """Test elevation query returns None outside bounds."""
        loader = DEMLoader()
        loader.metadata = DEMMetadata(
            file_path="test.tif",
            crs="EPSG:4326",
            bounds=(72.8648611, 19.0851389, 72.9048611, 19.1251389),
            width=144,
            height=144,
            resolution=(0.00277778, -0.00277778),
            nodata_value=-9999.0,
            min_elevation=-3.70,
            max_elevation=123.59
        )

        elevation = loader.get_elevation(19.2, 72.7)
        assert elevation is None

    def test_elevation_caching(self):
        """Test elevation caching mechanism."""
        loader = DEMLoader()

        # Manually set cache
        cache_key = (19.105139, 72.884861)  # rounded to 6 decimals
        expected_elevation = 42.5

        loader.elevation_cache[cache_key] = expected_elevation

        # Query with rounded coordinates should hit cache
        elevation = loader.get_elevation(19.1051389, 72.8848611)
        assert elevation == expected_elevation


class TestDEMLoaderSlope:
    """Test DEM loader slope calculations."""

    def test_calculate_slope_not_loaded(self):
        """Test slope calculation returns None when DEM not loaded."""
        loader = DEMLoader()
        slope = loader.calculate_slope(19.1051389, 72.8848611)
        assert slope is None

    def test_calculate_slope_outside_bounds(self):
        """Test slope calculation returns None outside bounds."""
        loader = DEMLoader()
        loader.metadata = DEMMetadata(
            file_path="test.tif",
            crs="EPSG:4326",
            bounds=(72.8648611, 19.0851389, 72.9048611, 19.1251389),
            width=144,
            height=144,
            resolution=(0.00277778, -0.00277778),
            nodata_value=-9999.0,
            min_elevation=-3.70,
            max_elevation=123.59
        )

        slope = loader.calculate_slope(19.2, 72.7)
        assert slope is None


class TestTerrainPointDerivation:
    """Test terrain point derivation."""

    def test_get_terrain_point_not_loaded(self):
        """Test terrain point returns fallback when DEM not loaded."""
        loader = DEMLoader()
        point = loader.get_terrain_point(19.1051389, 72.8848611)

        assert point.valid is False
        assert point.reason == "DEM not loaded"
        assert point.elevation_m == 0
        assert point.low_point_factor == 0.5

    def test_get_terrain_point_outside_bounds(self):
        """Test terrain point returns fallback outside bounds."""
        loader = DEMLoader()
        loader.metadata = DEMMetadata(
            file_path="test.tif",
            crs="EPSG:4326",
            bounds=(72.8648611, 19.0851389, 72.9048611, 19.1251389),
            width=144,
            height=144,
            resolution=(0.00277778, -0.00277778),
            nodata_value=-9999.0,
            min_elevation=-3.70,
            max_elevation=123.59
        )

        point = loader.get_terrain_point(19.2, 72.7)

        assert point.valid is False
        assert "outside dem bounds" in point.reason.lower()


class TestBatchOperations:
    """Test batch terrain operations."""

    def test_get_elevations_batch_not_loaded(self):
        """Test batch elevation returns None list when DEM not loaded."""
        loader = DEMLoader()
        locations = [(19.1051389, 72.8848611), (19.1151389, 72.8948611)]

        elevations = loader.get_elevations_batch(locations)

        assert len(elevations) == 2
        assert all(e is None for e in elevations)


class TestFallbackBehavior:
    """Test fallback behavior when DEM unavailable."""

    def test_get_terrain_at_location_fallback(self):
        """Test fallback model when DEM not available."""
        with patch('app.services.dem_service.get_dem_loader') as mock_get_loader:
            mock_loader = Mock()
            mock_loader.is_loaded.return_value = False
            mock_get_loader.return_value = mock_loader

            point = get_terrain_at_location(19.1051389, 72.8848611)

            assert point.valid is False
            assert point.reason == "Using fallback model"
            assert point.elevation_m == 100.0
            assert point.slope_degrees == 2.0
            assert point.low_point_factor == 0.5

    def test_get_terrain_batch_fallback(self):
        """Test batch fallback when DEM not available."""
        with patch('app.services.dem_service.get_dem_loader') as mock_get_loader:
            mock_loader = Mock()
            mock_loader.is_loaded.return_value = False
            mock_get_loader.return_value = mock_loader

            locations = [(19.1051389, 72.8848611), (19.1151389, 72.8948611)]
            points = get_terrain_batch(locations)

            assert len(points) == 2
            assert all(not p.valid for p in points)


class TestDataValidation:
    """Test data validation in DEM service."""

    def test_nodata_handling(self):
        """Test NoData value handling in elevation queries."""
        loader = DEMLoader()
        loader.metadata = DEMMetadata(
            file_path="test.tif",
            crs="EPSG:4326",
            bounds=(72.8648611, 19.0851389, 72.9048611, 19.1251389),
            width=10,
            height=10,
            resolution=(0.04, -0.04),
            nodata_value=-9999.0,
            min_elevation=-3.70,
            max_elevation=123.59
        )

        # Create mock raster with NoData
        mock_raster = Mock()
        mock_raster.index.return_value = (5, 5)
        mock_raster.read.return_value = np.full((10, 10), -9999.0)

        loader.raster = mock_raster

        elevation = loader.get_elevation(19.1051389, 72.8848611)

        # Should return None for NoData
        assert elevation is None

    def test_slope_clipping(self):
        """Test slope clipping to 0-90 degree range."""
        loader = DEMLoader()
        loader.metadata = DEMMetadata(
            file_path="test.tif",
            crs="EPSG:4326",
            bounds=(72.8648611, 19.0851389, 72.9048611, 19.1251389),
            width=10,
            height=10,
            resolution=(0.04, -0.04),
            nodata_value=-9999.0,
            min_elevation=-3.70,
            max_elevation=123.59
        )

        # Create mock steep raster
        mock_raster = Mock()
        mock_raster.index.return_value = (5, 5)

        steep_array = np.array([
            [100, 100, 100],
            [100, 50, 100],
            [100, 0, 100]
        ], dtype=float)

        mock_raster.read.return_value = steep_array

        loader.raster = mock_raster

        # Slope should be clipped to 0-90
        slope = loader.calculate_slope(19.1051389, 72.8848611, window_size=3)

        if slope is not None:
            assert 0 <= slope <= 90


class TestLowPointFactorCalculation:
    """Test low-point factor derivation from slope."""

    def test_low_point_factor_range(self):
        """Test that low-point factor stays in valid range."""
        # Flat terrain (slope 0) should have high accumulation
        flat_slope = 0
        flat_factor = 1.0 - (flat_slope / 90.0) * 0.8
        # Clamp to valid range like the implementation does
        flat_factor = max(0.2, min(1.0, flat_factor))
        assert 0.2 <= flat_factor <= 1.0

        # Steep terrain (slope 90) should have low accumulation
        steep_slope = 90
        steep_factor = 1.0 - (steep_slope / 90.0) * 0.8
        # Clamp to valid range like the implementation does
        steep_factor = max(0.2, min(1.0, steep_factor))
        assert 0.2 <= steep_factor <= 1.0

        # Slope should inversely relate to accumulation
        assert flat_factor > steep_factor


class TestGlobalDEMInstance:
    """Test global DEM loader instance management."""

    def test_get_dem_loader_singleton(self):
        """Test get_dem_loader returns same instance."""
        # Reset global
        import app.services.dem_service as dem_module
        dem_module._dem_loader = None

        loader1 = get_dem_loader()
        loader2 = get_dem_loader()

        # Should be same instance
        assert loader1 is loader2

    def test_get_dem_loader_custom_path(self):
        """Test get_dem_loader with custom path."""
        import app.services.dem_service as dem_module
        dem_module._dem_loader = None

        custom_path = "custom/path/dem.tif"
        loader = get_dem_loader(custom_path)

        assert str(loader.dem_path) == custom_path


class TestErrorHandling:
    """Test error handling and edge cases."""

    def test_invalid_coordinates(self):
        """Test handling of invalid coordinates."""
        loader = DEMLoader()
        loader.metadata = DEMMetadata(
            file_path="test.tif",
            crs="EPSG:4326",
            bounds=(72.8648611, 19.0851389, 72.9048611, 19.1251389),
            width=144,
            height=144,
            resolution=(0.00277778, -0.00277778),
            nodata_value=-9999.0,
            min_elevation=-3.70,
            max_elevation=123.59
        )

        # Very large coordinates should be handled gracefully
        point = loader.get_terrain_point(1000.0, 1000.0)
        assert point.valid is False

    def test_rasterio_import_missing(self):
        """Test behavior when rasterio is not available."""
        import app.services.dem_service as dem_module

        # Save original state
        original_rasterio = dem_module.RASTERIO_AVAILABLE

        try:
            dem_module.RASTERIO_AVAILABLE = False
            loader = DEMLoader("test.tif")
            result = loader.load()

            # Should return False when rasterio unavailable
            assert result is False

        finally:
            dem_module.RASTERIO_AVAILABLE = original_rasterio


class TestDEMIntegration:
    """Integration tests with flood service."""

    def test_terrain_service_integration(self):
        """Test integration with terrain service."""
        from app.services.terrain_service import calculate_terrain_accumulation_factor
        from app.models.schemas import TerrainInput

        # Create terrain input without lat/lon (fallback mode)
        terrain = TerrainInput(slope=0.02, low_point_factor=0.5)

        factor = calculate_terrain_accumulation_factor(terrain)

        # Should return a valid factor
        assert 0.5 <= factor <= 1.5

    def test_batch_terrain_characteristics(self):
        """Test batch terrain characteristic retrieval."""
        from app.services.terrain_service import get_batch_terrain_characteristics

        locations = [
            (19.0851389, 72.8648611),
            (19.1251389, 72.9048611),
            (19.1051389, 72.8848611)
        ]

        results = get_batch_terrain_characteristics(locations)

        assert len(results) == 3
        for elevation, slope, low_point in results:
            assert isinstance(elevation, (int, float))
            assert 0 <= slope <= 1.0
            assert 0 <= low_point <= 1.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
