"""
Módulo de valores iniciales para el modelo de dinámica de sistemas
de gestión de agua - Caudal Regante

PARÁMETROS CONFIGURABLES - Edita aquí para cambiar el comportamiento del modelo
"""

# ============================== ACCIONES DE AGUA ==============================

# Número de acciones que tiene el regante
# Cada acción otorga derecho a usar agua
NUMERO_ACCIONES = 4 # acciones (parámetro configurable)

# Volumen de agua por acción (m³/día)
# Cantidad máxima que se puede usar por cada acción
# 1 acción = 1 L/s × 12 horas (turno) × 3600 seg/hora = 43,200 L = 43.2 m³
VALOR_ACCION = 43.2  # m³/turno por acción

# Agua máxima disponible sin desmarque
# = NUMERO_ACCIONES × VALOR_ACCION
AGUA_MAXIMA_REGANTE = NUMERO_ACCIONES * VALOR_ACCION  # m³/día

# Desmarque Inicial (antes de la fecha de cambio)
# Porcentaje de derechos superficiales que se pueden usar
PORCENTAJE_DESMARQUE_INICIAL = 0.15  # % de derechos

# Desmarque Final (desde la fecha de cambio en adelante)
# Porcentaje de derechos superficiales que se pueden usar
PORCENTAJE_DESMARQUE_FINAL = 0.15  # % de derechos

# Fecha de cambio de desmarque (mes-día, será aplicada cada año)
FECHA_DESMARQUE = "09-01"  # 1 de septiembre

# Salto entre escenarios de desmarque final
# Cada escenario suma/resta este valor al desmarque base
# Siempre se generan 5 escenarios: -2, -1, 0, +1, +2
# Ejemplo: salto=0.03 y base=0.15 → 9%, 12%, 15%, 18%, 21%
SALTO_DESMARQUE = 0.025  

# ============================== AGUA SUBTERRÁNEA (RECARGAS) ==============================

# Eventos de recarga de agua subterránea
# Cada tupla: ("MM-DD", volumen_m3_recargado)
#   - "MM-DD": fecha en que ocurre la recarga (formato mes-día, se aplica cada año)
#   - volumen_m3_recargado: cantidad que se recarga ESE día (no acumulativo)
# Cada recarga se suma a la oferta total SOLO en el día de la recarga
# EJEMPLO: 20 m³ el 1-enero y 30 m³ el 1-julio = 50 m³ recargados en el año
RECARGAS_AGUA_SUBTERRANEA = [
    ("01-01", 20.0),   # Recarga inicial: 20 m³ el 1 de enero
    ("07-01", 10.0),   
]

# ============================== PÉRDIDAS ==============================

# Pérdidas como variables aleatorias UNIFORMES: (mínimo, máximo)
# Cada día con flujo muestrea un valor distinto dentro del rango

# Pérdida por filtración (seepage en el suelo)
PERDIDA_FILTRACION = (0.03, 0.06)   # (3%, 6%)

# Pérdida por conducción (fricción / evaporación en el canal)
PERDIDA_CONDUCCION = (0.01, 0.04)   # (1%, 4%)

# ============================== MANTENIMIENTO ==============================

# Duración del mantenimiento (días que permanece cerrado el canal)
DURACION_MANTENIMIENTO = 7  # días

# CALENDARIO DE PARADAS (Días de inicio de cada período de mantenimiento)
# Especifica en qué días del año comienzan los períodos de mantenimiento
# Cada parada dura DURACION_MANTENIMIENTO días consecutivos
# EJEMPLO: [20, 150, 300] = 3 paradas: 
#   - Parada 1: días 20-33 (14 días)
#   - Parada 2: días 150-156 (7 días)
#   - Parada 3: días 300-306 (7 días)
CALENDARIO_PARADAS = [250]  # Días de inicio (configurable)    

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
FRECUENCIA_TURNO = 9  # días 

# Duración real del turno en días
DURACION_TURNO = 1  # días (el turno dura 1 día)

# ============================== TIEMPO DE SIMULACIÓN ==============================

# Período total de simulación (días)
TIEMPO_TOTAL = 365  # días (1 año)

# Paso de integración numérica (días)
PASO_SIMULACION = 1  # día

# Fecha de inicio de la simulación
FECHA_INICIO = "2024-01-01"  # Formato YYYY-MM-DD (configurable)

# NOTA: FECHA_DESMARQUE define cuándo cambia de desmarque inicial a desmarque final
# Formato: MM-DD (mes-día), se aplica cada año
#
# LÓGICA DE AGUA SUBTERRÁNEA:
# - Lista de recargas: RECARGAS_AGUA_SUBTERRANEA [("MM-DD", m³_recargados), ...]
# - Cada recarga se agrega a la oferta total SOLO el día de la recarga
# - No hay consumo diario ni stock continuo
