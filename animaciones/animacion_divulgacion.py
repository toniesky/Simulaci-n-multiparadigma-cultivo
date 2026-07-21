"""
Animacion de Divulgacion — Simulador de Gestion del Agua
=========================================================
Version accesible para audiencias no tecnicas.

Para renderizar:
  .venv_manim/Scripts/manim -pql animaciones/animacion_divulgacion.py PresentacionCompleta
  .venv_manim/Scripts/manim -pqh animaciones/animacion_divulgacion.py PresentacionCompleta

Salida: animaciones/media/videos/animacion_divulgacion/
"""

from manim import *

# ── Paleta ──────────────────────────────────────────────────────────────────
AZUL_OSC  = "#1e3a5f"
AZUL_MED  = "#2d6a9f"
AZUL_CLAR = "#93c5fd"
VERDE     = "#16a34a"
VERDE_CL  = "#bbf7d0"
AMBAR     = "#d97706"
AMBAR_CL  = "#fde68a"
ROJO      = "#dc2626"
GRIS      = "#6b7280"
GRIS_CL   = "#f3f4f6"
LILA      = "#7c3aed"
TEAL      = "#0d9488"

# ── Datos de precios reales (CLP/unidad = precio_ha / rendimiento) ──────────
# Fuente: productividad_cultivos.csv (promedio 2014-2025, IPC base 04/2026)
MESES_CORTOS = ["Ene","Feb","Mar","Abr","May","Jun","Jul","Ago","Sep","Oct","Nov","Dic"]

PRECIOS_REALES = [
    # (nombre, [CLP/unidad por mes], color)
    ("Lechuga",  [332, 290, 328, 314, 307, 328, 368, 367, 326, 282, 263, 260], AZUL_MED),
    ("Brocoli",  [641, 542, 570, 560, 542, 537, 544, 519, 545, 530, 500, 507], VERDE),
    ("Acelga",   [865, 690, 689, 644, 610, 597, 652, 660, 629, 605, 634, 647], ROJO),
    ("Apio",     [758, 523, 519, 519, 516, 520, 534, 549, 553, 541, 597, 588], TEAL),
    ("Choclo",   [285, 157, 167, 160, 168, 225, 294, 354, 353, 335, 289, 224], LILA),
]


def _params_panel(titulo, items, color, ancho=3.2, pos=RIGHT * 4.2 + UP * 0.5):
    """Panel lateral de parametros de entrada."""
    header = Text(titulo, font_size=14, color=color, weight=BOLD)
    filas = VGroup(header)
    for item in items:
        filas.add(Text(f"  {item}", font_size=11, color=GRIS))
    filas.arrange(DOWN, aligned_edge=LEFT, buff=0.13)
    bg = SurroundingRectangle(
        filas, corner_radius=0.15, color=color,
        fill_color=color, fill_opacity=0.07, buff=0.2,
    )
    return VGroup(bg, filas).move_to(pos)


# ─────────────────────────────────────────────
# ESCENA 1: Titulo — gancho
# ─────────────────────────────────────────────
class Titulo(Scene):
    def construct(self):
        pregunta = Text(
            "Como decide un agricultor\nque plantar, cuanto regar\ny cuando cosechar?",
            font_size=40, color=WHITE, weight=BOLD, line_spacing=1.3,
        )

        self.play(Write(pregunta), run_time=2.5)
        self.wait(1.5)

        resp = Text(
            "Un simulador resuelve las 3 preguntas a la vez.",
            font_size=24, color=VERDE,
        ).next_to(pregunta, DOWN, buff=0.7)
        self.play(FadeIn(resp, shift=UP * 0.3))
        self.wait(1)

        subtitulo = Text(
            "Dinamica de Sistemas  +  Eventos Discretos  +  Optimizacion",
            font_size=17, color=GRIS,
        ).next_to(resp, DOWN, buff=0.5)
        barra = Line(LEFT * 5.5, RIGHT * 5.5, color=AZUL_MED, stroke_width=1.5).next_to(subtitulo, DOWN, buff=0.35)
        capstone = Text("Capstone · 2026", font_size=16, color=GRIS).next_to(barra, DOWN, buff=0.25)
        self.play(FadeIn(subtitulo), Create(barra), FadeIn(capstone), run_time=1.2)
        self.wait(2)
        self.play(*[FadeOut(m) for m in self.mobjects])


