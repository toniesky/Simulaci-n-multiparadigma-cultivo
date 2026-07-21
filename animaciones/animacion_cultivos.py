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
MORADO    = "#ab47bc"
PANEL_BG  = "#161b22"

# Datos ilustrativos de cultivos
CULTIVOS = [
    {
        "nombre":      "Uva de mesa",
        "color":       CELESTE,
        "duracion":    "210 días",
        "rendimiento": "28 t/ha",
        "estacion":    "Nov – Jun",
        "costo":       8,           # unidades relativas (de 10)
    },
    {
        "nombre":      "Palto",
        "color":       VERDE,
        "duracion":    "365 días",
        "rendimiento": "12 t/ha",
        "estacion":    "Todo el año",
        "costo":       6,
    },
    {
        "nombre":      "Nogal",
        "color":       AMBAR,
        "duracion":    "240 días",
        "rendimiento": "5 t/ha",
        "estacion":    "Oct – Abr",
        "costo":       5,
    },
    {
        "nombre":      "Limón",
        "color":       NARANJA,
        "duracion":    "300 días",
        "rendimiento": "20 t/ha",
        "estacion":    "Ago – Dic",
        "costo":       4,
    },
]

BUDGET_MAX = 10          # presupuesto total (unidades relativas)
PRESUPUESTO = 14          # presupuesto del agricultor (unidades)


def make_card(cultivo, width=2.6, height=3.1):
    col = cultivo["color"]
    bg  = Rectangle(
        width=width, height=height,
        color=GRIS_LINE, fill_color=PANEL_BG, fill_opacity=1,
        stroke_width=1.5,
    )
    hdr = Rectangle(
        width=width, height=0.52,
        color=col, fill_color=col, fill_opacity=0.9,
        stroke_width=0,
    ).move_to([0, height / 2 - 0.26, 0])
    hdr_t = Text(cultivo["nombre"], font_size=16, color=FONDO, weight=BOLD)
    hdr_t.move_to(hdr.get_center())

    props = [
        ("⏱", "Duración",    cultivo["duracion"]),
        ("⚖", "Rendimiento", cultivo["rendimiento"]),
        ("📅", "Estación",   cultivo["estacion"]),
    ]
    lines = VGroup()
    for icon, key, val in props:
        key_t = Text(f"{key}:", font_size=13, color=GRIS)
        val_t = Text(val,       font_size=14, color=BLANCO, weight=BOLD)
        row   = VGroup(key_t, val_t).arrange(RIGHT, buff=0.12)
        lines.add(row)
    lines.arrange(DOWN, buff=0.22, aligned_edge=LEFT)
    lines.move_to([0, -0.18, 0])

    # Barra de costo
    cost_lbl  = Text("Costo:", font_size=13, color=GRIS)
    cost_fill = Rectangle(
        width=(cultivo["costo"] / BUDGET_MAX) * (width - 0.45), height=0.19,
        color=col, fill_color=col, fill_opacity=0.85, stroke_width=0,
    )
    cost_row = VGroup(cost_lbl, cost_fill).arrange(RIGHT, buff=0.1)
    cost_row.next_to(lines, DOWN, buff=0.22)

    card = VGroup(bg, hdr, hdr_t, lines, cost_row)
    return card


