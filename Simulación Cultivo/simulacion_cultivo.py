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

        cult_rows     = [row for _, row in df_cult.iterrows()]

        n_cultivos    = len(cult_rows)
        all_combos_idx = list(_cwr(range(n_cultivos), particiones))
        n_total       = len(all_combos_idx)
        print(f'[INFO] Modo combinatorio: {n_cultivos} cultivos x {particiones} particiones'
              f' -> {n_total} combinaciones a evaluar (C(n+p-1,p), sin importar el orden)')
        print()

        for esc in escenarios:
            mejor_score      = float('-inf')
            mejor_combo      = None
            combos_evaluadas = []

            print(f'  [ESC {esc:+d}] Evaluando {n_total} combinaciones...')
            for n_eval, combo_idx in enumerate(all_combos_idx, 1):
                crops_combo = [cult_rows[i] for i in combo_idx]
                d_max = max(int(c['L_ini'] + c['L_des'] + c['L_med'] + c['L_fin'])
                            for c in crops_combo)
                oferta, en_par, recarga_sub = cargar_oferta_superficial_m3(base, d_max, dia_siembra, esc)
                dfs_c, est_fin_c, sub_fin_c = simular_multi_particion(
                    crops_combo, ha_part, regante, df_clima_sim, oferta, en_par,
                    recarga_sub_diaria=recarga_sub)

                total_score = 0.0
                total_costo = 0.0
                kpis_list   = []
                for i, df_t in enumerate(dfs_c):
                    kk = _kpis_de_df_sim(df_t, crops_combo[i], ha_part, frac_cult,
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

            # Si todas las combinaciones exceden el presupuesto, tomar la más barata
            if mejor_combo is None:
                print(f'  [WARN] Esc {esc:>+2d}: todas las combinaciones superan el '
                      f'presupuesto. Se elige la más barata.')
                mejor_combo = min(combos_evaluadas, key=lambda x: x['costo_total'])

            combos_evaluadas.sort(key=lambda x: x['score'], reverse=True)

            cultivos_mejor = mejor_combo['cultivos']
            print(f'  [MEJOR] Esc {esc:>+2d}: '
                  + ' | '.join(f'P{i+1}={c.title()}' for i, c in enumerate(cultivos_mejor))
                  + f'  score={mejor_combo["score"]:,.0f}  costo=${mejor_combo["costo_total"]:,.0f}')

            # Simulación final de la mejor combinación (para CSV detalle diario)
            crops_mejor = [cult_rows[i] for i in mejor_combo['combo_idx']]
            d_max_fin   = max(int(c['L_ini'] + c['L_des'] + c['L_med'] + c['L_fin'])
                              for c in crops_mejor)
            oferta_fin, en_par_fin, recarga_sub_fin = cargar_oferta_superficial_m3(
                base, d_max_fin, dia_siembra, esc)
            dfs_fin, est_fin, sub_fin = simular_multi_particion(
                crops_mejor, ha_part, regante, df_clima_sim, oferta_fin, en_par_fin,
                recarga_sub_diaria=recarga_sub_fin)

            est_ini     = float(regante['nivel_estanque_inicial_m3'])
            sub_ini     = float(P.STOCK_SUBTERRANEO_INICIAL_M3)
            costos_acum = 0.0

            for p, (c, df_s) in enumerate(zip(crops_mejor, dfs_fin)):
                cultivo_p  = str(c['nombre']).strip().lower()
                kpis_p     = _kpis_de_df_sim(df_s, c, ha_part, frac_cult, dia_siembra, df_prod)
                graficos_p = _graficos_b64(df_s, esc, 0)
                costo_p    = float(kpis_p.get('Costo_clp', 0) or 0)
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

                df_det = df_s.copy()
                df_det.insert(0, 'Particion', p + 1)
                df_det.insert(0, 'Escenario', esc)
                detalle_filas_p.append(df_det)

                fila = {'Escenario': esc, 'Particion': p + 1, 'Cultivo': cultivo_p}
                fila.update(kpis_p)
                resumen_filas_p.append(fila)

        df_resumen_p = pd.DataFrame(resumen_filas_p)
        df_detalle_p = pd.concat(detalle_filas_p, ignore_index=True)
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
