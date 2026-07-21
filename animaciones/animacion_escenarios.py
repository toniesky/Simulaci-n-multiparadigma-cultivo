from manim import *

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


class EscenaEscenarios(Scene):
    def construct(self):
        self.camera.background_color = FONDO

        # ── Título ──────────────────────────────────────────────────────────
        titulo = Text(
            "Generación de Escenarios de Desmarque",
            font_size=36, color=BLANCO, weight=BOLD,
        )
        titulo.to_edge(UP, buff=0.45)
        self.play(Write(titulo), run_time=1.2)
        self.wait(0.3)

        # ────────────────────────────────────────────────────────────────────
        # PARTE 1 – Predicción vs. realidad
        # ────────────────────────────────────────────────────────────────────
        txt1 = Text(
            "Sin embargo, toda predicción tiene un error.",
            font_size=24, color=GRIS,
        )
        txt1.next_to(titulo, DOWN, buff=0.35)
        self.play(FadeIn(txt1), run_time=0.8)
        self.wait(0.5)

        MAX_VAL = 20
        SCALE   = 3.0        # altura máxima en unidades Manim
        BASE_Y  = -1.85
        BAR_W   = 1.3

        def bh(v):
            return (v / MAX_VAL) * SCALE

        # --- Barra "Predicho" (celeste, 15) ---------------------------------
        h15 = bh(15)
        bar_pred = Rectangle(
            width=BAR_W, height=h15,
            color=CELESTE, fill_color=CELESTE, fill_opacity=0.85,
            stroke_width=1.5,
        ).move_to([-1.5, BASE_Y + h15 / 2, 0])

        lbl_p = Text("Predicho", font_size=22, color=BLANCO)
        lbl_p.move_to([-1.5, BASE_Y - 0.4, 0])

        val_p = Text("15", font_size=22, color=CELESTE, weight=BOLD)
        val_p.move_to([-1.5, BASE_Y + h15 + 0.3, 0])

        # --- Barra "Observado" (rojo, 16) -----------------------------------
        h16 = bh(16)
        bar_obs = Rectangle(
            width=BAR_W, height=h16,
            color=ROJO, fill_color=ROJO, fill_opacity=0.85,
            stroke_width=1.5,
        ).move_to([1.5, BASE_Y + h16 / 2, 0])

        lbl_o = Text("Observado", font_size=22, color=BLANCO)
        lbl_o.move_to([1.5, BASE_Y - 0.4, 0])

        val_o = Text("16", font_size=22, color=ROJO, weight=BOLD)
        val_o.move_to([1.5, BASE_Y + h16 + 0.3, 0])

        # Línea base
        eje1 = Line([-4.2, BASE_Y, 0], [4.2, BASE_Y, 0],
                    color=GRIS_LINE, stroke_width=2)
        self.play(Create(eje1), run_time=0.4)

        # Crecer barras desde abajo
        self.play(GrowFromEdge(bar_pred, DOWN), FadeIn(lbl_p), run_time=1.2)
        self.play(FadeIn(val_p), run_time=0.35)
        self.wait(0.25)
        self.play(GrowFromEdge(bar_obs, DOWN), FadeIn(lbl_o), run_time=1.2)
        self.play(FadeIn(val_o), run_time=0.35)

        # Línea de referencia al nivel predicho
        ref_line = DashedLine(
            [-3.8, BASE_Y + h15, 0], [3.8, BASE_Y + h15, 0],
            color=CELESTE, dash_length=0.13, stroke_width=1.5,
        )
        self.play(Create(ref_line), run_time=0.7)

        # Bracket "error" entre la línea predicha y la cima de bar_obs
        mid_y = BASE_Y + (h15 + h16) / 2
        bracket   = Line([2.4, BASE_Y + h15, 0], [2.4, BASE_Y + h16, 0],
                         color=AMBAR, stroke_width=3)
        cap_lo    = Line([2.32, BASE_Y + h15, 0], [2.48, BASE_Y + h15, 0],
                         color=AMBAR, stroke_width=3)
        cap_hi    = Line([2.32, BASE_Y + h16, 0], [2.48, BASE_Y + h16, 0],
                         color=AMBAR, stroke_width=3)
        err_txt   = Text("error", font_size=18, color=AMBAR)
        err_txt.move_to([2.95, mid_y, 0])

        self.play(
            Create(bracket), Create(cap_lo), Create(cap_hi),
            Write(err_txt),
            run_time=0.8,
        )
        self.wait(2.2)

        # Limpiar parte 1
        self.play(
            FadeOut(VGroup(
                eje1, bar_pred, bar_obs,
                lbl_p, lbl_o, val_p, val_o,
                ref_line, bracket, cap_lo, cap_hi, err_txt,
                txt1,
            )),
            run_time=0.8,
        )

        # ────────────────────────────────────────────────────────────────────
        # PARTE 2 – Los 5 escenarios
        # ────────────────────────────────────────────────────────────────────
        txt2 = Text(
            "Para considerar ese error, el modelo crea 5 escenarios.",
            font_size=23, color=GRIS,
        )
        txt2.next_to(titulo, DOWN, buff=0.35)
        self.play(FadeIn(txt2), run_time=0.8)
        self.wait(0.4)

        # (etiqueta, valor_visual, color, descripción)
        escenarios = [
            ("E−2", 10, ROJO,      "−2σ  ·  Pesimista"),
            ("E−1", 12, NARANJA,   "−1σ"),
            ("E 0", 15, CELESTE,   "Valor esperado"),
            ("E+1", 17, AZUL_CLAR, "+1σ"),
            ("E+2", 19, AZUL_PALE, "+2σ  ·  Optimista"),
        ]
        XS      = [-3.6, -1.8, 0.0, 1.8, 3.6]
        BW2     = 1.05
        BASE_Y2 = -1.85

        eje2 = Line([-5.3, BASE_Y2, 0], [5.3, BASE_Y2, 0],
                    color=GRIS_LINE, stroke_width=2)
        self.play(Create(eje2), run_time=0.4)

        # Construir todos los mobjects primero (sin animar)
        esc_mobs = []
        for i, (lbl_text, val, col, desc) in enumerate(escenarios):
            h  = bh(val)
            xp = XS[i]

            bar = Rectangle(
                width=BW2, height=h,
                color=col, fill_color=col, fill_opacity=0.85,
                stroke_width=1.5,
            ).move_to([xp, BASE_Y2 + h / 2, 0])

            nombre = Text(lbl_text, font_size=22, color=col, weight=BOLD)
            nombre.move_to([xp, BASE_Y2 - 0.38, 0])

            desc_t = Text(desc, font_size=13, color=GRIS)
            desc_t.move_to([xp, BASE_Y2 - 0.72, 0])

            val_t = Text(str(val), font_size=17, color=col)
            val_t.move_to([xp, BASE_Y2 + h + 0.27, 0])

            esc_mobs.append((bar, nombre, desc_t, val_t))

        # Animar en orden narrativo: E0 → E+1 → E+2 → E−1 → E−2
        for i in [2, 3, 4, 1, 0]:
            bar, nombre, desc_t, val_t = esc_mobs[i]
            self.play(GrowFromEdge(bar, DOWN), FadeIn(nombre), run_time=0.65)
            self.play(FadeIn(desc_t), FadeIn(val_t), run_time=0.3)

        self.wait(0.8)

        # Resaltar E0 (índice 2)
        bar_e0 = esc_mobs[2][0]
        hl   = SurroundingRectangle(bar_e0, color=CELESTE, buff=0.12, stroke_width=2.5)
        nota = Text("E0 = valor esperado por el modelo",
                    font_size=20, color=CELESTE)
        nota.to_edge(DOWN, buff=0.45)
        self.play(Create(hl), Write(nota), run_time=0.8)
        self.wait(2.0)
        self.play(FadeOut(hl), FadeOut(nota), run_time=0.5)

        # ────────────────────────────────────────────────────────────────────
        # PARTE 3 – Cierre
        # ────────────────────────────────────────────────────────────────────
        self.wait(0.4)
        cierre = Text(
            "Generando así 5 escenarios distintos de oferta hídrica.",
            font_size=26, color=BLANCO, weight=BOLD,
        )
        cierre.to_edge(DOWN, buff=0.55)
        self.play(Write(cierre), run_time=1.2)
        self.wait(2.5)

        # Fade final
        all_mobs = VGroup(
            titulo, txt2, eje2, cierre,
            *[mo for grp in esc_mobs for mo in grp],
        )
        self.play(FadeOut(all_mobs), run_time=1.0)
