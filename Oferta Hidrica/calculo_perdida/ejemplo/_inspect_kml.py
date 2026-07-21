import geopandas as gpd
import pyogrio

KML = "mapa valle pan de azúcar.kml"
layers = [r[0] for r in pyogrio.list_layers(KML)]
print("=== CAPAS DEL KML ===")
for l in layers:
    gdf = gpd.read_file(KML, layer=l)
    tipos = gdf.geometry.type.unique().tolist()
    print(f"  [{l}] -> {len(gdf)} features | tipos: {tipos}")
    if "Name" in gdf.columns:
        nombres = gdf["Name"].tolist()
        print(f"     Names: {nombres[:8]}")
    else:
        print("     (sin columna Name)")
