"""Generación de gráficos de resultados de la simulación (3 paneles, PNG)."""

import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.patches import Patch
import pandas as pd


def graficar(resultados, iv, output_path):
    """
    Genera y guarda el gráfico de 3 paneles de la simulación.

    Paneles:
        1. Oferta superficial ajustada (turnos, mantenimientos, cambio desmarque)
        2. Stock de agua subterránea (evolución diaria y reinicio)
        3. Oferta total = superficial (ajustada) + subterránea

    Args:
        resultados: DataFrame retornado por simulacion.simular
        iv: módulo initial_values cargado
        output_path: ruta absoluta del archivo PNG de salida
    """
    fig, axes = plt.subplots(2, 1, figsize=(18, 9))
    fechas = pd.to_datetime(resultados['Fecha'])
    primer_anio = fechas.dt.year.iloc[0]
    fecha_cambio_str = f"{primer_anio}-{iv.FECHA_DESMARQUE}"

    # ===== PANEL 1: Oferta superficial =====
    altura_mant = resultados['EnParada'].apply(lambda x: 25.0 if x == 1 else 0.0)
    axes[0].bar(fechas, altura_mant, color='red', alpha=0.4, width=1.0,
                label='Período de Mantenimiento', zorder=1)

    mask_sup = resultados['OfertaSuperficial'] > 0
    axes[0].bar(
        fechas[mask_sup], resultados.loc[mask_sup, 'OfertaSuperficial'],
        color='blue', alpha=0.9, width=0.9,
        label='Turno/Desmarque (Oferta Superficial)', zorder=2,
    )

    mask_otros = (resultados['OfertaSuperficial'] == 0) & (resultados['EnParada'] == 0)
    axes[0].bar(
        fechas[mask_otros], [1.0] * mask_otros.sum(),
        color='lightgray', alpha=0.3, width=0.9, label='Otros días', zorder=0,
    )

    try:
        axes[0].axvline(
            pd.to_datetime(fecha_cambio_str), color='orange',
            linestyle='--', linewidth=2,
            label=f'Cambio desmarque ({iv.FECHA_DESMARQUE})', alpha=0.7,
        )
    except Exception:
        pass

    axes[0].set_ylabel('Agua Disponible (m³)', fontsize=12, fontweight='bold')
    axes[0].set_title(
        f'Panel 1: Oferta Superficial Ajustada '
        f'(filtr. U[{iv.PERDIDA_FILTRACION[0]*100:.0f}%–{iv.PERDIDA_FILTRACION[1]*100:.0f}%], '
        f'cond. U[{iv.PERDIDA_CONDUCCION[0]*100:.0f}%–{iv.PERDIDA_CONDUCCION[1]*100:.0f}%])\n'
        f'({iv.PORCENTAJE_DESMARQUE_INICIAL*100:.0f}% hasta {iv.FECHA_DESMARQUE} → '
        f'{iv.PORCENTAJE_DESMARQUE_FINAL*100:.0f}% desde {iv.FECHA_DESMARQUE})',
        fontsize=13, fontweight='bold',
    )
    axes[0].grid(True, alpha=0.3, axis='y')
    axes[0].set_ylim(0, 30)
    axes[0].legend(handles=[
        Patch(facecolor='blue', alpha=0.9, label='Turno/Desmarque (Oferta Superficial)'),
        Patch(facecolor='red', alpha=0.4, label=f'Período Mantenimiento ({iv.DURACION_MANTENIMIENTO} días)'),
        Patch(facecolor='lightgray', alpha=0.3, label='Otros días'),
    ], loc='upper right', fontsize=10)

    # ===== PANEL 2: Recargas de agua subterránea =====
    recargas = sorted(iv.RECARGAS_AGUA_SUBTERRANEA, key=lambda r: r[0])
    colores_recarga = ['teal', 'mediumseagreen', 'cadetblue', 'steelblue']

    for i, (fecha_mm_dd, cantidad) in enumerate(recargas):
        fecha_recarga = pd.to_datetime(f"{primer_anio}-{fecha_mm_dd}")
        color = colores_recarga[i % len(colores_recarga)]

        axes[1].bar(
            fecha_recarga, cantidad, width=14,
            color=color, alpha=0.8, edgecolor='white', linewidth=1.5,
            label=f'Recarga {fecha_mm_dd}: +{cantidad:.0f} m³',
            align='edge',
        )
        axes[1].text(
            fecha_recarga + pd.Timedelta(days=7), cantidad + max(cantidad * 0.04, 0.8),
            f'+{cantidad:.0f} m³', ha='center', va='bottom',
            fontsize=12, fontweight='bold', color=color,
        )

    axes[1].set_ylabel('Cantidad Recargada (m³)', fontsize=12, fontweight='bold')
    max_recarga = max(c for _, c in recargas) if recargas else 1
    axes[1].set_ylim(0, max_recarga * 1.35)
    axes[1].set_title(
        'Panel 2: Recargas de Agua Subterránea (m³ adicionales en cada fecha)',
        fontsize=13, fontweight='bold',
    )
    axes[1].grid(True, alpha=0.3, axis='y')
    axes[1].legend(loc='upper right', fontsize=10)
    axes[1].set_xlabel('Fecha', fontsize=12, fontweight='bold')

    for ax in axes:
        ax.xaxis.set_major_locator(mdates.MonthLocator())
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        ax.tick_params(axis='x', rotation=45)

    plt.tight_layout()
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"[OK] Gráficos guardados en: {output_path}")
    plt.close()
