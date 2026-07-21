import re
from datetime import date, datetime
from pathlib import Path

import pandas as pd
import dash
import dash_bootstrap_components as dbc
from dash import dcc, html, Input, Output, State, ctx, ALL

BASE     = Path(__file__).resolve().parent
MOD1_DIR = BASE / "Oferta Hidrica"
MOD2_DIR = BASE / "Simulaci\u00f3n Cultivo"
IV_PATH  = MOD1_DIR / "src" / "initial_values.py"
PAR_PATH = MOD2_DIR / "parametros.py"
REG_PATH = MOD2_DIR / "inputs" / "regantes.csv"
METODO_PATH = MOD2_DIR / "inputs" / "metodo_riego.csv"
PROD_PATH = MOD2_DIR / "inputs" / "productividad_cultivos.csv"
CULT_PATH = MOD2_DIR / "inputs" / "data_cultivos.csv"
CALEND_PATH = MOD2_DIR / "inputs" / "calendario_siembra.csv"

MESES_COLS = ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio',
              'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre']
MESES_LBL = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun',
             'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']


def _fmt(n, dec=2):
    """Formatea número con separador de miles '.' y decimal ','  (estilo CL/ES)."""
    return f"{float(n):,.{dec}f}".replace(",", "\u00b7").replace(".", ",").replace("\u00b7", ".")


def _parse_money(v):
    """Parsea valor monetario formateado '1.234.567' → int (strip separadores)."""
    if v is None:
        return 0
    return int(str(v).replace(".", "").replace(",", "").strip() or 0)


def _money_input(id_, val, step=None, min_=0):
    """Input tipo texto con separador de miles visible dentro del campo."""
    kw = {"min": 0}
    if step:
        kw["step"] = step
    return dbc.Input(
        id=id_, type="text", value=_fmt(val, 0),
        inputMode="numeric", className="form-control form-control-sm",
        **kw,
    )


def _patch_py_file(path, replacements):
    text = path.read_text(encoding="utf-8")
    for key, val in replacements.items():
        text = re.sub(
            rf"^{re.escape(key)}\s*=\s*\[.*?\]",
            f"{key} = {val}",
            text, flags=re.MULTILINE | re.DOTALL,
        )
        text = re.sub(
            rf"^({re.escape(key)}\s*=\s*)(?!\[).*$",
            lambda m, v=val: f"{key} = {v}",
            text, flags=re.MULTILINE,
        )
    path.write_text(text, encoding="utf-8")


def _date_to_day(d):
    return datetime.strptime(d, "%Y-%m-%d").timetuple().tm_yday


def _load_regantes():
    return pd.read_csv(REG_PATH)


def _load_metodo_riego():
    return pd.read_csv(METODO_PATH)


def _load_productividad():
    return pd.read_csv(PROD_PATH)


def _load_calendario():
    return pd.read_csv(CALEND_PATH)


def _load_data_cultivos():
    return pd.read_csv(CULT_PATH)


def _mini_mapa(lat, lon, kml_path, height=280):
    """Genera HTML de un mini-mapa con canal, bifurcaciones y marcador del regante."""
    try:
        import geopandas as gpd
        import folium
        import pyogrio

        kml = str(kml_path)
        layers = [r[0] for r in pyogrio.list_layers(kml)]
        all_lines = []
        for lyr in layers:
            gdf = gpd.read_file(kml, layer=lyr)
            lines = gdf[gdf.geometry.type == "LineString"]
            if not lines.empty:
                all_lines.append(lines)

        m = folium.Map(
            location=[-30.0318, -71.2424], zoom_start=11, tiles=None,
            width="100%", height=height,
        )
        folium.TileLayer(
            tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
            attr="Esri", name="Satelite",
        ).add_to(m)

        if all_lines:
            lineas = pd.concat(all_lines, ignore_index=True)
            lineas_proj = lineas.copy()
            lineas_proj.crs = "EPSG:4326"
            canal_idx = lineas_proj.to_crs(32719).length.idxmax()
            for i, (_, row) in enumerate(lineas.iterrows()):
                color  = "#60a5fa" if i == canal_idx else "#1a3d6e"
                weight = 3          if i == canal_idx else 1.5
                folium.GeoJson(
                    row.geometry.__geo_interface__,
                    style_function=lambda x, c=color, w=weight: {
                        "color": c, "weight": w, "opacity": 0.85
                    },
                ).add_to(m)

        folium.Marker(
            [lat, lon],
            icon=folium.Icon(color="red", icon="home", prefix="fa"),
            popup=f"Predio ({lat:.4f}, {lon:.4f})",
        ).add_to(m)

        return m._repr_html_()
    except Exception as e:
        return (
            f"<div style='padding:12px;font-family:sans-serif;color:#b00'>"
            f"No se pudo generar el mapa: {e}</div>"
        )


def _load_mod1():
    import importlib.util, types
    spec = importlib.util.spec_from_file_location("iv", IV_PATH)
    m = types.ModuleType("iv")
    spec.loader.exec_module(m)
    return m


def _load_mod2():
    import importlib.util, types
    spec = importlib.util.spec_from_file_location("par", PAR_PATH)
    m = types.ModuleType("par")
    spec.loader.exec_module(m)
    return m


try:
    IV     = _load_mod1()
    PAR    = _load_mod2()
    DF_REG = _load_regantes()
except Exception as e:
    IV = PAR = None
    DF_REG = pd.DataFrame()
    print(f"[WARN] No se pudieron cargar par\u00e1metros: {e}")

def _get_paradas_default(iv=None):
    default = [
        {"dia": 152, "label": "01 Jun 2026"},
        {"dia": 174, "label": "23 Jun 2026"},
        {"dia": 196, "label": "15 Jul 2026"},
        {"dia": 218, "label": "06 Ago 2026"},
        {"dia": 240, "label": "28 Ago 2026"},
    ]
    if iv is None:
        return default
    try:
        import datetime as _dt
        _base_year = datetime.strptime(iv.FECHA_INICIO, "%Y-%m-%d").year
        result = []
        for d in iv.CALENDARIO_PARADAS:
            dt = datetime(_base_year, 1, 1) + _dt.timedelta(days=d - 1)
            result.append({"dia": d, "label": dt.strftime("%d %b %Y")})
        return result
    except Exception:
        return default


