"""Reporte interactivo de Simulación de Cultivo.

Dashboard comparativo de escenarios + explorador de combinaciones.
Reemplaza el scroll vertical del reporte estático por navegación por pestañas.

NO modifica ningún cálculo: lee el cache generado por `simulacion_cultivo.py`
(`outputs/_cache_simulacion.pkl`) y, para la pestaña "Explorar combinación",
re-simula bajo demanda usando exactamente las mismas funciones del pipeline.

Uso:
    cd "Simulación Cultivo"
    python reporte_interactivo.py
    # abre http://localhost:8051
"""
import os
import sys
import pickle
from datetime import date as _date, timedelta as _td

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

import parametros as P
from modulos.objetos import ETAPAS_OPACIDAD, ETAPAS_LABELS, ETAPAS_KEYS, MESES

import dash
import dash_bootstrap_components as dbc
from dash import dcc, html, dash_table, Input, Output, State, ALL
import plotly.graph_objects as go

CACHE_PATH = os.path.join(BASE_DIR, P.DIR_SALIDA, '_cache_simulacion.pkl')

# Colores consistentes con la estética del proyecto
COL_PRIMARY = '#1a3d6e'
COL_ACCENT  = '#2563a8'
COL_OK      = '#16a34a'
COL_WARN    = '#f59e0b'
COL_BAD     = '#dc2626'
COL_BG      = '#eef1f6'

ESC_LABEL = {-2: 'Escenario −2', -1: 'Escenario −1', 0: 'Escenario 0',
             1: 'Escenario +1', 2: 'Escenario +2'}


# ───────────────────────────── Utilidades ──────────────────────────────────
def _nombre_bonito(cultivo):
    if cultivo is None:
        return '—'
    c = str(cultivo).strip().lower()
    if c == 'no_plantar':
        return 'No plantar'
    return c.replace('_', ' ').title()


def _fmt_clp(v):
    if v is None:
        return 'n/d'
    try:
        return f"$ {int(round(float(v))):,}".replace(',', '.')
    except (TypeError, ValueError):
        return 'n/d'


def _fmt_num(v, dec=1):
    if v is None:
        return 'n/d'
    try:
        s = f"{float(v):,.{dec}f}"
        return s.replace(',', '_').replace('.', ',').replace('_', '.')
    except (TypeError, ValueError):
        return 'n/d'


def _esc_label(esc):
    return ESC_LABEL.get(int(esc), f'Escenario {esc:+d}')


# ─────────────────────────── Carga del cache ───────────────────────────────
def cargar_cache(forzar_simulacion=False):
    """Carga el cache; si no existe (o se fuerza), ejecuta la simulación."""
    if forzar_simulacion or not os.path.isfile(CACHE_PATH):
        print('[INFO] Cache no encontrado. Ejecutando simulación completa...')
        cwd0 = os.getcwd()
        try:
            os.chdir(BASE_DIR)
            import simulacion_cultivo
            simulacion_cultivo.main()
        finally:
            os.chdir(cwd0)
    with open(CACHE_PATH, 'rb') as fh:
        data = pickle.load(fh)
    return data['pasos_greedy'], data['contexto']


# ──────────────────── Agregación por escenario ─────────────────────────────
def resumen_por_escenario(pasos, esc):
    filas = [p for p in pasos if p['esc'] == esc]
    filas = sorted(filas, key=lambda x: x['particion'])

    def s(campo):
        tot = 0.0
        for f in filas:
            v = f['kpis'].get(campo)
            if v is not None:
                try:
                    tot += float(v)
                except (TypeError, ValueError):
                    pass
        return tot

    margen   = s('Margen_real_clp')
    ingreso  = s('Ingreso_real_clp')
    costo    = s('Costo_clp')
    prod     = s('Produccion_real')
    aplicado = s('Aplicado_m3')
    deficit  = s('Deficit_m3')

    ppto_total = filas[0].get('presupuesto_total') if filas else None
    ppto_usado = costo
    ppto_rest  = (ppto_total - ppto_usado) if ppto_total is not None else None

    # Calidad promedio ponderada por producción (solo cultivos reales)
    reales = [f for f in filas if f['cultivo'] != 'no_plantar']
    num1 = num2 = nump = peso = 0.0
    for f in reales:
        w = float(f['kpis'].get('Produccion_real') or 0) or 1.0
        num1 += w * float(f['kpis'].get('Primera_%') or 0)
        num2 += w * float(f['kpis'].get('Segunda_%') or 0)
        nump += w * float(f['kpis'].get('Perdida_%') or 0)
        peso += w
    if peso > 0:
        calidad1 = num1 / peso
        calidad2 = num2 / peso
        calidadp = nump / peso
    else:
        calidad1 = calidad2 = calidadp = 0.0

    cultivos = [f['cultivo'] for f in filas]

    return {
        'esc': esc, 'margen': margen, 'ingreso': ingreso, 'costo': costo,
        'prod': prod, 'aplicado': aplicado, 'deficit': deficit,
        'ppto_total': ppto_total, 'ppto_usado': ppto_usado, 'ppto_rest': ppto_rest,
        'calidad1': calidad1, 'calidad2': calidad2, 'calidadp': calidadp,
        'cultivos': cultivos,
    }


def construir_resumenes(pasos, escenarios):
    return [resumen_por_escenario(pasos, e) for e in escenarios]


# ──────────────────────────── Cargar datos ─────────────────────────────────
PASOS, CONTEXTO = cargar_cache()
ESCENARIOS   = CONTEXTO['escenarios']
PARTICIONES  = int(CONTEXTO['particiones'])
REGANTE      = CONTEXTO['regante']
CULTIVOS_DISP = CONTEXTO['cultivos_disponibles']
RESUMENES    = construir_resumenes(PASOS, ESCENARIOS)

