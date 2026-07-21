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
PANEL_BG  = "#161b22"


def make_node(label, color, r=0.58):
    circ = Circle(radius=r, color=color,
                  fill_color=PANEL_BG, fill_opacity=1, stroke_width=2.8)
    txt  = Text(label, font_size=16, color=color, weight=BOLD)
    txt.move_to(circ.get_center())
    return VGroup(circ, txt)


class EscenaDinamicaSistemas(Scene):
    def construct(self):
        self.camera.background_color = FONDO

        # ── Título ─────────────────────────────────────────────────────────
        titulo = Text(
            "Dinámica de Sistemas",
            font_size=40, color=BLANCO, weight=BOLD,
        )
        titulo.to_edge(UP, buff=0.42)
        self.play(Write(titulo), run_time=1.0)
        self.wait(0.2)

        # ── Subtítulo ──────────────────────────────────────────────────────
        sub = Text(
            "El modelo cruza la información del agricultor,\n"
            "el canal y su regulación.",
            font_size=22, color=GRIS, line_spacing=1.3,
        )
        sub.next_to(titulo, DOWN, buff=0.28)
        self.play(FadeIn(sub), run_time=0.8)
        self.wait(0.4)

        # ── Nodos fuente ───────────────────────────────────────────────────
        n_agr = make_node("Agricultor",        VERDE)
        n_can = make_node("Canal",             CELESTE)
        n_dsm = make_node("Desmarque\nactual", AMBAR)

        n_agr.move_to([-4.2,  1.4, 0])
        n_can.move_to([-4.2,  0.0, 0])
        n_dsm.move_to([-4.2, -1.4, 0])

        # Nodo central Simulación
        sim_circ = Circle(radius=0.78, color=BLANCO,
                          fill_color=PANEL_BG, fill_opacity=1, stroke_width=3)
        sim_circ.move_to([0.4, 0.0, 0])
        sim_lbl = Text("Simulación", font_size=18, color=BLANCO, weight=BOLD)
        sim_lbl.move_to(sim_circ.get_center())
        g_sim = VGroup(sim_circ, sim_lbl)

        # Flechas fuente → simulación
        def arr(src, col):
            return Arrow(
                src.get_right(), g_sim.get_left(),
                color=col, buff=0.08,
                stroke_width=2.5,
                max_tip_length_to_length_ratio=0.14,
            )

        a_agr = arr(n_agr, VERDE)
        a_can = arr(n_can, CELESTE)
        a_dsm = arr(n_dsm, AMBAR)

        for n, a in [(n_agr, a_agr), (n_can, a_can), (n_dsm, a_dsm)]:
            self.play(GrowFromCenter(n), run_time=0.5)
            self.play(GrowArrow(a), run_time=0.45)

        self.play(GrowFromCenter(g_sim), run_time=0.7)
        self.wait(1.0)

        # ── Parte 2 – Incertidumbre septiembre ────────────────────────────
        self.play(FadeOut(sub), run_time=0.45)

        txt2 = Text(
            "Pero existe otra fuente de incertidumbre.",
            font_size=23, color=GRIS,
        )
        txt2.next_to(titulo, DOWN, buff=0.28)
        self.play(FadeIn(txt2), run_time=0.7)
        self.wait(0.35)

        # Badge "Septiembre"
        b_rect = RoundedRectangle(
            width=2.3, height=0.62, corner_radius=0.14,
            color=AMBAR, fill_color=AMBAR, fill_opacity=0.15, stroke_width=2.2,
        ).move_to([0.4, -2.55, 0])
        b_txt = Text("Septiembre", font_size=20, color=AMBAR, weight=BOLD)
        b_txt.move_to(b_rect.get_center())
        badge = VGroup(b_rect, b_txt)

        txt3 = Text(
            "Para cosechas cercanas a septiembre\n"
            "la simulación necesita conocer\n"
            "el desmarque del siguiente período.",
            font_size=18, color=GRIS, line_spacing=1.25,
        )
        txt3.next_to(badge, DOWN, buff=0.28)

        self.play(FadeIn(badge), run_time=0.6)
        self.play(FadeIn(txt3), run_time=0.9)
        self.wait(0.7)

        # Nodo "?" a la derecha del modelo
        fut_circ = Circle(radius=0.62, color=ROJO,
                          fill_color=PANEL_BG, fill_opacity=1, stroke_width=2.8)
        fut_circ.move_to([3.1, 0.0, 0])
        fut_q = Text("?", font_size=44, color=ROJO, weight=BOLD)
        fut_q.move_to(fut_circ.get_center())
        g_fut = VGroup(fut_circ, fut_q)

        fut_cap = Text(
            "Desmarque\nsiguiente período",
            font_size=15, color=ROJO, line_spacing=1.2,
        )
        fut_cap.next_to(g_fut, DOWN, buff=0.22)

        # Flecha punteada sim → ?
        a_fut = Arrow(
            g_sim.get_right(), g_fut.get_left(),
            color=ROJO, buff=0.08,
            stroke_width=2.5,
            max_tip_length_to_length_ratio=0.15,
        )

        self.play(GrowArrow(a_fut), run_time=0.55)
        self.play(GrowFromCenter(g_fut), FadeIn(fut_cap), run_time=0.75)

        # Pulso de alerta
        pulse = fut_circ.copy().set_stroke(color=ROJO, opacity=0.0)
        self.play(
            fut_circ.copy().animate.scale(1.45).set_stroke(opacity=0),
            run_time=0.9, rate_func=there_and_back,
        )
        self.wait(2.2)

        # ── Fade final ─────────────────────────────────────────────────────
        self.play(
            FadeOut(VGroup(
                titulo, txt2, txt3, badge,
                n_agr, n_can, n_dsm,
                a_agr, a_can, a_dsm,
                g_sim, a_fut, g_fut, fut_cap,
            )),
            run_time=1.0,
        )
