"""Gráficos diarios del balance hídrico — devuelve imágenes PNG en base64."""
import io
import base64
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import parametros as P


def _graficos_b64(df_sim, escenario, h_afa_pct):
    """Devuelve dict con los dos PNG (humedad, et) en base64.
    Grafica humedad volumetrica theta (%) en la misma escala que CC y PMP.
    Conversion: theta = PMP + (CC-PMP) * H_pct/100."""
    out = {}

    cc_ref  = P.CC  * 100.0
    pmp_ref = P.PMP * 100.0
    theta_pct = pmp_ref + (cc_ref - pmp_ref) * df_sim['H_pct'] / 100.0
    theta_obj = pmp_ref + (cc_ref - pmp_ref) * P.H_OBJETIVO_PCT / 100.0

    fig, ax = plt.subplots(figsize=(9, 3.3))
    # Bandas rojas para períodos de parada de canal
    if 'EnParada' in df_sim.columns:
        en_parada = df_sim['EnParada'].astype(int).values
        dias = df_sim['Dia'].values
        i = 0
        parada_label_added = False
        while i < len(en_parada):
            if en_parada[i] == 1:
                j = i
                while j < len(en_parada) and en_parada[j] == 1:
                    j += 1
                lbl = 'Parada canal' if not parada_label_added else None
                ax.axvspan(dias[i] - 0.5, dias[j - 1] + 0.5,
                           color='red', alpha=0.18, zorder=1, label=lbl)
                parada_label_added = True
                i = j
            else:
                i += 1
    ax.plot(df_sim['Dia'], theta_pct, color='tab:blue',
            linewidth=1.8, label='Humedad volumetrica', zorder=3)
    ax.axhline(cc_ref, color='tab:green', linestyle='-', linewidth=1.2,
               label=f'CC = {cc_ref:.1f}%', zorder=2)
    ax.axhline(theta_obj, color='tab:olive', linestyle='--', linewidth=1.0,
               label=f'Objetivo riego = {theta_obj:.1f}%', zorder=2)
    ax.axhline(pmp_ref, color='tab:red', linestyle='-', linewidth=1.2,
               label=f'PMP = {pmp_ref:.1f}%', zorder=2)
    # Línea de umbral de emergencia (en escala theta)
    umbral_theta_graf = getattr(P, 'HUMEDAD_EMERGENCIA_PCT', 12.0)
    ax.axhline(umbral_theta_graf, color='tab:purple', linestyle=':', linewidth=1.0,
               label=f'Umbral emergencia = {umbral_theta_graf:.1f}%', zorder=2)
    ax.set_ylim(0, cc_ref * 1.15)
    ax.set_xlabel('Dia desde siembra')
    ax.set_ylabel('Humedad volumetrica (%)')
    ax.set_title(f'Escenario {escenario} - Humedad del suelo')
    ax.grid(True, alpha=0.3)
    ax.legend(loc='best', fontsize=8, ncol=2)
    fig.tight_layout()
    buf = io.BytesIO(); fig.savefig(buf, format='png', dpi=95); plt.close(fig)
    out['humedad'] = base64.b64encode(buf.getvalue()).decode('ascii')

    fig, ax = plt.subplots(figsize=(9, 3.3))
    ax.plot(df_sim['Dia'], df_sim['ETo_mm'], color='tab:gray', linewidth=1.2, label='ETo')
    ax.plot(df_sim['Dia'], df_sim['Etc_mm'], color='tab:green', linewidth=1.4, label='Etc real')
    ax.bar(df_sim['Dia'], df_sim['Riego_mm'], color='tab:blue', alpha=0.55, label='Riego')
    ax.set_xlabel('Dia desde siembra'); ax.set_ylabel('mm/dia')
    ax.set_title(f'Escenario {escenario} - Evapotranspiracion y riego')
    ax.grid(True, alpha=0.3); ax.legend(loc='best', fontsize=8)
    fig.tight_layout()
    buf = io.BytesIO(); fig.savefig(buf, format='png', dpi=95); plt.close(fig)
    out['et'] = base64.b64encode(buf.getvalue()).decode('ascii')

    # --- Calendario de riego ---
    import numpy as np
    dias        = df_sim['Dia'].values
    canal_riego = df_sim['Canal_Riego_m3'].values
    canal_est   = df_sim['Canal_Estanque_m3'].values
    perdida_c   = df_sim['Perdida_m3'].values
    aplicado    = df_sim['Aplicado_m3'].values
    sub_usado   = df_sim['Subterranea_Usada_m3'].values
    est_usado   = np.maximum(0.0, aplicado - canal_riego - sub_usado)

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 5.5), sharex=True)
    fig.subplots_adjust(hspace=0.08)

    # Panel 1: llegada de agua por canal
    canal_tot = canal_riego + canal_est + perdida_c
    mask_c = canal_tot > 0.01
    dc = dias[mask_c]
    ax1.bar(dc, canal_riego[mask_c],  color='#1565c0', label='Riego directo', alpha=0.88, width=0.8)
    ax1.bar(dc, canal_est[mask_c],   bottom=canal_riego[mask_c],
            color='#90caf9', label='Almacenado (estanque)', alpha=0.88, width=0.8)
    ax1.bar(dc, perdida_c[mask_c],
            bottom=(canal_riego + canal_est)[mask_c],
            color='#ef9a9a', label='Perdida (desborde)', alpha=0.88, width=0.8)
    ax1.set_ylabel('m\u00b3 / dia')
    ax1.set_title(f'Escenario {escenario} \u2014 Calendario de riego')
    ax1.legend(fontsize=8, loc='upper right', ncol=3)
    ax1.grid(axis='y', alpha=0.25)
    ax1.set_ylim(bottom=0)
    ax1.tick_params(labelbottom=False)
    ax1.text(0.01, 0.97, 'Llegada por canal', transform=ax1.transAxes,
             fontsize=8, color='#1565c0', va='top', style='italic')

    # Panel 2: agua aplicada por fuente
    mask_a = aplicado > 0.01
    da = dias[mask_a]
    ax2.bar(da, canal_riego[mask_a], color='#1565c0', label='Del canal', alpha=0.88, width=0.8)
    ax2.bar(da, est_usado[mask_a], bottom=canal_riego[mask_a],
            color='#388e3c', label='Del estanque', alpha=0.88, width=0.8)
    ax2.bar(da, sub_usado[mask_a], bottom=(canal_riego + est_usado)[mask_a],
            color='#e65100', label='Subterr\u00e1neo', alpha=0.88, width=0.8)
    ax2.set_ylabel('m\u00b3 / dia')
    ax2.set_xlabel('D\u00eda desde siembra')
    ax2.legend(fontsize=8, loc='upper right', ncol=3)
    ax2.grid(axis='y', alpha=0.25)
    ax2.set_ylim(bottom=0)
    ax2.text(0.01, 0.97, 'Agua aplicada al cultivo', transform=ax2.transAxes,
             fontsize=8, color='#388e3c', va='top', style='italic')

    buf = io.BytesIO(); fig.savefig(buf, format='png', dpi=95); plt.close(fig)
    out['calendario'] = base64.b64encode(buf.getvalue()).decode('ascii')
    return out
