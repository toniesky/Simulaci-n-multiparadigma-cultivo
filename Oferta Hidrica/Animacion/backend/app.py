"""
Backend Flask para animación de simulación
Lee CalendarioOferta.csv y sirve los datos para la animación interactiva
Soporta múltiples escenarios de incertidumbre
"""

from flask import Flask, jsonify, send_from_directory, request
from flask_cors import CORS
import pandas as pd
import os
import webbrowser
from pathlib import Path
import sys
import importlib

app = Flask(__name__)
CORS(app)

# Agregar headers anti-caché a TODAS las respuestas
@app.after_request
def add_no_cache_headers(response):
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

# Agregar ruta al módulo src para importar initial_values
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

# Rutas
BASE_DIR = Path(__file__).parent.parent.parent
DATA_PATH = BASE_DIR / 'data' / 'outputs' / 'CalendarioOferta.csv'
INDICADORES_PATH = BASE_DIR / 'data' / 'outputs' / 'Indicadores_Disponibilidad.csv'
FRONTEND_DIR = BASE_DIR / 'Animacion' / 'frontend'

# Cargar datos
def cargar_datos():
    """Carga datos del CSV de ofertas (incluye todos los escenarios)."""
    try:
        df = pd.read_csv(DATA_PATH)
        if 'Escenario' not in df.columns:
            df['Escenario'] = 0
        return df
    except FileNotFoundError:
        return None

def cargar_indicadores():
    """Carga indicadores de disponibilidad"""
    try:
        df = pd.read_csv(INDICADORES_PATH)
        return df
    except FileNotFoundError:
        return None

def obtener_escenarios():
    """Obtiene lista de escenarios disponibles"""
    df = cargar_datos()
    if df is None or 'Escenario' not in df.columns:
        return [0]  # Si no hay columna Escenario, retorna escenario por defecto
    return sorted(df['Escenario'].unique().tolist())

@app.route('/')
def index():
    """Sirve el archivo HTML principal"""
    return send_from_directory(FRONTEND_DIR, 'index.html')

@app.route('/api/escenarios')
def get_escenarios():
    """API que retorna los escenarios disponibles"""
    escenarios = obtener_escenarios()
    return jsonify({'escenarios': escenarios})

@app.route('/api/datos')
def get_datos():
    """API que retorna los datos de simulación, filtrados por escenario si se especifica"""
    df = cargar_datos()
    if df is None:
        return jsonify({'error': 'No hay datos disponibles'}), 404
    
    # Obtener escenario del query parameter
    escenario_param = request.args.get('escenario', default=None, type=int)
    
    # Si se especifica escenario y existe la columna, filtrar
    if escenario_param is not None and 'Escenario' in df.columns:
        df = df[df['Escenario'] == escenario_param]
    
    if df.empty:
        return jsonify({'error': f'No hay datos para el escenario {escenario_param}'}), 404
    
    # Compatibilidad con CSVs antiguos: si no existe OfertaBruta, crearla
    if 'OfertaBruta' not in df.columns:
        df['OfertaBruta'] = df['OfertaSuperficial']
    # PerdidaTotal derivada si falta
    if 'PerdidaTotal' not in df.columns:
        df['PerdidaTotal'] = df['OfertaBruta'] - df['OfertaSuperficial']
    
    datos = df.to_dict('records')
    return jsonify({
        'dias': len(datos),
        'datos': datos,
        'columnas': list(datos[0].keys()) if datos else [],
        'escenario_actual': escenario_param
    })

@app.route('/api/stats')
def get_stats():
    """API que retorna estadísticas resumidas"""
    df = cargar_datos()
    if df is None:
        return jsonify({'error': 'No hay datos'}), 404
    
    # Obtener escenario del query parameter
    escenario_param = request.args.get('escenario', default=None, type=int)
    
    # Si se especifica escenario y existe la columna, filtrar
    if escenario_param is not None and 'Escenario' in df.columns:
        df = df[df['Escenario'] == escenario_param]
    
    if df.empty:
        return jsonify({'error': f'No hay datos para el escenario {escenario_param}'}), 404
    
    stats = {
        'oferta_promedio': float(df['OfertaAgua'].mean()),
        'oferta_maxima': float(df['OfertaAgua'].max()),
        'oferta_minima': float(df['OfertaAgua'].min()),
        'acciones_promedio': float(df['AccionesDisponibles'].mean()),
        'dias_con_desmarque': int((df['AccionesDisponibles'] > 0).sum()),
        'total_dias': len(df),
        'escenario_actual': escenario_param
    }
    
    return jsonify(stats)

@app.route('/api/indicadores')
def get_indicadores():
    """API que retorna indicadores para un escenario específico"""
    df_ind = cargar_indicadores()
    if df_ind is None:
        return jsonify({'error': 'No hay indicadores disponibles'}), 404
    
    # Obtener escenario del query parameter
    escenario_param = request.args.get('escenario', default=0, type=int)
    
    # Filtrar por escenario
    fila = df_ind[df_ind['Escenario'] == escenario_param]
    
    if fila.empty:
        return jsonify({'error': f'No hay indicadores para el escenario {escenario_param}'}), 404
    
    # Convertir fila a diccionario
    indicador_dict = fila.iloc[0].to_dict()
    
    # Redondear números
    for key, value in indicador_dict.items():
        if isinstance(value, float):
            indicador_dict[key] = round(value, 2)
    
    return jsonify({'indicador': indicador_dict})

