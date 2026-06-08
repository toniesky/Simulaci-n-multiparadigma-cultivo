"""Gráficos diarios del balance hídrico — devuelve imágenes PNG en base64."""
import io
import base64
import datetime
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
import parametros as P


def _fecha_base(fecha_siembra=None):
    """Retorna fecha de siembra calculada automáticamente si no se pasa."""
    if fecha_siembra is None:
        doy = P.DIA_INICIO_SIMULACION + getattr(P, 'DIA_SIEMBRA', 1) - 1
        return datetime.date(2026, 1, 1) + datetime.timedelta(days=doy - 1)
    return fecha_siembra


def _dias_a_fechas(dias, fecha_siembra):
    return [fecha_siembra + datetime.timedelta(days=int(d) - 1) for d in dias]


def _fmt_ax_fechas(ax):
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%d %b'))
    ax.xaxis.set_major_locator(mdates.AutoDateLocator())
    ax.figure.autofmt_xdate(rotation=30, ha='right')


def _b64_fig(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=95)
    plt.close(fig)
    return base64.b64encode(buf.getvalue()).decode('ascii')


# ---------------------------------------------------------------------------
# Gráfico 1 (único por escenario): Distribución de Oferta Superficial
# ---------------------------------------------------------------------------
def _grafico_canal_b64(df_sim, escenario, fecha_siembra=None):
    """Barras apiladas: oferta total del regante = riego directo + almacenado + pérdida.
    Usa las columnas *_Total_m3 para mostrar la oferta completa (no la fracción de una partición)."""
    fs = _fecha_base(fecha_siembra)
    dias  = df_sim['Dia'].values
    xs    = _dias_a_fechas(dias, fs)
    bar_w = datetime.timedelta(days=1)

    if 'Canal_Riego_Total_m3' in df_sim.columns:
        riego   = df_sim['Canal_Riego_Total_m3'].values
        est     = df_sim['Canal_Estanque_Total_m3'].values
        perdida = df_sim['Perdida_Total_m3'].values
    else:
        riego   = df_sim['Canal_Riego_m3'].values
        est     = df_sim['Canal_Estanque_m3'].values
        perdida = df_sim['Perdida_m3'].values

    total = riego + est + perdida
    mask  = total > 0.01
    xm    = [xs[k] for k in range(len(xs)) if mask[k]]

    fig, ax = plt.subplots(figsize=(10, 3.2))
    ax.bar(xm, riego[mask],   color='#1565c0', label='Riego directo',       alpha=0.88, width=bar_w)
    ax.bar(xm, est[mask],     bottom=riego[mask],
           color='#90caf9', label='Almacenado en estanque', alpha=0.88, width=bar_w)
    ax.bar(xm, perdida[mask], bottom=(riego + est)[mask],
           color='#ef9a9a', label='Pérdida (sin absorber)',  alpha=0.88, width=bar_w)
    ax.set_ylabel('m³ / día')
    ax.set_title(f'Escenario {escenario} — Distribución de Oferta Superficial')
    ax.legend(fontsize=8, loc='upper right', ncol=3)
    ax.grid(axis='y', alpha=0.25)
    ax.set_ylim(bottom=0)
    _fmt_ax_fechas(ax)
    fig.tight_layout()
    return _b64_fig(fig)


# ---------------------------------------------------------------------------
# Gráfico 2 (único por escenario): Agua aplicada total apilada por cultivo
# ---------------------------------------------------------------------------
def _grafico_agua_cultivos_b64(dfs_list, nombres, colores, escenario, fecha_siembra=None):
    """Barras apiladas: agua aplicada total (suma de particiones) coloreada por cultivo.
    dfs_list : list[DataFrame]  — uno por partición activa
    nombres  : list[str]        — nombre del cultivo en cada partición
    colores  : list[str]        — color hex para cada cultivo (igual que Gantt)
    """
    if not dfs_list:
        return None
    fs    = _fecha_base(fecha_siembra)
    bar_w = datetime.timedelta(days=1)

    # Eje de días = unión de todos los DataFrames (el más largo gana).
    # Así cultivos cortos no recortan el eje cuando otro termina más tarde.
    dias_ref = np.array(sorted(set(
        d for df_p in dfs_list for d in df_p['Dia'].values
    )))

    fig, ax = plt.subplots(figsize=(10, 3.2))
    bottom = np.zeros(len(dias_ref))
    for df_p, nombre, color in zip(dfs_list, nombres, colores):
        idx_map = {d: i for i, d in enumerate(df_p['Dia'].values)}
        vals = np.array([
            df_p['Aplicado_m3'].values[idx_map[d]] if d in idx_map else 0.0
            for d in dias_ref
        ])
        mask = vals > 0.005
        xs   = _dias_a_fechas(dias_ref, fs)
        ax.bar(
            [xs[k] for k in range(len(xs)) if mask[k]],
            vals[mask],
            bottom=bottom[mask],
            color=color, alpha=0.88, width=bar_w,
            label=nombre.title(),
        )
        bottom += vals

    ax.set_ylabel('m³ / día')
    ax.set_title(f'Escenario {escenario} — Agua aplicada por cultivo')
    ax.legend(fontsize=8, loc='upper right', ncol=len(nombres))
    ax.grid(axis='y', alpha=0.25)
    ax.set_ylim(bottom=0)
    _fmt_ax_fechas(ax)
    fig.tight_layout()
    return _b64_fig(fig)


