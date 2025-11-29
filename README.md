Setup Instructions
1. Ensure that you have the Python version 3.9-3.11 installed

2. You need atleast one OpenStreetMap pbf file that you want to map, e.g:
staffordshire-251128.osm.pbf  
west-midlands-251128.osm.pbf

2. Before running the script, ensure that you have the following Python packages installed:
pip install folium
pip install pyproj shapely
pip install osmium

3. To create the interactive web page, simply run folium.visualisation.pyproj

4. Customising the Input Region
In the main() function, modify this tuple:
for pfb_file, name, population, total_area_km_in (
    ("staffordshire-251128.osm.pbf", "Staffordshire", 1177578, 2714),
);

You can list multiple regions:
for pbf_file, name, population, total_area_km in (
    ("west-midlands.osm.pbf", "West Midlands", 5950757, 13004),
    ("staffordshire.osm.pbf", "Staffordshire", 1177578, 2714),
    ("cheshire.osm.pbf", "Cheshire", 1055866, 2343),
):

5. View the generated Green Map
