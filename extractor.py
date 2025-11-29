from typing import Dict, List, Set
import osmium
from models import GreenSpace, GreenSpaceType, Coordinates, Optional


class GreenSpaceExtractor:
    """Extracts green spaces from OSM PBF files with optimized memory usage"""
    
    def __init__(self):
        self._green_leisure: Set[str] = {'park', 'garden', 'nature_reserve', 'recreation_ground'}
        self._green_landuse: Set[str] = {'forest', 'meadow', 'grass', 'recreation_ground', 'orchard'}
        self._green_natural: Set[str] = {'wood', 'grassland', 'heath'}
        
        # Mapping from OSM tag values to GreenSpaceType enum
        self._type_mapping: Dict[str, GreenSpaceType] = {
            'park': GreenSpaceType.PARK,
            'forest': GreenSpaceType.FOREST,
            'garden': GreenSpaceType.GARDEN,
            'nature_reserve': GreenSpaceType.NATURE_RESERVE,
            'meadow': GreenSpaceType.MEADOW,
            'grassland': GreenSpaceType.GRASSLAND,
            'wood': GreenSpaceType.WOOD,
            'recreation_ground': GreenSpaceType.RECREATION_GROUND
        }
        
        # Store only needed node IDs (first pass)
        self._needed_node_ids: Set[int] = set()
        # Store only needed node coordinates (second pass)
        self._node_coords: Dict[int, Coordinates] = {}
    
    def _determine_space_type(self, tags: Dict[str, str]) -> GreenSpaceType:
        """Determine the green space type from OSM tags"""
        # Check leisure tags first
        if 'leisure' in tags:
            leisure_val = tags['leisure']
            if leisure_val in self._type_mapping:
                return self._type_mapping[leisure_val]
        
        # Check landuse tags
        if 'landuse' in tags:
            landuse_val = tags['landuse']
            if landuse_val in self._type_mapping:
                return self._type_mapping[landuse_val]
        
        # Check natural tags
        if 'natural' in tags:
            natural_val = tags['natural']
            if natural_val in self._type_mapping:
                return self._type_mapping[natural_val]
        
        return GreenSpaceType.OTHER
    
    def _is_green_space_tags(self, tags) -> bool:
        """Check if tags indicate a green space"""
        for tag in tags:
            if ((tag.k == 'leisure' and tag.v in self._green_leisure) or
                (tag.k == 'landuse' and tag.v in self._green_landuse) or
                (tag.k == 'natural' and tag.v in self._green_natural)):
                return True
        return False
    
    def _calculate_centroid(self, coordinates: List[Coordinates]) -> Optional[Coordinates]:
        """Calculate centroid of a polygon"""
        if not coordinates:
            return None
        
        avg_lat = sum(c.lat for c in coordinates) / len(coordinates)
        avg_lon = sum(c.lon for c in coordinates) / len(coordinates)
        return Coordinates(lat=avg_lat, lon=avg_lon)
    
    def _create_green_space_from_way(self, way: osmium, include_geometry: bool = True) -> Optional[GreenSpace]:
        """Create a GreenSpace object from an OSM way"""
        if not way.tags:
            return None
        
        # Convert tags to dictionary
        tags_dict = {tag.k: tag.v for tag in way.tags}
        
        # Check if this is a green space
        if not self._is_green_space_tags(way.tags):
            return None
        
        # Extract basic information
        name = tags_dict.get('name', 'Unnamed')
        space_type = self._determine_space_type(tags_dict)
        
        # Get node coordinates if available
        coordinates = []
        if include_geometry:
            for node in way.nodes:
                if node.ref in self._node_coords:
                    coordinates.append(self._node_coords[node.ref])
        
        # Calculate centroid
        centroid = self._calculate_centroid(coordinates) if coordinates else None
        
        # Create GreenSpace object
        green_space = GreenSpace(
            osm_id=way.id,
            osm_type='way',
            name=name,
            space_type=space_type,
            tags=tags_dict,
            version=way.version,
            changeset=way.changeset,
            timestamp=str(way.timestamp) if way.timestamp else "",
            node_count=len(way.nodes),
            node_ids=[node.ref for node in way.nodes],
            centroid=centroid
        )
        
        # Store coordinates in green_space for visualization
        if coordinates:
            green_space.coordinates = coordinates
        
        # Try to extract area if available
        if 'area' in tags_dict:
            try:
                green_space.area_sq_m = float(tags_dict['area'])
            except (ValueError, TypeError):
                pass
        
        return green_space
    
    def _create_green_space_from_relation(self, relation) -> Optional[GreenSpace]:
        """Create a GreenSpace object from an OSM relation"""
        if not relation.tags:
            return None
        
        # Convert tags to dictionary
        tags_dict = {tag.k: tag.v for tag in relation.tags}
        
        # Check if this is a green space
        if not self._is_green_space_tags(relation.tags):
            return None
        
        # Extract basic information
        name = tags_dict.get('name', 'Unnamed')
        space_type = self._determine_space_type(tags_dict)
        
        # Create GreenSpace object
        green_space = GreenSpace(
            osm_id=relation.id,
            osm_type='relation',
            name=name,
            space_type=space_type,
            tags=tags_dict,
            version=relation.version,
            changeset=relation.changeset,
            timestamp=str(relation.timestamp) if relation.timestamp else "",
            node_count=0,  # Relations don't have direct node count
            node_ids=[]    # Relations have members, not direct nodes
        )
        
        return green_space
    
    def extract_from_file(self, file_path: str) -> List[GreenSpace]:
        """Extract all green spaces from a PBF file with optimized memory usage"""
        
        # Pass 1: Identify which node IDs we actually need
        print("Pass 1: Identifying needed nodes...")
        
        class NodeIdentifier(osmium.SimpleHandler):
            def __init__(self, extractor: 'GreenSpaceExtractor'):
                super().__init__()
                self.extractor = extractor
                self.green_way_count = 0
            
            def way(self, w):
                if w.tags and self.extractor._is_green_space_tags(w.tags):
                    # This is a green space way, remember all its nodes
                    for node in w.nodes:
                        self.extractor._needed_node_ids.add(node.ref)
                    self.green_way_count += 1
        
        identifier = NodeIdentifier(self)
        identifier.apply_file(file_path)
        print(f"Found {identifier.green_way_count} green space ways")
        print(f"Need coordinates for {len(self._needed_node_ids)} nodes")
        
        # Pass 2: Load only the coordinates we need
        print("Pass 2: Loading required node coordinates...")
        
        class NodeCollector(osmium.SimpleHandler):
            def __init__(self, extractor: 'GreenSpaceExtractor'):
                super().__init__()
                self.extractor = extractor
                self.loaded_count = 0
            
            def node(self, n):
                # Only store coordinates for nodes we actually need
                if n.id in self.extractor._needed_node_ids:
                    self.extractor._node_coords[n.id] = Coordinates(
                        lat=n.location.lat,
                        lon=n.location.lon
                    )
                    self.loaded_count += 1
        
        node_collector = NodeCollector(self)
        node_collector.apply_file(file_path, locations=True)
        print(f"Loaded {node_collector.loaded_count} node coordinates")
        
        # Clear the needed IDs set to free memory
        self._needed_node_ids.clear()
        
        # Pass 3: Extract green spaces with geometry
        print("Pass 3: Extracting green spaces with geometry...")
        
        class GreenSpaceHandler(osmium.SimpleHandler):
            def __init__(self, extractor: 'GreenSpaceExtractor'):
                super().__init__()
                self.extractor = extractor
                self.green_spaces: List[GreenSpace] = []
            
            def way(self, w) -> None:
                green_space = self.extractor._create_green_space_from_way(w, include_geometry=True)
                if green_space:
                    self.green_spaces.append(green_space)
            
            def relation(self, r) -> None:
                green_space = self.extractor._create_green_space_from_relation(r)
                if green_space:
                    self.green_spaces.append(green_space)
        
        handler = GreenSpaceHandler(self)
        handler.apply_file(file_path)
        
        print(f"Extracted {len(handler.green_spaces)} green spaces")
        
        # Clear node coordinates to free memory
        self._node_coords.clear()
        
        return handler.green_spaces