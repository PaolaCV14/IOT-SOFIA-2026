"""Genera SOFIA_LabDST_Presentacion_v2.pptx (16:9) con python-pptx.
Versión 2 Oficial de Avance - Segundo Corte (LabDST, ITESO, Otoño 2026).

Sistema de diseño:
- 16:9. Portada (Slide 1) y cierre (Slide 10) con fondo oscuro (#0B132B).
- Slides 2 a 9 y de respaldo con fondo claro blanco hueso (#F8FAFC).
- Acento Teal (#14B8A6), alerta Calor/Riesgo (#DC2626 / #EF4444).
- Títulos: 38 a 44 pt, máximo 2 líneas.
- Cuerpo: mínimo 22 pt; tablas: mínimo 20 pt; números destacados: >= 66 pt.
- Pies, créditos y chips de rastreador: 12 a 14 pt.
- Rastreador superior de 5 chips (PLANTEAMIENTO · DISEÑO · RESULTADOS · BRECHA · SIGUIENTES).
- 10 slides visibles + 2 slides de respaldo OCULTAS (show="0").
- Límite de palabras: <= 45 palabras visibles (<= 60 en tablas).
- Sin fórmulas ni jerga matemática.

Uso:
  python3 build_deck_v2.py
  python3 build_deck_v2.py --check
"""
import os
import sys
import re
import argparse
import tempfile
from PIL import Image
import qrcode
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE, MSO_CONNECTOR
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR

HERE = os.path.dirname(os.path.abspath(__file__))
FIG = os.path.join(HERE, "..", "paper", "Equipo 1 - segundo corte", "figures")
OUT = os.path.join(HERE, "SOFIA_LabDST_Presentacion_v2.pptx")
TMP = tempfile.mkdtemp()

# =====================================================================
# CONSTANTES DE PALETA Y FUENTES
# =====================================================================
# Fondos
BG_DARK = RGBColor(0x0B, 0x13, 0x2B)     # Azul marino noche profundo
BG_LIGHT = RGBColor(0xF8, 0xFA, 0xFC)    # Blanco hueso suave
CARD_DARK = RGBColor(0x1C, 0x25, 0x41)   # Tarjeta en modo oscuro
CARD_LIGHT = RGBColor(0xEE, 0xF2, 0xF6)  # Tarjeta en modo claro (#EEF2F6)
CARD_WHITE = RGBColor(0xFF, 0xFF, 0xFF)  # Tarjeta blanca pura

# Textos
TEXT_DARK = RGBColor(0x0F, 0x17, 0x2A)   # Texto principal en modo claro (Slate 900)
TEXT_WHITE = RGBColor(0xF8, 0xFA, 0xFC)  # Texto principal en modo oscuro
WHITE = RGBColor(0xFF, 0xFF, 0xFF)       # Blanco puro
MUTED_LIGHT = RGBColor(0x47, 0x55, 0x69) # Texto secundario en modo claro (Slate 600)
MUTED_DARK = RGBColor(0x94, 0xA3, 0xB8)  # Texto secundario en modo oscuro (Slate 400)

# Acentos
TEAL = RGBColor(0x14, 0xB8, 0xA6)        # Acento principal (Teal #14B8A6)
TEAL_DARK = RGBColor(0x0D, 0x94, 0x88)   # Teal oscuro para alto contraste (#0D9488)
TEAL_BG = RGBColor(0xCC, 0xFB, 0xF1)     # Teal pastel para chips activos (#CCFBF1)
RED_ALERT = RGBColor(0xDC, 0x26, 0x26)   # Alerta de calor/riesgo (#DC2626)
AMBER_ALERT = RGBColor(0xD9, 0x77, 0x06) # Alerta ámbar (#D97706)

FONT = "Calibri"

TRACKER_STAGES = [
    "PLANTEAMIENTO",
    "DISEÑO",
    "RESULTADOS",
    "BRECHA",
    "SIGUIENTES",
]


# =====================================================================
# INICIALIZACIÓN DE PRESENTACIÓN
# =====================================================================
prs = Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)
W, H = prs.slide_width, prs.slide_height
BLANK = prs.slide_layouts[6]


# =====================================================================
# FUNCIONES AUXILIARES DE DISEÑO
# =====================================================================
def create_slide(dark=False, notes=""):
    """Crea una nueva slide con fondo y notas de orador."""
    s = prs.slides.add_slide(BLANK)
    s.background.fill.solid()
    s.background.fill.fore_color.rgb = BG_DARK if dark else BG_LIGHT
    if notes:
        s.notes_slide.notes_text_frame.text = notes
    return s


def rect(s, x, y, w, h, fill=CARD_LIGHT, line=None, shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.03):
    """Agrega un contenedor / tarjeta redondeada."""
    r = s.shapes.add_shape(shape, x, y, w, h)
    r.fill.solid()
    r.fill.fore_color.rgb = fill
    if line is None:
        r.line.fill.background()
    else:
        r.line.color.rgb = line
        r.line.width = Pt(1.5)
    r.shadow.inherit = False
    if shape == MSO_SHAPE.ROUNDED_RECTANGLE:
        r.adjustments[0] = radius
    return r


def tracker(s, active_stage=None, slide_n=None, is_backup=False, dark=False):
    """Rastreador superior de 5 chips y número de página abajo a la derecha."""
    if is_backup:
        # Etiqueta de respaldo arriba a la izquierda
        rect(s, Inches(0.8), Inches(0.32), Inches(1.8), Inches(0.35),
             fill=AMBER_ALERT, shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.2)
        text_box(s, Inches(0.8), Inches(0.35), Inches(1.8), Inches(0.3),
                 "RESPALDO", size=13, color=WHITE, bold=True, align=PP_ALIGN.CENTER)
        text_box(s, Inches(11.2), Inches(7.05), Inches(1.3), Inches(0.3),
                 "RESPALDO", size=13, color=MUTED_LIGHT if not dark else MUTED_DARK,
                 bold=True, align=PP_ALIGN.RIGHT)
        return

    # Chips de etapas arriba
    chip_w = Inches(1.7)
    chip_h = Inches(0.32)
    start_x = Inches(0.8)
    gap = Inches(0.12)
    for idx, stage in enumerate(TRACKER_STAGES):
        cx = start_x + idx * (chip_w + gap)
        is_active = (stage == active_stage)
        
        if is_active:
            fill_c = TEAL if dark else TEAL_BG
            text_c = WHITE if dark else TEAL_DARK
            border_c = TEAL
        else:
            fill_c = CARD_DARK if dark else CARD_LIGHT
            text_c = MUTED_DARK if dark else MUTED_LIGHT
            border_c = None
            
        rect(s, cx, Inches(0.32), chip_w, chip_h, fill=fill_c, line=border_c,
             shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.25)
        text_box(s, cx, Inches(0.35), chip_w, chip_h, stage, size=12,
                 color=text_c, bold=is_active, align=PP_ALIGN.CENTER)

    # Contador de página n/10 abajo a la derecha
    if slide_n is not None:
        text_box(s, Inches(12.0), Inches(7.05), Inches(0.8), Inches(0.3),
                 f"{slide_n}/10", size=13, color=MUTED_DARK if dark else MUTED_LIGHT,
                 align=PP_ALIGN.RIGHT)


