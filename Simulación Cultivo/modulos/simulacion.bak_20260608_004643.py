"""Balance hídrico diario FAO-56 (coeficiente doble: Kcb + Ke)."""
import pandas as pd
import parametros as P
from .fao56 import calcular_kcb, calcular_kcmax


def _dias_hasta_proximo_turno(dia_idx, oferta_lista):
    """Cuenta cuántos días faltan desde dia_idx+1 hasta el próximo día con oferta > 0.
    Retorna 1 si ya hay turno hoy, o el resto del ciclo si no hay más turnos."""
    for d in range(dia_idx + 1, len(oferta_lista)):
        if oferta_lista[d] > 0:
            return max(1, d - dia_idx)
    return max(1, len(oferta_lista) - dia_idx)

def simular_cultivo(c, df_clima, oferta_canal_m3_diaria, regante, en_parada_diaria=None,
                    estanque_ini=None, stock_sub_ini=None, recarga_sub_diaria=None):
    """Ejecuta la simulación FAO-56 para una fila de cultivo y un regante.
    oferta_canal_m3_diaria: lista con la oferta SUPERFICIAL del canal (m3) por día desde la siembra.
    en_parada_diaria: lista de enteros (0/1) indicando si el canal está en parada ese día.
    regante: dict con 'frecuencia_dias', 'hectareas', 'capacidad_estanque_m3',
             'nivel_estanque_inicial_m3'.
    estanque_ini: nivel inicial del estanque (m3). Si None, usa regante['nivel_estanque_inicial_m3'].
    stock_sub_ini: stock subterráneo inicial (m3). Si None, usa P.STOCK_SUBTERRANEO_INICIAL_M3.
    El regante decide regar SOLO los días múltiplo de su frecuencia (F, 2F, 3F, ...).
    Si no es día de turno: la oferta superficial del día se pierde y el subterráneo
    queda intacto."""
    L_ini, L_des = int(c['L_ini']), int(c['L_des'])
    L_med, L_fin = int(c['L_med']), int(c['L_fin'])
    Kcb_ini = float(c['Kcb_ini'])
    Kcb_med = float(c['Kcb_med'])
    Kcb_fin = float(c['Kcb_fin'])
    h   = float(c['h'])
    p   = float(c['p'])
    Ze  = float(c['Ze'])
    few = float(c['few'])
    dias_totales = L_ini + L_des + L_med + L_fin

    AET = P.AET
    AFE = P.AFE
    ADT = 1000.0 * (P.CC - P.PMP) * Ze
    AFA = p * ADT

    hectareas         = float(regante['hectareas'])
    frecuencia        = int(regante['frecuencia_dias'])
    fraccion_cult     = float(regante.get('fraccion_cultivada', 1.0))
    capacidad_m3      = float(regante['capacidad_estanque_m3'])
    nivel_estanque_m3 = (float(estanque_ini) if estanque_ini is not None
                         else float(regante['nivel_estanque_inicial_m3']))
    stock_sub_m3      = (float(stock_sub_ini) if stock_sub_ini is not None
                         else float(P.STOCK_SUBTERRANEO_INICIAL_M3))
    # Conversion mm <-> m3 referida al AREA CULTIVADA (donde efectivamente
    # esta el cultivo y se reparte el riego). 1 mm sobre hectareas*fracc =
    # ha_to_mm m3. Toda la simulacion (Dr, Etc, R, ADT) usa este mismo
    # marco fisico: mm sobre area cultivada.
    ha_cultivadas     = hectareas * fraccion_cult
    ha_to_mm          = 10.0 * ha_cultivadas
    dias_sin_riego    = 0   # contador de dias consecutivos sin aplicar riego
    dias_sin_canal    = 0   # solo se reinicia cuando el CANAL entrega agua
    estanque_ciclo    = False  # True si el estanque ya riegó en este inter-turno

    De = min(P.De0, AET)
    Dr = min(P.Dr0, ADT)  # clampear al maximo fisico del cultivo

    filas = []
    for dia in range(dias_totales):
        dia_n = dia + 1   # día 1-indexado para el turno
        idx = min(dia, len(df_clima) - 1)
        clima  = df_clima.iloc[idx]
        ETo    = float(clima['[Prom] mm Evapotranspiración'])
        Pr     = float(clima['[Prom] mm Precipitación'])
        u2     = float(clima['[Prom] m/s Velocidad de Viento'])
        hr_min = float(clima['[Min] % Humedad Relativa'])
        oferta_canal_m3 = (float(oferta_canal_m3_diaria[dia])
                           if dia < len(oferta_canal_m3_diaria) else 0.0)
        en_parada = (int(en_parada_diaria[dia])
                     if en_parada_diaria and dia < len(en_parada_diaria) else 0)
        # Renovación de derechos de agua subterránea: el cupo legal se suma
        # al stock disponible en la fecha de renovación (acumulativo).
        if recarga_sub_diaria and dia < len(recarga_sub_diaria):
            stock_sub_m3 += float(recarga_sub_diaria[dia])

        kcb   = calcular_kcb(dia, L_ini, L_des, L_med,
                             Kcb_ini, Kcb_med, Kcb_fin, L_fin)
        kcmax = calcular_kcmax(kcb, h, hr_min, u2)

        # 1) Kr en función de De(t-1)
        if De <= AFE:
            Kr = 1.0
        else:
            Kr = max(0.0, (AET - De) / (AET - AFE))

        # 2) Ke
        Ke = min(Kr * (kcmax - kcb), few * kcmax)
        Ke = max(Ke, 0.0)

        # 3) Es
        Es = Ke * ETo

        # ---- Demanda objetivo (politica H_OBJETIVO_PCT) ----
        # Se busca llevar la humedad del suelo desde su valor actual hasta
        # H_OBJETIVO_PCT (% de agua util disponible, definido en parametros),
        # descontando la lluvia del dia. Internamente se traduce a Dr:
        #   Dr_objetivo = ADT * (1 - H_OBJETIVO_PCT/100)
        # El sobrante de canal (si la demanda < oferta) recarga el estanque
        # hasta su capacidad; lo que no cabe se cuenta como Perdida_m3.
        Etc_pot         = (kcb * ETo + Es)                     # mm (sobre area cultivada)
        Dr_objetivo_mm  = ADT * (1.0 - P.H_OBJETIVO_PCT / 100.0)
        # --- HUMEDAD MÍNIMA DE SEGURIDAD ---
        # Si la humedad baja del umbral, se fuerza riego hasta ese valor
        theta_min_pct = getattr(P, 'HUMEDAD_MINIMA_PCT', None)
        if theta_min_pct is not None:
            Dr_min_mm = ADT * (1.0 - theta_min_pct / 100.0)
            if Dr > Dr_min_mm:
                Dr_objetivo_mm = min(Dr_objetivo_mm, Dr_min_mm)
                # Se fuerza la demanda a rellenar hasta el mínimo
                demanda_neta_mm = max(0.0, Dr - Dr_objetivo_mm - Pr)
                demanda_neta_m3 = demanda_neta_mm * ha_to_mm

        # --- POLÍTICA: RIEGO HASTA CAPACIDAD DE CAMPO ---
        if getattr(P, 'RIEGO_HASTA_CC', False):
            Dr_objetivo_mm = 0.0  # Dr=0 equivale a humedad = CC
            demanda_neta_mm = max(0.0, Dr - Dr_objetivo_mm - Pr)
            demanda_neta_m3 = demanda_neta_mm * ha_to_mm

        demanda_neta_m3 = max(0.0, Dr - Dr_objetivo_mm - Pr)
        demanda_neta_m3 = demanda_neta_m3 * ha_to_mm

        # ---- Turno del regante ----
        # El CalendarioOferta ya define cuando llega agua al regante; por lo
        # tanto cualquier dia con oferta > 0 es un "dia de turno". El campo
        # frecuencia_dias del regante queda como informacion contextual y NO
        # bloquea la captacion (antes podia desincronizarse del calendario y
        # se perdia la oferta).
        es_turno = oferta_canal_m3 > 0

        sub_usado_m3      = 0.0
        aplicado_m3      = 0.0
        perdida_m3       = 0.0
        canal_riego_m3   = 0.0   # canal → riego directo
        canal_estanque_m3 = 0.0  # canal → estanque

        # 1) Captacion desde el canal cuando hay oferta
        if es_turno:
            usar_canal = min(oferta_canal_m3, demanda_neta_m3)
            canal_riego_m3 = usar_canal
            aplicado_m3 += usar_canal
            sobrante_canal = oferta_canal_m3 - usar_canal
            # el sobrante del canal recarga el estanque (hasta capacidad)
            espacio_estanque = capacidad_m3 - nivel_estanque_m3
            recarga = min(sobrante_canal, espacio_estanque)
            canal_estanque_m3 = recarga
            nivel_estanque_m3 += recarga
            perdida_m3 += sobrante_canal - recarga

        # 2) Si tras el canal queda demanda, se complementa con ESTANQUE y
        #    luego SUBTERRÁNEA, ambos controlados por dias_sin_canal.
        #    El estanque solo se activa UNA VEZ por ciclo inter-turno.
        falta_m3 = max(0.0, demanda_neta_m3 - aplicado_m3)
        umbral_est = getattr(P, 'DIAS_SIN_RIEGO_PARA_ESTANQUE',
                             P.DIAS_SIN_RIEGO_PARA_SUBTERRANEA)
        if (falta_m3 > 0 and dias_sin_canal >= umbral_est
                and not estanque_ciclo and nivel_estanque_m3 > 0):
            # Días hasta el próximo turno del canal
            dias_hasta_turno = 1
            for _d in range(dia + 1, len(oferta_canal_m3_diaria)):
                if oferta_canal_m3_diaria[_d] > 0:
                    dias_hasta_turno = _d - dia
                    break
            dias_hasta_turno = max(1, dias_hasta_turno)
            # Cuota proporcional: más días hasta el turno → más agua ahora.
            # Cubre la demanda estimada para todo el periodo restante.
            cuota_m3 = min(falta_m3 * dias_hasta_turno, nivel_estanque_m3)
            nivel_estanque_m3 -= cuota_m3
            aplicado_m3       += cuota_m3
            falta_m3          = max(0.0, demanda_neta_m3 - aplicado_m3)
            estanque_ciclo     = True   # no vuelve a regar hasta el próximo turno

        if falta_m3 > 0 and dias_sin_canal >= P.DIAS_SIN_RIEGO_PARA_SUBTERRANEA:
            if stock_sub_m3 > 0:
                sub_usado_m3  = min(falta_m3, stock_sub_m3)
                stock_sub_m3 -= sub_usado_m3
                aplicado_m3  += sub_usado_m3

        deficit_m3 = max(0.0, demanda_neta_m3 - aplicado_m3)

        # Contadores de días sin riego
        if aplicado_m3 > 0:
            dias_sin_riego = 0
        else:
            dias_sin_riego += 1
        # dias_sin_canal solo se reinicia cuando el CANAL entrega agua
        if es_turno and canal_riego_m3 > 0:
            dias_sin_canal    = 0
            estanque_ciclo    = False   # nuevo ciclo: habilitar estanque
        else:
            dias_sin_canal += 1
            # Si el canal no llega pero ya pasó un ciclo completo (frecuencia
            # de turno), habilitar el estanque de nuevo para el próximo ciclo
            if dias_sin_canal % frecuencia == 0:
                estanque_ciclo = False

        R = aplicado_m3 / ha_to_mm if ha_to_mm > 0 else 0.0   # lámina efectiva (mm)

        # 4) Actualizar De
        De = De - Pr - R + Es
        De = min(max(De, 0.0), AET)

        # 5) Ks en función de Dr(t-1)
        if Dr <= AFA:
            Ks = 1.0
        else:
            Ks = max(0.0, (ADT - Dr) / (ADT - AFA))

        # 5b) Retención no lineal por textura de suelo (f(H) = H^alpha).
        #     H_norm = (1 - Dr/ADT) ∈ [0,1] = agua útil disponible normalizada.
        #     Solo afecta a la TRANSPIRACIÓN; la evaporación Es queda intacta.
        H_norm = max(0.0, 1.0 - Dr / ADT)
        f_H    = H_norm ** P.ALPHA_SUELO

        # 6) Etc = Ks * Kcb * ETo * f(H) + Es  (en mm sobre area cultivada;
        #    la fraccion_cultivada se aplica a traves de ha_to_mm al pasar
        #    a m3, no aqui sobre la lamina).
        Ep  = Ks * kcb * ETo * f_H
        Etc = Ep + Es

        # 7) Actualizar Dr — fracción del agua aplicada que drena por debajo
        #    de la zona radicular según textura (FRACCION_DRENAJE).
        #    La capa superficial (De) no se ve afectada: el drenaje ocurre
        #    a mayor profundidad que Ze.
        f_drain = getattr(P, 'FRACCION_DRENAJE', 0.0)
        Dr = Dr - Pr * (1.0 - f_drain) - R * (1.0 - f_drain) + Etc
        Dr = min(max(Dr, 0.0), ADT)

        H = (1.0 - Dr / ADT) * 100.0
        Etc_m3_ha    = Etc * 10.0                       # m3 por ha cultivada
        Etc_m3_total = Etc_m3_ha * ha_cultivadas        # m3 totales
        Riego_m3     = R * ha_to_mm

        filas.append({
            'Cultivo':            c['nombre'],
            'Dia':                dia_n,
            'Turno':              int(es_turno),
            'Kcb':                round(kcb, 3),
            'Kcmax':              round(kcmax, 3),
            'ETo_mm':             round(ETo, 3),
            'Etc_mm':             round(Etc, 3),
            'Etc_m3_ha':          round(Etc_m3_ha, 3),
            'Etc_m3_total':       round(Etc_m3_total, 3),
            'Demanda_m3':         round(demanda_neta_m3, 3),
            'OfertaCanal_m3':     round(oferta_canal_m3, 3),
            'Canal_Riego_m3':    round(canal_riego_m3, 3),
            'Canal_Estanque_m3': round(canal_estanque_m3, 3),
            'Subterranea_Usada_m3': round(sub_usado_m3, 3),
            'Stock_Subterraneo_m3': round(stock_sub_m3, 3),
            'Aplicado_m3':        round(aplicado_m3, 3),
            'Estanque_m3':        round(nivel_estanque_m3, 3),
            'Perdida_m3':         round(perdida_m3, 3),
            # Totales a nivel REGANTE (en partición única coinciden con la fila):
            # permiten verificar  Oferta = Riego directo + Almacenado + Perdida
            'Oferta_Canal_Total_m3':    round(oferta_canal_m3, 3),
            'Canal_Riego_Total_m3':     round(canal_riego_m3, 3),
            'Canal_Estanque_Total_m3':  round(canal_estanque_m3, 3),
            'Perdida_Total_m3':         round(perdida_m3, 3),
            'Deficit_m3':         round(deficit_m3, 3),
            'Riego_mm':           round(R, 3),
            'Riego_m3':           round(Riego_m3, 3),
            'H_pct':              round(H, 2),
            'Theta_vol_pct':      round(P.PMP * 100.0 + (P.CC - P.PMP) * 100.0 * H / 100.0, 2),
            'EnParada':           en_parada,
        })
    return pd.DataFrame(filas), ADT, AFA