# Mapa global cultivo -> color (misma paleta que la Carta Gantt)
from modulos.objetos import PALETTE_CULTIVOS as _PAL
CROP_COLORS = {str(c).strip().lower(): _PAL[i % len(_PAL)]
               for i, c in enumerate(CULTIVOS_DISP)}
CROP_COLORS['no_plantar'] = '#cbd5e1'


def _color_cultivo(cultivo):
    return CROP_COLORS.get(str(cultivo).strip().lower(), '#94a3b8')


def _chips_particiones(cultivos, height=18):
    """Recuadros de color por partición (mismos colores que la Gantt)."""
    chips = []
    for i, c in enumerate(cultivos):
        es_np = str(c).strip().lower() == 'no_plantar'
        chips.append(html.Div([
            html.Div(f'P{i+1}', style={
                'fontSize': '10px', 'color': '#64748b', 'textAlign': 'center',
                'marginBottom': '2px', 'fontWeight': '600'}),
            html.Div(_nombre_bonito(c), title=_nombre_bonito(c), style={
                'backgroundColor': _color_cultivo(c),
                'color': '#fff' if not es_np else '#475569',
                'border': '1px solid rgba(0,0,0,.08)',
                'borderRadius': '5px', 'padding': f'{height//4}px 6px',
                'fontSize': '11px', 'fontWeight': '600', 'whiteSpace': 'nowrap',
                'overflow': 'hidden', 'textOverflow': 'ellipsis',
                'opacity': '0.55' if es_np else '1',
                'textAlign': 'center', 'minWidth': '74px'}),
        ], style={'display': 'inline-block', 'marginRight': '6px',
                  'verticalAlign': 'top'}))
    return html.Div(chips, style={'display': 'flex', 'flexWrap': 'wrap',
                                  'gap': '2px'})


def _chip_md_single(cultivo):
    """Chip de color (HTML) para un solo cultivo, para celdas markdown."""
    es_np = str(cultivo).strip().lower() == 'no_plantar'
    col = _color_cultivo(cultivo)
    txt = '#475569' if es_np else '#ffffff'
    return (
        f'<span style="display:inline-block;background:{col};color:{txt};'
        f'border-radius:4px;padding:2px 10px;'
        f'font-size:12px;font-weight:600;white-space:nowrap'
        f'{";opacity:0.6" if es_np else ""}">'
        f'{_nombre_bonito(cultivo)}</span>'
    )


def _chips_md(cultivos):
    """Recuadros de color por partición como HTML para celdas markdown."""
    parts = []
    for i, c in enumerate(cultivos):
        es_np = str(c).strip().lower() == 'no_plantar'
        col = _color_cultivo(c)
        txt = '#475569' if es_np else '#ffffff'
        parts.append(
            f'<span style="display:inline-block;background:{col};color:{txt};'
            f'border-radius:4px;padding:1px 7px;margin:1px 4px 1px 0;'
            f'font-size:11px;font-weight:600;white-space:nowrap">'
            f'P{i+1} {_nombre_bonito(c)}</span>'
        )
    return ' '.join(parts)



# ═══════════════════════════ VISTAS / TABS ═════════════════════════════════
def _best_indices(resumenes):
    """Índices del mejor escenario por cada métrica destacada."""
    def argmax(key):
        return max(range(len(resumenes)), key=lambda i: resumenes[i][key])

    def argmin(key):
        return min(range(len(resumenes)), key=lambda i: resumenes[i][key])

    return {
        'margen':  argmax('margen'),
        'prod':    argmax('prod'),
        'deficit': argmin('deficit'),
        'calidad': argmax('calidad1'),
    }


def vista_dashboard():
    best = _best_indices(RESUMENES)

    columnas = [
        {'name': 'Escenario',        'id': 'escenario'},
        {'name': 'Margen total',     'id': 'margen'},
        {'name': 'Ingreso total',    'id': 'ingreso'},
        {'name': 'Costos',           'id': 'costo'},
        {'name': 'Producción (kg)',  'id': 'prod'},
        {'name': 'Agua aplicada (m³)', 'id': 'aplicado'},
        {'name': 'Déficit (m³)',     'id': 'deficit'},
        {'name': 'Ppto. utilizado',  'id': 'ppto'},
        {'name': 'Calidad 1ª prom.', 'id': 'calidad'},
    ]
    data = []
    for r in RESUMENES:
        if r['ppto_total']:
            ppto_str = f"{_fmt_clp(r['ppto_usado'])} / {_fmt_clp(r['ppto_total'])}"
        else:
            ppto_str = _fmt_clp(r['ppto_usado'])
        data.append({
            'escenario': _esc_label(r['esc']),
            'margen':   _fmt_clp(r['margen']),
            'ingreso':  _fmt_clp(r['ingreso']),
            'costo':    _fmt_clp(r['costo']),
            'prod':     _fmt_num(r['prod'], 1),
            'aplicado': _fmt_num(r['aplicado'], 1),
            'deficit':  _fmt_num(r['deficit'], 1),
            'ppto':     ppto_str,
            'calidad':  f"{_fmt_num(r['calidad1'], 1)} %",
        })

    style_cond = [
        {'if': {'row_index': best['margen'],  'column_id': 'margen'},
         'backgroundColor': '#dcfce7', 'fontWeight': '700', 'color': '#14532d'},
        {'if': {'row_index': best['prod'],    'column_id': 'prod'},
         'backgroundColor': '#dbeafe', 'fontWeight': '700', 'color': '#1e3a8a'},
        {'if': {'row_index': best['deficit'], 'column_id': 'deficit'},
         'backgroundColor': '#dcfce7', 'fontWeight': '700', 'color': '#14532d'},
        {'if': {'row_index': best['calidad'], 'column_id': 'calidad'},
         'backgroundColor': '#fef9c3', 'fontWeight': '700', 'color': '#713f12'},
    ]

    tabla = dash_table.DataTable(
        columns=columnas, data=data,
        style_as_list_view=True,
        style_header={'backgroundColor': COL_PRIMARY, 'color': '#fff',
                      'fontWeight': '700', 'textAlign': 'center',
                      'border': 'none', 'fontSize': '13px'},
        style_cell={'textAlign': 'center', 'padding': '12px 10px',
                    'fontFamily': 'Segoe UI, system-ui, Arial', 'fontSize': '13px',
                    'border': '1px solid #e5e9f0'},
        style_data_conditional=[
            {'if': {'column_id': 'escenario'}, 'fontWeight': '700',
             'color': COL_PRIMARY, 'textAlign': 'left'},
            *style_cond,
        ],
    )

    leyenda = html.Div([
        html.Span("● ", style={'color': '#16a34a'}),
        html.Small("Mayor margen / menor déficit   ", className='text-muted'),
        html.Span("● ", style={'color': '#2563a8'}),
        html.Small("Mayor producción   ", className='text-muted'),
        html.Span("● ", style={'color': '#ca8a04'}),
        html.Small("Mejor calidad", className='text-muted'),
    ], className='mt-2')

    return html.Div([
        html.H5("Comparación de escenarios", className='fw-bold mb-1',
                style={'color': COL_PRIMARY}),
        html.P("Identifica el mejor escenario sin abrir el detalle. Las celdas "
               "destacadas marcan el óptimo de cada métrica.",
               className='text-muted small'),
        dbc.Card(dbc.CardBody([tabla, leyenda]), className='shadow-sm'),
    ])


