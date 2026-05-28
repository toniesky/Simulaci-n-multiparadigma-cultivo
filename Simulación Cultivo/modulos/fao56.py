"""Coeficientes FAO-56: cálculo de Kcb diario y Kcmax."""


def calcular_kcb(dia, L_ini, L_des, L_med, Kcb_ini, Kcb_med, Kcb_fin, L_fin):
    """Kcb diario (interpolación lineal por fase FAO-56)."""
    if dia < L_ini:
        return Kcb_ini
    if dia < L_ini + L_des:
        return Kcb_ini + (dia - L_ini) / L_des * (Kcb_med - Kcb_ini)
    if dia < L_ini + L_des + L_med:
        return Kcb_med
    return Kcb_med + (dia - (L_ini + L_des + L_med)) / L_fin * (Kcb_fin - Kcb_med)

def calcular_kcmax(kcb, h, hr_min, u2):
    """Kcmax FAO-56 ec. 72."""
    primer = 1.2 + (0.04 * (u2 - 2) - 0.004 * (hr_min - 45)) * ((h / 3) ** 0.3)
    return max(primer, kcb + 0.05)