_CUSTOM_CSS = """
<style>
  :root {
    --primary: #1a3d6e;
    --accent:  #2563a8;
    --ok:      #16a34a;
    --warn:    #f59e0b;
    --bad:     #dc2626;
    --bg:      #eef1f6;
    --border:  #d1d9e4;
  }
  body, .dash-application {
    font-family: 'Segoe UI', system-ui, Arial, sans-serif !important;
    background: var(--bg) !important;
  }
  .card {
    border-radius: 8px !important;
    border: 1px solid #a8b8cc !important;
    box-shadow: 0 2px 6px rgba(26,61,110,.10) !important;
  }
  .card-header {
    background: #e8eef7 !important;
    border-bottom: 2px solid #a8b8cc !important;
    font-weight: 700 !important;
    color: var(--primary) !important;
    font-size: 13px !important;
  }
  .text-primary { color: var(--primary) !important; }
  .text-success { color: var(--ok) !important; }
  .text-dark    { color: var(--primary) !important; }
  .form-control-sm, .form-select-sm {
    border-radius: 5px !important;
    border-color: var(--border) !important;
    font-size: 13px !important;
    font-family: 'Segoe UI', system-ui, Arial !important;
  }
  .form-control-sm:focus, .form-select-sm:focus {
    border-color: var(--accent) !important;
    box-shadow: 0 0 0 3px rgba(37,99,168,.12) !important;
  }
  .input-group-text {
    border-radius: 5px !important;
    border-color: var(--border) !important;
    background: #f8fafc !important;
    font-size: 12px !important;
    color: #6b7280 !important;
    font-family: 'Segoe UI', system-ui, Arial !important;
  }
  .btn-success { background: var(--ok)  !important; border-color: var(--ok)  !important; font-weight: 700 !important; border-radius: 6px !important; }
  .btn-primary { background: var(--accent) !important; border-color: var(--accent) !important; font-weight: 700 !important; border-radius: 6px !important; }
  .btn-outline-primary { border-color: var(--accent) !important; color: var(--accent) !important; border-radius: 6px !important; }
  .alert { border-radius: 6px !important; font-size: 13px !important; }
  .alert-success  { background: #dcfce7 !important; border-color: #86efac !important; color: #14532d !important; }
  .alert-danger   { background: #fee2e2 !important; border-color: #fca5a5 !important; color: #991b1b !important; }
  .alert-info     { background: #dbeafe !important; border-color: #93c5fd !important; color: #1e3a8a !important; }
  .alert-warning  { background: #fef9c3 !important; border-color: #fde047 !important; color: #713f12 !important; }
  .alert-secondary { background: #f8fafc !important; border-color: var(--border) !important; color: #374151 !important; }
  h6.fw-bold { font-size: 13px !important; letter-spacing: -.01em; }
  .fw-semibold.small { font-size: 10px !important; text-transform: uppercase; letter-spacing: .07em; color: #6b7280 !important; }
  .Select-control { border-radius: 5px !important; border-color: var(--border) !important; font-size: 13px !important; }
  .DateInput_input { font-size: 13px !important; font-family: 'Segoe UI', system-ui, Arial !important; }
  .accordion-button { font-size: 13px !important; font-weight: 600 !important; color: var(--primary) !important; }
  .list-group-item { border-color: var(--border) !important; font-size: 13px !important; }
  small.text-muted { font-size: 11px !important; color: #9ca3af !important; }
  hr { border-color: var(--border) !important; opacity: 1 !important; }
  .nav-tabs { border-bottom: 2px solid var(--border) !important; gap: 4px; }
  .nav-tabs .nav-link { color: #6b7280 !important; font-weight: 600 !important; font-size: 13px !important; border: none !important; border-bottom: 2px solid transparent !important; margin-bottom: -2px !important; padding: 10px 18px !important; border-radius: 0 !important; background: transparent !important; }
  .nav-tabs .nav-link:hover { color: var(--accent) !important; border-bottom-color: var(--border2) !important; }
  .nav-tabs .nav-link.active { color: var(--primary) !important; border-bottom: 2px solid var(--primary) !important; font-weight: 700 !important; }
  .tab-content { background: transparent !important; }
  /* Separación de secciones dentro de cards y acordeón */
  .accordion-body { padding: 20px 16px !important; }
  .accordion-item  { border-color: var(--border) !important; margin-bottom: 4px !important; border-radius: 6px !important; overflow: hidden; }
  .accordion-button { padding: 12px 16px !important; font-size: 13px !important; font-weight: 600 !important; color: var(--primary) !important; background: var(--surface2) !important; }
  .accordion-button:not(.collapsed) { background: #e8eef7 !important; color: var(--primary) !important; box-shadow: none !important; }
  .accordion-button::after { filter: none !important; }
  /* Subsecciones dentro del acordeón */
  .mb-2.fw-semibold, p.fw-semibold { font-size: 11px !important; font-weight: 700 !important; text-transform: uppercase !important; letter-spacing: .06em !important; color: var(--text3) !important; margin-top: 18px !important; margin-bottom: 8px !important; padding-bottom: 4px !important; border-bottom: 1px solid var(--border) !important; }
  hr.my-2 { margin-top: 18px !important; margin-bottom: 18px !important; border-color: #a8b8cc !important; border-width: 1px !important; opacity: 1 !important; }
  /* Separación entre campos */
  .card-body { padding: 20px !important; }
  .card-body .row { margin-bottom: 2px; }
  .mb-3 { margin-bottom: 14px !important; }
</style>
"""

app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.FLATLY],
    suppress_callback_exceptions=True,
    title="Simulador — Editar Parámetros",
)
app.index_string = """<!DOCTYPE html>
<html>
<head>
{%metas%}
<title>{%title%}</title>
""" + _CUSTOM_CSS + """
{%favicon%}
{%css%}
</head>
<body>
{%app_entry%}
<footer>{%config%}{%scripts%}{%renderer%}</footer>
</body>
</html>
"""


def _field(label, component):
    return dbc.Col(html.Div([
        dbc.Label(label, className="fw-semibold small mb-1"),
        component,
    ], className="mb-3"))


def _num(id_, val, step: float = 1, min_=None, max_=None, disabled=False):
    kw = {}
    if min_ is not None: kw["min"] = min_
    if max_ is not None: kw["max"] = max_
    # step entero -> fuerza enteros; step decimal -> "any" acepta cualquier decimal
    step_attr = step if isinstance(step, int) else "any"
    return dbc.Input(id=id_, type="number", value=val, step=step_attr, disabled=disabled,
                     className="form-control form-control-sm", **kw)


def _parada_row(dia, label, idx):
    return dbc.ListGroupItem(
        dbc.Row([
            dbc.Col(html.Span(f"\U0001f4cd {label}", className="text-dark"), width=8),
            dbc.Col(html.Span(f"(d\u00eda {dia})", className="text-muted small"), width=2),
            dbc.Col(
                dbc.Button("x", id={"type": "del-parada", "index": idx},
                           color="danger", outline=True, size="sm", className="py-0 px-2"),
                width=2, className="text-end",
            ),
        ], align="center"),
        className="py-2",
    )


