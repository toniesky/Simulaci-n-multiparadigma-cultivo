from manim import *

class TituloIntro(Scene):
    def construct(self):
        # Fondo negro clásico Manim (default)

        titulo = Text(
            "Modelo de Soporte a la Toma de Decisiones\n"
            "en la Agricultura Basado en\n"
            "Simulación Multiparadigma",
            font_size=34,
            color=WHITE,
            weight=BOLD,
            line_spacing=1.3,
        )

        linea = Line(LEFT * 5.8, RIGHT * 5.8, color=GRAY, stroke_width=1.2)

        capstone = Text("Capstone de Investigación", font_size=18, color=GRAY_B)

        int_lbl = Text("Integrantes", font_size=14, color=GRAY_B, weight=BOLD)
        int_names = Text(
            "Claudio Malebrán Cabezas  ·  Daniel Morales González  ·  Antonio Pereira Vergara",
            font_size=12,
            color=WHITE,
        )

        tut_lbl = Text("Tutores", font_size=14, color=GRAY_B, weight=BOLD)
        tut_names = Text(
            "Carlos Monardes Concha  ·  Agustín Olivares Soto",
            font_size=12,
            color=WHITE,
        )

        contenido = VGroup(
            titulo, linea, capstone, int_lbl, int_names, tut_lbl, tut_names
        )
        contenido.arrange(DOWN, buff=0.28)
        contenido.center()

        self.play(FadeIn(titulo, shift=UP * 0.25), run_time=1.5)
        self.play(Create(linea), run_time=0.7)
        self.play(FadeIn(capstone), run_time=0.6)
        self.play(FadeIn(int_lbl), FadeIn(int_names), run_time=0.6)
        self.play(FadeIn(tut_lbl), FadeIn(tut_names), run_time=0.6)
        self.wait(3.5)
        self.play(FadeOut(contenido), run_time=1.0)
