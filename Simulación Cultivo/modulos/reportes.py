"""Generación de reportes HTML del simulador (particiones y comparativa global)."""
from datetime import datetime, timedelta, date as _date
_td = timedelta  # alias usado en código Gantt
import pandas as pd
import parametros as P
from .objetos import (
    MESES, PALETTE_CULTIVOS,
    FILAS_RANKING_VISIBLES, ETAPAS_OPACIDAD, ETAPAS_LABELS, ETAPAS_KEYS,
)


def _fmt_clp(v):
    """Formatea CLP con separador de miles. None/NaN -> 'n/d'."""
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return 'n/d'
    try:
        return f"$ {int(round(float(v))):,}".replace(',', '.')
    except (TypeError, ValueError):
        return 'n/d'

def _fmt_num(v, dec=1):
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return 'n/d'
    try:
        return f"{float(v):,.{dec}f}".replace(',', '_').replace('.', ',').replace('_', '.')
    except (TypeError, ValueError):
        return 'n/d'

def _generar_html_particiones(out_html, regante, n_part, escenarios, pasos_greedy):
    _cap_est_m3 = float(regante.get('capacidad_estanque_m3', 1.0)) or 1.0
    """Genera un reporte HTML para el modo de selección greedy por particiones.
    Muestra Calidad y Rentabilidad como secciones separadas antes de los gráficos."""
    fecha        = datetime.now().strftime('%Y-%m-%d %H:%M')
    ha_tot       = float(regante['hectareas'])
    frac_cult    = float(regante.get('fraccion_cultivada', 1.0))
    ha_p         = ha_tot / n_part
    ha_cult_p    = ha_p * frac_cult
    m2_cult_p    = ha_cult_p * 10_000
    rid          = int(regante['id'])
    rnom         = str(regante.get('nombre', ''))

    css = """
    *,*::before,*::after{box-sizing:border-box}
    body{font-family:'Segoe UI',system-ui,Arial,sans-serif;font-size:14px;background:#eef1f6;color:#1c1c1c;margin:0;padding:0;line-height:1.55}
    /* ---- Header ---- */
    .header{background:linear-gradient(135deg,#0d2b52 0%,#1a3d6e 55%,#2563a8 100%);color:#fff;padding:28px 48px 24px}
    .header h1{margin:0 0 8px;font-size:1.55rem;font-weight:700;letter-spacing:.3px}
    .header-meta{display:flex;gap:28px;flex-wrap:wrap;margin-top:4px;font-size:.85rem;opacity:.82}
    .header-meta b{color:#fff;font-weight:600}
    /* ---- Layout ---- */
    .container{max-width:1220px;margin:0 auto;padding:28px 32px 64px}
    .section-card{background:#fff;border:1px solid #d8dde8;border-radius:10px;padding:26px 30px;margin-bottom:30px;box-shadow:0 2px 10px rgba(0,0,0,.07)}
    /* ---- Títulos ---- */
    h2{display:flex;align-items:center;color:#1a3d6e;font-size:1.08rem;font-weight:700;margin:0 0 20px;padding:13px 20px;border-left:5px solid #2563a8;background:#f0f4fb;border-radius:0 7px 7px 0;border:1px solid #d0daf0;border-left:5px solid #2563a8}
    h3{color:#1a3d6e;font-size:.79rem;font-weight:700;text-transform:uppercase;letter-spacing:.7px;margin:28px 0 12px;padding-bottom:6px;border-bottom:2px solid #c8d4e8}
    /* ---- Nota informativa ---- */
    .nota{background:#fffbea;border-left:4px solid #f59e0b;padding:11px 16px;font-size:.81rem;margin:4px 0 24px;border-radius:0 7px 7px 0;line-height:1.6;color:#4a3800}
    /* ---- Combinación seleccionada ---- */
    .combinacion{display:flex;gap:10px;flex-wrap:wrap;margin:8px 0 24px;padding:16px 20px;background:#f4f7fd;border:1px solid #c8d4e8;border-radius:8px}
    .badge{background:#1a3d6e;color:#fff;padding:7px 18px;border-radius:24px;font-size:.87rem;font-weight:700;letter-spacing:.2px;box-shadow:0 1px 4px rgba(0,0,0,.2)}
    .badge span{font-size:.72rem;opacity:.72;margin-right:5px}
    .badge small{display:block;font-size:.70rem;opacity:.70;font-weight:400}
    /* ---- KPI rows ---- */
    .kpi-row{display:flex;gap:10px;flex-wrap:wrap;margin:4px 0 8px}
    .kpi{background:#fff;border:1px solid #dce3ee;border-radius:8px;padding:10px 16px;font-size:.79rem;min-width:118px;color:#555;box-shadow:0 1px 4px rgba(0,0,0,.06)}
    .kpi b{display:block;font-size:1.05rem;color:#1a3d6e;font-weight:700;margin-bottom:1px}
    /* KPIs financieros destacados */
    .kpi-hero{border-radius:9px;padding:13px 20px;min-width:148px;box-shadow:0 2px 8px rgba(0,0,0,.15)}
    .kpi-hero b{font-size:1.3rem;font-weight:800;color:#fff;margin-bottom:2px;display:block}
    .kpi-hero.margen {background:linear-gradient(135deg,#0f3460,#1a3d6e);color:#c8d8f0}
    .kpi-hero.ingreso{background:linear-gradient(135deg,#14532d,#166534);color:#bbf7d0}
    .kpi-hero.costo  {background:linear-gradient(135deg,#7c2d12,#9a3412);color:#fecaca}
    .kpi-hero.prod   {background:linear-gradient(135deg,#1e3a5f,#2563a8);color:#bfdbfe}
    /* Desglose canal */
    .kpi-canal{border-left:3px solid #2563a8}
    .canal-breakdown{margin-top:6px;display:flex;flex-direction:column;gap:2px}
    .canal-breakdown span{font-size:.74rem;color:#555;padding-left:2px}
    .canal-breakdown span::before{content:"↳ ";color:#2563a8}
    /* ---- Estado del agua ---- */
    .water-state{background:#e8f0fb;border:1px solid #9bb8e8;border-left:4px solid #2563a8;border-radius:8px;padding:13px 18px;font-size:.82rem;margin:6px 0 24px;display:flex;gap:32px;flex-wrap:wrap;box-shadow:0 1px 4px rgba(0,0,0,.06)}
    .water-state div{min-width:180px}
    .water-state b{display:block;font-size:.85rem;color:#1a3d6e;margin-bottom:3px;font-weight:700}
    /* ---- Presupuesto ---- */
    .ppto-state{background:#fffbf0;border:1px solid #fbbf24;border-left:4px solid #f59e0b;border-radius:8px;padding:12px 18px;font-size:.82rem;margin:6px 0 24px;box-shadow:0 1px 4px rgba(0,0,0,.06)}
    .ppto-state b{color:#c2410c;font-weight:700}
    .ppto-bar-wrap{display:inline-block;background:#e5e7eb;border-radius:4px;height:10px;width:180px;vertical-align:middle;margin:0 8px}
    .ppto-bar-used{height:10px;border-radius:4px 0 0 4px;background:#f97316;display:inline-block;vertical-align:top}
    .ppto-row{display:flex;gap:12px;flex-wrap:wrap;margin-top:10px}
    .ppto-step{background:#fff;border:1px solid #fde68a;border-radius:6px;padding:8px 14px;font-size:.79rem;min-width:160px}
    .ppto-step b{display:block;color:#c2410c;font-size:.84rem;margin-bottom:2px}
    .ppto-step .excede{color:#b91c1c;font-size:.76rem}
    /* ---- Tablas ---- */
    table{border-collapse:collapse;width:100%;font-size:.8rem;margin-bottom:22px;background:#fff;border-radius:8px;overflow:hidden;box-shadow:0 1px 5px rgba(0,0,0,.07)}
    th{background:#e8eef6;color:#1a3d6e;padding:8px 10px;text-align:right;border-bottom:2px solid #b8c9e0;white-space:nowrap;font-size:.77rem;font-weight:700}
    th:first-child,th:nth-child(2){text-align:left}
    th.sec-agua{background:#dbeafe;color:#1e40af}
    th.sec-hum{background:#dcfce7;color:#14532d}
    th.sec-cal{background:#ffedd5;color:#7c2d12}
    th.sec-rent{background:#fce7f3;color:#831843}
    td{padding:7px 10px;border-bottom:1px solid #eef0f4;text-align:right;vertical-align:middle}
    td:first-child,td:nth-child(2){text-align:left;font-weight:600;color:#333}
    tr:last-child td{border-bottom:none}
    tr:hover:not(.ganador) td{background:#f4f7ff}
    tr.ganador td{background:#dcfce7;font-weight:700}
    tr:nth-child(even):not(.ganador):not(:hover){background:#fafbfd}
    .excede{color:#b91c1c;font-size:.76rem}
    /* ---- Barras ---- */
    .bar-wrap{width:80px;display:inline-block;vertical-align:middle;background:#e5e7eb;border-radius:3px;height:8px;margin-left:6px}
    .bar{height:8px;border-radius:3px;display:inline-block;vertical-align:top}
    .bar-green{background:#22c55e}
    .bar-orange{background:#f97316}
    .bar-red{background:#ef4444}
    /* ---- Gantt ---- */
    .gantt-wrap{background:#fff;border:1px solid #d8dde8;border-radius:8px;padding:14px 18px;margin:6px 0 24px;overflow-x:auto;box-shadow:0 1px 5px rgba(0,0,0,.06)}
    .gantt-axis{position:relative;height:20px;margin-left:110px;margin-bottom:2px}
    .gantt-tick{position:absolute;font-size:.68rem;color:#888;white-space:nowrap;border-left:1px solid #ccd;padding-left:3px;top:0;height:100%}
    .gantt-row{display:flex;align-items:center;margin-bottom:5px;min-height:34px}
    .gantt-lbl{width:110px;min-width:110px;font-size:.78rem;font-weight:700;color:#1a3d6e;line-height:1.4;padding-right:6px}
    .gantt-track{flex:1;display:flex;align-items:center;gap:8px}
    .gantt-bar{flex:1;display:flex;height:26px;border-radius:5px;overflow:hidden;box-shadow:0 1px 4px rgba(0,0,0,.14)}
    .gseg{display:flex;align-items:center;justify-content:center;overflow:hidden;white-space:nowrap;font-size:.65rem;color:#fff;font-weight:700;min-width:0}
    .gseg span{overflow:hidden;text-overflow:ellipsis;padding:0 3px}
    .gantt-cosecha{font-size:.74rem;color:#555;white-space:nowrap}
    .gantt-legend{display:flex;gap:14px;flex-wrap:wrap;margin:8px 0 4px;font-size:.74rem;color:#555}
    .gantt-legend span{display:inline-block;width:12px;height:12px;border-radius:2px;margin-right:4px;vertical-align:middle}
    """

    def _clp(v):
        if v is None or (isinstance(v, float) and pd.isna(v)): return 'n/d'
        try: return f"$ {int(round(float(v))):,}".replace(',', '.')
        except: return 'n/d'

    def _pct(v):
        if v is None or (isinstance(v, float) and pd.isna(v)): return 'n/d'
        try: return f"{float(v):.1f}%"
        except: return 'n/d'

    def _m3(v):
        if v is None or (isinstance(v, float) and pd.isna(v)): return 'n/d'
        try: return f"{float(v):.1f} m³"
        except: return 'n/d'

    def _bar(pct_val, color):
        """Barra de progreso proporcional al valor 0-100."""
        if pct_val is None or (isinstance(pct_val, float) and pd.isna(pct_val)):
            return ''
        w = max(0, min(100, float(pct_val)))
        return (f'<span class="bar-wrap"><span class="bar bar-{color}" '
                f'style="width:{w}%"></span></span>')

    nota_agua = (
        "<b>Agua compartida entre particiones:</b> el canal entrega agua una sola vez por día "
        "y se reparte entre todos los cultivos según su demanda. El estanque y el agua "
        "subterránea también son compartidos. Menos agua disponible → menor humedad del suelo "
        "(H%) → mayor proporción en segunda o pérdida → menor ingreso real."
    )

    secciones = []
    for esc in escenarios:
        pasos_esc = [p for p in pasos_greedy if p['esc'] == esc]
        if not pasos_esc:
            continue

        # ---- Badges ----
        badges_html = ''.join(
            f'<div class="badge"><span>P{ps["particion"]}</span>'
            f'{ps["cultivo"].title()}</div>'
            for ps in pasos_esc
        )

        # ---- KPIs totales del portafolio ----
        margen_total  = sum(float(ps['kpis'].get('Margen_real_clp',  0) or 0) for ps in pasos_esc)
        ingreso_total = sum(float(ps['kpis'].get('Ingreso_real_clp', 0) or 0) for ps in pasos_esc)
        costo_total   = sum(float(ps['kpis'].get('Costo_clp',        0) or 0) for ps in pasos_esc)
        prod_total    = sum(float(ps['kpis'].get('Produccion_real',   0) or 0) for ps in pasos_esc)
        aplic_total   = sum(float(ps['kpis'].get('Aplicado_m3',       0) or 0) for ps in pasos_esc)
        def_total     = sum(float(ps['kpis'].get('Deficit_m3',        0) or 0) for ps in pasos_esc)
        canal_total   = sum(float(ps['kpis'].get('OfertaCanal_m3',    0) or 0) for ps in pasos_esc)
        sub_total     = sum(float(ps['kpis'].get('Subterranea_m3',    0) or 0) for ps in pasos_esc)
        est_med_total = sum(float(ps['kpis'].get('Estanque_medio_m3', 0) or 0) for ps in pasos_esc)
        est_util_avg  = round(est_med_total / n_part / _cap_est_m3 * 100, 1) if _cap_est_m3 > 0 else 0.0
        # Descomposición canal: riego directo + almacenado en estanque + pérdida
        canal_riego_total = sum(float(ps['kpis'].get('Canal_Riego_m3',    0) or 0) for ps in pasos_esc)
        canal_est_total   = sum(float(ps['kpis'].get('Canal_Estanque_m3', 0) or 0) for ps in pasos_esc)
        canal_perd_total  = sum(float(ps['kpis'].get('Perdida_m3',        0) or 0) for ps in pasos_esc)
        canal_grand_total = sum(float(ps['kpis'].get('OfertaCanal_total_m3', 0) or 0) for ps in pasos_esc)
        _pct_c = lambda v: f"{v/canal_grand_total*100:.0f}%" if canal_grand_total > 0 else "–"

        kpis_html = f"""
        <div class="kpi-row">
          <div class="kpi kpi-hero margen"><b>{_clp(margen_total)}</b>Margen total</div>
          <div class="kpi kpi-hero ingreso"><b>{_clp(ingreso_total)}</b>Ingreso real total</div>
          <div class="kpi kpi-hero costo"><b>{_clp(costo_total)}</b>Costo total</div>
          <div class="kpi kpi-hero prod"><b>{prod_total:,.1f} kg</b>Producción total</div>
        </div>
        <div class="kpi-row">
          <div class="kpi"><b>{ha_p*10_000:,.0f} m²</b>Superficie por partición</div>
          <div class="kpi kpi-canal">
            <b>{_m3(canal_grand_total)}</b>Oferta canal total
            <div class="canal-breakdown">
              <span>Riego: {_m3(canal_riego_total)} ({_pct_c(canal_riego_total)})</span>
              <span>Estanque: {_m3(canal_est_total)} ({_pct_c(canal_est_total)})</span>
              <span>Pérdida: {_m3(canal_perd_total)} ({_pct_c(canal_perd_total)})</span>
            </div>
          </div>
          <div class="kpi"><b>{_m3(sub_total)}</b>Agua subterránea</div>
          <div class="kpi"><b>{_m3(aplic_total)}</b>Agua total aplicada</div>
          <div class="kpi"><b>{_m3(def_total)}</b>Déficit total</div>
          <div class="kpi"><b>{est_util_avg:.1f}%</b>% util. estanque</div>
          <div class="kpi"><b>{_m3(est_med_total / n_part)}</b>Nivel med. estanque</div>
        </div>"""

        # ---- Estado compartido del agua ----
        ps0 = pasos_esc[0]
        est_ini  = ps0.get('estanque_ini', 0)
        est_fin  = ps0.get('estanque_fin', 0)
        sub_ini  = ps0.get('sub_ini', 0)
        sub_fin  = ps0.get('sub_fin', 0)
        water_state_html = f"""
        <div class="water-state">
          <div><b>Estanque compartido</b>
            Inicio: {_m3(est_ini)} &nbsp;→&nbsp; Fin: <b>{_m3(est_fin)}</b>
            &nbsp;(consumido: {_m3(est_ini - est_fin if isinstance(est_ini,(int,float)) and isinstance(est_fin,(int,float)) else None)})
          </div>
          <div><b>Agua subterránea compartida</b>
            Inicio: {_m3(sub_ini)} &nbsp;→&nbsp; Fin: <b>{_m3(sub_fin)}</b>
            &nbsp;(consumido: {_m3(sub_ini - sub_fin if isinstance(sub_ini,(int,float)) and isinstance(sub_fin,(int,float)) else None)})
          </div>
        </div>"""

        # ---- Presupuesto por partición ----
        ppto_total = ps0.get('presupuesto_total')
        if ppto_total:
            pasos_ppto = []
            for ps in pasos_esc:
                pa   = ps.get('presupuesto_antes', ppto_total)
                pc   = ps.get('presupuesto_costo', 0) or 0
                pd_v = ps.get('presupuesto_despues', 0)
                usado_pct = (1 - (pd_v / ppto_total)) * 100 if ppto_total else 0
                pasos_ppto.append(f"""
                  <div class="ppto-step">
                    <b>P{ps['particion']}: {ps['cultivo'].title()}</b>
                    Antes: {_clp(pa)}<br>
                    Costo: <span style="color:#e65100">{_clp(pc)}</span><br>
                    Restante: <b>{_clp(pd_v)}</b>
                  </div>""")
            costo_total_ppto = sum(float(ps.get('presupuesto_costo', 0) or 0) for ps in pasos_esc)
            usado_final_pct  = min(100.0, costo_total_ppto / ppto_total * 100) if ppto_total else 0
            ppto_html = f"""
            <div class="ppto-state">
              <b>Presupuesto: {_clp(ppto_total)}</b>
              &nbsp; Usado: {_clp(costo_total_ppto)}
              <span class="ppto-bar-wrap"><span class="ppto-bar-used"
                style="width:{usado_final_pct:.1f}%"></span></span>
              Restante: <b>{_clp(ppto_total - costo_total_ppto)}</b>
              <div class="ppto-row">{''.join(pasos_ppto)}</div>
            </div>"""
        else:
            ppto_html = ''

        # ---- Tabla Calidad por partición ----
        def _fila_calidad(ps):
            k = ps['kpis']
            p1   = k.get('Primera_%')
            p2   = k.get('Segunda_%')
            pp   = k.get('Perdida_%')
            _p1f = (float(p1)/100 if p1 is not None else 0)
            _p2f = (float(p2)/100 if p2 is not None else 0)
            _ppf = (float(pp)/100 if pp is not None else 0)
            fq = _p1f*1.0 + _p2f*0.6 + _ppf*0.0
            fq_str = f"{fq*100:.1f}%" if (_p1f + _p2f + _ppf) > 0 else 'n/d'
            return f"""<tr>
              <td>P{ps['particion']}</td>
              <td>{ps['cultivo'].title()}</td>
              <td class="sec-cal">{_pct(p1)}{_bar(p1,'green')}</td>
              <td class="sec-cal">{_pct(p2)}{_bar(p2,'orange')}</td>
              <td class="sec-cal">{_pct(pp)}{_bar(pp,'red')}</td>
              <td class="sec-cal">{fq_str}</td>
            </tr>"""

        filas_calidad = ''.join(_fila_calidad(ps) for ps in pasos_esc)
        tabla_calidad = f"""
        <table>
          <tr>
            <th>Part.</th><th>Cultivo</th>
            <th class="sec-cal">1ª calidad</th>
            <th class="sec-cal">2ª calidad</th>
            <th class="sec-cal">Pérdida</th>
            <th class="sec-cal">Factor calidad</th>
          </tr>
          {filas_calidad}
        </table>"""

        # ---- Tabla Rentabilidad por partición ----
        def _fila_rent(ps):
            k = ps['kpis']
            ing_id = k.get('Ingreso_ideal_clp')
            ing_r  = k.get('Ingreso_real_clp')
            mar_r  = k.get('Margen_real_clp')
            costo  = k.get('Costo_clp')
            return f"""<tr>
              <td>P{ps['particion']}</td>
              <td>{ps['cultivo'].title()}</td>
              <td class="sec-rent">{_clp(ing_id)}</td>
              <td class="sec-rent">{_clp(ing_r)}</td>
              <td class="sec-rent">{_clp(costo)}</td>
              <td class="sec-rent">{_clp(mar_r)}</td>
            </tr>"""

        filas_rent = ''.join(_fila_rent(ps) for ps in pasos_esc)
        tabla_rent = f"""
        <table>
          <tr>
            <th>Part.</th><th>Cultivo</th>
            <th class="sec-rent">Ingreso ideal</th>
            <th class="sec-rent">Ingreso real</th>
            <th class="sec-rent">Costo</th>
            <th class="sec-rent">Margen real</th>
          </tr>
          {filas_rent}
        </table>"""

        # ---- Ranking de combinaciones evaluadas ----
        todas_combos = pasos_esc[0].get('todas_combos') or []
        if todas_combos:
            FILAS_INI  = FILAS_RANKING_VISIBLES
            esc_id     = f'esc{esc}'.replace('+','p').replace('-','m')
            encab_partic = ''.join(f'<th>P{i+1}</th>' for i in range(n_part))
            cultivos_mejor = [ps['cultivo'] for ps in pasos_esc]
            filas_vis  = ''
            filas_ext  = ''
            for rank, cb in enumerate(todas_combos, 1):
                es_mejor  = (cb['cultivos'] == cultivos_mejor)
                celdas_p  = ''.join(f'<td>{c.title()}</td>' for c in cb['cultivos'])
                excede_tag = ('<span class="excede">Excede ppto</span>'
                              if cb.get('excede_presupuesto') else '&#10003;')
                fila = (f'<tr class="{"ganador" if es_mejor else ""}">'
                        f'<td>{rank}</td>{celdas_p}'
                        f'<td>{_clp(cb["costo_total"])}</td>'
                        f'<td>{excede_tag}</td>'
                        f'<td>{_clp(cb["score"])}</td></tr>')
                if rank <= FILAS_INI:
                    filas_vis += fila
                else:
                    filas_ext += f'<tr class="combo-extra combo-{esc_id}" style="display:none">{fila[fila.index(">")+1:]}'
            n_extra = max(0, len(todas_combos) - FILAS_INI)
            btn_mas = ''
            if n_extra > 0:
                btn_mas = (f'<button class="btn-mas" id="btn-{esc_id}" '
                           f'onclick="toggleCombos(\'{esc_id}\',{n_extra},this)">'
                           f'Ver {n_extra} combinaciones m&#225;s &#9660;</button>')
            pasos_html = f"""
            <p style="font-size:.82rem;color:#555;margin:0 0 6px">
              Se evaluaron <b>{len(todas_combos)}</b> combinaciones simultáneamente
              (sin importar el orden de las particiones),
              <b>ordenadas de mayor a menor margen total</b>.
              La fila resaltada en verde es la combinación elegida.
            </p>
            <table id="tbl-{esc_id}">
              <tr><th>#</th>{encab_partic}<th>Costo total</th><th>Presupuesto</th><th>Margen total (CLP)</th></tr>
              {filas_vis}{filas_ext}
            </table>
            {btn_mas}"""
        else:
            pasos_html = '<p style="font-size:.82rem;color:#888">Sin datos de ranking.</p>'

        # ---- Gantt de calendario de cultivo ----
        _MESES   = MESES
        _PALETTE = PALETTE_CULTIVOS
        _crop_color = {}
        for _ps in pasos_esc:
            _c = _ps['cultivo']
            if _c not in _crop_color:
                _crop_color[_c] = _PALETTE[len(_crop_color) % len(_PALETTE)]

        _ds   = pasos_esc[0].get('dia_siembra', 1)
        _t0   = _date(2025, 1, 1) + _td(days=P.DIA_INICIO_SIMULACION + _ds - 2)
        _max_dias = max(
            sum(ps.get('etapas', {}).get(k, 0) for k in ('L_ini','L_des','L_med','L_fin'))
            for ps in pasos_esc) or 1
        _span = _max_dias + 15
        _stage_ops  = ETAPAS_OPACIDAD
        _stage_lbls = ETAPAS_LABELS
        _stage_keys = ETAPAS_KEYS

        # Marcas de mes en el eje
        _ticks = ''
        _d = _date(_t0.year, _t0.month, 1)
        while (_d - _t0).days <= _span:
            _x = max(0, (_d - _t0).days) / _span * 100
            _ticks += (f'<div class="gantt-tick" style="left:{_x:.1f}%">'
                       f'{_MESES[_d.month-1]}</div>')
            _d = _date(_d.year + (_d.month == 12), (_d.month % 12) + 1, 1)

        # Filas del Gantt
        _filas_g = ''
        for _ps in pasos_esc:
            _e = _ps.get('etapas', {})
            if not _e:
                continue
            _total = sum(_e.get(k, 0) for k in _stage_keys)
            _col   = _crop_color[_ps['cultivo']]
            _cosecha = (_t0 + _td(days=_total)).strftime(f'%d {_MESES[(_t0+_td(days=_total)).month-1]}')
            _segs = ''
            for _k, _lbl, _op in zip(_stage_keys, _stage_lbls, _stage_ops):
                _w = _e.get(_k, 0) / _span * 100
                _segs += (f'<div class="gseg" style="width:{_w:.2f}%;background:{_col};'
                          f'opacity:{_op}" title="{_lbl}: {_e.get(_k,0)} días">'
                          f'<span>{_lbl} {_e.get(_k,0)}d</span></div>')
            _sp_w = (_span - _total) / _span * 100
            _filas_g += (f'<div class="gantt-row">'
                         f'<div class="gantt-lbl">P{_ps["particion"]}'
                         f'<br><span style="color:{_col}">{_ps["cultivo"].title()}</span></div>'
                         f'<div class="gantt-track">'
                         f'<div class="gantt-bar">{_segs}'
                         f'<div style="flex:{_sp_w:.1f} 0 0"></div></div>'
                         f'<div class="gantt-cosecha">cosecha ~{_cosecha}</div>'
                         f'</div></div>')

        _leyenda = ''.join(
            f'<div><span style="background:{v};opacity:.9;display:inline-block;'
            f'width:12px;height:12px;border-radius:2px;margin-right:4px;vertical-align:middle">'
            f'</span>{k.title()}</div>'
            for k, v in _crop_color.items())
        _leyenda_ops = ''.join(
            f'<div><span style="background:#666;opacity:{op};display:inline-block;'
            f'width:12px;height:12px;border-radius:2px;margin-right:4px;vertical-align:middle">'
            f'</span>{lbl}</div>'
            for lbl, op in zip(['Inicial','Desarrollo','Media','Final'], _stage_ops))

        gantt_html = (f'<div class="gantt-wrap">'
                      f'<div style="display:flex;gap:18px;flex-wrap:wrap;margin-bottom:8px;'
                      f'font-size:.74rem;color:#555">{_leyenda}{_leyenda_ops}</div>'
                      f'<div class="gantt-axis">{_ticks}</div>'
                      f'{_filas_g}</div>')

        # ---- Gráficos de simulación diaria de la mejor combinación ----
        graficos_parts_html = []
        for _ps in pasos_esc:
            _g = _ps.get('graficos')
            if not _g:
                continue
            _hum_b64 = _g['humedad']
            _cal_b64  = _g.get('calendario') or _g.get('et', '')
            _pnum    = _ps['particion']
            _pnm     = _ps['cultivo'].title()
            graficos_parts_html.append(
                f'<div style="margin-bottom:24px">'
                f'<p style="font-size:.85rem;font-weight:700;color:#1a3d6e;margin:4px 0">'
                f'P{_pnum} — {_pnm}</p>'
                f'<img src="data:image/png;base64,{_hum_b64}"'
                f' style="width:100%;max-width:720px;display:block;margin-bottom:6px"'
                f' alt="Humedad suelo P{_pnum}">'
                f'<img src="data:image/png;base64,{_cal_b64}"'
                f' style="width:100%;max-width:720px;display:block"'
                f' alt="Calendario riego P{_pnum}">'
                f'</div>'
            )
        graficos_html = ''.join(graficos_parts_html)

        secciones.append(f"""
        <div class="section-card">
          <h2>Escenario {esc:+d}</h2>
          <div class="nota">{nota_agua}</div>
          <h3>Combinación seleccionada</h3>
          <div class="combinacion">{badges_html}</div>
          <h3>Indicadores del portafolio</h3>
          {kpis_html}
          <h3>Estado del agua compartida</h3>
          {water_state_html}
          {'<h3>Presupuesto</h3>' + ppto_html if ppto_html else ''}
          <h3>Calendario de cultivo por partición</h3>
          {gantt_html}
          <h3>Calidad de cosecha por partición</h3>
          {tabla_calidad}
          <h3>Rentabilidad por partición</h3>
          {tabla_rent}
          {'<h3>Simulación diaria por partición</h3>' + graficos_html if graficos_html else ''}
          <h3>Ranking de combinaciones evaluadas</h3>
          {pasos_html}
        </div>
        """)

    html = f"""<!DOCTYPE html><html lang="es"><head>
    <meta charset="UTF-8">
    <title>Reporte Particiones — {n_part} Particiones</title>
    <style>{css}
    .btn-mas{{background:#2563a8;color:#fff;border:none;border-radius:5px;
              padding:7px 20px;font-size:.82rem;cursor:pointer;margin:8px 0 20px;
              letter-spacing:.2px;box-shadow:0 1px 4px rgba(0,0,0,.15)}}
    .btn-mas:hover{{background:#1a3d6e}}
    </style>
    <script>
    function toggleCombos(escId, nExtra, btn) {{
      var rows = document.querySelectorAll('.combo-' + escId);
      var shown = rows.length > 0 && rows[0].style.display !== 'none';
      rows.forEach(function(r){{ r.style.display = shown ? 'none' : ''; }});
      btn.innerHTML = shown
        ? 'Ver ' + nExtra + ' combinaciones m\u00e1s &#9660;'
        : 'Mostrar menos &#9650;';
    }}
    </script></head><body>
    <div class="header">
      <h1>Selección de Cultivos por Partición</h1>
      <div class="header-meta">
        <span>Regante <b>#{rid} {rnom}</b></span>
        <span>Superficie total <b>{ha_tot:.2f} ha</b></span>
        <span><b>{n_part} particiones</b> de {ha_p*10_000:,.0f} m² c/u</span>
        <span>Generado <b>{fecha}</b></span>
      </div>
    </div>
    <div class="container">
      {''.join(secciones)}
    </div></body></html>"""

    with open(out_html, 'w', encoding='utf-8') as fh:
        fh.write(html)