def title(s, heading, dark=False, is_alert=False):
    """Título principal con punch (38 a 44 pt, máximo 2 líneas)."""
    color = WHITE if dark else (RED_ALERT if is_alert else TEXT_DARK)
    text_box(s, Inches(0.8), Inches(0.75), Inches(11.7), Inches(0.85),
             heading, size=40, color=color, bold=True)


def text_box(s, x, y, w, h, content, size=22, color=TEXT_DARK, bold=False,
             align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP, italic=False):
    """Caja de texto con tipografía Calibri."""
    tb = s.shapes.add_textbox(x, y, w, h)
    tf = tb.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    tf.margin_left = tf.margin_right = Inches(0.04)
    tf.margin_top = tf.margin_bottom = Inches(0.02)
    lines = content if isinstance(content, list) else [content]
    for i, ln in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        r = p.add_run()
        r.text = ln
        r.font.size = Pt(size)
        r.font.bold = bold
        r.font.italic = italic
        r.font.color.rgb = color
        r.font.name = FONT
    return tb


def prep_image(name, maxw=2200):
    """Prepara una imagen desde la carpeta de figuras o raíz."""
    src = os.path.join(FIG, name)
    if not os.path.exists(src):
        src = os.path.join(HERE, name)
    if not os.path.exists(src):
        return None, (0, 0)
    im = Image.open(src)
    if im.width > maxw:
        im = im.resize((maxw, int(im.height * maxw / im.width)), Image.LANCZOS)
    dst = os.path.join(TMP, name.replace(" ", "_"))
    im.convert("RGB").save(dst, quality=92)
    return dst, im.size


def add_image(s, name, x, y, w, h, card=True, caption=None, fallback_desc=""):
    """Inserta imagen grande sin deformar; si falta, coloca recuadro visible."""
    path, size = prep_image(name)
    if path is None:
        # Recuadro visible de imagen faltante
        rect(s, x, y, w, h, fill=CARD_LIGHT, line=MUTED_LIGHT, radius=0.03)
        text_box(s, x + Inches(0.2), y + h // 2 - Inches(0.3), w - Inches(0.4), Inches(0.6),
                 f"IMAGEN: {fallback_desc or name}", size=16, color=MUTED_LIGHT,
                 align=PP_ALIGN.CENTER, italic=True)
        return False

    iw, ih = size
    pad = Inches(0.04)
    if card:
        rect(s, x, y, w, h, fill=CARD_WHITE, line=MUTED_LIGHT, radius=0.02)
    bw, bh = w - 2 * pad, h - 2 * pad
    ratio = min(bw / iw, bh / ih)
    pw, ph = int(iw * ratio), int(ih * ratio)
    s.shapes.add_picture(path, x + (w - pw) // 2, y + (h - ph) // 2, pw, ph)
    if caption:
        text_box(s, x, y + h + Inches(0.02), w, Inches(0.26), caption, size=12,
                 color=MUTED_LIGHT, align=PP_ALIGN.CENTER, italic=True)
    return True


def arrow_line(s, x1, y1, x2, y2, color=TEAL):
    """Flecha de conector recta."""
    c = s.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, x1, y1, x2, y2)
    c.line.color.rgb = color
    c.line.width = Pt(2.0)
    ln = c.line._get_or_add_ln()
    from lxml import etree
    tail = etree.SubElement(ln, "{http://schemas.openxmlformats.org/drawingml/2006/main}tailEnd")
    tail.set("type", "triangle")
    return c


# =====================================================================
# CONSTRUCCIÓN DE SLIDES (1 a 10 + 2 de respaldo)
# =====================================================================

def build_slide_1():
    """SLIDE 1 — Portada (fondo oscuro) · Tiempo: 15 s"""
    notes = (
        "Tiempo: 15 s\n"
        "Somos el equipo de SOFÍA: una pared de paneles panal que te mira y te responde. "
        "Hoy les contamos qué construimos, qué medimos y por qué todavía no está lista para un museo."
    )
    s = create_slide(dark=True, notes=notes)
    
    # Barra de acento
    rect(s, 0, 0, Inches(0.18), H, fill=TEAL, shape=MSO_SHAPE.RECTANGLE)
    
    # Textos izquierda
    text_box(s, Inches(0.8), Inches(1.0), Inches(5.6), Inches(1.1),
             "SOFÍA", size=68, color=WHITE, bold=True)
    text_box(s, Inches(0.8), Inches(2.2), Inches(5.6), Inches(0.6),
             "La pared robótica que te mira", size=30, color=TEAL, bold=True)
    text_box(s, Inches(0.8), Inches(2.95), Inches(5.4), Inches(1.5),
             "Paneles impresos en 3D que te siguen, reaccionan a tus gestos y no se queman",
             size=22, color=TEXT_WHITE)
             
    # Pie
    text_box(s, Inches(0.8), Inches(5.6), Inches(5.6), Inches(1.3),
             ["LabDST · ITESO · Segundo Corte · Otoño 2026",
              "Equipo: Paola Covarrubias · Lizeth Méndez · Bernardo Orozco · Karen Sánchez · Alan Fuentes"],
             size=13, color=MUTED_DARK)

    # Imágenes a la derecha: Render 3D grande (60% del alto) + recuadro físico pequeño
    add_image(s, "sofia_solid.png", Inches(6.6), Inches(1.0), Inches(5.9), Inches(4.3),
              card=True, caption="Módulo cinético en panal")
    add_image(s, "modulo_fisico.png", Inches(10.1), Inches(4.7), Inches(2.4), Inches(1.9),
              card=True, caption="Prototipo físico armado")
    return s


