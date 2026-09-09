import json

with open('data/roads/roads.geojson', 'r', encoding='utf-8') as f:
    data = json.load(f)

min_lon = 180
max_lon = -180
min_lat = 90
max_lat = -90

for f in data['features']:
    if f['geometry']['type'] == 'LineString':
        coords = f['geometry']['coordinates']
        for c in coords:
            min_lon = min(min_lon, c[0])
            max_lon = max(max_lon, c[0])
            min_lat = min(min_lat, c[1])
            max_lat = max(max_lat, c[1])

print(f"BBox: lon {min_lon:.4f} to {max_lon:.4f}, lat {min_lat:.4f} to {max_lat:.4f}")