def _panel_mod1():
    iv = IV
    _tasa  = 1.0                              # L/s por acción (definición conceptual)
    _horas = getattr(iv, "HORAS_TURNO", 12)
    _m3    = round(_tasa * _horas * 3.6, 2)  # m³/turno por acción
    return dbc.Card([
        dbc.CardHeader(
            html.H6("Módulo 1 — Oferta Hídrica", className="mb-0 fw-bold text-primary")
        ),
        dbc.CardBody([
            html.P("Derechos de agua superficial y ciclo de turnos", className="text-muted small mb-3"),
            dbc.Row([
                _field("Número de acciones",
                    dbc.InputGroup([
                        _num("iv-acciones", getattr(iv, "NUMERO_ACCIONES", 4), min_=1),
                        dbc.InputGroupText("acc", className="small"),
                    ], size="sm")
                ),
                _field("Tasa por acción",
                    dbc.InputGroup([
                        _num("iv-tasa-accion", _tasa, step=0.1, min_=0.1),
                        dbc.InputGroupText("L/s", className="small"),
                    ], size="sm")
                ),
            ]),
            dbc.Row([
                _field("Duración del turno",
                    dbc.InputGroup([
                        _num("iv-horas-turno", _horas, min_=1),
                        dbc.InputGroupText("horas", className="small"),
                    ], size="sm")
                ),
                dbc.Col(html.Div([
                    dbc.Label("Volumen/turno por acción", className="fw-semibold small mb-1"),
                    dbc.InputGroup([
                        dbc.Input(id="iv-m3-display", value=f"{_fmt(_m3)} m³/turno",
                                  disabled=True,
                                  className="form-control form-control-sm text-muted bg-light"),
                    ], size="sm"),
                ], className="mb-3")),
            ]),
            html.Hr(className="my-2"),
            html.P("Horizonte de simulación", className="fw-semibold small mb-2"),
            dbc.Row([
                _field("Fecha de inicio",
                    dcc.DatePickerSingle(
                        id="iv-fecha-inicio",
                        display_format="DD/MMM/YYYY",
                        date=getattr(iv, "FECHA_INICIO", "2026-01-01"),
                        style={"fontSize": "13px"},
                    )
                ),
                _field("Duración de la simulación",
                    dbc.InputGroup([
                        _num("iv-tiempo-total", getattr(iv, "TIEMPO_TOTAL", 400), min_=1),
                        dbc.InputGroupText("días", className="small"),
                    ], size="sm")
                ),
            ]),
            html.Hr(className="my-2"),
            html.P("Desmarque del canal", className="fw-semibold small mb-2"),
            dbc.Row([
                _field("Inicial (temporada actual)",
                    dbc.InputGroup([
                        _num("iv-desm-ini", round(getattr(iv, "PORCENTAJE_DESMARQUE_INICIAL", 0.15)*100, 1), step=0.5, min_=0, max_=100),
                        dbc.InputGroupText("%", className="small"),
                    ], size="sm")
                ),
                _field("Final (próxima temporada)",
                    dbc.InputGroup([
                        _num("iv-desm-fin", round(getattr(iv, "PORCENTAJE_DESMARQUE_FINAL", 0.15)*100, 1), step=0.5, min_=0, max_=100),
                        dbc.InputGroupText("%", className="small"),
                    ], size="sm")
                ),
            ]),
            dbc.Row([
                _field("Salto entre escenarios",
                    dbc.InputGroup([
                        _num("iv-salto-desm", round(getattr(iv, "SALTO_DESMARQUE", 0.025)*100, 1), step=0.5, min_=0, max_=100),
                        dbc.InputGroupText("±%", className="small"),
                    ], size="sm")
                ),
            ]),
            html.Hr(className="my-2"),
            html.P("Ciclo de turno y mantenimiento", className="fw-semibold small mb-2"),
            dbc.Row([
                _field("Frecuencia de turno",
                    dbc.InputGroup([
                        _num("iv-frec-turno", getattr(iv, "FRECUENCIA_TURNO", 9), min_=1),
                        dbc.InputGroupText("días", className="small"),
                    ], size="sm")
                ),
                _field("Duración de mantenimiento",
                    dbc.InputGroup([
                        _num("iv-dur-mant", getattr(iv, "DURACION_MANTENIMIENTO", 8), min_=1),
                        dbc.InputGroupText("días", className="small"),
                    ], size="sm")
                ),
            ]),
            html.Hr(className="my-2"),
            html.P("Calendario de Paradas", className="fw-semibold small mb-2"),
            dbc.Row([
                dbc.Col(dcc.DatePickerSingle(id="parada-fecha-picker", display_format="DD/MMM/YYYY", date=str(date(2026, 6, 1)), style={"fontSize": "13px"}), width=8),
                dbc.Col(dbc.Button("+ Agregar", id="btn-add-parada", color="primary", outline=True, size="sm", className="w-100"), width=4),
            ], className="mb-2"),
            dbc.ListGroup(
                id="lista-paradas",
                children=[_parada_row(p["dia"], p["label"], i) for i, p in enumerate(_get_paradas_default(iv))],
                flush=True, className="small",
            ),
            dcc.Store(id="store-paradas", data=_get_paradas_default(iv)),
        ]),
    ], className="h-100 shadow-sm")


def _panel_mod2():
    par = PAR
    try:
        import datetime as _dt
        _dia = getattr(par, "DIA_INICIO_SIMULACION", 213)
        _fecha_ini = (datetime(2026, 1, 1) + _dt.timedelta(days=_dia - 1)).date()
    except Exception:
        _fecha_ini = date(2026, 8, 1)

    return dbc.Card([
        dbc.CardHeader(
            html.H6("Módulo 2 — Simulación de Cultivo", className="mb-0 fw-bold text-success")
        ),
        dbc.CardBody([
            html.P("Planificación de parcelas y balance hídrico FAO-56", className="text-muted small mb-3"),
            dbc.Row([
                _field("Fecha inicio siembra", dcc.DatePickerSingle(id="par-fecha-inicio", display_format="DD/MMM/YYYY", date=str(_fecha_ini), style={"fontSize": "13px"})),
                _field("Particiones de terreno", dbc.InputGroup([
                    _num("par-particiones", getattr(par, "PARTICIONES", 1), min_=1, max_=10),
                    dbc.InputGroupText("parc.", className="small"),
                ], size="sm")),
            ]),
            dbc.Row([
                _field("Presupuesto", dbc.InputGroup([
                    dbc.InputGroupText("$", className="small"),
                    _money_input("par-presupuesto", getattr(par, "PRESUPUESTO", 2000000)),
                    dbc.InputGroupText("CLP", className="small"),
                ], size="sm")),
            ]),
            html.Hr(className="my-2"),
            html.P("Propiedades del suelo (FAO-56)", className="fw-semibold small mb-2"),
            dbc.Row([
                _field("Capacidad de campo (CC)", dbc.InputGroup([
                    _num("par-cc", getattr(par, "CC", 0.164), step=0.001, min_=0),
                    dbc.InputGroupText("m³/m³", className="small"),
                ], size="sm")),
                _field("Punto marchitez (PMP)", dbc.InputGroup([
                    _num("par-pmp", getattr(par, "PMP", 0.082), step=0.001, min_=0),
                    dbc.InputGroupText("m³/m³", className="small"),
                ], size="sm")),
            ]),
            dbc.Row([
                _field("α retención no lineal", dbc.InputGroup([
                    _num("par-alpha", getattr(par, "ALPHA_SUELO", 3.2), step=0.1, min_=0),
                    dbc.InputGroupText("α", className="small"),
                ], size="sm")),
            ]),
            html.Hr(className="my-2"),
            html.P("Agua subterránea", className="fw-semibold small mb-2"),
            dbc.Row([
                dbc.Col(
                    dbc.Switch(id="reg-tiene-sub", label="¿Tiene derechos de agua subterránea?",
                               value=bool(int(DF_REG.iloc[0].get("tiene_derechos_subterranea", 1))) if not DF_REG.empty else True,
                               className="small mt-1"),
                    className="mb-2",
                ),
            ]),
            dbc.Row([
                _field("Stock inicial (m3)", _num("par-stock-sub", getattr(par, "STOCK_SUBTERRANEO_INICIAL_M3", 200.0), step=10, min_=0,
                       disabled=not bool(int(DF_REG.iloc[0].get("tiene_derechos_subterranea", 1))) if not DF_REG.empty else False)),
                _field("Dias sin riego para usar pozo", _num("par-dias-sub", getattr(par, "DIAS_SIN_RIEGO_PARA_SUBTERRANEA", 3), min_=0,
                       disabled=not bool(int(DF_REG.iloc[0].get("tiene_derechos_subterranea", 1))) if not DF_REG.empty else False)),
            ]),
            dbc.Row([
                _field("Dias sin turno canal para usar estanque", _num("par-dias-est", getattr(par, "DIAS_SIN_RIEGO_PARA_ESTANQUE", 2), min_=0)),
            ]),
        ]),
    ], className="h-100 shadow-sm")