# ─────────────────────────────────────────────
# ESCENA 2: Paso 1 — Escenarios de Oferta Hidrica
# ─────────────────────────────────────────────
class EscenarioHidrico(Scene):
    def construct(self):
        # Encabezado
        paso = Text("PASO 1", font_size=14, color=AZUL_MED, weight=BOLD).to_corner(UL, buff=0.4)
        titulo = Text("Cuanta agua hay disponible?", font_size=34, color=WHITE, weight=BOLD).to_edge(UP, buff=0.4)
        paradigma = Text("Paradigma: Dinamica de Sistemas", font_size=15, color=AZUL_MED).next_to(titulo, DOWN, buff=0.15)
        self.play(FadeIn(paso), Write(titulo), FadeIn(paradigma))

        # ─ Diagrama de flujos simplificado ─
        # Fuentes de agua
        src_canal = RoundedRectangle(corner_radius=0.2, width=2.5, height=1.1,
                                      fill_color=AZUL_MED, fill_opacity=0.15,
                                      stroke_color=AZUL_MED, stroke_width=2).shift(LEFT * 4.5 + UP * 0.3)
        lbl_canal = Text("Canal\nde riego", font_size=14, color=AZUL_MED, weight=BOLD).move_to(src_canal)

        src_sub = RoundedRectangle(corner_radius=0.2, width=2.5, height=1.1,
                                    fill_color=TEAL, fill_opacity=0.12,
                                    stroke_color=TEAL, stroke_width=2).shift(LEFT * 4.5 + DOWN * 1.6)
        lbl_sub = Text("Derechos de\nagua subterra nea", font_size=13, color=TEAL, weight=BOLD).move_to(src_sub)

        # Stock central
        stock = RoundedRectangle(corner_radius=0.25, width=2.8, height=1.4,
                                  fill_color=AZUL_CLAR, fill_opacity=0.4,
                                  stroke_color=AZUL_MED, stroke_width=2.5).shift(LEFT * 0.5 + DOWN * 0.6)
        lbl_stock = Text("Agua\ndisponible", font_size=16, color=AZUL_OSC, weight=BOLD).move_to(stock)

        # Salida: escenarios
        out_box = RoundedRectangle(corner_radius=0.2, width=2.8, height=1.1,
                                    fill_color=AMBAR, fill_opacity=0.12,
                                    stroke_color=AMBAR, stroke_width=2).shift(RIGHT * 3.8 + DOWN * 0.6)
        lbl_out = Text("5 escenarios\nde oferta", font_size=14, color=AMBAR, weight=BOLD).move_to(out_box)

        # Perdidas
        perd = Text("- Perdidas por filtracion\n- Mantenimiento del canal", font_size=12, color=ROJO).shift(LEFT * 0.5 + DOWN * 2.4)
        flecha_perd = Arrow(stock.get_bottom(), perd.get_top(), buff=0.1, color=ROJO, stroke_width=1.8)

        # Flechas principales
        a1 = Arrow(src_canal.get_right(), stock.get_top() + LEFT * 0.3, buff=0.1, color=AZUL_MED, stroke_width=2.5)
        a2 = Arrow(src_sub.get_right(), stock.get_bottom() + LEFT * 0.3, buff=0.1, color=TEAL, stroke_width=2)
        a3 = Arrow(stock.get_right(), out_box.get_left(), buff=0.1, color=AMBAR, stroke_width=2.5)

        self.play(FadeIn(src_canal), Write(lbl_canal), run_time=0.7)
        self.play(FadeIn(src_sub),   Write(lbl_sub),   run_time=0.7)
        self.play(Create(a1), Create(a2), run_time=0.7)
        self.play(FadeIn(stock),    Write(lbl_stock),  run_time=0.6)
        self.play(Create(flecha_perd), FadeIn(perd), run_time=0.6)
        self.play(Create(a3), FadeIn(out_box), Write(lbl_out), run_time=0.7)

        # Los 5 escenarios como etiquetas
        escs = VGroup(*[
            Text(f"Esc {s:+d}", font_size=13, color=AMBAR, weight=BOLD)
            for s in [-2, -1, 0, +1, +2]
        ]).arrange(DOWN, buff=0.18).next_to(out_box, RIGHT, buff=0.35)
        self.play(LaggedStartMap(FadeIn, escs, lag_ratio=0.15), run_time=0.8)

        # Panel de parametros
        panel = _params_panel(
            "Parametros de entrada",
            [
                "N acciones de agua",
                "% desmarque ini / final",
                "Perdidas filtracion (%)",
                "Frecuencia turno (dias)",
                "Calendario de paradas",
                "Recargas subterraneas (m3)",
            ],
            AZUL_MED, pos=RIGHT * 4.8 + UP * 2.2,
        )
        self.play(FadeIn(panel, shift=LEFT * 0.2))
        self.wait(2.5)
        self.play(*[FadeOut(m) for m in self.mobjects])


