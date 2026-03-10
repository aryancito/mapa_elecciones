import geopandas as gpd

# Leer el archivo gpkg
gdf = gpd.read_file("data\PROVINCIA.gpkg")

# Reproyectar a WGS84
gdf = gdf.to_crs(epsg=4326)

# Guardar como GeoJSON
gdf.to_file("PROVINCIA.geojson", driver="GeoJSON")