def _panel_regante():
    df = DF_REG
    opciones = [{"label": row["nombre"], "value": row["id"]} for _, row in df.iterrows()] if not df.empty else []
    first = df.iloc[0] if not df.empty else {}
    _tiene_est = float(first.get("capacidad_estanque_m3", 0)) > 0
    _caudal_max = getattr(IV, "CAUDAL_MAXIMO_LS", None) if IV else None
    _efic       = getattr(IV, "EFICIENCIA_POSICION_PCT", None) if IV else None
    _canal_km   = getattr(IV, "CANAL_KM", None) if IV else None
    # Opciones de método de riego
    try:
        df_met = _load_metodo_riego()
        _opciones_riego = [{"label": row["descripcion"], "value": row["metodo"]} for _, row in df_met.iterrows()]
        _factor_map     = dict(zip(df_met["metodo"], df_met["factor"]))
    except Exception:
        _opciones_riego = [{"label": "Goteo (95%)", "value": "goteo"},
                           {"label": "Aspersión (80%)", "value": "aspersion"},
                           {"label": "Tradicional (60%)", "value": "tradicional"}]
        _factor_map = {"goteo": 0.95, "aspersion": 0.80, "tradicional": 0.60}
    _metodo_actual  = str(first.get("metodo_riego", "goteo"))
    _factor_actual  = _factor_map.get(_metodo_actual, 0.95)

    if _caudal_max is not None:
        _badge_color = "success" if _caudal_max >= 30 else "warning" if _caudal_max >= 10 else "danger"
        _caudal_badge = dbc.Alert([
            html.Strong(f"Caudal máximo en predio: {_fmt(_caudal_max)} L/s"),
            html.Span(f"  —  eficiencia {_fmt(_efic, 1)} %  |  canal {_fmt(_canal_km, 1)} km",
                      className="text-muted small ms-2"),
        ], color=_badge_color, className="py-2 mb-0 small")
    else:
        _caudal_badge = dbc.Alert("Guarda los parámetros para calcular el caudal máximo.",
                                   color="secondary", className="py-2 mb-0 small")

    # Mini-mapa del predio
    _lat0 = float(first.get("latitud",  -30.05))
    _lon0 = float(first.get("longitud", -71.25))
    _kml_path = (MOD1_DIR / getattr(IV, "KML_CANAL_PATH", "")) if IV else None
    _map_src = (_mini_mapa(_lat0, _lon0, _kml_path)
                if _kml_path and _kml_path.exists()
                else "<div style='padding:12px;color:#888'>KML no disponible</div>")

    return dbc.Card([
        dbc.CardHeader(
            html.H6("Datos del Regante", className="mb-0 fw-bold text-dark")
        ),
        dbc.CardBody([
            dbc.Row([
                dbc.Col([
                    dbc.Label("Seleccionar regante", className="fw-semibold small mb-1"),
                    dcc.Dropdown(id="reg-selector", options=opciones, value=first.get("id", 1), clearable=False, style={"fontSize": "13px"}),
                ], md=4),
            ], className="mb-3"),
            dbc.Row([
                _field("Nombre", dbc.Input(id="reg-nombre", value=first.get("nombre", ""), size="sm")),
                _field("Hectáreas", dbc.InputGroup([
                    _num("reg-hectareas", first.get("hectareas", 0.5), step=0.1, min_=0),
                    dbc.InputGroupText("ha", className="small"),
                ], size="sm")),
                _field("Frecuencia de turno", dbc.InputGroup([
                    _num("reg-frec", first.get("frecuencia_dias", 9), min_=1),
                    dbc.InputGroupText("días", className="small"),
                ], size="sm")),
            ]),
            html.Hr(className="my-2"),
            html.P("Ubicación del predio (WGS-84)", className="fw-semibold small mb-2"),
            dbc.Row([
                _field("Latitud",  _num("reg-latitud",  float(first.get("latitud",  -30.05)), step=0.0001)),
                _field("Longitud", _num("reg-longitud", float(first.get("longitud", -71.25)), step=0.0001)),
            ]),
            html.Hr(className="my-2"),
            html.P("Tecnificación del riego", className="fw-semibold small mb-2"),
            dbc.Row([
                _field("Tipo de riego",
                    dcc.Dropdown(
                        id="reg-metodo-riego",
                        options=_opciones_riego,
                        value=_metodo_actual,
                        clearable=False,
                        style={"fontSize": "13px"},
                    )
                ),
                dbc.Col(html.Div([
                    dbc.Label("Factor de eficiencia", className="fw-semibold small mb-1"),
                    dbc.Input(id="reg-factor-tec",
                              value=f"{int(_factor_actual*100)} %  (x{_factor_actual})",
                              disabled=True,
                              className="form-control form-control-sm bg-light text-muted"),
                ], className="mb-3")),
            ]),
            _caudal_badge,
            html.Iframe(
                id="mini-mapa-regante",
                srcDoc=_map_src,
                style={"width": "100%", "height": "280px",
                       "border": "none", "borderRadius": "8px",
                       "marginTop": "10px"},
            ),
            html.Hr(className="my-2"),
            html.P("Estanque predial", className="fw-semibold small mb-2 mt-2"),
            dbc.Row([
                dbc.Col(
                    dbc.Switch(id="reg-tiene-estanque", label="¿Tiene estanque?", value=_tiene_est, className="small mt-1"),
                    md=6, className="mb-2",
                ),
            ]),
            dbc.Row([
                _field("Capacidad", dbc.InputGroup([
                    dbc.Input(id="reg-cap-est", type="number", value=float(first.get("capacidad_estanque_m3", 0)), step=10, min=0, disabled=not _tiene_est, className="form-control form-control-sm"),
                    dbc.InputGroupText("m³", className="small"),
                ], size="sm")),
                _field("Nivel inicial", dbc.InputGroup([
                    dbc.Input(id="reg-nivel-est", type="number", value=float(first.get("nivel_estanque_inicial_m3", 0)), step=5, min=0, disabled=not _tiene_est, className="form-control form-control-sm"),
                    dbc.InputGroupText("m³", className="small"),
                ], size="sm")),
            ]),
            dcc.Store(id="store-reg-id", data=int(DF_REG.iloc[0]["id"]) if not DF_REG.empty else 1),
        ]),
    ], className="shadow-sm")


