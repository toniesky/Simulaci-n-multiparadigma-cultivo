from manim import *
import numpy as np
import math

# ── Paleta ──────────────────────────────────────────────────────────────────
FONDO     = "#0d1117"
BLANCO    = "#f0f4f8"
CELESTE   = "#42c4f5"
AMBAR     = "#f9a825"
GRIS      = "#8b9ab0"
GRIS_LINE = "#4a5568"
VERDE     = "#4caf50"
ROJO      = "#e53935"
NARANJA   = "#fb8c00"
PANEL_BG  = "#161b22"
AZUL_CLAR = "#29b6f6"

DAYS = 18


def mini_calendar(color, mult=1.0, bar_w_total=1.7, bar_h_max=1.15, days=DAYS):
    """Mini gráfico de barras representando un calendario de oferta."""
    base = np.array([
        3 + 2 * math.sin(i / 3.0) + 1.2 * math.cos(i / 2.0) + 2
        for i in range(days)
    ])
    base   = np.clip(base * mult, 0.1, None)
    mx     = base.max()
    bw     = bar_w_total / days
    bars   = VGroup()
    for d, v in enumerate(base):
        bh = (v / mx) * bar_h_max
        bx = -bar_w_total / 2 + bw / 2 + d * bw
        b  = Rectangle(
            width=bw * 0.72, height=bh,
            color=color, fill_color=color, fill_opacity=0.85,
            stroke_width=0,
        ).move_to([bx, bh / 2 - 0.0, 0])
        bars.add(b)
    return bars


