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


app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.FLATLY],
    suppress_callback_exceptions=True,
    title="Simulador — Editar Par\u00e1metros",
)


def _field(label, component):
    return dbc.Col(html.Div([
        dbc.Label(label, className="fw-semibold small mb-1"),
        component,
    ], className="mb-3"))


def _num(id_, val, step=1, min_=None, max_=None, disabled=False):
    kw = {}
    if min_ is not None: kw["min"] = min_
    if max_ is not None: kw["max"] = max_
    return dbc.Input(id=id_, type="number", value=val, step=step, disabled=disabled,
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
    return dbc.Card([
        dbc.CardHeader(html.H6("Modulo 1 - Oferta Hidrica", className="mb-0 fw-bold")),
        dbc.CardBody([
            dbc.Row([
                _field("Acciones de agua", _num("iv-acciones", getattr(iv, "NUMERO_ACCIONES", 4), min_=1)),
                _field("Valor por accion (m3)", _num("iv-valor-accion", getattr(iv, "VALOR_ACCION", 43.2), step=0.1, min_=0)),
            ]),
            dbc.Row([
                _field("Desmarque inicial (%)", _num("iv-desm-ini", round(getattr(iv, "PORCENTAJE_DESMARQUE_INICIAL", 0.15)*100, 1), step=0.5, min_=0, max_=100)),
                _field("Desmarque final (%)", _num("iv-desm-fin", round(getattr(iv, "PORCENTAJE_DESMARQUE_FINAL", 0.15)*100, 1), step=0.5, min_=0, max_=100)),
            ]),
            dbc.Row([
                _field("Frecuencia turno (dias)", _num("iv-frec-turno", getattr(iv, "FRECUENCIA_TURNO", 9), min_=1)),
                _field("Duracion mantenimiento (dias)", _num("iv-dur-mant", getattr(iv, "DURACION_MANTENIMIENTO", 8), min_=1)),
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
        dbc.CardHeader(html.H6("Modulo 2 - Simulacion Cultivo", className="mb-0 fw-bold")),
        dbc.CardBody([
            dbc.Row([
                _field("Fecha inicio siembra", dcc.DatePickerSingle(id="par-fecha-inicio", display_format="DD/MMM/YYYY", date=str(_fecha_ini), style={"fontSize": "13px"})),
                _field("Particiones de terreno", _num("par-particiones", getattr(par, "PARTICIONES", 1), min_=1, max_=10)),
            ]),
            dbc.Row([
                _field("Presupuesto (CLP)", _num("par-presupuesto", getattr(par, "PRESUPUESTO", 2000000), step=50000, min_=0)),
            ]),
            html.Hr(className="my-2"),
            html.P("Propiedades del Suelo (FAO-56)", className="fw-semibold small mb-2"),
            dbc.Row([
                _field("CC (m3/m3)", _num("par-cc", getattr(par, "CC", 0.164), step=0.001, min_=0)),
                _field("PMP (m3/m3)", _num("par-pmp", getattr(par, "PMP", 0.082), step=0.001, min_=0)),
            ]),
            dbc.Row([
                _field("Alpha suelo", _num("par-alpha", getattr(par, "ALPHA_SUELO", 3.2), step=0.1, min_=0)),
            ]),
            html.Hr(className="my-2"),
            html.P("Agua Subterranea", className="fw-semibold small mb-2"),
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

    return dbc.Card([
        dbc.CardHeader(html.H6("Datos del Regante", className="mb-0 fw-bold")),
        dbc.CardBody([
            dbc.Row([
                dbc.Col([
                    dbc.Label("Seleccionar regante", className="fw-semibold small mb-1"),
                    dcc.Dropdown(id="reg-selector", options=opciones, value=first.get("id", 1), clearable=False, style={"fontSize": "13px"}),
                ], md=4),
            ], className="mb-3"),
            dbc.Row([
                _field("Nombre", dbc.Input(id="reg-nombre", value=first.get("nombre", ""), size="sm")),
                _field("Hectareas", _num("reg-hectareas", first.get("hectareas", 0.5), step=0.1, min_=0)),
                _field("Frec. turno (dias)", _num("reg-frec", first.get("frecuencia_dias", 9), min_=1)),
            ]),
            dbc.Row([
                dbc.Col(
                    dbc.Switch(id="reg-tiene-estanque", label="¿Tiene estanque?", value=_tiene_est, className="small mt-1"),
                    md=6, className="mb-2",
                ),
            ]),
            dbc.Row([
                _field("Cap. estanque (m3)", dbc.Input(id="reg-cap-est", type="number", value=float(first.get("capacidad_estanque_m3", 0)), step=10, min=0, disabled=not _tiene_est, className="form-control form-control-sm")),
                _field("Nivel inicial estanque (m3)", dbc.Input(id="reg-nivel-est", type="number", value=float(first.get("nivel_estanque_inicial_m3", 0)), step=5, min=0, disabled=not _tiene_est, className="form-control form-control-sm")),
                dbc.Col(html.Div([
                    dbc.Label("Fracc. cultivada", className="fw-semibold small mb-1"),
                    dbc.InputGroup([
                        dbc.Input(value=first.get("fraccion_cultivada", 0.6), disabled=True, size="sm"),
                        dbc.InputGroupText("(fijo)", className="small"),
                    ]),
                ], className="mb-3")),
            ]),
            dcc.Store(id="store-reg-id", data=int(DF_REG.iloc[0]["id"]) if not DF_REG.empty else 1),
        ]),
    ], className="shadow-sm")


def serve_layout():
    global IV, PAR, DF_REG
    try:
        IV     = _load_mod1()
        PAR    = _load_mod2()
        DF_REG = _load_regantes()
    except Exception as e:
        print(f"[WARN] No se pudieron recargar parámetros: {e}")
    return dbc.Container([
        dbc.Row(dbc.Col(
            html.Div([
                html.H4("Simulador Multiparadigma - Editar Parametros", className="mb-0 fw-bold text-white"),
                html.Small("Edita los valores y pulsa Guardar Todo para actualizar los archivos de configuracion.", className="text-white-50"),
            ], className="py-3 px-4",
               style={"background": "linear-gradient(135deg,#1e3a5f,#2d6a9f)", "borderRadius": "10px"}),
            className="mb-4 mt-3",
        )),
        dbc.Row([
            dbc.Col(_panel_mod1(), md=6, className="mb-3"),
            dbc.Col(_panel_mod2(), md=6, className="mb-3"),
        ]),
        dbc.Row(dbc.Col(_panel_regante(), className="mb-3")),
        dbc.Row([
            dbc.Col(
                dbc.Button("Guardar Todo", id="btn-guardar-todo", color="success", size="lg", className="w-100 fw-bold"),
                md=3,
            ),
            dbc.Col(
                dbc.Button("Simular Todo", id="btn-simular", color="primary", size="lg", className="w-100 fw-bold"),
                md=3,
            ),
        ], justify="center", className="mb-3"),
        dbc.Row(dbc.Col([
            html.Div(id="msg-guardar-todo"),
            html.Div(id="msg-simular", className="mt-2"),
        ], md={"size": 6, "offset": 3}), className="mb-5"),
    ], fluid=True, style={"backgroundColor": "#f4f6fb", "minHeight": "100vh"})


app.layout = serve_layout


@app.callback(
    Output("reg-nombre",         "value"),
    Output("reg-hectareas",      "value"),
    Output("reg-frec",           "value"),
    Output("reg-cap-est",        "value"),
    Output("reg-nivel-est",      "value"),
    Output("reg-tiene-estanque", "value"),
    Output("reg-tiene-sub",      "value"),
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
            tiene, tiene_sub, int(reg_id))


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
    State("iv-valor-accion", "value"),
    State("iv-desm-ini",     "value"),
    State("iv-desm-fin",     "value"),
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
    State("store-reg-id",         "data"),
    prevent_initial_call=True,
)
def guardar_todo(_, acciones, valor_ac, desm_ini, desm_fin, frec_turno, dur_mant, paradas,
                 fecha_ini, particiones, presupuesto, cc, pmp, alpha, stock_sub, dias_sub, dias_est,
                 reg_sel, reg_nombre, reg_hectareas, reg_frec, reg_cap_est, reg_nivel_est,
                 tiene_estanque, tiene_sub, reg_id):
    errores = []
    try:
        _patch_py_file(IV_PATH, {
            "NUMERO_ACCIONES":              int(acciones)        if acciones    is not None else 4,
            "VALOR_ACCION":                 float(valor_ac)      if valor_ac    is not None else 43.2,
            "PORCENTAJE_DESMARQUE_INICIAL": round(float(desm_ini) / 100, 4) if desm_ini is not None else 0.15,
            "PORCENTAJE_DESMARQUE_FINAL":   round(float(desm_fin) / 100, 4) if desm_fin is not None else 0.15,
            "FRECUENCIA_TURNO":             int(frec_turno)      if frec_turno  is not None else 9,
            "DURACION_MANTENIMIENTO":       int(dur_mant)        if dur_mant    is not None else 8,
            "CALENDARIO_PARADAS":           repr([p["dia"] for p in paradas]),
        })
    except Exception as e:
        errores.append(f"initial_values.py: {e}")
    try:
        _patch_py_file(PAR_PATH, {
            "DIA_INICIO_SIMULACION":           int(_date_to_day(fecha_ini) if fecha_ini else 213),
            "PARTICIONES":                     int(particiones) if particiones is not None else 1,
            "PRESUPUESTO":                     int(presupuesto) if presupuesto is not None else 0,
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
        df.to_csv(REG_PATH, index=False)
    except Exception as e:
        errores.append(f"regantes.csv: {e}")

    if errores:
        return dbc.Alert(["Errores: "] + [html.Br()] + [html.Span(f"- {e}") for e in errores], color="danger", className="py-2")
    return dbc.Alert([
        html.Strong("Parametros guardados correctamente."), html.Br(),
        html.Small(f"Archivos: initial_values.py, parametros.py, regantes.csv  ({datetime.now().strftime('%H:%M:%S')})", className="text-muted"),
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
    reporte_partic = str(MOD2_DIR / "outputs" / "ReporteParticiones.html")
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
        "echo  Simulacion completada. Abriendo reporte...",
        "echo ============================================================",
        "echo.",
        # 'start ""' usa la asociacion de Windows => respeta el navegador predeterminado real
        f'if exist "{reporte_partic}" (start "" "{reporte_partic}")',
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
        html.Small("La ventana se cierra al terminar (o pulsa cualquier tecla).", className="text-muted"),
    ], color="info", className="py-2")


if __name__ == "__main__":
    print("\\n[OK] Abriendo en http://localhost:8050\\n")
    app.run(debug=False, port=8050)