# ─────────────────────────────────────────────
# ESCENA 3: Calendario de Oferta (barras animadas)
# ─────────────────────────────────────────────
class CalendarioOferta(Scene):
    def construct(self):
        paso = Text("PASO 1 · Resultado", font_size=14, color=AZUL_MED, weight=BOLD).to_corner(UL, buff=0.4)
        titulo = Text("El Calendario de Oferta", font_size=34, color=WHITE, weight=BOLD).to_edge(UP, buff=0.4)
        sub = Text("Garantia de m3 disponibles cada dia del anio", font_size=16, color=GRIS).next_to(titulo, DOWN, buff=0.15)
        self.play(FadeIn(paso), Write(titulo), FadeIn(sub))

        # Eje x (tiempo) y eje y (m3)
        eje_x = Line(LEFT * 5.5, RIGHT * 5.5, color=GRIS, stroke_width=1.5).shift(DOWN * 1.6)
        eje_y = Line(DOWN * 1.6 + LEFT * 5.5, UP * 1.5 + LEFT * 5.5, color=GRIS, stroke_width=1.5)
        lbl_y = Text("m3", font_size=12, color=GRIS).next_to(eje_y.get_top(), LEFT, buff=0.1)
        lbl_x = Text("Dias del anio →", font_size=12, color=GRIS).next_to(eje_x.get_right(), RIGHT, buff=0.1)
        self.play(Create(eje_x), Create(eje_y), FadeIn(lbl_y), FadeIn(lbl_x))

        # Patron de barras: simula el calendario real
        # turno cada 7 dias, paradas en junio-agosto
        import random
        random.seed(42)
        n_dias = 52  # representacion semanal
        barras = VGroup()
        x_start = -5.3
        dx = 10.6 / n_dias
        alto_turno = 2.5
        base_y = -1.6

        for i in range(n_dias):
            es_parada = 22 <= i <= 32  # jun-ago
            es_turno  = (i % 7 == 0) and not es_parada

            if es_turno:
                h = alto_turno
                color = AZUL_MED
                op = 0.85
            elif es_parada:
                h = 0.25
                color = ROJO
                op = 0.5
            else:
                h = 0.0
                color = GRIS
                op = 0.0

            if h > 0:
                barra = Rectangle(
                    width=dx * 0.8, height=h,
                    fill_color=color, fill_opacity=op,
                    stroke_width=0,
                ).move_to([x_start + i * dx, base_y + h / 2, 0])
                barras.add(barra)

        self.play(LaggedStartMap(GrowFromEdge, barras, edge=DOWN, lag_ratio=0.04), run_time=2.5)

        # Leyenda
        leyenda = VGroup(
            VGroup(
                Rectangle(width=0.35, height=0.35, fill_color=AZUL_MED, fill_opacity=0.85, stroke_width=0),
                Text("Dia de turno (agua disponible)", font_size=12, color=AZUL_MED),
            ).arrange(RIGHT, buff=0.15),
            VGroup(
                Rectangle(width=0.35, height=0.35, fill_color=ROJO, fill_opacity=0.5, stroke_width=0),
                Text("Periodo de mantenimiento (sin agua)", font_size=12, color=ROJO),
            ).arrange(RIGHT, buff=0.15),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.2).to_edge(DOWN, buff=0.3).to_edge(LEFT, buff=0.5)
        self.play(FadeIn(leyenda))

        # Output
        csv_box = VGroup(
            RoundedRectangle(corner_radius=0.15, width=5.8, height=0.65,
                             fill_color=AMBAR, fill_opacity=0.12,
                             stroke_color=AMBAR, stroke_width=2),
            Text("Salida:  CalendarioOferta.csv  →  input para el siguiente modulo",
                 font_size=13, color=AMBAR, weight=BOLD),
        )
        csv_box[1].move_to(csv_box[0])
        csv_box.to_edge(DOWN, buff=0.3).to_edge(RIGHT, buff=0.4)
        self.play(FadeIn(csv_box))
        self.wait(2.5)
        self.play(*[FadeOut(m) for m in self.mobjects])


# ─────────────────────────────────────────────
# ESCENA 4: Paso 2 — Combinatorio de Cultivos
# ─────────────────────────────────────────────
class Combinatorio(Scene):
    def construct(self):
        paso = Text("PASO 2", font_size=14, color=VERDE, weight=BOLD).to_corner(UL, buff=0.4)
        titulo = Text("Que combinacion de cultivos es la mejor?", font_size=30, color=WHITE, weight=BOLD).to_edge(UP, buff=0.4)
        paradigma = Text("Paradigma: Simulacion de Eventos Discretos", font_size=15, color=VERDE).next_to(titulo, DOWN, buff=0.15)
        self.play(FadeIn(paso), Write(titulo), FadeIn(paradigma))

        # Concepto: el predio tiene particiones
        particiones = VGroup(*[
            VGroup(
                Square(side_length=1.2, fill_color=VERDE_CL, fill_opacity=0.4,
                       stroke_color=VERDE, stroke_width=2),
                Text(f"Terreno\n{i+1}", font_size=13, color=VERDE),
            ).arrange(DOWN, buff=0.08)
            for i in range(4)
        ]).arrange(RIGHT, buff=0.35).shift(UP * 0.8)
        self.play(LaggedStartMap(FadeIn, particiones, lag_ratio=0.2), run_time=0.9)

        # Opciones de cultivo
        opciones_lbl = Text("Opciones por terreno:", font_size=14, color=GRIS).shift(DOWN * 0.2 + LEFT * 3.5)
        opciones = VGroup(
            Text("Lechuga", font_size=13, color=AZUL_MED),
            Text("Brocoli", font_size=13, color=VERDE),
            Text("Acelga", font_size=13, color=AMBAR),
            Text("Apio", font_size=13, color=TEAL),
            Text("Tomate", font_size=13, color=ROJO),
            Text("Choclo", font_size=13, color=LILA),
            Text("No plantar", font_size=13, color=GRIS),
        ).arrange(DOWN, buff=0.12, aligned_edge=LEFT).next_to(opciones_lbl, DOWN, buff=0.15)
        self.play(FadeIn(opciones_lbl))
        self.play(LaggedStartMap(FadeIn, opciones, lag_ratio=0.1), run_time=0.8)

        # La formula matematica
        formula_lbl = Text("Formula de combinaciones con repeticion:", font_size=14, color=AZUL_OSC, weight=BOLD).shift(DOWN * 0.2 + RIGHT * 1.5)
        formula = MathTex(
            r"\binom{n + k - 1}{k}",
            font_size=52, color=AZUL_MED,
        ).next_to(formula_lbl, DOWN, buff=0.3)
        vars_lbl = VGroup(
            Text("n = 7 opciones de cultivo", font_size=13, color=AZUL_MED),
            Text("k = 4 terrenos",            font_size=13, color=VERDE),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.12).next_to(formula, DOWN, buff=0.25)
        self.play(Write(formula_lbl), run_time=0.7)
        self.play(Write(formula), run_time=1)
        self.play(FadeIn(vars_lbl))

        # Resultado numerico
        resultado = MathTex(
            r"\binom{10}{4} = 210 \text{ combinaciones}",
            font_size=36, color=AMBAR,
        ).next_to(vars_lbl, DOWN, buff=0.25)
        self.play(Write(resultado))

        # Total de simulaciones
        total_box = VGroup(
            RoundedRectangle(corner_radius=0.15, width=6.5, height=0.72,
                             fill_color=VERDE, fill_opacity=0.12,
                             stroke_color=VERDE, stroke_width=2),
            Text("210 combinaciones  x  5 escenarios  =  1,050 simulaciones por regante",
                 font_size=14, color=VERDE, weight=BOLD),
        )
        total_box[1].move_to(total_box[0])
        total_box.to_edge(DOWN, buff=0.25)
        self.play(FadeIn(total_box))

        # Panel de parametros
        panel = _params_panel(
            "Parametros de entrada",
            [
                "CalendarioOferta.csv",
                "Presupuesto del regante",
                "N de terrenos (particiones)",
                "Dia de inicio de simulacion",
                "Datos del regante (ha, estanque)",
            ],
            VERDE, pos=RIGHT * 4.5 + UP * 0.8,
        )
        self.play(FadeIn(panel, shift=LEFT * 0.2))
        self.wait(2.5)
        self.play(*[FadeOut(m) for m in self.mobjects])


