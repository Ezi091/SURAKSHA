"""
Tests for Safe Routing Service

Verifies:
- Normal shortest path calculation
- Safe route avoids HIGH/SEVERE risk roads
- Safe route can be longer than normal route
- No rerouting when original route is safe
- Error handling when no route exists
"""

import pytest
from app.services.routing_service import (
    RoutingService,
    RoadNetwork,
    RoadSegment,
    RoadRiskLevel,
    create_demo_network
)


@pytest.fixture
def demo_network():
    """Create demo network for testing"""
    return create_demo_network()


@pytest.fixture
def routing_service(demo_network):
    """Create routing service with demo network"""
    return RoutingService(demo_network)


def test_normal_shortest_route(routing_service):
    """Test 1: Normal shortest route calculation (distance only)"""
    route = routing_service.dijkstra("n1", "n5", mode="normal")

    assert route is not None
    assert route.origin == "n1"
    assert route.destination == "n5"
    assert len(route.segment_ids) > 0
    # Normal route should find shortest path regardless of risk
    assert route.total_distance_km < 10.0


def test_safe_route_avoids_high_risk(routing_service):
    """Test 2: Safe route avoids HIGH risk roads"""
    route = routing_service.dijkstra("n1", "n5", mode="safe")

    assert route is not None
    # Should not contain segment s2 (HIGH risk)
    assert "s2" not in route.segment_ids


def test_safe_route_avoids_severe_risk(routing_service):
    """Test 3: Safe route avoids SEVERE risk roads"""
    route = routing_service.dijkstra("n1", "n5", mode="safe")

    assert route is not None
    # Should not contain segment s6 (SEVERE risk)
    assert "s6" not in route.segment_ids


def test_safe_route_can_be_longer(routing_service):
    """Test 4: Safe route can be longer than normal route"""
    normal_route = routing_service.dijkstra("n1", "n5", mode="normal")
    safe_route = routing_service.dijkstra("n1", "n5", mode="safe")

    assert normal_route is not None
    assert safe_route is not None

    # Safe route may be longer to avoid risks
    # (it's OK if equal length, but usually longer)
    assert safe_route.total_distance_km >= normal_route.total_distance_km * 0.95


def test_rerouting_when_normal_route_has_high_risk(routing_service):
    """Test 5: Rerouting detected when normal route has HIGH risk"""
    result = routing_service.calculate_safe_route("n1", "n5")

    assert "error" not in result
    assert result['needs_rerouting'] is True
    assert "HIGH" in result['reason'] or "SEVERE" in result['reason']
    assert len(result['avoided_segments']) > 0


def test_avoided_segments_not_in_safe_route(routing_service):
    """Test 6: Avoided segments are not in safe route"""
    result = routing_service.calculate_safe_route("n1", "n5")

    safe_set = set(result['safe_route']['segment_ids'])
    avoided_set = set(result['avoided_segments'])

    # Avoided segments should not be in safe route
    assert safe_set & avoided_set == set()


def test_distance_comparison(routing_service):
    """Test 7: Distance increase is calculated correctly"""
    result = routing_service.calculate_safe_route("n1", "n5")

    normal_dist = result['normal_route']['distance_km']
    safe_dist = result['safe_route']['distance_km']
    increase = result['distance_increase_km']

    # Distance increase should match calculation
    expected_increase = max(0, safe_dist - normal_dist)
    assert abs(increase - expected_increase) < 0.01


def test_no_route_returns_error(routing_service):
    """Test 8: Non-existent nodes return error"""
    result = routing_service.calculate_safe_route("invalid_start", "invalid_end")

    assert "error" in result


def test_same_origin_destination(routing_service):
    """Test 9: Same origin and destination"""
    # Create custom network for this test
    network = RoadNetwork()
    network.add_segment(RoadSegment("s1", "n1", "n2", 1.0, RoadRiskLevel.LOW, 0.0))

    service = RoutingService(network)
    route = service.dijkstra("n1", "n1", mode="normal")

    # Route from node to itself should have zero distance and no segments
    assert route is not None
    assert route.total_distance_km == 0.0
    assert len(route.segment_ids) == 0


def test_moderate_risk_penalty(routing_service):
    """Test 10: Moderate risk roads receive penalty but not avoided"""
    # Get safe route
    route = routing_service.dijkstra("n1", "n5", mode="safe")

    assert route is not None
    # Safe route may use moderate-risk roads if needed (s4 is MODERATE)
    # The presence of s4 in some paths is OK as long as HIGH/SEVERE avoided
    has_only_low_moderate = all(
        risk in [RoadRiskLevel.LOW.value, RoadRiskLevel.MODERATE.value]
        for risk in route.risk_levels
    )
    assert has_only_low_moderate


def test_route_segments_connected(routing_service):
    """Test 11: Route segments form a connected path"""
    route = routing_service.dijkstra("n1", "n5", mode="normal")

    assert route is not None
    segments = [routing_service.network.segments[seg_id] for seg_id in route.segment_ids]

    # Check segments form a valid path
    current_node = route.origin
    for segment in segments:
        # Segment should connect from current node
        assert current_node in [segment.start_node, segment.end_node]
        # Move to next node
        current_node = segment.end_node if segment.start_node == current_node else segment.start_node

    # Final node should be destination
    assert current_node == route.destination


def test_water_depth_data_included(routing_service):
    """Test 12: Water depth data is included in route"""
    result = routing_service.calculate_safe_route("n1", "n5")

    assert "water_depths" in result['normal_route']
    assert "water_depths" in result['safe_route']
    assert len(result['normal_route']['water_depths']) == len(result['normal_route']['segment_ids'])
    assert len(result['safe_route']['water_depths']) == len(result['safe_route']['segment_ids'])


def test_risk_levels_included(routing_service):
    """Test 13: Risk level data is included in route"""
    result = routing_service.calculate_safe_route("n1", "n5")

    assert "risk_levels" in result['normal_route']
    assert "risk_levels" in result['safe_route']

    # Risk levels should be strings (enum values)
    for risk in result['normal_route']['risk_levels']:
        assert risk in ["LOW", "MODERATE", "HIGH", "SEVERE"]

    for risk in result['safe_route']['risk_levels']:
        assert risk in ["LOW", "MODERATE", "HIGH", "SEVERE"]


def test_affected_segments_in_both_routes(routing_service):
    """Test 14: Affected segments are in both normal and safe routes"""
    result = routing_service.calculate_safe_route("n1", "n5")

    normal_set = set(result['normal_route']['segment_ids'])
    safe_set = set(result['safe_route']['segment_ids'])
    affected_set = set(result['affected_segments'])

    # Affected should be intersection
    assert affected_set == normal_set & safe_set


def test_demo_network_structure(demo_network):
    """Test 15: Demo network has expected structure"""
    expected_nodes = {"n1", "n2", "n3", "n4", "n5"}
    expected_segments = {"s1", "s2", "s3", "s4", "s5", "s6"}

    assert set(demo_network.adjacency.keys()) == expected_nodes
    assert set(demo_network.segments.keys()) == expected_segments
