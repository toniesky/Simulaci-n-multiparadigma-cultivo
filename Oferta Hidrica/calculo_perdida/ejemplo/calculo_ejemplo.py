import math
from pathlib import Path
import pandas as pd
import geopandas as gpd
import folium
import pyogrio
from shapely.geometry import Point, LineString

_DIR = Path(__file__).resolve().parent
KML_FILE  = str(_DIR / "mapa valle pan de azúcar.kml")
CSV_FILE  = str(_DIR / "Indicadores_Regantes.csv")
HTML_FILE = str(_DIR / "Mapa_Regantes_Bellavista.html")

# ==========================
# CONFIGURACIÓN
# ==========================

REGANTES = [
    {"Nombre":"Predio 1", "Lat":-30.0899, "Lon":-71.2464},
    {"Nombre":"Predio 2", "Lat":-30.0453, "Lon":-71.2368},
    {"Nombre":"Predio 3", "Lat":-29.9940, "Lon":-71.2433},
    {"Nombre":"Predio 4", "Lat":-30.0403, "Lon":-71.2285},
    {"Nombre":"Predio 5", "Lat":-30.0119, "Lon":-71.2499},
    {"Nombre":"Predio 6", "Lat":-30.0287, "Lon":-71.2794},
    {"Nombre":"Predio 7", "Lat":-30.0949, "Lon":-71.2417},
    {"Nombre":"Predio 8", "Lat":-30.0729, "Lon":-71.2615},
    {"Nombre":"Predio 9", "Lat":-30.0456, "Lon":-71.2702},
    {"Nombre":"Predio 10","Lat":-30.0510, "Lon":-71.2609},
    {"Nombre":"Predio 11","Lat":-30.0178, "Lon":-71.2430},
    {"Nombre":"Predio 12","Lat":-30.0571, "Lon":-71.2563},
]

# Tasa de pérdida en bifurcaciones (canales secundarios).
# Mucho menor que el canal principal — ajustar según mediciones.
PERDIDA_BIF_PCT_KM = 0.5  # %/km

# Caudal medido en la cabecera del canal (Tabla 3-5, km 0.1)
Q_INICIAL_LS = 1.145 * 1000  # 1.145 m³/s → 1145 L/s

# Tabla 3-5: Aforos canal Bellavista — (inicio_km, termino_km, perdida_pct)
# Pérdidas negativas se tratan como 0 (afluencias o error de medición)
TRAMOS_AFORO = [
    ( 0.1,  1.8,  2.5),
    ( 1.8,  3.9, 11.6),
    ( 3.9,  6.3,  0.5),
    ( 6.3,  8.1,  7.1),
    # gap 8.1 – 12.4
    (12.4, 14.5,  0.0),
    (14.5, 15.5,  0.0),
    (15.5, 17.5, 10.0),
    (17.5, 19.8,  3.0),
    (19.8, 22.6,  6.0),
    (22.6, 25.0,  6.4),
    (25.0, 27.1,  0.0),
    (27.1, 30.5,  4.1),
    (30.5, 31.7,  0.0),
    (31.7, 32.9,  7.3),
    (32.9, 35.1, 16.9),
    (35.1, 36.8, 10.5),
    # gap 36.8 – 41.7
    (41.7, 45.2, 13.1),
    # gap 45.2 – 47.0
    (47.0, 48.5,  2.3),
    # gap 48.5 – 49.2
    (49.2, 50.0,  1.1),
    (50.0, 50.8,  7.6),
    # gap 50.8 – 52.2
    (52.2, 54.2, 17.4),
]


def calcular_perdida(dist_km):
    """
    Pérdida acumulada (%) hasta dist_km usando los tramos de aforo.
    Composición multiplicativa: cada tramo reduce el caudal remanente.
    Dentro del tramo parcial se interpola proporcionalmente.
    """
    eficiencia = 1.0
    for inicio, termino, perdida_pct in TRAMOS_AFORO:
        p = max(0.0, perdida_pct) / 100.0   # negativos → 0
        if dist_km <= inicio:
            break                            # aún no llegamos a este tramo
        elif dist_km >= termino:
            eficiencia *= (1.0 - p)          # tramo completo
        else:
            fraccion = (dist_km - inicio) / (termino - inicio)
            eficiencia *= (1.0 - p * fraccion)  # tramo parcial
            break
    return round((1.0 - eficiencia) * 100, 2)

# ==========================
# LECTURA
# ==========================