class EscenaSimulacion(Scene):
    def construct(self):
        self.camera.background_color = FONDO

        # ────────────────────────────────────────────────────────────────────
        # TÍTULO
        # ────────────────────────────────────────────────────────────────────
        titulo = Text(
            "La Simulación",
            font_size=42, color=BLANCO, weight=BOLD,
        )
        titulo.to_edge(UP, buff=0.42)
        self.play(Write(titulo), run_time=1.0)
        self.wait(0.2)

        # ────────────────────────────────────────────────────────────────────
        # PARTE 1 – Tomar combinación + calendario de oferta
        # ────────────────────────────────────────────────────────────────────
        txt1 = Text(
            "El modelo toma cada combinación y,\n"
            "usando el calendario del escenario correspondiente,\n"
            "calcula día a día el balance hídrico.",
            font_size=20, color=GRIS, line_spacing=1.3,
        )
        txt1.next_to(titulo, DOWN, buff=0.3)
        self.play(FadeIn(txt1), run_time=0.9)
        self.wait(0.4)

        # Calendario miniatura (E0, celeste)
        cal_bg = Rectangle(
            width=2.1, height=1.6,
            color=GRIS_LINE, fill_color=PANEL_BG, fill_opacity=1,
            stroke_width=1.5,
        ).move_to([-4.1, -0.75, 0])

        cal_hdr = Rectangle(
            width=2.1, height=0.38,
            color=CELESTE, fill_color=CELESTE, fill_opacity=0.9,
            stroke_width=0,
        ).move_to([-4.1, -0.75 + 0.61, 0])
        cal_hdr_t = Text("E 0", font_size=16, color=FONDO, weight=BOLD)
        cal_hdr_t.move_to(cal_hdr.get_center())

        cal_bars = mini_calendar(CELESTE, mult=1.0)
        cal_bars.move_to([-4.1, -0.75 - 0.25, 0])

        g_cal = VGroup(cal_bg, cal_hdr, cal_hdr_t, cal_bars)

        self.play(FadeIn(cal_bg), FadeIn(cal_hdr), Write(cal_hdr_t), run_time=0.5)
        self.play(
            LaggedStart(*[GrowFromEdge(b, DOWN) for b in cal_bars], lag_ratio=0.06),
            run_time=0.9,
        )

        # Flecha → bloque "Balance hídrico"
        bloque_rect = RoundedRectangle(
            width=2.3, height=0.72, corner_radius=0.16,
            color=CELESTE, fill_color=PANEL_BG, fill_opacity=1,
            stroke_width=2.2,
        ).move_to([-0.7, -0.75, 0])
        bloque_txt = Text("Balance\nhídrico", font_size=18, color=CELESTE, weight=BOLD,
                          line_spacing=1.1)
        bloque_txt.move_to(bloque_rect.get_center())
        g_bloque = VGroup(bloque_rect, bloque_txt)

        arr1 = Arrow(
            cal_bg.get_right(), bloque_rect.get_left(),
            color=CELESTE, buff=0.08,
            stroke_width=2.5, max_tip_length_to_length_ratio=0.14,
        )
        self.play(GrowArrow(arr1), run_time=0.5)
        self.play(FadeIn(bloque_rect), Write(bloque_txt), run_time=0.6)

        # Contador de días (ticker)
        dia_lbl = Text("Día 1", font_size=20, color=AMBAR)
        dia_lbl.next_to(g_bloque, DOWN, buff=0.28)

        self.play(FadeIn(dia_lbl), run_time=0.3)
        for d in [5, 10, 15, DAYS]:
            new_lbl = Text(f"Día {d}", font_size=20, color=AMBAR)
            new_lbl.move_to(dia_lbl.get_center())
            self.play(Transform(dia_lbl, new_lbl), run_time=0.22)
        self.wait(0.6)

        # ────────────────────────────────────────────────────────────────────
        # PARTE 2 – Humedad del suelo + estrés hídrico
        # ────────────────────────────────────────────────────────────────────
        self.play(FadeOut(txt1), run_time=0.4)
        txt2 = Text(
            "Se estima la humedad del suelo\n"
            "y el estrés hídrico de cada partición.",
            font_size=20, color=GRIS, line_spacing=1.3,
        )
        txt2.next_to(titulo, DOWN, buff=0.3)
        self.play(FadeIn(txt2), run_time=0.8)

        # Gauge de humedad (barra vertical)
        GAUGE_H = 2.2
        gauge_bg = Rectangle(
            width=0.52, height=GAUGE_H,
            color=GRIS_LINE, fill_color=PANEL_BG, fill_opacity=1,
            stroke_width=2,
        ).move_to([1.8, -0.75, 0])

        # Nivel inicial alto → baja con el tiempo
        def make_gauge_fill(pct, color):
            h = GAUGE_H * pct
            r = Rectangle(
                width=0.52, height=h,
                color=color, fill_color=color, fill_opacity=0.85,
                stroke_width=0,
            )
            r.move_to([1.8, -0.75 - GAUGE_H / 2 + h / 2, 0])
            return r

        gauge_fill = make_gauge_fill(0.80, VERDE)
        gauge_lbl  = Text("Humedad\ndel suelo", font_size=14, color=GRIS,
                          line_spacing=1.1)
        gauge_lbl.next_to(gauge_bg, DOWN, buff=0.18)
        gauge_pct  = Text("80%", font_size=16, color=VERDE)
        gauge_pct.next_to(gauge_bg, UP, buff=0.12)

        arr2 = Arrow(
            bloque_rect.get_right(), gauge_bg.get_left(),
            color=GRIS, buff=0.08,
            stroke_width=2, max_tip_length_to_length_ratio=0.14,
        )
        self.play(GrowArrow(arr2), run_time=0.45)
        self.play(FadeIn(gauge_bg), FadeIn(gauge_fill),
                  FadeIn(gauge_lbl), FadeIn(gauge_pct), run_time=0.6)

        # Bajar nivel → estrés
        gauge_fill2 = make_gauge_fill(0.28, NARANJA)
        pct2 = Text("28%", font_size=16, color=NARANJA)
        pct2.move_to(gauge_pct.get_center())

        self.play(
            Transform(gauge_fill, gauge_fill2),
            Transform(gauge_pct, pct2),
            run_time=1.2, rate_func=linear,
        )

        # Estrés hídrico badge
        stress_r = RoundedRectangle(
            width=2.0, height=0.6, corner_radius=0.14,
            color=ROJO, fill_color=ROJO, fill_opacity=0.15,
            stroke_width=2.2,
        ).move_to([3.6, -0.75, 0])
        stress_t = Text("¡Estrés\nhídrico!", font_size=17, color=ROJO, weight=BOLD,
                        line_spacing=1.1)
        stress_t.move_to(stress_r.get_center())
        g_stress = VGroup(stress_r, stress_t)

        arr3 = Arrow(
            gauge_bg.get_right(), stress_r.get_left(),
            color=ROJO, buff=0.08,
            stroke_width=2.5, max_tip_length_to_length_ratio=0.14,
        )
        self.play(GrowArrow(arr3), run_time=0.4)
        self.play(FadeIn(stress_r), Write(stress_t), run_time=0.6)
        self.wait(1.2)

        # ────────────────────────────────────────────────────────────────────
        # PARTE 3 – Estándar de calidad
        # ────────────────────────────────────────────────────────────────────
        self.play(FadeOut(txt2), run_time=0.4)
        txt3 = Text(
            "Ese estrés determina la distribución\n"
            "del estándar de calidad de la cosecha.",
            font_size=20, color=GRIS, line_spacing=1.3,
        )
        txt3.next_to(titulo, DOWN, buff=0.3)
        self.play(FadeIn(txt3), run_time=0.8)
        self.wait(0.5)

        # Barra apilada horizontal: 1ª calidad / 2ª calidad / pérdidas
        PCTS   = [0.55, 0.30, 0.15]    # primera, segunda, pérdida
        COLORS = [VERDE, AMBAR, ROJO]
        LABELS = ["1ª calidad", "2ª calidad", "Pérdidas"]
        BAR_W  = 5.8
        BAR_H  = 0.72
        BAR_Y  = -2.45
        BAR_X0 = -BAR_W / 2

        # Fondo de la barra
        bar_bg = Rectangle(
            width=BAR_W, height=BAR_H,
            color=GRIS_LINE, fill_color=GRIS_LINE, fill_opacity=0.25,
            stroke_width=1.5,
        ).move_to([0, BAR_Y, 0])
        self.play(FadeIn(bar_bg), run_time=0.4)

        x_cursor = BAR_X0
        seg_mobs = []
        for pct, col, lbl_str in zip(PCTS, COLORS, LABELS):
            sw  = BAR_W * pct
            seg = Rectangle(
                width=sw, height=BAR_H,
                color=col, fill_color=col, fill_opacity=0.85,
                stroke_width=0,
            ).move_to([x_cursor + sw / 2, BAR_Y, 0])

            pct_t = Text(f"{int(pct*100)}%", font_size=17, color=FONDO, weight=BOLD)
            pct_t.move_to(seg.get_center())

            lbl = Text(lbl_str, font_size=14, color=col)
            lbl.next_to(seg, DOWN, buff=0.22)

            self.play(GrowFromEdge(seg, LEFT), run_time=0.7)
            self.play(FadeIn(pct_t), FadeIn(lbl), run_time=0.3)
            x_cursor += sw
            seg_mobs.extend([seg, pct_t, lbl])

        self.wait(1.0)

        # Flecha de estrés → barra calidad
        arr4 = Arrow(
            g_stress.get_bottom(),
            [g_stress.get_center()[0], bar_bg.get_top()[1] + 0.05, 0],
            color=ROJO, buff=0.08,
            stroke_width=2.5, max_tip_length_to_length_ratio=0.14,
        )
        self.play(GrowArrow(arr4), run_time=0.5)
        self.wait(2.0)

        # ── Fade final ─────────────────────────────────────────────────────
        self.play(
            FadeOut(VGroup(
                titulo, txt3,
                g_cal, arr1, g_bloque, dia_lbl,
                arr2, gauge_bg, gauge_fill, gauge_lbl, gauge_pct,
                arr3, g_stress, arr4,
                bar_bg, *seg_mobs,
            )),
            run_time=1.1,
        )
