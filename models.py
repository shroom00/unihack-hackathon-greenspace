from utils import escape
from typing import Dict, List, Optional, Set, Any
from dataclasses import dataclass, field
from enum import Enum

class GreenSpaceType(Enum):
    PARK = "park"
    FOREST = "forest"
    GARDEN = "garden"
    NATURE_RESERVE = "nature_reserve"
    MEADOW = "meadow"
    GRASSLAND = "grassland"
    WOOD = "wood"
    RECREATION_GROUND = "recreation_ground"
    OTHER = "other"

@dataclass
class Coordinates:
    """Represents geographic coordinates"""
    lat: float
    lon: float
    
    def __str__(self) -> str:
        return f"({self.lat:.6f}, {self.lon:.6f})"

@dataclass
class GreenSpace:
    """Represents a green space with all relevant information"""
    
    # Basic identification
    osm_id: int
    osm_type: str  # 'way', 'relation', 'node'
    name: str
    space_type: GreenSpaceType
    
    # Geographic information
    centroid: Optional[Coordinates] = None
    area_sq_m: Optional[float] = None
    perimeter_m: Optional[float] = None
    
    # Geometry - polygon coordinates for visualization
    coordinates: List[Coordinates] = field(default_factory=list)
    
    # OSM-specific data
    tags: Dict[str, str] = None
    version: int = 1
    changeset: int = 0
    timestamp: str = ""
    
    # Geometric properties (for ways)
    node_count: int = 0
    node_ids: List[int] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = {}
        if self.node_ids is None:
            self.node_ids = []
        if self.coordinates is None:
            self.coordinates = []
    
    @property
    def has_name(self) -> bool:
        """Check if this green space has a name"""
        return self.name != "Unnamed"
    
    @property
    def is_natural(self) -> bool:
        """Check if this is a natural green space (vs man-made)"""
        natural_types = {
            GreenSpaceType.FOREST, GreenSpaceType.WOOD, 
            GreenSpaceType.MEADOW, GreenSpaceType.GRASSLAND
        }
        return self.space_type in natural_types
    
    @property
    def is_recreational(self) -> bool:
        """Check if this is a recreational green space"""
        recreational_types = {
            GreenSpaceType.PARK, GreenSpaceType.GARDEN,
            GreenSpaceType.RECREATION_GROUND
        }
        return self.space_type in recreational_types
    
    @property
    def has_geometry(self) -> bool:
        """Check if this green space has polygon geometry"""
        return len(self.coordinates) > 0
    
    def get_tag(self, key: str, default: str = "") -> str:
        """Safely get a tag value"""
        return self.tags.get(key, default)
    
    def has_tag(self, key: str) -> bool:
        """Check if a tag exists"""
        return key in self.tags
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'osm_id': self.osm_id,
            'osm_type': self.osm_type,
            'name': escape(self.name),
            'space_type': self.space_type.value,
            'centroid': (self.centroid.lat, self.centroid.lon) if self.centroid else None,
            'coordinates': [(c.lat, c.lon) for c in self.coordinates] if self.coordinates else [],
            'area_sq_m': self.area_sq_m,
            'perimeter_m': self.perimeter_m,
            'tags': {k: escape(v) for k, v in self.tags.items()},
            'version': self.version,
            'changeset': self.changeset,
            'timestamp': self.timestamp,
            'node_count': self.node_count,
            'has_name': self.has_name,
            'is_natural': self.is_natural,
            'is_recreational': self.is_recreational,
            'has_geometry': self.has_geometry
        }
    
    def __str__(self) -> str:
        return f"{self.name} ({self.space_type.value}) - {self.osm_type} {self.osm_id}"