import json
from pathlib import Path
from datetime import datetime
from typing import List
from models import Coordinates, GreenSpace, GreenSpaceType  # Your previous classes

class GreenSpaceCache:
    """Cache green spaces to JSON files"""
    
    def __init__(self, cache_dir: str = "green_space_cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
    
    def _get_cache_path(self, pbf_file: str, format: str = "json") -> Path:
        """Generate cache file path from PBF filename"""
        pbf_path = Path(pbf_file)
        cache_name = f"{pbf_path.stem}_green_spaces.{format}"
        return self.cache_dir / cache_name
    
    def cache_exists(self, pbf_file: str, format: str = "json") -> bool:
        """Check if cache exists for a PBF file"""
        cache_path = self._get_cache_path(pbf_file, format)
        return cache_path.exists()
    
    def save_to_json(self, green_spaces: List[GreenSpace], pbf_file: str) -> None:
        """Save green spaces to JSON cache"""
        cache_path = self._get_cache_path(pbf_file, "json")
        
        # Convert to serializable format
        data = {
            'metadata': {
                'source_file': pbf_file,
                'export_date': datetime.now().isoformat(),
                'green_space_count': len(green_spaces)
            },
            'green_spaces': [space.to_dict() for space in green_spaces]
        }
        
        with open(cache_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"Cached {len(green_spaces)} green spaces to {cache_path}")
    
    def load_from_json(self, pbf_file: str) -> List[GreenSpace]:
        """Load green spaces from JSON cache"""
        cache_path = self._get_cache_path(pbf_file, "json")
        
        if not cache_path.exists():
            raise FileNotFoundError(f"Cache file not found: {cache_path}")
        
        with open(cache_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Reconstruct GreenSpace objects
        green_spaces = []
        for space_data in data['green_spaces']:
            # Reconstruct Coordinates object if exists
            centroid = None
            if space_data['centroid']:
                centroid = Coordinates(space_data['centroid'][0], space_data['centroid'][1])
            
            # Reconstruct GreenSpaceType
            space_type = GreenSpaceType(space_data['space_type'])
            
            green_space = GreenSpace(
                osm_id=space_data['osm_id'],
                osm_type=space_data['osm_type'],
                name=space_data['name'],
                space_type=space_type,
                centroid=centroid,
                area_sq_m=space_data['area_sq_m'],
                perimeter_m=space_data['perimeter_m'],
                tags=space_data['tags'],
                version=space_data['version'],
                changeset=space_data['changeset'],
                timestamp=space_data['timestamp'],
                node_count=space_data['node_count'],
                node_ids=space_data.get('node_ids', [])
            )
            green_spaces.append(green_space)
        
        print(f"Loaded {len(green_spaces)} green spaces from cache")
        return green_spaces
