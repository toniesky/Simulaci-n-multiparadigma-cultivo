"""
Animación del Desmarque — Canal del Elqui
==========================================
Dos escenas independientes:
  1. EscenaCanal   — compuerta que solo deja pasar el 15%
  2. EscenaVaso    — vaso graduado con el agua que realmente llega

Renderizar (baja calidad, rápido):
  .venv_manim\\Scripts\\manim -pql animaciones/animacion_desmarque.py EscenaCanal
  .venv_manim\\Scripts\\manim -pql animaciones/animacion_desmarque.py EscenaVaso
  .venv_manim\\Scripts\\manim -pql animaciones/animacion_desmarque.py Desmarque
"""

from manim import *

# ── Paleta ───────────────────────────────────────────────────────────────────
FONDO      = "#0d1117"   # negro
BLANCO     = "#f0f4f8"   # blanco
CELESTE    = "#42c4f5"   # celeste agua
AMBAR      = "#f9a825"   # ámbar para el desmarque
GRIS       = "#8b9ab0"   # gris para texto secundario
GRIS_LINE  = "#4a5568"   # gris para paredes/líneas


# ═══════════════════════════════════════════════════════════════════════════
# ESCENA 1 — La compuerta del canal
# ═══════════════════════════════════════════════════════════════════════════
class EscenaCanal(Scene):
    def construct(self):
        # ── Título ──────────────────────────────────────────────────────────
        titulo = Text("El Desmarque", font_size=48, color=BLANCO, weight=BOLD)
        subtitulo = Text("¿Cuánta agua llega realmente al predio?",
                         font_size=24, color=GRIS)
        VGroup(titulo, subtitulo).arrange(DOWN, buff=0.3).move_to(UP * 2.8)

        self.play(Write(titulo), run_time=1.2)
        self.play(FadeIn(subtitulo), run_time=0.8)
        self.wait(0.5)

        # ── Canal: dos rectángulos paralelos (paredes) ───────────────────────
        pared_sup = Rectangle(width=9, height=0.25, color=GRIS_LINE, fill_opacity=0.6)
        pared_inf = Rectangle(width=9, height=0.25, color=GRIS_LINE, fill_opacity=0.6)
        pared_sup.move_to(LEFT * 0.5 + UP * 0.5)
        pared_inf.move_to(LEFT * 0.5 + DOWN * 0.5)
        lbl_canal = Text("Canal de riego", font_size=20, color=GRIS)
        lbl_canal.next_to(pared_sup, UP, buff=0.15)

        self.play(
            FadeIn(pared_sup), FadeIn(pared_inf),
            FadeIn(lbl_canal),
            run_time=0.8
        )

        # ── Agua fluyendo (llena) — potencial 1 L/s ─────────────────────────
        agua_llena = Rectangle(width=4, height=0.75, color=CELESTE,
                               fill_opacity=0.35, stroke_color=CELESTE, stroke_width=2)
        agua_llena.move_to(LEFT * 3.5)
        lbl_accion = Text("1 acción = 1 L/s  (potencial)", font_size=20, color=CELESTE)
        lbl_accion.next_to(agua_llena, UP, buff=0.55)

        self.play(FadeIn(agua_llena, shift=RIGHT), FadeIn(lbl_accion), run_time=1.0)
        self.wait(0.4)

        # ── Compuerta ────────────────────────────────────────────────────────
        compuerta = Rectangle(width=0.3, height=1.0, color=GRIS_LINE, fill_opacity=0.9)
        compuerta.move_to(ORIGIN)
        lbl_comp = Text("Compuerta\n(desmarque)", font_size=18, color=GRIS)
        lbl_comp.next_to(compuerta, DOWN, buff=0.2)

        self.play(FadeIn(compuerta), FadeIn(lbl_comp), run_time=0.6)
        self.wait(0.3)

        # ── La compuerta solo deja el 15% ────────────────────────────────────
        apertura_pct = Text("15 %", font_size=36, color=AMBAR, weight=BOLD)
        apertura_pct.next_to(compuerta, UP, buff=0.15)

        ranura = Rectangle(width=0.3, height=0.75 * 0.15,
                           color=CELESTE, fill_opacity=0.9, stroke_width=0)
        ranura.align_to(compuerta, DOWN).shift(UP * 0.05)

        self.play(FadeIn(apertura_pct), run_time=0.8)
        self.play(FadeIn(ranura), run_time=0.5)
        self.wait(0.3)

        # ── Hilo de agua tras la compuerta ───────────────────────────────────
        agua_real = Rectangle(width=0.1, height=0.75 * 0.15,
                              color=CELESTE, fill_opacity=0.9, stroke_width=0)
        agua_real.next_to(compuerta, RIGHT, buff=0)
        agua_real.align_to(ranura, DOWN)

        self.play(agua_real.animate.set_width(3.5), run_time=1.2)

        lbl_real = Text("0.15 L/s  (real)", font_size=20, color=CELESTE)
        lbl_real.next_to(agua_real, UP, buff=0.2)
        self.play(FadeIn(lbl_real), run_time=0.6)

        # ── Comparación final ────────────────────────────────────────────────
        self.wait(0.5)
        msg = VGroup(
            Text("Desmarque actual:", font_size=22, color=BLANCO),
            Text("15 %  →  0.15 L/s por acción", font_size=28, color=AMBAR, weight=BOLD),
        ).arrange(DOWN, buff=0.2).move_to(DOWN * 2.8)
        recuadro = SurroundingRectangle(msg, color=AMBAR, buff=0.2, corner_radius=0.15)

        self.play(FadeIn(msg), Create(recuadro), run_time=1.0)
        self.wait(2)


