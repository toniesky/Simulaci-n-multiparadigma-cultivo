"""Indicadores de desempeño: KPIs hídricos, económicos y por combinación de cultivos."""
import pandas as pd
import parametros as P
from .simulacion import simular_cultivo
from .carga_datos import cargar_oferta_superficial_m3
from .calidad import _mes_cosecha, _calcular_calidad


def _kpis_economicos(cultivo, dia_siembra, dias_totales, hectareas,
                     fraccion_cult, df_prod):
    """Calcula ingreso (segun mes de cosecha), costo, margen y produccion
    para el cultivo. Devuelve dict; si no hay datos, todos los valores son
    None y 'mes_cosecha' igualmente queda calculado."""
    _, mes_nombre = _mes_cosecha(dia_siembra, dias_totales)
    ha_efectivas = hectareas * fraccion_cult
    base_kpis = {
        'Mes_cosecha':       mes_nombre,
        'Ha_efectivas':      round(ha_efectivas, 3),
        'Ingreso_ideal_clp':  None,
        'Costo_clp':         None,
        'Margen_ideal_clp':  None,
        'Produccion':        None,
        'Unidad':            None,
        'Rendimiento_ha':    None,
        'Precio_ha_mes_clp': None,
    }
    if df_prod is None or cultivo not in df_prod.index:
        return base_kpis
    fila = df_prod.loc[cultivo]
    precio_ha = float(fila[mes_nombre])
    costo_ha  = float(fila['costo'])
    rend_ha   = float(fila['rendimiento'])
    unidad    = str(fila['unidad'])
    ingreso   = precio_ha * ha_efectivas
    costo     = costo_ha  * ha_efectivas
    produccion = rend_ha  * ha_efectivas
    base_kpis.update({
        'Ingreso_ideal_clp':  round(ingreso, 0),
        'Costo_clp':         round(costo, 0),
        'Margen_ideal_clp':  round(ingreso - costo, 0),
        'Produccion':        round(produccion, 1),
        'Unidad':            unidad,
        'Rendimiento_ha':    round(rend_ha, 1),
        'Precio_ha_mes_clp': round(precio_ha, 0),
    })
    return base_kpis

