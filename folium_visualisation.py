from html import escape
import folium
from typing import List
import webbrowser
from pathlib import Path

from models import GreenSpace


def create_green_space_map(green_spaces: List[GreenSpace], name: str, population: int, total_area_km: int) -> str:
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

    # Create map with standard OpenStreetMap tiles
    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=13,
        tiles="OpenStreetMap",
        control_scale=True,
    )

    # Add alternative tile layers
    folium.TileLayer(
        tiles="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
        attr='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
        name="OpenStreetMap",
        overlay=False,
        control=True,
    ).add_to(m)

    folium.TileLayer(
        tiles="https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png",
        attr='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
        name="CartoDB Positron",
        overlay=False,
        control=True,
    ).add_to(m)

    # Color mapping for fills and borders - MORE VIBRANT COLORS
    type_colors = {
        "park": {"fill": "#32CD32", "border": "#228B22"},  # Lime green / Forest green
        "forest": {"fill": "#228B22", "border": "#006400"},  # Forest green / Dark green
        "garden": {"fill": "#7CFC00", "border": "#32CD32"},  # Lawn green / Lime green
        "nature_reserve": {
            "fill": "#FFD700",
            "border": "#FF8C00",
        },  # Gold / Dark orange
        "meadow": {
            "fill": "#ADFF2F",
            "border": "#9ACD32",
        },  # Green yellow / Yellow green
        "grassland": {
            "fill": "#90EE90",
            "border": "#32CD32",
        },  # Light green / Lime green
        "wood": {"fill": "#2E8B57", "border": "#006400"},  # Sea green / Dark green
        "recreation_ground": {
            "fill": "#87CEEB",
            "border": "#4682B4",
        },  # Sky blue / Steel blue
    }

    # Statistics
    spaces_with_geometry = 0
    spaces_without_geometry = 0
    total_green_area_sq_m = 0
    total_area_sq_m = total_area_km * 1000000
    spaces_with_area = 0

    # Create feature groups for better organization
    polygon_group = folium.FeatureGroup(name="Green Space Areas")
    marker_group = folium.FeatureGroup(name="Markers (no geometry)")

    # Add polygons and markers for each green space
    for space in green_spaces:
        if not space.centroid:
            continue

        # Get colors for this type
        colors = type_colors.get(
            space.space_type.value, {"fill": "#808080", "border": "#404040"}
        )

        # Create popup content with area info
        if space.area_sq_m:
            area_text = f"<br><b>Area:</b> {space.area_sq_m:,.0f} m²"
        else:
            area_text = "<br><b>Area:</b> Not calculated"

        geometry_text = (
            "<br>✓ Geometry available" if space.has_geometry else "<br>✗ No geometry"
        )
        popup_html = f"""
        <div style="min-width: 250px">
            <h4>{escape(space.name)}</h4>
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

            # Create polygon with more visible styling
            folium.Polygon(
                locations=locations,
                popup=folium.Popup(popup_html, max_width=300),
                tooltip=f"{escape(space.name)} ({space.space_type.value})",
                color=colors["border"],
                fill=True,
                fillColor=colors["fill"],
                fillOpacity=0.6,
                weight=3,
                opacity=1.0,
            ).add_to(polygon_group)

            spaces_with_geometry += 1

            # Track area statistics
            if space.area_sq_m:
                total_green_area_sq_m += space.area_sq_m
                spaces_with_area += 1
        else:
            # Fallback to marker if no geometry
            folium.Marker(
                location=[space.centroid.lat, space.centroid.lon],
                popup=folium.Popup(popup_html, max_width=300),
                tooltip=f"{space.name} ({space.space_type.value})",
                icon=folium.Icon(color="gray", icon="tree", prefix="fa"),
            ).add_to(marker_group)

            spaces_without_geometry += 1

    # Add feature groups to map
    polygon_group.add_to(m)
    marker_group.add_to(m)

    # Add layer control AFTER adding feature groups
    folium.LayerControl(position="topright").add_to(m)

    # Calculate total area in different units
    total_green_area_hectares = total_green_area_sq_m / 10000  # 1 hectare = 10,000 m²
    total_green_area_sq_km = total_green_area_sq_m / 1_000_000  # 1 km² = 1,000,000 m²

    # Add legend with statistics
    legend_html = f"""
    <div style="position: fixed; 
                top: 10px; left: 50px; width: 220px; height: auto; 
                background-color: white; border:2px solid grey; z-index:9999; 
                font-size:12px; padding: 10px; border-radius: 5px;">
    <h4 style="margin-top:0;">🌳 Green Spaces</h4>
    """

    for space_type, colors in type_colors.items():
        legend_html += f'<p style="margin: 4px 0;"><span style="color:{colors["fill"]}; font-size: 20px;">■</span> {space_type.replace("_", " ").title()}</p>'

    legend_html += f"""
    <hr style="margin: 8px 0;">
    <p style="margin: 4px 0;"><strong>Total Spaces:</strong> {len(green_spaces)}</p>
    <p style="margin: 4px 0;"><strong>With geometry:</strong> {spaces_with_geometry}</p>
    <p style="margin: 4px 0;"><strong>Markers only:</strong> {spaces_without_geometry}</p>
    <hr style="margin: 8px 0;">
    <p style="margin: 4px 0;"><strong>Total Area:</strong></p>
    <p style="margin: 4px 0; padding-left: 10px;">{total_area_sq_m:,.0f} m²</p>
    <p style="margin: 4px 0; padding-left: 10px;">{total_area_km:.2f} km²</p>
    <p style="margin: 4px 0;"><strong>Total Green Area:</strong></p>
    <p style="margin: 4px 0; padding-left: 10px;">{total_green_area_sq_m:,.0f} m²</p>
    <p style="margin: 4px 0; padding-left: 10px;">{total_green_area_sq_km:.2f} km²</p>
    <p style="margin: 4px 0; font-size: 10px; color: #666;">({spaces_with_area} spaces have area data)</p>
    <p style="margin: 4px 0;"><strong>Overall Green Area: {(total_green_area_sq_km/total_area_km)*100:.2f}%</strong></p>
    <p style="margin: 4px 0;"><strong>Population: {population} </strong></p>    
    </div>
    """

    m.get_root().html.add_child(folium.Element(legend_html))

    # Save map
    filename = f"green_spaces_interactive_map_{name.lower().replace(' ', '_')}.html"
    m.save(filename)

    print(f"\n📊 Visualization Statistics:")
    print(f"   Total green spaces: {len(green_spaces)}")
    print(f"   With polygon geometry: {spaces_with_geometry}")
    print(f"   Marker fallback: {spaces_without_geometry}")
    print(f"\n🌿 Total Green Space Area:")
    print(f"   {total_green_area_sq_m:,.0f} m²")
    print(f"   {total_green_area_hectares:,.2f} hectares")
    print(f"   {total_green_area_sq_km:.2f} km²")
    print(f"   ({spaces_with_area} spaces have area data)")

    return filename


def main():
    """Main function with proper error handling"""
    from manager import GreenSpaceManager

    for pbf_file, name, population, total_area_km in (
        ("west-midlands-251128.osm.pbf", "West Midlands", 5950757, 13004),
        ("staffordshire-251128.osm.pbf", "Staffordshire", 1177578, 2714),
    ):
        try:
            manager = GreenSpaceManager(name, population, total_area_km)

            print(f"===== {name} =====")
            print("Loading green spaces...")
            green_spaces = manager.get_green_spaces(pbf_file)
            print(f"✅ Loaded {len(green_spaces)} green spaces")

            # Create map
            print("Creating interactive map...")
            map_file = create_green_space_map(green_spaces, name, population, total_area_km)

            # Open in browser
            print(f"🌐 Opening map: {map_file}")
            webbrowser.open(f"file://{Path(map_file).absolute()}")

            print("✅ Map created successfully!")

        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback

            traceback.print_exc()


if __name__ == "__main__":
    main()