# Get all layers from the KML file
kml_layers = [row[0] for row in pyogrio.list_layers(KML_FILE)]

# Initialize lists to hold geometries from all layers
all_line_geometries_from_layers = []
all_point_geometries_from_layers = []

for layer_name in kml_layers:
    # Read each layer
    layer_gdf = gpd.read_file(KML_FILE, layer=layer_name, driver="KML")
    # Convert CRS for consistency
    layer_gdf = layer_gdf.to_crs(32719)

    # Separate LineString and Point geometries and append to respective lists
    lines_in_layer = layer_gdf[layer_gdf.geometry.type == "LineString"].copy()
    points_in_layer = layer_gdf[layer_gdf.geometry.type == "Point"].copy()

    if not lines_in_layer.empty:
        all_line_geometries_from_layers.append(lines_in_layer)
    if not points_in_layer.empty:
        all_point_geometries_from_layers.append(points_in_layer)

# Concatenate all LineString and Point GeoDataFrames
# Ensure that if lists are empty, we create an empty GeoDataFrame to avoid errors with pd.concat
lineas = pd.concat(all_line_geometries_from_layers, ignore_index=True) if all_line_geometries_from_layers else gpd.GeoDataFrame(geometry=[], crs=32719)
puntos = pd.concat(all_point_geometries_from_layers, ignore_index=True) if all_point_geometries_from_layers else gpd.GeoDataFrame(geometry=[], crs=32719)


# intenta detectar canal principal
canal = None
if not lineas.empty:
    # Find the longest LineString to be the main canal
    canal = lineas.iloc[[lineas.length.idxmax()]]

# Determine bifurcations
if canal is not None and not canal.empty:
    bif = lineas.drop(canal.index)
else:
    bif = gpd.GeoDataFrame(geometry=[], crs=32719) # No canal means no bifurcations

# Filter points for 'cortes' and 'referencias'
cortes = puntos[puntos["Name"].str.lower().str.startswith("corte", na=False)].copy() if not puntos.empty else gpd.GeoDataFrame(geometry=[], crs=32719)
referencias = puntos[~puntos.index.isin(cortes.index)].copy() if not puntos.empty else gpd.GeoDataFrame(geometry=[], crs=32719)

if canal is None or canal.empty:
    raise RuntimeError("No se encontró el canal principal incluso después de revisar todas las capas del KML. Asegúrese de que el archivo KML contenga al menos una geometría LineString para el canal principal.")

canal_line = canal.geometry.iloc[0]

# ==========================
# ASOCIAR BIFURCACIONES A CORTES
# ==========================

bif_info = []

for idx,row in bif.iterrows():
    linea = row.geometry
    inicio = Point(list(linea.coords)[0])

    corte = cortes.distance(inicio).idxmin()
    corte_geom = cortes.loc[corte].geometry

    dist_canal = canal_line.project(canal_line.interpolate(canal_line.project(corte_geom)))

    bif_info.append({
        "idx":idx,
        "linea":linea,
        "dist_canal":dist_canal,
        "inicio":inicio
    })

# ==========================
# ASOCIAR REFERENCIAS A BIFURCACIÓN
# ==========================

ref_data=[]

for idx,row in referencias.iterrows():
    p=row.geometry

    mejor=None
    mejor_d=1e20

    for b in bif_info:
        d=b["linea"].distance(p)
        if d<mejor_d:
            mejor_d=d
            mejor=b

    dist_bif=mejor["linea"].project(mejor["linea"].interpolate(mejor["linea"].project(p)))

    ref_data.append({
        "Nombre":row["Name"],
        "geom":p,
        "dist_canal":mejor["dist_canal"],
        "dist_bif":dist_bif,
        "bif_idx":mejor["idx"],   # bifurcación a la que pertenece este punto
    })

# ==========================
# CALCULAR PREDIOS
# ==========================

resultados=[]
ref_geom_predios=[]  # punto más cercano de cada predio (CRS 32719)

