"""Soporte para el reporte interactivo.

Contiene `simular_combo_detalle`, que re-simula UNA combinación arbitraria de
cultivos (la elegida por el usuario en la pestaña "Explorar combinación") y
devuelve los mismos KPIs y gráficos que se generan para la combinación ganadora
en `simulacion_cultivo.py`. NO modifica ningún cálculo: reutiliza exactamente las
mismas funciones del pipeline (`simular_multi_particion`, `_kpis_de_df_sim`,
`_graficos_b64`, etc.).
"""
import pandas as pd
import parametros as P
from .funciones import (
    cargar_oferta_superficial_m3,
    simular_multi_particion,
    _kpis_de_df_sim,
    _graficos_b64,
    _grafico_canal_b64,
    _grafico_agua_cultivos_b64,
    _grafico_estanque_b64,
    _grafico_sub_b64,
)
from .objetos import PALETTE_CULTIVOS

# KPIs en cero para particiones "no_plantar" (idéntico a simulacion_cultivo.py)
_KPIS_NP = {k: 0.0 for k in [
    'Margen_real_clp', 'Ingreso_ideal_clp', 'Ingreso_real_clp', 'Costo_clp',
    'Produccion_real', 'Aplicado_m3', 'Deficit_m3', 'OfertaCanal_m3',
    'Subterranea_m3', 'Estanque_medio_m3', 'Canal_Riego_m3',
    'Canal_Estanque_m3', 'Perdida_m3', 'OfertaCanal_total_m3',
    'Primera_%', 'Segunda_%', 'Perdida_%', 'Cobertura_%',
]}