class EscenaCultivos(Scene):
    def construct(self):
        self.camera.background_color = FONDO

        # ── Título ─────────────────────────────────────────────────────────
        titulo = Text(
            "Cada cultivo es distinto",
            font_size=38, color=BLANCO, weight=BOLD,
        )
        titulo.to_edge(UP, buff=0.42)
        self.play(Write(titulo), run_time=1.0)

        txt1 = Text(
            "Duración, rendimiento, estacionalidad y costos\n"
            "varían para cada cultivo.",
            font_size=21, color=GRIS, line_spacing=1.3,
        )
        txt1.next_to(titulo, DOWN, buff=0.28)
        self.play(FadeIn(txt1), run_time=0.8)
        self.wait(0.3)

        # ── Tarjetas de cultivos ───────────────────────────────────────────
        XS     = [-4.9, -1.65, 1.65, 4.9]
        cards  = []
        cmobs  = []

        for i, (cult, xp) in enumerate(zip(CULTIVOS, XS)):
            card = make_card(cult)
            card.move_to([xp, -0.55, 0])
            cards.append(card)

        for card in cards:
            self.play(FadeIn(card), run_time=0.55)

        self.wait(1.2)

        # Resaltar diferencias — pulsar cada tarjeta brevemente
        for card in cards:
            self.play(card.animate.scale(1.06), run_time=0.18, rate_func=there_and_back)

        self.wait(0.6)

        # ── Parte 2 – Presupuesto ──────────────────────────────────────────
        self.play(FadeOut(txt1), run_time=0.35)

        txt2 = Text(
            "Además, cada agricultor debe ajustarse\n"
            "al presupuesto disponible.",
            font_size=21, color=GRIS, line_spacing=1.3,
        )
        txt2.next_to(titulo, DOWN, buff=0.28)
        self.play(FadeIn(txt2), run_time=0.7)
        self.wait(0.3)

        # Mover cartas hacia arriba para hacer espacio
        self.play(
            *[card.animate.shift(UP * 0.45) for card in cards],
            run_time=0.5,
        )

        # Barra de presupuesto
        BAR_W  = 9.4
        BAR_H  = 0.55
        BAR_Y  = -2.7

        budget_bg = Rectangle(
            width=BAR_W, height=BAR_H,
            color=GRIS_LINE, fill_color=GRIS_LINE, fill_opacity=0.2,
            stroke_width=1.5,
        ).move_to([0, BAR_Y, 0])

        budget_lbl = Text("Presupuesto disponible", font_size=16, color=GRIS)
        budget_lbl.next_to(budget_bg, UP, buff=0.16)

        self.play(FadeIn(budget_bg), FadeIn(budget_lbl), run_time=0.5)

        # Llenar barra con los costos de los cultivos (colores apilados)
        x_cursor = -BAR_W / 2
        seg_mobs = []
        total_w  = 0

        for cult in CULTIVOS:
            sw = (cult["costo"] / PRESUPUESTO) * BAR_W
            seg = Rectangle(
                width=sw, height=BAR_H,
                color=cult["color"], fill_color=cult["color"], fill_opacity=0.82,
                stroke_width=0,
            ).move_to([x_cursor + sw / 2, BAR_Y, 0])
            self.play(GrowFromEdge(seg, LEFT), run_time=0.5)
            x_cursor += sw
            total_w  += sw
            seg_mobs.append(seg)

        # Marcador de límite (borde del presupuesto)
        limit_x = -BAR_W / 2 + BAR_W   # extremo derecho = presupuesto total
        limit_line = DashedLine(
            [limit_x, BAR_Y - BAR_H * 0.7, 0],
            [limit_x, BAR_Y + BAR_H * 0.7, 0],
            color=AMBAR, stroke_width=2.8, dash_length=0.12,
        )
        limit_lbl = Text("Límite", font_size=14, color=AMBAR)
        limit_lbl.next_to(limit_line, UP, buff=0.1)

        self.play(Create(limit_line), FadeIn(limit_lbl), run_time=0.5)

        # Flecha señalando que la suma ocupa parte del presupuesto
        used_pct = int(sum(c["costo"] for c in CULTIVOS) / PRESUPUESTO * 100)
        used_txt = Text(
            f"Combinación actual: {used_pct}% del presupuesto",
            font_size=17, color=AMBAR,
        )
        used_txt.next_to(budget_bg, DOWN, buff=0.28)
        self.play(Write(used_txt), run_time=0.8)

        self.wait(2.2)

        # ── Fade final ─────────────────────────────────────────────────────
        self.play(
            FadeOut(VGroup(
                titulo, txt2,
                *cards,
                budget_bg, budget_lbl, limit_line, limit_lbl,
                *seg_mobs, used_txt,
            )),
            run_time=1.0,
        )
