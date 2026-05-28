"""Balance hídrico diario: oferta superficial y subterránea."""

import random
from datetime import datetime
import pandas as pd


def get_porcentaje_desmarque(fecha_str, iv, desmarque_override=None):
    """
    Porcentaje de desmarque según la fecha (cambio dinámico).

    Antes de FECHA_DESMARQUE → PORCENTAJE_DESMARQUE_INICIAL
    Desde FECHA_DESMARQUE   → desmarque_override o PORCENTAJE_DESMARQUE_FINAL
    """
    fecha = datetime.strptime(fecha_str, "%Y-%m-%d")
    fecha_cambio = datetime.strptime(f"{fecha.year}-{iv.FECHA_DESMARQUE}", "%Y-%m-%d")
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