def vista_cultivos():
    columnas = [{'name': 'Escenario', 'id': 'escenario'}]
    for p in range(PARTICIONES):
        columnas.append({'name': f'P{p+1}', 'id': f'p{p+1}',
                         'presentation': 'markdown'})

    data = []
    for r in RESUMENES:
        fila = {'escenario': _esc_label(r['esc'])}
        for p in range(PARTICIONES):
            cult = r['cultivos'][p] if p < len(r['cultivos']) else 'no_plantar'
            fila[f'p{p+1}'] = _chip_md_single(cult)
        data.append(fila)

    style_cond = [
        {'if': {'column_id': 'escenario'}, 'fontWeight': '700',
         'color': COL_PRIMARY, 'textAlign': 'left'},
    ]

    tabla = dash_table.DataTable(
        columns=columnas, data=data, style_as_list_view=True,
        markdown_options={'html': True},
        style_header={'backgroundColor': COL_PRIMARY, 'color': '#fff',
                      'fontWeight': '700', 'textAlign': 'center', 'border': 'none'},
        style_cell={'textAlign': 'center', 'padding': '12px 10px',
                    'fontFamily': 'Segoe UI, system-ui, Arial', 'fontSize': '13px',
                    'border': '1px solid #e5e9f0'},
        style_data_conditional=style_cond,
    )
    return html.Div([
        html.H5("Cultivos seleccionados por escenario", className='fw-bold mb-1',
                style={'color': COL_PRIMARY}),
        html.P("Qué cultivo ganó en cada partición, para cada escenario "
               "(mismos colores que la Carta Gantt y Corridas experimentales).",
               className='text-muted small'),
        dbc.Card(dbc.CardBody(tabla), className='shadow-sm'),
    ])


def vista_presupuesto():
    tiene_ppto = any(r['ppto_total'] for r in RESUMENES)
    if not tiene_ppto:
        return dbc.Alert("No hay un presupuesto configurado (P.PRESUPUESTO). "
                         "Esta vista compara solo el costo utilizado.",
                         color='warning')

    labels = [_esc_label(r['esc']) for r in RESUMENES]
    usados = [r['ppto_usado'] for r in RESUMENES]
    restantes = [max(r['ppto_rest'] or 0, 0) for r in RESUMENES]
    total = RESUMENES[0]['ppto_total']

    fig = go.Figure()
    fig.add_bar(name='Utilizado', x=labels, y=usados, marker_color=COL_ACCENT,
                text=[_fmt_clp(v) for v in usados], textposition='inside')
    fig.add_bar(name='Restante', x=labels, y=restantes, marker_color='#cbd5e1',
                text=[_fmt_clp(v) for v in restantes], textposition='inside')
    if total:
        fig.add_hline(y=total, line_dash='dash', line_color=COL_BAD,
                      annotation_text=f'Presupuesto: {_fmt_clp(total)}',
                      annotation_position='top left')
    fig.update_layout(barmode='stack', template='plotly_white',
                      height=420, margin=dict(l=40, r=20, t=30, b=40),
                      legend=dict(orientation='h', y=1.12, x=0),
                      yaxis_title='CLP')

    return html.Div([
        html.H5("Comparación de presupuesto", className='fw-bold mb-1',
                style={'color': COL_PRIMARY}),
        html.P("Presupuesto disponible, utilizado y restante por escenario.",
               className='text-muted small'),
        dbc.Card(dbc.CardBody(dcc.Graph(figure=fig)), className='shadow-sm'),
    ])