def _cultivo_items(df, cal_df=None, dc_df=None):
    if cal_df is not None:
        cal_idx = cal_df.set_index("nombre")
    else:
        cal_idx = None
    if dc_df is not None:
        dc_idx = dc_df.set_index("nombre")
    else:
        dc_idx = None
    items = []
    for _, row in df.iterrows():
        nombre = str(row['nombre'])
        display = nombre.replace('_', ' ').title()

        def cid(col, n=nombre):
            return {"type": "cult", "col": col, "nombre": n}

        def calid(col, n=nombre):
            return {"type": "cal", "col": col, "nombre": n}

        def pid(col, n=nombre):
            return {"type": "pheno", "col": col, "nombre": n}

        # ── Economía ─────────────────────────────────────────────────────────
        econ = dbc.Row([
            _field("Costo ($/ha)", _money_input(cid('costo'), float(row['costo']))),
            _field("Rendimiento (u/ha)", _money_input(cid('rendimiento'), float(row['rendimiento']))),
            _field("Unidad", dcc.Dropdown(
                id=cid('unidad'),
                options=[{"label": "unidad", "value": "unidad"}, {"label": "kg", "value": "kg"}],
                value=str(row['unidad']), clearable=False, style={"fontSize": "13px"})),
        ])

        # ── Estacionalidad ────────────────────────────────────────────────────
        meses = []
        for col, lbl in zip(MESES_COLS, MESES_LBL):
            if cal_idx is not None and nombre in cal_idx.index:
                siembra_on = bool(int(cal_idx.loc[nombre, col]) == 1)
            else:
                siembra_on = True
            meses.append(dbc.Col(html.Div([
                dbc.Label(lbl, className="small mb-0 text-muted"),
                _money_input(cid(col), float(row[col])),
                dbc.Switch(id=calid(col), value=siembra_on, label="Siembra",
                           className="small mt-1"),
            ]), xs=4, md=2, className="mb-2"))
        estac = html.Div([
            html.P("Ingreso por hectárea por mes (estacionalidad) y meses de siembra permitidos",
                   className="fw-semibold small mb-2 mt-2"),
            dbc.Row(meses),
        ])

        # ── Fenología FAO-56 (data_cultivos.csv) ─────────────────────────────
        dc = dc_idx.loc[nombre] if dc_idx is not None and nombre in dc_idx.index else {}

        def _pv(col, default=0):
            return float(dc[col]) if col in dc else default

        def _pheno_num(col, default, step=1, min_=0):
            return _num(pid(col), _pv(col, default), step=step, min_=min_)

        fases = dbc.Row([
            _field("L ini (días)", _pheno_num('L_ini', 20)),
            _field("L des (días)", _pheno_num('L_des', 25)),
            _field("L med (días)", _pheno_num('L_med', 20)),
            _field("L fin (días)", _pheno_num('L_fin', 15)),
        ])
        kc = dbc.Row([
            _field("Kc ini",  _pheno_num('Kc_ini',  0.7,  step=0.01)),
            _field("Kc med",  _pheno_num('Kc_med',  0.9,  step=0.01)),
            _field("Kc fin",  _pheno_num('Kc_fin',  0.85, step=0.01)),
        ])
        kcb = dbc.Row([
            _field("Kcb ini", _pheno_num('Kcb_ini', 0.15, step=0.01)),
            _field("Kcb med", _pheno_num('Kcb_med', 0.95, step=0.01)),
            _field("Kcb fin", _pheno_num('Kcb_fin', 0.85, step=0.01)),
        ])
        suelo = dbc.Row([
            _field("h (m)",   _pheno_num('h',   0.3,  step=0.01)),
            _field("p",       _pheno_num('p',   0.4,  step=0.01)),
            _field("Ze (m)",  _pheno_num('Ze',  0.15, step=0.01)),
            _field("few",     _pheno_num('few', 0.5,  step=0.01)),
        ])
        fao = html.Div([
            html.Hr(className="my-2"),
            html.P("Parámetros FAO-56 (fenología y coeficientes)", className="fw-semibold small mb-2"),
            html.P("Duración de fases", className="text-muted small mb-1"),
            fases,
            html.P("Coeficiente de cultivo Kc", className="text-muted small mb-1 mt-1"),
            kc,
            html.P("Coeficiente basal Kcb", className="text-muted small mb-1 mt-1"),
            kcb,
            html.P("Parámetros de suelo y planta", className="text-muted small mb-1 mt-1"),
            suelo,
        ])

        items.append(dbc.AccordionItem(
            [econ, html.Hr(className="my-2"), estac, fao], title=display))
    return items


def _panel_cultivos():
    try:
        df     = _load_productividad()
        cal_df = _load_calendario()
        dc_df  = _load_data_cultivos()
        cuerpo = _cultivo_items(df, cal_df, dc_df)
    except Exception as e:
        cuerpo = [dbc.Alert(f"No se pudo cargar datos de cultivos: {e}", color="warning")]
    return dbc.Card([
        dbc.CardHeader(html.H6("Configuracion de Cultivos", className="mb-0 fw-semibold text-primary")),
        dbc.CardBody([
            html.Small(
                "Haz clic en un cultivo para editar sus propiedades. "
                "Los cambios se guardan al pulsar Guardar Todo.",
                className="text-muted d-block mb-2",
            ),
            dbc.Accordion(id="acordeon-cultivos", children=cuerpo,
                          start_collapsed=True, flush=True),
            html.Hr(className="my-3"),
            dbc.Row([
                dbc.Col(dbc.Input(id="input-nuevo-cultivo",
                                  placeholder="Nombre del nuevo cultivo", size="sm"), md=8),
                dbc.Col(dbc.Button("+ Agregar cultivo", id="btn-add-cultivo",
                                   color="primary", outline=True, size="sm",
                                   className="w-100"), md=4),
            ], className="g-2"),
            # btn-guardar-cultivos oculto (necesario para el callback de agregar)
            dbc.Button(id="btn-guardar-cultivos", style={"display": "none"}),
            html.Div(id="msg-cultivos", className="mt-2"),
        ]),
    ], className="shadow-sm mb-3")


def serve_layout():
    global IV, PAR, DF_REG
    try:
        IV     = _load_mod1()
        PAR    = _load_mod2()
        DF_REG = _load_regantes()
    except Exception as e:
        print(f"[WARN] No se pudieron recargar parámetros: {e}")
    return dbc.Container([

        # ── Header ──────────────────────────────────────────────────────
        dbc.Row(dbc.Col(
            html.Div([
                dbc.Row([
                    dbc.Col([
                        html.H4("Simulador Multiparadigma", className="mb-0 fw-bold text-white"),
                        html.Small("Gestión de agua de riego — Valle de Elqui", className="text-white-50"),
                    ], xs=12, md=8),
                    dbc.Col([
                        html.Small("Edita los valores y pulsa Guardar Todo.", className="text-white-50 d-block"),
                        html.Small("Luego Simular Todo para ejecutar ambos módulos.", className="text-white-50 d-block"),
                    ], xs=12, md=4, className="text-md-end mt-2 mt-md-0"),
                ], align="center"),
            ], className="py-3 px-4",
               style={"background": "linear-gradient(135deg,#1a3d6e,#2563a8)", "borderRadius": "10px"}),
            className="mb-3 mt-3",
        )),

        # ── Tabs ─────────────────────────────────────────────────────────
        dbc.Tabs([

            # Tab 1 — Módulo 1: Canal
            dbc.Tab(
                dbc.Row([dbc.Col(_panel_mod1(), md=8, className="mb-3")],
                        justify="center", className="mt-3"),
                label="Módulo 1 — Canal",
                tab_id="tab-mod1",
                label_style={"fontWeight": "600", "fontSize": "13px"},
            ),

            # Tab 2 — Módulo 2 + Regante
            dbc.Tab(
                dbc.Row([
                    dbc.Col(_panel_mod2(),   md=5, className="mb-3"),
                    dbc.Col(_panel_regante(), md=7, className="mb-3"),
                ], className="mt-3"),
                label="Módulo 2 — Regante",
                tab_id="tab-mod2",
                label_style={"fontWeight": "600", "fontSize": "13px"},
            ),

            # Tab 3 — Cultivos
            dbc.Tab(
                dbc.Row([dbc.Col(_panel_cultivos(), className="mb-3")],
                        className="mt-3"),
                label="Cultivos",
                tab_id="tab-cultivos",
                label_style={"fontWeight": "600", "fontSize": "13px"},
            ),

        ], id="main-tabs", active_tab="tab-mod1",
           className="mb-3 border-bottom-0"),

        # ── Botones de acción ────────────────────────────────────────────
        dbc.Row([
            dbc.Col(
                dbc.Button("Guardar Todo", id="btn-guardar-todo", color="success",
                           size="lg", className="w-100 fw-bold"),
                md=3,
            ),
            dbc.Col(
                dbc.Button("Simular Todo", id="btn-simular", color="primary",
                           size="lg", className="w-100 fw-bold"),
                md=3,
            ),
        ], justify="center", className="mb-3"),

        dbc.Row(dbc.Col([
            html.Div(id="msg-guardar-todo"),
            html.Div(id="msg-simular", className="mt-2"),
        ], md={"size": 6, "offset": 3}), className="mb-5"),

    ], fluid=True, style={"backgroundColor": "#eef1f6", "minHeight": "100vh"})


