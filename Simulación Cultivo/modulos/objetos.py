"""
Constantes estructurales internas del simulador.
NO son parámetros de usuario (esos están en parametros.py).
Son listas, paletas, etiquetas y valores fijos que el código necesita
para funcionar, pero que el usuario no modifica.
"""

# Nombres de meses completos en español — usados en cálculo de mes de cosecha
MESES_ES = [
    'enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio',
    'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre',
]

# Nombres de meses abreviados — usados en Gantt y reportes
MESES = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun',
         'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']

# Paleta de colores por cultivo (Gantt y leyendas HTML)
PALETTE_CULTIVOS = [
    '#2563a8', '#43a047', '#e53935', '#fb8c00', '#8e24aa',
    '#00897b', '#f4511e', '#6d4c41', '#546e7a', '#c0ca33',
]

# Filas visibles por defecto en la tabla de ranking de combinaciones
FILAS_RANKING_VISIBLES = 20

# Etapas fenológicas FAO-56: opacidad visual, etiqueta y clave de duración
ETAPAS_OPACIDAD = [0.45, 0.65, 1.0, 0.75]
ETAPAS_LABELS   = ['Ini', 'Des', 'Med', 'Fin']
ETAPAS_KEYS     = ['L_ini', 'L_des', 'L_med', 'L_fin']
