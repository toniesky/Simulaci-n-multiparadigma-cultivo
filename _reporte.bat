@echo off
chcp 1252 > nul
title Reporte Interactivo - Capstone
cd /d "C:\Users\anton\Desktop\Capstone\Modelo\Simulación Cultivo"
echo.
echo ============================================================
echo  Reporte Interactivo - Simulacion Cultivo
echo ============================================================
echo.
echo Iniciando servidor en http://localhost:8051 ...
echo (Si no hay simulacion previa, se ejecutara primero. Espere.)
echo.
start "" "http://localhost:8051"
"C:\Users\anton\Desktop\Capstone\Modelo\.venv\Scripts\python.exe" "C:\Users\anton\Desktop\Capstone\Modelo\Simulación Cultivo\reporte_interactivo.py"
pause