"""
OSM-based Routing Service

Provides flood-aware routing using real OpenStreetMap road data.

The service:
1. Loads OSM road network from GeoJSON
2. Builds routing graph with real geometries
3. Calculates normal shortest routes
4. Applies flood risk penalties to create safe routes
5. Returns routes with real road names and geometries
"""

import heapq
import logging
from typing import List, Tuple, Dict, Optional
from dataclasses import dataclass
from enum import Enum

from app.services.road_data_service import RoadDataLoader

logger = logging.getLogger(__name__)


class RoadRiskLevel(str, Enum):
    LOW = "LOW"
    MODERATE = "MODERATE"
    HIGH = "HIGH"
    SEVERE = "SEVERE"


@dataclass
class RoadSegment:
    """Represents a road segment in the network."""
    id: str
    osm_way_id: str
    start_node: str
    end_node: str
    distance_km: float
    name: Optional[str]
    highway_type: Optional[str]
    geometry: List[Tuple[float, float]]  # [(lon, lat), ...]
    risk_level: RoadRiskLevel = RoadRiskLevel.LOW
    water_depth_cm: float = 0.0

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


class OSMRoadNetwork:
    """Road network built from OpenStreetMap data."""

    def __init__(self):
        self.segments: Dict[str, RoadSegment] = {}
        self.adjacency: Dict[str, List[str]] = {}  # node -> [segment_ids]
        self.nodes: Dict[str, Tuple[float, float]] = {}  # node_id -> (lat, lon)
        self.loader: Optional[RoadDataLoader] = None

    def load_from_geojson(self, geojson_path: str = "data/roads/roads.geojson") -> bool:
        """
        Load road network from GeoJSON file.

        Returns:
            True if successful, False otherwise
        """
        try:
            self.loader = RoadDataLoader(geojson_path)

            if not self.loader.load():
                return False

            self.loader.build_graph()

            # Convert to routing graph
            self.nodes = self.loader.nodes.copy()

            for edge in self.loader.edges:
                segment = RoadSegment(
                    id=edge['id'],
                    osm_way_id=edge['osm_way_id'],
                    start_node=edge['start_node'],
                    end_node=edge['end_node'],
                    distance_km=edge['length_km'],
                    name=edge['name'],
                    highway_type=edge['highway_type'],
                    geometry=edge['geometry'],
                    risk_level=RoadRiskLevel.LOW,
                    water_depth_cm=0.0
                )

                self.add_segment(segment)

            logger.info(f"Loaded OSM network: {len(self.nodes)} nodes, {len(self.segments)} segments")
            return True

        except Exception as e:
            logger.error(f"Failed to load OSM network: {e}")
            return False

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

    def find_nearest_node(self, lat: float, lon: float) -> Optional[str]:
        """Find nearest node to given coordinates."""
        if self.loader:
            return self.loader.get_nearest_node(lat, lon)
        return None

    def apply_flood_risk(self, flood_zones: List[Dict]):
        """
        Apply flood risk to road segments based on flood prediction zones.

        Args:
            flood_zones: List of dicts with 'coordinates' (lat, lon), 'radius' (m),
                        'risk' level, and 'depth' (cm)
        """
        for segment in self.segments.values():
            # Check segment midpoint against flood zones
            if len(segment.geometry) >= 2:
                # Get midpoint
                mid_lon = sum(p[0] for p in segment.geometry) / len(segment.geometry)
                mid_lat = sum(p[1] for p in segment.geometry) / len(segment.geometry)

                # Find highest risk zone affecting this segment
                max_risk = RoadRiskLevel.LOW
                max_depth = 0.0

                for zone in flood_zones:
                    zone_lat, zone_lon = zone['coordinates']
                    zone_radius_km = zone['radius'] / 1000.0  # Convert m to km

                    # Calculate distance from segment midpoint to zone center
                    from app.services.road_data_service import haversine_distance
                    dist_km = haversine_distance(mid_lon, mid_lat, zone_lon, zone_lat)

                    # If within zone radius, apply risk
                    if dist_km <= zone_radius_km:
                        zone_risk_str = zone.get('risk', 'low').upper()
                        try:
                            zone_risk = RoadRiskLevel[zone_risk_str]
                            # Take maximum risk
                            if zone_risk.value > max_risk.value:
                                max_risk = zone_risk
                                max_depth = max(max_depth, zone.get('depth', 0.0))
                        except KeyError:
                            pass

                segment.risk_level = max_risk
                segment.water_depth_cm = max_depth


@dataclass
class Route:
    """Represents a calculated route."""
    origin: str
    destination: str
    origin_coords: Tuple[float, float]  # (lat, lon)
    destination_coords: Tuple[float, float]  # (lat, lon)
    total_distance_km: float
    segment_ids: List[str]
    risk_levels: List[str]
    water_depths: List[float]
    road_names: List[Optional[str]]
    geometry: List[List[Tuple[float, float]]]  # List of LineStrings

    @property
    def has_high_risk(self) -> bool:
        """Check if route contains HIGH or SEVERE risk segments."""
        return any(risk in ["HIGH", "SEVERE"] for risk in self.risk_levels)

    @property
    def max_depth(self) -> float:
        """Get maximum water depth on route."""
        return max(self.water_depths) if self.water_depths else 0.0


