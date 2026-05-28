"""Evaluación de mes de cosecha y calidad de producción (modelo determinístico FAO-56)."""
import math as _math
from datetime import datetime, timedelta
import parametros as P
from .objetos import MESES_ES


def _mes_cosecha(dia_siembra, dias_totales):
    """Devuelve (numero_mes 1-12, nombre_mes) del dia de cosecha, calculado
    a partir del DIA_INICIO_SIMULACION + DIA_SIEMBRA + ciclo. El DOY se
    interpreta sobre un anho calendario estandar (365 dias, no bisiesto)."""
    inicio_doy = P.DIA_INICIO_SIMULACION + (dia_siembra - 1)
    cosecha_doy = inicio_doy + dias_totales - 1
    # Modular al anho calendario [1, 365]
    cosecha_doy = ((cosecha_doy - 1) % 365) + 1
    fecha = datetime(2025, 1, 1) + timedelta(days=cosecha_doy - 1)
    return fecha.month, MESES_ES[fecha.month - 1]

def _calcular_calidad(deficit_m3, aplicado_m3, dias_estres, dias_totales,
                      cobertura_pct, h_min_pct, h_med_pct, nombre_cultivo):
    """Calcula distribucion de calidad segun procedimiento determinístico FAO-56.
    Retorna dict con Primera_pct, Segunda_pct, Perdida_pct (cada uno 0-100).

    S1: fraccion del agua demandada que no fue cubierta (eficiencia hidrica).
    S2: deficit promedio de humedad relativo al umbral de estrés (70% H_pct).
        Metrica continua (0 cuando h_med >= 70%, hasta 1 cuando h_med = 0%).
        Mas robusta que contar dias discretos bajo umbral AFA, porque los
        riegos de emergencia producen muchos dias bajo el umbral aunque el
        cultivo se recupere (conteo binario infla artificialmente el estres).
    """
    # --- S1: fracción de agua no cubierta ---
    total_agua = deficit_m3 + aplicado_m3
    S1 = deficit_m3 / total_agua if total_agua > 0 else 0.0

    # --- S2: déficit continuo de humedad media respecto al umbral de estrés ---
    S2 = max(0.0, min(1.0, 1.0 - h_med_pct / 70.0))

    S_eff = 0.6 * S1 + 0.4 * S2
    S_eff_corr = S_eff ** 1.3 if S_eff > 0.0 else 0.0

    # Condición óptima de cultivo
    condicion_optima = (
        cobertura_pct >= 95.0 and
        h_med_pct     >= 70.0 and
        S_eff         <= 0.60
    )

    # Penalización por humedad mínima muy baja
    h_ref = h_med_pct
    if h_ref <= 5.0:
        p_perdida_extra = 0.10
    elif h_ref <= 10.0:
        p_perdida_extra = 0.05
    else:
        p_perdida_extra = 0.0

    # Ky según tipo de cultivo
    cultivos_fruto = {'tomate', 'choclo', 'brocoli', 'repollo'}
    Ky = 1.1 if nombre_cultivo.lower() in cultivos_fruto else 1.0
    R = max(0.0, 1.0 - Ky * S_eff_corr)  # noqa

    # Proporciones base (k=3, θ=0.6; techo 0.4 en pérdida)
    primera_base = _math.exp(-1.5 * S_eff_corr)
    perdida_base = min(0.4, 1.0 / (1.0 + _math.exp(-3.0 * (S_eff_corr - 0.6))))
    segunda_base = max(0.0, 1.0 - primera_base - perdida_base)

    # --- Distribución según condición ---
    if condicion_optima:
        perdida = perdida_base * 0.3
        segunda = segunda_base + 0.3 * perdida_base
        primera = 1.0 - (segunda + perdida)
    else:
        # Sin doble compresión: las proporciones base ya suman 1.
        # La pérdida se ajusta solo con p_perdida_extra y cobertura.
        perdida = min(1.0, perdida_base + p_perdida_extra)
        primera = primera_base
        segunda = segunda_base

        # Penalización por cobertura baja (solo si < 90%)
        if cobertura_pct < 90.0:
            cob_frac = (90.0 - cobertura_pct) / 90.0
            primera = max(0.0, primera - cob_frac * 0.25)
            segunda = max(0.0, segunda - cob_frac * 0.10)
            perdida = 1.0 - primera - segunda

        # Piso mínimo de Primera cuando cobertura > 90%
        if cobertura_pct > 90.0 and primera < 0.30:
            delta   = 0.30 - primera
            primera = 0.30
            if perdida >= delta:
                perdida -= delta
            else:
                segunda = max(0.0, segunda - (delta - perdida))
                perdida = 0.0

    # --- Caps de pérdida según H_med (escalonado) ---
    if h_med_pct >= 80.0 and perdida > 0.15:
        exceso  = perdida - 0.15
        perdida = 0.15
        segunda += exceso * 0.6; primera += exceso * 0.4
    elif h_med_pct >= 70.0 and perdida > 0.25:
        exceso  = perdida - 0.25
        perdida = 0.25
        segunda += exceso * 0.6; primera += exceso * 0.4
    elif h_med_pct >= 50.0 and perdida > 0.40:
        exceso  = perdida - 0.40
        perdida = 0.40
        segunda += exceso * 0.6; primera += exceso * 0.4
    elif h_med_pct >= 35.0 and perdida > 0.55:
        exceso  = perdida - 0.55
        perdida = 0.55
        segunda += exceso * 0.6; primera += exceso * 0.4

    # --- Reforzar Primera cuando H_med es alta ---
    if h_med_pct >= 75.0:
        boost   = min(0.15, segunda)
        primera += boost; segunda -= boost

    # --- Rebalance final ---
    if primera > 0.85:
        exceso  = primera - 0.85
        primera = 0.85
        segunda += exceso
    perdida = max(perdida, 0.02)

    # Normalización final
    total = primera + segunda + perdida
    if total > 0.0:
        primera /= total; segunda /= total; perdida /= total

    return {
        'Primera_%': round(primera * 100, 1),
        'Segunda_%': round(segunda * 100, 1),
        'Perdida_%': round(perdida * 100, 1),
    }
