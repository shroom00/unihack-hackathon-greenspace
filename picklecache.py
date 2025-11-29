from datetime import datetime
from pathlib import Path
import pickle
import gzip
from typing import List

from models import GreenSpace

class GreenSpacePickleCache:
    """Cache green spaces using pickle (faster, preserves objects exactly)"""
    
    def __init__(self, cache_dir: str = "green_space_cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
    
    def _get_cache_path(self, pbf_file: str, compressed: bool = True) -> Path:
        pbf_path = Path(pbf_file)
        ext = "pkl.gz" if compressed else "pkl"
        cache_name = f"{pbf_path.stem}_green_spaces.{ext}"
        return self.cache_dir / cache_name
    

    def cache_exists(self, pbf_file: str, format: str = "json") -> bool:
        """Check if cache exists for a PBF file"""
        cache_path = self._get_cache_path(pbf_file, format)
        return cache_path.exists()
    
    def save_to_pickle(self, name: str, population: int, total_area_km: float, green_spaces: List[GreenSpace], pbf_file: str, compress: bool = True) -> None:
        """Save to pickle format (much faster than JSON)"""
        cache_path = self._get_cache_path(pbf_file, compress)
        
        data = {
            'metadata': {
                'source_file': pbf_file,
                'export_date': datetime.now(),
                'green_space_count': len(green_spaces),
                "name": name,
                "population": population,
                "total_area_km": total_area_km
            },
            'green_spaces': green_spaces
        }
        
        if compress:
            with gzip.open(cache_path, 'wb') as f:
                pickle.dump(data, f, pickle.HIGHEST_PROTOCOL)
        else:
            with open(cache_path, 'wb') as f:
                pickle.dump(data, f, pickle.HIGHEST_PROTOCOL)
        
        print(f"Cached {len(green_spaces)} green spaces to {cache_path}")
    
    def load_from_pickle(self, pbf_file: str, compressed: bool = True) -> List[GreenSpace]:
        """Load from pickle cache"""
        cache_path = self._get_cache_path(pbf_file, compressed)
        
        if not cache_path.exists():
            raise FileNotFoundError(f"Cache file not found: {cache_path}")
        
        if compressed:
            with gzip.open(cache_path, 'rb') as f:
                data = pickle.load(f)
        else:
            with open(cache_path, 'rb') as f:
                data = pickle.load(f)
        
        print(f"Loaded {len(data['green_spaces'])} green spaces from cache")
        return data['green_spaces']