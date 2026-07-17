"""Balance hídrico diario: oferta superficial y subterránea."""

import random
from datetime import datetime, timedelta
import pandas as pd


def fecha_cambio_desmarque(iv):
    """
    Fecha ÚNICA de cambio de desmarque: el primer FECHA_DESMARQUE (mes-día)
    que ocurre en o después de FECHA_INICIO.

    El desmarque cambia UNA sola vez y luego se mantiene (continuidad), sin
    reiniciarse al cruzar el año. Antes de esta fecha se aplica el desmarque
    inicial; desde esta fecha en adelante, el desmarque final.
    """
    inicio = datetime.strptime(iv.FECHA_INICIO, "%Y-%m-%d")
    cambio = datetime.strptime(f"{inicio.year}-{iv.FECHA_DESMARQUE}", "%Y-%m-%d")
    if cambio < inicio:
        # Si el cambio de ese año ya pasó al iniciar, se usa el del próximo año.
        cambio = datetime.strptime(f"{inicio.year + 1}-{iv.FECHA_DESMARQUE}", "%Y-%m-%d")
    return cambio


def get_porcentaje_desmarque(fecha_str, iv, desmarque_override=None):
    """
    Porcentaje de desmarque según la fecha (cambio único con continuidad).

    Antes de fecha_cambio_desmarque → PORCENTAJE_DESMARQUE_INICIAL
    Desde fecha_cambio_desmarque    → desmarque_override o PORCENTAJE_DESMARQUE_FINAL

    El cambio ocurre una sola vez (primer FECHA_DESMARQUE desde el inicio) y se
    mantiene indefinidamente, evitando que al cambiar de año se vuelva al
    desmarque anterior.
    """
    fecha = datetime.strptime(fecha_str, "%Y-%m-%d")
    fecha_cambio = fecha_cambio_desmarque(iv)
    if fecha < fecha_cambio:
        return iv.PORCENTAJE_DESMARQUE_INICIAL
    return desmarque_override if desmarque_override is not None else iv.PORCENTAJE_DESMARQUE_FINAL


def get_recarga_dia(fecha_str, iv):
    """
    Retorna la cantidad de agua subterránea recargada en la fecha dada.
    Solo hay recarga en las fechas especificadas en RECARGAS_AGUA_SUBTERRANEA.
    En todos los demás días retorna 0.0.
    """
    fecha = datetime.strptime(fecha_str, "%Y-%m-%d")
    anio = fecha.year
    for fecha_mm_dd, cantidad in iv.RECARGAS_AGUA_SUBTERRANEA:
        if fecha == datetime.strptime(f"{anio}-{fecha_mm_dd}", "%Y-%m-%d"):
            return cantidad
    return 0.0


def calcular_agua_dia(dia, calendario, iv, desmarque_override=None):
    """
    Oferta hídrica para un día específico.

        - OfertaSuperficial_neta = NumeroAcciones x ValorAccion x Desmarque x (1 - Pérdida)
          (solo en días con apertura de canal y día de turno)
        - RecargaSubterranea = cantidad recargada HOY según RECARGAS_AGUA_SUBTERRANEA
          (0.0 en todos los demás días)

    Returns:
        (oferta_sup_neta, oferta_sup_bruta, perdida_m3, recarga_hoy, desmarque_pct)
    """
    fila = calendario.iloc[dia - 1]
    apertura = int(fila['AperturaCanal'])
    fecha_str = str(fila['Fecha'])
    dia_en_turno = int(fila['DiaEnTurno'])

    desmarque_pct = get_porcentaje_desmarque(fecha_str, iv, desmarque_override)
    recarga_hoy = get_recarga_dia(fecha_str, iv)

    oferta_sup_bruta = 0.0
    oferta_sup_neta = 0.0
    perdida_conduccion = 0.0
    perdida_filtracion = 0.0
    if apertura == 1 and dia_en_turno in (1, iv.FRECUENCIA_TURNO):
        agua_maxima = iv.NUMERO_ACCIONES * iv.VALOR_ACCION
        oferta_sup_bruta = agua_maxima * desmarque_pct
        # Pérdida por conducción: uniforme aleatoria
        coef_conduccion = random.uniform(iv.PERDIDA_CONDUCCION[0], iv.PERDIDA_CONDUCCION[1])
        oferta_tras_conduccion = oferta_sup_bruta * (1 - coef_conduccion)
        # Pérdida por filtración: uniforme aleatoria
        coef_filtracion = random.uniform(iv.PERDIDA_FILTRACION[0], iv.PERDIDA_FILTRACION[1])
        oferta_sup_neta = oferta_tras_conduccion * (1 - coef_filtracion)
        perdida_conduccion = oferta_sup_bruta - oferta_tras_conduccion
        perdida_filtracion = oferta_tras_conduccion - oferta_sup_neta

    perdida_total = perdida_conduccion + perdida_filtracion
    return oferta_sup_neta, oferta_sup_bruta, perdida_conduccion, perdida_filtracion, perdida_total, recarga_hoy, desmarque_pct