# ─────────────────────────────────────────────
# ESCENA 5: Los Precios Son Estacionales
#           Grafico animado (replica del real)
# ─────────────────────────────────────────────
class PreciosEstacionales(Scene):
    def construct(self):
        paso = Text("CRITERIO 1 de seleccion", font_size=14, color=AMBAR, weight=BOLD).to_corner(UL, buff=0.4)
        titulo = Text("Los precios son estacionales", font_size=32, color=WHITE, weight=BOLD).to_edge(UP, buff=0.4)
        sub = Text("El mismo cultivo puede valer el doble segun cuando llega al mercado",
                   font_size=15, color=GRIS).next_to(titulo, DOWN, buff=0.15)
        self.play(FadeIn(paso), Write(titulo), FadeIn(sub))

        # ── Ejes ──────────────────────────────────────────────────────────
        ax = Axes(
            x_range=[0.5, 13, 1],
            y_range=[0, 1000, 200],
            x_length=9.5,
            y_length=4.8,
            tips=False,
            axis_config={"color": GRIS, "stroke_width": 1.5, "include_ticks": False},
            y_axis_config={
                "numbers_to_include": [0, 200, 400, 600, 800],
                "font_size": 12,
                "color": GRIS,
            },
        ).shift(DOWN * 0.8 + LEFT * 0.3)

        # Etiquetas eje X (meses)
        x_labels = VGroup(*[
            Text(m, font_size=12, color=GRIS).move_to(ax.c2p(i + 1, 0) + DOWN * 0.38)
            for i, m in enumerate(MESES_CORTOS)
        ])

        # Etiqueta eje Y
        y_lbl = Text("CLP / unidad", font_size=12, color=GRIS).rotate(PI / 2).next_to(ax.get_left(), LEFT, buff=0.45)

        # Lineas de cuadricula horizontales
        grillas = VGroup(*[
            DashedLine(
                ax.c2p(0.5, v), ax.c2p(13, v),
                color=GRIS, stroke_width=0.8, stroke_opacity=0.4,
                dash_length=0.12,
            )
            for v in [200, 400, 600, 800]
        ])

        self.play(Create(ax), FadeIn(x_labels), FadeIn(y_lbl), Create(grillas), run_time=1)

        # ── Lineas de precio por cultivo ───────────────────────────────────
        cultivos_mostrar = PRECIOS_REALES  # todos

        lineas_finales = []
        for nombre, vals, color in cultivos_mostrar:
            # Puntos del poligono
            puntos = [ax.c2p(i + 1, v) for i, v in enumerate(vals)]

            linea = VMobject(color=color, stroke_width=2.8, stroke_opacity=0.9)
            linea.set_points_as_corners(puntos)

            dots = VGroup(*[
                Dot(p, color=color, radius=0.065, fill_opacity=0.9)
                for p in puntos
            ])

            # Etiqueta al final de la linea (mes Dic)
            lbl_fin = Text(nombre, font_size=13, color=color, weight=BOLD).next_to(
                ax.c2p(12, vals[11]), RIGHT, buff=0.15
            )

            self.play(
                Create(linea),
                run_time=1.4,
            )
            self.play(
                FadeIn(dots),
                Write(lbl_fin),
                run_time=0.4,
            )
            lineas_finales.append((nombre, vals, color, lbl_fin))

        self.wait(0.5)

        # ── Destacar el pico de Lechuga en Jul-Ago ─────────────────────────
        lechuga_vals = PRECIOS_REALES[0][1]
        peak_pt = ax.c2p(7, lechuga_vals[6])   # Julio
        peak_arrow = Arrow(
            peak_pt + UP * 0.9 + LEFT * 0.5,
            peak_pt + UP * 0.15,
            color=AZUL_MED, stroke_width=2, buff=0.05,
        )
        peak_lbl = Text("Pico Jul:\nlechuga mas cara", font_size=12, color=AZUL_MED, weight=BOLD)
        peak_lbl.next_to(peak_arrow.get_start(), UP, buff=0.08)
        self.play(Create(peak_arrow), Write(peak_lbl), run_time=0.7)

        # ── Destacar el pico de Acelga en Enero ───────────────────────────
        acelga_vals = PRECIOS_REALES[2][1]
        peak_ac = ax.c2p(1, acelga_vals[0])
        peak_arrow2 = Arrow(
            peak_ac + UP * 0.6 + RIGHT * 0.5,
            peak_ac + UP * 0.12,
            color=ROJO, stroke_width=2, buff=0.05,
        )
        peak_lbl2 = Text("Pico Ene:\nacelga mas cara", font_size=12, color=ROJO, weight=BOLD)
        peak_lbl2.next_to(peak_arrow2.get_start(), UP + RIGHT * 0.3, buff=0.05)
        self.play(Create(peak_arrow2), Write(peak_lbl2), run_time=0.7)

        self.wait(0.5)

        # Conclusion
        concl = Text(
            "El simulador calcula el mes de cosecha segun el cultivo y la fecha de siembra,\n"
            "y usa el precio de ese mes para calcular el ingreso esperado.",
            font_size=14, color=AZUL_OSC,
        ).to_edge(DOWN, buff=0.25)
        self.play(Write(concl), run_time=1.2)
        self.wait(3)
        self.play(*[FadeOut(m) for m in self.mobjects])


