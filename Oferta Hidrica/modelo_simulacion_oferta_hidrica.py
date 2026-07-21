"""
Modelo de Gestión de Agua - Caudal Regante
Punto de entrada principal. La lógica está organizada en:

  modulos/
    carga_params.py   <- carga de parámetros sin caché de módulos
    calendarios.py    <- generación de calendarios de turnos y paradas
    simulacion.py     <- balance hídrico diario (oferta superficial y subterránea)
    indicadores.py    <- indicadores avanzados de disponibilidad
    graficos.py       <- gráficos de resultados (PNG, 3 paneles)
    escenarios.py     <- generación de escenarios de desmarque
    exportar.py       <- guardado de CSV y lanzamiento de animación

  src/
    initial_values.py <- parámetros configurables por el usuario

Ejecutar directamente:
  python modelo_simulacion_oferta_hidrica.py
"""

import os
import sys
import pandas as pd
from pathlib import Path

# Asegurar que el directorio del script esté en sys.path para encontrar modulos/
sys.path.insert(0, str(Path(__file__).resolve().parent))

from modulos import (  # noqa: E402
    carga_params,
    calendarios,
    simulacion,
    indicadores,
    graficos,
    escenarios,
    exportar,
    limpieza,
)

def main():
    """Función principal: ejecuta el modelo con múltiples escenarios de desmarque."""
    script_dir = Path(__file__).resolve().parent
    os.chdir(script_dir)
    print(f"[OK] Directorio de trabajo: {script_dir}")

    print(f"\n{'#'*60}")
    print("# MODELO DE DINÁMICA DE SISTEMAS - CAUDAL REGANTE")
    print("# Simulación Multi-Escenario con Incertidumbre de Desmarque")
    print(f"{'#'*60}\n")

    # ===== LIMPIAR PUERTO Y CACHÉ =====
    limpieza.limpiar_puerto(5000)
    limpieza.limpiar_cache(script_dir)

    # ===== CARGAR PARÁMETROS =====
    iv = carga_params.cargar_initial_values(script_dir)
    print("[OK] Valores iniciales recargados:")
    print(f"     NUMERO_ACCIONES = {iv.NUMERO_ACCIONES}")
    print(f"     VALOR_ACCION    = {iv.VALOR_ACCION} m³/acción  (1 L/s × {getattr(iv,'HORAS_TURNO',12)} h)")
    print(f"     RECARGAS_AGUA_SUBTERRANEA:")
    for fecha_mm_dd, cantidad in iv.RECARGAS_AGUA_SUBTERRANEA:
        print(f"       -> {fecha_mm_dd}: {cantidad} m3")

    # ===== CAUDAL MÁXIMO POR POSICIÓN GEOGRÁFICA =====
    # Ya calculado al cargar initial_values.py (iv.CAUDAL_MAXIMO_LS)
    caudal_maximo_ls = iv.CAUDAL_MAXIMO_LS
    print(f"\n[CAUDAL] Restricción geográfica del regante:")
    print(f"         Posición: ({iv.REGANTE_LATITUD}, {iv.REGANTE_LONGITUD})")
    print(f"         Canal: {iv.CANAL_KM} km | Bifurc: {iv.BIF_KM} km")
    print(f"         Eficiencia posición: {iv.EFICIENCIA_POSICION_PCT} %")
    print(f"         Usuarios upstream: {iv.PUNTOS_UPSTREAM} × {iv.PENALIZACION_UPSTREAM_LS} L/s")
    print(f"         Caudal máximo en predio: {caudal_maximo_ls} L/s\n")

    # ===== GENERAR CALENDARIOS =====
    print("[INICIO] Generando calendarios con valores iniciales actualizados...")
    calendarios.guardar_calendario_paradas(iv, script_dir)
    calendario = calendarios.generar_calendario(iv)
    print(f"[OK] Calendarios generados automáticamente. Días simulados: {len(calendario)}\n")

    # ===== GENERAR ESCENARIOS =====
    lista_escenarios = escenarios.generar_escenarios(iv)
    num_escenarios = len(lista_escenarios)
    salto_pct = iv.SALTO_DESMARQUE * 100

    print(f"Desmarque base (escenario 0): {iv.PORCENTAJE_DESMARQUE_FINAL*100:.1f}%")
    print(f"Salto entre escenarios      : {salto_pct:.1f}%")
    print(f"Número de escenarios        : {num_escenarios}")
    print("\nEscenarios:")
    for num, desmarque in lista_escenarios:
        label = "Principal" if num == 0 else f"+{num} saltos" if num > 0 else f"{num} saltos"
        print(f"  Escenario {num:+d}: {desmarque*100:.1f}%  ({label})")

    print(f"\n{'='*60}\n")

    # ===== SIMULAR TODOS LOS ESCENARIOS =====
    todos_resultados = []
    for idx, (numero_escenario, desmarque_2) in enumerate(lista_escenarios):
        print(f"\n[{idx+1}/{num_escenarios}] Escenario {numero_escenario} "
              f"(desmarque final: {desmarque_2*100:.1f}%)...")
        print(f"\n{'='*60}")
        print(f"SIMULACIÓN - Escenario {numero_escenario} (desmarque 2: {desmarque_2*100:.1f}%)")
        print(f"Acciones: {iv.NUMERO_ACCIONES} × 1 L/s × {getattr(iv,'HORAS_TURNO',12)} h = "
              f"{iv.NUMERO_ACCIONES * iv.VALOR_ACCION} m³ máximo | Cap: {caudal_maximo_ls} L/s")
        print(f"Desmarque INICIAL (antes del {iv.FECHA_DESMARQUE}): "
              f"{iv.PORCENTAJE_DESMARQUE_INICIAL*100:.0f}%")
        print(f"Desmarque FINAL (desde {iv.FECHA_DESMARQUE}): {desmarque_2*100:.1f}%")
        print(f"{'='*60}")

        res = simulacion.simular(calendario, iv, desmarque_2, numero_escenario,
                                 caudal_maximo_ls=caudal_maximo_ls)
        indicadores.calcular_indicadores(res, iv)
        todos_resultados.append(res)
        print(f"[OK] Simulación completada para {iv.TIEMPO_TOTAL} días")

    # ===== COMBINAR RESULTADOS =====
    df_combinado = pd.concat(todos_resultados, ignore_index=True)

    # ===== GRÁFICOS DEL ESCENARIO PRINCIPAL =====
    print(f"\n{'='*60}")
    print("Generando gráficos del escenario principal...")
    res_principal = simulacion.simular(calendario, iv, None, 0,
                                       caudal_maximo_ls=caudal_maximo_ls)
    graficos.graficar(
        res_principal, iv,
        str(script_dir / 'data' / 'outputs' / 'Graficos.png')
    )

    # ===== GUARDAR CSV COMBINADO =====
    csv_path = str(script_dir / 'data' / 'outputs' / 'CalendarioOferta.csv')
    exportar.guardar_csv(df_combinado, csv_path)
    print(f"[OK] {num_escenarios} escenarios guardados en: {csv_path}")

    # Eliminar archivo obsoleto si existe
    obsoleto = str(script_dir / 'data' / 'outputs' / 'CalendarioOferta_Escenarios.csv')
    if os.path.exists(obsoleto):
        try:
            os.remove(obsoleto)
            print(f"[OK] Archivo obsoleto eliminado: {obsoleto}")
        except (PermissionError, OSError):
            pass

    # ===== VALIDAR CSV =====
    print("\n[VALIDACIÓN] Verificando que CSV tiene datos correctos...")
    try:
        df_v = pd.read_csv(csv_path)
        df_p = df_v[df_v['Escenario'] == 0]
        dias_con_agua = int((df_p['OfertaSuperficial'] > 0).sum())
        oferta_total  = round(df_p['OfertaSuperficial'].sum(), 2)
        print(f"  Días con oferta superficial: {dias_con_agua}")
        print(f"  Oferta neta total (esc. 0) : {oferta_total} m³")
        print(f"  Caudal máximo aplicado      : {caudal_maximo_ls} L/s")
        print("  [OK] CSV CORRECTO")
    except Exception as e:
        print(f"  [!] Error en validación: {e}")

    # ===== RESUMEN FINAL =====
    print(f"\n{'='*60}")
    print("RESUMEN FINAL")
    print(f"{'='*60}")
    print(f"Desmarque inicial (antes del {iv.FECHA_DESMARQUE}): "
          f"{iv.PORCENTAJE_DESMARQUE_INICIAL*100:.0f}%")
    print(f"Desmarque final (desde {iv.FECHA_DESMARQUE}): "
          f"{iv.PORCENTAJE_DESMARQUE_FINAL*100:.1f}% (salto ±{salto_pct:.1f}%)")
    print(f"Escenarios generados: {num_escenarios}")
    print(f"Período de simulación: {iv.FECHA_INICIO} - {iv.TIEMPO_TOTAL} días")
    print(f"Duración mantenimiento: {iv.DURACION_MANTENIMIENTO} días")
    print(f"Frecuencia de turno: cada {iv.FRECUENCIA_TURNO} días")

    # ===== BALANCE HÍDRICO SUPERFICIAL (escenario principal) =====
    print(f"\n{'-'*60}")
    print("BALANCE HIDRICO SUPERFICIAL -- Escenario Principal (0)")
    print(f"{'-'*60}")
    df_p0 = df_combinado[df_combinado['Escenario'] == 0]
    oferta_neta  = df_p0['OfertaSuperficial'].sum()
    oferta_bruta = df_p0['OfertaBruta'].sum()
    perd_total   = df_p0['PerdidaTotal'].sum()
    recarga_sub  = df_p0['RecargaSubterranea'].sum()
    dias_turno   = int((df_p0['AperturaCanal'] == 1).sum())
    pct = lambda v: f"  ({v/oferta_bruta*100:.1f}%)" if oferta_bruta > 0 else ""
    print(f"  Oferta bruta total (canal)  : {oferta_bruta:>12,.1f} m3")
    print(f"  + Riego (llega al campo)    : {oferta_neta:>12,.1f} m3{pct(oferta_neta)}")
    print(f"  + Pérdida por posición      : {perd_total:>12,.1f} m3{pct(perd_total)}")
    print(f"  Recarga subterranea (DAA)   : {recarga_sub:>12,.1f} m3")
    print(f"  Días con apertura de canal  : {dias_turno:>12} dias")
    print(f"  Caudal máximo en predio     : {caudal_maximo_ls:>12.1f} L/s")

    print(f"\n{'#'*60}")
    print("# SIMULACIÓN COMPLETADA EXITOSAMENTE")
    print(f"{'#'*60}\n")

    # ===== ANIMACIÓN =====
    import sys as _sys
    _batch = (os.environ.get('NO_ANIMATION') == '1'
              or not _sys.stdout.isatty()
              or not _sys.stdin.isatty())
    if _batch:
        print("[OK] Animacion omitida (modo batch).")
        return

    print("\n" + "="*60)
    print("Deseas abrir la animacion interactiva en el navegador?")
    try:
        respuesta = input("Escribe 'si' o 'no' (por defecto: si): ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        respuesta = 'no'
        print("(Sin entrada interactiva, omitiendo animacion)")

    if respuesta != 'no':
        print("\nIniciando servidor de animación...")
        print("(Presiona Ctrl+C en la terminal para detener)\n")
        exportar.lanzar_animacion(script_dir)


if __name__ == '__main__':
    main()