def simular_multi_particion(crops_list, ha_part, regante, df_clima, oferta_canal_m3, en_parada,
                             estanque_ini=None, stock_sub_ini=None, recarga_sub_diaria=None):
    """Simula N cultivos en N particiones de ha_part ha cada una, compartiendo el mismo
    estanque y stock subterráneo día a día (modelo simultáneo correcto).

    El canal entrega agua UNA sola vez por día y se reparte entre todas las particiones
    de forma proporcional a su demanda diaria. El excedente de canal recarga el estanque
    compartido. El estanque y el subterráneo también se reparten entre quienes los necesitan.

    crops_list          : lista de filas pd.Series con parámetros de cultivo.
    ha_part             : hectáreas por partición.
    regante             : dict/Series con capacidad_estanque_m3, fraccion_cultivada, etc.
    df_clima            : DataFrame de clima recortado al inicio de siembra.
    oferta_canal_m3     : lista con oferta TOTAL del canal (m3) por día (para el regante).
    en_parada           : lista de ints (0/1) por día.
    estanque_ini / stock_sub_ini : estado inicial compartido; None → usa defaults del regante/P.

    Returns (list[pd.DataFrame], estanque_final_m3, stock_sub_final_m3).
    """
    n = len(crops_list)
    ini_est = (float(estanque_ini) if estanque_ini is not None
               else float(regante['nivel_estanque_inicial_m3']))
    ini_sub = (float(stock_sub_ini) if stock_sub_ini is not None
               else float(P.STOCK_SUBTERRANEO_INICIAL_M3))
    if n == 0:
        return [], ini_est, ini_sub

    frac_cult     = float(regante.get('fraccion_cultivada', 1.0))
    ha_cultivadas = ha_part * frac_cult
    frecuencia    = int(regante.get('frecuencia_dias', 9))
    ha_to_mm      = 10.0 * ha_cultivadas          # 1 mm sobre ha_cultivadas → m3
    capacidad_m3  = float(regante['capacidad_estanque_m3'])
    nivel_est_m3  = ini_est
    stock_sub_m3  = ini_sub

    dias_max = max(int(c['L_ini'] + c['L_des'] + c['L_med'] + c['L_fin']) for c in crops_list)

    # Estado por partición
    estados = []
    for c in crops_list:
        ADT = 1000.0 * (P.CC - P.PMP) * float(c['Ze'])
        AFA = float(c['p']) * ADT
        estados.append({
            'De': min(P.De0, P.AET),
            'Dr': min(P.Dr0, ADT),
            'ADT': ADT, 'AFA': AFA,
            'dias_sin_riego': 0,
            'dias_sin_canal': 0,       # solo reinicia cuando el canal entrega agua
            'estanque_ciclo': False,   # True si el estanque ya rió en este inter-turno
            'dias_totales': int(c['L_ini'] + c['L_des'] + c['L_med'] + c['L_fin']),
            'filas': [],
        })

    for dia in range(dias_max):
        dia_n      = dia + 1
        idx        = min(dia, len(df_clima) - 1)
        clima      = df_clima.iloc[idx]
        ETo        = float(clima['[Prom] mm Evapotranspiración'])
        Pr         = float(clima['[Prom] mm Precipitación'])
        u2         = float(clima['[Prom] m/s Velocidad de Viento'])
        hr_min     = float(clima['[Min] % Humedad Relativa'])
        oferta_dia = float(oferta_canal_m3[dia]) if dia < len(oferta_canal_m3) else 0.0
        parada_dia = int(en_parada[dia]) if en_parada and dia < len(en_parada) else 0
        es_turno   = oferta_dia > 0
        # Renovación de derechos de agua subterránea (cupo legal compartido
        # por todas las particiones del regante).
        if recarga_sub_diaria and dia < len(recarga_sub_diaria):
            stock_sub_m3 += float(recarga_sub_diaria[dia])

        # ── 1) Demanda de riego de cada partición activa ─────────────────────
        demandas_m3 = []
        Ke_list     = []
        kcb_list    = []
        kcmax_list  = []
        for i, c in enumerate(crops_list):
            s = estados[i]
            if dia >= s['dias_totales']:
                demandas_m3.append(0.0); Ke_list.append(0.0)
                kcb_list.append(0.0);   kcmax_list.append(0.0)
                continue
            L_ini = int(c['L_ini']); L_des = int(c['L_des'])
            L_med = int(c['L_med']); L_fin = int(c['L_fin'])
            kcb   = calcular_kcb(dia, L_ini, L_des, L_med,
                                  float(c['Kcb_ini']), float(c['Kcb_med']),
                                  float(c['Kcb_fin']), L_fin)
            kcmax = calcular_kcmax(kcb, float(c['h']), hr_min, u2)
            kcb_list.append(kcb); kcmax_list.append(kcmax)

            De_i = s['De']
            Kr   = 1.0 if De_i <= P.AFE else max(0.0, (P.AET - De_i) / (P.AET - P.AFE))
            Ke   = max(0.0, min(Kr * (kcmax - kcb), float(c['few']) * kcmax))
            Ke_list.append(Ke)

            Dr_obj = (0.0 if getattr(P, 'RIEGO_HASTA_CC', False)
                      else s['ADT'] * (1.0 - P.H_OBJETIVO_PCT / 100.0))
            dem_mm = max(0.0, s['Dr'] - Dr_obj - Pr)
            demandas_m3.append(dem_mm * ha_to_mm)

        total_demanda = sum(demandas_m3)

        # ── 2) Distribuir agua del canal (UNA entrega total compartida) ───────
        asignado_canal    = [0.0] * n
        perdida_portfolio = 0.0
        recarga           = 0.0   # canal → estanque (compartido)
        if es_turno:
            usar_canal = min(oferta_dia, total_demanda) if total_demanda > 0 else 0.0
            if total_demanda > 0:
                for i in range(n):
                    asignado_canal[i] = usar_canal * (demandas_m3[i] / total_demanda)
            sobrante  = oferta_dia - usar_canal
            espacio   = capacidad_m3 - nivel_est_m3
            recarga   = min(sobrante, espacio)
            nivel_est_m3     += recarga
            perdida_portfolio  = sobrante - recarga

        # ── 3) Estanque (racionado) y subterráneo para cubrir déficit restante ─
        aplicado  = list(asignado_canal)
        sub_usado = [0.0] * n

        umbral_est = getattr(P, 'DIAS_SIN_RIEGO_PARA_ESTANQUE',
                             P.DIAS_SIN_RIEGO_PARA_SUBTERRANEA)
        # Días hasta el próximo turno del canal (para racionar el estanque)
        dias_hasta_turno = 1
        for _d in range(dia + 1, len(oferta_canal_m3)):
            if oferta_canal_m3[_d] > 0:
                dias_hasta_turno = _d - dia
                break
        dias_hasta_turno = max(1, dias_hasta_turno)

        elegibles_est = [i for i in range(n)
                         if dia < estados[i]['dias_totales']
                         and estados[i]['dias_sin_canal'] >= umbral_est
                         and not estados[i]['estanque_ciclo']]
        faltas_est = [max(0.0, demandas_m3[i] - aplicado[i]) for i in range(n)]
        falta_est_total = sum(faltas_est[i] for i in elegibles_est)

        if falta_est_total > 0 and nivel_est_m3 > 0:
            # Cuota racionada: distribuir el déficit entre los días hasta el turno
            cuota_total = falta_est_total / dias_hasta_turno
            usar_tank = min(cuota_total, nivel_est_m3)
            nivel_est_m3 -= usar_tank
            for i in elegibles_est:
                if falta_est_total > 0:
                    aplicado[i] += usar_tank * (faltas_est[i] / falta_est_total)
                    estados[i]['estanque_ciclo'] = True  # un solo uso por ciclo inter-turno

        elegibles_sub = [i for i in range(n)
                         if dia < estados[i]['dias_totales']
                         and estados[i]['dias_sin_canal'] >= P.DIAS_SIN_RIEGO_PARA_SUBTERRANEA]
        faltas2     = [max(0.0, demandas_m3[i] - aplicado[i]) for i in range(n)]
        falta_eleg2 = sum(faltas2[i] for i in elegibles_sub)
        if falta_eleg2 > 0 and stock_sub_m3 > 0:
            usar_sub = min(falta_eleg2, stock_sub_m3)
            stock_sub_m3 -= usar_sub
            for i in elegibles_sub:
                if falta_eleg2 > 0:
                    add = usar_sub * (faltas2[i] / falta_eleg2)
                    aplicado[i]  += add
                    sub_usado[i] += add

        # ── 4) Actualizar estados y registrar ─────────────────────────────────
        # Numero de particiones ACTIVAS este dia (cultivo aun en curso)
        n_activas = sum(1 for i in range(n) if dia < estados[i]['dias_totales'])
        n_rep = max(n_activas, 1)  # divisor para Canal_Estanque y Perdida
        for i, c in enumerate(crops_list):
            s = estados[i]
            if dia >= s['dias_totales']:
                continue
            kcb  = kcb_list[i]
            Ke   = Ke_list[i]
            Es   = Ke * ETo
            R    = aplicado[i] / ha_to_mm if ha_to_mm > 0 else 0.0

            s['De'] = min(max(s['De'] - Pr - R + Es, 0.0), P.AET)

            Ks     = (1.0 if s['Dr'] <= s['AFA']
                      else max(0.0, (s['ADT'] - s['Dr']) / (s['ADT'] - s['AFA'])))
            H_norm = max(0.0, 1.0 - s['Dr'] / s['ADT'])
            f_H    = H_norm ** P.ALPHA_SUELO
            Ep     = Ks * kcb * ETo * f_H
            Etc    = Ep + Es

            # Actualizar Dr — fracción del agua aplicada que drena por debajo
            # de la zona radicular según textura (FRACCION_DRENAJE), igual que
            # en simular_cultivo (partición única). El drenaje ocurre a mayor
            # profundidad que Ze, por lo que no afecta a De (capa superficial).
            f_drain = getattr(P, 'FRACCION_DRENAJE', 0.0)
            s['Dr'] = min(max(s['Dr'] - Pr * (1.0 - f_drain)
                              - R * (1.0 - f_drain) + Etc, 0.0), s['ADT'])
            H       = (1.0 - s['Dr'] / s['ADT']) * 100.0

            if aplicado[i] > 0:
                s['dias_sin_riego'] = 0
            else:
                s['dias_sin_riego'] += 1
            # dias_sin_canal solo se reinicia cuando el canal entrega agua directamente
            if asignado_canal[i] > 0:
                s['dias_sin_canal']  = 0
                s['estanque_ciclo']  = False   # nuevo ciclo: habilitar estanque
            else:
                s['dias_sin_canal'] += 1
                # Si el canal no llega pero ya pasó un ciclo completo,
                # habilitar el estanque de nuevo para el próximo ciclo
                if s['dias_sin_canal'] % frecuencia == 0:
                    s['estanque_ciclo'] = False

            s['filas'].append({
                'Cultivo':              c['nombre'],
                'Dia':                  dia_n,
                'Turno':                int(es_turno),
                'Kcb':                  round(kcb,                   3),
                'Kcmax':                round(kcmax_list[i],          3),
                'ETo_mm':               round(ETo,                   3),
                'Etc_mm':               round(Etc,                   3),
                'Etc_m3_ha':            round(Etc * 10.0,            3),
                'Etc_m3_total':         round(Etc * 10.0 * ha_cultivadas, 3),
                'Demanda_m3':           round(demandas_m3[i],        3),
                'OfertaCanal_m3':       round(asignado_canal[i],     3),
                'Canal_Riego_m3':       round(asignado_canal[i],     3),
                'Canal_Estanque_m3':    round(recarga / n_rep,       3),
                'Subterranea_Usada_m3': round(sub_usado[i],          3),
                'Stock_Subterraneo_m3': round(stock_sub_m3,          3),
                'Aplicado_m3':          round(aplicado[i],           3),
                'Estanque_m3':          round(nivel_est_m3,          3),
                'Perdida_m3':           round(perdida_portfolio / n_rep, 3),
                # Totales a nivel REGANTE (iguales en todas las particiones):
                # permiten verificar  Oferta = Riego directo + Almacenado + Perdida
                'Oferta_Canal_Total_m3':    round(oferta_dia,            3),
                'Canal_Riego_Total_m3':     round(sum(asignado_canal),   3),
                'Canal_Estanque_Total_m3':  round(recarga,               3),
                'Perdida_Total_m3':         round(perdida_portfolio,     3),
                'Deficit_m3':           round(max(0.0, demandas_m3[i] - aplicado[i]), 3),
                'Riego_mm':             round(R,                     3),
                'Riego_m3':             round(aplicado[i],           3),
                'H_pct':                round(H,                     2),
                'Theta_vol_pct':        round(P.PMP*100.0 + (P.CC-P.PMP)*100.0*H/100.0, 2),
                'EnParada':             parada_dia,
            })

    dfs = [pd.DataFrame(s['filas']) for s in estados]
    return dfs, nivel_est_m3, stock_sub_m3