# ─────────────────────────────────────────────
# ESCENA 6: Estres Hidrico — distribucion del agua
# ─────────────────────────────────────────────
class EstresHidrico(Scene):
    def construct(self):
        paso = Text("CRITERIO 2 de seleccion", font_size=14, color=VERDE, weight=BOLD).to_corner(UL, buff=0.4)
        titulo = Text("El agua define la calidad de la cosecha", font_size=30, color=WHITE, weight=BOLD).to_edge(UP, buff=0.4)
        self.play(FadeIn(paso), Write(titulo))

        # Columna izquierda: ciclo de cultivo con fases
        fases_lbl = Text("Ciclo del cultivo (ejemplo: 90 dias)", font_size=14, color=GRIS).shift(LEFT * 3.5 + UP * 1.2)
        fases = VGroup(*[
            VGroup(
                Rectangle(width=w, height=0.5, fill_color=c, fill_opacity=0.7,
                          stroke_color=c, stroke_width=1.2),
                Text(n, font_size=11, color=c),
            ).arrange(DOWN, buff=0.06)
            for w, c, n in [
                (0.9, AZUL_CLAR, "Inicio"),
                (1.3, VERDE,     "Desarrollo"),
                (1.8, VERDE_CL,  "Media"),
                (0.9, AMBAR,     "Final"),
            ]
        ]).arrange(RIGHT, buff=0.05).next_to(fases_lbl, DOWN, buff=0.2)
        self.play(Write(fases_lbl))
        self.play(LaggedStartMap(FadeIn, fases, lag_ratio=0.25), run_time=0.9)

        # Escenario A: agua suficiente
        esc_a = VGroup(
            Text("Con agua suficiente:", font_size=14, color=VERDE, weight=BOLD),
            Text("La demanda hidrica del cultivo queda cubierta", font_size=13, color=GRIS),
            Text("La planta crece sin restricciones", font_size=13, color=GRIS),
            Text("Rendimiento al maximo esperado", font_size=13, color=VERDE),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.15).shift(LEFT * 3.5 + DOWN * 0.9)

        # Escenario B: estres hidrico
        esc_b = VGroup(
            Text("Con estres hidrico:", font_size=14, color=ROJO, weight=BOLD),
            Text("La oferta no alcanza la demanda hidrica", font_size=13, color=GRIS),
            Text("El suelo se seca y la planta sufre", font_size=13, color=GRIS),
            Text("Rendimiento reducido  →  menos ingreso", font_size=13, color=ROJO),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.15).shift(RIGHT * 2.0 + DOWN * 0.9)

        self.play(FadeIn(esc_a, shift=RIGHT * 0.2), run_time=0.7)
        self.play(FadeIn(esc_b, shift=LEFT * 0.2), run_time=0.7)

        # Separador
        sep = DashedLine(UP * 0.2 + DOWN * 2.5, DOWN * 2.5, color=GRIS,
                          stroke_width=1, stroke_opacity=0.5).shift(RIGHT * 0.1)
        self.play(Create(sep))

        # Panel de parametros
        panel = _params_panel(
            "Parametros del suelo",
            [
                "CC  (capacidad de campo)",
                "PMP (punto de marchitez)",
                "Alpha (no linealidad estres)",
                "Stock subterra neo inicial (m3)",
                "Datos climaticos (ETo diaria)",
                "Dias sin riego → uso subterra neo",
            ],
            VERDE, pos=RIGHT * 4.6 + UP * 1.0,
        )
        self.play(FadeIn(panel, shift=LEFT * 0.2))
        self.wait(2.5)
        self.play(*[FadeOut(m) for m in self.mobjects])