app.layout = serve_layout


@app.callback(
    Output("reg-nombre",         "value"),
    Output("reg-hectareas",      "value"),
    Output("reg-frec",           "value"),
    Output("reg-cap-est",        "value"),
    Output("reg-nivel-est",      "value"),
    Output("reg-tiene-estanque", "value"),
    Output("reg-tiene-sub",      "value"),
    Output("reg-latitud",        "value"),
    Output("reg-longitud",       "value"),
    Output("reg-metodo-riego",   "value"),
    Output("store-reg-id",       "data"),
    Input("reg-selector",  "value"),
    prevent_initial_call=True,
)
def cargar_regante(reg_id):
    df  = _load_regantes()
    row = df[df["id"] == reg_id].iloc[0]
    tiene = float(row["capacidad_estanque_m3"]) > 0
    tiene_sub = bool(int(row.get("tiene_derechos_subterranea", 1)))
    return (row["nombre"], row["hectareas"], row["frecuencia_dias"],
            row["capacidad_estanque_m3"], row["nivel_estanque_inicial_m3"],
            tiene, tiene_sub,
            float(row.get("latitud",  -30.05)),
            float(row.get("longitud", -71.25)),
            str(row.get("metodo_riego", "goteo")),
            int(reg_id))


@app.callback(
    Output("reg-cap-est",   "disabled"),
    Output("reg-nivel-est", "disabled"),
    Output("reg-cap-est",   "value", allow_duplicate=True),
    Output("reg-nivel-est", "value", allow_duplicate=True),
    Input("reg-tiene-estanque", "value"),
    State("reg-cap-est",   "value"),
    State("reg-nivel-est", "value"),
    prevent_initial_call=True,
)
def toggle_estanque(tiene, cap_val, nivel_val):
    if tiene:
        return False, False, cap_val, nivel_val
    return True, True, 0, 0


@app.callback(
    Output("iv-m3-display", "value"),
    Input("iv-tasa-accion",  "value"),
    Input("iv-horas-turno",  "value"),
    prevent_initial_call=False,
)
def actualizar_m3_display(tasa, horas):
    t = float(tasa  or 1.0)
    h = float(horas or 12)
    m3 = round(t * h * 3.6, 2)
    return f"{_fmt(m3)} m³/turno"


@app.callback(
    Output("mini-mapa-regante", "srcDoc"),
    Input("reg-latitud",  "value"),
    Input("reg-longitud", "value"),
    prevent_initial_call=True,
)
def actualizar_mini_mapa(lat, lon):
    if lat is None or lon is None:
        return dash.no_update
    _kml = (MOD1_DIR / getattr(IV, "KML_CANAL_PATH", "")) if IV else None
    if _kml and _kml.exists():
        return _mini_mapa(float(lat), float(lon), _kml)
    return "<div style='padding:12px;color:#888'>KML no disponible</div>"


@app.callback(
    Output("reg-factor-tec", "value"),
    Input("reg-metodo-riego", "value"),
    prevent_initial_call=True,
)
def actualizar_factor_tec(metodo):
    try:
        df_met = _load_metodo_riego()
        fila = df_met[df_met["metodo"] == metodo]
        if not fila.empty:
            f = float(fila.iloc[0]["factor"])
            return f"{int(f*100)} %  (x{f})"
    except Exception:
        pass
    factores = {"goteo": 0.95, "aspersion": 0.80, "tradicional": 0.60}
    f = factores.get(metodo, 1.0)
    return f"{int(f*100)} %  (x{f})"


@app.callback(
    Output("par-stock-sub", "disabled"),
    Output("par-dias-sub",  "disabled"),
    Output("par-stock-sub", "value", allow_duplicate=True),
    Input("reg-tiene-sub", "value"),
    State("par-stock-sub", "value"),
    prevent_initial_call=True,
)
def toggle_sub(tiene_sub, stock_val):
    if tiene_sub:
        return False, False, stock_val
    return True, True, 0


@app.callback(
    Output("store-paradas", "data"),
    Output("lista-paradas", "children"),
    Input("btn-add-parada",                     "n_clicks"),
    Input({"type": "del-parada", "index": ALL}, "n_clicks"),
    State("parada-fecha-picker", "date"),
    State("store-paradas",       "data"),
    prevent_initial_call=True,
)
def gestionar_paradas(n_add, n_del, fecha_sel, paradas):
    triggered = ctx.triggered_id
    if triggered == "btn-add-parada" and fecha_sel:
        dia   = _date_to_day(fecha_sel)
        label = datetime.strptime(fecha_sel, "%Y-%m-%d").strftime("%d %b %Y")
        if not any(p["dia"] == dia for p in paradas):
            paradas = sorted(paradas + [{"dia": dia, "label": label}], key=lambda x: x["dia"])
    elif isinstance(triggered, dict) and triggered.get("type") == "del-parada":
        paradas = [p for i, p in enumerate(paradas) if i != triggered["index"]]
    return paradas, [_parada_row(p["dia"], p["label"], i) for i, p in enumerate(paradas)]