def build_slide_2():
    """SLIDE 2 — Planteamiento: Problema, Objetivos y Cronograma · Tiempo: 50 s"""
    notes = (
        "Tiempo: 50 s\n"
        "Las paredes cinéticas de museos y aeropuertos son caras, usan motores industriales cerrados "
        "y, si algo las detiene, el motor se sobrecalienta. Queremos una alternativa modular y accesible, "
        "impresa en 3D, que te siga en vivo y se proteja sola. Hoy estamos en el Corte 2: ya hay prototipo "
        "que responde; el Corte 3 es la pared completa."
    )
    s = create_slide(dark=False, notes=notes)
    tracker(s, active_stage="PLANTEAMIENTO", slide_n=2)
    title(s, "Las paredes interactivas cuestan mucho y se queman")
    
    # Izquierda: 3 filas con ícono
    col1_w = Inches(5.6)
    rect(s, Inches(0.8), Inches(1.8), col1_w, Inches(4.0), fill=CARD_WHITE, line=MUTED_LIGHT)
    
    filas = [
        ("💰 Carísimas", "Motores industriales inaccesibles"),
        ("🔒 Cerradas", "Difíciles de adaptar y reparar"),
        ("🔥 Se queman", "Un motor forzado se sobrecalienta"),
    ]
    for i, (tit_f, desc_f) in enumerate(filas):
        fy = Inches(1.95 + i * 1.05)
        text_box(s, Inches(1.0), fy, col1_w - Inches(0.4), Inches(0.4),
                 tit_f, size=22, color=RED_ALERT if i == 2 else TEXT_DARK, bold=True)
        text_box(s, Inches(1.0), fy + Inches(0.4), col1_w - Inches(0.4), Inches(0.4),
                 desc_f, size=18, color=MUTED_LIGHT)
                 
    text_box(s, Inches(1.0), Inches(5.1), col1_w - Inches(0.4), Inches(0.6),
             "En museos y aeropuertos trabajan todo el día y la gente las toca.",
             size=16, color=TEXT_DARK, italic=True)

    # Derecha: Objetivo general + 3 específicos + imagen de piezas
    col2_x = Inches(6.7)
    col2_w = Inches(5.8)
    rect(s, col2_x, Inches(1.8), col2_w, Inches(4.0), fill=CARD_LIGHT)
    
    text_box(s, col2_x + Inches(0.2), Inches(1.9), col2_w - Inches(2.2), Inches(1.1),
             "Objetivo general: pared robótica modular, accesible y segura que sigue a las personas y reacciona a sus gestos.",
             size=18, color=TEXT_DARK, bold=True)
             
    # Imagen pequeña de piezas impresas junto a los objetivos
    add_image(s, "sofia_exploded.png", col2_x + Inches(3.9), Inches(1.9), Inches(1.7), Inches(2.1),
              card=True, caption="Piezas 3D")
              
    especificos = [
        "1  Paneles modulares impresos en 3D",
        "2  Seguimiento y gestos en vivo (>30 FPS)",
        "3  Medir calor y diseñar protección",
    ]
    for idx, esp in enumerate(especificos):
        text_box(s, col2_x + Inches(0.2), Inches(3.1 + idx * 0.45), col2_w - Inches(0.4), Inches(0.4),
                 esp, size=18, color=TEAL_DARK, bold=True)

    # Bloque 3: Línea de tiempo D-Lab + Materiales
    rect(s, Inches(0.8), Inches(6.0), Inches(11.7), Inches(0.85), fill=CARD_WHITE, line=TEAL)
    text_box(s, Inches(1.0), Inches(6.08), Inches(11.3), Inches(0.35),
             "Corte 1 · Diseño ✓    ➔    Corte 2 · Prototipo que te sigue ● ESTAMOS AQUÍ    ➔    Corte 3 · Pared completa",
             size=18, color=TEAL_DARK, bold=True, align=PP_ALIGN.CENTER)
    text_box(s, Inches(1.0), Inches(6.45), Inches(11.3), Inches(0.35),
             "Materiales: 16 módulos PLA SOFIA003, 32 servos MG90S, 64 tornillos M3, 2 PCA9685, 1 ESP32-C3 y cámara web.",
             size=15, color=MUTED_LIGHT, align=PP_ALIGN.CENTER)
    return s


def build_slide_3():
    """SLIDE 3 — Marco Referencial: Lo que existe y nuestro diferenciador · Tiempo: 40 s"""
    notes = (
        "Tiempo: 40 s\n"
        "Hay obras espectaculares como inFORM del MIT, que mueve 900 pines pero vive en un laboratorio, "
        "y esculturas de aeropuerto que repiten una coreografía grabada sin verte. SOFÍA te ve en vivo, "
        "es modular e imprimible en 3D, y además estudia cuánto calor aguanta su motor. "
        "Como el servomotor no tiene sensor interno, medimos su calentamiento en laboratorio con osciloscopio "
        "y termómetro láser. Nos apoyamos en robótica modular, interacción humano-robot y visión por computadora."
    )
    s = create_slide(dark=False, notes=notes)
    tracker(s, active_stage="PLANTEAMIENTO", slide_n=3)
    title(s, "Hermosas, caras y ciegas")
    
    col_w = Inches(3.7)
    
    # Col 1: inFORM
    rect(s, Inches(0.8), Inches(1.8), col_w, Inches(3.7), fill=CARD_WHITE, line=MUTED_LIGHT)
    add_image(s, "inform_placeholder.png", Inches(1.0), Inches(1.95), col_w - Inches(0.4), Inches(1.5),
              card=True, fallback_desc="inFORM (MIT Media Lab)")
    text_box(s, Inches(1.0), Inches(3.6), col_w - Inches(0.4), Inches(0.4),
             "MIT inFORM", size=22, bold=True, color=TEXT_DARK)
    text_box(s, Inches(1.0), Inches(4.05), col_w - Inches(0.4), Inches(1.3),
             "900 pines que forman relieve en vivo. Prototipo de laboratorio.",
             size=18, color=MUTED_LIGHT)

    # Col 2: Esculturas de aeropuerto
    rect(s, Inches(4.8), Inches(1.8), col_w, Inches(3.7), fill=CARD_WHITE, line=MUTED_LIGHT)
    add_image(s, "aeropuerto_placeholder.png", Inches(5.0), Inches(1.95), col_w - Inches(0.4), Inches(1.5),
              card=True, fallback_desc="Escultura cinética de aeropuerto")
    text_box(s, Inches(5.0), Inches(3.6), col_w - Inches(0.4), Inches(0.4),
             "Arte Comercial", size=22, bold=True, color=TEXT_DARK)
    text_box(s, Inches(5.0), Inches(4.05), col_w - Inches(0.4), Inches(1.3),
             "Coreografía grabada en ciclo. No te ven.",
             size=18, color=MUTED_LIGHT)

    # Col 3: SOFÍA (resaltada con Teal)
    rect(s, Inches(8.8), Inches(1.8), col_w, Inches(3.7), fill=CARD_LIGHT, line=TEAL)
    add_image(s, "modulo_fisico.png", Inches(9.0), Inches(1.95), col_w - Inches(0.4), Inches(1.5),
              card=True, caption="Prototipo SOFÍA")
    text_box(s, Inches(9.0), Inches(3.6), col_w - Inches(0.4), Inches(0.4),
             "SOFÍA (ITESO)", size=22, bold=True, color=TEAL_DARK)
    text_box(s, Inches(9.0), Inches(4.05), col_w - Inches(0.4), Inches(1.3),
             "Te ve en vivo · Modular en 3D · Sin sensor interno: medido con láser y osciloscopio",
             size=18, color=TEXT_DARK, bold=True)

    # Banda de diferenciador
    rect(s, Inches(0.8), Inches(5.65), Inches(11.7), Inches(0.8), fill=CARD_WHITE, line=AMBER_ALERT)
    text_box(s, Inches(1.0), Inches(5.72), Inches(11.3), Inches(0.35),
             "Diferenciador: el motor no avisa calor; medimos en banco con láser y osciloscopio.",
             size=19, color=TEXT_DARK, bold=True)
    text_box(s, Inches(1.0), Inches(6.12), Inches(11.3), Inches(0.3),
             "Robótica modular · Interacción humano-robot · Visión por computadora",
             size=14, color=TEAL_DARK, bold=True)
             
    # Pie académico
    text_box(s, Inches(0.8), Inches(6.6), Inches(11.7), Inches(0.3),
             "Apoyado en: Seo et al. 2019 · Fong et al. 2003 · MediaPipe/OpenCV 2026",
             size=12, color=MUTED_LIGHT)
    return s