# ─────────────────────────────────────────────
# ESCENA 7: Costos y Decision Final
# ─────────────────────────────────────────────
class DecisionFinal(Scene):
    def construct(self):
        paso = Text("CRITERIO 3 y Decision", font_size=14, color=AMBAR, weight=BOLD).to_corner(UL, buff=0.4)
        titulo = Text("Que cultivo elegir?", font_size=36, color=WHITE, weight=BOLD).to_edge(UP, buff=0.4)
        self.play(FadeIn(paso), Write(titulo))

        formula_lbl = Text("Para cada combinacion el modelo calcula:", font_size=15, color=GRIS).shift(UP * 1.2)
        self.play(Write(formula_lbl))

        componentes = VGroup(
            VGroup(
                Text("[+]", font_size=22, color=VERDE, weight=BOLD),
                VGroup(
                    Text("Ingreso", font_size=17, color=VERDE, weight=BOLD),
                    Text("precio estacional x produccion real x hectareas efectivas", font_size=12, color=GRIS),
                ).arrange(DOWN, aligned_edge=LEFT, buff=0.05),
            ).arrange(RIGHT, buff=0.2),
            VGroup(
                Text("[-]", font_size=22, color=ROJO, weight=BOLD),
                VGroup(
                    Text("Costo", font_size=17, color=ROJO, weight=BOLD),
                    Text("costo de cultivar esa fraccion de terreno ($/ha x ha efectivas)", font_size=12, color=GRIS),
                ).arrange(DOWN, aligned_edge=LEFT, buff=0.05),
            ).arrange(RIGHT, buff=0.2),
            VGroup(
                Text("[!]", font_size=22, color=AMBAR, weight=BOLD),
                VGroup(
                    Text("Restriccion presupuestaria", font_size=17, color=AMBAR, weight=BOLD),
                    Text("si Costo total > Presupuesto → combinacion descartada", font_size=12, color=GRIS),
                ).arrange(DOWN, aligned_edge=LEFT, buff=0.05),
            ).arrange(RIGHT, buff=0.2),
            VGroup(
                Text("[!]", font_size=22, color=LILA, weight=BOLD),
                VGroup(
                    Text("Restricciones estacionales", font_size=17, color=LILA, weight=BOLD),
                    Text("cultivos disponibles segun el mes de siembra (calendario de disponibilidad)", font_size=12, color=GRIS),
                ).arrange(DOWN, aligned_edge=LEFT, buff=0.05),
            ).arrange(RIGHT, buff=0.2),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.28).next_to(formula_lbl, DOWN, buff=0.3)

        for comp in componentes:
            self.play(FadeIn(comp, shift=RIGHT * 0.3), run_time=0.5)

        resultado = VGroup(
            RoundedRectangle(corner_radius=0.18, width=8.2, height=0.72,
                             fill_color=VERDE, fill_opacity=0.13,
                             stroke_color=VERDE, stroke_width=2),
            Text("Score = Ingreso − Costo    (el maximo entre todas las combinaciones validas)",
                 font_size=14, color=VERDE, weight=BOLD),
        )
        resultado[1].move_to(resultado[0])
        resultado.to_edge(DOWN, buff=0.25)
        self.play(FadeIn(resultado))
        self.wait(2.5)
        self.play(*[FadeOut(m) for m in self.mobjects])


# ─────────────────────────────────────────────
# ESCENA 8: Resultado — Portafolio Optimo
# ─────────────────────────────────────────────
class ResultadoFinal(Scene):
    def construct(self):
        titulo = Text("El resultado: portafolio optimo por escenario", font_size=30, color=WHITE, weight=BOLD).to_edge(UP, buff=0.4)
        self.play(Write(titulo))

        # Tabla de escenarios
        escenarios = [
            ("Esc -2  (muy poca agua)", 1.8, ROJO,    "Solo lechuga        →  agua es el limite"),
            ("Esc -1  (poca agua)",     2.9, AMBAR,   "Lechuga x3 + No plantar"),
            ("Esc  0  (normal)",        4.2, VERDE,   "Brocoli + Lechuga x2 + Acelga"),
            ("Esc +1  (buena oferta)",  5.1, VERDE,   "Brocoli x2 + Lechuga + Espinaca"),
            ("Esc +2  (abundante)",     5.6, AZUL_MED,"Brocoli x2 + Acelga + Apio"),
        ]

        filas = VGroup()
        for label, score, color, detalle in escenarios:
            barra = Rectangle(
                width=score * 0.72, height=0.52,
                fill_color=color, fill_opacity=0.72, stroke_color=color, stroke_width=1.2,
            )
            lbl_esc   = Text(label,          font_size=12, color=color, weight=BOLD).next_to(barra, LEFT, buff=0.15)
            lbl_score = Text(f"${score:.1f}M", font_size=12, color=color).next_to(barra, RIGHT, buff=0.12)
            lbl_det   = Text(detalle, font_size=10, color=GRIS).next_to(lbl_score, RIGHT, buff=0.35)
            filas.add(VGroup(lbl_esc, barra, lbl_score, lbl_det))

        filas.arrange(DOWN, aligned_edge=LEFT, buff=0.28).shift(LEFT * 0.3 + DOWN * 0.2)
        for f in filas:
            self.play(FadeIn(f, shift=RIGHT * 0.3), run_time=0.48)

        # Reporte
        reporte_box = VGroup(
            RoundedRectangle(corner_radius=0.15, width=7.5, height=0.65,
                             fill_color=AZUL_MED, fill_opacity=0.1,
                             stroke_color=AZUL_MED, stroke_width=2),
            Text("El reporte HTML detalla cada combinacion evaluada  →  se abre automaticamente",
                 font_size=13, color=AZUL_MED, weight=BOLD),
        )
        reporte_box[1].move_to(reporte_box[0])
        reporte_box.to_edge(DOWN, buff=0.3)
        self.play(FadeIn(reporte_box))
        self.wait(2.5)
        self.play(*[FadeOut(m) for m in self.mobjects])


