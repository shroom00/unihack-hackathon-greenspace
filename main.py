
# Usage example with type hints and autocompletion
from typing import List
from extractor import GreenSpaceExtractor
from manager import GreenSpaceManager
from models import GreenSpace


def main():
    fp = "west-midlands-251128.osm.pbf"
    
    # Use this simple setup
    manager = GreenSpaceManager()

    green_spaces = manager.get_green_spaces(fp)

    print(f"Found {len(green_spaces)} green spaces")
    
    # Example usage with full autocompletion
    for space in green_spaces[:5]:
        print(f"\n{space}")
        print(f"  Type: {space.space_type.value}")
        print(f"  Has name: {space.has_name}")
        print(f"  Is natural: {space.is_natural}")
        print(f"  Is recreational: {space.is_recreational}")
        print(f"  Node count: {space.node_count}")
        
        # Access specific tags safely
        if space.has_tag('operator'):
            print(f"  Operator: {space.get_tag('operator')}")
        
        # Convert to dict if needed
        space_dict = space.to_dict()
        print(f"  As dict keys: {list(space_dict.keys())}")

if __name__ == "__main__":
    main()
