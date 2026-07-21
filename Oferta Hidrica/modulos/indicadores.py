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
    suma_neta  = df['OfertaSuperficial'].sum()
    suma_bruta = df['OfertaBruta'].sum() if 'OfertaBruta' in df.columns else suma_neta
    dias_turno = int((df['OfertaBruta'] > 0).sum()) if 'OfertaBruta' in df.columns else 0

    print(f"\n1. OFERTA SUPERFICIAL:")
    print(f"   Días con agua superficial : {(df['OfertaSuperficial'] > 0).sum()}")
    print(f"   Días SIN agua superficial : {(df['OfertaSuperficial'] == 0).sum()}")
    print(f"   Máx. días CONSECUTIVOS sin agua: {max_sin_sup} días")
    print(f"   Oferta bruta total (m³)   : {suma_bruta:.2f}")
    print(f"   Oferta neta total (m³)    : {suma_neta:.2f}")

    # --- 2. Pérdida determinística por posición ---
    suma_perdida = suma_bruta - suma_neta
    pct_perdida  = (suma_perdida / suma_bruta * 100) if suma_bruta > 0 else 0
    perd_por_turno = (suma_perdida / dias_turno) if dias_turno > 0 else 0

    print(f"\n2. PÉRDIDA POR POSICIÓN GEOGRÁFICA (cap caudal máximo):")
    caudal_max = getattr(iv, 'CAUDAL_MAXIMO_LS', None)
    if caudal_max is not None:
        print(f"   Caudal máximo en predio   : {caudal_max:.2f} L/s")
    print(f"   Pérdida acumulada (m³)    : {suma_perdida:.2f}")
    print(f"   Pérdida (% sobre bruto)   : {pct_perdida:.1f}%")
    print(f"   Pérdida promedio/turno    : {perd_por_turno:.2f} m³/turno")
    print(f"   Número de turnos con canal: {dias_turno}")

    # --- 3. Días sin ningún agua ---
    sin_agua = (
        (df['OfertaSuperficial'] == 0) & (df['RecargaSubterranea'] == 0)
    ).astype(int)
    dias_sin_agua = sin_agua.sum()
    periodos_sin_agua = _periodos_consecutivos(sin_agua)

    print(f"\n3. DISPONIBILIDAD TOTAL:")
    print(f"   Días SIN NINGÚN AGUA : {dias_sin_agua}")
    if periodos_sin_agua:
        print(f"   Máx. CONSECUTIVOS sin agua: {max(periodos_sin_agua)} días")

    # --- 4. Agua subterránea ---
    recargas = sorted(iv.RECARGAS_AGUA_SUBTERRANEA, key=lambda r: r[0])
    total_recargado = sum(c for _, c in recargas)

    print(f"\n4. AGUA SUBTERRÁNEA (RECARGAS):")
    for i, (fecha_mm_dd, cantidad) in enumerate(recargas):
        print(f"   Recarga {i+1} ({fecha_mm_dd}): +{cantidad:.0f} m³")
    print(f"   TOTAL recargado: {total_recargado:.2f} m³")

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