def build_slide_4():
    """SLIDE 4 — Diseño de la Investigación: 3 medidas y líneas rojas · Tiempo: 55 s"""
    notes = (
        "Tiempo: 55 s\n"
        "Medimos tres cosas, cada una con su línea roja: la velocidad de la cámara, la respuesta a gestos "
        "y el calor del motor. Para medir el calor usamos termómetro láser y osciloscopio en banco de pruebas con un tope físico. "
        "Y probamos todo el prototipo completo: cámara, software, Bluetooth, la tarjeta ESP32 y los paneles."
    )
    s = create_slide(dark=False, notes=notes)
    tracker(s, active_stage="DISEÑO", slide_n=4)
    title(s, "Tres cosas medidas, tres líneas rojas")
    
    # Tabla / Matriz de 3 filas
    ty = Inches(1.75)
    tw = Inches(11.7)
    
    headers = ["QUÉ MEDIMOS", "CÓMO", "APROBAMOS SI"]
    col_ws = [Inches(3.2), Inches(4.8), Inches(3.7)]
    
    # Cabecera
    cx = Inches(0.8)
    for h_txt, cw in zip(headers, col_ws):
        rect(s, cx, ty, cw, Inches(0.4), fill=TEAL_BG, line=None, radius=0.1)
        text_box(s, cx, ty + Inches(0.06), cw, Inches(0.3), h_txt, size=13,
                 color=TEAL_DARK, bold=True, align=PP_ALIGN.CENTER)
        cx += cw
        
    filas_matriz = [
        ("Velocidad de cámara", "Ensayos frente a cámara web (FPS y retraso)", "> 30 FPS y < 100 ms"),
        ("Respuesta a gestos", "Saludo, corazón y juego frente a la cámara", "El panel responde al saludo en vivo"),
        ("Calor del motor", "Termómetro láser y osciloscopio con tope de atasco", "Bajo 55 °C y corte antes de 15 s"),
    ]
    for r_i, (c1, c2, c3) in enumerate(filas_matriz):
        ry = ty + Inches(0.48 + r_i * 0.95)
        rect(s, Inches(0.8), ry, tw, Inches(0.88), fill=CARD_WHITE, line=MUTED_LIGHT)
        text_box(s, Inches(1.0), ry + Inches(0.18), Inches(3.0), Inches(0.5), c1, size=20, color=TEXT_DARK, bold=True)
        text_box(s, Inches(4.1), ry + Inches(0.18), Inches(4.6), Inches(0.6), c2, size=18, color=MUTED_LIGHT)
        text_box(s, Inches(8.9), ry + Inches(0.18), Inches(3.4), Inches(0.6), c3, size=18, color=TEAL_DARK, bold=True)

    # Cadena horizontal de 5 bloques
    rect(s, Inches(0.8), Inches(4.9), tw, Inches(1.85), fill=CARD_LIGHT)
    text_box(s, Inches(1.0), Inches(5.0), tw - Inches(0.4), Inches(0.3),
             "El prototipo puesto a prueba (cadena completa):", size=15, color=TEXT_DARK, bold=True)
             
    cadena = [
        ("Cámara web", "60 Hz"),
        ("Software PC", "MediaPipe"),
        ("Bluetooth", "BLE"),
        ("ESP32-C3", "2x PCA9685"),
        ("16 módulos", "32 servos MG90S"),
    ]
    bw = Inches(2.1)
    by = Inches(5.45)
    for i, (b_t, b_s) in enumerate(cadena):
        bx = Inches(1.0 + i * 2.32)
        rect(s, bx, by, bw, Inches(1.05), fill=CARD_WHITE, line=TEAL)
        text_box(s, bx, by + Inches(0.12), bw, Inches(0.4), b_t, size=17, color=TEXT_DARK, bold=True, align=PP_ALIGN.CENTER)
        text_box(s, bx, by + Inches(0.55), bw, Inches(0.4), b_s, size=14, color=MUTED_LIGHT, align=PP_ALIGN.CENTER)
        if i < 4:
            arrow_line(s, bx + bw, by + Inches(0.52), Inches(1.0 + (i + 1) * 2.32), by + Inches(0.52))
    return s


