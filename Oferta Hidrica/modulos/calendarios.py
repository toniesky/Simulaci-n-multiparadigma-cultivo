"""Generación de calendarios de turnos y paradas del canal."""

import os
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path


def generar_calendario(iv):
    """
    Genera el DataFrame de calendario con turnos y paradas.

    Columnas resultantes:
        Dia, Fecha, NumeroTurno, DiaEnTurno, TurnoActivo,
        EnParada, DuracionMantenimiento, AperturaCanal

    Args:
        iv: módulo initial_values cargado

    Returns:
        DataFrame con el calendario completo
    """
    dias = list(range(1, iv.TIEMPO_TOTAL + 1))
    fecha_inicio = datetime.strptime(iv.FECHA_INICIO, "%Y-%m-%d")
    fechas = [fecha_inicio + timedelta(days=i - 1) for i in dias]

    turnos = []
    numero_turno = 1
    for dia in dias:
        dia_en_turno = ((dia - 1) % iv.FRECUENCIA_TURNO) + 1
        turno_activo = 1 if dia_en_turno == 1 else 0
        turnos.append({
            'Dia': dia,
            'Fecha': fechas[dia - 1].strftime("%Y-%m-%d"),
            'NumeroTurno': numero_turno,
            'DiaEnTurno': dia_en_turno,
            'TurnoActivo': turno_activo,
        })
        if dia_en_turno == iv.FRECUENCIA_TURNO:
            numero_turno += 1

    calendario = pd.DataFrame(turnos)

    dias_parada = _dias_en_parada(iv)
    calendario['EnParada'] = calendario['Dia'].apply(lambda d: 1 if d in dias_parada else 0)
    calendario['DuracionMantenimiento'] = calendario['EnParada'].apply(
        lambda x: iv.DURACION_MANTENIMIENTO if x == 1 else 0
    )
    calendario['AperturaCanal'] = (
        (calendario['TurnoActivo'] == 1) & (calendario['EnParada'] == 0)
    ).astype(int)

    return calendario


def guardar_calendario_paradas(iv, script_dir):
    """
    Genera y guarda data/inputs/CalendarioParadas.csv.

    Args:
        iv: módulo initial_values cargado
        script_dir: directorio raíz del proyecto (Path o str)

    Returns:
        DataFrame de paradas generado
    """
    fecha_inicio_dt = datetime.strptime(iv.FECHA_INICIO, "%Y-%m-%d")
    dias_parada = _dias_en_parada(iv)

    paradas_data = []
    for dia in range(1, iv.TIEMPO_TOTAL + 1):
        fecha_actual = fecha_inicio_dt + timedelta(days=dia - 1)
        en_parada = 1 if dia in dias_parada else 0
        paradas_data.append({
            'Dia': dia,
            'Fecha': fecha_actual.strftime("%Y-%m-%d"),
            'EnParada': en_parada,
            'DuracionMantenimiento': iv.DURACION_MANTENIMIENTO if en_parada else 0,
        })

    df = pd.DataFrame(paradas_data)
    out_path = Path(script_dir) / 'data' / 'inputs' / 'CalendarioParadas.csv'
    os.makedirs(out_path.parent, exist_ok=True)
    df.to_csv(out_path, index=False)

    print(f"[OK] CalendarioParadas.csv generado:")
    print(f"     Días en parada: {len(df[df['EnParada'] == 1])}")
    print(f"     Duración mantenimiento: {iv.DURACION_MANTENIMIENTO} días")
    return df


# ---- helpers privados -------------------------------------------------------

def _dias_en_parada(iv):
    """Retorna el conjunto de días que caen dentro de algún período de parada."""
    dias = set()
    for dia_inicio in iv.CALENDARIO_PARADAS:
        for offset in range(iv.DURACION_MANTENIMIENTO):
            dia = dia_inicio + offset
            if dia <= iv.TIEMPO_TOTAL:
                dias.add(dia)
    return dias