def vista_calidad():
    labels = [_esc_label(r['esc']) for r in RESUMENES]
    primera = [r['calidad1'] for r in RESUMENES]
    segunda = [r['calidad2'] for r in RESUMENES]
    perdida = [r['calidadp'] for r in RESUMENES]

    fig = go.Figure()
    fig.add_bar(name='1ª calidad', x=labels, y=primera, marker_color=COL_OK,
                text=[f"{v:.0f}%" for v in primera], textposition='inside')
    fig.add_bar(name='2ª calidad', x=labels, y=segunda, marker_color=COL_WARN,
                text=[f"{v:.0f}%" for v in segunda], textposition='inside')
    fig.add_bar(name='Pérdidas', x=labels, y=perdida, marker_color=COL_BAD,
                text=[f"{v:.0f}%" for v in perdida], textposition='inside')
    fig.update_layout(barmode='stack', template='plotly_white', height=420,
                      margin=dict(l=40, r=20, t=30, b=40),
                      legend=dict(orientation='h', y=1.12, x=0),
                      yaxis_title='% de producción', yaxis_range=[0, 100])

    return html.Div([
        html.H5("Comparación de calidad", className='fw-bold mb-1',
                style={'color': COL_PRIMARY}),
        html.P("Distribución de calidad (1ª, 2ª y pérdidas) ponderada por "
               "producción, por escenario.", className='text-muted small'),
        dbc.Card(dbc.CardBody(dcc.Graph(figure=fig)), className='shadow-sm'),
    ])


def _corridas_money_fmt():
    from dash.dash_table.Format import Format, Scheme, Symbol, Group
    return (Format(precision=0, scheme=Scheme.fixed)
            .symbol(Symbol.yes).symbol_prefix('$\u00a0')
            .group(Group.yes).group_delimiter('.'))


def _corridas_filas(esc):
    """Filas (corridas) de un escenario, ordenadas por margen desc."""
    paso1 = next((p for p in PASOS
                  if p['esc'] == esc and p['particion'] == 1), None)
    ppto_total = paso1.get('presupuesto_total') if paso1 else None
    filas = []
    if paso1:
        for c in (paso1.get('todas_combos') or []):
            cultivos = c.get('cultivos') or []
            costo = float(c.get('costo_total') or 0)
            if c.get('excede_presupuesto') and ppto_total is not None:
                exceso = costo - float(ppto_total)
                ppto_txt = f'✗ excede {_fmt_clp(exceso)}'
            else:
                ppto_txt = '✓'
            filas.append({
                'esc_val': int(esc),
                'cultivos_raw': '|'.join(str(x) for x in cultivos),
                'combo':  _chips_md(cultivos),
                'margen': float(c.get('margen', c.get('score')) or 0),
                'calidad': float(c.get('calidad_prom') or 0),
                'score':  float(c.get('score') or 0),
                'costo':  costo,
                'ppto':   ppto_txt,
            })
    filas.sort(key=lambda x: x['score'], reverse=True)
    return filas


def _corridas_hero(esc, filas):
    if not filas:
        return dbc.Alert(f"{_esc_label(esc)}: sin corridas registradas.",
                         color='warning')
    mejor = filas[0]
    return dbc.Card(dbc.CardBody([
        html.Div(f"Mejor corrida · {_esc_label(esc)}", className='text-muted small'),
        html.H3(_fmt_clp(mejor['margen']), className='fw-bold mb-2',
                style={'color': COL_OK if mejor['margen'] >= 0 else COL_BAD}),
        _chips_particiones(mejor['cultivos_raw'].split('|')),
    ]), className='shadow-sm mb-3', style={'borderLeft': f'5px solid {COL_OK}'})


def _corridas_resumen(esc, filas):
    n_total   = len(filas)
    n_cumplen = sum(1 for f in filas if f['ppto'] == '✓')
    n_positivo = sum(1 for f in filas if f['margen'] > 0)
    return dbc.Row([
        dbc.Col(_kpi_card('Corridas en este escenario',
                          f"{n_total:,}".replace(',', '.'), COL_ACCENT), md=4),
        dbc.Col(_kpi_card('Cumplen presupuesto',
                          f"{n_cumplen:,}".replace(',', '.'), COL_OK), md=4),
        dbc.Col(_kpi_card('Con margen positivo',
                          f"{n_positivo:,}".replace(',', '.'), COL_PRIMARY), md=4),
    ], className='g-2 mb-3')