# ---------------------------------------------------------------------------
# Gráfico 3 (condicional): Nivel del estanque compartido
# ---------------------------------------------------------------------------
def _grafico_estanque_b64(df_sim, escenario, cap_m3=None, fecha_siembra=None):
    """Línea del nivel del estanque a lo largo de la temporada."""
    fs   = _fecha_base(fecha_siembra)
    xs   = _dias_a_fechas(df_sim['Dia'].values, fs)
    nivel = df_sim['Estanque_m3'].values

    fig, ax = plt.subplots(figsize=(10, 3.0))
    ax.fill_between(xs, nivel, alpha=0.25, color='#0288d1')
    ax.plot(xs, nivel, color='#0288d1', linewidth=1.8, label='Nivel estanque')
    if cap_m3 and cap_m3 > 0:
        ax.axhline(cap_m3, color='#01579b', linestyle='--', linewidth=1.1,
                   label=f'Capacidad {cap_m3:.0f} m³')
    ax.set_ylabel('m³')
    ax.set_title(f'Escenario {escenario} — Nivel del estanque compartido')
    ax.legend(fontsize=8)
    ax.grid(axis='y', alpha=0.25)
    ax.set_ylim(bottom=0)
    _fmt_ax_fechas(ax)
    fig.tight_layout()
    return _b64_fig(fig)


# ---------------------------------------------------------------------------
# Gráfico 4 (condicional): Stock de agua subterránea
# ---------------------------------------------------------------------------
def _grafico_sub_b64(df_sim, escenario, fecha_siembra=None):
    """Línea del stock de agua subterránea a lo largo de la temporada."""
    if 'Stock_Subterraneo_m3' not in df_sim.columns:
        return None
    fs    = _fecha_base(fecha_siembra)
    xs    = _dias_a_fechas(df_sim['Dia'].values, fs)
    stock = df_sim['Stock_Subterraneo_m3'].values

    fig, ax = plt.subplots(figsize=(10, 3.0))
    ax.fill_between(xs, stock, alpha=0.20, color='#6d4c41')
    ax.plot(xs, stock, color='#6d4c41', linewidth=1.8, label='Stock subterráneo')
    ax.set_ylabel('m³')
    ax.set_title(f'Escenario {escenario} — Stock de agua subterránea')
    ax.legend(fontsize=8)
    ax.grid(axis='y', alpha=0.25)
    ax.set_ylim(bottom=0)
    _fmt_ax_fechas(ax)
    fig.tight_layout()
    return _b64_fig(fig)


