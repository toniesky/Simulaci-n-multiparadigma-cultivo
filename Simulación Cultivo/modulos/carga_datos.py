"""Carga de datos de entrada desde archivos CSV (clima, oferta, regantes, productividad)."""
import os
import pandas as pd
import parametros as P


def cargar_oferta_superficial_m3(base, dias_totales, dia_siembra, escenario):
    """Carga CalendarioOferta y devuelve la oferta superficial del canal (m3)
    y el indicador EnParada por dia, alineados al dia de siembra del regante.
    Retorna (oferta_m3: list, en_parada: list)."""
    ruta = os.path.normpath(os.path.join(base, P.ARCHIVO_OFERTA))
    df = pd.read_csv(ruta)
    df = df[df['Escenario'] == escenario].sort_values('Dia').reset_index(drop=True)
    if df.empty:
        raise ValueError(f"No hay datos para Escenario={escenario} en {ruta}")
    inicio = (P.DIA_INICIO_SIMULACION - 1) + (dia_siembra - 1)
    ventana = df.iloc[inicio:inicio + dias_totales]
    oferta_m3  = ventana['OfertaSuperficial'].astype(float).tolist()
    en_parada  = ventana['EnParada'].astype(int).tolist() if 'EnParada' in ventana.columns else []
    recarga_sub = (ventana['RecargaSubterranea'].astype(float).tolist()
                   if 'RecargaSubterranea' in ventana.columns else [])
    while len(oferta_m3) < dias_totales:
        oferta_m3.append(0.0)
    while len(en_parada) < dias_totales:
        en_parada.append(0)
    while len(recarga_sub) < dias_totales:
        recarga_sub.append(0.0)
    return oferta_m3, en_parada, recarga_sub

def listar_escenarios(base):
    """Devuelve la lista ordenada de escenarios disponibles en CalendarioOferta."""
    ruta = os.path.normpath(os.path.join(base, P.ARCHIVO_OFERTA))
    df = pd.read_csv(ruta)
    return sorted(df['Escenario'].unique().tolist())

def cargar_productividad(base):
    """Carga el CSV de productividad (ingreso/ha por mes, costo, rendimiento,
    unidad). Devuelve un DataFrame indexado por nombre de cultivo (lower).
    Si el archivo no existe, devuelve None (los KPIs economicos quedan n/d)."""
    ruta = os.path.join(base, P.ARCHIVO_PRODUCTIVIDAD)
    if not os.path.exists(ruta):
        return None
    df = pd.read_csv(ruta)
    df['nombre'] = df['nombre'].astype(str).str.strip().str.lower()
    return df.set_index('nombre')

def cargar_regante(base):
    """Carga EL regante seleccionado por P.REGANTE_ID (debe ser un int).
    Devuelve una pd.Series con sus parametros de manejo."""
    ruta = os.path.join(base, P.ARCHIVO_REGANTES)
    df = pd.read_csv(ruta)
    sel_id = getattr(P, 'REGANTE_ID', None)
    if sel_id is None or isinstance(sel_id, (list, tuple, set)):
        raise ValueError(
            "REGANTE_ID debe ser un entero (un solo regante por corrida). "
            f"Valor actual: {sel_id!r}")
    sub = df[df['id'] == sel_id]
    if sub.empty:
        ids = ', '.join(str(x) for x in df['id'].tolist())
        raise ValueError(
            f"REGANTE_ID={sel_id} no encontrado en {ruta}. Disponibles: {ids}")
    return sub.iloc[0]