def _simular_combinacion(base, regante, c, df_clima_full, escenario, df_prod=None,
                         estanque_ini=None, stock_sub_ini=None):
    """Ejecuta la simulacion para un (cultivo c, escenario) usando el regante
    fijo. Devuelve (df_sim, info) con metadatos y KPIs ya calculados.
    estanque_ini/stock_sub_ini: recursos iniciales; si None usa los defaults."""
    cultivo       = str(c['nombre']).strip().lower()
    dia_siembra   = int(P.DIA_SIEMBRA)
    hectareas     = float(regante['hectareas'])
    fraccion_cult = float(regante.get('fraccion_cultivada', 1.0))
    dias_totales  = int(c['L_ini'] + c['L_des'] + c['L_med'] + c['L_fin'])

    df_clima = df_clima_full.iloc[(P.DIA_INICIO_SIMULACION - 1) + (dia_siembra - 1):].reset_index(drop=True)
    oferta_canal_m3, en_parada = cargar_oferta_superficial_m3(
        base, dias_totales, dia_siembra, escenario)
    df_sim, ADT, AFA = simular_cultivo(c, df_clima, oferta_canal_m3, regante, en_parada,
                                        estanque_ini=estanque_ini, stock_sub_ini=stock_sub_ini)

    etc_total   = df_sim['Etc_m3_total'].sum()
    oferta_can  = df_sim['OfertaCanal_m3'].sum()
    canal_riego = df_sim['Canal_Riego_m3'].sum()
    canal_est   = df_sim['Canal_Estanque_m3'].sum()
    aplicado    = df_sim['Aplicado_m3'].sum()
    sub_usada   = df_sim['Subterranea_Usada_m3'].sum()
    perdida     = df_sim['Perdida_m3'].sum()
    deficit     = df_sim['Deficit_m3'].sum()
    # AFA en escala H_pct: H = (1-Dr/ADT)*100, AFA <-> Dr=p*ADT => H_AFA=(1-p)*100
    h_afa_pct  = (1.0 - float(c['p'])) * 100.0
    dias_estres = int((df_sim['H_pct'] < h_afa_pct).sum())

    info = {
        'cultivo':     cultivo,
        'dia_siembra': dia_siembra,
        'hectareas':   hectareas,
        'frec':        int(regante['frecuencia_dias']),
        'cap':         float(regante['capacidad_estanque_m3']),
        'niv_ini':     float(regante['nivel_estanque_inicial_m3']),
        'ADT':         ADT,
        'AFA':         AFA,
        'h_afa_pct':   h_afa_pct,
        'dias_totales': dias_totales,
        'c':           c,
        'kpis': {
            'Etc_m3':              round(etc_total, 1),
            'OfertaCanal_m3':      round(oferta_can, 1),
            'Canal_Riego_m3':      round(canal_riego, 1),
            'Canal_Estanque_m3':   round(canal_est, 1),
            'OfertaCanal_total_m3': round(canal_riego + canal_est + perdida, 1),
            'Aplicado_m3':         round(aplicado, 1),
            'Subterranea_m3':    round(sub_usada, 1),
            'Stock_sub_final':   round(df_sim['Stock_Subterraneo_m3'].iloc[-1], 1),
            'Perdida_m3':        round(perdida, 1),
            'Deficit_m3':        round(deficit, 1),
            'Estanque_final':    round(df_sim['Estanque_m3'].iloc[-1], 1),
            'Estanque_medio_m3': round(df_sim['Estanque_m3'].mean(), 1),
            'Turnos':            int(df_sim['Turno'].sum()),
            'Dias_estres':       dias_estres,
            'Cobertura_%':       round(aplicado / etc_total * 100 if etc_total > 0 else 0.0, 1),
            'Eficiencia_canal_%': round((1 - perdida / oferta_can) * 100 if oferta_can > 0 else 0.0, 1),
            'Autosuf_sup_%':     round((oferta_can - perdida) / etc_total * 100 if etc_total > 0 else 0.0, 1),
            'Depend_sub_%':      round(sub_usada / aplicado * 100 if aplicado > 0 else 0.0, 1),
            'H_min_%':           round(df_sim['H_pct'].min(), 1),
            'H_med_%':           round(df_sim['H_pct'].mean(), 1),
            'H_max_%':           round(df_sim['H_pct'].max(), 1),
            'H_final_%':         round(df_sim['H_pct'].iloc[-1], 1),
            'Theta_vol_min_%':   round(df_sim['Theta_vol_pct'].min(), 2),
            'Theta_vol_med_%':   round(df_sim['Theta_vol_pct'].mean(), 2),
        },
    }
    # KPIs economicos (ingreso segun mes de cosecha, costo, margen, produccion)
    info['kpis'].update(_kpis_economicos(
        cultivo, dia_siembra, dias_totales, hectareas, fraccion_cult, df_prod))

    # Distribucion de calidad
    info['kpis'].update(_calcular_calidad(
        deficit_m3=info['kpis']['Deficit_m3'],
        aplicado_m3=info['kpis']['Aplicado_m3'],
        dias_estres=info['kpis']['Dias_estres'],
        dias_totales=dias_totales,
        cobertura_pct=info['kpis']['Cobertura_%'],
        h_min_pct=info['kpis']['H_min_%'],
        h_med_pct=info['kpis']['H_med_%'],
        nombre_cultivo=cultivo,
    ))

    # Ingreso real ajustado por calidad (PASO 2-5)
    # Factores de valorización: Primera=1.0, Segunda=0.6, Pérdida=0.0 (sin ingreso)
    _p1  = info['kpis']['Primera_%'] / 100.0
    _p2  = info['kpis']['Segunda_%'] / 100.0
    _pp  = info['kpis']['Perdida_%'] / 100.0
    _F   = _p1 * 1.0 + _p2 * 0.6 + _pp * 0.0
    _ing_ideal = info['kpis'].get('Ingreso_ideal_clp')
    _costo     = info['kpis'].get('Costo_clp')
    if _ing_ideal is not None:
        _ing_real  = round(_ing_ideal * _F, 0)
        _mar_real  = round(_ing_real - (_costo or 0.0), 0)
    else:
        _ing_real  = None
        _mar_real  = None
    info['kpis']['Ingreso_real_clp'] = _ing_real
    info['kpis']['Margen_real_clp']  = _mar_real

    # Producción real: descontando la fracción perdida
    _prod_ideal = info['kpis'].get('Produccion')
    if _prod_ideal is not None:
        info['kpis']['Produccion_real'] = round(_prod_ideal * (1.0 - _pp), 1)
    else:
        info['kpis']['Produccion_real'] = None

    return df_sim, info

