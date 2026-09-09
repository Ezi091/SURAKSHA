"""
Safe Routing Service

Provides flood-aware alternative routing using Dijkstra's algorithm.

The routing service consumes flood-risk information and calculates:
1. Normal shortest route (ignoring flood risk)
2. Safe route (avoiding high/severe risk roads)

Uses a synthetic demo road graph for Phase 1.
Can be extended with OSM data in future phases.
"""

import heapq
from typing import List, Tuple, Dict, Optional
from dataclasses import dataclass
from enum import Enum


class RoadRiskLevel(str, Enum):
    LOW = "LOW"
    MODERATE = "MODERATE"
    HIGH = "HIGH"
    SEVERE = "SEVERE"


@dataclass
class RoadSegment:
    """Represents a road segment in the network."""
    id: str
    start_node: str
    end_node: str
    distance_km: float
    risk_level: RoadRiskLevel = RoadRiskLevel.LOW
    water_depth_cm: float = 0.0

    def is_traversable_for_safety(self, depth_threshold_cm: float = 15.0) -> bool:
        """Check if road can be used for safe routing."""
        if self.risk_level in [RoadRiskLevel.HIGH, RoadRiskLevel.SEVERE]:
            return False
        if self.water_depth_cm > depth_threshold_cm:
            return False
        return True

    def get_cost(self, mode: str = "normal") -> float:
        """
        Calculate traversal cost based on mode.

        Args:
            mode: "normal" (distance only) or "safe" (distance + flood penalty)

        Returns:
            Cost for pathfinding (distance + optional penalties)
        """
        if mode == "normal":
            return self.distance_km

        # Safe mode: add penalties for risky roads
        cost = self.distance_km

        if self.risk_level == RoadRiskLevel.MODERATE:
            cost *= 1.5  # 50% penalty
        elif self.risk_level == RoadRiskLevel.HIGH:
            cost *= 3.0  # 200% penalty
        elif self.risk_level == RoadRiskLevel.SEVERE:
            cost *= 10.0  # 900% penalty (strongly avoid)

        # Add depth penalty
        if self.water_depth_cm > 0:
            cost += (self.water_depth_cm / 10.0)  # +0.1 per cm

        return cost


class RoadNetwork:
    """Represents the road network graph."""

    def __init__(self):
        self.segments: Dict[str, RoadSegment] = {}
        self.adjacency: Dict[str, List[str]] = {}  # node -> [segment_ids]

    def add_segment(self, segment: RoadSegment):
        """Add a road segment to the network."""
        self.segments[segment.id] = segment

        # Build adjacency list
        if segment.start_node not in self.adjacency:
            self.adjacency[segment.start_node] = []
        if segment.end_node not in self.adjacency:
            self.adjacency[segment.end_node] = []

        self.adjacency[segment.start_node].append(segment.id)
        self.adjacency[segment.end_node].append(segment.id)

    def get_neighbors(self, node: str) -> List[Tuple[str, str]]:
        """
        Get neighbors of a node.

        Returns:
            List of (neighbor_node, segment_id) tuples
        """
        neighbors = []
        if node not in self.adjacency:
            return neighbors

        for seg_id in self.adjacency[node]:
            segment = self.segments[seg_id]
            if segment.start_node == node:
                neighbors.append((segment.end_node, seg_id))
            else:
                neighbors.append((segment.start_node, seg_id))

        return neighbors


@dataclass
class Route:
    """Represents a calculated route."""
    origin: str
    destination: str
    total_distance_km: float
    segment_ids: List[str]
    risk_levels: List[str]
    water_depths: List[float]

    @property
    def has_high_risk(self) -> bool:
        """Check if route contains HIGH or SEVERE risk segments."""
        return any(risk in [RoadRiskLevel.HIGH, RoadRiskLevel.SEVERE]
                  for risk in self.risk_levels)

    @property
    def max_depth(self) -> float:
        """Get maximum water depth on route."""
        return max(self.water_depths) if self.water_depths else 0.0