# ---------------------------------------------------------------------------
# Función principal (por partición)
# ---------------------------------------------------------------------------
def _graficos_b64(df_sim, escenario, h_afa_pct, fecha_siembra=None):
    """Devuelve dict con PNG por partición: 'humedad', 'et', 'fuente'.
    - 'humedad': evolución de la humedad volumétrica del suelo.
    - 'et'     : ETo / ETc real y riego en mm.
    - 'fuente' : agua aplicada al cultivo desglosada por fuente
                 (canal directo / estanque / subterráneo).
    Los gráficos compartidos (canal total y agua por cultivo) se generan
    con _grafico_canal_b64() y _grafico_agua_cultivos_b64()."""
    out = {}
    fs  = _fecha_base(fecha_siembra)
    xs  = _dias_a_fechas(df_sim['Dia'], fs)

    cc_ref  = P.CC  * 100.0
    pmp_ref = P.PMP * 100.0
    theta_pct = pmp_ref + (cc_ref - pmp_ref) * df_sim['H_pct'] / 100.0
    theta_obj = pmp_ref + (cc_ref - pmp_ref) * P.H_OBJETIVO_PCT / 100.0

    # ── Humedad ────────────────────────────────────────────────────────────
    fig, ax = plt.subplots(figsize=(9, 3.3))
    if 'EnParada' in df_sim.columns:
        en_parada = df_sim['EnParada'].astype(int).values
        xs_raw    = _dias_a_fechas(df_sim['Dia'].values, fs)
        i, added  = 0, False
        while i < len(en_parada):
            if en_parada[i] == 1:
                j = i
                while j < len(en_parada) and en_parada[j] == 1:
                    j += 1
                ax.axvspan(xs_raw[i], xs_raw[j - 1], color='red', alpha=0.18,
                           zorder=1, label='Parada canal' if not added else None)
                added = True
                i = j
            else:
                i += 1
    ax.plot(xs, theta_pct, color='tab:blue', linewidth=1.8, label='Humedad volumetrica', zorder=3)
    ax.axhline(cc_ref,    color='tab:green',  linestyle='-',  linewidth=1.2,
               label=f'CC = {cc_ref:.1f}%', zorder=2)
    ax.axhline(theta_obj, color='tab:olive',  linestyle='--', linewidth=1.0,
               label=f'Objetivo riego = {theta_obj:.1f}%', zorder=2)
    ax.axhline(pmp_ref,   color='tab:red',    linestyle='-',  linewidth=1.2,
               label=f'PMP = {pmp_ref:.1f}%', zorder=2)
    umbral = getattr(P, 'HUMEDAD_EMERGENCIA_PCT', 12.0)
    ax.axhline(umbral,    color='tab:purple', linestyle=':', linewidth=1.0,
               label=f'Umbral emergencia = {umbral:.1f}%', zorder=2)
    ax.set_ylim(0, cc_ref * 1.15)
    ax.set_xlabel('Fecha')
    ax.set_ylabel('Humedad volumetrica (%)')
    ax.set_title(f'Escenario {escenario} — Humedad del suelo')
    ax.grid(True, alpha=0.3)
    ax.legend(loc='best', fontsize=8, ncol=2)
    _fmt_ax_fechas(ax)
    fig.tight_layout()
    out['humedad'] = _b64_fig(fig)

    # ── ET ─────────────────────────────────────────────────────────────────
    fig, ax = plt.subplots(figsize=(9, 3.3))
    ax.plot(xs, df_sim['ETo_mm'], color='tab:gray',  linewidth=1.2, label='ETo')
    ax.plot(xs, df_sim['Etc_mm'], color='tab:green', linewidth=1.4, label='Etc real')
    ax.bar(xs,  df_sim['Riego_mm'], color='tab:blue', alpha=0.55, label='Riego')
    ax.set_xlabel('Fecha')
    ax.set_ylabel('mm/día')
    ax.set_title(f'Escenario {escenario} — Evapotranspiración y riego')
    ax.grid(True, alpha=0.3)
    ax.legend(loc='best', fontsize=8)
    _fmt_ax_fechas(ax)
    fig.tight_layout()
    out['et'] = _b64_fig(fig)

    # ── Agua aplicada por fuente (panel único, por partición) ──────────────
    dias_vals  = df_sim['Dia'].values
    xs_vals    = _dias_a_fechas(dias_vals, fs)
    bar_w      = datetime.timedelta(days=1)
    canal_riego = df_sim['Canal_Riego_m3'].values
    aplicado    = df_sim['Aplicado_m3'].values
    sub_usado   = df_sim['Subterranea_Usada_m3'].values
    est_usado   = np.maximum(0.0, aplicado - canal_riego - sub_usado)

    mask_a = aplicado > 0.01
    da     = [xs_vals[k] for k in range(len(xs_vals)) if mask_a[k]]

    fig, ax = plt.subplots(figsize=(10, 3.2))
    ax.bar(da, canal_riego[mask_a], color='#1565c0', label='Del canal',    alpha=0.88, width=bar_w)
    ax.bar(da, est_usado[mask_a],   bottom=canal_riego[mask_a],
           color='#388e3c', label='Del estanque', alpha=0.88, width=bar_w)
    ax.bar(da, sub_usado[mask_a],   bottom=(canal_riego + est_usado)[mask_a],
           color='#e65100', label='Subterráneo',  alpha=0.88, width=bar_w)
    ax.set_ylabel('m³ / día')
    ax.set_title(f'Escenario {escenario} — Agua aplicada por fuente')
    ax.legend(fontsize=8, loc='upper right', ncol=3)
    ax.grid(axis='y', alpha=0.25)
    ax.set_ylim(bottom=0)
    _fmt_ax_fechas(ax)
    fig.tight_layout()
    out['fuente'] = _b64_fig(fig)

    return out