def simular(calendario, iv, desmarque_override=None, numero_escenario=None):
    """
    Ejecuta la simulación completa y retorna el DataFrame de resultados.

    Args:
        calendario: DataFrame generado por calendarios.generar_calendario
        iv: módulo initial_values cargado
        desmarque_override: porcentaje de desmarque final (None → usa iv.PORCENTAJE_DESMARQUE_FINAL)
        numero_escenario: identificador añadido como columna 'Escenario' si se indica

    Returns:
        DataFrame con columnas adicionales:
            OfertaSuperficial, PerdidaConduccion, PerdidaFiltracion, PerdidaTotal,
            PorcentajeDesmarque, RecargaSubterranea [, Escenario]
    """
    resultados = calendario.copy()

    # --- Límite de simulación: un único ciclo de desmarque ---
    # El desmarque estimado sólo es válido hasta el próximo cambio (el
    # septiembre siguiente). Más allá se requeriría una nueva predicción del
    # desmarque, por lo que no es posible simular ese período con la
    # información disponible.
    fecha_inicio = datetime.strptime(iv.FECHA_INICIO, "%Y-%m-%d")
    fecha_fin = fecha_inicio + timedelta(days=iv.TIEMPO_TOTAL - 1)
    cambio = fecha_cambio_desmarque(iv)
    fecha_limite = cambio.replace(year=cambio.year + 1)  # próximo FECHA_DESMARQUE
    if fecha_fin >= fecha_limite:
        dias_max = (fecha_limite - fecha_inicio).days
        raise ValueError(
            f"El horizonte de simulación termina el {fecha_fin.date()} y excede el "
            f"próximo cambio de desmarque ({fecha_limite.date()}). No es posible "
            f"simular más allá de un ciclo de desmarque: reduzca TIEMPO_TOTAL a un "
            f"máximo de {dias_max} días."
        )

    os_list, pcond_list, pfilt_list, ptot_list, dpc_list, stk_list = [], [], [], [], [], []
    for dia in range(1, iv.TIEMPO_TOTAL + 1):
        os_, _, pcond, pfilt, ptot, stk, dpc = calcular_agua_dia(dia, calendario, iv, desmarque_override)
        os_list.append(os_)
        pcond_list.append(pcond)
        pfilt_list.append(pfilt)
        ptot_list.append(ptot)
        dpc_list.append(dpc)
        stk_list.append(stk)

    resultados['OfertaSuperficial'] = os_list
    resultados['PerdidaConduccion'] = pcond_list
    resultados['PerdidaFiltracion'] = pfilt_list
    resultados['PerdidaTotal'] = ptot_list
    resultados['PorcentajeDesmarque'] = dpc_list
    resultados['RecargaSubterranea'] = stk_list
    if numero_escenario is not None:
        resultados['Escenario'] = numero_escenario

    # Eliminar columnas internas/redundantes del output final
    cols_drop = [c for c in ['DiaEnTurno', 'DuracionMantenimiento'] if c in resultados.columns]
    if cols_drop:
        resultados = resultados.drop(columns=cols_drop)

    return resultados
