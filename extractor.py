from typing import Dict, List, Set
import osmium
from models import GreenSpace, GreenSpaceType, Optional


class GreenSpaceExtractor:
    """Extracts green spaces from OSM PBF files"""
    
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
    
    def _create_green_space_from_way(self, way: osmium) -> Optional[GreenSpace]:
        """Create a GreenSpace object from an OSM way"""
        if not way.tags:
            return None
        
        # Convert tags to dictionary
        tags_dict = {tag.k: tag.v for tag in way.tags}
        
        # Check if this is a green space
        is_green_space = False
        for tag in way.tags:
            if ((tag.k == 'leisure' and tag.v in self._green_leisure) or
                (tag.k == 'landuse' and tag.v in self._green_landuse) or
                (tag.k == 'natural' and tag.v in self._green_natural)):
                is_green_space = True
                break
        
        if not is_green_space:
            return None
        
        # Extract basic information
        name = tags_dict.get('name', 'Unnamed')
        space_type = self._determine_space_type(tags_dict)
        
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
            node_ids=[node.ref for node in way.nodes]
        )
        
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
        is_green_space = False
        for tag in relation.tags:
            if ((tag.k == 'leisure' and tag.v in self._green_leisure) or
                (tag.k == 'landuse' and tag.v in self._green_landuse) or
                (tag.k == 'natural' and tag.v in self._green_natural)):
                is_green_space = True
                break
        
        if not is_green_space:
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
        """Extract all green spaces from a PBF file"""
        
        class GreenSpaceHandler(osmium.SimpleHandler):
            def __init__(self, extractor: 'GreenSpaceExtractor'):
                super().__init__()
                self.extractor = extractor
                self.green_spaces: List[GreenSpace] = []
            
            def way(self, w) -> None:
                green_space = self.extractor._create_green_space_from_way(w)
                if green_space:
                    self.green_spaces.append(green_space)
            
            def relation(self, r) -> None:
                green_space = self.extractor._create_green_space_from_relation(r)
                if green_space:
                    self.green_spaces.append(green_space)
        
        handler = GreenSpaceHandler(self)
        handler.apply_file(file_path)
        
        return handler.green_spaces