def _kpis_de_df_sim(df_sim, c, ha_part, fraccion_cult, dia_siembra, df_prod):
    """Calcula todos los KPIs a partir de un df_sim ya generado por simular_multi_particion.
    Devuelve el mismo dict de kpis que _simular_combinacion."""
    cultivo      = str(c['nombre']).strip().lower()
    dias_totales = int(c['L_ini'] + c['L_des'] + c['L_med'] + c['L_fin'])
    h_afa_pct    = (1.0 - float(c['p'])) * 100.0

    etc_total   = df_sim['Etc_m3_total'].sum()
    oferta_can  = df_sim['OfertaCanal_m3'].sum()   # canal -> riego directo
    canal_est   = df_sim['Canal_Estanque_m3'].sum()  # canal -> estanque
    aplicado    = df_sim['Aplicado_m3'].sum()
    sub_usada   = df_sim['Subterranea_Usada_m3'].sum()
    perdida     = df_sim['Perdida_m3'].sum()
    deficit     = df_sim['Deficit_m3'].sum()
    dias_estres = int((df_sim['H_pct'] < h_afa_pct).sum())

    kpis = {
        'Etc_m3':              round(etc_total, 1),
        'OfertaCanal_m3':      round(oferta_can, 1),
        'Canal_Riego_m3':      round(oferta_can, 1),   # en multi, OfertaCanal = riego canal
        'Canal_Estanque_m3':   round(canal_est, 1),
        'OfertaCanal_total_m3': round(oferta_can + canal_est + perdida, 1),
        'Aplicado_m3':         round(aplicado, 1),
        'Subterranea_m3':     round(sub_usada, 1),
        'Stock_sub_final':    round(df_sim['Stock_Subterraneo_m3'].iloc[-1], 1),
        'Perdida_m3':         round(perdida, 1),
        'Deficit_m3':         round(deficit, 1),
        'Estanque_final':     round(df_sim['Estanque_m3'].iloc[-1], 1),
        'Estanque_medio_m3':  round(df_sim['Estanque_m3'].mean(), 1),
        'Turnos':             int(df_sim['Turno'].sum()),
        'Dias_estres':        dias_estres,
        'Cobertura_%':        round(aplicado / etc_total * 100 if etc_total > 0 else 0.0, 1),
        'Eficiencia_canal_%': round((1 - perdida / oferta_can) * 100 if oferta_can > 0 else 0.0, 1),
        'Autosuf_sup_%':      round((oferta_can - perdida) / etc_total * 100 if etc_total > 0 else 0.0, 1),
        'Depend_sub_%':       round(sub_usada / aplicado * 100 if aplicado > 0 else 0.0, 1),
        'H_min_%':            round(df_sim['H_pct'].min(), 1),
        'H_med_%':            round(df_sim['H_pct'].mean(), 1),
        'H_max_%':            round(df_sim['H_pct'].max(), 1),
        'H_final_%':          round(df_sim['H_pct'].iloc[-1], 1),
        'Theta_vol_min_%':    round(df_sim['Theta_vol_pct'].min(), 2),
        'Theta_vol_med_%':    round(df_sim['Theta_vol_pct'].mean(), 2),
    }
    kpis.update(_kpis_economicos(cultivo, dia_siembra, dias_totales, ha_part, fraccion_cult, df_prod))
    kpis.update(_calcular_calidad(
        deficit_m3=kpis['Deficit_m3'], aplicado_m3=kpis['Aplicado_m3'],
        dias_estres=kpis['Dias_estres'], dias_totales=dias_totales,
        cobertura_pct=kpis['Cobertura_%'], h_min_pct=kpis['H_min_%'],
        h_med_pct=kpis['H_med_%'], nombre_cultivo=cultivo))

    _p1 = kpis['Primera_%'] / 100.0
    _p2 = kpis['Segunda_%'] / 100.0
    _pp = kpis['Perdida_%'] / 100.0
    _F  = _p1 * 1.0 + _p2 * 0.6 + _pp * 0.0
    _ing_ideal = kpis.get('Ingreso_ideal_clp')
    _costo     = kpis.get('Costo_clp')
    if _ing_ideal is not None:
        kpis['Ingreso_real_clp'] = round(_ing_ideal * _F, 0)
        kpis['Margen_real_clp']  = round(kpis['Ingreso_real_clp'] - (_costo or 0.0), 0)
    else:
        kpis['Ingreso_real_clp'] = None
        kpis['Margen_real_clp']  = None
    _prod_ideal = kpis.get('Produccion')
    kpis['Produccion_real'] = round(_prod_ideal * (1.0 - _pp), 1) if _prod_ideal is not None else None
    return kpis
