"""
Cálculo del caudal máximo (L/s) para un regante según su posición geográfica.

La función principal `calcular_caudal_maximo` lee el KML del sistema de canales
y determina cuánta agua puede recibir físicamente un predio dado su distancia al
canal principal, a la bifurcación más cercana y la cantidad de usuarios aguas arriba
en la misma bifurcación.

Uso:
    from calculo_perdida.caudal_maximo import calcular_caudal_maximo

    resultado = calcular_caudal_maximo(
        lat=-30.0899, lon=-71.2464,
        kml_path="calculo_perdida/ejemplo/mapa valle pan de azúcar.kml",
    )
    print(resultado["caudal_max_ls"])  # L/s disponibles en el predio
"""

# ── Tabla de aforos Bellavista (inicio_km, termino_km, perdida_pct) ──────────
# Pérdidas negativas se tratan como 0 (afluencias o error de medición).
# Fuente: Tabla 3-5, Resumen de resultados aforos canal Bellavista.
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


def _calcular_perdida_canal(dist_km):
    """
    Pérdida acumulada (%) hasta dist_km usando los tramos de aforo.
    Composición multiplicativa por tramo; interpolación proporcional dentro
    del tramo parcial.
    """
    eficiencia = 1.0
    for inicio, termino, perdida_pct in TRAMOS_AFORO:
        p = max(0.0, perdida_pct) / 100.0
        if dist_km <= inicio:
            break
        elif dist_km >= termino:
            eficiencia *= (1.0 - p)
        else:
            fraccion = (dist_km - inicio) / (termino - inicio)
            eficiencia *= (1.0 - p * fraccion)
            break
    return round((1.0 - eficiencia) * 100, 2)


