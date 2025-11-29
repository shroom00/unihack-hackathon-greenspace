import osmium

def extract_green_spaces(file_path):
    """Extract only green space data from PBF file"""
    
    class GreenSpaceHandler(osmium.SimpleHandler):
        def __init__(self):
            super().__init__()
            self.green_spaces = []
        
        def is_green_space(self, tags):
            """Check if element is a green space"""
            green_tags = {
                'leisure': ['park', 'garden', 'nature_reserve', 'recreation_ground'],
                'landuse': ['forest', 'meadow', 'grass', 'recreation_ground'],
                'natural': ['wood', 'grassland', 'heath']
            }
            
            for key, values in green_tags.items():
                if key in tags and tags[key] in values:
                    return True
            return False
        
        def node(self, n):
            if n.tags and self.is_green_space(dict(n.tags)):
                self.green_spaces.append({
                    'type': 'node',
                    'id': n.id,
                    'lat': n.location.lat,
                    'lon': n.location.lon,
                    'tags': dict(n.tags)
                })
        
        def way(self, w):
            if w.tags and self.is_green_space(dict(w.tags)):
                self.green_spaces.append({
                    'type': 'way',
                    'id': w.id,
                    'node_count': len(w.nodes),
                    'tags': dict(w.tags)
                })
        
        def relation(self, r):
            if r.tags and self.is_green_space(dict(r.tags)):
                self.green_spaces.append({
                    'type': 'relation',
                    'id': r.id,
                    'member_count': len(r.members),
                    'tags': dict(r.tags)
                })
    
    handler = GreenSpaceHandler()
    handler.apply_file(file_path)
    
    return handler.green_spaces

# Usage
green_spaces = extract_green_spaces("west-midlands-251128.osm.pbf")

print(f"Found {len(green_spaces)} green space elements")
print("\nGreen Spaces:")
for space in green_spaces:
    name = space['tags'].get('name', 'Unnamed')
    element_type = space['type']
    print(f"{element_type.upper()} {space['id']}: {name}")
    print(f"  Tags: {space['tags']}")
