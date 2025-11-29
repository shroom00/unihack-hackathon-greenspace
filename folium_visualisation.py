import folium
from typing import List
import webbrowser
from pathlib import Path

from models import GreenSpace

def create_green_space_map(green_spaces: List[GreenSpace], pbf_file: str = None) -> str:
    """
    Create a Folium map with green spaces drawn as polygons
    Returns the filename of the saved map
    """
    # Calculate center from first few spaces if they have centroids
    center_lat, center_lon = 52.4862, -1.8904  # Default: Birmingham
    
    # Try to find a better center from data
    valid_centroids = [s for s in green_spaces if s.centroid]
    if valid_centroids:
        avg_lat = sum(s.centroid.lat for s in valid_centroids) / len(valid_centroids)
        avg_lon = sum(s.centroid.lon for s in valid_centroids) / len(valid_centroids)
        center_lat, center_lon = avg_lat, avg_lon
    
    # Create map
    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=12,
        tiles='OpenStreetMap'
    )
    
    # Add different tile layers WITH ATTRIBUTIONS
    folium.TileLayer(
        'Stamen Terrain',
        attr='Map tiles by <a href="http://stamen.com">Stamen Design</a>, under <a href="http://creativecommons.org/licenses/by/3.0">CC BY 3.0</a>. Data by <a href="http://openstreetmap.org">OpenStreetMap</a>, under <a href="http://www.openstreetmap.org/copyright">ODbL</a>.'
    ).add_to(m)
    
    folium.TileLayer(
        'CartoDB positron',
        attr='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>'
    ).add_to(m)
    
    folium.TileLayer(
        'CartoDB dark_matter',
        attr='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>'
    ).add_to(m)
    
    folium.LayerControl().add_to(m)
    
    # Color mapping for fills and borders
    type_colors = {
        'park': {'fill': '#90EE90', 'border': '#228B22'},           # Light green / Forest green
        'forest': {'fill': '#228B22', 'border': '#006400'},         # Forest green / Dark green
        'garden': {'fill': '#98FB98', 'border': '#32CD32'},         # Pale green / Lime green
        'nature_reserve': {'fill': '#FFD700', 'border': '#FF8C00'}, # Gold / Dark orange
        'meadow': {'fill': '#ADFF2F', 'border': '#9ACD32'},         # Green yellow / Yellow green
        'grassland': {'fill': '#7CFC00', 'border': '#32CD32'},      # Lawn green / Lime green
        'wood': {'fill': '#2E8B57', 'border': '#006400'},           # Sea green / Dark green
        'recreation_ground': {'fill': '#87CEEB', 'border': '#4682B4'} # Sky blue / Steel blue
    }
    
    # Statistics
    spaces_with_geometry = 0
    spaces_without_geometry = 0
    
    # Create feature groups for better organization
    polygon_group = folium.FeatureGroup(name='Green Space Areas')
    marker_group = folium.FeatureGroup(name='Markers (no geometry)')
    
    # Add polygons and markers for each green space
    for space in green_spaces:
        if not space.centroid:
            continue
        
        # Get colors for this type
        colors = type_colors.get(space.space_type.value, {'fill': '#808080', 'border': '#404040'})
        
        # Create popup content
        area_text = f"<br>Area: {space.area_sq_m:.0f} m²" if space.area_sq_m else ""
        geometry_text = "<br>✓ Geometry available" if space.has_geometry else "<br>✗ No geometry"
        popup_html = f"""
        <div style="min-width: 250px">
            <h4>{space.name}</h4>
            <b>Type:</b> {space.space_type.value}<br>
            <b>OSM ID:</b> {space.osm_id}{area_text}{geometry_text}
            <br><br>
            <a href="https://www.openstreetmap.org/way/{space.osm_id}" 
               target="_blank" style="color: blue; text-decoration: underline;">
               View on OpenStreetMap
            </a>
        </div>
        """
        
        # Draw polygon if geometry is available
        if space.has_geometry and len(space.coordinates) >= 3:
            # Convert coordinates to list of [lat, lon] pairs
            locations = [[coord.lat, coord.lon] for coord in space.coordinates]
            
            # Create polygon
            folium.Polygon(
                locations=locations,
                popup=folium.Popup(popup_html, max_width=300),
                tooltip=f"{space.name} ({space.space_type.value})",
                color=colors['border'],
                fill=True,
                fillColor=colors['fill'],
                fillOpacity=0.5,
                weight=2,
                opacity=0.8
            ).add_to(polygon_group)
            
            spaces_with_geometry += 1
        else:
            # Fallback to marker if no geometry
            folium.Marker(
                location=[space.centroid.lat, space.centroid.lon],
                popup=folium.Popup(popup_html, max_width=300),
                tooltip=f"{space.name} ({space.space_type.value})",
                icon=folium.Icon(color='gray', icon='tree', prefix='fa')
            ).add_to(marker_group)
            
            spaces_without_geometry += 1
    
    # Add feature groups to map
    polygon_group.add_to(m)
    marker_group.add_to(m)
    
    # Add legend
    legend_html = f'''
    <div style="position: fixed; 
                top: 10px; left: 50px; width: 200px; height: auto; 
                background-color: white; border:2px solid grey; z-index:9999; 
                font-size:12px; padding: 10px; border-radius: 5px;">
    <h4 style="margin-top:0;">🌳 Green Spaces</h4>
    '''
    
    for space_type, colors in type_colors.items():
        legend_html += f'<p><span style="color:{colors["fill"]}; font-size: 20px;">■</span> {space_type.replace("_", " ").title()}</p>'
    
    legend_html += f'''
    <hr style="margin: 8px 0;">
    <p><strong>Total:</strong> {len(green_spaces)} spaces</p>
    <p><strong>With geometry:</strong> {spaces_with_geometry}</p>
    <p><strong>Markers only:</strong> {spaces_without_geometry}</p>
    </div>
    '''
    
    m.get_root().html.add_child(folium.Element(legend_html))
    
    # Save map
    filename = "green_spaces_interactive_map.html"
    m.save(filename)
    
    print(f"\n📊 Visualization Statistics:")
    print(f"   Total green spaces: {len(green_spaces)}")
    print(f"   With polygon geometry: {spaces_with_geometry}")
    print(f"   Marker fallback: {spaces_without_geometry}")
    
    return filename

def main():
    """Main function with proper error handling"""
    try:
        from manager import GreenSpaceManager
        
        # Load data
        manager = GreenSpaceManager()
        pbf_file = "west-midlands-251128.osm.pbf"  # Change to your file
        
        print("Loading green spaces...")
        green_spaces = manager.get_green_spaces(pbf_file)
        print(f"✅ Loaded {len(green_spaces)} green spaces")
        
        # Create map
        print("Creating interactive map...")
        map_file = create_green_space_map(green_spaces)
        
        # Open in browser
        print(f"🌐 Opening map: {map_file}")
        webbrowser.open(f'file://{Path(map_file).absolute()}')
        
        print("✅ Map created successfully!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()