# ─────────────────────────────────────────────
# ESCENA 9: Cierre
# ─────────────────────────────────────────────
class Cierre(Scene):
    def construct(self):
        titulo = Text("En resumen", font_size=42, color=WHITE, weight=BOLD)
        self.play(Write(titulo))
        self.play(titulo.animate.to_edge(UP, buff=0.45))

        pasos = [
            ("1.", "Dinamica de Sistemas genera 5 escenarios de oferta hidrica diaria",    AZUL_MED),
            ("2.", "El CalendarioOferta.csv es el puente al siguiente modulo",              AMBAR),
            ("3.", "Eventos Discretos simula 1,050 combinaciones de cultivo",               VERDE),
            ("4.", "Para cada una: precio estacional x produccion con estres x hectareas",  AMBAR),
            ("5.", "Minus el costo de cultivo, dentro del presupuesto del regante",         ROJO),
            ("6.", "El modelo elige el portafolio con mayor margen por escenario",          VERDE),
        ]

        filas = VGroup()
        for num, texto, color in pasos:
            n = Text(num,   font_size=20, color=color, weight=BOLD)
            t = Text(texto, font_size=18, color=AZUL_OSC)
            filas.add(VGroup(n, t).arrange(RIGHT, buff=0.3))
        filas.arrange(DOWN, aligned_edge=LEFT, buff=0.3).next_to(titulo, DOWN, buff=0.5)

        for fila in filas:
            self.play(FadeIn(fila, shift=RIGHT * 0.3), run_time=0.44)

        self.wait(0.5)
        fin = Text(
            "Capstone · Simulacion Multiparadigma de Gestion del Agua · 2026",
            font_size=16, color=GRIS,
        ).to_edge(DOWN, buff=0.35)
        self.play(FadeIn(fin))
        self.wait(3)
        self.play(*[FadeOut(m) for m in self.mobjects])


