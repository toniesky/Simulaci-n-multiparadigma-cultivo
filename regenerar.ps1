# Script para limpiar caché completo y regenerar datos

Write-Host "=== LIMPIANDO CACHE PYTHON ===" -ForegroundColor Cyan

# Eliminar todos los __pycache__
Get-ChildItem -Path "c:\Users\anton\OneDrive\Desktop\Capstone\Modelo" -Recurse -Directory -Filter "__pycache__" | 
    ForEach-Object { 
        Remove-Item $_.FullName -Recurse -Force -ErrorAction SilentlyContinue
        Write-Host "  ✓ Eliminado: $($_.FullName)"
    }

# Eliminar archivos .pyc
Get-ChildItem -Path "c:\Users\anton\OneDrive\Desktop\Capstone\Modelo" -Recurse -File -Filter "*.pyc" | 
    ForEach-Object { 
        Remove-Item $_.FullName -Force -ErrorAction SilentlyContinue
    }

Write-Host "`n=== VERIFICANDO PARAMETRO ===" -ForegroundColor Cyan
cd "c:\Users\anton\OneDrive\Desktop\Capstone\Modelo\Oferta Hidrica"
.\.venv\Scripts\python.exe -c "from src.initial_values import VALOR_ACCION, NUMERO_ACCIONES; print('VALOR_ACCION = ' + str(VALOR_ACCION)); print('Total = ' + str(NUMERO_ACCIONES * VALOR_ACCION))"

Write-Host "`n=== EJECUTANDO MODELO ===" -ForegroundColor Cyan
.\.venv\Scripts\python.exe create_data.py
.\.venv\Scripts\python.exe modelo_sistema_agua.py

Write-Host "`n=== VERIFICANDO CSV ===" -ForegroundColor Cyan
.\.venv\Scripts\python.exe -c "import pandas as pd; df = pd.read_csv('data/outputs/CalendarioOferta.csv'); turno = df[df['AperturaCanal']==1].iloc[0]; print(f'Primer turno: Dia {turno[\"Dia\"]}, OfertaSuperficial = {turno[\"OfertaSuperficial\"]:.2f} m3'); print(f'Esperado: ~155.52 m3 (8 acciones × 43.2 × 45% desmarque)')"

Write-Host "`n✓ REGENERACIÓN COMPLETADA" -ForegroundColor Green
