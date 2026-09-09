"""
Road Data Service

Loads OpenStreetMap road data from GeoJSON and builds a routing graph.

The service:
1. Reads data/roads/roads.geojson
2. Extracts LineString geometries
3. Extracts OSM metadata (ID, name, highway type)
4. Builds a graph where intersections are nodes and roads are edges
5. Calculates edge costs based on actual geometry length
"""

import json
import logging
from math import radians, cos, sin, asin, sqrt
from typing import Dict, List, Tuple, Optional, Set
from pathlib import Path
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class RoadFeature:
    """Represents a road feature from GeoJSON."""
    osm_id: str
    name: Optional[str]
    highway_type: Optional[str]
    coordinates: List[Tuple[float, float]]  # [(lon, lat), ...]
    length_km: float


def haversine_distance(lon1: float, lat1: float, lon2: float, lat2: float) -> float:
    """
    Calculate the great circle distance between two points on Earth in kilometers.

    Args:
        lon1, lat1: First point (longitude, latitude) in degrees
        lon2, lat2: Second point (longitude, latitude) in degrees

    Returns:
        Distance in kilometers
    """
    # Convert to radians
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])

    # Haversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    r = 6371  # Radius of earth in kilometers
    return c * r


def calculate_line_length(coordinates: List[Tuple[float, float]]) -> float:
    """
    Calculate total length of a LineString in kilometers.

    Args:
        coordinates: List of (lon, lat) tuples

    Returns:
        Total length in kilometers
    """
    total = 0.0
    for i in range(len(coordinates) - 1):
        lon1, lat1 = coordinates[i]
        lon2, lat2 = coordinates[i + 1]
        total += haversine_distance(lon1, lat1, lon2, lat2)
    return total


def node_id_from_coords(lat: float, lon: float, precision: int = 6) -> str:
    """
    Generate a unique node ID from coordinates.

    Args:
        lat, lon: Coordinates in degrees
        precision: Decimal places to round to (default 6 ≈ 0.11m)

    Returns:
        Node ID string like "19.080000,72.880000"
    """
    return f"{round(lat, precision)},{round(lon, precision)}"


class RoadDataLoader:
    """Loads and processes OpenStreetMap road data from GeoJSON."""

    def __init__(self, geojson_path: str = "data/roads/roads.geojson"):
        self.geojson_path = geojson_path
        self.features: List[RoadFeature] = []
        self.nodes: Dict[str, Tuple[float, float]] = {}  # node_id -> (lat, lon)
        self.edges: List[Dict] = []  # List of edge dicts with metadata

    def load(self) -> bool:
        """
        Load GeoJSON file and extract road features.

        Returns:
            True if successful, False otherwise
        """
        try:
            # Try multiple paths in case working directory varies
            possible_paths = [
                Path(self.geojson_path),
                Path("../") / self.geojson_path,
                Path(".") / self.geojson_path,
            ]

            path = None
            for p in possible_paths:
                if p.exists():
                    path = p
                    break

            if path is None:
                logger.error(f"GeoJSON file not found: {self.geojson_path} (tried multiple paths)")
                return False

            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            if data.get('type') != 'FeatureCollection':
                logger.error("Invalid GeoJSON: not a FeatureCollection")
                return False

            features = data.get('features', [])
            logger.info(f"Loading {len(features)} features from {self.geojson_path}")

            for feature in features:
                if feature.get('geometry', {}).get('type') != 'LineString':
                    continue

                coords = feature['geometry']['coordinates']
                if len(coords) < 2:
                    continue

                # Convert to (lon, lat) tuples
                coords_tuples = [(c[0], c[1]) for c in coords]

                # Calculate length
                length_km = calculate_line_length(coords_tuples)

                # Extract properties
                props = feature.get('properties', {})
                osm_id = props.get('@id', feature.get('id', f'unknown_{len(self.features)}'))
                name = props.get('name')
                highway_type = props.get('highway')

                road_feature = RoadFeature(
                    osm_id=osm_id,
                    name=name,
                    highway_type=highway_type,
                    coordinates=coords_tuples,
                    length_km=length_km
                )

                self.features.append(road_feature)

            logger.info(f"Loaded {len(self.features)} road features")
            return True

        except Exception as e:
            logger.error(f"Failed to load GeoJSON: {e}")
            return False

    def build_graph(self):
        """
        Build routing graph from loaded features.

        Creates nodes at road intersections/endpoints and edges for road segments.
        """
        logger.info("Building routing graph...")

        # Track all coordinate occurrences to find intersections
        coord_counts: Dict[str, int] = {}
        coord_to_latlon: Dict[str, Tuple[float, float]] = {}

        for feature in self.features:
            for lon, lat in feature.coordinates:
                node_id = node_id_from_coords(lat, lon)
                coord_counts[node_id] = coord_counts.get(node_id, 0) + 1
                coord_to_latlon[node_id] = (lat, lon)

        # Nodes are intersections (used 3+ times) or endpoints (used once)
        # We'll create nodes at ALL unique coordinates for complete connectivity
        self.nodes = coord_to_latlon

        # Build edges from road features
        edge_id = 0
        for feature in self.features:
            coords = feature.coordinates

            # Create edges between consecutive coordinates
            for i in range(len(coords) - 1):
                lon1, lat1 = coords[i]
                lon2, lat2 = coords[i + 1]

                start_node = node_id_from_coords(lat1, lon1)
                end_node = node_id_from_coords(lat2, lon2)

                # Calculate segment length
                segment_length = haversine_distance(lon1, lat1, lon2, lat2)

                edge = {
                    'id': f"edge_{edge_id}",
                    'osm_way_id': feature.osm_id,
                    'start_node': start_node,
                    'end_node': end_node,
                    'length_km': segment_length,
                    'name': feature.name,
                    'highway_type': feature.highway_type,
                    'geometry': [(lon1, lat1), (lon2, lat2)]
                }

                self.edges.append(edge)
                edge_id += 1

        logger.info(f"Graph built: {len(self.nodes)} nodes, {len(self.edges)} edges")

    def get_nearest_node(self, lat: float, lon: float) -> Optional[str]:
        """
        Find the nearest node to given coordinates.

        Args:
            lat, lon: Query coordinates

        Returns:
            Node ID of nearest node, or None if no nodes exist
        """
        if not self.nodes:
            return None

        min_dist_sq = float('inf')
        nearest_node = None

        for node_id, (nlat, nlon) in self.nodes.items():
            # Use squared distance for efficiency (no sqrt needed)
            dlat = nlat - lat
            dlon = nlon - lon
            dist_sq = dlat * dlat + dlon * dlon

            if dist_sq < min_dist_sq:
                min_dist_sq = dist_sq
                nearest_node = node_id

        return nearest_node

    def get_node_coords(self, node_id: str) -> Optional[Tuple[float, float]]:
        """Get (lat, lon) coordinates for a node."""
        return self.nodes.get(node_id)

    def get_summary(self) -> Dict:
        """Get summary statistics of loaded road data."""
        total_length = sum(e['length_km'] for e in self.edges)

        # Count unique OSM ways
        unique_ways = len(set(e['osm_way_id'] for e in self.edges))

        # Count named roads
        named_roads = sum(1 for f in self.features if f.name)

        return {
            'total_features': len(self.features),
            'total_nodes': len(self.nodes),
            'total_edges': len(self.edges),
            'unique_osm_ways': unique_ways,
            'named_roads': named_roads,
            'total_length_km': round(total_length, 2),
            'geojson_path': self.geojson_path
        }
