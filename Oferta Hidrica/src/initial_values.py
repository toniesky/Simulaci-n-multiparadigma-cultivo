"""
Módulo de valores iniciales para el modelo de dinámica de sistemas
de gestión de agua - Caudal Regante

PARÁMETROS CONFIGURABLES - Edita aquí para cambiar el comportamiento del modelo
"""

# ============================== ACCIONES DE AGUA ==============================

# Número de acciones que tiene el regante
# Cada acción otorga derecho a usar agua
NUMERO_ACCIONES = 40

# Valor de una acción: 1 L/s durante HORAS_TURNO horas (m³ por turno)
# 1 L/s × 12 h × 3600 s/h / 1000 = 43.2 m³
HORAS_TURNO = 12
VALOR_ACCION = 43.2

# Agua máxima disponible sin desmarque
# = NUMERO_ACCIONES × VALOR_ACCION
AGUA_MAXIMA_REGANTE = NUMERO_ACCIONES * VALOR_ACCION  # m³/día

# Desmarque Inicial (antes de la fecha de cambio)
# Porcentaje de derechos superficiales que se pueden usar
PORCENTAJE_DESMARQUE_INICIAL = 0.15

# Desmarque Final (desde la fecha de cambio en adelante)
# Porcentaje de derechos superficiales que se pueden usar
PORCENTAJE_DESMARQUE_FINAL = 0.15

# Fecha de cambio de desmarque (mes-día, será aplicada cada año)
FECHA_DESMARQUE = "09-01"  # 1 de septiembre

# Salto entre escenarios de desmarque final
# Cada escenario suma/resta este valor al desmarque base

SALTO_DESMARQUE = 0.012

# ============================== AGUA SUBTERRÁNEA (RECARGAS) ==============================

# Eventos de recarga de agua subterránea
# Cada tupla: ("MM-DD", volumen_m3_recargado)
#   - "MM-DD": fecha en que ocurre la recarga (formato mes-día, se aplica cada año)
#   - volumen_m3_recargado: cantidad que se recarga ESE día (no acumulativo)
# Cada recarga se suma a la oferta total SOLO en el día de la recarga
# EJEMPLO: 20 m³ el 1-enero y 30 m³ el 1-julio = 50 m³ recargados en el año
RECARGAS_AGUA_SUBTERRANEA = [
   
]

# ============================== POSICIÓN GEOGRÁFICA DEL REGANTE ==============================

# Coordenadas WGS-84 del predio del regante (actualizadas desde app.py al seleccionar regante)
REGANTE_LATITUD = -30.0899
REGANTE_LONGITUD = -71.2464

# ============================== PARÁMETROS DEL CANAL (KML) ==============================

# Ruta al KML del sistema de canales (relativa a este archivo / src/)
KML_CANAL_PATH = "calculo_perdida/ejemplo/mapa valle pan de azúcar.kml"

# Caudal medido en la cabecera del canal (L/s) — Tabla 3-5, km 0.1
Q_INICIAL_LS = 1145.0

# Tasa de pérdida en bifurcaciones secundarias (%/km)
PERDIDA_BIF_PCT_KM = 0.5

# Penalización por cada usuario aguas arriba en la misma bifurcación (L/s)
PENALIZACION_UPSTREAM_LS = 10.0

# ============================== MANTENIMIENTO ==============================

# Duración del mantenimiento (días que permanece cerrado el canal)
DURACION_MANTENIMIENTO = 7

# CALENDARIO DE PARADAS (Días de inicio de cada período de mantenimiento)
# Especifica en qué días del año comienzan los períodos de mantenimiento
# Cada parada dura DURACION_MANTENIMIENTO días consecutivos
# Fuente: Aviso Asociación de Regantes Marcos — Calendario de cortas invierno 2026
CALENDARIO_PARADAS = [152, 174, 195, 218, 240]

# ============================== S,OCKS INICIALES ==============================

# El regante NO tiene caudal inicial
# Solo accede a agua en los días de desmarque (turno)
# No aplica: STOCK_INICIAL_CAUDAL = 0 (innecesario)
#
# LÓGICA DE DESMARQUE:
# - Antes de FECHA_DESMARQUE: PORCENTAJE_DESMARQUE_INICIAL (45%)
# - Desde FECHA_DESMARQUE en adelante: PORCENTAJE_DESMARQUE_FINAL (35%)

# ============================== TURNOS ==============================

# Frecuencia del turno: cada cuántos días toca turno (TASA)
FRECUENCIA_TURNO = 9

# Duración real del turno en días
DURACION_TURNO = 1  # días (el turno dura 1 día)

# ============================== TIEMPO DE SIMULACIÓN ==============================

# Período total de simulación (días)
TIEMPO_TOTAL = 400

# Paso de integración numérica (días)
PASO_SIMULACION = 1  # día

# Fecha de inicio de la simulación
FECHA_INICIO = "2026-01-01"

# NOTA: FECHA_DESMARQUE define cuándo cambia de desmarque inicial a desmarque final
# Formato: MM-DD (mes-día), se aplica cada año
#
# LÓGICA DE AGUA SUBTERRÁNEA:
# - Lista de recargas: RECARGAS_AGUA_SUBTERRANEA [("MM-DD", m³_recargados), ...]

# ============================== CAUDAL MÁXIMO (calculado desde posición) ==============================
# Se recalcula automáticamente cada vez que se carga este archivo.
# Usa REGANTE_LATITUD, REGANTE_LONGITUD y los parámetros del canal KML.
try:
    from pathlib import Path as _Path
    import sys as _sys
    _sys.path.insert(0, str(_Path(__file__).resolve().parent.parent))
    from calculo_perdida.caudal_maximo import calcular_caudal_maximo as _calc_qmax
    _kml_abs = (_Path(__file__).resolve().parent.parent / KML_CANAL_PATH).resolve()
    _qinfo = _calc_qmax(
        REGANTE_LATITUD, REGANTE_LONGITUD, str(_kml_abs),
        Q_INICIAL_LS, PERDIDA_BIF_PCT_KM, PENALIZACION_UPSTREAM_LS,
    )
    CAUDAL_MAXIMO_LS        = _qinfo["caudal_max_ls"]    # L/s disponibles en el predio
    EFICIENCIA_POSICION_PCT = _qinfo["eficiencia_pct"]   # % de eficiencia total
    CANAL_KM                = _qinfo["canal_km"]         # km hasta el predio en el canal
    BIF_KM                  = _qinfo["bif_km"]           # km en la bifurcación
    PUNTOS_UPSTREAM         = _qinfo["puntos_upstream"]  # usuarios aguas arriba
except Exception:
    # Fallback si el KML no está disponible
    CAUDAL_MAXIMO_LS        = round(Q_INICIAL_LS * 0.26, 2)
    EFICIENCIA_POSICION_PCT = 26.0
    CANAL_KM                = 0.0
    BIF_KM                  = 0.0
    PUNTOS_UPSTREAM         = 0
# - Cada recarga se agrega a la oferta total SOLO el día de la recarga
# - No hay consumo diario ni stock continuo
