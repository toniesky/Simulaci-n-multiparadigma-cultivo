import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from src.initial_values import TIEMPO_TOTAL, FECHA_INICIO

# ===== CALENDARIO DE TURNOS =====
# NO SE GENERA - Se calcula dinámicamente en modelo_sistema_agua.py
# # Turno cada FRECUENCIA_TURNO días, con duración DURACION_TURNO
# fecha_inicio = datetime.strptime(FECHA_INICIO, "%Y-%m-%d")
# turnos_data = []
# for dia in range(1, TIEMPO_TOTAL + 1):
#     fecha_actual = fecha_inicio + timedelta(days=dia-1)
#     turno_num = ((dia - 1) // FRECUENCIA_TURNO) + 1
#     dia_en_turno = ((dia - 1) % FRECUENCIA_TURNO) + 1
#     turno_activo = 1 if dia_en_turno <= DURACION_TURNO else 0
#     turnos_data.append({
#         'Dia': dia,
#         'Fecha': fecha_actual.strftime("%Y-%m-%d"),
#         'NumeroTurno': turno_num,
#         'DiaEnTurno': dia_en_turno,
#         'TurnoActivo': turno_activo
#     })
#
# df_turnos = pd.DataFrame(turnos_data)
# df_turnos.to_csv('data/inputs/CalendarioTurnosCanal.csv', index=False)
# print("[OK] CalendarioTurnosCanal.csv creado")
# print(df_turnos.head(30))

# ===== CALENDARIO DE PARADAS =====
from src.initial_values import DURACION_MANTENIMIENTO, CALENDARIO_PARADAS

# Definir fecha_inicio para generar fechas
fecha_inicio = datetime.strptime(FECHA_INICIO, "%Y-%m-%d")

paradas_data = []
dias_parada_inicio = CALENDARIO_PARADAS  # Leer desde initial_values.py

# Crear conjunto de TODOS los días de parada (considerando duración)
dias_en_parada = set()
for dia_inicio in dias_parada_inicio:
    for offset in range(DURACION_MANTENIMIENTO):
        dia_parada = dia_inicio + offset
        if dia_parada <= TIEMPO_TOTAL:
            dias_en_parada.add(dia_parada)

for dia in range(1, TIEMPO_TOTAL + 1):
    fecha_actual = fecha_inicio + timedelta(days=dia-1)
    en_parada = 1 if dia in dias_en_parada else 0
    duracion_parada = DURACION_MANTENIMIENTO if en_parada else 0
    paradas_data.append({
        'Dia': dia,
        'Fecha': fecha_actual.strftime("%Y-%m-%d"),
        'EnParada': en_parada,
        'DuracionMantenimiento': duracion_parada
    })

df_paradas = pd.DataFrame(paradas_data)
df_paradas.to_csv('data/inputs/CalendarioParadas.csv', index=False)
print("[OK] CalendarioParadas.csv creado")
print(f"   Días en parada: {len(df_paradas[df_paradas['EnParada'] == 1])}")

# ===== CALENDARIO DE APERTURA =====
# NO SE GENERA - Se calcula dinámicamente en modelo_sistema_agua.py
# # El canal está abierto:
# # - Día 1 de cada turno (para Opción 1 - desmarque inicio)
# # - Último día del turno (para Opción 2 - desmarque final)
# apertura_data = []
# for dia in range(1, TIEMPO_TOTAL + 1):
#     fecha_actual = fecha_inicio + timedelta(days=dia-1)
#     dia_en_turno = ((dia - 1) % FRECUENCIA_TURNO) + 1
#     # Canal abierto en día 1 (Opción 1) O último día del ciclo (Opción 2)
#     canal_abierto = 1 if (dia_en_turno == 1 or dia_en_turno == FRECUENCIA_TURNO) else 0
#     apertura_data.append({
#         'Dia': dia,
#         'Fecha': fecha_actual.strftime("%Y-%m-%d"),
#         'CanalAbiertoProgramado': canal_abierto
#     })
#
# df_apertura = pd.DataFrame(apertura_data)
# df_apertura.to_csv('data/inputs/CalendarioApertura.csv', index=False)
# print("\n[OK] CalendarioApertura.csv creado")
# print(f"Patrón: Abierto en día 1 (Opción 1) y día {FRECUENCIA_TURNO} (Opción 2)")
# print(f"Ciclo: cada {FRECUENCIA_TURNO} días")
# print(df_apertura.head(FRECUENCIA_TURNO + 3))

print("\n[OK] CalendarioParadas.csv creado exitosamente")