def calcular_caudal_maximo(lat, lon, kml_path,
                            q_inicial_ls=1145.0,
                            perdida_bif_pct_km=0.5,
                            penalizacion_upstream_ls=8.0):
    """
    Calcula el caudal máximo (L/s) disponible en el predio según su posición.

    Parámetros
    ----------
    lat, lon : float
        Coordenadas WGS-84 del predio (latitud, longitud).
    kml_path : str
        Ruta absoluta o relativa al KML del sistema de canales.
    q_inicial_ls : float
        Caudal medido en la cabecera del canal (L/s). Default: 1145 L/s.
    perdida_bif_pct_km : float
        Tasa de pérdida en bifurcaciones secundarias (%/km). Default: 0.5.
    penalizacion_upstream_ls : float
        Reducción de caudal por cada usuario aguas arriba en la misma
        bifurcación (L/s por usuario). Default: 8.0.

    Retorna
    -------
    dict con claves:
        caudal_max_ls      : caudal máximo disponible en el predio (L/s)
        eficiencia_pct     : eficiencia total canal+bifurcación (%)
        canal_km           : distancia al punto de conexión en el canal (km)
        bif_km             : distancia en la bifurcación (km)
        puntos_upstream    : usuarios aguas arriba en la misma bifurcación
        penalizacion_ls    : caudal descontado por usuarios upstream (L/s)
    """
    import pandas as pd
    import geopandas as gpd
    import pyogrio
    from shapely.geometry import Point

    kml_path = str(kml_path)

    # ── Leer todas las capas del KML ─────────────────────────────────────────
    kml_layers = [r[0] for r in pyogrio.list_layers(kml_path)]
    all_lines, all_points = [], []
    for layer_name in kml_layers:
        gdf = gpd.read_file(kml_path, layer=layer_name).to_crs(32719)
        lines  = gdf[gdf.geometry.type == "LineString"]
        points = gdf[gdf.geometry.type == "Point"]
        if not lines.empty:
            all_lines.append(lines)
        if not points.empty:
            all_points.append(points)

    if not all_lines:
        return _fallback(q_inicial_ls)

    lineas = pd.concat(all_lines, ignore_index=True)
    puntos = (pd.concat(all_points, ignore_index=True)
              if all_points else gpd.GeoDataFrame(geometry=[], crs=32719))

    # ── Canal principal (LineString más larga) y bifurcaciones ───────────────
    canal      = lineas.iloc[[lineas.length.idxmax()]]
    bif        = lineas.drop(canal.index)
    canal_line = canal.geometry.iloc[0]

    # ── Separar cortes y referencias ──────────────────────────────────────────
    if not puntos.empty and "Name" in puntos.columns:
        cortes     = puntos[puntos["Name"].str.lower().str.startswith("corte", na=False)].copy()
        referencias = puntos[~puntos.index.isin(cortes.index)].copy()
    else:
        cortes      = gpd.GeoDataFrame(geometry=[], crs=32719)
        referencias = puntos.copy() if not puntos.empty else gpd.GeoDataFrame(geometry=[], crs=32719)

    # ── Construir bif_info ────────────────────────────────────────────────────
    bif_info = []
    for idx, row in bif.iterrows():
        linea  = row.geometry
        inicio = Point(list(linea.coords)[0])
        corte_geom = cortes.loc[cortes.distance(inicio).idxmin()].geometry if not cortes.empty else inicio
        dist_canal = canal_line.project(canal_line.interpolate(canal_line.project(corte_geom)))
        bif_info.append({
            "idx":        idx,
            "linea":      linea,
            "dist_canal": dist_canal,
        })

    # ── Construir ref_data ────────────────────────────────────────────────────
    ref_data = []
    if not referencias.empty and bif_info:
        for _, row in referencias.iterrows():
            p      = row.geometry
            mejor  = min(bif_info, key=lambda b: b["linea"].distance(p))
            dist_b = mejor["linea"].project(mejor["linea"].interpolate(mejor["linea"].project(p)))
            ref_data.append({
                "geom":       p,
                "dist_canal": mejor["dist_canal"],
                "dist_bif":   dist_b,
                "bif_idx":    mejor["idx"],
            })

    if not ref_data:
        return _fallback(q_inicial_ls)

    # ── Punto más cercano al predio ───────────────────────────────────────────
    predio_geom = gpd.GeoSeries([Point(lon, lat)], crs=4326).to_crs(32719).iloc[0]
    mejor_ref   = min(ref_data, key=lambda r: predio_geom.distance(r["geom"]))

    canal_km = mejor_ref["dist_canal"] / 1000
    bif_km   = mejor_ref["dist_bif"]   / 1000

    # ── Usuarios aguas arriba en la misma bifurcación ────────────────────────
    puntos_upstream = sum(
        1 for ref in ref_data
        if ref["bif_idx"] == mejor_ref["bif_idx"]
        and ref["dist_bif"] < mejor_ref["dist_bif"]
    )
    penalizacion_ls = puntos_upstream * penalizacion_upstream_ls

    # ── Eficiencia por posición ───────────────────────────────────────────────
    efic_canal = 1 - _calcular_perdida_canal(canal_km) / 100
    efic_bif   = max(0.0, 1 - perdida_bif_pct_km * bif_km / 100)
    efic_total = efic_canal * efic_bif

    caudal_max_ls = max(0.0, q_inicial_ls * efic_total - penalizacion_ls)

    return {
        "caudal_max_ls":   round(caudal_max_ls, 2),
        "eficiencia_pct":  round(efic_total * 100, 2),
        "canal_km":        round(canal_km, 3),
        "bif_km":          round(bif_km, 3),
        "puntos_upstream": puntos_upstream,
        "penalizacion_ls": round(penalizacion_ls, 1),
    }


def _fallback(q_inicial_ls):
    """Resultado por defecto cuando el KML no tiene geometrías suficientes."""
    return {
        "caudal_max_ls":   round(q_inicial_ls * 0.26, 2),
        "eficiencia_pct":  26.0,
        "canal_km":        0.0,
        "bif_km":          0.0,
        "puntos_upstream": 0,
        "penalizacion_ls": 0.0,
    }
