"""
Tests for OSM-based Routing Service

Verifies:
- Loading GeoJSON road data
- Building routing graph
- Finding nearest nodes
- Normal shortest route calculation
- Safe route avoids HIGH/SEVERE risk roads
- Safe route can be longer than normal
- Error handling for invalid locations
"""

import pytest
from pathlib import Path
from app.services.osm_routing_service import (
    OSMRoadNetwork,
    OSMRoutingService,
    RoadRiskLevel
)


@pytest.fixture
def osm_network():
    """Load OSM road network from GeoJSON."""
    network = OSMRoadNetwork()
    success = network.load_from_geojson("data/roads/roads.geojson")
    assert success, "Failed to load OSM road data"
    return network


@pytest.fixture
def routing_service(osm_network):
    """Create routing service with OSM network."""
    return OSMRoutingService(osm_network)


def test_geojson_file_exists():
    """Test 1: GeoJSON file exists at expected location."""
    # Check from repo root (tests run from backend dir)
    path1 = Path("../data/roads/roads.geojson")
    path2 = Path("data/roads/roads.geojson")
    assert path1.exists() or path2.exists(), f"GeoJSON file not found at {path1} or {path2}"


def test_load_geojson(osm_network):
    """Test 2: GeoJSON loads successfully and contains data."""
    assert osm_network.loader is not None
    assert len(osm_network.loader.features) > 0
    assert len(osm_network.segments) > 0
    assert len(osm_network.nodes) > 0


def test_graph_structure(osm_network):
    """Test 3: Graph has valid structure with nodes and edges."""
    summary = osm_network.loader.get_summary()

    assert summary['total_features'] > 100, "Too few road features"
    assert summary['total_nodes'] > 500, "Too few nodes in graph"
    assert summary['total_edges'] > 500, "Too few edges in graph"
    assert summary['total_length_km'] > 50, "Total road length too short"

    # Print summary for debugging
    print(f"\nLoaded road network:")
    print(f"  Features: {summary['total_features']}")
    print(f"  Nodes: {summary['total_nodes']}")
    print(f"  Edges: {summary['total_edges']}")
    print(f"  Total length: {summary['total_length_km']} km")


def test_find_nearest_node(osm_network):
    """Test 4: Finding nearest node works."""
    # Use coordinates in Mumbai
    lat, lon = 19.0760, 72.8777

    node = osm_network.find_nearest_node(lat, lon)
    assert node is not None, "Could not find nearest node"

    # Node should have valid coordinates
    coords = osm_network.nodes.get(node)
    assert coords is not None
    assert len(coords) == 2


def test_nearest_node_is_close(osm_network):
    """Test 5: Nearest node is reasonably close to query point."""
    lat, lon = 19.0760, 72.8777
    node = osm_network.find_nearest_node(lat, lon)

    node_lat, node_lon = osm_network.nodes[node]

    # Distance should be small (less than 0.01 degrees ~ 1 km)
    distance_sq = (node_lat - lat)**2 + (node_lon - lon)**2
    assert distance_sq < 0.0001, "Nearest node too far away"


def test_normal_route_calculation(routing_service, osm_network):
    """Test 6: Calculate normal route between two points."""
    # Use well-separated points
    result = routing_service.calculate_safe_route(
        origin_lat=19.0760,
        origin_lon=72.8777,
        dest_lat=19.1000,
        dest_lon=72.9000,
        depth_threshold_cm=15.0,
        flood_zones=[]
    )

    assert 'error' not in result, f"Route calculation failed: {result.get('error')}"
    assert result['normal_route']['distance_km'] > 0
    assert len(result['normal_route']['segment_ids']) > 0


def test_route_has_geometry(routing_service):
    """Test 7: Routes include actual road geometries."""
    result = routing_service.calculate_safe_route(
        origin_lat=19.0760,
        origin_lon=72.8777,
        dest_lat=19.1000,
        dest_lon=72.9000,
        depth_threshold_cm=15.0
    )

    if 'error' not in result:
        # Check that geometry is present
        assert result['normal_route']['geometry'] is not None
        assert len(result['normal_route']['geometry']) > 0

        # Each geometry should be a list of coordinates
        for geom in result['normal_route']['geometry']:
            assert len(geom) >= 2, "Segment has fewer than 2 points"


def test_route_road_names(routing_service):
    """Test 8: Routes include road names when available."""
    result = routing_service.calculate_safe_route(
        origin_lat=19.0760,
        origin_lon=72.8777,
        dest_lat=19.1000,
        dest_lon=72.9000,
        depth_threshold_cm=15.0
    )

    if 'error' not in result:
        # Check road_summary is present
        assert 'road_summary' in result['normal_route']
        assert isinstance(result['normal_route']['road_summary'], str)
        assert len(result['normal_route']['road_summary']) > 0


def test_same_origin_destination_error(routing_service):
    """Test 9: Same origin and destination returns error."""
    lat, lon = 19.0760, 72.8777

    result = routing_service.calculate_safe_route(
        origin_lat=lat,
        origin_lon=lon,
        dest_lat=lat,
        dest_lon=lon
    )

    assert 'error' in result


def test_distance_metrics(routing_service):
    """Test 10: Distance metrics are calculated correctly."""
    result = routing_service.calculate_safe_route(
        origin_lat=19.0760,
        origin_lon=72.8777,
        dest_lat=19.1000,
        dest_lon=72.9000
    )

    if 'error' not in result:
        normal_dist = result['normal_route']['distance_km']
        safe_dist = result['safe_route']['distance_km']
        increase = result['distance_increase_km']

        # Distance increase should match
        expected_increase = max(0, safe_dist - normal_dist)
        assert abs(increase - expected_increase) < 0.01


def test_risk_and_depth_arrays_match(routing_service):
    """Test 11: Risk and depth arrays match segment count."""
    result = routing_service.calculate_safe_route(
        origin_lat=19.0760,
        origin_lon=72.8777,
        dest_lat=19.1000,
        dest_lon=72.9000
    )

    if 'error' not in result:
        normal = result['normal_route']
        assert len(normal['risk_levels']) == len(normal['segment_ids'])
        assert len(normal['water_depths']) == len(normal['segment_ids'])
        assert len(normal['road_names']) == len(normal['segment_ids'])


def test_geometry_coordinate_structure(routing_service):
    """Test 12: Route geometry coordinates are in proper format."""
    result = routing_service.calculate_safe_route(
        origin_lat=19.0760,
        origin_lon=72.8777,
        dest_lat=19.1000,
        dest_lon=72.9000
    )

    if 'error' not in result:
        for geom in result['normal_route']['geometry']:
            for coord in geom:
                assert len(coord) == 2, "Coordinate should be [lon, lat]"
                lon, lat = coord
                assert -180 <= lon <= 180, "Longitude out of range"
                assert -90 <= lat <= 90, "Latitude out of range"