def _generar_html(out_html, regante, cultivos, escenarios, df_resumen,
                  graficos, meta_cult):
    """Genera el reporte HTML autocontenido para todas las combinaciones
    cultivo x escenario, usando el regante seleccionado como contexto fijo."""
    fecha = datetime.now().strftime('%Y-%m-%d %H:%M')
    n_cult = len(cultivos)
    n_esc  = len(escenarios)
    rid    = int(regante['id'])
    rnom   = str(regante.get('nombre', ''))

    # ---------- Tabla maestra (una fila por combinacion) ----------
    def _td(val, kind=None):
        cls = ''
        if kind == 'good' and isinstance(val, (int, float)) and val >= 80:
            cls = 'good'
        elif kind == 'bad' and isinstance(val, (int, float)) and val > 50:
            cls = 'bad'
        return f'<td class="{cls}">{val}</td>'

    filas_tbl = []
    last_cult = None
    for _, r in df_resumen.iterrows():
        cult = r['Cultivo']
        cls_row = ' class="sep"' if last_cult is not None and cult != last_cult else ''
        last_cult = cult
        filas_tbl.append(
            f'<tr{cls_row}>'
            f'<td><b>{cult}</b></td>'
            f'<td><b>{r["Escenario"]}</b></td>'
            f'<td>{r["Etc_m3"]}</td>'
            f'<td>{r["OfertaCanal_m3"]}</td>'
            f'<td>{r["Aplicado_m3"]}</td>'
            f'<td>{r["Subterranea_m3"]}</td>'
            f'<td>{r["Perdida_m3"]}</td>'
            f'<td>{r["Deficit_m3"]}</td>'
            f'<td>{r["Turnos"]}</td>'
            f'<td>{r["Dias_estres"]}</td>'
            + _td(r["Cobertura_%"], 'good')
            + _td(r["Eficiencia_canal_%"], 'good')
            + _td(r["Depend_sub_%"], 'bad')
            + f'<td>{r["H_min_%"]}</td>'
            + f'<td>{r["H_med_%"]}</td>'
            + f'<td>{r["H_final_%"]}</td>'
            + f'<td style="color:#2e7d32;font-weight:600">{r["Primera_%"]}%</td>'
            + f'<td style="color:#ef6c00;font-weight:600">{r["Segunda_%"]}%</td>'
            + f'<td style="color:#c62828;font-weight:600">{r["Perdida_%"]}%</td>'
            + '</tr>'
        )
    tabla = '\n'.join(filas_tbl)

    # ---------- Resumen por cultivo (promedios entre escenarios) ----------
    # NOTA: KPIs economicos (mes, ingreso, costo, margen, produccion, unidad)
    # son CONSTANTES por cultivo (no dependen del escenario), por eso se
    # toman con 'first'. Cobertura/Deficit/etc si varian -> 'mean'.
    agg = (df_resumen
           .groupby(['Cultivo'], as_index=False)
           .agg(Cobertura=('Cobertura_%', 'mean'),
                Deficit=('Deficit_m3', 'mean'),
                DepSub=('Depend_sub_%', 'mean'),
                EfCanal=('Eficiencia_canal_%', 'mean'),
                DiasEstres=('Dias_estres', 'mean'),
                Mes=('Mes_cosecha', 'first'),
                Ingreso_ideal=('Ingreso_ideal_clp', 'first'),
                Ingreso_real=('Ingreso_real_clp', 'first'),
                Costo=('Costo_clp', 'first'),
                Margen_real=('Margen_real_clp', 'first'),
                Produccion=('Produccion', 'first'),
                Produccion_real=('Produccion_real', 'first'),
                Unidad=('Unidad', 'first')))
    filas_agg = []
    for _, r in agg.iterrows():
        cob = r['Cobertura']; sem = ('ok' if cob >= 95 else 'warn' if cob >= 70 else 'bad')
        prod_str = (f'{_fmt_num(r["Produccion"], 0)} {r["Unidad"]}'
                    if r['Produccion'] is not None and not pd.isna(r['Produccion'])
                    else 'n/d')
        prod_real_str = (f'{_fmt_num(r["Produccion_real"], 0)} {r["Unidad"]}'
                         if r['Produccion_real'] is not None and not pd.isna(r['Produccion_real'])
                         else 'n/d')
        _mar_col_agg = '#2e7d32' if (r['Margen_real'] or 0) >= 0 else '#c62828'
        filas_agg.append(
            f'<tr><td><b>{r["Cultivo"]}</b></td>'
            f'<td>{r["Mes"]}</td>'
            f'<td><span class="badge {sem}">{cob:.1f}%</span></td>'
            f'<td>{r["Deficit"]:.1f}</td>'
            f'<td>{r["EfCanal"]:.1f}%</td>'
            f'<td>{r["DepSub"]:.1f}%</td>'
            f'<td>{r["DiasEstres"]:.1f}</td>'
            f'<td>{_fmt_clp(r["Ingreso_ideal"])}</td>'
            f'<td>{_fmt_clp(r["Ingreso_real"])}</td>'
            f'<td>{_fmt_clp(r["Costo"])}</td>'
            f'<td><b style="color:{_mar_col_agg};">{_fmt_clp(r["Margen_real"])}</b></td>'
            f'<td>{prod_str}</td>'
            f'<td>{prod_real_str}</td></tr>'
        )
    tabla_agg = '\n'.join(filas_agg)

    # ---------- Secciones por cultivo ----------
    secciones_cult = []
    for cult in cultivos:
        info = meta_cult[cult]
        c = info['c']
        k = info['kpis']
        prod_str = (f'{_fmt_num(k["Produccion"], 0)} {k["Unidad"]}'
                    if k.get('Produccion') is not None else 'n/d')
        prod_real_str = (f'{_fmt_num(k["Produccion_real"], 0)} {k["Unidad"]}'
                         if k.get('Produccion_real') is not None else 'n/d')
        # tarjetas de configuracion del cultivo
        cfg = (
            f'<div class="cfg-grid">'
            f'<div><span>Cultivo</span><b>{info["cultivo"]}</b></div>'
            f'<div><span>Ciclo</span><b>{info["dias_totales"]} días</b></div>'
            f'<div><span>Día siembra</span><b>{info["dia_siembra"]}</b></div>'
            f'<div><span>Mes cosecha</span><b>{k.get("Mes_cosecha", "n/d")}</b></div>'
            f'<div><span>Ha efectivas</span><b>{_fmt_num(k.get("Ha_efectivas"), 2)} ha</b></div>'
            f'<div><span>ADT / AFA</span><b>{info["ADT"]:.1f} / {info["AFA"]:.1f} mm</b></div>'
            f'<div><span>AFA en H_pct</span><b>{info["h_afa_pct"]:.0f}%</b></div>'
            f'<div><span>p (agotam.)</span><b>{float(c["p"]):.2f}</b></div>'
            f'</div>'
            f'<div class="cfg-grid" style="margin-top:8px;">'
            f'<div><span>Precio/ha (mes cosecha)</span><b>{_fmt_clp(k.get("Precio_ha_mes_clp"))}</b></div>'
            f'<div><span>Costo/ha</span><b>{_fmt_clp(float(k["Costo_clp"])/k["Ha_efectivas"]) if k.get("Costo_clp") is not None and k.get("Ha_efectivas") else "n/d"}</b></div>'
            f'<div><span>Rendimiento/ha</span><b>{_fmt_num(k.get("Rendimiento_ha"), 0)} {k.get("Unidad") or ""}</b></div>'
            f'<div><span>Producción ideal</span><b>{prod_str}</b></div>'
            f'<div><span>Producción real (sin pérdidas)</span><b>{prod_real_str}</b></div>'
            f'<div><span>Ingreso ideal</span><b>{_fmt_clp(k.get("Ingreso_ideal_clp"))}</b></div>'
            f'<div><span>Ingreso real</span><b>{_fmt_clp(k.get("Ingreso_real_clp"))}</b></div>'
            f'<div><span>Costo</span><b>{_fmt_clp(k.get("Costo_clp"))}</b></div>'
            f'<div><span>Margen real</span><b style="color:{"#2e7d32" if (k.get("Margen_real_clp") or 0) >= 0 else "#c62828"};">{_fmt_clp(k.get("Margen_real_clp"))}</b></div>'
            f'</div>'
        )
        # sub-secciones por escenario
        sub_secs = []
        for esc in escenarios:
            r = df_resumen[(df_resumen['Cultivo'] == cult) &
                           (df_resumen['Escenario'] == esc)].iloc[0]
            img_h = graficos[cult][esc]['humedad']
            img_e = graficos[cult][esc]['et']
            cob = r['Cobertura_%']
            sem = ('ok' if cob >= 95 else 'warn' if cob >= 70 else 'bad')
            sub_secs.append(f'''
            <div class="esc-block">
              <h3>Escenario {esc} <span class="badge {sem}">Cobertura {cob}%</span></h3>
              <div class="kpis">
                <div class="kpi"><span>Etc real</span><b>{r["Etc_m3"]} m³</b></div>
                <div class="kpi"><span>Aplicado</span><b>{r["Aplicado_m3"]} m³</b></div>
                <div class="kpi"><span>Canal pérd.</span><b>{r["Perdida_m3"]} m³</b></div>
                <div class="kpi"><span>Subterránea</span><b>{r["Subterranea_m3"]} m³</b></div>
                <div class="kpi"><span>Stock pozo final</span><b>{r["Stock_sub_final"]} m³</b></div>
                <div class="kpi"><span>Déficit</span><b>{r["Deficit_m3"]} m³</b></div>
                <div class="kpi"><span>Días estrés</span><b>{r["Dias_estres"]} / {info["dias_totales"]}</b></div>
                <div class="kpi"><span>Ef. canal</span><b>{r["Eficiencia_canal_%"]}%</b></div>
                <div class="kpi"><span>Dep. pozo</span><b>{r["Depend_sub_%"]}%</b></div>
                <div class="kpi"><span>H promedio</span><b>{r["H_med_%"]}%</b></div>
              </div>
              <div class="kpis" style="margin-top:6px;">
                <div class="kpi" style="border-left-color:#2e7d32;"><span>1ª Calidad</span><b style="color:#2e7d32">{r["Primera_%"]}%</b></div>
                <div class="kpi" style="border-left-color:#ef6c00;"><span>2ª Calidad</span><b style="color:#ef6c00">{r["Segunda_%"]}%</b></div>
                <div class="kpi" style="border-left-color:#c62828;"><span>Pérdida calidad</span><b style="color:#c62828">{r["Perdida_%"]}%</b></div>
              </div>
              <div class="kpis" style="margin-top:6px;">
                <div class="kpi"><span>Ingreso ideal</span><b>{_fmt_clp(r.get("Ingreso_ideal_clp"))}</b></div>
                <div class="kpi"><span>Ingreso real</span><b>{_fmt_clp(r.get("Ingreso_real_clp"))}</b></div>
                <div class="kpi"><span>Costo</span><b>{_fmt_clp(r.get("Costo_clp"))}</b></div>
                <div class="kpi" style="border-left-color:{'#2e7d32' if (r.get('Margen_real_clp') or 0) >= 0 else '#c62828'};"><span>Margen real</span><b style="color:{'#2e7d32' if (r.get('Margen_real_clp') or 0) >= 0 else '#c62828'}">{_fmt_clp(r.get("Margen_real_clp"))}</b></div>
              </div>
              <div class="graficos">
                <img src="data:image/png;base64,{img_h}" alt="Humedad esc {esc}"/>
                <img src="data:image/png;base64,{img_e}" alt="ET esc {esc}"/>
              </div>
            </div>
            ''')
        secciones_cult.append(f'''
        <section class="reg" id="cult-{cult}">
          <h2>Cultivo – {cult}</h2>
          {cfg}
          {''.join(sub_secs)}
        </section>
        ''')

    # navegacion lateral
    nav = '<nav class="toc"><b>Cultivos</b><ul>' + ''.join(
        f'<li><a href="#cult-{cult}">{cult}</a></li>'
        for cult in cultivos
    ) + '</ul></nav>'

    html = f'''<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<title>Reporte simulación de demanda - {n_cult} cultivos x {n_esc} escenarios</title>
<style>
  :root {{ --bg:#fafafa; --fg:#222; --acc:#1565c0; --ok:#2e7d32; --warn:#ef6c00; --bad:#c62828; }}
  body {{ font-family:-apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif;
          background:var(--bg); color:var(--fg); margin:0; padding:24px 32px;
          padding-left:240px; }}
  h1 {{ color:var(--acc); margin:0 0 4px; }}
  .meta {{ color:#666; margin-bottom:18px; font-size:14px; }}
  nav.toc {{ position:fixed; top:0; left:0; bottom:0; width:200px;
             background:#1e293b; color:#cbd5e1; padding:18px 14px;
             overflow-y:auto; font-size:13px; }}
  nav.toc b {{ color:#fff; display:block; margin-bottom:8px; font-size:14px; }}
  nav.toc ul {{ list-style:none; padding:0; margin:0; }}
  nav.toc li {{ margin:4px 0; }}
  nav.toc a {{ color:#cbd5e1; text-decoration:none; }}
  nav.toc a:hover {{ color:#fff; text-decoration:underline; }}
  .config {{ background:#fff; border:1px solid #ddd; border-radius:8px;
             padding:14px 18px; margin-bottom:24px; font-size:14px; }}
  .config dl {{ display:grid; grid-template-columns:repeat(4,minmax(0,1fr));
                gap:6px 16px; margin:0; }}
  .config dt {{ color:#666; }} .config dd {{ margin:0; font-weight:600; }}
  table.resumen {{ width:100%; border-collapse:collapse; background:#fff;
                   font-size:12px; margin-bottom:28px;
                   box-shadow:0 1px 3px rgba(0,0,0,.08); }}
  table.resumen th, table.resumen td {{ padding:6px 8px; text-align:right;
                                        border-bottom:1px solid #eee; }}
  table.resumen th {{ background:#1565c0; color:#fff; font-weight:600;
                      position:sticky; top:0; }}
  table.resumen td:nth-child(1),table.resumen td:nth-child(2) {{ text-align:left; }}
  table.resumen tr.sep td {{ border-top:2px solid #888; }}
  td.good {{ color:var(--ok); font-weight:600; }}
  td.bad  {{ color:var(--bad); font-weight:600; }}
  table.agg {{ width:100%; border-collapse:collapse; background:#fff;
               font-size:13px; margin-bottom:28px;
               box-shadow:0 1px 3px rgba(0,0,0,.08); }}
  table.agg th, table.agg td {{ padding:7px 10px; border-bottom:1px solid #eee; }}
  table.agg th {{ background:#0f766e; color:#fff; text-align:left; }}
  section.reg {{ background:#fff; border:1px solid #ddd; border-radius:8px;
                 padding:18px 20px; margin-bottom:24px;
                 box-shadow:0 1px 3px rgba(0,0,0,.06); }}
  section.reg h2 {{ margin:0 0 14px; color:var(--acc); font-size:20px;
                    border-bottom:2px solid var(--acc); padding-bottom:6px; }}
  .cfg-grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(140px,1fr));
               gap:8px; margin-bottom:18px; font-size:13px; }}
  .cfg-grid div {{ background:#f1f5f9; padding:6px 10px; border-radius:4px; }}
  .cfg-grid span {{ color:#666; font-size:11px; display:block; }}
  .cfg-grid b {{ color:#222; }}
  .esc-block {{ border-top:1px dashed #ccc; padding-top:14px; margin-top:14px; }}
  .esc-block h3 {{ margin:0 0 10px; color:#333; font-size:16px; }}
  .badge {{ display:inline-block; padding:3px 10px; border-radius:12px;
            font-size:12px; color:#fff; margin-left:8px; vertical-align:middle; }}
  .badge.ok   {{ background:var(--ok); }}
  .badge.warn {{ background:var(--warn); }}
  .badge.bad  {{ background:var(--bad); }}
  .kpis {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(140px,1fr));
           gap:8px; margin-bottom:12px; }}
  .kpi {{ background:#f3f6fa; border-left:3px solid var(--acc);
          padding:7px 10px; border-radius:4px; }}
  .kpi span {{ display:block; color:#666; font-size:11px; text-transform:uppercase;
               letter-spacing:.4px; }}
  .kpi b {{ font-size:15px; color:#222; }}
  .kpi-canal {{ border-left:3px solid #1565c0; }}
  .canal-breakdown {{ margin-top:5px; display:flex; flex-direction:column; gap:2px; }}
  .canal-breakdown span {{ font-size:10.5px; color:#444; text-transform:none;
                           letter-spacing:0; padding-left:2px; }}
  .canal-breakdown span::before {{ content:"↳ "; color:#1565c0; }}
  .graficos {{ display:grid; grid-template-columns:1fr 1fr; gap:10px; }}
  .graficos img {{ width:100%; border:1px solid #eee; border-radius:4px; }}
  @media (max-width: 1100px) {{
    body {{ padding-left:32px; }}
    nav.toc {{ position:static; width:auto; margin-bottom:18px; }}
    .graficos {{ grid-template-columns:1fr; }}
  }}
  footer {{ text-align:center; color:#888; font-size:12px; margin-top:30px; }}
</style>
</head>
<body>
  {nav}
  <h1>Reporte de simulación de demanda hídrica</h1>
  <div class="meta">Generado el {fecha} · Regante #{rid} {rnom} · {n_cult} cultivos × {n_esc} escenarios = {n_cult*n_esc} simulaciones</div>

  <div class="config">
    <dl>
      <dt>Regante</dt><dd>#{rid} {rnom}</dd>
      <dt>Superficie</dt><dd>{float(regante["hectareas"])} ha</dd>
      <dt>Fracción cultivada</dt><dd>{float(regante["fraccion_cultivada"]):.2f}</dd>
      <dt>Frec. turno</dt><dd>{int(regante["frecuencia_dias"])} días</dd>
      <dt>Estanque ini/cap</dt><dd>{float(regante["nivel_estanque_inicial_m3"]):.0f} / {float(regante["capacidad_estanque_m3"]):.0f} m³</dd>
      <dt>Día siembra</dt><dd>{P.DIA_SIEMBRA}</dd>
      <dt>Política riego</dt><dd>Hasta H = {P.H_OBJETIVO_PCT:.0f}%</dd>
      <dt>Umbral pozo</dt><dd>{P.DIAS_SIN_RIEGO_PARA_SUBTERRANEA} días sin riego</dd>
      <dt>Stock subterráneo ini</dt><dd>{P.STOCK_SUBTERRANEO_INICIAL_M3:.0f} m³</dd>
      <dt>Día inicio sim.</dt><dd>{P.DIA_INICIO_SIMULACION}</dd>
      <dt>α suelo</dt><dd>{P.ALPHA_SUELO}</dd>
      <dt>CC / PMP</dt><dd>{P.CC} / {P.PMP}</dd>
      <dt>AET / AFE</dt><dd>{P.AET:.1f} / {P.AFE:.1f} mm</dd>
    </dl>
  </div>

  <h2 style="color:#0f766e; margin-top:0;">Resumen por cultivo (promedio entre escenarios)</h2>
  <p style="color:#666; font-size:12px; margin:-12px 0 12px;">
    Los KPIs económicos (mes, ingreso, costo, margen, producción) dependen
    solo del cultivo y el día de siembra, no del escenario.
  </p>
  <table class="agg">
    <thead><tr>
      <th>Cultivo</th><th>Mes cosecha</th><th>Cobertura</th>
      <th>Déficit m³</th><th>Ef. canal</th><th>Dep. pozo</th><th>Días estrés</th>
      <th>Ingreso ideal</th><th>Ingreso real</th><th>Costo</th><th>Margen real</th><th>Prod. ideal</th><th>Prod. real</th>
    </tr></thead>
    <tbody>{tabla_agg}</tbody>
  </table>

  <h2 style="color:#333;">Comparativa global (cultivos × escenarios)</h2>
  <table class="resumen">
    <thead><tr>
      <th>Cultivo</th><th>Esc</th>
      <th>Etc m³</th><th>Canal m³</th><th>Aplicado m³</th>
      <th>Sub m³</th><th>Pérdida m³</th><th>Déficit m³</th>
      <th>Turnos</th><th>D.estrés</th>
      <th>Cob.%</th><th>Ef.canal%</th><th>Dep.pozo%</th>
      <th>H min%</th><th>H med%</th><th>H final%</th>
      <th>1ª%</th><th>2ª%</th><th>Pérd.%</th>
    </tr></thead>
    <tbody>{tabla}</tbody>
  </table>

  {''.join(secciones_cult)}

  <footer>FAO-56 doble coeficiente · Modelo de balance hídrico capstone</footer>
</body>
</html>'''

    with open(out_html, 'w', encoding='utf-8') as f:
        f.write(html)
