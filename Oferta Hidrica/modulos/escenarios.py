"""Generación de escenarios de desmarque con tolerancia configurable."""


def generar_escenarios(iv):
    """
    Genera 5 escenarios fijos (-2, -1, 0, +1, +2) variando el desmarque
    final en pasos de SALTO_DESMARQUE alrededor de PORCENTAJE_DESMARQUE_FINAL.

    Ejemplo: PORCENTAJE_DESMARQUE_FINAL=0.15, SALTO_DESMARQUE=0.03
        → [(-2, 0.09), (-1, 0.12), (0, 0.15), (1, 0.18), (2, 0.21)]

    Args:
        iv: módulo initial_values cargado

    Returns:
        Lista de tuplas (numero_escenario, desmarque_2_value)
    """
    base  = iv.PORCENTAJE_DESMARQUE_FINAL
    salto = iv.SALTO_DESMARQUE

    escenarios = [(0, base)]
    for i in range(1, 3):
        escenarios.append(( i, max(0.0, base + i * salto)))  # por arriba
    for i in range(1, 3):
        escenarios.append((-i, max(0.0, base - i * salto)))  # por abajo

    return escenarios