# ─────────────────────────────────────────────
# ESCENA 10: Recomendacion — Gantt + Monitoreo
# ─────────────────────────────────────────────
class RecomendacionFinal(Scene):
    def construct(self):
        titulo = Text("El modelo entrega una recomendacion concreta", font_size=28, color=WHITE, weight=BOLD).to_edge(UP, buff=0.35)
        self.play(Write(titulo))

        # ── Recomendacion por escenario ────────────────────────────────────
        esc_lbl = Text("Para cada escenario (de mas pesimista a mas optimista):",
                       font_size=13, color=GRIS).shift(UP * 2.5 + LEFT * 1)
        self.play(FadeIn(esc_lbl))

        recomendaciones = [
            ("Esc -2", ["T1: Lechuga",    "T2: No plantar", "T3: No plantar", "T4: No plantar"], ROJO),
            ("Esc  0", ["T1: Brocoli",    "T2: Lechuga",    "T3: Lechuga",    "T4: Acelga"],     VERDE),
            ("Esc +2", ["T1: Brocoli",    "T2: Brocoli",    "T3: Acelga",     "T4: Apio"],       AZUL_MED),
        ]
        cols_grp = VGroup()
        for esc_nombre, terrenos, color in recomendaciones:
            col = VGroup(
                Text(esc_nombre, font_size=12, color=color, weight=BOLD),
                *[Text(t, font_size=11, color=GRIS) for t in terrenos],
            ).arrange(DOWN, aligned_edge=LEFT, buff=0.12)
            bg = SurroundingRectangle(col, corner_radius=0.12, color=color,
                                      fill_color=color, fill_opacity=0.08, buff=0.15)
            cols_grp.add(VGroup(bg, col))
        cols_grp.arrange(RIGHT, buff=0.5).next_to(esc_lbl, DOWN, buff=0.2)
        self.play(LaggedStartMap(FadeIn, cols_grp, lag_ratio=0.3), run_time=1.0)

        # ── Carta Gantt ──────────────────────────────────────────────────────────
        gantt_lbl = Text("Programacion de cosechas (Carta Gantt)",
                         font_size=13, color=AMBAR, weight=BOLD).shift(DOWN * 1.5 + LEFT * 2)
        self.play(Write(gantt_lbl))

        cultivos_gantt = [
            ("T1: Brocoli",  1,  3, VERDE),
            ("T2: Lechuga",  2,  5, AZUL_MED),
            ("T3: Lechuga",  3,  6, AZUL_MED),
            ("T4: Acelga",   1,  4, AMBAR),
        ]
        gantt_base_y = -2.0
        gantt_x0     = -4.5
        gantt_escala = 1.1
        gantt_barras = VGroup()
        for i, (nombre, ini, fin, color) in enumerate(cultivos_gantt):
            y = gantt_base_y - i * 0.45
            barra = Rectangle(
                width=(fin - ini) * gantt_escala, height=0.32,
                fill_color=color, fill_opacity=0.75, stroke_color=color, stroke_width=1,
            ).move_to([gantt_x0 + (ini + (fin - ini) / 2) * gantt_escala, y, 0])
            lbl_n = Text(nombre, font_size=10, color=color).next_to(barra, LEFT, buff=0.1)
            cosecha_lbl = Text("cosecha", font_size=9, color=color)
            cosecha_lbl.next_to(barra, RIGHT, buff=0.08)
            gantt_barras.add(VGroup(barra, lbl_n, cosecha_lbl))

        meses_gantt = ["M1", "M2", "M3", "M4", "M5", "M6"]
        meses_lbl = VGroup(*[
            Text(m, font_size=10, color=GRIS).move_to(
                [gantt_x0 + (j + 1) * gantt_escala, gantt_base_y + 0.45, 0])
            for j, m in enumerate(meses_gantt)
        ])
        self.play(FadeIn(meses_lbl))
        self.play(LaggedStartMap(GrowFromEdge, [b[0] for b in gantt_barras], edge=LEFT, lag_ratio=0.2), run_time=1.2)
        self.play(LaggedStartMap(FadeIn, [VGroup(b[1], b[2]) for b in gantt_barras], lag_ratio=0.15), run_time=0.6)

        # ── Monitoreo de humedad ──────────────────────────────────────────────────
        monitor_lbl = Text("Monitoreo: balance diario de humedad del suelo",
                           font_size=13, color=TEAL, weight=BOLD).shift(DOWN * 3.05 + LEFT * 1.5)
        self.play(Write(monitor_lbl))

        puntos_hum = [
            0.85, 0.78, 0.70, 0.63, 0.90, 0.82, 0.74, 0.66,
            0.58, 0.52, 0.47, 0.88, 0.80, 0.72, 0.64, 0.55,
            0.48, 0.42, 0.36, 0.30, 0.28, 0.90, 0.82, 0.74,
        ]
        n_pts = len(puntos_hum)
        ancho_graf = 7.5
        base_hum_y = -3.4
        escala_hum = 0.38

        eje_hx = Line(
            LEFT * (ancho_graf / 2) + [0, base_hum_y, 0],
            RIGHT * (ancho_graf / 2) + [0, base_hum_y, 0],
            color=GRIS, stroke_width=1
        ).shift(RIGHT * 0.3)
        cc_line = DashedLine(
            [0.3 - ancho_graf / 2, base_hum_y + escala_hum * 1.0, 0],
            [0.3 + ancho_graf / 2, base_hum_y + escala_hum * 1.0, 0],
            color=AZUL_CLAR, stroke_width=1.2, dash_length=0.1,
        )
        pmp_line = DashedLine(
            [0.3 - ancho_graf / 2, base_hum_y + escala_hum * 0.25, 0],
            [0.3 + ancho_graf / 2, base_hum_y + escala_hum * 0.25, 0],
            color=ROJO, stroke_width=1.2, dash_length=0.1,
        )
        cc_txt  = Text("CC",  font_size=10, color=AZUL_CLAR).next_to(cc_line,  RIGHT, buff=0.08)
        pmp_txt = Text("PMP", font_size=10, color=ROJO).next_to(pmp_line, RIGHT, buff=0.08)

        dx_h = ancho_graf / (n_pts - 1)
        pts_hum_coords = [
            [-ancho_graf / 2 + 0.3 + i * dx_h, base_hum_y + escala_hum * v, 0]
            for i, v in enumerate(puntos_hum)
        ]
        curva_hum = VMobject(color=TEAL, stroke_width=2.2)
        curva_hum.set_points_as_corners(pts_hum_coords)

        zona_estres = Polygon(
            *[pts_hum_coords[16], pts_hum_coords[17], pts_hum_coords[18],
              pts_hum_coords[19], pts_hum_coords[20],
              [pts_hum_coords[20][0], base_hum_y + escala_hum * 0.25, 0],
              [pts_hum_coords[16][0], base_hum_y + escala_hum * 0.25, 0]],
            fill_color=ROJO, fill_opacity=0.25, stroke_width=0,
        )

        self.play(Create(eje_hx), Create(cc_line), Create(pmp_line),
                  FadeIn(cc_txt), FadeIn(pmp_txt))
        self.play(Create(curva_hum), run_time=2)
        self.play(FadeIn(zona_estres))
        estres_txt = Text("dias de estres", font_size=9, color=ROJO).move_to(
            [pts_hum_coords[18][0], base_hum_y + escala_hum * 0.1, 0])
        self.play(FadeIn(estres_txt))
        self.wait(2.5)
        self.play(*[FadeOut(m) for m in self.mobjects])


# ─────────────────────────────────────────────
# PRESENTACION COMPLETA
# ─────────────────────────────────────────────
class PresentacionCompleta(Scene):
    """Version divulgativa del simulador.
    Uso: manim -pql animaciones/animacion_divulgacion.py PresentacionCompleta
    """
    def construct(self):
        for SceneClass in [
            Titulo,
            EscenarioHidrico,
            CalendarioOferta,
            Combinatorio,
            PreciosEstacionales,
            EstresHidrico,
            DecisionFinal,
            ResultadoFinal,
            RecomendacionFinal,
            Cierre,
        ]:
            SceneClass.construct(self)
