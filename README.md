Setup Instructions

1. Ensure that you have the Python version 3.9-3.11 installed

2. You need atleast one OpenStreetMap pbf file that you want to map, e.g:
   staffordshire-251128.osm.pbf  
   west-midlands-251128.osm.pbf

3. Before running the script, ensure that you have the following Python packages installed:
   pip install folium
   pip install shapely
   pip install osmium

4. To create the interactive web page, simply run folium_visualisation.py

5. Customising the Input Region
   In the main() function, modify the nested tuple containing pfb_file, name, population and total_area_km_in.

   You can list multiple regions:
   for pbf_file, name, population, total_area_km in (
   ("west-midlands.osm.pbf", "West Midlands", 5950757, 13004),
   ("staffordshire.osm.pbf", "Staffordshire", 1177578, 2714),
   ("cheshire.osm.pbf", "Cheshire", 1055866, 2343),
   ):

6. View the generated Green Map
   Run main.py to launch the flask webserver