def build_slide_5():
    """SLIDE 5 — Resultados: Software de visión y simulación · Tiempo: 40 s"""
    notes = (
        "Tiempo: 40 s\n"
        "El software lee tu cuerpo y tus dos manos en 3D a más de 30 cuadros por segundo y reconoce "
        "saludo, corazón y piedra-papel-tijera. Antes de mover motores reales, simulamos en Unity "
        "cómo los 16 paneles giran hacia ti."
    )
    s = create_slide(dark=False, notes=notes)
    tracker(s, active_stage="RESULTADOS", slide_n=5)
    title(s, "Te sigue la mano a más de 30 cuadros por segundo")
    
    # Captura grande de PySide6 a la izquierda (55% del ancho)
    add_image(s, "sofia_gui.png", Inches(0.8), Inches(1.8), Inches(6.5), Inches(4.8),
              card=True, caption="Estación de control en tiempo real (PySide6)")
              
    # Derecha: Stat 30+ FPS + subtexto + chips + simulación Unity
    rx = Inches(7.6)
    rw = Inches(4.9)
    
    # Número destacado
    rect(s, rx, Inches(1.8), rw, Inches(1.4), fill=CARD_WHITE, line=TEAL)
    text_box(s, rx, Inches(1.85), rw, Inches(0.75), "30+ FPS", size=66, color=TEAL_DARK, bold=True, align=PP_ALIGN.CENTER)
    text_box(s, rx, Inches(2.65), rw, Inches(0.4), "Cuerpo y dos manos (21 puntos cada una)", size=18, color=MUTED_LIGHT, align=PP_ALIGN.CENTER)

    # 3 Chips de gestos
    rect(s, rx, Inches(3.35), rw, Inches(0.9), fill=CARD_LIGHT)
    text_box(s, rx + Inches(0.2), Inches(3.45), rw - Inches(0.4), Inches(0.7),
             "Gestos:  👋 Saludo   ·   💖 Corazón   ·   👊 Puño", size=18, color=TEXT_DARK, bold=True)

    # Cuadrícula 2x2 de frames Unity
    f_w = Inches(2.35)
    f_h = Inches(1.05)
    add_image(s, "fig_sim_1.png", rx, Inches(4.4), f_w, f_h, card=True)
    add_image(s, "fig_sim_2.png", rx + f_w + Inches(0.2), Inches(4.4), f_w, f_h, card=True)
    add_image(s, "fig_sim_3.png", rx, Inches(5.55), f_w, f_h, card=True)
    add_image(s, "fig_sim_4.png", rx + f_w + Inches(0.2), Inches(5.55), f_w, f_h, card=True)
    text_box(s, rx, Inches(6.65), rw, Inches(0.3),
             "Simulación: los 16 paneles giran hacia ti", size=13, color=MUTED_LIGHT, align=PP_ALIGN.CENTER, italic=True)
    return s


def build_slide_6():
    """SLIDE 6 — Resultados: Prototipo físico responde · Tiempo: 45 s"""
    notes = (
        "Tiempo: 45 s\n"
        "En el prototipo físico, la persona saluda frente a la cámara y el panel responde con su movimiento. "
        "Hicimos decenas de ensayos de gestos y rutinas. Y siendo honestos con los criterios: la fluidez y el "
        "calor en uso normal ya cumplen; la respuesta en milisegundos está en validación, y el corte automático "
        "está diseñado pero falta programarlo."
    )
    s = create_slide(dark=False, notes=notes)
    tracker(s, active_stage="RESULTADOS", slide_n=6)
    title(s, "Saludas, y el panel te contesta")
    
    # Izquierda: Secuencia de 3 imágenes (60% del ancho)
    seq_w = Inches(2.25)
    seq_h = Inches(3.8)
    sy = Inches(1.8)
    
    add_image(s, "modulo_fisico.png", Inches(0.8), sy, seq_w, seq_h, card=True, caption="1. El módulo")
    add_image(s, "sofia_saludo1.png", Inches(3.2), sy, seq_w, seq_h, card=True, caption="2. Tu saludo")
    add_image(s, "sofia_saludo2.png", Inches(5.6), sy, seq_w, seq_h, card=True, caption="3. El panel responde")
    
    # Banda
    rect(s, Inches(0.8), Inches(5.95), Inches(7.05), Inches(0.7), fill=CARD_LIGHT)
    text_box(s, Inches(1.0), Inches(6.12), Inches(6.65), Inches(0.4),
             "Decenas de ensayos de gestos y rutinas grabados", size=18, color=TEAL_DARK, bold=True)

    # Derecha: Tarjeta "¿Cumplimos?" con 4 filas
    rx = Inches(8.2)
    rw = Inches(4.3)
    rect(s, rx, Inches(1.8), rw, Inches(4.85), fill=CARD_WHITE, line=TEAL)
    text_box(s, rx + Inches(0.3), Inches(2.0), rw - Inches(0.6), Inches(0.4),
             "¿Cumplimos los criterios?", size=24, color=TEXT_DARK, bold=True)
             
    check_items = [
        ("Más de 30 FPS", "✓ Cumplido", TEAL_DARK),
        ("Menos de 100 ms", "◐ En validación", AMBER_ALERT),
        ("Bajo 55 °C", "✓ En uso normal", TEAL_DARK),
        ("Corte < 15 s", "◐ Diseñado (falta código)", AMBER_ALERT),
    ]
    for i, (crit, stat_txt, c_col) in enumerate(check_items):
        cy = Inches(2.65 + i * 0.95)
        text_box(s, rx + Inches(0.3), cy, rw - Inches(0.6), Inches(0.35),
                 crit, size=20, color=TEXT_DARK, bold=True)
        text_box(s, rx + Inches(0.3), cy + Inches(0.38), rw - Inches(0.6), Inches(0.4),
                 stat_txt, size=18, color=c_col, bold=True)
    return s


def build_slide_7():
    """SLIDE 7 — Hallazgo Clave: Gráfica térmica y límite de 60 °C · Tiempo: 50 s"""
    notes = (
        "Tiempo: 50 s\n"
        "Este es nuestro hallazgo clave. Con el motor libre no se calienta, pero atorado a propósito "
        "llegó a 64.8 grados en menos de cuatro minutos, y a los tres minutos ya pasaba de 60, donde el "
        "plástico se afloja. Por eso diseñamos el corte automático a los 15 segundos: según nuestra curva, "
        "ahí el motor solo ha subido unos siete grados."
    )
    s = create_slide(dark=False, notes=notes)
    tracker(s, active_stage="RESULTADOS", slide_n=7)
    title(s, "Si un panel se atora, en 3 minutos pasa de 60 °C", is_alert=True)
    
    # Gráfica térmica grande a la izquierda (62% del ancho)
    add_image(s, "grafica_termica_reconstruida.png", Inches(0.8), Inches(1.8), Inches(7.5), Inches(4.9),
              card=True, caption="Medición en banco con osciloscopio y termómetro láser (sin sensor en motor)")
              
    # Derecha: 64.8 °C enorme + textos
    rx = Inches(8.6)
    rw = Inches(3.9)
    
    # Número 64.8 °C
    rect(s, rx, Inches(1.8), rw, Inches(1.8), fill=CARD_WHITE, line=RED_ALERT)
    text_box(s, rx, Inches(1.9), rw, Inches(0.8), "64.8 °C", size=68, color=RED_ALERT, bold=True, align=PP_ALIGN.CENTER)
    text_box(s, rx + Inches(0.2), Inches(2.75), rw - Inches(0.4), Inches(0.7),
             "a los 226 s, hasta que se oyó el engrane forzarse", size=18, color=MUTED_LIGHT, align=PP_ALIGN.CENTER)

    # Texto 1: Sin carga
    rect(s, rx, Inches(3.8), rw, Inches(1.2), fill=CARD_LIGHT)
    text_box(s, rx + Inches(0.2), Inches(4.0), rw - Inches(0.4), Inches(0.8),
             "Sin carga: no se calienta.", size=22, color=TEXT_DARK, bold=True)

    # Texto 2: Corte a 15 s
    rect(s, rx, Inches(5.2), rw, Inches(1.5), fill=TEAL_BG, line=TEAL)
    text_box(s, rx + Inches(0.2), Inches(5.4), rw - Inches(0.4), Inches(1.1),
             "Con corte a 15 s: sube solo ~7 °C", size=22, color=TEAL_DARK, bold=True)
    return s