def simular_combo_detalle(contexto, esc, cultivos_nombres):
    """Re-simula una combinación específica y devuelve KPIs + gráficos por partición.

    Parámetros
    ----------
    contexto : dict
        Contexto guardado por `simulacion_cultivo.main()` en el cache pickle.
    esc : int
        Escenario (-2, -1, 0, +1, +2).
    cultivos_nombres : list[str]
        Nombre del cultivo por partición (o 'no_plantar'), longitud = particiones.

    Devuelve
    --------
    dict con:
        'esc', 'cultivos', 'pasos' (lista por partición con kpis+graficos),
        'graficos_compartidos' (canal/cultivos/estanque/sub/crop_colors),
        'estanque_ini', 'estanque_fin', 'sub_ini', 'sub_fin',
        'presupuesto_total', 'excede_presupuesto', 'costo_total'.
    """
    base          = contexto['base']
    regante       = contexto['regante']
    df_clima_sim  = contexto['df_clima_sim']
    dia_siembra   = int(contexto['dia_siembra'])
    ha_part       = float(contexto['ha_part'])
    frac_cult     = float(contexto['frac_cult'])
    df_prod       = contexto['df_prod']
    cult_by_name  = contexto['cult_by_name']
    particiones   = int(contexto['particiones'])
    presupuesto_total = contexto['presupuesto_total']

    est_ini = float(regante['nivel_estanque_inicial_m3'])
    sub_ini = float(P.STOCK_SUBTERRANEO_INICIAL_M3)

    # Normalizar lista de cultivos a la longitud de particiones
    cultivos_nombres = [str(n).strip().lower() for n in cultivos_nombres]
    if len(cultivos_nombres) < particiones:
        cultivos_nombres = cultivos_nombres + ['no_plantar'] * (
            particiones - len(cultivos_nombres))
    cultivos_nombres = cultivos_nombres[:particiones]

    crops = [cult_by_name[n] for n in cultivos_nombres]
    crops_reales = [c for c in crops
                    if str(c['nombre']).strip().lower() != 'no_plantar']

    # ── Caso: todas las particiones sin plantar ──────────────────────────
    if not crops_reales:
        pasos = []
        for p, c in enumerate(crops):
            pasos.append({
                'particion': p + 1, 'cultivo': 'no_plantar',
                'kpis': _KPIS_NP.copy(), 'graficos': None,
                'etapas': {'L_ini': 0, 'L_des': 0, 'L_med': 0, 'L_fin': 0},
                'presupuesto_costo': 0.0,
            })
        return {
            'esc': esc, 'cultivos': cultivos_nombres, 'pasos': pasos,
            'graficos_compartidos': {
                'grafico_canal': None, 'grafico_cultivos': None,
                'grafico_estanque': None, 'grafico_sub': None, 'crop_colors': {},
            },
            'estanque_ini': est_ini, 'estanque_fin': est_ini,
            'sub_ini': sub_ini, 'sub_fin': sub_ini,
            'presupuesto_total': presupuesto_total,
            'excede_presupuesto': False, 'costo_total': 0.0,
            'dia_siembra': dia_siembra,
        }

    # ── Simulación de la combinación ─────────────────────────────────────
    d_max = max(int(c['L_ini'] + c['L_des'] + c['L_med'] + c['L_fin'])
                for c in crops_reales)
    oferta, en_par, recarga_sub = cargar_oferta_superficial_m3(
        base, d_max, dia_siembra, esc)
    dfs_fin, est_fin, sub_fin = simular_multi_particion(
        crops_reales, ha_part, regante, df_clima_sim, oferta, en_par,
        recarga_sub_diaria=recarga_sub)

    # ── KPIs y gráficos por partición ────────────────────────────────────
    pasos       = []
    costo_total = 0.0
    df_idx      = 0
    for p, c in enumerate(crops):
        cultivo_p = str(c['nombre']).strip().lower()
        if cultivo_p == 'no_plantar':
            kpis_p     = _KPIS_NP.copy()
            graficos_p = None
            costo_p    = 0.0
            etapas_p   = {'L_ini': 0, 'L_des': 0, 'L_med': 0, 'L_fin': 0}
        else:
            df_s       = dfs_fin[df_idx]; df_idx += 1
            kpis_p     = _kpis_de_df_sim(df_s, c, ha_part, frac_cult,
                                         dia_siembra, df_prod)
            graficos_p = _graficos_b64(df_s, esc, 0)
            costo_p    = float(kpis_p.get('Costo_clp', 0) or 0)
            etapas_p   = {
                'L_ini': int(c['L_ini']), 'L_des': int(c['L_des']),
                'L_med': int(c['L_med']), 'L_fin': int(c['L_fin']),
            }
        costo_total += costo_p
        pasos.append({
            'particion': p + 1, 'cultivo': cultivo_p,
            'kpis': kpis_p, 'graficos': graficos_p,
            'etapas': etapas_p, 'presupuesto_costo': costo_p,
        })

    # ── Gráficos compartidos (una vez por combinación) ───────────────────
    crop_color_map = {}
    for _c in crops_reales:
        _nm = str(_c['nombre']).strip().lower()
        if _nm not in crop_color_map:
            crop_color_map[_nm] = PALETTE_CULTIVOS[
                len(crop_color_map) % len(PALETTE_CULTIVOS)]
    nombres_real = [str(c['nombre']).strip().lower() for c in crops_reales]
    colores_real = [crop_color_map[n] for n in nombres_real]

    g_canal = _grafico_canal_b64(dfs_fin[0], esc) if dfs_fin else None
    g_cultivos = (_grafico_agua_cultivos_b64(dfs_fin, nombres_real, colores_real, esc)
                  if dfs_fin else None)
    cap_est = float(regante.get('capacidad_estanque_m3', 0) or 0)
    g_estanque = (_grafico_estanque_b64(dfs_fin[0], esc, cap_est)
                  if dfs_fin and cap_est > 0 else None)
    tiene_sub = (int(regante.get('tiene_derechos_subterranea', 0) or 0) == 1
                 or float(regante.get('STOCK_SUBTERRANEO_INICIAL_M3',
                          getattr(P, 'STOCK_SUBTERRANEO_INICIAL_M3', 0)) or 0) > 0)
    g_sub = (_grafico_sub_b64(dfs_fin[0], esc) if dfs_fin and tiene_sub else None)

    excede = (presupuesto_total is not None
              and costo_total > presupuesto_total + 0.01)

    return {
        'esc': esc, 'cultivos': cultivos_nombres, 'pasos': pasos,
        'graficos_compartidos': {
            'grafico_canal': g_canal, 'grafico_cultivos': g_cultivos,
            'grafico_estanque': g_estanque, 'grafico_sub': g_sub,
            'crop_colors': crop_color_map,
        },
        'estanque_ini': est_ini, 'estanque_fin': est_fin,
        'sub_ini': sub_ini, 'sub_fin': sub_fin,
        'presupuesto_total': presupuesto_total,
        'excede_presupuesto': excede, 'costo_total': costo_total,
        'dia_siembra': dia_siembra,
    }