for r in REGANTES:

    predio=Point(r["Lon"],r["Lat"])
    predio=gpd.GeoSeries([predio],crs=4326).to_crs(32719).iloc[0]

    mejor=None
    mejor_d=1e20

    for ref in ref_data:
        d=predio.distance(ref["geom"])
        if d<mejor_d:
            mejor_d=d
            mejor=ref

    canal_km = mejor["dist_canal"] / 1000
    bif_km   = mejor["dist_bif"]   / 1000

    # Puntos de referencia en la MISMA bifurcación y ANTES del punto más cercano
    # (dist_bif menor = más cerca de la entrada → aguas arriba del predio)
    puntos_upstream = sum(
        1 for ref in ref_data
        if ref["bif_idx"] == mejor["bif_idx"]
        and ref["dist_bif"] < mejor["dist_bif"]
    )
    penalizacion_ls = puntos_upstream * 8.0

    # Pérdida canal: tabla de aforos (multiplicativa por tramo)
    efic_canal = 1 - calcular_perdida(canal_km) / 100
    # Pérdida bifurcación: tasa lineal mucho menor (PERDIDA_BIF_PCT_KM %/km)
    efic_bif   = max(0.0, 1 - PERDIDA_BIF_PCT_KM * bif_km / 100)
    # Eficiencia total: composición multiplicativa
    efic_total = efic_canal * efic_bif

    perdida_canal = round((1 - efic_canal) * 100, 2)
    perdida_bif   = round((1 - efic_bif)   * 100, 2)
    perdida_total = round((1 - efic_total)  * 100, 2)
    eficiencia    = round(efic_total * 100, 2)
    caudal_ls     = round(max(0.0, Q_INICIAL_LS * efic_total - penalizacion_ls), 2)

    resultados.append({
        "Predio":             r["Nombre"],
        "Canal_km":           round(canal_km, 3),
        "Bifurcacion_km":     round(bif_km,   3),
        "Perdida_Canal_%":    perdida_canal,
        "Perdida_Bif_%":      perdida_bif,
        "Perdida_Total_%":    perdida_total,
        "Eficiencia_%":       eficiencia,
        "Puntos_Upstream":    puntos_upstream,
        "Penalizacion_Ls":    penalizacion_ls,
        "Caudal_Recibido_Ls": caudal_ls,
    })
    ref_geom_predios.append(mejor["geom"])

df=pd.DataFrame(resultados)
print(df)
df.to_csv(CSV_FILE, index=False, encoding="utf-8-sig")

# ==========================
# MAPA
# ==========================

m=folium.Map(location=[-30.03,-71.24],zoom_start=12,tiles=None)
folium.TileLayer("OpenStreetMap").add_to(m)
folium.TileLayer(
    tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
    attr="Esri"
).add_to(m)

can4326=canal.to_crs(4326)
folium.GeoJson(can4326,style_function=lambda x:{"color":"blue","weight":4}).add_to(m)

for _,row in bif.to_crs(4326).iterrows():
    folium.GeoJson(row.geometry,style_function=lambda x:{"color":"green","weight":2}).add_to(m)

for _,row in cortes.to_crs(4326).iterrows():
    folium.CircleMarker(
        [row.geometry.y,row.geometry.x],
        radius=4,
        color="red",
        popup=row["Name"]
    ).add_to(m)

for ref in ref_data:
    p4326=gpd.GeoSeries([ref["geom"]],crs=32719).to_crs(4326).iloc[0]
    folium.CircleMarker(
        [p4326.y,p4326.x],
        radius=3,
        color="orange",
        fill=True,
        popup=ref["Nombre"]
    ).add_to(m)

for r,res,ref_geom in zip(REGANTES,resultados,ref_geom_predios):
    # Línea recta predio → punto de referencia más cercano
    ref_p4326 = gpd.GeoSeries([ref_geom], crs=32719).to_crs(4326).iloc[0]
    folium.PolyLine(
        locations=[[r["Lat"], r["Lon"]], [ref_p4326.y, ref_p4326.x]],
        color="white", weight=2, dash_array="6", opacity=0.8,
        tooltip=f"{res['Predio']} → ref más cercana",
    ).add_to(m)
    folium.Marker(
        [r["Lat"],r["Lon"]],
        popup=f"""
<b>{res['Predio']}</b><br>
Canal: {res['Canal_km']} km → {res['Perdida_Canal_%']} %<br>
Bifurcación: {res['Bifurcacion_km']} km → {res['Perdida_Bif_%']} %<br>
Puntos upstream: {res['Puntos_Upstream']} × 5 L/s = -{res['Penalizacion_Ls']} L/s<br>
<b>Pérdida total: {res['Perdida_Total_%']} %</b><br>
<b>Eficiencia: {res['Eficiencia_%']} %</b><br>
<b>Caudal recibido: {res['Caudal_Recibido_Ls']} L/s</b>
"""
    ).add_to(m)

folium.LayerControl().add_to(m)
m.save(HTML_FILE)

print("Proceso terminado.")