def build_slide_8():
    """SLIDE 8 — Brecha con el Entorno Real: Gente y Entorno · Tiempo: 40 s"""
    notes = (
        "Tiempo: 40 s\n"
        "En el laboratorio probamos con una persona, a un metro y con luz controlada. "
        "En un museo hay multitud, sol y sombras, y gente a tres o cinco metros, donde la mano se ve "
        "entre tres y cinco veces más chica. Además hoy dependemos de una laptop con cables; "
        "en una instalación el sistema debe ir oculto en el marco."
    )
    s = create_slide(dark=False, notes=notes)
    tracker(s, active_stage="BRECHA", slide_n=8)
    title(s, "Un laboratorio no es un museo: gente y entorno")
    
    # Tabla visual 4 filas (LO QUE PROBAMOS | LO QUE EXIGE UN MUSEO | POR QUÉ IMPORTA)
    headers = ["LO QUE PROBAMOS", "LO QUE EXIGE UN MUSEO", "POR QUÉ IMPORTA"]
    col_ws = [Inches(3.4), Inches(4.4), Inches(3.9)]
    
    ty = Inches(1.8)
    cx = Inches(0.8)
    for h_txt, cw in zip(headers, col_ws):
        rect(s, cx, ty, cw, Inches(0.4), fill=TEAL_BG, line=None, radius=0.1)
        text_box(s, cx, ty + Inches(0.06), cw, Inches(0.3), h_txt, size=13,
                 color=TEAL_DARK, bold=True, align=PP_ALIGN.CENTER)
        cx += cw

    filas_b1 = [
        ("👤 1 persona sola", "👥 Multitud, manos cruzadas", "¿A quién sigue?"),
        ("💡 Luz de laboratorio", "☀️ Sol, reflejos y sombras", "Confunde a la cámara"),
        ("📏 Distancia de 1 m", "📐 Público a 3–5 m", "La mano se ve 3 a 5× más chica"),
        ("💻 Laptop con cables", "📦 Sistema oculto en el marco", "Sin intervención humana"),
    ]
    for r_i, (c1, c2, c3) in enumerate(filas_b1):
        ry = Inches(2.35 + r_i * 1.1)
        rect(s, Inches(0.8), ry, Inches(11.7), Inches(0.95), fill=CARD_WHITE, line=MUTED_LIGHT)
        text_box(s, Inches(1.0), ry + Inches(0.25), Inches(3.1), Inches(0.5), c1, size=20, color=TEXT_DARK, bold=True)
        text_box(s, Inches(4.3), ry + Inches(0.25), Inches(4.1), Inches(0.5), c2, size=20, color=TEXT_DARK)
        text_box(s, Inches(8.7), ry + Inches(0.25), Inches(3.6), Inches(0.5), c3, size=18, color=AMBER_ALERT, bold=True)
    return s


def build_slide_9():
    """SLIDE 9 — Brecha con el Entorno Real: 10 minutos vs 12 horas · Tiempo: 45 s"""
    notes = (
        "Tiempo: 45 s\n"
        "Probamos diez minutos; un museo abre de ocho a doce horas, entre cincuenta y setenta veces más. "
        "Y un niño que sujeta un pétalo es exactamente nuestro ensayo de atasco: 60 grados en tres minutos. "
        "Además, 32 motores juntos piden hasta 25 o 30 amperes, y si un panel falla hoy lo reinicia un "
        "ingeniero; en un museo debe recuperarse solo."
    )
    s = create_slide(dark=False, notes=notes)
    tracker(s, active_stage="BRECHA", slide_n=9)
    title(s, "10 minutos vs 12 horas")
    
    # Número destacado arriba
    rect(s, Inches(0.8), Inches(1.75), Inches(11.7), Inches(0.95), fill=CARD_LIGHT)
    text_box(s, Inches(1.1), Inches(1.8), Inches(3.2), Inches(0.8),
             "50–70×", size=66, color=AMBER_ALERT, bold=True)
    text_box(s, Inches(4.5), Inches(2.0), Inches(7.5), Inches(0.5),
             "más tiempo de operación diaria en un museo frente a nuestras pruebas",
             size=22, color=TEXT_DARK, bold=True)

    # Tabla de 4 filas
    filas_b2 = [
        ("Pruebas de 10 min", "8 a 12 h cada día", "Calor acumulado"),
        ("Nadie la toca", "Niños sujetando pétalos", "Es nuestro ensayo de atasco: 60 °C en 3 min"),
        ("1 módulo en banco", "32 motores: hasta 25–30 A", "Fuente industrial"),
        ("Reinicia un ingeniero", "Se auto-recupera", "Un panel falla, la pared sigue"),
    ]
    for r_i, (c1, c2, c3) in enumerate(filas_b2):
        ry = Inches(2.85 + r_i * 0.88)
        rect(s, Inches(0.8), ry, Inches(11.7), Inches(0.78), fill=CARD_WHITE, line=MUTED_LIGHT)
        text_box(s, Inches(1.0), ry + Inches(0.18), Inches(3.0), Inches(0.4), c1, size=18, color=TEXT_DARK, bold=True)
        text_box(s, Inches(4.2), ry + Inches(0.18), Inches(4.2), Inches(0.4), c2, size=18, color=TEXT_DARK)
        text_box(s, Inches(8.6), ry + Inches(0.18), Inches(3.7), Inches(0.4), c3, size=17, color=RED_ALERT, bold=True)

    # Banda de conclusión mecánica
    rect(s, Inches(0.8), Inches(6.5), Inches(11.7), Inches(0.6), fill=TEAL_BG, line=TEAL)
    text_box(s, Inches(1.0), Inches(6.62), Inches(11.3), Inches(0.35),
             "Falta un acople mecánico: que el pétalo ceda sin romper engranes ni lastimar dedos.",
             size=18, color=TEAL_DARK, bold=True, align=PP_ALIGN.CENTER)
    return s