def vista_corridas():
    money = _corridas_money_fmt()
    from dash.dash_table.Format import Format, Scheme, Group
    num_miles = (Format(precision=0, scheme=Scheme.fixed)
                 .group(Group.yes).group_delimiter('.'))

    if not any(next((p for p in PASOS if p['esc'] == e and p['particion'] == 1), None)
               for e in ESCENARIOS):
        return dbc.Alert(
            "No hay corridas experimentales registradas en el cache. "
            "Vuelve a ejecutar la simulación para regenerarlo.", color='warning')

    # Escenario por defecto: el escenario 0 (si existe); si no, el primero
    esc_def = 0 if 0 in ESCENARIOS else ESCENARIOS[0]
    opciones = [{'label': _esc_label(e), 'value': e} for e in ESCENARIOS]
    filas0 = _corridas_filas(esc_def)

    columnas = [
        {'name': 'Combinación (P1 · P2 · …)', 'id': 'combo',
         'presentation': 'markdown'},
        {'name': 'Margen', 'id': 'margen', 'type': 'numeric', 'format': money},
        {'name': 'Calidad comp.', 'id': 'calidad', 'type': 'numeric',
         'format': Format(precision=0, scheme=Scheme.fixed)},
        {'name': 'Score', 'id': 'score', 'type': 'numeric', 'format': num_miles},
        {'name': 'Costo',  'id': 'costo',  'type': 'numeric', 'format': money},
        {'name': 'Presupuesto', 'id': 'ppto'},
    ]

    tabla = dash_table.DataTable(
        id='tabla-corridas',
        columns=columnas, data=filas0,
        sort_action='native', filter_action='native', page_size=15,
        markdown_options={'html': True},
        style_as_list_view=True,
        cell_selectable=True,
        style_header={'backgroundColor': COL_PRIMARY, 'color': '#fff',
                      'fontWeight': '700', 'textAlign': 'center',
                      'border': 'none', 'fontSize': '13px'},
        style_cell={'textAlign': 'center', 'padding': '10px 10px',
                    'fontFamily': 'Segoe UI, system-ui, Arial', 'fontSize': '13px',
                    'border': '1px solid #e5e9f0'},
        style_cell_conditional=[
            {'if': {'column_id': 'combo'}, 'textAlign': 'left', 'minWidth': '340px'},
            {'if': {'column_id': 'margen'}, 'textAlign': 'right'},
            {'if': {'column_id': 'calidad'}, 'textAlign': 'right'},
            {'if': {'column_id': 'score'}, 'textAlign': 'right'},
            {'if': {'column_id': 'costo'}, 'textAlign': 'right'},
        ],
        style_data_conditional=[
            {'if': {'filter_query': '{ppto} contains "excede"'},
             'color': '#9ca3af', 'fontStyle': 'italic'},
            {'if': {'filter_query': '{margen} < 0', 'column_id': 'margen'},
             'color': COL_BAD},
            {'if': {'filter_query': '{margen} > 0', 'column_id': 'margen'},
             'color': COL_OK, 'fontWeight': '600'},
            {'if': {'state': 'active'},
             'backgroundColor': '#e0ecff', 'border': f'1px solid {COL_ACCENT}'},
        ],
        css=[{'selector': 'td.dash-cell div.dash-cell-value',
              'rule': 'overflow: visible;'}],
    )

    control = dbc.Card(dbc.CardBody(dbc.Row([
        dbc.Col([
            dbc.Label('Escenario', className='fw-semibold small'),
            dcc.Dropdown(id='sel-esc-corridas', options=opciones, value=esc_def,
                         clearable=False, style={'fontSize': '13px'}),
        ], md=4, sm=12),
        dbc.Col(html.Div("Cambia el escenario para ver sus corridas. "
                         "Haz clic en una fila para el detalle completo.",
                         className='text-muted small mt-4'), md=8),
    ])), className='shadow-sm mb-3')

    return html.Div([
        html.H5("Corridas experimentales", className='fw-bold mb-1',
                style={'color': COL_PRIMARY}),
        html.P("Combinaciones evaluadas, ordenadas por el score del modelo "
               "(margen × calidad promedio de 1ª). Cada recuadro de color es una "
               "partición (mismos colores que la Carta Gantt).",
               className='text-muted small'),
        control,
        html.Div(_corridas_hero(esc_def, filas0), id='corridas-hero'),
        html.Div(_corridas_resumen(esc_def, filas0), id='corridas-resumen'),
        dbc.Card(dbc.CardBody(tabla), className='shadow-sm mb-3'),
        dcc.Loading(html.Div(id='detalle-corrida'), type='default'),
    ])