class RoutingService:
    """Service for calculating flood-safe routes."""

    def __init__(self, network: RoadNetwork):
        self.network = network

    def dijkstra(
        self,
        origin: str,
        destination: str,
        mode: str = "normal"
    ) -> Optional[Route]:
        """
        Calculate shortest path using Dijkstra's algorithm.

        Args:
            origin: Start node ID
            destination: End node ID
            mode: "normal" or "safe"

        Returns:
            Route object or None if no path found
        """
        if origin not in self.network.adjacency or destination not in self.network.adjacency:
            return None

        # Priority queue: (cost, node, path_segments)
        pq = [(0, origin, [])]
        visited = set()
        distances = {origin: 0}

        while pq:
            current_cost, current_node, path = heapq.heappop(pq)

            if current_node in visited:
                continue

            visited.add(current_node)

            if current_node == destination:
                # Build route from segment IDs
                segment_ids = path
                risk_levels = []
                water_depths = []
                total_distance = 0.0

                for seg_id in segment_ids:
                    seg = self.network.segments[seg_id]
                    risk_levels.append(seg.risk_level)
                    water_depths.append(seg.water_depth_cm)
                    total_distance += seg.distance_km

                return Route(
                    origin=origin,
                    destination=destination,
                    total_distance_km=total_distance,
                    segment_ids=segment_ids,
                    risk_levels=[r.value for r in risk_levels],
                    water_depths=water_depths
                )

            # Explore neighbors
            for neighbor_node, seg_id in self.network.get_neighbors(current_node):
                if neighbor_node in visited:
                    continue

                segment = self.network.segments[seg_id]
                cost = segment.get_cost(mode)
                new_cost = current_cost + cost

                if neighbor_node not in distances or new_cost < distances[neighbor_node]:
                    distances[neighbor_node] = new_cost
                    new_path = path + [seg_id]
                    heapq.heappush(pq, (new_cost, neighbor_node, new_path))

        return None

    def calculate_safe_route(
        self,
        origin: str,
        destination: str,
        depth_threshold_cm: float = 15.0
    ) -> Dict:
        """
        Calculate both normal and safe routes.

        Returns:
            {
                'normal_route': Route,
                'safe_route': Route,
                'needs_rerouting': bool,
                'affected_segments': [segment_ids],
                'avoided_segments': [segment_ids],
                'reason': str
            }
        """
        # Get normal route
        normal_route = self.dijkstra(origin, destination, mode="normal")
        if not normal_route:
            return {'error': f'No route found from {origin} to {destination}'}

        # Get safe route
        safe_route = self.dijkstra(origin, destination, mode="safe")
        if not safe_route:
            return {'error': f'No safe route found from {origin} to {destination}'}

        # Determine if rerouting is needed
        needs_rerouting = (
            normal_route.has_high_risk or
            normal_route.max_depth > depth_threshold_cm
        )

        # Find affected and avoided segments
        normal_set = set(normal_route.segment_ids)
        safe_set = set(safe_route.segment_ids)

        affected_segments = list(normal_set & safe_set)
        avoided_segments = list(normal_set - safe_set)

        # Determine reason for rerouting
        reason = "Route is safe"
        if needs_rerouting:
            if normal_route.has_high_risk:
                reason = "Original route contains HIGH/SEVERE flood risk"
            elif normal_route.max_depth > depth_threshold_cm:
                reason = f"Original route has water depth > {depth_threshold_cm} cm"

        return {
            'normal_route': {
                'origin': normal_route.origin,
                'destination': normal_route.destination,
                'distance_km': round(normal_route.total_distance_km, 2),
                'segment_ids': normal_route.segment_ids,
                'risk_levels': normal_route.risk_levels,
                'water_depths': [round(d, 1) for d in normal_route.water_depths],
                'max_water_depth_cm': round(normal_route.max_depth, 1),
                'has_high_risk': normal_route.has_high_risk
            },
            'safe_route': {
                'origin': safe_route.origin,
                'destination': safe_route.destination,
                'distance_km': round(safe_route.total_distance_km, 2),
                'segment_ids': safe_route.segment_ids,
                'risk_levels': safe_route.risk_levels,
                'water_depths': [round(d, 1) for d in safe_route.water_depths],
                'max_water_depth_cm': round(safe_route.max_depth, 1),
                'has_high_risk': safe_route.has_high_risk
            },
            'needs_rerouting': needs_rerouting,
            'distance_increase_km': round(
                max(0, safe_route.total_distance_km - normal_route.total_distance_km), 2
            ),
            'affected_segments': affected_segments,
            'avoided_segments': avoided_segments,
            'reason': reason
        }


def create_demo_network() -> RoadNetwork:
    r"""
    Create a small demo road network for testing.

    Network structure:

    n1 ---s1(1km,LOW)--- n2
    |                     |
    s2(1.5km,HIGH)        s3(1km,LOW)
    |                     |
    n3 ---s4(1km,MOD)---- n4
     \                   /
      s5(2km,LOW)   s6(1.5km,SEVERE)
       \           /
        \         /
          n5(dest)

    Best normal route: n1 -> n2 -> n4 -> n5 (4.5 km)
    Best safe route: n1 -> n3 -> n4 -> n5 or n1 -> n3 -> n5 (avoiding HIGH/SEVERE)
    """
    network = RoadNetwork()

    # Segments (depths calibrated to adjusted thresholds for demo visibility)
    # Threshold calibration: LOW=10cm, MODERATE=20cm, HIGH=35cm, SEVERE=50+cm
    segments = [
        RoadSegment("s1", "n1", "n2", 1.0, RoadRiskLevel.LOW, 0.0),
        RoadSegment("s2", "n1", "n3", 1.5, RoadRiskLevel.HIGH, 18.0),  # Elevated to near MODERATE threshold
        RoadSegment("s3", "n2", "n4", 1.0, RoadRiskLevel.LOW, 0.0),
        RoadSegment("s4", "n3", "n4", 1.0, RoadRiskLevel.MODERATE, 12.0),  # Moderate risk with noticeable depth
        RoadSegment("s5", "n3", "n5", 2.0, RoadRiskLevel.LOW, 0.0),
        RoadSegment("s6", "n4", "n5", 1.5, RoadRiskLevel.SEVERE, 45.0),  # Severe risk with high depth
    ]

    for seg in segments:
        network.add_segment(seg)

    return network