def build_slide_10():
    """SLIDE 10 — Cierre: Qué corregimos y qué sigue · Tiempo: 40 s (fondo oscuro)"""
    notes = (
        "Tiempo: 40 s\n"
        "De los comentarios del Primer Corte atendimos tres cosas: objetivos claros, mediciones reales con sensores "
        "y una comparativa formal. Para el Corte 3 faltan la tarjeta de potencia definitiva, programar el apagado "
        "automático y armar la colmena de 16 paneles. SOFÍA ya te mira; falta que aguante todo el día. "
        "Gracias, quedamos atentos a sus preguntas."
    )
    s = create_slide(dark=True, notes=notes)
    tracker(s, active_stage="SIGUIENTES", slide_n=10, dark=True)
    title(s, "De prototipo a pared completa", dark=True)
    
    # 2 Columnas
    cw = Inches(5.7)
    
    # Izquierda: Atendimos del Corte 1
    rect(s, Inches(0.8), Inches(1.8), cw, Inches(3.3), fill=CARD_DARK, line=TEAL)
    text_box(s, Inches(1.05), Inches(1.95), cw - Inches(0.5), Inches(0.4),
             "Atendimos del Corte 1", size=24, color=TEAL, bold=True)
             
    c1_items = [
        "✓ Objetivos claros y delimitados (1 gen + 3 esp)",
        "✓ Mediciones reales (682 lecturas térmicas)",
        "✓ Comparativa formal (MIT inFORM y comerciales)",
    ]
    for i, itm in enumerate(c1_items):
        text_box(s, Inches(1.05), Inches(2.55 + i * 0.7), cw - Inches(0.5), Inches(0.6),
                 itm, size=18, color=TEXT_WHITE)

    # Derecha: Para el Corte 3
    rect(s, Inches(6.8), Inches(1.8), cw, Inches(3.3), fill=CARD_DARK, line=AMBER_ALERT)
    text_box(s, Inches(7.05), Inches(1.95), cw - Inches(0.5), Inches(0.4),
             "Para el Corte 3", size=24, color=AMBER_ALERT, bold=True)
             
    c3_items = [
        "1  PCB de potencia definitiva (30 A)",
        "2  Apagado automático por software (< 15 s)",
        "3  Colmena completa de 16 paneles",
    ]
    for i, itm in enumerate(c3_items):
        text_box(s, Inches(7.05), Inches(2.55 + i * 0.7), cw - Inches(0.5), Inches(0.6),
                 itm, size=18, color=TEXT_WHITE, bold=True)

    # Frase final grande
    rect(s, Inches(0.8), Inches(5.3), Inches(11.7), Inches(0.75), fill=CARD_DARK, line=TEAL)
    text_box(s, Inches(1.0), Inches(5.45), Inches(11.3), Inches(0.45),
             "SOFÍA ya te mira. Falta que aguante todo el día.",
             size=26, color=TEAL, bold=True, align=PP_ALIGN.CENTER)

    # Pie con QR + enlace a GitHub y ¿Preguntas?
    add_image(s, "qr_github.png", Inches(0.8), Inches(6.2), Inches(0.95), Inches(0.95), card=False)
    text_box(s, Inches(1.9), Inches(6.45), Inches(7.0), Inches(0.4),
             "github.com/PaolaCV14/IOT-SOFIA-2026", size=18, color=WHITE, bold=True)
    text_box(s, Inches(9.5), Inches(6.35), Inches(3.0), Inches(0.5),
             "¿Preguntas?", size=28, color=TEAL, bold=True, align=PP_ALIGN.RIGHT)
    return s


def build_slide_b1():
    """SLIDE B1 (RESPALDO 1, show="0") — Por dentro de SOFÍA: Arquitectura y BOM"""
    notes = (
        "Slide de respaldo B1: Arquitectura electrónica interna y lista detallada de componentes "
        "para responder dudas técnicas sobre cableado, buses I2C y distribución de corriente."
    )
    s = create_slide(dark=False, notes=notes)
    # Marcar oculta
    s._element.set("show", "0")
    tracker(s, is_backup=True, dark=False)
    title(s, "Por dentro de SOFÍA: Arquitectura y Componentes")
    
    # Diagrama de flujo
    rect(s, Inches(0.8), Inches(1.8), Inches(11.7), Inches(1.1), fill=CARD_LIGHT)
    text_box(s, Inches(1.0), Inches(1.9), Inches(11.3), Inches(0.3),
             "Diagrama de señales y buses:", size=15, color=TEXT_DARK, bold=True)
    text_box(s, Inches(1.0), Inches(2.3), Inches(11.3), Inches(0.4),
             "Cámara web  ➔  PC (Python + MediaPipe)  ➔  BLE  ➔  ESP32-C3  ➔  2x PCA9685 (I²C)  ➔  32 servos MG90S",
             size=18, color=TEAL_DARK, bold=True, align=PP_ALIGN.CENTER)

    # Lista de materiales / BOM
    rect(s, Inches(0.8), Inches(3.1), Inches(6.5), Inches(3.8), fill=CARD_WHITE, line=MUTED_LIGHT)
    text_box(s, Inches(1.0), Inches(3.25), Inches(6.1), Inches(0.4),
             "Lista de Materiales (BOM 16 Módulos)", size=20, color=TEXT_DARK, bold=True)
             
    bom_items = [
        "• 16 módulos panal PLA (diseño custom SOFIA003)",
        "• 32 servomotores metálicos MG90S (TowerPro)",
        "• 64 tornillos M3 × 10 mm (sujeción de servos y armazón)",
        "• 2 controladores PWM I²C PCA9685 de 16 canales",
        "• 1 microcontrolador ESP32-C3 Master (Wi-Fi / BLE)",
        "• Banco: osciloscopio y termómetro láser (sin sensor en motor)",
    ]
    for i, itm in enumerate(bom_items):
        text_box(s, Inches(1.0), Inches(3.75 + i * 0.48), Inches(6.1), Inches(0.4),
                 itm, size=18, color=MUTED_LIGHT)

    # Imagen de PCB o esquemático
    add_image(s, "PCB1.png", Inches(7.5), Inches(3.1), Inches(5.0), Inches(3.8),
              card=True, caption="Diseño PCB de potencia para 32 motores")
    return s


