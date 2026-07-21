@echo off
chcp 1252 > nul
title Simulacion - Capstone
echo.
echo ============================================================
echo  MODULO 1 - Oferta Hidrica
echo ============================================================
echo.
cd /d "C:\Users\anton\Desktop\Capstone\Modelo\Oferta Hidrica"
set NO_ANIMATION=1
"C:\Users\anton\Desktop\Capstone\Modelo\.venv\Scripts\python.exe" modelo_simulacion_oferta_hidrica.py
echo.
start "Animacion Oferta Hidrica" "C:\Users\anton\Desktop\Capstone\Modelo\.venv\Scripts\python.exe" "C:\Users\anton\Desktop\Capstone\Modelo\Oferta Hidrica\Animacion\backend\app.py"
echo [OK] Servidor de animacion iniciado en http://localhost:5000
echo.
echo ============================================================
echo  MODULO 2 - Simulacion Cultivo
echo ============================================================
echo.
cd /d "C:\Users\anton\Desktop\Capstone\Modelo\Simulación Cultivo"
"C:\Users\anton\Desktop\Capstone\Modelo\.venv\Scripts\python.exe" simulacion_cultivo.py
echo.
echo ============================================================
echo  Simulacion completada. Abriendo reporte interactivo...
echo ============================================================
echo.
echo Limpiando servidor anterior del reporte (puerto 8051)...
powershell -NoProfile -Command "Get-NetTCPConnection -LocalPort 8051 -State Listen -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique | ForEach-Object { Stop-Process -Id $_ -Force -ErrorAction SilentlyContinue }"
timeout /t 2 /nobreak > nul
echo Iniciando servidor en http://localhost:8051 ...
start "" "http://localhost:8051"
"C:\Users\anton\Desktop\Capstone\Modelo\.venv\Scripts\python.exe" "C:\Users\anton\Desktop\Capstone\Modelo\Simulación Cultivo\reporte_interactivo.py"
pause