"""
Parámetros de simulación de demanda hídrica del cultivo.
Modificar aquí los valores para ajustar el escenario.
"""

# ---------- Regante seleccionado ----------
# La simulacion usa UN solo regante por corrida. El regante aporta SOLO los
# parametros de manejo (hectareas, fraccion cultivada, frecuencia de turno,
# capacidad y nivel inicial de estanque). Los cultivos se iteran TODOS desde
# data_cultivos.csv y se cruzan con cada escenario del CalendarioOferta.
REGANTE_ID = 1

# ---------- Dia de siembra global ----------
# Indice 1-based del dia de siembra (offset relativo a DIA_INICIO_SIMULACION).
# Aplica a TODOS los cultivos por igual. siembra=1 -> el cultivo arranca el
# mismo dia que DIA_INICIO_SIMULACION; siembra=15 -> 14 dias despues.
DIA_SIEMBRA = 1

# ---------- Archivos de entrada ----------
ARCHIVO_REGANTES      = 'inputs/regantes.csv'
ARCHIVO_CULTIVOS           = 'inputs/data_cultivos.csv'
ARCHIVO_CALENDARIO_SIEMBRA = 'inputs/calendario_siembra.csv'  # 1=disponible por mes de inicio
ARCHIVO_CLIMA              = 'inputs/datosclima.csv'
ARCHIVO_PRODUCTIVIDAD = 'inputs/productividad_cultivos.csv'
DIR_SALIDA            = 'outputs'

# ---------- Dia de inicio global de la simulacion ----------
# Indice 1-based del primer dia que se toma del CSV de clima y del
# CalendarioOferta. El 'dia_siembra' de cada regante en regantes.csv se
# interpreta como offset relativo a este origen (siembra=1 -> empieza el
# mismo dia; siembra=15 -> empieza 14 dias despues del inicio global).
#   1   -> arranca el 01 de enero del CSV de clima
#   91  -> arranca aprox. 1 de abril, etc.
#   213 -> arranca el 01 de agosto
DIA_INICIO_SIMULACION = 213

# ---------- Propiedades de suelo (FAO-56) ----------
# Contenido de humedad volumétrico
CC = 0.164
PMP = 0.082

# Profundidad de la capa superficial evaporante (m)
Ze_evap = 0.15   # FAO-56 recomienda 0.10 - 0.15 m

# ---------- Reservorios de agua del suelo ----------
# AET (TEW): agua total evaporable de la capa superficial (mm)
#   AET = 1000 * (CC - 0.5 * PMP) * Ze_evap
AET = 1000.0 * (CC - 0.5 * PMP) * Ze_evap   # ≈ 25 mm

# AFE (REW): agua fácilmente evaporable (mm). FAO-56 tabla 19: 8-10 mm para suelo medio
AFE = 8.0

# ---------- Condiciones iniciales de los déficits ----------
# 0 = suelo a capacidad de campo (sin déficit)
De0 = 0.0   # déficit evaporación inicial (mm)
Dr0 = 0.0   # déficit zona radicular inicial (mm) — 0 = suelo a CC al inicio de siembra

# ---------- Oferta del canal ----------
# La simulación itera automáticamente sobre TODOS los escenarios presentes
# en CalendarioOferta.csv (columna 'Escenario'). El reporte consolidado
# se genera en outputs/ReporteEscenarios.{png,csv}.
ARCHIVO_OFERTA = '../Oferta Hidrica/data/outputs/CalendarioOferta.csv'

# ---------- Stock de agua subterránea ----------
# Volumen inicial del acuífero disponible para el regante (m3). Se va
# descontando día a día cada vez que el regante extrae de aquí para
# complementar la oferta superficial.
STOCK_SUBTERRANEO_INICIAL_M3 = 0.0

# Umbral de días consecutivos SIN riego que habilita usar la oferta
# subterránea para cubrir la demanda. El pozo es independiente del turno
# del canal: cualquier día puede activarse si se cumple esta condición.
DIAS_SIN_RIEGO_PARA_SUBTERRANEA = 0