@app.route('/api/parametros')
def get_parametros():
    """API que retorna los parámetros del modelo - SIEMPRE recarga para evitar caché"""
    try:
        # Limpiar módulo cacheado
        if 'initial_values' in sys.modules:
            del sys.modules['initial_values']
        
        # Recargar fresco
        import initial_values
        importlib.reload(initial_values)
        
        from initial_values import (
            NUMERO_ACCIONES, VALOR_ACCION,
            PORCENTAJE_DESMARQUE_INICIAL, PORCENTAJE_DESMARQUE_FINAL,
            FECHA_DESMARQUE, SALTO_DESMARQUE,
            RECARGAS_AGUA_SUBTERRANEA,
            FRECUENCIA_TURNO, DURACION_MANTENIMIENTO
        )
        try:
            from initial_values import HORAS_TURNO, CAUDAL_MAXIMO_LS, EFICIENCIA_POSICION_PCT
        except ImportError:
            HORAS_TURNO = 12
            CAUDAL_MAXIMO_LS = 0.0
            EFICIENCIA_POSICION_PCT = 0.0
        
        parametros = {
            'ACCIONES': {
                'NUMERO_ACCIONES': int(NUMERO_ACCIONES),
                'VALOR_ACCION':    float(VALOR_ACCION),
                'HORAS_TURNO':     int(HORAS_TURNO),
                'CAUDAL_MAXIMO_LS': float(CAUDAL_MAXIMO_LS),
                'EFICIENCIA_POSICION_PCT': float(EFICIENCIA_POSICION_PCT)
            },
            'DESMARQUE': {
                'PORCENTAJE_INICIAL': float(PORCENTAJE_DESMARQUE_INICIAL * 100),
                'PORCENTAJE_FINAL': float(PORCENTAJE_DESMARQUE_FINAL * 100),
                'FECHA_CAMBIO': FECHA_DESMARQUE,
                'SALTO_DESMARQUE': float(SALTO_DESMARQUE * 100)
            },
            'AGUA_SUBTERRANEA': {
                'RECARGAS': [{'fecha': f, 'cantidad': float(c)} for f, c in RECARGAS_AGUA_SUBTERRANEA]
            },
            'TURNO': {
                'FRECUENCIA_DIAS': int(FRECUENCIA_TURNO),
                'MANTENIMIENTO_DIAS': int(DURACION_MANTENIMIENTO)
            }
        }
        
        return jsonify(parametros)
    except ImportError as e:
        return jsonify({'error': f'No se pudo cargar initial_values: {str(e)}'}), 500

@app.route('/api/variables')
def get_variables():
    """API que retorna las variables del día actual"""
    df = cargar_datos()
    if df is None:
        return jsonify({'error': 'No hay datos disponibles'}), 404
    
    escenario_param = request.args.get('escenario', default=0, type=int)
    dia_param = request.args.get('dia', default=1, type=int)
    
    # Filtrar por escenario y día
    df_filtered = df[(df['Escenario'] == escenario_param) & (df['Dia'] == dia_param)]
    
    if df_filtered.empty:
        return jsonify({'error': f'No hay datos para escenario {escenario_param}, día {dia_param}'}), 404
    
    row = df_filtered.iloc[0]
    
    SEGUNDOS_TURNO = 12 * 3600  # 43 200 s
    oferta_bruta_m3 = round(float(row.get('OfertaBruta', 0)), 4)
    oferta_neta_m3  = round(float(row.get('OfertaSuperficial', 0)), 4)
    variables = {
        'DIA_NUMERO': int(row.get('Dia', 0)),
        'FECHA': str(row.get('Fecha', '')),
        'OFERTA_SUPERFICIAL': round(oferta_neta_m3, 2),
        'OFERTA_BRUTA':       round(oferta_bruta_m3, 2),
        'PERDIDA_TOTAL':      round(oferta_bruta_m3 - oferta_neta_m3, 2),
        # Caudal en L/s: m³ × 1000 / segundos del turno
        'CAUDAL_BRUTO_LS':    round(oferta_bruta_m3 * 1000 / SEGUNDOS_TURNO, 3),
        'CAUDAL_EFECTIVO_LS': round(oferta_neta_m3  * 1000 / SEGUNDOS_TURNO, 3),
        'RECARGA_SUBTERRANEA': round(float(row.get('RecargaSubterranea', 0)), 2),
        'PORCENTAJE_DESMARQUE': round(float(row.get('PorcentajeDesmarque', 0)) * 100, 2),
        'NUMERO_TURNO': int(row.get('NumeroTurno', 0)),
        'TURNO_ACTIVO': int(row.get('TurnoActivo', 0)),
        'EN_PARADA': int(row.get('EnParada', 0)),
        'APERTURA_CANAL': int(row.get('AperturaCanal', 0))
    }
    
    return jsonify(variables)

@app.route('/<path:filename>')
def serve_static(filename):
    """Sirve archivos CSS y JS"""
    return send_from_directory(FRONTEND_DIR, filename)

if __name__ == '__main__':
    # Abrir navegador automáticamente
    webbrowser.open('http://localhost:5000')
    
    # Iniciar servidor
    print("="*60)
    print("SERVIDOR ANIMACIÓN - Sistema de Gestión de Agua")
    print("="*60)
    print("[OK] Abriendo navegador en http://localhost:5000")
    print("[OK] Presiona Ctrl+C para detener el servidor")
    print("="*60)
    
    app.run(debug=False, port=5000, use_reloader=False)
