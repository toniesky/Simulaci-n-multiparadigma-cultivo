from manim import *

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
MARRON    = "#8d6e63"
PANEL_BG  = "#161b22"

# Colores para las capas del triángulo textural (simplificado como barra)
C_ARENA   = "#f5c842"
C_LIMO    = "#a5d6a7"
C_ARCILLA = "#ef9a9a"


class EscenaSuelo(Scene):
    def construct(self):
        self.camera.background_color = FONDO

        # ── Título ─────────────────────────────────────────────────────────
        titulo = Text(
            "Caracterización del Suelo",
            font_size=38, color=BLANCO, weight=BOLD,
        )
        titulo.to_edge(UP, buff=0.42)
        self.play(Write(titulo), run_time=1.0)

        txt1 = Text(
            "Estudios de laboratorio determinan\n"
            "las propiedades físicas del suelo.",
            font_size=21, color=GRIS, line_spacing=1.3,
        )
        txt1.next_to(titulo, DOWN, buff=0.28)
        self.play(FadeIn(txt1), run_time=0.8)
        self.wait(0.3)

        # ────────────────────────────────────────────────────────────────────
        # PARTE 1 – PMP, CC y textura
        # ────────────────────────────────────────────────────────────────────

        # --- Barra de humedad: PMP y CC sobre eje -------------------------
        BAR_W = 5.6
        BAR_H = 0.62
        BAR_Y = -0.3
        BAR_X = -1.5

        # Zona de agua disponible (entre PMP y CC)
        PMP_PCT = 0.28    # 28% del eje
        CC_PCT  = 0.70    # 70% del eje

        bar_bg = Rectangle(
            width=BAR_W, height=BAR_H,
            color=GRIS_LINE, fill_color=GRIS_LINE, fill_opacity=0.22,
            stroke_width=1.5,
        ).move_to([BAR_X, BAR_Y, 0])

        # Zona no disponible (izquierda de PMP)
        w_nd = BAR_W * PMP_PCT
        seg_nd = Rectangle(
            width=w_nd, height=BAR_H,
            color=ROJO, fill_color=ROJO, fill_opacity=0.55, stroke_width=0,
        ).move_to([BAR_X - BAR_W / 2 + w_nd / 2, BAR_Y, 0])

        # Zona disponible (entre PMP y CC)
        w_d = BAR_W * (CC_PCT - PMP_PCT)
        seg_d = Rectangle(
            width=w_d, height=BAR_H,
            color=CELESTE, fill_color=CELESTE, fill_opacity=0.55, stroke_width=0,
        ).move_to([BAR_X - BAR_W / 2 + w_nd + w_d / 2, BAR_Y, 0])

        # Zona sobre CC (gravitacional)
        w_grav = BAR_W * (1 - CC_PCT)
        seg_grav = Rectangle(
            width=w_grav, height=BAR_H,
            color=GRIS, fill_color=GRIS, fill_opacity=0.35, stroke_width=0,
        ).move_to([BAR_X - BAR_W / 2 + w_nd + w_d + w_grav / 2, BAR_Y, 0])

        # Marcas PMP y CC
        x_pmp = BAR_X - BAR_W / 2 + w_nd
        x_cc  = BAR_X - BAR_W / 2 + w_nd + w_d

        line_pmp = DashedLine(
            [x_pmp, BAR_Y - BAR_H * 0.8, 0], [x_pmp, BAR_Y + BAR_H * 0.8, 0],
            color=ROJO, stroke_width=2.5, dash_length=0.1,
        )
        line_cc = DashedLine(
            [x_cc, BAR_Y - BAR_H * 0.8, 0], [x_cc, BAR_Y + BAR_H * 0.8, 0],
            color=VERDE, stroke_width=2.5, dash_length=0.1,
        )

        lbl_pmp = Text("PMP", font_size=16, color=ROJO, weight=BOLD)
        lbl_pmp.next_to(line_pmp, DOWN, buff=0.18)
        lbl_cc = Text("CC", font_size=16, color=VERDE, weight=BOLD)
        lbl_cc.next_to(line_cc, DOWN, buff=0.18)

        lbl_nd  = Text("No disponible", font_size=13, color=ROJO)
        lbl_nd.move_to([BAR_X - BAR_W / 2 + w_nd / 2, BAR_Y + BAR_H * 0.85, 0])
        lbl_disp = Text("Agua disponible", font_size=13, color=CELESTE)
        lbl_disp.move_to([BAR_X - BAR_W / 2 + w_nd + w_d / 2, BAR_Y + BAR_H * 0.85, 0])

        self.play(FadeIn(bar_bg), run_time=0.4)
        self.play(
            GrowFromEdge(seg_nd, LEFT),
            GrowFromEdge(seg_d, LEFT),
            GrowFromEdge(seg_grav, LEFT),
            run_time=1.0,
        )
        self.play(
            Create(line_pmp), Create(line_cc),
            FadeIn(lbl_pmp), FadeIn(lbl_cc),
            FadeIn(lbl_nd), FadeIn(lbl_disp),
            run_time=0.7,
        )
        self.wait(0.5)

        # --- Triángulo textural simplificado (barra apilada) ---------------
        TBAR_W = 2.8
        TBAR_H = 0.55
        TBAR_X = 4.0
        TBAR_Y = BAR_Y

        fracs = [("Arena\n55%", 0.55, C_ARENA),
                 ("Limo\n30%",  0.30, C_LIMO),
                 ("Arcilla\n15%", 0.15, C_ARCILLA)]

        tbg = Rectangle(
            width=TBAR_W, height=TBAR_H,
            color=GRIS_LINE, fill_color=GRIS_LINE, fill_opacity=0.18,
            stroke_width=1.5,
        ).move_to([TBAR_X, TBAR_Y, 0])

        tcap = Text("Textura del suelo", font_size=15, color=GRIS)
        tcap.next_to(tbg, UP, buff=0.45)

        self.play(FadeIn(tbg), FadeIn(tcap), run_time=0.4)

        tx_cursor = TBAR_X - TBAR_W / 2
        t_segs = []
        t_lbls = []
        for lbl_str, frac, col in fracs:
            sw = TBAR_W * frac
            seg = Rectangle(
                width=sw, height=TBAR_H,
                color=col, fill_color=col, fill_opacity=0.85, stroke_width=0,
            ).move_to([tx_cursor + sw / 2, TBAR_Y, 0])
            lbl = Text(lbl_str, font_size=11, color=col, line_spacing=1.0)
            lbl.next_to(seg, DOWN, buff=0.15)
            t_segs.append(seg)
            t_lbls.append(lbl)
            tx_cursor += sw

        self.play(
            LaggedStart(*[GrowFromEdge(s, LEFT) for s in t_segs], lag_ratio=0.25),
            run_time=0.9,
        )
        self.play(*[FadeIn(l) for l in t_lbls], run_time=0.4)
        self.wait(0.5)

        # Clasificación
        clasif_r = RoundedRectangle(
            width=2.5, height=0.6, corner_radius=0.14,
            color=MARRON, fill_color=MARRON, fill_opacity=0.18, stroke_width=2,
        ).move_to([TBAR_X, TBAR_Y - 1.35, 0])
        clasif_t = Text("Franco Arenoso", font_size=17, color=MARRON, weight=BOLD)
        clasif_t.move_to(clasif_r.get_center())
        clasif_cap = Text("Clasificación:", font_size=14, color=GRIS)
        clasif_cap.next_to(clasif_r, UP, buff=0.14)

        arr_clas = Arrow(
            tbg.get_bottom(), clasif_r.get_top(),
            color=MARRON, buff=0.06, stroke_width=2,
            max_tip_length_to_length_ratio=0.18,
        )
        self.play(GrowArrow(arr_clas), run_time=0.4)
        self.play(FadeIn(clasif_r), Write(clasif_t), FadeIn(clasif_cap), run_time=0.6)
        self.wait(1.2)

        # Limpiar toda la parte 1 antes de pasar a FAO-56
        parte1 = VGroup(
            bar_bg, seg_nd, seg_d, seg_grav,
            line_pmp, line_cc, lbl_pmp, lbl_cc, lbl_nd, lbl_disp,
            tbg, tcap, *t_segs, *t_lbls,
            arr_clas, clasif_r, clasif_t, clasif_cap,
            txt1,
        )
        self.play(FadeOut(parte1), run_time=0.8)
        self.wait(0.2)

        # ────────────────────────────────────────────────────────────────────
        # PARTE 2 – FAO-56 y los 3 parámetros
        # ────────────────────────────────────────────────────────────────────
        self.play(FadeOut(txt1), run_time=0.35)
        txt2 = Text(
            "Recurriendo al manual FAO-56 se obtienen\n"
            "los parámetros fundamentales del balance hídrico.",
            font_size=20, color=GRIS, line_spacing=1.3,
        )
        txt2.next_to(titulo, DOWN, buff=0.28)
        self.play(FadeIn(txt2), run_time=0.8)
        self.wait(0.3)

        # Badge FAO-56
        fao_r = RoundedRectangle(
            width=2.1, height=0.72, corner_radius=0.16,
            color=AMBAR, fill_color=AMBAR, fill_opacity=0.14, stroke_width=2.5,
        ).move_to([-4.3, -1.5, 0])
        fao_t = Text("FAO-56", font_size=24, color=AMBAR, weight=BOLD)
        fao_t.move_to(fao_r.get_center())
        g_fao = VGroup(fao_r, fao_t)
        self.play(FadeIn(fao_r), Write(fao_t), run_time=0.7)

        # Los 3 parámetros
        params = [
            ("AFE",  "Agua Fácilmente\nEvaporable",   CELESTE, [-0.8, -1.5, 0]),
            ("AET",  "Agua Evaporable\nTotal",         VERDE,   [ 1.8, -1.5, 0]),
            ("ADZR", "Agua Disponible\nZona Radicular",NARANJA, [ 4.5, -1.5, 0]),
        ]

        g_params = []
        for sigla, desc, col, pos in params:
            circ = Circle(radius=0.52, color=col,
                          fill_color=PANEL_BG, fill_opacity=1, stroke_width=2.5)
            sig_t = Text(sigla, font_size=18, color=col, weight=BOLD)
            sig_t.move_to(circ.get_center())
            desc_t = Text(desc, font_size=13, color=GRIS, line_spacing=1.15)
            desc_t.next_to(circ, DOWN, buff=0.22)
            g = VGroup(circ, sig_t, desc_t)
            g.move_to(pos)
            g_params.append(g)

            arr = Arrow(
                fao_r.get_right(), circ.get_left(),
                color=col, buff=0.06, stroke_width=2,
                max_tip_length_to_length_ratio=0.16,
            )
            self.play(GrowArrow(arr), run_time=0.4)
            self.play(GrowFromCenter(VGroup(circ, sig_t)), FadeIn(desc_t), run_time=0.6)

        self.wait(2.0)

        # ── Fade final ─────────────────────────────────────────────────────
        all_mobs = VGroup(titulo, txt2, g_fao, *g_params)
        self.play(FadeOut(all_mobs), run_time=1.0)