# ---------- Retención no lineal de humedad por textura de suelo ----------
# Factor multiplicativo f(H) = H^ALPHA_SUELO aplicado a la transpiración
# (Ks * Kcb * ETo). H es el % de agua útil disponible normalizado [0,1]
# que se calcula del déficit radicular Dr. NO afecta a la evaporación Es.
# Valores orientativos por textura:
#   arenoso:        1.2 - 1.5
#   franco:         1.5 - 2.0
#   franco-arcill.: 2.0 - 3.0
#   arcilloso:      3.0 - 5.0
ALPHA_SUELO = 3.2

# ---------- Fracción de drenaje por textura de suelo ----------
# Fracción del agua aplicada (riego + precipitación) que drena inmediatamente
# por debajo de la zona radicular sin quedar disponible para el cultivo.
# Modela cómo la textura condiciona el estado de humedad del suelo al final
# del día dado un volumen de agua introducido. Solo afecta al balance de Dr
# (zona radicular). La capa de evaporación superficial (De) no se modifica.
# Calibrable con sensor volumétrico: medir theta antes y ~24 h después de
# un riego conocido sin planta activa.
# Valores orientativos por textura:
#   arenoso:        0.30 - 0.45   (drena rápido, retiene poco)
#   franco:         0.10 - 0.20
#   franco-arcill.: 0.02 - 0.08
#   arcilloso:      0.00 - 0.02   (drena lento, retiene casi todo)
FRACCION_DRENAJE = 0.10

# ---------- Politica de cantidad de riego ----------
# Cuando se decide regar (turno o respaldo), la cantidad objetivo es la
# necesaria para llevar la humedad del suelo (H_pct, % de agua util
# disponible) desde su valor actual hasta H_OBJETIVO_PCT, descontando la
# lluvia del dia.
# Internamente: Dr_objetivo = ADT * (1 - H_OBJETIVO_PCT/100)
# demanda_mm = max(0, Dr - Dr_objetivo - Pr)
#   100 -> rellenar hasta capacidad de campo (CC). Maximo riego.
#    50 -> regar hasta el punto medio entre PMP y CC.
#     0 -> no regar (siempre alcanza el objetivo).
# El sobrante del canal recarga el estanque hasta su capacidad; lo que no
# cabe se cuenta como Perdida_m3 (desperdicio).
H_OBJETIVO_PCT = 20.0

# ---------- Humedad mínima de seguridad ----------
# Si la humedad baja de este valor, se fuerza riego hasta al menos este umbral
HUMEDAD_MINIMA_PCT = 100.0 * PMP + 2.0   # por defecto 2% sobre PMP

# ---------- Riego de emergencia desde estanque ----------
# Si H_pct cae a este umbral o menos (fuera de turno), se aplica desde el
# estanque una cuota diaria = (agua para llegar a HUMEDAD_OBJETIVO_EMERGENCIA_PCT)
# dividida entre los días que faltan para el próximo turno.
# Esto suaviza el efecto de esperar entre turnos cuando el suelo está muy seco.
HUMEDAD_EMERGENCIA_PCT   = 14.0   # H_pct que activa el riego de emergencia
HUMEDAD_OBJETIVO_EMERGENCIA_PCT = 50.0  # H_pct objetivo a alcanzar en el reparto

# ---------- Política de riego: objetivo = CC ----------
# Si esta opción está en True, el riego siempre apunta a llenar hasta CC
RIEGO_HASTA_CC = True

# ---------- Particiones de terreno (modo greedy) ----------
# Si PARTICIONES > 1, el terreno del regante se divide en N partes iguales.
# Se elige el mejor cultivo para cada partición de forma secuencial (greedy):
#   1) Se simulan todos los cultivos disponibles con los recursos actuales.
#   2) Se selecciona el cultivo con mayor Margen_real_clp (o Primera_% si
#      no hay datos de productividad).
#   3) Los recursos consumidos (estanque, subterránea) se descuentan antes
#      de evaluar la siguiente partición.
# PARTICIONES = 1 mantiene el comportamiento original (todos los cultivos
# se simulan de forma independiente sobre la superficie total).
PARTICIONES = 4

# Presupuesto total disponible para costear los cultivos de todas las
# particiones (pesos CLP). Se distribuye en orden: si la partición 1 cuesta
# X, a la partición 2 solo le quedan (PRESUPUESTO - X).
# Los cultivos cuyo costo supere el presupuesto restante quedan excluidos de
# la selección para esa partición.
# None o 0 → sin restricción de presupuesto.
PRESUPUESTO = 4000000
