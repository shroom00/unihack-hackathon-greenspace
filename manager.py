from typing import Any, Dict, List
from extractor import GreenSpaceExtractor
from models import GreenSpace
from picklecache import GreenSpacePickleCache
from storage import GreenSpaceCache

class GreenSpaceManager:
    """Main manager that handles extraction and caching automatically"""
    
    def __init__(self, cache_dir: str = "green_space_cache", use_cache: bool = True):
        self.extractor = GreenSpaceExtractor()
        self.cache = GreenSpaceCache(cache_dir)
        self.pickle_cache = GreenSpacePickleCache(cache_dir)
        self.use_cache = use_cache
    
    def get_green_spaces(self, pbf_file: str, force_refresh: bool = False) -> List[GreenSpace]:
        """
        Get green spaces - uses cache if available, otherwise extracts and caches
        """
        # Try to load from cache first
        if self.use_cache and not force_refresh:
            try:
                # Prefer pickle cache for speed
                if self.pickle_cache.cache_exists(pbf_file):
                    print("Loading from pickle cache")
                    return self.pickle_cache.load_from_pickle(pbf_file)
                elif self.cache.cache_exists(pbf_file):
                    return self.cache.load_from_json(pbf_file)
            except Exception as e:
                print(f"Cache loading failed, extracting fresh: {e}")
        
        # Extract from PBF file
        print(f"Extracting green spaces from {pbf_file}...")
        green_spaces = self.extractor.extract_from_file(pbf_file)
        
        # Cache the results
        if self.use_cache:
            try:
                # Save to both formats
                self.pickle_cache.save_to_pickle(green_spaces, pbf_file)
                self.cache.save_to_json(green_spaces, pbf_file)
            except Exception as e:
                print(f"Warning: Caching failed: {e}")
        
        return green_spaces
    
    def get_cache_info(self, pbf_file: str) -> Dict[str, Any]:
        """Get information about cache status"""
        json_exists = self.cache.cache_exists(pbf_file)
        pickle_exists = self.pickle_cache.cache_exists(pbf_file)
        
        info = {
            'json_cache_exists': json_exists,
            'pickle_cache_exists': pickle_exists,
            'any_cache_exists': json_exists or pickle_exists
        }
        
        if json_exists:
            json_path = self.cache._get_cache_path(pbf_file)
            info['json_size_mb'] = json_path.stat().st_size / (1024 * 1024)
        
        if pickle_exists:
            pickle_path = self.pickle_cache._get_cache_path(pbf_file)
            info['pickle_size_mb'] = pickle_path.stat().st_size / (1024 * 1024)
        
        return