def vista_explorar():
    opciones_esc = [{'label': _esc_label(e), 'value': e} for e in ESCENARIOS]
    opciones_cult = [{'label': _nombre_bonito(c), 'value': c} for c in CULTIVOS_DISP]
    opciones_cult.append({'label': 'No plantar', 'value': 'no_plantar'})

    selectores_part = []
    for p in range(PARTICIONES):
        selectores_part.append(dbc.Col([
            dbc.Label(f'Partición {p+1}', className='fw-semibold small'),
            dcc.Dropdown(
                id={'type': 'sel-cultivo', 'index': p},
                options=opciones_cult,
                value=CULTIVOS_DISP[0] if CULTIVOS_DISP else 'no_plantar',
                clearable=False, style={'fontSize': '13px'},
            ),
        ], md=3, sm=6, className='mb-2'))

    controles = dbc.Card(dbc.CardBody([
        dbc.Row([
            dbc.Col([
                dbc.Label('Escenario', className='fw-semibold small'),
                dcc.Dropdown(id='sel-escenario', options=opciones_esc,
                             value=ESCENARIOS[len(ESCENARIOS) // 2],
                             clearable=False, style={'fontSize': '13px'}),
            ], md=3, sm=12, className='mb-2'),
            dbc.Col(html.Div(), md=9),
        ]),
        html.Hr(className='my-2'),
        dbc.Label('Cultivo por partición', className='fw-semibold small'),
        dbc.Row(selectores_part),
        dbc.Button('Simular combinación', id='btn-simular-combo',
                   color='primary', className='fw-bold mt-2'),
    ]), className='shadow-sm mb-3')

    return html.Div([
        html.H5("Explorar combinación", className='fw-bold mb-1',
                style={'color': COL_PRIMARY}),
        html.P("Elige un escenario y un cultivo por partición; al simular verás "
               "el detalle completo de esa combinación.", className='text-muted small'),
        controles,
        dcc.Loading(html.Div(id='salida-combo'), type='default'),
    ])


# ───────────────── Render del detalle (Explorar combinación) ────────────────
def _img(b64, alt=''):
    if not b64:
        return None
    return html.Img(src=f'data:image/png;base64,{b64}',
                    style={'width': '100%', 'borderRadius': '8px',
                           'border': '1px solid #e5e9f0'}, alt=alt)


def _gantt_figure(res):
    fig = go.Figure()
    filas = [p for p in res['pasos'] if p['cultivo'] != 'no_plantar']
    crop_colors = res['graficos_compartidos']['crop_colors']
    if not filas:
        fig.add_annotation(text='Sin cultivos plantados',
                           showarrow=False, font=dict(size=14, color='#94a3b8'))
        fig.update_layout(template='plotly_white', height=180)
        return fig

    # Origen de fechas: mismo criterio que el reporte estatico
    ds = int(res.get('dia_siembra', 1) or 1)
    t0 = _date(2025, 1, 1) + _td(days=int(P.DIA_INICIO_SIMULACION) + ds - 2)

    def _fdate(dd):
        return f"{dd.day:02d} {MESES[dd.month - 1]}"

    for f in filas:
        y = f"P{f['particion']}: {_nombre_bonito(f['cultivo'])}"
        color = crop_colors.get(f['cultivo'], COL_ACCENT)
        etapas = f['etapas']
        dur = [etapas['L_ini'], etapas['L_des'], etapas['L_med'], etapas['L_fin']]
        offset = 0
        for i, d in enumerate(dur):
            if d <= 0:
                continue
            inicio = t0 + _td(days=offset)
            fin = inicio + _td(days=d)
            fig.add_trace(go.Bar(
                y=[y], x=[d * 86400000], base=inicio.isoformat(), orientation='h',
                marker=dict(color=color, opacity=ETAPAS_OPACIDAD[i]),
                name=ETAPAS_LABELS[i], showlegend=False,
                hovertemplate=(f"{ETAPAS_LABELS[i]}: {_fdate(inicio)} → "
                               f"{_fdate(fin)} ({d} días)<extra></extra>"),
            ))
            offset += d

    fig.update_layout(
        barmode='stack', template='plotly_white',
        height=120 + 55 * len(filas),
        margin=dict(l=10, r=20, t=20, b=40),
        xaxis=dict(type='date', tickformat='%d %b', title='Fecha'),
        yaxis=dict(autorange='reversed'),
    )
    return fig


def _calidad_combo_figure(reales):
    labels = [f"P{p['particion']}: {_nombre_bonito(p['cultivo'])}" for p in reales]
    primera = [float(p['kpis'].get('Primera_%') or 0) for p in reales]
    segunda = [float(p['kpis'].get('Segunda_%') or 0) for p in reales]
    perdida = [float(p['kpis'].get('Perdida_%') or 0) for p in reales]

    fig = go.Figure()
    fig.add_bar(name='1ª calidad', x=labels, y=primera, marker_color=COL_OK,
                text=[f"{v:.0f}%" for v in primera], textposition='inside')
    fig.add_bar(name='2ª calidad', x=labels, y=segunda, marker_color=COL_WARN,
                text=[f"{v:.0f}%" for v in segunda], textposition='inside')
    fig.add_bar(name='Pérdidas', x=labels, y=perdida, marker_color=COL_BAD,
                text=[f"{v:.0f}%" for v in perdida], textposition='inside')
    fig.update_layout(barmode='stack', template='plotly_white', height=360,
                      margin=dict(l=40, r=20, t=30, b=70),
                      legend=dict(orientation='h', y=1.15, x=0),
                      yaxis_title='% de producción', yaxis_range=[0, 100])
    return fig


def _kpi_card(titulo, valor, color=COL_PRIMARY, sub=None):
    cuerpo = [html.Div(titulo, className='text-muted', style={'fontSize': '12px'}),
              html.Div(valor, className='fw-bold',
                       style={'fontSize': '18px', 'color': color})]
    if sub:
        cuerpo.append(html.Div(sub, className='text-muted', style={'fontSize': '11px'}))
    return dbc.Card(dbc.CardBody(cuerpo, className='py-2 px-3'),
                    className='shadow-sm', style={'borderLeft': f'4px solid {color}'})


def render_detalle_combo(res):
    pasos  = res['pasos']
    reales = [p for p in pasos if p['cultivo'] != 'no_plantar']

    # ── Resumen agregado ──
    margen = sum(float(p['kpis'].get('Margen_real_clp') or 0) for p in pasos)
    ingreso = sum(float(p['kpis'].get('Ingreso_real_clp') or 0) for p in pasos)
    costo = sum(float(p['kpis'].get('Costo_clp') or 0) for p in pasos)
    prod = sum(float(p['kpis'].get('Produccion_real') or 0) for p in pasos)
    aplicado = sum(float(p['kpis'].get('Aplicado_m3') or 0) for p in pasos)
    deficit = sum(float(p['kpis'].get('Deficit_m3') or 0) for p in pasos)

    alerta_ppto = None
    if res['excede_presupuesto']:
        alerta_ppto = dbc.Alert(
            [html.Strong("⚠ Excede el presupuesto. "),
             f"Costo {_fmt_clp(res['costo_total'])} > "
             f"{_fmt_clp(res['presupuesto_total'])}."],
            color='danger', className='py-2')

    kpis_row = dbc.Row([
        dbc.Col(_kpi_card('Margen total', _fmt_clp(margen),
                          COL_OK if margen >= 0 else COL_BAD), md=2, sm=4),
        dbc.Col(_kpi_card('Ingreso total', _fmt_clp(ingreso), COL_ACCENT), md=2, sm=4),
        dbc.Col(_kpi_card('Costos', _fmt_clp(costo), COL_BAD), md=2, sm=4),
        dbc.Col(_kpi_card('Producción', f"{_fmt_num(prod, 1)} kg", COL_PRIMARY), md=2, sm=4),
        dbc.Col(_kpi_card('Agua aplicada', f"{_fmt_num(aplicado, 1)} m³", COL_ACCENT), md=2, sm=4),
        dbc.Col(_kpi_card('Déficit', f"{_fmt_num(deficit, 1)} m³",
                          COL_WARN if deficit > 0 else COL_OK), md=2, sm=4),
    ], className='g-2 mb-3')

    # ── Tabla rentabilidad ──
    rent_rows = []
    for p in reales:
        k = p['kpis']
        rent_rows.append(html.Tr([
            html.Td(f"P{p['particion']}"),
            html.Td(_nombre_bonito(p['cultivo'])),
            html.Td(_fmt_clp(k.get('Ingreso_ideal_clp')), className='text-end'),
            html.Td(_fmt_clp(k.get('Ingreso_real_clp')), className='text-end'),
            html.Td(_fmt_clp(k.get('Costo_clp')), className='text-end'),
            html.Td(_fmt_clp(k.get('Margen_real_clp')), className='text-end fw-bold'),
        ]))
    tabla_rent = dbc.Table([
        html.Thead(html.Tr([html.Th('Part.'), html.Th('Cultivo'),
                            html.Th('Ing. ideal', className='text-end'),
                            html.Th('Ing. real', className='text-end'),
                            html.Th('Costo', className='text-end'),
                            html.Th('Margen', className='text-end')])),
        html.Tbody(rent_rows),
    ], bordered=False, hover=True, striped=True, size='sm', className='mb-0')

    # ── Tabla calidad ──
    cal_rows = []
    for p in reales:
        k = p['kpis']
        cal_rows.append(html.Tr([
            html.Td(f"P{p['particion']}"),
            html.Td(_nombre_bonito(p['cultivo'])),
            html.Td(f"{_fmt_num(k.get('Primera_%'), 1)} %", className='text-end'),
            html.Td(f"{_fmt_num(k.get('Segunda_%'), 1)} %", className='text-end'),
            html.Td(f"{_fmt_num(k.get('Perdida_%'), 1)} %", className='text-end'),
        ]))
    tabla_cal = dbc.Table([
        html.Thead(html.Tr([html.Th('Part.'), html.Th('Cultivo'),
                            html.Th('1ª calidad', className='text-end'),
                            html.Th('2ª calidad', className='text-end'),
                            html.Th('Pérdida', className='text-end')])),
        html.Tbody(cal_rows),
    ], bordered=False, hover=True, striped=True, size='sm', className='mb-0')

    # ── Estado del agua ──
    estado_agua = dbc.Row([
        dbc.Col(_kpi_card('Estanque inicio → fin',
                          f"{_fmt_num(res['estanque_ini'], 0)} → "
                          f"{_fmt_num(res['estanque_fin'], 0)} m³", COL_ACCENT), md=4),
        dbc.Col(_kpi_card('Subterráneo inicio → fin',
                          f"{_fmt_num(res['sub_ini'], 0)} → "
                          f"{_fmt_num(res['sub_fin'], 0)} m³", COL_PRIMARY), md=4),
    ], className='g-2')

    # ── Presupuesto ──
    presup = None
    if res['presupuesto_total']:
        usado = res['costo_total']
        pct = min(usado / res['presupuesto_total'] * 100, 100) if res['presupuesto_total'] else 0
        presup = html.Div([
            html.Div([
                html.Span(f"Utilizado: {_fmt_clp(usado)}", className='small fw-semibold'),
                html.Span(f"Disponible: {_fmt_clp(res['presupuesto_total'])}",
                          className='small text-muted float-end'),
            ]),
            dbc.Progress(value=pct, color=('danger' if res['excede_presupuesto'] else 'success'),
                         className='mt-1', style={'height': '20px'},
                         label=f"{pct:.0f}%"),
        ])

    # ── Gráficos compartidos ──
    gc = res['graficos_compartidos']
    graf_compartidos = []
    for titulo, key in [('Distribución de oferta superficial', 'grafico_canal'),
                        ('Agua aplicada por cultivo', 'grafico_cultivos'),
                        ('Nivel del estanque', 'grafico_estanque'),
                        ('Stock de agua subterránea', 'grafico_sub')]:
        img = _img(gc.get(key), titulo)
        if img is not None:
            graf_compartidos.append(dbc.Col([
                html.H6(titulo, className='small fw-bold mt-2',
                        style={'color': COL_PRIMARY}), img], md=6, className='mb-3'))

    # ── Gráficos por partición ──
    graf_part = []
    for p in reales:
        g = p['graficos'] or {}
        imgs = []
        for titulo, key in [('Humedad del suelo', 'humedad'),
                            ('ET y riego', 'et'),
                            ('Agua por fuente', 'fuente')]:
            im = _img(g.get(key), titulo)
            if im is not None:
                imgs.append(dbc.Col([html.Div(titulo, className='small text-muted'),
                                     im], md=4, className='mb-2'))
        if imgs:
            graf_part.append(dbc.Card(dbc.CardBody([
                html.H6(f"P{p['particion']} · {_nombre_bonito(p['cultivo'])}",
                        className='fw-bold', style={'color': COL_PRIMARY}),
                dbc.Row(imgs),
            ]), className='shadow-sm mb-3'))

    secciones = [
        alerta_ppto,
        kpis_row,
        dbc.Card(dbc.CardBody([
            html.H6('Carta Gantt', className='fw-bold', style={'color': COL_PRIMARY}),
            dcc.Graph(figure=_gantt_figure(res), config={'displayModeBar': False}),
        ]), className='shadow-sm mb-3'),
        dbc.Row([
            dbc.Col(dbc.Card(dbc.CardBody([
                html.H6('Rentabilidad', className='fw-bold', style={'color': COL_PRIMARY}),
                tabla_rent]), className='shadow-sm h-100'), md=6, className='mb-3'),
            dbc.Col(dbc.Card(dbc.CardBody([
                html.H6('Calidad', className='fw-bold', style={'color': COL_PRIMARY}),
                tabla_cal]), className='shadow-sm h-100'), md=6, className='mb-3'),
        ]),
        dbc.Card(dbc.CardBody([
            html.H6('Distribución de calidad por partición', className='fw-bold',
                    style={'color': COL_PRIMARY}),
            html.P("1ª, 2ª calidad y pérdidas (% de producción) de cada cultivo.",
                   className='text-muted small mb-1'),
            dcc.Graph(figure=_calidad_combo_figure(reales),
                      config={'displayModeBar': False}),
        ]), className='shadow-sm mb-3') if reales else None,
        dbc.Card(dbc.CardBody([
            html.H6('Estado del agua compartida', className='fw-bold',
                    style={'color': COL_PRIMARY}),
            estado_agua]), className='shadow-sm mb-3'),
    ]
    if presup is not None:
        secciones.append(dbc.Card(dbc.CardBody([
            html.H6('Presupuesto', className='fw-bold', style={'color': COL_PRIMARY}),
            presup]), className='shadow-sm mb-3'))
    if graf_compartidos:
        secciones.append(dbc.Card(dbc.CardBody([
            html.H6('Oferta hídrica y reservorios', className='fw-bold',
                    style={'color': COL_PRIMARY}),
            dbc.Row(graf_compartidos)]), className='shadow-sm mb-3'))
    if graf_part:
        secciones.append(html.H6('Simulación diaria por partición',
                                 className='fw-bold mt-2', style={'color': COL_PRIMARY}))
        secciones.extend(graf_part)

    return html.Div([s for s in secciones if s is not None])


# ════════════════════════════ APP / LAYOUT ═════════════════════════════════
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.FLATLY],
                title='Reporte Interactivo · Cultivo')