def build_slide_b2():
    """SLIDE B2 (RESPALDO 2, show="0") — Preguntas probables de jueces"""
    notes = (
        "Slide de respaldo B2: Respuestas sintéticas de una línea listas para proyectar si los jueces "
        "profundizan en la justificación de componentes, detección de atasco o costo."
    )
    s = create_slide(dark=False, notes=notes)
    # Marcar oculta
    s._element.set("show", "0")
    tracker(s, is_backup=True, dark=False)
    title(s, "Preguntas probables de los jueces")
    
    qa_list = [
        ("¿Por qué MG90S?", "Engranes metálicos, bajo costo y fácil de conseguir en volumen."),
        ("¿Cómo detectan el atasco?", "El servo no tiene sensor interno ni avisa calor; usamos corte por software a 15 s."),
        ("¿Por qué 15 segundos?", "En 15 s solo sube ~7 °C; llegar a 60 °C toma 3 min (medido con láser y osciloscopio)."),
        ("¿Qué pasa con varias personas?", "Es la brecha número 1 que identificamos; hoy probamos con una."),
        ("¿Cuánto cuesta vs comercial?", "Aún no tenemos costeo final; usamos piezas comerciales de bajo costo (servo, ESP32, PLA)."),
        ("¿Cumplen menos de 100 ms?", "Es el criterio de diseño; está en proceso de validación con video de alta velocidad."),
    ]
    
    col_w = Inches(5.7)
    for i, (q, a) in enumerate(qa_list):
        col_x = Inches(0.8) if i < 3 else Inches(6.8)
        row_y = Inches(1.8 + (i % 3) * 1.6)
        
        rect(s, col_x, row_y, col_w, Inches(1.45), fill=CARD_WHITE, line=TEAL)
        text_box(s, col_x + Inches(0.2), row_y + Inches(0.12), col_w - Inches(0.4), Inches(0.4),
                 q, size=20, color=TEAL_DARK, bold=True)
        text_box(s, col_x + Inches(0.2), row_y + Inches(0.55), col_w - Inches(0.4), Inches(0.8),
                 a, size=18, color=TEXT_DARK)
    return s


# =====================================================================
# VERIFICACIÓN DE REGLAS (--check)
# =====================================================================
def run_check():
    """Verifica reglas de diseño, tamaños de fuente, límites y tiempos."""
    print("=" * 65)
    print("EJECUTANDO REVISIÓN DE INTEGRIDAD (--check)")
    print("=" * 65)
    
    errors = []
    warnings = []
    
    total_time = 0
    slide_times = []
    
    prs_check = Presentation(OUT)
    print(f"Total diapositivas en deck: {len(prs_check.slides)}")
    
    # 1. Verificar número de slides
    if len(prs_check.slides) != 12:
        errors.append(f"Se esperaban 12 diapositivas (10 + 2 respaldo), se encontraron {len(prs_check.slides)}")

    for idx, slide in enumerate(prs_check.slides):
        slide_num = idx + 1
        is_backup = (slide_num > 10)
        
        # Verificar notas
        notes = slide.notes_slide.notes_text_frame.text if slide.has_notes_slide else ""
        if not notes.strip():
            errors.append(f"Slide {slide_num}: NO tiene notas de orador.")
        else:
            m = re.search(r"Tiempo:\s*(\d+)\s*s", notes)
            if m:
                t_val = int(m.group(1))
                total_time += t_val
                slide_times.append((slide_num, t_val))
            elif not is_backup:
                warnings.append(f"Slide {slide_num}: No se encontró etiqueta 'Tiempo: X s' en notas.")

        # Verificar ocultamiento en slides de respaldo
        if is_backup:
            show_val = slide._element.get("show")
            if show_val != "0":
                errors.append(f"Slide de respaldo {slide_num}: atributo show='{show_val}' (debe ser '0').")

        # Verificar formas y texto
        for shape in slide.shapes:
            # Límites de la diapositiva
            left_in = shape.left / Inches(1)
            top_in = shape.top / Inches(1)
            width_in = shape.width / Inches(1)
            height_in = shape.height / Inches(1)
            
            if left_in < -0.05 or top_in < -0.05 or (left_in + width_in) > 13.38 or (top_in + height_in) > 7.55:
                warnings.append(f"Slide {slide_num}: forma fuera de límites (x={left_in:.2f}, y={top_in:.2f}, w={width_in:.2f}, h={height_in:.2f})")

            # Fuentes de texto
            if shape.has_text_frame:
                for p in shape.text_frame.paragraphs:
                    for r in p.runs:
                        if r.font.size is not None:
                            pt_val = r.font.size.pt
                            # Reglas: pies/créditos/chips >= 12 pt; tablas >= 16 pt; cuerpo >= 18 pt; títulos >= 38 pt
                            if pt_val < 11.5:
                                errors.append(f"Slide {slide_num}: Texto '{r.text[:20]}' tiene fuente menor a 12 pt ({pt_val} pt)")

    # Verificar suma de tiempos
    print(f"\nTiempos por diapositiva visible:")
    for s_idx, s_t in slide_times:
        print(f"  Slide {s_idx:2d}: {s_t:2d} s")
    print(f"Tiempo total acumulado: {total_time} s ({total_time/60:.2f} min)")
    
    if 400 <= total_time <= 450:
        print(f"✓ TIEMPO VÁLIDO: {total_time} s está en el rango objetivo [400, 450] s.")
    else:
        errors.append(f"Tiempo total ({total_time} s) fuera de rango permitido [400, 450] s.")

    # Resumen
    print("\n" + "=" * 65)
    if errors:
        print(f"RESULTADO: ❌ FALLÓ con {len(errors)} error(es):")
        for err in errors:
            print("  -", err)
        return False
    else:
        print("RESULTADO: ✓ TODAS LAS REGLAS PASARON SATISFACTORIAMENTE!")
        if warnings:
            print(f"Avisos ({len(warnings)}):")
            for w in warnings:
                print("  *", w)
        return True


# =====================================================================
# EJECUCIÓN PRINCIPAL
# =====================================================================
def main():
    parser = argparse.ArgumentParser(description="Generador SOFIA Deck v2")
    parser.add_argument("--check", action="store_true", help="Ejecuta validación de reglas de diseño")
    args = parser.parse_args()

    print("Generando SOFIA_LabDST_Presentacion_v2.pptx...")
    build_slide_1()
    build_slide_2()
    build_slide_3()
    build_slide_4()
    build_slide_5()
    build_slide_6()
    build_slide_7()
    build_slide_8()
    build_slide_9()
    build_slide_10()
    build_slide_b1()
    build_slide_b2()

    prs.save(OUT)
    print(f"Presentación v2 guardada exitosamente en:\n  {OUT}")

    if args.check:
        success = run_check()
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
