import json

with open('data/roads/roads.geojson', 'r', encoding='utf-8') as f:
    data = json.load(f)

places = []
for f in data['features']:
    if f['geometry']['type'] == 'LineString':
        name = f['properties'].get('name')
        if name:
            places.append((name, f['geometry']['coordinates'][0]))
            
print("Sample places:")
# deduplicate names
seen = set()
for p in places:
    if p[0] not in seen:
        print(f"{{ id: '{p[1][1]},{p[1][0]}', name: '{p[0]}' }},")
        seen.add(p[0])
    if len(seen) >= 10:
        break