@app.callback(
    Output("msg-guardar-todo", "children"),
    Input("btn-guardar-todo",  "n_clicks"),
    State("iv-acciones",     "value"),
    State("iv-tasa-accion",  "value"),
    State("iv-horas-turno",  "value"),
    State("iv-fecha-inicio", "date"),
    State("iv-tiempo-total", "value"),
    State("iv-desm-ini",     "value"),
    State("iv-desm-fin",     "value"),
    State("iv-salto-desm",   "value"),
    State("iv-frec-turno",   "value"),
    State("iv-dur-mant",     "value"),
    State("store-paradas",   "data"),
    State("par-fecha-inicio","date"),
    State("par-particiones", "value"),
    State("par-presupuesto", "value"),
    State("par-cc",          "value"),
    State("par-pmp",         "value"),
    State("par-alpha",       "value"),
    State("par-stock-sub",   "value"),
    State("par-dias-sub",    "value"),
    State("par-dias-est",    "value"),
    State("reg-selector",   "value"),
    State("reg-nombre",     "value"),
    State("reg-hectareas",  "value"),
    State("reg-frec",       "value"),
    State("reg-cap-est",         "value"),
    State("reg-nivel-est",        "value"),
    State("reg-tiene-estanque",   "value"),
    State("reg-tiene-sub",        "value"),
    State("reg-latitud",          "value"),
    State("reg-longitud",         "value"),
    State("reg-metodo-riego",     "value"),
    State("store-reg-id",         "data"),
    State({"type": "cult",  "col": ALL, "nombre": ALL}, "value"),
    State({"type": "cult",  "col": ALL, "nombre": ALL}, "id"),
    State({"type": "cal",   "col": ALL, "nombre": ALL}, "value"),
    State({"type": "cal",   "col": ALL, "nombre": ALL}, "id"),
    State({"type": "pheno", "col": ALL, "nombre": ALL}, "value"),
    State({"type": "pheno", "col": ALL, "nombre": ALL}, "id"),
    prevent_initial_call=True,
)
def guardar_todo(_, acciones, tasa_accion, horas_turno, fecha_inicio_iv, tiempo_total, desm_ini, desm_fin, salto_desm, frec_turno, dur_mant, paradas,
                 fecha_ini, particiones, presupuesto, cc, pmp, alpha, stock_sub, dias_sub, dias_est,
                 reg_sel, reg_nombre, reg_hectareas, reg_frec, reg_cap_est, reg_nivel_est,
                 tiene_estanque, tiene_sub, reg_lat, reg_lon, reg_metodo,
                 reg_id, cult_vals, cult_ids, cal_vals, cal_ids, pheno_vals, pheno_ids):
    errores = []
    # Cargar mapa de factores de tecnificación
    try:
        _df_met = _load_metodo_riego()
        _factor_map = dict(zip(_df_met["metodo"], _df_met["factor"].astype(float)))
    except Exception:
        _factor_map = {"goteo": 0.95, "aspersion": 0.80, "tradicional": 0.60}
    try:
        _tasa = float(tasa_accion) if tasa_accion is not None else 1.0
        _h    = int(horas_turno)   if horas_turno  is not None else 12
        _patch_py_file(IV_PATH, {
            "NUMERO_ACCIONES":              int(acciones)        if acciones    is not None else 4,
            "HORAS_TURNO":                  _h,
            "VALOR_ACCION":                 round(_tasa * _h * 3.6, 4),
            "FECHA_INICIO":                 f'"{fecha_inicio_iv}"' if fecha_inicio_iv else '"2026-01-01"',
            "TIEMPO_TOTAL":                 int(tiempo_total) if tiempo_total is not None else 400,
            "PORCENTAJE_DESMARQUE_INICIAL": round(float(desm_ini) / 100, 4) if desm_ini is not None else 0.15,
            "PORCENTAJE_DESMARQUE_FINAL":   round(float(desm_fin) / 100, 4) if desm_fin is not None else 0.15,
            "SALTO_DESMARQUE":              round(float(salto_desm) / 100, 4) if salto_desm is not None else 0.025,
            "FRECUENCIA_TURNO":             int(frec_turno)      if frec_turno  is not None else 9,
            "DURACION_MANTENIMIENTO":       int(dur_mant)        if dur_mant    is not None else 8,
            "CALENDARIO_PARADAS":           repr([p["dia"] for p in paradas]),
            "REGANTE_LATITUD":              float(reg_lat)       if reg_lat     is not None else -30.05,
            "REGANTE_LONGITUD":             float(reg_lon)       if reg_lon     is not None else -71.25,
            "METODO_RIEGO":                 f'"{reg_metodo}"'    if reg_metodo  else '"goteo"',
            "FACTOR_TECNIFICACION":         _factor_map.get(reg_metodo, 0.95) if reg_metodo else 0.95,
        })
    except Exception as e:
        errores.append(f"initial_values.py: {e}")
    try:
        _patch_py_file(PAR_PATH, {
            "DIA_INICIO_SIMULACION":           int(_date_to_day(fecha_ini) if fecha_ini else 213),
            "PARTICIONES":                     int(particiones) if particiones is not None else 1,
            "PRESUPUESTO":                     _parse_money(presupuesto),
            "CC":                              float(cc) if cc is not None else 0.164,
            "PMP":                             float(pmp) if pmp is not None else 0.082,
            "ALPHA_SUELO":                     float(alpha) if alpha is not None else 3.2,
            # Si no tiene derechos subterráneos, forzar stock=0 y umbral=9999 (efectivamente bloqueado)
            "STOCK_SUBTERRANEO_INICIAL_M3":    float(stock_sub) if (tiene_sub and stock_sub is not None) else 0.0,
            "DIAS_SIN_RIEGO_PARA_SUBTERRANEA": int(dias_sub) if (tiene_sub and dias_sub is not None) else 9999,
            "DIAS_SIN_RIEGO_PARA_ESTANQUE":    int(dias_est) if dias_est is not None else 2,
            "REGANTE_ID":                      int(reg_id) if reg_id is not None else 1,
        })
    except Exception as e:
        errores.append(f"parametros.py: {e}")
    try:
        df = _load_regantes()
        idx = df[df["id"] == reg_sel].index[0]
        df.loc[idx, "nombre"]                    = reg_nombre
        df.loc[idx, "hectareas"]                 = float(reg_hectareas)
        df.loc[idx, "frecuencia_dias"]           = int(reg_frec)
        df.loc[idx, "capacidad_estanque_m3"]     = float(reg_cap_est) if tiene_estanque and reg_cap_est is not None else 0.0
        df.loc[idx, "nivel_estanque_inicial_m3"] = float(reg_nivel_est) if tiene_estanque and reg_nivel_est is not None else 0.0
        df.loc[idx, "tiene_derechos_subterranea"] = int(bool(tiene_sub))
        df.loc[idx, "latitud"]  = float(reg_lat)  if reg_lat  is not None else -30.05
        df.loc[idx, "longitud"] = float(reg_lon)  if reg_lon  is not None else -71.25
        df.loc[idx, "metodo_riego"] = str(reg_metodo) if reg_metodo else "goteo"
        df.to_csv(REG_PATH, index=False)
    except Exception as e:
        errores.append(f"regantes.csv: {e}")
    # Cultivos (productividad + calendario + fenologia)
    try:
        PHENO_INT = {"L_ini", "L_des", "L_med", "L_fin"}
        df_cult = _load_productividad().set_index("nombre")
        for val, id_ in zip(cult_vals, cult_ids):
            col, nombre = id_["col"], id_["nombre"]
            if col == "unidad":
                df_cult.loc[nombre, col] = str(val) if val else "unidad"
            else:
                df_cult.loc[nombre, col] = _parse_money(val)
        df_cult.reset_index().to_csv(PROD_PATH, index=False)
        cal = _load_calendario().set_index("nombre")
        for val, id_ in zip(cal_vals, cal_ids):
            cal.loc[id_["nombre"], id_["col"]] = 1 if val else 0
        cal.reset_index().to_csv(CALEND_PATH, index=False)
        dc = _load_data_cultivos().set_index("nombre")
        for val, id_ in zip(pheno_vals, pheno_ids):
            col, nombre = id_["col"], id_["nombre"]
            if val is not None:
                dc.loc[nombre, col] = int(round(float(val))) if col in PHENO_INT else round(float(val), 4)
        dc.reset_index().to_csv(CULT_PATH, index=False)
    except Exception as e:
        errores.append(f"cultivos: {e}")

    if errores:
        return dbc.Alert(["Errores: "] + [html.Br()] + [html.Span(f"- {e}") for e in errores], color="danger", className="py-2")
    return dbc.Alert([
        html.Strong("Parametros guardados correctamente."), html.Br(),
        html.Small(f"Archivos: initial_values.py, parametros.py, regantes.csv, cultivos  ({datetime.now().strftime('%H:%M:%S')})", className="text-muted"),
    ], color="success", className="py-2")