class OSMRoutingService:
    """Service for calculating flood-safe routes using OSM data."""

    def __init__(self, network: OSMRoadNetwork):
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
                road_names = []
                geometries = []
                total_distance = 0.0

                for seg_id in segment_ids:
                    seg = self.network.segments[seg_id]
                    risk_levels.append(seg.risk_level.value)
                    water_depths.append(seg.water_depth_cm)
                    road_names.append(seg.name)
                    geometries.append(seg.geometry)
                    total_distance += seg.distance_km

                origin_coords = self.network.nodes.get(origin, (0, 0))
                dest_coords = self.network.nodes.get(destination, (0, 0))

                return Route(
                    origin=origin,
                    destination=destination,
                    origin_coords=origin_coords,
                    destination_coords=dest_coords,
                    total_distance_km=total_distance,
                    segment_ids=segment_ids,
                    risk_levels=risk_levels,
                    water_depths=water_depths,
                    road_names=road_names,
                    geometry=geometries
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
        origin_lat: float,
        origin_lon: float,
        dest_lat: float,
        dest_lon: float,
        depth_threshold_cm: float = 15.0,
        flood_zones: Optional[List[Dict]] = None
    ) -> Dict:
        """
        Calculate both normal and safe routes between coordinates.

        Args:
            origin_lat, origin_lon: Start coordinates
            dest_lat, dest_lon: Destination coordinates
            depth_threshold_cm: Maximum acceptable water depth
            flood_zones: List of flood zone dicts

        Returns:
            Dict with route information or error
        """
        # Apply flood risk if zones provided
        if flood_zones:
            self.network.apply_flood_risk(flood_zones)

        # Find nearest nodes
        origin_node = self.network.find_nearest_node(origin_lat, origin_lon)
        dest_node = self.network.find_nearest_node(dest_lat, dest_lon)

        if not origin_node or not dest_node:
            return {'error': 'Could not find nearest road nodes for given coordinates'}

        if origin_node == dest_node:
            return {'error': 'Origin and destination are the same location'}

        # Get normal route
        normal_route = self.dijkstra(origin_node, dest_node, mode="normal")
        if not normal_route:
            return {'error': f'No route found between origin and destination'}

        # Get safe route
        safe_route = self.dijkstra(origin_node, dest_node, mode="safe")
        if not safe_route:
            return {'error': f'No safe route found between origin and destination'}

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

        # Build readable road name summary
        def get_road_summary(route: Route) -> str:
            unique_names = []
            seen = set()
            for name in route.road_names:
                if name and name not in seen:
                    unique_names.append(name)
                    seen.add(name)
                    if len(unique_names) >= 3:  # Limit to first 3 unique names
                        break

            if unique_names:
                summary = " → ".join(unique_names)
                if len(route.road_names) > len(unique_names):
                    summary += " → ..."
                return summary
            return "Unnamed roads"

        return {
            'normal_route': {
                'origin': normal_route.origin,
                'destination': normal_route.destination,
                'origin_coords': normal_route.origin_coords,
                'destination_coords': normal_route.destination_coords,
                'distance_km': round(normal_route.total_distance_km, 2),
                'segment_ids': normal_route.segment_ids,
                'risk_levels': normal_route.risk_levels,
                'water_depths': [round(d, 1) for d in normal_route.water_depths],
                'max_water_depth_cm': round(normal_route.max_depth, 1),
                'has_high_risk': normal_route.has_high_risk,
                'road_names': normal_route.road_names,
                'geometry': normal_route.geometry,
                'road_summary': get_road_summary(normal_route)
            },
            'safe_route': {
                'origin': safe_route.origin,
                'destination': safe_route.destination,
                'origin_coords': safe_route.origin_coords,
                'destination_coords': safe_route.destination_coords,
                'distance_km': round(safe_route.total_distance_km, 2),
                'segment_ids': safe_route.segment_ids,
                'risk_levels': safe_route.risk_levels,
                'water_depths': [round(d, 1) for d in safe_route.water_depths],
                'max_water_depth_cm': round(safe_route.max_depth, 1),
                'has_high_risk': safe_route.has_high_risk,
                'road_names': safe_route.road_names,
                'geometry': safe_route.geometry,
                'road_summary': get_road_summary(safe_route)
            },
            'needs_rerouting': needs_rerouting,
            'distance_increase_km': round(
                max(0, safe_route.total_distance_km - normal_route.total_distance_km), 2
            ),
            'affected_segments': affected_segments,
            'avoided_segments': avoided_segments,
            'reason': reason
        }
