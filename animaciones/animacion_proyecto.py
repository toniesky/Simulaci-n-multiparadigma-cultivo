"""
Animación Manim — Simulador Multiparadigma de Gestión de Agua
=============================================================
Para renderizar (desde la raíz del proyecto):
  .venv_manim\Scripts\manim -pql animaciones/animacion_proyecto.py ProyectoCompleto   # 480p
  .venv_manim\Scripts\manim -pqh animaciones/animacion_proyecto.py ProyectoCompleto   # 1080p

Salida: animaciones/media/videos/animacion_proyecto/

Requiere Python 3.12 (NO 3.14):
  py -3.12 -m venv .venv_manim
  .venv_manim\Scripts\pip install manim
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


def _caja(label, sub="", color=AZUL_MED, w=3.2, h=1.5, pos=ORIGIN):
    r = RoundedRectangle(corner_radius=0.2, width=w, height=h,
                         fill_color=color, fill_opacity=0.13,
                         stroke_color=color, stroke_width=2).move_to(pos)
    t1 = Text(label, font_size=17, color=color, weight=BOLD).move_to(r.get_center() + (UP * 0.2 if sub else ORIGIN))
    grp = VGroup(r, t1)
    if sub:
        t2 = Text(sub, font_size=13, color=GRIS).move_to(r.get_center() + DOWN * 0.3)
        grp.add(t2)
    return grp


# ─────────────────────────────────────────────
# ESCENA 1: Título
# ─────────────────────────────────────────────
class Titulo(Scene):
    def construct(self):
        titulo = Text(
            "Simulador Multiparadigma\nde Gestión del Agua",
            font_size=46, color=AZUL_OSC, weight=BOLD,
        ).set_color_by_gradient(AZUL_OSC, AZUL_MED)
        subtitulo = Text(
            "Dinámica de Sistemas  ·  Eventos Discretos  ·  Optimización Combinatoria",
            font_size=20, color=GRIS,
        ).next_to(titulo, DOWN, buff=0.5)
        barra = Line(LEFT * 5, RIGHT * 5, color=AZUL_MED, stroke_width=2).next_to(subtitulo, DOWN, buff=0.4)
        autores = Text("Capstone · 2026", font_size=18, color=GRIS).next_to(barra, DOWN, buff=0.3)
        self.play(Write(titulo), run_time=2)
        self.play(FadeIn(subtitulo), Create(barra), FadeIn(autores), run_time=1.5)
        self.wait(2)
        self.play(*[FadeOut(m) for m in self.mobjects])


# ─────────────────────────────────────────────
# ESCENA 2: El Problema
# ─────────────────────────────────────────────
class ElProblema(Scene):
    def construct(self):
        titulo = Text("El Problema", font_size=38, color=AZUL_OSC, weight=BOLD).to_edge(UP, buff=0.4)
        self.play(Write(titulo))
        dims = [
            ("Hidrica",    "Oferta incierta,\ndiscontinua y acotada",    AZUL_MED),
            ("Agronomica", "Estres hidrico\nreduce rendimiento",          VERDE),
            ("Economica",  "Precio estacional:\ncosecha en mes correcto", AMBAR),
        ]
        cajas = VGroup()
        for titulo_d, desc, color in dims:
            caja = RoundedRectangle(corner_radius=0.2, width=3.3, height=2.2,
                                    fill_color=color, fill_opacity=0.12,
                                    stroke_color=color, stroke_width=2)
            t1 = Text(titulo_d, font_size=19, color=color, weight=BOLD).move_to(caja.get_top() + DOWN * 0.45)
            t2 = Text(desc, font_size=15, color=GRIS).move_to(caja.get_center() + DOWN * 0.2)
            cajas.add(VGroup(caja, t1, t2))
        cajas.arrange(RIGHT, buff=0.5).next_to(titulo, DOWN, buff=0.7)
        for c in cajas:
            self.play(FadeIn(c, shift=UP * 0.3), run_time=0.7)
        trade = Text(
            "Optimizar las 3 dimensiones simultaneamente, por escenario de oferta",
            font_size=18, color=AZUL_OSC,
        ).to_edge(DOWN, buff=0.7)
        self.play(Write(trade))
        self.wait(2)
        self.play(*[FadeOut(m) for m in self.mobjects])


# ─────────────────────────────────────────────
# ESCENA 3: Datos de Entrada
# ─────────────────────────────────────────────
class DatosEntrada(Scene):
    def construct(self):
        titulo = Text("Datos de Entrada al Sistema", font_size=34, color=AZUL_OSC, weight=BOLD).to_edge(UP, buff=0.4)
        self.play(Write(titulo))
        col_clima = VGroup(
            Text("Datos Climaticos", font_size=17, color=AZUL_MED, weight=BOLD),
            Text("Temperatura max/min", font_size=13, color=GRIS),
            Text("Humedad relativa", font_size=13, color=GRIS),
            Text("Velocidad del viento", font_size=13, color=GRIS),
            Text("Radiacion solar", font_size=13, color=GRIS),
            Text("-> ETo diaria (Penman-M.)", font_size=13, color=AZUL_MED, weight=BOLD),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.18)
        col_sistema = VGroup(
            Text("Sistema de Riego", font_size=17, color=LILA, weight=BOLD),
            Text("N acciones de agua", font_size=13, color=GRIS),
            Text("Volumen por accion (m3)", font_size=13, color=GRIS),
            Text("% desmarque inicial/final", font_size=13, color=GRIS),
            Text("Calendario de paradas", font_size=13, color=GRIS),
            Text("Frecuencia de turno (dias)", font_size=13, color=LILA, weight=BOLD),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.18)
        col_regante = VGroup(
            Text("Datos del Regante", font_size=17, color=AMBAR, weight=BOLD),
            Text("Hectareas totales", font_size=13, color=GRIS),
            Text("Fraccion cultivada", font_size=13, color=GRIS),
            Text("Capacidad estanque (m3)", font_size=13, color=GRIS),
            Text("Nivel estanque inicial", font_size=13, color=GRIS),
            Text("Stock subterra neo (m3)", font_size=13, color=AMBAR, weight=BOLD),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.18)
        cols = VGroup(col_clima, col_sistema, col_regante).arrange(RIGHT, buff=0.7, aligned_edge=UP)
        cols.next_to(titulo, DOWN, buff=0.5)
        for col, color in [(col_clima, AZUL_CLAR), (col_sistema, LILA), (col_regante, AMBAR_CL)]:
            bg = SurroundingRectangle(col, corner_radius=0.15, color=color, fill_color=color,
                                      fill_opacity=0.08, buff=0.2)
            self.play(Create(bg), FadeIn(col, shift=UP * 0.2), run_time=0.8)
        nota = Text("Todos los parametros se editan desde la interfaz Dash sin tocar el codigo",
                    font_size=15, color=VERDE).to_edge(DOWN, buff=0.5)
        self.play(Write(nota))
        self.wait(2.5)
        self.play(*[FadeOut(m) for m in self.mobjects])


# ─────────────────────────────────────────────
# ESCENA 4: Módulo 1 — Oferta Hídrica
# ─────────────────────────────────────────────
class Modulo1Oferta(Scene):
    def construct(self):
        titulo = Text("Modulo 1 - Oferta Hidrica", font_size=34, color=AZUL_MED, weight=BOLD).to_edge(UP, buff=0.35)
        sub = Text("Dinamica de Sistemas - stocks y flujos diarios", font_size=17, color=GRIS).next_to(titulo, DOWN, buff=0.15)
        self.play(Write(titulo), FadeIn(sub))
        stock_canal = Rectangle(width=2.2, height=1.3, fill_color=AZUL_CLAR, fill_opacity=0.55,
                                 stroke_color=AZUL_MED, stroke_width=2.5).shift(LEFT * 2.5 + DOWN * 0.3)
        lbl_canal = Text("Canal\n(stock)", font_size=15, color=AZUL_OSC, weight=BOLD).move_to(stock_canal)
        stock_est = Rectangle(width=1.8, height=1.0, fill_color=VERDE_CL, fill_opacity=0.6,
                               stroke_color=VERDE, stroke_width=2).shift(RIGHT * 3.2 + DOWN * 0.3)
        lbl_est = Text("Estanque\npredial", font_size=13, color=VERDE).move_to(stock_est)
        stock_sub = Rectangle(width=1.6, height=0.8, fill_color=AMBAR_CL, fill_opacity=0.6,
                               stroke_color=AMBAR, stroke_width=1.5).shift(RIGHT * 3.2 + DOWN * 2.2)
        lbl_sub = Text("Agua\nsubterranea", font_size=12, color=AMBAR).move_to(stock_sub)
        self.play(FadeIn(stock_canal), Write(lbl_canal))
        self.play(FadeIn(stock_est),   Write(lbl_est))
        self.play(FadeIn(stock_sub),   Write(lbl_sub))
        flecha_entrada = Arrow(LEFT * 5.3 + DOWN * 0.3, stock_canal.get_left(), buff=0,
                                color=AZUL_MED, stroke_width=3)
        lbl_desmarque = Text("Desmarque\n(acciones x m3)", font_size=12, color=AZUL_MED).next_to(flecha_entrada, UP, buff=0.1)
        flecha_riego = Arrow(stock_canal.get_right(), stock_est.get_left(), buff=0,
                              color=VERDE, stroke_width=2.5)
        lbl_riego = Text("Turno de riego", font_size=12, color=VERDE).next_to(flecha_riego, UP, buff=0.1)
        flecha_perdida = Arrow(stock_canal.get_bottom(), stock_canal.get_bottom() + DOWN * 0.9,
                                color=ROJO, stroke_width=2)
        lbl_perdida = Text("Perdidas\n(cond. + filtr.)", font_size=11, color=ROJO).next_to(flecha_perdida, LEFT, buff=0.1)
        flecha_sub2 = Arrow(stock_sub.get_top(), stock_est.get_bottom(), buff=0.05,
                             color=AMBAR, stroke_width=2)
        lbl_sub2 = Text("Recarga\nsubterranea", font_size=11, color=AMBAR).next_to(flecha_sub2, RIGHT, buff=0.05)
        self.play(Create(flecha_entrada), Write(lbl_desmarque))
        self.play(Create(flecha_riego),   Write(lbl_riego))
        self.play(Create(flecha_perdida), Write(lbl_perdida))
        self.play(Create(flecha_sub2),    Write(lbl_sub2))
        parada_box = RoundedRectangle(corner_radius=0.15, width=2.2, height=0.6,
                                       fill_color=ROJO, fill_opacity=0.15,
                                       stroke_color=ROJO, stroke_width=1.5).shift(DOWN * 2.5 + LEFT * 2.5)
        parada_lbl = Text("Paradas\nprogramadas", font_size=12, color=ROJO).move_to(parada_box)
        self.play(FadeIn(VGroup(parada_box, parada_lbl)))
        esc_grp = VGroup(
            Text("5 escenarios de % desmarque:", font_size=14, color=AMBAR, weight=BOLD),
            VGroup(*[Text(f"Esc {s:+d}", font_size=13, color=AMBAR) for s in [-2, -1, 0, 1, 2]]
                   ).arrange(RIGHT, buff=0.35),
        ).arrange(DOWN, buff=0.2).to_edge(DOWN, buff=0.8).to_edge(RIGHT, buff=0.6)
        self.play(FadeIn(esc_grp))
        csv_lbl = Text("->  CalendarioOferta.csv  (oferta m3/dia x 5 escenarios)",
                        font_size=14, color=AMBAR, weight=BOLD).to_edge(DOWN, buff=0.25)
        self.play(Write(csv_lbl))
        self.wait(2)
        self.play(*[FadeOut(m) for m in self.mobjects])


# ─────────────────────────────────────────────
# ESCENA 5: Cola de Riego
# ─────────────────────────────────────────────
class ColaDeRiego(Scene):
    def construct(self):
        titulo = Text("Distribucion del Agua en el Predio", font_size=32, color=AZUL_MED, weight=BOLD).to_edge(UP, buff=0.4)
        self.play(Write(titulo))
        dias_labels = ["Lun", "Mar", "Mie", "Jue", "Vie", "Sab", "Dom", "Lun", "Mar", "Mie", "Jue"]
        tipos = ["turno", "nada", "nada", "parada", "nada", "turno", "nada", "nada", "nada", "parada", "nada"]
        colores_tipo = {"turno": AZUL_MED, "nada": GRIS, "parada": ROJO}
        barras = VGroup()
        for d, t in zip(dias_labels, tipos):
            alto = 1.2 if t == "turno" else (0.3 if t == "parada" else 0.6)
            rect = Rectangle(width=0.65, height=alto,
                              fill_color=colores_tipo[t], fill_opacity=0.7,
                              stroke_color=colores_tipo[t], stroke_width=1.2)
            lbl = Text(d, font_size=10, color=GRIS)
            barras.add(VGroup(rect, lbl).arrange(DOWN, buff=0.08))
        barras.arrange(RIGHT, buff=0.1).shift(UP * 0.5)
        self.play(LaggedStartMap(FadeIn, barras, lag_ratio=0.08), run_time=1.2)
        leyenda = VGroup(
            VGroup(Rectangle(width=0.4, height=0.3, fill_color=AZUL_MED, fill_opacity=0.7, stroke_width=0),
                   Text("Turno de riego", font_size=13, color=AZUL_MED)).arrange(RIGHT, buff=0.15),
            VGroup(Rectangle(width=0.4, height=0.3, fill_color=ROJO, fill_opacity=0.7, stroke_width=0),
                   Text("Dia de parada", font_size=13, color=ROJO)).arrange(RIGHT, buff=0.15),
            VGroup(Rectangle(width=0.4, height=0.3, fill_color=GRIS, fill_opacity=0.4, stroke_width=0),
                   Text("Sin riego programado", font_size=13, color=GRIS)).arrange(RIGHT, buff=0.15),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.15).to_edge(RIGHT, buff=0.5).shift(UP * 0.5)
        self.play(FadeIn(leyenda))
        flujos = VGroup(
            Text("Dia de turno:", font_size=14, color=AZUL_MED, weight=BOLD),
            Text("  Canal -> Riego directo al suelo + llenado del estanque", font_size=13, color=AZUL_MED),
            Text("Dia de parada / sin turno:", font_size=14, color=ROJO, weight=BOLD),
            Text("  Sin canal -> Estanque + agua subterranea cubren el deficit", font_size=13, color=ROJO),
            Text("Balance diario:", font_size=14, color=VERDE, weight=BOLD),
            Text("  Aplicado = min(ETc requerida, agua disponible)", font_size=13, color=VERDE),
            Text("  Deficit = ETc - Aplicado  ->  penaliza produccion", font_size=13, color=ROJO),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.20).to_edge(LEFT, buff=0.5).to_edge(DOWN, buff=0.4)
        for linea in flujos:
            self.play(FadeIn(linea, shift=RIGHT * 0.2), run_time=0.38)
        self.wait(2)
        self.play(*[FadeOut(m) for m in self.mobjects])


# ─────────────────────────────────────────────
# ESCENA 6: Restricción Estacional
# ─────────────────────────────────────────────
class RestriccionEstacional(Scene):
    def construct(self):
        titulo = Text("Restriccion Estacional de Cultivos", font_size=32, color=AMBAR, weight=BOLD).to_edge(UP, buff=0.4)
        self.play(Write(titulo))
        meses = ["Ene","Feb","Mar","Abr","May","Jun","Jul","Ago","Sep","Oct","Nov","Dic"]
        eje = VGroup(*[Text(m, font_size=12, color=GRIS) for m in meses]).arrange(RIGHT, buff=0.25)
        eje.next_to(titulo, DOWN, buff=0.5)
        self.play(FadeIn(eje))
        cultivos_data = [
            ("Lechuga",  [1,1,1,1,1,0,0,0,1,1,1,1], AZUL_MED),
            ("Brocoli",  [1,1,0,0,0,0,0,0,1,1,1,1], VERDE),
            ("Acelga",   [1,1,1,1,0,0,0,1,1,1,1,1], AMBAR),
            ("Espinaca", [1,1,0,0,0,0,0,0,0,1,1,1], LILA),
        ]
        cult_grps = VGroup()
        for nombre, disponible, color in cultivos_data:
            fila = VGroup(*[
                Rectangle(width=0.5, height=0.3,
                          fill_color=color if d else GRIS_CL,
                          fill_opacity=0.8 if d else 0.3,
                          stroke_color=color if d else GRIS, stroke_width=0.8)
                for d in disponible
            ]).arrange(RIGHT, buff=0.12)
            lbl = Text(nombre, font_size=13, color=color, weight=BOLD)
            lbl.next_to(fila, LEFT, buff=0.3)
            cult_grps.add(VGroup(lbl, fila))
        cult_grps.arrange(DOWN, buff=0.22, aligned_edge=RIGHT).next_to(eje, DOWN, buff=0.3)
        for g in cult_grps:
            self.play(FadeIn(g, shift=UP * 0.15), run_time=0.5)
        precio_box = VGroup(
            Text("Precio estacional en mes de cosecha:", font_size=14, color=ROJO, weight=BOLD),
            Text("Mes de inicio + duracion del cultivo = mes de cosecha", font_size=13, color=AMBAR),
            Text("Cosecha en verano -> precio bajo   (sobreoferta)", font_size=13, color=ROJO),
            Text("Cosecha en otono  -> precio alto    (escasez)",    font_size=13, color=VERDE),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.18).to_edge(DOWN, buff=0.3)
        self.play(FadeIn(precio_box))
        self.wait(2.5)
        self.play(*[FadeOut(m) for m in self.mobjects])


# ─────────────────────────────────────────────
# ESCENA 7: Balance Hídrico FAO-56
# ─────────────────────────────────────────────
class BalanceHidrico(Scene):
    def construct(self):
        titulo = Text("Balance Hidrico Diario - FAO-56", font_size=32, color=VERDE, weight=BOLD).to_edge(UP, buff=0.4)
        self.play(Write(titulo))
        capa_ev = Rectangle(width=4.5, height=0.75, fill_color=AMBAR_CL, fill_opacity=0.7,
                             stroke_color=AMBAR, stroke_width=2).shift(LEFT * 1.5 + UP * 0.8)
        capa_rz = Rectangle(width=4.5, height=1.5, fill_color=VERDE_CL, fill_opacity=0.5,
                             stroke_color=VERDE, stroke_width=2).shift(LEFT * 1.5 + DOWN * 0.2)
        lbl_ev = Text("Capa evaporante (Ze = 0.15 m)  ->  Ke diario", font_size=13, color=AMBAR).move_to(capa_ev)
        lbl_rz = Text("Zona radicular (Dr)  ->  balance Ks y Kcb", font_size=13, color=VERDE).move_to(capa_rz)
        self.play(FadeIn(capa_ev), Write(lbl_ev))
        self.play(FadeIn(capa_rz), Write(lbl_rz))
        eq_ks = MathTex(
            r"K_s = \left(\frac{TAW - D_r}{TAW - RAW}\right)^{\alpha}",
            font_size=30, color=AZUL_OSC
        ).to_edge(RIGHT, buff=0.5).shift(UP * 0.6)
        eq_etc = MathTex(
            r"ET_c = (K_{cb} \cdot K_s + K_e) \cdot ET_o",
            font_size=28, color=VERDE
        ).next_to(eq_ks, DOWN, buff=0.4)
        eq_dr = MathTex(
            r"D_r(t+1) = D_r(t) + ET_c - \text{Aplicado}",
            font_size=26, color=AZUL_MED
        ).next_to(eq_etc, DOWN, buff=0.4)
        self.play(Write(eq_ks), run_time=1)
        self.play(Write(eq_etc), run_time=0.9)
        self.play(Write(eq_dr), run_time=0.9)
        etapas_lbl = Text("Etapas fenologicas (FAO-56):", font_size=14, color=GRIS).to_edge(DOWN, buff=1.3).to_edge(LEFT, buff=0.5)
        etapas = VGroup(*[
            VGroup(
                Rectangle(width=w, height=0.45, fill_color=c, fill_opacity=0.65,
                          stroke_color=c, stroke_width=1.5),
                Text(n, font_size=12, color=c),
            ).arrange(DOWN, buff=0.08)
            for w, c, n in [(0.9, AZUL_CLAR, "Ini"), (1.4, VERDE, "Des"),
                             (1.9, VERDE_CL, "Med"), (0.9, AMBAR, "Fin")]
        ]).arrange(RIGHT, buff=0.04).next_to(etapas_lbl, RIGHT, buff=0.5)
        self.play(Write(etapas_lbl))
        self.play(LaggedStartMap(FadeIn, etapas, lag_ratio=0.3), run_time=1)
        nota = Text("Ks < 1  ->  estres  ->  ETc reducida  ->  menor rendimiento y produccion",
                    font_size=13, color=ROJO).to_edge(DOWN, buff=0.3)
        self.play(Write(nota))
        self.wait(2.5)
        self.play(*[FadeOut(m) for m in self.mobjects])


# ─────────────────────────────────────────────
# ESCENA 8: Optimización Combinatoria
# ─────────────────────────────────────────────
class OptimizacionCombinatorio(Scene):
    def construct(self):
        titulo = Text("Optimizacion Combinatoria del Portafolio",
                      font_size=30, color=VERDE, weight=BOLD).to_edge(UP, buff=0.4)
        self.play(Write(titulo))
        n_part = 4
        particiones = VGroup(*[
            VGroup(
                Square(side_length=1.1, fill_color=GRIS_CL, fill_opacity=0.5,
                       stroke_color=GRIS, stroke_width=1.5),
                Text(f"P{i+1}", font_size=15, color=GRIS),
            ).arrange(DOWN, buff=0.08)
            for i in range(n_part)
        ]).arrange(RIGHT, buff=0.45).shift(UP * 1.5)
        self.play(LaggedStartMap(FadeIn, particiones, lag_ratio=0.2), run_time=0.8)
        combos = [("Brocoli", VERDE), ("Lechuga", AZUL_MED), ("No plantar", GRIS), ("Lechuga", AZUL_MED)]
        for i, (nombre, color) in enumerate(combos):
            lbl = Text(nombre, font_size=12, color=color, weight=BOLD)
            lbl.move_to(particiones[i][0].get_center())
            self.play(FadeIn(lbl, scale=0.8), run_time=0.3)
        pipeline = VGroup(
            Text("Para cada combinacion:", font_size=15, color=AZUL_OSC, weight=BOLD),
            Text("  1.  Balance hidrico FAO-56  (365 dias de simulacion)", font_size=13, color=GRIS),
            Text("  2.  Calcular ETc real  ->  produccion con estres hidrico", font_size=13, color=GRIS),
            Text("  3.  Mes de cosecha  ->  precio estacional del mercado",   font_size=13, color=AMBAR),
            Text("  4.  Ingreso = precio x produccion x hectareas efectivas", font_size=13, color=VERDE),
            Text("  5.  Score = Ingreso - Costo   (si Costo <= Presupuesto)", font_size=13, color=VERDE),
            Text("  6.  Score = 0  si todo es No plantar",                    font_size=13, color=ROJO),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.22).shift(DOWN * 0.4).to_edge(LEFT, buff=0.5)
        for linea in pipeline:
            self.play(FadeIn(linea, shift=RIGHT * 0.2), run_time=0.38)
        score_box = VGroup(
            RoundedRectangle(corner_radius=0.15, width=5.5, height=0.7,
                             fill_color=VERDE, fill_opacity=0.15,
                             stroke_color=VERDE, stroke_width=2),
            Text("Mejor combo: Score $4.2M   Costo $2.8M   dentro del presupuesto",
                 font_size=13, color=VERDE, weight=BOLD),
        )
        score_box[1].move_to(score_box[0])
        score_box.to_edge(DOWN, buff=0.25)
        self.play(FadeIn(score_box))
        combos_txt = Text("210 combinaciones evaluadas por escenario  (6 cultivos + No plantar x 4 particiones)",
                          font_size=12, color=GRIS).next_to(score_box, UP, buff=0.15)
        self.play(Write(combos_txt))
        self.wait(2.5)
        self.play(*[FadeOut(m) for m in self.mobjects])


# ─────────────────────────────────────────────
# ESCENA 9: Resultado por Escenario
# ─────────────────────────────────────────────
class ResultadoPorEscenario(Scene):
    def construct(self):
        titulo = Text("Resultado por Escenario de Oferta", font_size=32, color=AZUL_OSC, weight=BOLD).to_edge(UP, buff=0.4)
        self.play(Write(titulo))
        escenarios = [
            ("Esc -2", 1.8, ROJO,    "Solo lechuga  (agua muy escasa)"),
            ("Esc -1", 2.9, AMBAR,   "Lechuga x3 + No plantar"),
            ("Esc  0", 4.2, VERDE,   "Brocoli + Lechuga x2 + Acelga"),
            ("Esc +1", 5.1, VERDE,   "Brocoli x2 + Lechuga + Espinaca"),
            ("Esc +2", 5.6, AZUL_MED,"Brocoli x2 + Acelga + Espinaca"),
        ]
        barras = VGroup()
        for label, score, color, detalle in escenarios:
            barra = Rectangle(width=score * 0.7, height=0.55,
                              fill_color=color, fill_opacity=0.75,
                              stroke_color=color, stroke_width=1.5)
            lbl_esc   = Text(label,          font_size=13, color=color, weight=BOLD).next_to(barra, LEFT, buff=0.15)
            lbl_score = Text(f"${score:.1f}M", font_size=12, color=color).next_to(barra, RIGHT, buff=0.12)
            lbl_det   = Text(detalle,         font_size=11, color=GRIS).next_to(barra, RIGHT, buff=1.5)
            barras.add(VGroup(lbl_esc, barra, lbl_score, lbl_det))
        barras.arrange(DOWN, aligned_edge=LEFT, buff=0.3).shift(LEFT * 0.5)
        for f in barras:
            self.play(FadeIn(f, shift=RIGHT * 0.3), run_time=0.5)
        reporte_box = VGroup(
            RoundedRectangle(corner_radius=0.15, width=7, height=0.65,
                             fill_color=AZUL_MED, fill_opacity=0.12,
                             stroke_color=AZUL_MED, stroke_width=2),
            Text("->  ReporteParticiones.html  se abre automaticamente en el navegador",
                 font_size=13, color=AZUL_MED, weight=BOLD),
        )
        reporte_box[1].move_to(reporte_box[0])
        reporte_box.to_edge(DOWN, buff=0.3)
        self.play(FadeIn(reporte_box))
        self.wait(2.5)
        self.play(*[FadeOut(m) for m in self.mobjects])


# ─────────────────────────────────────────────
# ESCENA 10: Interfaz Dash
# ─────────────────────────────────────────────
class InterfazDash(Scene):
    def construct(self):
        titulo = Text("Interfaz - app.py", font_size=34, color=AZUL_OSC, weight=BOLD).to_edge(UP, buff=0.4)
        self.play(Write(titulo))
        p1 = _caja("Modulo 1\nOferta Hidrica",    "Acciones, desmarques,\nfrecuencia turno", AZUL_MED, w=3.0, h=2.2, pos=LEFT  * 3.8 + UP * 0.3)
        p2 = _caja("Modulo 2\nSimulacion Cultivo", "Presupuesto, suelo,\nparticiones, clima", VERDE,   w=3.0, h=2.2, pos=ORIGIN + UP * 0.3)
        p3 = _caja("Datos del\nRegante",            "Hectareas, estanque,\nstock subterra neo",AMBAR,   w=3.0, h=2.2, pos=RIGHT * 3.8 + UP * 0.3)
        for p in [p1, p2, p3]:
            self.play(FadeIn(p, shift=UP * 0.3), run_time=0.6)
        btn_g = RoundedRectangle(corner_radius=0.2, width=2.8, height=0.65,
                                  fill_color=VERDE, fill_opacity=0.8,
                                  stroke_color=VERDE).shift(LEFT * 1.8 + DOWN * 2.1)
        btn_s = RoundedRectangle(corner_radius=0.2, width=2.8, height=0.65,
                                  fill_color=AZUL_MED, fill_opacity=0.8,
                                  stroke_color=AZUL_MED).shift(RIGHT * 1.8 + DOWN * 2.1)
        lbl_g = Text("Guardar Todo", font_size=17, color=WHITE, weight=BOLD).move_to(btn_g)
        lbl_s = Text("Simular Todo", font_size=17, color=WHITE, weight=BOLD).move_to(btn_s)
        self.play(FadeIn(btn_g), Write(lbl_g), FadeIn(btn_s), Write(lbl_s))
        self.wait(0.4)
        self.play(btn_g.animate.set_fill(opacity=1.0), run_time=0.2)
        archivos = VGroup(
            Text("ok  initial_values.py  (Modulo 1)", font_size=12, color=VERDE),
            Text("ok  parametros.py       (Modulo 2)", font_size=12, color=VERDE),
            Text("ok  regantes.csv        (Regante)",  font_size=12, color=VERDE),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.12).next_to(btn_g, DOWN, buff=0.2)
        self.play(LaggedStartMap(FadeIn, archivos, lag_ratio=0.2), run_time=0.7)
        self.play(btn_g.animate.set_fill(opacity=0.8), run_time=0.2)
        self.wait(0.4)
        self.play(btn_s.animate.set_fill(opacity=1.0), run_time=0.2)
        cmd_txt = Text("-> Abre CMD\n-> Modulo 1 + animacion\n-> Modulo 2 + reporte HTML", font_size=12, color=AZUL_MED)
        cmd_txt.next_to(btn_s, DOWN, buff=0.2)
        self.play(FadeIn(cmd_txt), run_time=0.6)
        self.play(btn_s.animate.set_fill(opacity=0.8), run_time=0.2)
        self.wait(2)
        self.play(*[FadeOut(m) for m in self.mobjects])


# ─────────────────────────────────────────────
# ESCENA 11: Cierre
# ─────────────────────────────────────────────
class Cierre(Scene):
    def construct(self):
        titulo = Text("Flujo Completo del Sistema", font_size=36, color=AZUL_OSC, weight=BOLD)
        self.play(Write(titulo))
        self.play(titulo.animate.to_edge(UP, buff=0.45))
        pasos = [
            ("1.", "Datos climaticos  ->  ETo diaria (Penman-Monteith)",                 AZUL_MED),
            ("2.", "Modulo 1: stocks y flujos  ->  CalendarioOferta.csv x 5 escenarios", AZUL_MED),
            ("3.", "Turnos de riego + paradas  ->  disponibilidad real dia a dia",        LILA),
            ("4.", "Mes de inicio  ->  cultivos disponibles  ->  mes de cosecha",         AMBAR),
            ("5.", "Balance FAO-56 diario: ETc, Ks, deficit hidrico",                     VERDE),
            ("6.", "Combinatorio: 210 combos x precio estacional  ->  score maximo",      VERDE),
            ("7.", "Resultado: portafolio optimo por escenario en ReporteHTML",            ROJO),
        ]
        filas = VGroup()
        for num, texto, color in pasos:
            n = Text(num,   font_size=20, color=color, weight=BOLD)
            t = Text(texto, font_size=18, color=AZUL_OSC)
            filas.add(VGroup(n, t).arrange(RIGHT, buff=0.3))
        filas.arrange(DOWN, aligned_edge=LEFT, buff=0.28).next_to(titulo, DOWN, buff=0.5)
        for fila in filas:
            self.play(FadeIn(fila, shift=RIGHT * 0.3), run_time=0.42)
        fin = Text("Capstone - Simulacion Multiparadigma de Gestion del Agua - 2026",
                   font_size=16, color=GRIS).to_edge(DOWN, buff=0.35)
        self.play(FadeIn(fin))
        self.wait(3)
        self.play(*[FadeOut(m) for m in self.mobjects])


# ─────────────────────────────────────────────
# ESCENA COMPLETA
# ─────────────────────────────────────────────
class ProyectoCompleto(Scene):
    """Renderiza todas las escenas en un unico video.
    Uso: manim -pql animaciones/animacion_proyecto.py ProyectoCompleto
    """
    def construct(self):
        for SceneClass in [
            Titulo,
            ElProblema,
            DatosEntrada,
            Modulo1Oferta,
            ColaDeRiego,
            RestriccionEstacional,
            BalanceHidrico,
            OptimizacionCombinatorio,
            ResultadoPorEscenario,
            InterfazDash,
            Cierre,
        ]:
            SceneClass.construct(self)