@app.callback(
    Output("msg-simular", "children"),
    Input("btn-simular", "n_clicks"),
    prevent_initial_call=True,
)
def simular_todo(_):
    import sys
    python = sys.executable
    mod1_dir = str(MOD1_DIR)
    mod2_dir = str(MOD2_DIR)
    animacion_py   = str(MOD1_DIR / "Animacion" / "backend" / "app.py")
    reporte_py     = str(MOD2_DIR / "reporte_interactivo.py")
    bat_lines = [
        "@echo off",
        "chcp 1252 > nul",
        "title Simulacion - Capstone",
        "echo.",
        "echo ============================================================",
        "echo  MODULO 1 - Oferta Hidrica",
        "echo ============================================================",
        "echo.",
        f'cd /d "{mod1_dir}"',
        # NO_ANIMATION=1 evita el prompt input() y la doble ejecucion por pipe
        "set NO_ANIMATION=1",
        f'"{python}" modelo_simulacion_oferta_hidrica.py',
        "echo.",
        # Lanza animacion en ventana separada; el backend abre el navegador automaticamente
        f'start "Animacion Oferta Hidrica" "{python}" "{animacion_py}"',
        "echo [OK] Servidor de animacion iniciado en http://localhost:5000",
        "echo.",
        "echo ============================================================",
        "echo  MODULO 2 - Simulacion Cultivo",
        "echo ============================================================",
        "echo.",
        f'cd /d "{mod2_dir}"',
        f'"{python}" simulacion_cultivo.py',
        "echo.",
        "echo ============================================================",
        "echo  Simulacion completada. Abriendo reporte interactivo...",
        "echo ============================================================",
        "echo.",
        # PROTOCOLO DE LIMPIEZA: mata cualquier reporte viejo en el puerto 8051
        # para que la nueva instancia lea el cache recien generado (particiones actualizadas).
        "echo Limpiando servidor anterior del reporte (puerto 8051)...",
        'powershell -NoProfile -Command "Get-NetTCPConnection -LocalPort 8051 -State Listen -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique | ForEach-Object { Stop-Process -Id $_ -Force -ErrorAction SilentlyContinue }"',
        # Espera breve para que el sistema libere el puerto antes de relanzar
        "timeout /t 2 /nobreak > nul",
        "echo Iniciando servidor en http://localhost:8051 ...",
        # Abre el navegador y levanta el servidor del reporte interactivo
        'start "" "http://localhost:8051"',
        f'"{python}" "{reporte_py}"',
        "pause",
    ]
    bat_path = BASE / "_simular.bat"
    bat_path.write_text("\r\n".join(bat_lines), encoding="cp1252")
    import subprocess
    subprocess.Popen(
        f'start "Simulacion Capstone" cmd /k "{bat_path}"',
        shell=True,
    )
    return dbc.Alert([
        html.Strong("Simulacion iniciada en nueva ventana CMD."),
        html.Br(),
        html.Small("Al terminar se abrira el reporte interactivo en http://localhost:8051.", className="text-muted"),
    ], color="info", className="py-2")


@app.callback(
    Output("msg-cultivos", "children"),
    Input("btn-guardar-cultivos", "n_clicks"),
    State({"type": "cult",  "col": ALL, "nombre": ALL}, "value"),
    State({"type": "cult",  "col": ALL, "nombre": ALL}, "id"),
    State({"type": "cal",   "col": ALL, "nombre": ALL}, "value"),
    State({"type": "cal",   "col": ALL, "nombre": ALL}, "id"),
    State({"type": "pheno", "col": ALL, "nombre": ALL}, "value"),
    State({"type": "pheno", "col": ALL, "nombre": ALL}, "id"),
    prevent_initial_call=True,
)
def guardar_cultivos(_, values, ids, cal_values, cal_ids, pheno_values, pheno_ids):
    PHENO_INT = {"L_ini", "L_des", "L_med", "L_fin"}
    try:
        df = _load_productividad().set_index("nombre")
        for val, id_ in zip(values, ids):
            col, nombre = id_["col"], id_["nombre"]
            if col == "unidad":
                df.loc[nombre, col] = str(val) if val else "unidad"
            else:
                df.loc[nombre, col] = _parse_money(val)
        df.reset_index().to_csv(PROD_PATH, index=False)
        # Calendario de siembra
        cal = _load_calendario().set_index("nombre")
        for val, id_ in zip(cal_values, cal_ids):
            col, nombre = id_["col"], id_["nombre"]
            cal.loc[nombre, col] = 1 if val else 0
        cal.reset_index().to_csv(CALEND_PATH, index=False)
        # Parámetros fenológicos FAO-56
        dc = _load_data_cultivos().set_index("nombre")
        for val, id_ in zip(pheno_values, pheno_ids):
            col, nombre = id_["col"], id_["nombre"]
            if val is None:
                continue
            dc.loc[nombre, col] = int(round(float(val))) if col in PHENO_INT else round(float(val), 4)
        dc.reset_index().to_csv(CULT_PATH, index=False)
        return dbc.Alert([
            html.Strong("Cultivos guardados correctamente."), html.Br(),
            html.Small(f"Archivos: productividad_cultivos.csv, calendario_siembra.csv, data_cultivos.csv  ({datetime.now().strftime('%H:%M:%S')})",
                       className="text-muted"),
        ], color="success", className="py-2")
    except Exception as e:
        return dbc.Alert(f"Error al guardar: {e}", color="danger", className="py-2")


@app.callback(
    Output("acordeon-cultivos", "children"),
    Output("msg-cultivos", "children", allow_duplicate=True),
    Output("input-nuevo-cultivo", "value"),
    Input("btn-add-cultivo", "n_clicks"),
    State("input-nuevo-cultivo", "value"),
    prevent_initial_call=True,
)
def agregar_cultivo(_, nombre_nuevo):
    if not nombre_nuevo or not str(nombre_nuevo).strip():
        return dash.no_update, dbc.Alert("Ingresa un nombre para el nuevo cultivo.",
                                         color="warning", className="py-2"), dash.no_update
    nombre = str(nombre_nuevo).strip().lower().replace(" ", "_")
    df = _load_productividad()
    if nombre in df["nombre"].astype(str).values:
        return dash.no_update, dbc.Alert(f"El cultivo '{nombre}' ya existe.",
                                         color="warning", className="py-2"), dash.no_update
    # Nueva fila economica (valores en 0, unidad por defecto)
    fila: dict = {c: 0 for c in MESES_COLS}
    fila["nombre"] = nombre
    fila["costo"] = 0
    fila["rendimiento"] = 0
    fila["unidad"] = "unidad"
    df = pd.concat([df, pd.DataFrame([fila])], ignore_index=True)
    df.to_csv(PROD_PATH, index=False)
    # Fenologia por defecto en data_cultivos.csv para que el cultivo sea simulable
    try:
        dfc = pd.read_csv(CULT_PATH)
        if nombre not in dfc["nombre"].astype(str).values:
            pheno = {"nombre": nombre, "L_ini": 20, "L_des": 25, "L_med": 20, "L_fin": 15,
                     "Kc_ini": 0.7, "Kc_med": 0.9, "Kc_fin": 0.85,
                     "Kcb_ini": 0.15, "Kcb_med": 0.95, "Kcb_fin": 0.85,
                     "h": 0.3, "p": 0.4, "Ze": 0.15, "few": 0.5}
            dfc = pd.concat([dfc, pd.DataFrame([{c: pheno.get(c, 0) for c in dfc.columns}])],
                            ignore_index=True)
            dfc.to_csv(CULT_PATH, index=False)
    except Exception:
        pass
    # Calendario de siembra por defecto (todos los meses permitidos = 1)
    try:
        dcal = _load_calendario()
        if nombre not in dcal["nombre"].astype(str).values:
            fila_cal: dict = {c: 1 for c in MESES_COLS}
            fila_cal["nombre"] = nombre
            dcal = pd.concat([dcal, pd.DataFrame([{c: fila_cal.get(c, 1) for c in dcal.columns}])],
                             ignore_index=True)
            dcal.to_csv(CALEND_PATH, index=False)
    except Exception:
        pass
    cal_df = _load_calendario()
    dc_df  = _load_data_cultivos()
    return (_cultivo_items(df, cal_df, dc_df),
            dbc.Alert(f"Cultivo '{nombre}' agregado. Edita sus valores y pulsa Guardar cambios.",
                      color="info", className="py-2"),
            "")


if __name__ == "__main__":
    print("\\n[OK] Abriendo en http://localhost:8050\\n")
    app.run(debug=False, port=8050)
