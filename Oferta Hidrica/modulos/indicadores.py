"""Indicadores avanzados de disponibilidad hídrica."""


def calcular_indicadores(resultados, iv):
    """
    Imprime indicadores avanzados sobre disponibilidad y consumo de agua.

    Args:
        resultados: DataFrame retornado por simulacion.simular
        iv: módulo initial_values cargado
    """
    df = resultados

    print(f"\n{'='*60}")
    print("INDICADORES AVANZADOS DE DISPONIBILIDAD")
    print(f"{'='*60}")

    # --- 1. Oferta superficial ---
    sin_sup = (df['OfertaSuperficial'] == 0).astype(int)
    periodos_sin_sup = _periodos_consecutivos(sin_sup)
    max_sin_sup = max(periodos_sin_sup) if periodos_sin_sup else 0
    suma_sup = df['OfertaSuperficial'].sum()

    print(f"\n1. OFERTA SUPERFICIAL:")
    print(f"   Días con agua superficial: {(df['OfertaSuperficial'] > 0).sum()}")
    print(f"   Días SIN agua superficial: {(df['OfertaSuperficial'] == 0).sum()}")
    print(f"   Tiempo máximo CONSECUTIVO sin agua superficial: {max_sin_sup} días")
    print(f"   Número de períodos sin agua superficial: {len(periodos_sin_sup)}")
    if periodos_sin_sup:
        print(f"   Promedio días por período sin agua: {sum(periodos_sin_sup)/len(periodos_sin_sup):.1f} días")
    print(f"   SUMA TOTAL de agua superficial disponible: {suma_sup:.2f} m³")

    # --- 2. Días sin ningún agua ---
    sin_agua = (
        (df['OfertaSuperficial'] == 0) & (df['RecargaSubterranea'] == 0)
    ).astype(int)
    dias_sin_agua = sin_agua.sum()
    periodos_sin_agua = _periodos_consecutivos(sin_agua)

    print(f"\n2. DISPONIBILIDAD TOTAL:")
    print(f"   Días SIN NINGÚN AGUA (ni superficial ni subterránea): {dias_sin_agua}")
    if periodos_sin_agua:
        print(f"   Tiempo máximo CONSECUTIVO sin agua: {max(periodos_sin_agua)} días")
        print(f"   Número de períodos sin agua: {len(periodos_sin_agua)}")

    # --- 3. Agua subterránea ---
    recargas = sorted(iv.RECARGAS_AGUA_SUBTERRANEA, key=lambda r: r[0])
    total_recargado = sum(c for _, c in recargas)

    print(f"\n3. AGUA SUBTERRÁNEA (RECARGAS):")
    for i, (fecha_mm_dd, cantidad) in enumerate(recargas):
        print(f"   Recarga {i+1} ({fecha_mm_dd}): +{cantidad:.0f} m³")
    print(f"   TOTAL recargado en el año: {total_recargado:.2f} m³")

    print(f"   {'='*60}\n")


# ---- helpers privados -------------------------------------------------------

def _periodos_consecutivos(serie_binaria):
    """Retorna lista con la longitud de cada bloque de 1s consecutivos."""
    periodos = []
    actual = 0
    for val in serie_binaria:
        if val == 1:
            actual += 1
        else:
            if actual > 0:
                periodos.append(actual)
            actual = 0
    if actual > 0:
        periodos.append(actual)
    return periodos
