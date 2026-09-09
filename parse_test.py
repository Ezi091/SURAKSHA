import json
import logging
from math import radians, cos, sin, asin, sqrt

logging.basicConfig(level=logging.INFO)

def haversine(lon1, lat1, lon2, lat2):
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    dlon = lon2 - lon1 
    dlat = lat2 - lat1 
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a)) 
    r = 6371 
    return c * r

with open('data/roads/roads.geojson', 'r', encoding='utf-8') as f:
    data = json.load(f)

print(f"Loaded {len(data['features'])} features")
nodes = set()
total_len = 0
for f in data['features']:
    if f['geometry']['type'] == 'LineString':
        coords = f['geometry']['coordinates']
        for c in coords:
            nodes.add( (round(c[1], 6), round(c[0], 6)) )
        for i in range(len(coords)-1):
            total_len += haversine(coords[i][0], coords[i][1], coords[i+1][0], coords[i+1][1])

print(f"Total nodes: {len(nodes)}")
print(f"Total length: {total_len:.2f} km")