header = html.Div([
    html.Div([
        html.H3('Simulación de Cultivo · Reporte Interactivo',
                className='fw-bold mb-1', style={'color': '#fff'}),
        html.Div([
            html.Span(f"Regante #{int(REGANTE['id'])} "
                      f"{REGANTE.get('nombre', '')}  ·  ", className='small'),
            html.Span(f"{float(REGANTE['hectareas']):.2f} ha  ·  ", className='small'),
            html.Span(f"{PARTICIONES} particiones  ·  ", className='small'),
            html.Span(f"{len(ESCENARIOS)} escenarios", className='small'),
        ], style={'opacity': '0.85', 'color': '#fff'}),
    ], style={'maxWidth': '1220px', 'margin': '0 auto', 'padding': '22px 32px'}),
], style={'background': f'linear-gradient(135deg,#0d2b52,{COL_ACCENT})'})

app.layout = html.Div([
    header,
    html.Div([
        dbc.Tabs([
            dbc.Tab(vista_dashboard(), label='Dashboard', tab_id='tab-dash'),
            dbc.Tab(vista_cultivos(), label='Cultivos', tab_id='tab-cult'),
            dbc.Tab(vista_presupuesto(), label='Presupuesto', tab_id='tab-ppto'),
            dbc.Tab(vista_calidad(), label='Calidad', tab_id='tab-cal'),
            dbc.Tab(vista_corridas(), label='Corridas experimentales', tab_id='tab-corr'),
            dbc.Tab(vista_explorar(), label='Explorar combinación', tab_id='tab-exp'),
        ], className='mb-3'),
    ], style={'maxWidth': '1220px', 'margin': '0 auto', 'padding': '24px 32px 64px'}),
], style={'background': COL_BG, 'minHeight': '100vh'})


