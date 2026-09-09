import json
import logging
from math import radians, cos, sin, asin, sqrt

def haversine(lon1, lat1, lon2, lat2):
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    dlon = lon2 - lon1 
    dlat = lat2 - lat1 
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a)) 
    r = 6371 
    return c * r

def point_to_segment_dist_meters(px, py, x1, y1, x2, y2):
    # px, py, x1, y1, x2, y2 are lon, lat
    # Convert to locally flat metric space (meters)
    # Reference point is p
    deg_lat_m = 111320.0
    deg_lon_m = 111320.0 * cos(radians(py))
    
    px_m, py_m = 0.0, 0.0
    x1_m = (x1 - px) * deg_lon_m
    y1_m = (y1 - py) * deg_lat_m
    x2_m = (x2 - px) * deg_lon_m
    y2_m = (y2 - py) * deg_lat_m
    
    # Distance from (0,0) to line segment (x1_m,y1_m)-(x2_m,y2_m)
    dx = x2_m - x1_m
    dy = y2_m - y1_m
    if dx == 0 and dy == 0:
        return sqrt(x1_m**2 + y1_m**2)
    
    t = -(x1_m * dx + y1_m * dy) / (dx**2 + dy**2)
    t = max(0, min(1, t))
    
    closest_x = x1_m + t * dx
    closest_y = y1_m + t * dy
    return sqrt(closest_x**2 + closest_y**2)

print(point_to_segment_dist_meters(72.880, 19.080, 72.880, 19.080, 72.881, 19.080))