# ═══════════════════════════════════════════════════════════════════════════
# ESCENA 2 — El vaso graduado
# ═══════════════════════════════════════════════════════════════════════════
class EscenaVaso(Scene):
    def construct(self):
        # ── Título ──────────────────────────────────────────────────────────
        titulo = Text("¿Qué es el desmarque?", font_size=44, color=BLANCO, weight=BOLD)
        titulo.to_edge(UP, buff=0.4)
        self.play(Write(titulo), run_time=1.0)

        # ── Vaso (rectángulo abierto arriba) ─────────────────────────────────
        vaso_w, vaso_h = 2.2, 4.5
        vaso = VGroup(
            Line(LEFT * vaso_w/2 + DOWN * vaso_h/2,
                 LEFT * vaso_w/2 + UP * vaso_h/2, color=CELESTE, stroke_width=4),
            Line(RIGHT * vaso_w/2 + DOWN * vaso_h/2,
                 RIGHT * vaso_w/2 + UP * vaso_h/2, color=CELESTE, stroke_width=4),
            Line(LEFT * vaso_w/2 + DOWN * vaso_h/2,
                 RIGHT * vaso_w/2 + DOWN * vaso_h/2, color=CELESTE, stroke_width=4),
        ).move_to(LEFT * 2.5)

        self.play(Create(vaso), run_time=0.8)

        # ── Líneas de graduación ──────────────────────────────────────────────
        base_y   = vaso.get_bottom()[1]
        top_y    = vaso.get_top()[1]
        rango_y  = top_y - base_y
        cx       = vaso.get_center()[0]

        marcas = VGroup()
        for pct in [25, 50, 75, 100]:
            y = base_y + rango_y * pct / 100
            tick = Line(
                [cx - vaso_w/2, y, 0], [cx - vaso_w/2 + 0.35, y, 0],
                color=GRIS, stroke_width=2
            )
            lbl = Text(f"{pct}%", font_size=16, color=GRIS)
            lbl.next_to(tick, LEFT, buff=0.1)
            marcas.add(tick, lbl)

        self.play(FadeIn(marcas), run_time=0.5)

        # ── "Potencial" — línea punteada al 100 % ────────────────────────────
        y100 = base_y + rango_y
        linea_pot = DashedLine(
            [cx - vaso_w/2, y100, 0], [cx + vaso_w/2, y100, 0],
            color=CELESTE, dash_length=0.15, stroke_width=2
        )
        lbl_pot = Text("100%  (potencial)", font_size=18, color=CELESTE)
        lbl_pot.next_to(linea_pot, RIGHT, buff=0.2)

        self.play(Create(linea_pot), FadeIn(lbl_pot), run_time=0.8)
        self.wait(0.3)

        # ── Agua llenando solo al 15% ─────────────────────────────────────────
        y15 = base_y + rango_y * 0.15
        agua = Rectangle(
            width=vaso_w - 0.08, height=0,
            color=CELESTE, fill_opacity=0.45, stroke_width=0
        )
        agua.align_to(vaso, DOWN).shift(UP * 0.04).set_x(cx)

        agua_final = Rectangle(
            width=vaso_w - 0.08, height=rango_y * 0.15,
            color=CELESTE, fill_opacity=0.45, stroke_width=0
        )
        agua_final.align_to(vaso, DOWN).shift(UP * 0.04).set_x(cx)
        self.play(Transform(agua, agua_final), run_time=1.5, rate_func=linear)

        # ── Línea y etiqueta al 15% ───────────────────────────────────────────
        linea_15 = Line(
            [cx - vaso_w/2, y15, 0], [cx + vaso_w/2, y15, 0],
            color=AMBAR, stroke_width=3
        )
        lbl_15 = Text("15 %  (desmarque real)", font_size=20, color=AMBAR, weight=BOLD)
        lbl_15.next_to(linea_15, RIGHT, buff=0.2)

        self.play(Create(linea_15), FadeIn(lbl_15), run_time=0.7)

        # ── Zona vacía — lo que "no llega" ───────────────────────────────────
        zona_vacia = Rectangle(
            width=vaso_w - 0.08, height=rango_y * 0.85,
            color=CELESTE, fill_opacity=0.06, stroke_width=0
        )
        zona_vacia.next_to(agua_final, UP, buff=0).set_x(cx)

        lbl_vacio = Text("lo que\nno llega", font_size=18, color=GRIS)
        lbl_vacio.move_to(zona_vacia)

        self.play(FadeIn(zona_vacia), FadeIn(lbl_vacio), run_time=0.8)
        self.wait(0.4)

        # ── Ecuación a la derecha ─────────────────────────────────────────────
        eq = VGroup(
            Text("1 acción", font_size=26, color=BLANCO, weight=BOLD),
            Text("=  1 L/s potencial", font_size=22, color=CELESTE),
            Line(LEFT * 1.4, RIGHT * 1.4, color=GRIS_LINE, stroke_width=1.5),
            Text("desmarque  15 %", font_size=22, color=AMBAR),
            Text("→  0.15 L/s real", font_size=26, color=BLANCO, weight=BOLD),
        ).arrange(DOWN, buff=0.22).move_to(RIGHT * 3.2)

        self.play(FadeIn(eq, shift=LEFT * 0.3), run_time=1.2)
        self.wait(2.5)


# ═══════════════════════════════════════════════════════════════════════════
# ESCENA COMBINADA — ambas seguidas
# ═══════════════════════════════════════════════════════════════════════════
class Desmarque(Scene):
    def construct(self):
        EscenaCanal.construct(self)
        self.clear()
        EscenaVaso.construct(self)
