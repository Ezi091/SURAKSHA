class SpatialIndex:
    def __init__(self):
        self.nodes = []

    def build(self, nodes_dict):
        self.nodes = list(nodes_dict.items()) # [('lat,lon', (lat, lon))]
        
    def nearest_node(self, lat, lon):
        best_dist = float('inf')
        best_node = None
        # simple linear scan
        for node_id, (nlat, nlon) in self.nodes:
            dlat = nlat - lat
            dlon = nlon - lon
            dist_sq = dlat*dlat + dlon*dlon
            if dist_sq < best_dist:
                best_dist = dist_sq
                best_node = node_id
        return best_node

s = SpatialIndex()
s.build({'node1': (19.0, 72.8), 'node2': (19.1, 72.9)})
print(s.nearest_node(19.05, 72.86))
