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
ROJO      = "#e53935"
NARANJA   = "#fb8c00"
AZUL_CLAR = "#29b6f6"
AZUL_PALE = "#81d4fa"
PANEL_BG  = "#161b22"

# (índice, etiqueta, color, multiplicador de caudal)
ESCENARIOS = [
    (-2, "E−2", ROJO,      0.55),
    (-1, "E−1", NARANJA,   0.75),
    ( 0, "E 0", CELESTE,   1.00),
    (+1, "E+1", AZUL_CLAR, 1.25),
    (+2, "E+2", AZUL_PALE, 1.50),
]


class EscenaCalendarios(Scene):
    def construct(self):
        self.camera.background_color = FONDO

        # ── Datos diarios base (patrón realista) ───────────────────────────
        DAYS = 15
        base = np.array([
            4 + 3 * math.sin(i / 3.5) + 1.5 * math.cos(i / 2.2) + 3
            for i in range(DAYS)
        ])
        base    = np.clip(base, 0.8, None)
        max_val = base.max() * 1.55   # escala consistente entre paneles

        # ── Layout ─────────────────────────────────────────────────────────
        XS     = [-4.5, -2.25, 0.0, 2.25, 4.5]
        PW     = 2.0
        PH     = 3.0
        BASE_Y = 0.2
        HDR_H  = 0.45

        chart_h  = PH - HDR_H - 0.3
        chart_y0 = BASE_Y - PH / 2 + 0.15   # fondo del área de barras
        bar_w    = (PW - 0.22) / DAYS

        # ── Título ─────────────────────────────────────────────────────────
        titulo = Text(
            "Resultado: 5 Calendarios de Oferta Hídrica",
            font_size=34, color=BLANCO, weight=BOLD,
        )
        titulo.to_edge(UP, buff=0.45)
        self.play(Write(titulo), run_time=1.0)

        # ── Narración ──────────────────────────────────────────────────────
        txt = Text(
            "El resultado son 5 calendarios que indican al agricultor\n"
            "cuánta agua tendrá disponible día a día.",
            font_size=21, color=GRIS, line_spacing=1.3,
        )
        txt.next_to(titulo, DOWN, buff=0.3)
        self.play(FadeIn(txt), run_time=0.9)
        self.wait(0.5)

        # ── Construir paneles ──────────────────────────────────────────────
        panels = []
        for idx, (num, lbl, col, mult) in enumerate(ESCENARIOS):
            xp   = XS[idx]
            vals = base * mult

            bg = Rectangle(
                width=PW, height=PH,
                color=GRIS_LINE,
                fill_color=PANEL_BG, fill_opacity=1,
                stroke_width=1.5,
            ).move_to([xp, BASE_Y, 0])

            hdr = Rectangle(
                width=PW, height=HDR_H,
                color=col, fill_color=col, fill_opacity=0.9,
                stroke_width=0,
            ).move_to([xp, BASE_Y + PH / 2 - HDR_H / 2, 0])

            hdr_txt = Text(lbl, font_size=20, color=FONDO, weight=BOLD)
            hdr_txt.move_to(hdr.get_center())

            bars = []
            for d in range(DAYS):
                bh = max((vals[d] / max_val) * chart_h, 0.02)
                bx = xp - PW / 2 + 0.11 + bar_w / 2 + d * bar_w
                b = Rectangle(
                    width=bar_w * 0.68, height=bh,
                    color=col, fill_color=col, fill_opacity=0.82,
                    stroke_width=0,
                ).move_to([bx, chart_y0 + bh / 2, 0])
                bars.append(b)

            panels.append((bg, hdr, hdr_txt, bars))

        # ── Animar en orden narrativo: E0 → E+1 → E+2 → E−1 → E−2 ────────
        order        = [2, 3, 4, 1, 0]
        all_bar_mobs = []

        for i in order:
            bg, hdr, hdr_txt, bars = panels[i]
            self.play(FadeIn(bg), FadeIn(hdr), Write(hdr_txt), run_time=0.5)
            self.play(
                LaggedStart(
                    *[GrowFromEdge(b, DOWN) for b in bars],
                    lag_ratio=0.08,
                ),
                run_time=0.8,
            )
            all_bar_mobs.extend([bg, hdr, hdr_txt] + bars)

        self.wait(0.8)

        # ── Línea escáner "día a día" recorre el panel E0 ─────────────────
        xp0     = XS[2]
        x_start = xp0 - PW / 2 + 0.11
        x_end   = xp0 + PW / 2 - 0.11

        scan = Line(
            [x_start, chart_y0, 0],
            [x_start, chart_y0 + chart_h + 0.1, 0],
            color=AMBAR, stroke_width=2.8,
        )
        scan_end = scan.copy().shift(RIGHT * (x_end - x_start))

        lbl_dia = Text("día a día →", font_size=17, color=AMBAR)
        lbl_dia.move_to([xp0, BASE_Y - PH / 2 - 0.38, 0])

        self.play(Create(scan), FadeIn(lbl_dia), run_time=0.4)
        self.play(Transform(scan, scan_end), run_time=1.4, rate_func=linear)
        self.play(FadeOut(scan), FadeOut(lbl_dia), run_time=0.4)

        # ── Cierre ─────────────────────────────────────────────────────────
        cierre = Text(
            "5 calendarios distintos de oferta hídrica.",
            font_size=26, color=BLANCO, weight=BOLD,
        )
        cierre.to_edge(DOWN, buff=0.45)
        self.play(Write(cierre), run_time=1.1)
        self.wait(2.5)

        self.play(
            FadeOut(VGroup(titulo, txt, cierre, *all_bar_mobs)),
            run_time=1.0,
        )
