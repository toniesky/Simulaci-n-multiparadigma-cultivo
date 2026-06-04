"""Simulación de cultivo — punto de entrada principal.

Importa todas las funciones desde modulos/funciones.py y ejecuta
el algoritmo greedy de selección de cultivos por partición.
"""
import os
import pandas as pd
import parametros as P
from modulos.funciones import (
    cargar_regante,
    cargar_productividad,
    listar_escenarios,
    cargar_oferta_superficial_m3,
    simular_multi_particion,
    _kpis_de_df_sim,
    _graficos_b64,
    _generar_html_particiones,
)

def main():
    base = os.path.dirname(os.path.abspath(__file__))
    df_cult  = pd.read_csv(os.path.join(base, P.ARCHIVO_CULTIVOS))
    df_clima_full = pd.read_csv(os.path.join(base, P.ARCHIVO_CLIMA))
    os.makedirs(os.path.join(base, P.DIR_SALIDA), exist_ok=True)
    df_cult['nombre'] = df_cult['nombre'].astype(str).str.strip().str.lower()

    # --- Filtrar cultivos por mes de inicio de simulacion ---
    import calendar
    _MESES = list(calendar.month_name)[1:]  # ['January', ..., 'December']
    _MESES_ES = ['enero','febrero','marzo','abril','mayo','junio',
                 'julio','agosto','septiembre','octubre','noviembre','diciembre']
    _dia_ini  = int(P.DIA_INICIO_SIMULACION)
    _dia_sie  = int(P.DIA_SIEMBRA)
    # dia efectivo de siembra en el anio de clima (1-365)
    _dia_efectivo = _dia_ini + _dia_sie - 1
    _mes_idx  = 0  # indice 0-based del mes
    _acum     = 0
    for _m in range(1, 13):
        _acum += calendar.monthrange(2001, _m)[1]  # anio no bisiesto (365 dias)
        if _dia_efectivo <= _acum:
            _mes_idx = _m - 1
            break
    _mes_col = _MESES_ES[_mes_idx]
    _cal_path = os.path.join(base, getattr(P, 'ARCHIVO_CALENDARIO_SIEMBRA',
                                           'inputs/calendario_siembra.csv'))
    if os.path.isfile(_cal_path):
        df_cal = pd.read_csv(_cal_path)
        df_cal['nombre'] = df_cal['nombre'].astype(str).str.strip().str.lower()
        if _mes_col in df_cal.columns:
            _disponibles = set(df_cal.loc[df_cal[_mes_col] == 1, 'nombre'])
            _excluidos   = [c for c in df_cult['nombre'] if c not in _disponibles]
            df_cult = df_cult[df_cult['nombre'].isin(_disponibles)].reset_index(drop=True)
            print(f'[INFO] Mes de inicio    : {_mes_col.capitalize()} '
                  f'(DIA_INICIO={_dia_ini} + DIA_SIEMBRA={_dia_sie} = dia {_dia_efectivo})')
            if _excluidos:
                print(f'[INFO] Cultivos excluidos este mes : {_excluidos}')
            else:
                print(f'[INFO] Todos los cultivos disponibles en {_mes_col}')
            if df_cult.empty:
                raise SystemExit(
                    f'[ERROR] Ninguna hortaliza disponible para el mes "{_mes_col}". '
                    'Revise inputs/calendario_siembra.csv o ajuste DIA_INICIO_SIMULACION.')
        else:
            print(f'[WARN] Columna "{_mes_col}" no encontrada en {_cal_path}; se usan todos los cultivos')
    else:
        print(f'[WARN] No se encontro {_cal_path}; se usan todos los cultivos')

    regante = cargar_regante(base)
    df_prod = cargar_productividad(base)
    escenarios = listar_escenarios(base)
    cultivos = df_cult['nombre'].tolist()
    print(f'[INFO] Regante   : #{int(regante["id"])} {regante.get("nombre", "")}')
    print(f'[INFO] Cultivos  : {cultivos}')
    print(f'[INFO] Escenarios: {escenarios}')

    # ---- Verificación de coeficientes de cultivo cargados ----
    # La simulación usa EXCLUSIVAMENTE las columnas Kcb_* (método dual FAO-56).
    # Las columnas Kc_* del CSV son informativas y NO afectan el cálculo de ETc.
    print()
    print('[INFO] Coeficientes Kcb cargados desde CSV (estos son los que usa la simulacion):')
    print(f'  {"Cultivo":<22} {"Kcb_ini":>8} {"Kcb_med":>8} {"Kcb_fin":>8}  {"Fases (ini/des/med/fin)"}')
    print(f'  {"-"*22} {"-"*8} {"-"*8} {"-"*8}  {"-"*28}')
    for _, row in df_cult.iterrows():
        nombre = str(row['nombre'])
        kcb_i  = float(row['Kcb_ini'])
        kcb_m  = float(row['Kcb_med'])
        kcb_f  = float(row['Kcb_fin'])
        fases  = f"{int(row['L_ini'])}/{int(row['L_des'])}/{int(row['L_med'])}/{int(row['L_fin'])} días"
        print(f'  {nombre:<22} {kcb_i:>8.3f} {kcb_m:>8.3f} {kcb_f:>8.3f}  {fases}')
        # Advertir SOLO si algún Kc_* es cercano a cero pero Kcb_* es alto,
        # lo que indica que el usuario intentó anular ETc modificando Kc_*
        # (que no usa la simulación). En FAO-56 dual, Kc y Kcb siempre difieren,
        # por lo que no se alerta por diferencias normales.
        for fase, kc_col, kcb_val in [('ini', 'Kc_ini', kcb_i),
                                       ('med', 'Kc_med', kcb_m),
                                       ('fin', 'Kc_fin', kcb_f)]:
            if kc_col in row.index:
                kc_val = float(row[kc_col])
                if kc_val < 0.05 and kcb_val > 0.1:
                    print(f'    [AVISO] {nombre}: Kc_{fase}={kc_val:.3f} (practicamente cero),'
                          f' pero Kcb_{fase}={kcb_val:.3f} es el valor real usado.'
                          f' Para reducir ETc en fase {fase}, modificar Kcb_{fase} en el CSV.')
    print()
    if df_prod is None:
        print('[WARN] No se encontro inputs/productividad_cultivos.csv: KPIs economicos = n/d')
    else:
        faltan = [c for c in cultivos if c not in df_prod.index]
        if faltan:
            print(f'[WARN] Sin datos productivos para: {faltan} (apareceran como n/d)')

    particiones = getattr(P, 'PARTICIONES', 1)

    # ── Reporte de selección de cultivos por particiones ─────────────────────
    if particiones >= 1:
        ha_original = float(regante['hectareas'])
        ha_part     = ha_original / particiones
        frac_cult   = float(regante.get('fraccion_cultivada', 1.0))

        print()
        print(f'[INFO] Modo particiones: {particiones} × {ha_part:.4f} ha/partición '
              f'({ha_part * frac_cult * 10_000:.0f} m² cultivados por partición)')
        print(f'[INFO] Modelo SIMULTÁNEO: todas las particiones comparten canal y estanque día a día.')
        print(f'[INFO] Greedy evalúa portafolio total en cada paso de selección.')
        print()

        pasos_greedy    = []
        resumen_filas_p = []
        detalle_filas_p = []
        dia_siembra     = int(P.DIA_SIEMBRA)
        df_clima_sim    = df_clima_full.iloc[
            (P.DIA_INICIO_SIMULACION - 1) + (dia_siembra - 1):
        ].reset_index(drop=True)

        _ppto_cfg = getattr(P, 'PRESUPUESTO', None)
        presupuesto_total = float(_ppto_cfg) if _ppto_cfg else None
        if presupuesto_total:
            print(f'[INFO] Presupuesto total: $ {presupuesto_total:,.0f} CLP'
                  f' (se distribuye entre las {particiones} particiones)')

        from itertools import combinations_with_replacement as _cwr
        import numpy as np

        cult_rows     = [row for _, row in df_cult.iterrows()]

        # Agregar "no plantar" como cultivo dummy con score=0 en cada particion
        # Esto permite combos mixtos como [Lechuga, No plantar, Acelga, No plantar]
        _no_plant_row = df_cult.iloc[0].copy() if not df_cult.empty else None
        if _no_plant_row is not None:
            for col in _no_plant_row.index:
                _no_plant_row[col] = 0
            _no_plant_row['nombre'] = 'no_plantar'
            cult_rows = cult_rows + [_no_plant_row]

        n_cultivos    = len(cult_rows)
        all_combos_idx = list(_cwr(range(n_cultivos), particiones))
        n_total       = len(all_combos_idx)
        print(f'[INFO] Modo combinatorio: {n_cultivos - 1} cultivos + "no plantar" x {particiones} particiones'
              f' -> {n_total} combinaciones a evaluar (incluye mezclas parciales sin plantar)')
        print()

        for esc in escenarios:
            mejor_score      = 0.0          # baseline: no plantar tiene score=0
            mejor_combo      = None          # None => no_plantar es la mejor opción
            combos_evaluadas = []

            print(f'  [ESC {esc:+d}] Evaluando {n_total} combinaciones...')
            for n_eval, combo_idx in enumerate(all_combos_idx, 1):
                crops_combo = [cult_rows[i] for i in combo_idx]

                # Si todas las particiones son no_plantar, score=0 sin simular
                if all(str(c['nombre']).strip().lower() == 'no_plantar' for c in crops_combo):
                    nombres = 'no_plantar x' + str(particiones)
                    print(f'    {n_eval:>4}/{n_total}  {nombres:<40}  score={0:>12,.0f}  costo=${0:>10,.0f}')
                    combos_evaluadas.append({
                        'combo_idx': combo_idx,
                        'cultivos': ['no_plantar'] * particiones,
                        'score': 0.0, 'costo_total': 0.0,
                        'excede_presupuesto': False, 'kpis_list': None,
                    })
                    continue

                # Filtrar solo particiones con cultivo real para simular
                crops_reales = [c for c in crops_combo if str(c['nombre']).strip().lower() != 'no_plantar']
                n_reales     = len(crops_reales)
                ha_part_real = (ha_original / particiones)  # cada particion mantiene su superficie

                d_max = max(int(c['L_ini'] + c['L_des'] + c['L_med'] + c['L_fin'])
                            for c in crops_reales)
                oferta, en_par, recarga_sub = cargar_oferta_superficial_m3(base, d_max, dia_siembra, esc)
                dfs_c, est_fin_c, sub_fin_c = simular_multi_particion(
                    crops_reales, ha_part_real, regante, df_clima_sim, oferta, en_par,
                    recarga_sub_diaria=recarga_sub)

                total_score = 0.0
                total_costo = 0.0
                kpis_list   = []
                df_idx = 0
                for i, c in enumerate(crops_combo):
                    if str(c['nombre']).strip().lower() == 'no_plantar':
                        kpis_list.append({k: 0.0 for k in [
                            'Margen_real_clp','Ingreso_real_clp','Costo_clp',
                            'Produccion_real','Aplicado_m3','Deficit_m3',
                        ]})
                    else:
                        df_t = dfs_c[df_idx]; df_idx += 1
                        kk = _kpis_de_df_sim(df_t, c, ha_part_real, frac_cult,
                                              dia_siembra, df_prod)
                        m = kk.get('Margen_real_clp')
                        if m is not None and not (isinstance(m, float) and pd.isna(m)):
                            total_score += float(m)
                        total_costo += float(kk.get('Costo_clp', 0) or 0)
                        kpis_list.append(kk)

                excede = (presupuesto_total is not None
                          and total_costo > presupuesto_total + 0.01)

                nombres = '+'.join(str(c['nombre']).strip() for c in crops_combo)
                ppto_tag = ' [EXCEDE ppto]' if excede else ''
                mejor_tag = ' <-- MEJOR' if (not excede and total_score > mejor_score) else ''
                print(f'    {n_eval:>4}/{n_total}  {nombres:<40}'
                      f'  score={total_score:>12,.0f}  costo=${total_costo:>10,.0f}'
                      f'{ppto_tag}{mejor_tag}')

                combos_evaluadas.append({
                    'combo_idx':          combo_idx,
                    'cultivos':           [str(c['nombre']).strip().lower() for c in crops_combo],
                    'score':              total_score,
                    'costo_total':        total_costo,
                    'excede_presupuesto': excede,
                    'kpis_list':          kpis_list,
                })

                if not excede and total_score > mejor_score:
                    mejor_score = total_score
                    mejor_combo = combos_evaluadas[-1]

            # Agregar "no plantar" como opción explícita en el ranking
            combos_evaluadas.append({
                'combo_idx':          None,
                'cultivos':           ['no_plantar'] * particiones,
                'score':              0.0,
                'costo_total':        0.0,
                'excede_presupuesto': False,
                'kpis_list':          None,
            })

            # Si ningún combo superó score=0, recomendar no plantar
            if mejor_combo is None:
                todos_exceden = all(c['excede_presupuesto']
                                    for c in combos_evaluadas
                                    if c['combo_idx'] is not None)
                motivo = ('todas las combinaciones superan el presupuesto'
                          if todos_exceden else 'ningún cultivo supera margen positivo')
                print(f'  [INFO] Esc {esc:>+2d}: {motivo}. Recomendación: NO PLANTAR.')

            combos_evaluadas.sort(key=lambda x: x['score'], reverse=True)

            cultivos_mejor = mejor_combo['cultivos'] if mejor_combo else ['no_plantar'] * particiones
            print(f'  [MEJOR] Esc {esc:>+2d}: '
                  + ' | '.join(f'P{i+1}={"No plantar" if c == "no_plantar" else c.title()}' for i, c in enumerate(cultivos_mejor))
                  + (f'  score={mejor_combo["score"]:,.0f}  costo=${mejor_combo["costo_total"]:,.0f}'
                     if mejor_combo else '  score=0  costo=$0'))

            est_ini = float(regante['nivel_estanque_inicial_m3'])
            sub_ini = float(P.STOCK_SUBTERRANEO_INICIAL_M3)

            if mejor_combo is None:
                # ── Caso no_plantar: no se simula, KPIs en cero ────────────────
                _kpis_np = {k: 0.0 for k in [
                    'Margen_real_clp', 'Ingreso_ideal_clp', 'Ingreso_real_clp', 'Costo_clp',
                    'Produccion_real', 'Aplicado_m3', 'Deficit_m3', 'OfertaCanal_m3',
                    'Subterranea_m3', 'Estanque_medio_m3', 'Canal_Riego_m3',
                    'Canal_Estanque_m3', 'Perdida_m3', 'OfertaCanal_total_m3',
                    'Primera_%', 'Segunda_%', 'Perdida_%', 'Cobertura_%',
                ]}
                for p in range(particiones):
                    pasos_greedy.append({
                        'esc': esc, 'particion': p + 1, 'cultivo': 'no_plantar',
                        'score': 0.0,
                        'estanque_ini': est_ini, 'estanque_fin': est_ini,
                        'sub_ini': sub_ini,      'sub_fin': sub_ini,
                        'kpis': _kpis_np.copy(),
                        'graficos': None,
                        'presupuesto_total':   presupuesto_total,
                        'presupuesto_antes':   presupuesto_total,
                        'presupuesto_costo':   0.0,
                        'presupuesto_despues': presupuesto_total,
                        'todas_combos': combos_evaluadas if p == 0 else None,
                        'dia_siembra': dia_siembra,
                        'etapas': {'L_ini': 0, 'L_des': 0, 'L_med': 0, 'L_fin': 0},
                    })
                    fila = {'Escenario': esc, 'Particion': p + 1, 'Cultivo': 'no_plantar'}
                    fila.update(_kpis_np)
                    resumen_filas_p.append(fila)
            else:
                # ── Simulación final de la mejor combinación (CSV detalle diario) ─
                crops_mejor = [cult_rows[i] for i in mejor_combo['combo_idx']]
                crops_mejor_reales = [c for c in crops_mejor
                                      if str(c['nombre']).strip().lower() != 'no_plantar']
                d_max_fin   = max(int(c['L_ini'] + c['L_des'] + c['L_med'] + c['L_fin'])
                                  for c in crops_mejor_reales) if crops_mejor_reales else 1
                oferta_fin, en_par_fin, recarga_sub_fin = cargar_oferta_superficial_m3(
                    base, d_max_fin, dia_siembra, esc)
                dfs_fin, est_fin, sub_fin = simular_multi_particion(
                    crops_mejor_reales, ha_part, regante, df_clima_sim, oferta_fin, en_par_fin,
                    recarga_sub_diaria=recarga_sub_fin)

                costos_acum = 0.0
                df_fin_idx  = 0   # índice sobre dfs_fin (solo cultivos reales)

                _kpis_np_fin = {k: 0.0 for k in [
                    'Margen_real_clp','Ingreso_ideal_clp','Ingreso_real_clp','Costo_clp',
                    'Produccion_real','Aplicado_m3','Deficit_m3','OfertaCanal_m3',
                    'Subterranea_m3','Estanque_medio_m3','Canal_Riego_m3',
                    'Canal_Estanque_m3','Perdida_m3','OfertaCanal_total_m3',
                    'Primera_%','Segunda_%','Perdida_%','Cobertura_%',
                ]}

                for p, c in enumerate(crops_mejor):
                    cultivo_p = str(c['nombre']).strip().lower()
                    if cultivo_p == 'no_plantar':
                        kpis_p    = _kpis_np_fin.copy()
                        graficos_p = None
                        costo_p   = 0.0
                        ppto_a    = (presupuesto_total - costos_acum) if presupuesto_total else None
                        ppto_d    = ppto_a
                    else:
                        df_s      = dfs_fin[df_fin_idx]; df_fin_idx += 1
                        kpis_p    = _kpis_de_df_sim(df_s, c, ha_part, frac_cult, dia_siembra, df_prod)
                        graficos_p = _graficos_b64(df_s, esc, 0)
                        costo_p   = float(kpis_p.get('Costo_clp', 0) or 0)
                        ppto_a    = (presupuesto_total - costos_acum) if presupuesto_total else None
                        ppto_d    = (ppto_a - costo_p)               if ppto_a is not None else None
                    costos_acum += costo_p

                    pasos_greedy.append({
                        'esc': esc, 'particion': p + 1, 'cultivo': cultivo_p,
                        'score': kpis_p.get('Margen_real_clp', 0),
                        'estanque_ini': est_ini, 'estanque_fin': est_fin,
                        'sub_ini': sub_ini,      'sub_fin': sub_fin,
                        'kpis': kpis_p,
                        'graficos': graficos_p,
                        'presupuesto_total':   presupuesto_total,
                        'presupuesto_antes':   ppto_a,
                        'presupuesto_costo':   costo_p,
                        'presupuesto_despues': ppto_d,
                        'todas_combos': combos_evaluadas if p == 0 else None,
                        'dia_siembra': dia_siembra,
                        'etapas': {
                            'L_ini': int(c['L_ini']),
                            'L_des': int(c['L_des']),
                            'L_med': int(c['L_med']),
                            'L_fin': int(c['L_fin']),
                        },
                    })

                    if cultivo_p != 'no_plantar':
                        df_det = df_s.copy()
                        df_det.insert(0, 'Particion', p + 1)
                        df_det.insert(0, 'Escenario', esc)
                        detalle_filas_p.append(df_det)

                    fila = {'Escenario': esc, 'Particion': p + 1, 'Cultivo': cultivo_p}
                    fila.update(kpis_p)
                    resumen_filas_p.append(fila)

        df_resumen_p = pd.DataFrame(resumen_filas_p)
        if detalle_filas_p:
            df_detalle_p = pd.concat(detalle_filas_p, ignore_index=True)
        else:
            df_detalle_p = pd.DataFrame()
        out_resumen_p = os.path.join(base, P.DIR_SALIDA, 'ReporteParticiones.csv')
        out_detalle_p = os.path.join(base, P.DIR_SALIDA, 'SimulacionParticiones.csv')
        df_resumen_p.to_csv(out_resumen_p, index=False)
        df_detalle_p.to_csv(out_detalle_p, index=False)
        print(f'[OK] CSV particiones: {out_resumen_p}')
        print(f'[OK] CSV detalle part: {out_detalle_p}')

        out_html_p = os.path.join(base, P.DIR_SALIDA, 'ReporteParticiones.html')
        _generar_html_particiones(out_html_p, regante, particiones, escenarios, pasos_greedy)
        print(f'[OK] HTML particiones: {out_html_p}')
        try:
            import webbrowser
            from pathlib import Path
            url = Path(out_html_p).as_uri()
            opened = webbrowser.open_new(url)
            if not opened:
                os.startfile(out_html_p)
        except Exception as e:
            print(f'[WARN] No se pudo abrir el HTML automaticamente: {e}')


if __name__ == '__main__':
    main()