@app.callback(
    Output('salida-combo', 'children'),
    Input('btn-simular-combo', 'n_clicks'),
    State('sel-escenario', 'value'),
    State({'type': 'sel-cultivo', 'index': ALL}, 'value'),
    prevent_initial_call=True,
)
def _simular_combo(n, esc, cultivos):
    if not n:
        return dash.no_update
    from modulos.interactivo import simular_combo_detalle
    try:
        res = simular_combo_detalle(CONTEXTO, int(esc), list(cultivos))
    except Exception as e:
        return dbc.Alert(f"Error al simular: {e}", color='danger')
    combo_txt = ' · '.join(_nombre_bonito(c) for c in cultivos)
    encabezado = dbc.Alert([
        html.Strong(f"{_esc_label(esc)}  —  "), combo_txt,
    ], color='light', className='py-2 border')
    return html.Div([encabezado, render_detalle_combo(res)])


@app.callback(
    Output('tabla-corridas', 'data'),
    Output('corridas-hero', 'children'),
    Output('corridas-resumen', 'children'),
    Output('detalle-corrida', 'children', allow_duplicate=True),
    Input('sel-esc-corridas', 'value'),
    prevent_initial_call=True,
)
def _cambiar_esc_corridas(esc):
    esc = int(esc)
    filas = _corridas_filas(esc)
    return filas, _corridas_hero(esc, filas), _corridas_resumen(esc, filas), None


@app.callback(
    Output('detalle-corrida', 'children', allow_duplicate=True),
    Input('tabla-corridas', 'active_cell'),
    State('tabla-corridas', 'derived_viewport_data'),
    prevent_initial_call=True,
)
def _detalle_corrida(active_cell, viewport):
    if not active_cell or not viewport:
        return dash.no_update
    idx = active_cell.get('row')
    if idx is None or idx >= len(viewport):
        return dash.no_update
    row = viewport[idx]
    esc = int(row['esc_val'])
    cultivos = str(row['cultivos_raw']).split('|')
    from modulos.interactivo import simular_combo_detalle
    try:
        res = simular_combo_detalle(CONTEXTO, esc, cultivos)
    except Exception as e:
        return dbc.Alert(f"Error al simular: {e}", color='danger')
    encabezado = dbc.Card(dbc.CardBody([
        html.Div([
            html.H6(f"Detalle de la corrida · {_esc_label(esc)}",
                    className='fw-bold mb-2', style={'color': COL_PRIMARY}),
        ]),
        _chips_particiones(cultivos),
    ]), className='shadow-sm mb-3', style={'borderLeft': f'5px solid {COL_ACCENT}'})
    return html.Div([encabezado, render_detalle_combo(res)])


if __name__ == '__main__':
    print('\n[OK] Reporte interactivo en http://localhost:8051\n')
    app.run(debug=False, port=8051)
