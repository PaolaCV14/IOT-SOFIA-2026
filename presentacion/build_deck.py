"""Genera SOFIA_LabDST_Presentacion.pptx (16:9) con python-pptx.
Uso:  python3 build_deck.py
"""
import os
import tempfile
from PIL import Image
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE, MSO_CONNECTOR
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR

HERE = os.path.dirname(os.path.abspath(__file__))
FIG = os.path.join(HERE, "..", "paper", "Equipo 1 - segundo corte", "figures")
OUT = os.path.join(HERE, "SOFIA_LabDST_Presentacion.pptx")
TMP = tempfile.mkdtemp()

# ---------- paleta ----------
BG = RGBColor(0x0B, 0x12, 0x20)
CARD = RGBColor(0x14, 0x1E, 0x33)
CARD2 = RGBColor(0x1B, 0x28, 0x44)
TEAL = RGBColor(0x2D, 0xD4, 0xBF)
ORANGE = RGBColor(0xF5, 0x9E, 0x0B)
RED = RGBColor(0xF8, 0x71, 0x71)
WHITE = RGBColor(0xF1, 0xF5, 0xF9)
MUTED = RGBColor(0x94, 0xA3, 0xB8)
FONT = "Calibri"

prs = Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)
W, H = prs.slide_width, prs.slide_height
BLANK = prs.slide_layouts[6]


# ---------- helpers ----------
def new_slide(notes=""):
    s = prs.slides.add_slide(BLANK)
    s.background.fill.solid()
    s.background.fill.fore_color.rgb = BG
    if notes:
        s.notes_slide.notes_text_frame.text = notes
    return s


def rect(s, x, y, w, h, fill=CARD, line=None, shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.06):
    r = s.shapes.add_shape(shape, x, y, w, h)
    r.fill.solid()
    r.fill.fore_color.rgb = fill
    if line is None:
        r.line.fill.background()
    else:
        r.line.color.rgb = line
        r.line.width = Pt(1.25)
    r.shadow.inherit = False
    if shape == MSO_SHAPE.ROUNDED_RECTANGLE:
        r.adjustments[0] = radius
    return r


def text(s, x, y, w, h, content, size=18, color=WHITE, bold=False, align=PP_ALIGN.LEFT,
         anchor=MSO_ANCHOR.TOP, italic=False):
    tb = s.shapes.add_textbox(x, y, w, h)
    tf = tb.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    tf.margin_left = tf.margin_right = Inches(0.05)
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


def bullets(s, x, y, w, h, items, size=18, color=WHITE, gap=8, dot=TEAL):
    tb = s.shapes.add_textbox(x, y, w, h)
    tf = tb.text_frame
    tf.word_wrap = True
    for i, it in enumerate(items):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.space_after = Pt(gap)
        r0 = p.add_run()
        r0.text = "▸ "
        r0.font.size = Pt(size)
        r0.font.color.rgb = dot
        r0.font.name = FONT
        if isinstance(it, tuple):  # (negrita, resto)
            rb = p.add_run()
            rb.text = it[0]
            rb.font.bold = True
            rb.font.size = Pt(size)
            rb.font.color.rgb = color
            rb.font.name = FONT
            rr = p.add_run()
            rr.text = it[1]
            rr.font.size = Pt(size)
            rr.font.color.rgb = MUTED
            rr.font.name = FONT
        else:
            rr = p.add_run()
            rr.text = it
            rr.font.size = Pt(size)
            rr.font.color.rgb = color
            rr.font.name = FONT
    return tb


def header(s, title, kicker=None, n=None):
    rect(s, 0, 0, Inches(0.18), H, fill=TEAL, shape=MSO_SHAPE.RECTANGLE)
    if kicker:
        text(s, Inches(0.6), Inches(0.35), Inches(9), Inches(0.35), kicker.upper(), size=13,
             color=TEAL, bold=True)
    text(s, Inches(0.6), Inches(0.65), Inches(12), Inches(0.9), title, size=34, bold=True)
    text(s, Inches(0.6), Inches(7.05), Inches(8), Inches(0.3),
         "SOFIA · LabDST · ITESO · Otoño 2026", size=11, color=MUTED)
    if n:
        text(s, Inches(12.2), Inches(7.05), Inches(0.9), Inches(0.3), str(n), size=11,
             color=MUTED, align=PP_ALIGN.RIGHT)


def prep(name, maxw=2200):
    """Reduce imágenes enormes para que el PPTX no pese de más."""
    src = os.path.join(FIG, name)
    im = Image.open(src)
    if im.width > maxw:
        im = im.resize((maxw, int(im.height * maxw / im.width)), Image.LANCZOS)
    dst = os.path.join(TMP, name.replace(" ", "_"))
    im.convert("RGB").save(dst, quality=90)
    return dst, im.size


def pic(s, name, x, y, w, h, card=True, caption=None, white_bg=True):
    """Coloca imagen centrada dentro de un recuadro (x,y,w,h) conservando proporción."""
    path, (iw, ih) = prep(name)
    pad = Inches(0.1)
    if card:
        rect(s, x, y, w, h, fill=RGBColor(255, 255, 255) if white_bg else CARD, radius=0.03)
    bw, bh = w - 2 * pad, h - 2 * pad
    ratio = min(bw / iw, bh / ih)
    pw, ph = int(iw * ratio), int(ih * ratio)
    s.shapes.add_picture(path, x + (w - pw) // 2, y + (h - ph) // 2, pw, ph)
    if caption:
        text(s, x, y + h + Inches(0.03), w, Inches(0.3), caption, size=11, color=MUTED,
             align=PP_ALIGN.CENTER, italic=True)


def stat(s, x, y, w, h, big, small, color=TEAL):
    rect(s, x, y, w, h, fill=CARD, line=color)
    text(s, x, y + Inches(0.1), w, h * 0.55, big, size=32, bold=True, color=color,
         align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
    text(s, x + Inches(0.1), y + h * 0.58, w - Inches(0.2), h * 0.4, small, size=12.5,
         color=MUTED, align=PP_ALIGN.CENTER)


def arrow(s, x1, y1, x2, y2, color=TEAL):
    c = s.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, x1, y1, x2, y2)
    c.line.color.rgb = color
    c.line.width = Pt(2.25)
    ln = c.line._get_or_add_ln()
    from lxml import etree
    tail = etree.SubElement(ln, "{http://schemas.openxmlformats.org/drawingml/2006/main}tailEnd")
    tail.set("type", "triangle")
    return c


# =====================================================================
# 1. PORTADA
# =====================================================================
s = new_slide(
    "Presentación (10 s): Somos el Equipo 1 de LabDST. Hoy presentamos SOFIA, una superficie "
    "cinética modular que responde a gestos humanos, y lo que descubrimos sobre sus servomotores.")
rect(s, 0, 0, W, H, fill=BG, shape=MSO_SHAPE.RECTANGLE)
rect(s, Inches(8.4), 0, Inches(4.93), H, fill=CARD, shape=MSO_SHAPE.RECTANGLE)
rect(s, 0, 0, Inches(0.18), H, fill=TEAL, shape=MSO_SHAPE.RECTANGLE)
pic(s, "sofia_solid.png", Inches(8.9), Inches(0.7), Inches(3.9), Inches(3.6), card=True)
pic(s, "modulo_fisico.png", Inches(8.9), Inches(4.5), Inches(3.9), Inches(2.1), card=True)
text(s, Inches(0.7), Inches(0.7), Inches(7), Inches(0.4), "LABDST · ITESO · AVANCES SEGUNDO CORTE",
     size=14, color=TEAL, bold=True)
text(s, Inches(0.7), Inches(1.3), Inches(7.5), Inches(1.3), "SOFIA", size=80, bold=True)
text(s, Inches(0.7), Inches(2.75), Inches(7.4), Inches(1.4),
     "Superficie robótica cinética modular para interacción humano-robot y "
     "caracterización térmica de actuadores", size=22, color=WHITE)
rect(s, Inches(0.75), Inches(4.3), Inches(1.2), Inches(0.06), fill=ORANGE, shape=MSO_SHAPE.RECTANGLE)
text(s, Inches(0.7), Inches(4.5), Inches(7.5), Inches(0.4), "EQUIPO 1", size=14, color=ORANGE, bold=True)
text(s, Inches(0.7), Inches(4.85), Inches(7.5), Inches(1.6),
     ["Paola M. Covarrubias-Viveros · Lizeth A. Méndez-Ortiz",
      "Juan Bernardo Orozco-Quirarte · Karen I. Sánchez-García",
      "Alan E. Fuentes-Gutiérrez"], size=17, color=WHITE)
text(s, Inches(0.7), Inches(6.3), Inches(7.5), Inches(0.7),
     ["Con: Jorge A. Lizarraga · Graciela Baca · Luis E. González-Jiménez · Luis F. Luque-Vega",
      "Depto. de Procesos Tecnológicos e Industriales, ITESO · Otoño 2026"],
     size=11.5, color=MUTED)

# =====================================================================
# 2. EL PROBLEMA
# =====================================================================
s = new_slide(
    "(45 s) SOFIA son 16 módulos con 2 grados de libertad: 32 servos MG90S. El servo comercial trae "
    "su control interno encapsulado, no lo vemos. Si un módulo se atora, el error de posición "
    "persiste, el motor jala corriente máxima y se calienta. En un arreglo denso eso es riesgo real.")
header(s, "Una superficie que responde… hasta que se calienta", "Contexto y problema", 2)
stat(s, Inches(0.6), Inches(1.75), Inches(2.9), Inches(1.5), "16", "módulos en panal hexagonal")
stat(s, Inches(3.7), Inches(1.75), Inches(2.9), Inches(1.5), "2 GDL", "por módulo (cabeceo + giro)", ORANGE)
stat(s, Inches(6.8), Inches(1.75), Inches(2.9), Inches(1.5), "32", "servomotores MG90S")
bullets(s, Inches(0.6), Inches(3.6), Inches(9.2), Inches(3.3), [
    ("Control encapsulado: ", "el lazo interno del servo comercial es inaccesible; solo vemos el PWM de 50 Hz."),
    ("Error persistente: ", "tolerancias, choques entre módulos u obstáculos impiden llegar a la consigna."),
    ("Consecuencia: ", "corriente de bloqueo, calentamiento y degradación (el PLA se ablanda ≈ 60 °C)."),
    ("Pregunta clave: ", "¿el servo se comporta como bang-bang o como control proporcional saturado?"),
], size=18, gap=10)
rect(s, Inches(10.1), Inches(1.75), Inches(2.7), Inches(5.0), fill=CARD2)
pic(s, "sofia_exploded.png", Inches(10.2), Inches(1.85), Inches(2.5), Inches(4.8), card=False)

# =====================================================================
# 3. PREGUNTA Y OBJETIVOS
# =====================================================================
s = new_slide(
    "(45 s) Nuestra pregunta rectora: ¿el error de posición persistente en un MG90S produce una firma "
    "térmica identificable que limite el tiempo seguro de sostén? Para responderla tenemos 4 objetivos medibles.")
header(s, "Pregunta de investigación y objetivos", "Qué queremos demostrar", 3)
rect(s, Inches(0.6), Inches(1.7), Inches(12.1), Inches(1.45), fill=CARD, line=TEAL)
text(s, Inches(0.9), Inches(1.78), Inches(11.5), Inches(1.3),
     "¿Un error de posición persistente en un servo MG90S produce una firma térmica "
     "identificable que acote el tiempo seguro de sostén de un módulo SOFIA?",
     size=23, bold=True, anchor=MSO_ANCHOR.MIDDLE, color=WHITE)
objs = [
    ("1", "Evaluar el actuador", "Rango angular 19.3°–70.2° y tiempos de asentamiento 75–180 ms (PWM 50 Hz)"),
    ("2", "Modelar la térmica", "Pendiente de calentamiento bajo bloqueo y límite seguro > 65 °C"),
    ("3", "Validar la percepción", "Pose 3D + 21 puntos de mano con MediaPipe a ≥ 30 FPS"),
    ("4", "Simular la cinemática", "Cinemática 2-GDL y seguimiento coordinado de los 16 módulos"),
]
for i, (n, t, d) in enumerate(objs):
    x = Inches(0.6 + (i % 2) * 6.15)
    y = Inches(3.45 + (i // 2) * 1.75)
    rect(s, x, y, Inches(5.95), Inches(1.55), fill=CARD2)
    rect(s, x, y, Inches(0.9), Inches(1.55), fill=TEAL if i % 2 == 0 else ORANGE, radius=0.1)
    text(s, x, y, Inches(0.9), Inches(1.55), n, size=40, bold=True, color=BG,
         align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
    text(s, x + Inches(1.05), y + Inches(0.12), Inches(4.8), Inches(0.45), t, size=19, bold=True)
    text(s, x + Inches(1.05), y + Inches(0.6), Inches(4.8), Inches(0.9), d, size=14.5, color=MUTED)

# =====================================================================
# 4. DIFERENCIADOR / ESTADO DEL ARTE
# =====================================================================
s = new_slide(
    "(40 s) inFORM y Transform tienen cientos de actuadores lineales pero asumen que el actuador siempre "
    "llega a su posición. SOFIA es más pequeño pero se enfoca en lo que ellos ignoran: qué pasa cuando el "
    "actuador se atora y cuánta temperatura genera.")
header(s, "Qué nos diferencia", "Estado del arte", 4)
rows = [
    ("Plataforma", "Unidades (GDL)", "Rango / GDL", "Actuador", "Latencia / tasa"),
    ("inFORM (MIT)", "900 (1-GDL)", "100 mm lineal", "Pin motorizado DC", "≈ 60 Hz"),
    ("Transform (MIT)", "1,152 (1-GDL)", "100 mm lineal", "Gearmotor DC", "≈ 30 Hz"),
    ("Celdas modulares", "Variable", "Rotacional", "Brushless / DC", "Bus distribuido"),
    ("SOFIA (nuestro)", "16 (2-GDL)", "19.3°–70.2°", "Metal MG90S", "≤ 33 ms (30 fps)"),
]
tx, ty = Inches(0.6), Inches(1.75)
colw = [Inches(2.5), Inches(2.2), Inches(2.2), Inches(2.6), Inches(2.6)]
rh = Inches(0.62)
for r_i, row in enumerate(rows):
    cx = tx
    for c_i, cell in enumerate(row):
        last = r_i == len(rows) - 1
        fill = TEAL if r_i == 0 else (CARD2 if last else CARD)
        rect(s, cx, ty + rh * r_i, colw[c_i] - Inches(0.05), rh - Inches(0.05), fill=fill,
             shape=MSO_SHAPE.RECTANGLE, line=ORANGE if last else None)
        text(s, cx, ty + rh * r_i, colw[c_i] - Inches(0.05), rh - Inches(0.05), cell,
             size=15, bold=(r_i == 0 or last), color=BG if r_i == 0 else WHITE,
             align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
        cx += colw[c_i]
rect(s, Inches(0.6), Inches(5.1), Inches(12.1), Inches(1.7), fill=CARD, line=ORANGE)
text(s, Inches(0.9), Inches(5.2), Inches(11.5), Inches(1.5), [
    "Brecha: las superficies cinéticas publicadas asumen que el actuador completa su trayectoria.",
    "SOFIA une visión de la mano (MediaPipe) con servos MG90S y mide experimentalmente "
    "qué pasa en bloqueo: corriente, temperatura y si la respuesta es bang-bang."],
     size=18, anchor=MSO_ANCHOR.MIDDLE)

# =====================================================================
# 5. ARQUITECTURA
# =====================================================================
s = new_slide(
    "(60 s) Una cámara alimenta un pipeline en Python con MediaPipe. El software decide ángulos q1 y q2 "
    "y los manda por BLE a un ESP32-C3. El ESP32 comanda dos PCA9685 por I2C que generan los 32 PWM. "
    "Los servos van a un riel de 5 V con un INA219 midiendo corriente.")
header(s, "Arquitectura del sistema", "Diseño e implementación", 5)
bw, bh = Inches(2.15), Inches(1.2)
y1 = Inches(2.3)
blocks = [
    ("Cámara RGB", "30 FPS", TEAL),
    ("Python 3.11", "MediaPipe + OpenCV\nGUI PySide6", TEAL),
    ("BLE / UDP", "ángulos (q1,q2)\n60°–120°", ORANGE),
    ("ESP32-C3", "maestro · telemetría\nrutinas en firmware", TEAL),
    ("2× PCA9685", "I²C · 32 canales\nPWM 50 Hz", TEAL),
]
xs = [Inches(0.5 + i * 2.55) for i in range(5)]
for (t, d, c), x in zip(blocks, xs):
    rect(s, x, y1, bw, bh, fill=CARD2, line=c)
    text(s, x, y1 + Inches(0.08), bw, Inches(0.4), t, size=17, bold=True, color=c, align=PP_ALIGN.CENTER)
    text(s, x, y1 + Inches(0.5), bw, Inches(0.7), d.split("\n"), size=12, color=MUTED, align=PP_ALIGN.CENTER)
for i in range(4):
    arrow(s, xs[i] + bw, y1 + bh // 2, xs[i + 1], y1 + bh // 2)
# fila de abajo
y2 = Inches(4.6)
rect(s, xs[4], y2, bw, bh, fill=CARD2, line=ORANGE)
text(s, xs[4], y2 + Inches(0.08), bw, Inches(0.4), "32× MG90S", size=17, bold=True, color=ORANGE, align=PP_ALIGN.CENTER)
text(s, xs[4], y2 + Inches(0.5), bw, Inches(0.7), ["16 módulos × 2 GDL"], size=12, color=MUTED, align=PP_ALIGN.CENTER)
arrow(s, xs[4] + bw // 2, y1 + bh, xs[4] + bw // 2, y2, ORANGE)
rect(s, xs[3], y2, bw, bh, fill=CARD2, line=RED)
text(s, xs[3], y2 + Inches(0.08), bw, Inches(0.4), "Fuente 5 V / 20 A", size=16, bold=True, color=RED, align=PP_ALIGN.CENTER)
text(s, xs[3], y2 + Inches(0.5), bw, Inches(0.7), ["riel de actuadores"], size=12, color=MUTED, align=PP_ALIGN.CENTER)
arrow(s, xs[3] + bw, y2 + bh // 2, xs[4], y2 + bh // 2, RED)
rect(s, xs[2], y2, bw, bh, fill=CARD2, line=TEAL)
text(s, xs[2], y2 + Inches(0.08), bw, Inches(0.4), "INA219", size=17, bold=True, color=TEAL, align=PP_ALIGN.CENTER)
text(s, xs[2], y2 + Inches(0.5), bw, Inches(0.7), ["corriente (shunt high-side)"], size=12, color=MUTED, align=PP_ALIGN.CENTER)
arrow(s, xs[2] + bw, y2 + bh // 2, xs[3], y2 + bh // 2, TEAL)
text(s, Inches(0.5), Inches(4.6), Inches(4.7), Inches(1.3), [
    "Gestos estáticos → ángulos directos",
    "Gestos dinámicos → rutinas en el ESP32",
    "Futuro: RS-485 / Modbus entre módulos"], size=14, color=WHITE)
bullets(s, Inches(0.5), Inches(6.05), Inches(12), Inches(0.9), [
    ("Etapa actual (Discover → Learn): ", "validado con placas COTS en protoboard; PCB ya enviada a fabricación.")],
    size=14.5)

# =====================================================================
# 6. HARDWARE: CAD + PCB
# =====================================================================
s = new_slide(
    "(30 s) Aquí el diseño mecánico: base, mecanismo central y tapa hexagonal; todo impreso en PLA. "
    "A la derecha, esquemático y layout de la PCB que integra potencia, comunicación y los 32 servos; "
    "ya está enviada a fabricación, falta validarla físicamente.")
header(s, "Diseño mecánico y electrónico", "Hardware", 6)
pic(s, "sofia_solid.png", Inches(0.6), Inches(1.75), Inches(3.0), Inches(3.0), caption="Ensamble 3D")
pic(s, "sofia_exploded.png", Inches(3.8), Inches(1.75), Inches(2.4), Inches(3.0), caption="Vista explotada")
pic(s, "sofia_schematic.png", Inches(6.6), Inches(1.75), Inches(3.05), Inches(2.0), caption="Esquemático PCB")
pic(s, "sofia_pcb_layout.png", Inches(9.8), Inches(1.75), Inches(2.9), Inches(2.0), caption="Layout PCB")
bullets(s, Inches(6.6), Inches(4.25), Inches(6.1), Inches(2.6), [
    "Base estructural + soporte central + tapa hexagonal (PLA)",
    "PCB: potencia, comunicación, PWM e interfaz para 32 servos",
    "Estado: enviada a fabricación · validación pendiente",
], size=16, gap=9)
bullets(s, Inches(0.6), Inches(5.3), Inches(5.8), Inches(1.6), [
    ("Mecanismo pan-tilt 2-GDL ", "con dos MG90S ortogonales por módulo."),
], size=16)

# =====================================================================
# 7. VISIÓN Y GESTOS
# =====================================================================
s = new_slide(
    "(50 s) MediaPipe extrae 33 puntos del cuerpo y 21 por mano. Normalizamos por el tamaño de la palma para "
    "no depender de la distancia. Un detector decide entre gestos estáticos, como corazón o piedra-papel-tijera, "
    "y dinámicos, como el saludo, que se detecta por inversiones laterales de la palma. La GUI muestra FPS y latencia.")
header(s, "Visión por computadora y gestos", "Percepción", 7)
pic(s, "sofia_gui.png", Inches(0.6), Inches(1.75), Inches(6.6), Inches(4.3),
    caption="Interfaz de SOFIA (PySide6): video, gesto, FPS, latencia, sliders y telemetría")
bullets(s, Inches(7.5), Inches(1.75), Inches(5.3), Inches(5.2), [
    ("MediaPipe + OpenCV: ", "33 puntos de pose y 2×21 de mano en 3D, ≥ 30 FPS en CPU."),
    ("Normalización: ", "distancias por escala de palma → robusto a la distancia."),
    ("Saludo (wave): ", "≥ 3 inversiones laterales con amplitud > 0.05."),
    ("Piedra-papel-tijera: ", "máquina de estados con histéresis de contacto."),
    ("Estáticos: ", "corazón, palma abierta, victoria, puño."),
    ("Seguridad: ", "tracking suspendido durante rutinas del ESP32."),
], size=16, gap=9)

# =====================================================================
# 8. CINEMÁTICA Y SIMULACIÓN
# =====================================================================
s = new_slide(
    "(45 s) Cada módulo es una cadena de dos rotaciones: R = Rx(q1)·Ry(q2). Despejamos la cinemática inversa en "
    "forma cerrada, q2 = arcsin(ux) y q1 = atan2(-uy, uz), con saturación a los límites del servo. "
    "En Unity simulamos los 16 módulos apuntando hacia un objetivo móvil.")
header(s, "Cinemática 2-GDL y simulación de 16 módulos", "Modelo", 8)
rect(s, Inches(0.6), Inches(1.75), Inches(5.0), Inches(2.05), fill=CARD, line=TEAL)
text(s, Inches(0.75), Inches(1.8), Inches(4.7), Inches(0.4), "Cinemática directa", size=15, bold=True, color=TEAL)
text(s, Inches(0.75), Inches(2.2), Inches(4.7), Inches(0.6), "R₁,₃(q₁,q₂) = Rₓ(q₁) · R_y(q₂)", size=22, bold=True)
text(s, Inches(0.75), Inches(2.9), Inches(4.7), Inches(0.8),
     "Normal de la faceta: r̂ = R₁,₃ [0 0 1]ᵀ", size=15, color=MUTED)
rect(s, Inches(0.6), Inches(4.0), Inches(5.0), Inches(2.0), fill=CARD, line=ORANGE)
text(s, Inches(0.75), Inches(4.05), Inches(4.7), Inches(0.4), "Cinemática inversa (forma cerrada)", size=15, bold=True, color=ORANGE)
text(s, Inches(0.75), Inches(4.45), Inches(4.7), Inches(1.4),
     ["q₂ = arcsin(uₓ)", "q₁ = atan2(−u_y, u_z)", "+ saturación a los límites del servo"], size=17, bold=True)
text(s, Inches(0.6), Inches(6.2), Inches(5.0), Inches(0.7),
     "Simulación en Unity: 16 módulos orientándose hacia un objetivo p(t) en 3D.", size=13.5, color=MUTED)
for i, nm in enumerate(["fig_sim_1.png", "fig_sim_3.png", "fig_sim_5.png", "fig_sim_2.png", "fig_sim_4.png", "fig_sim_6.png"]):
    x = Inches(5.95 + (i % 2) * 3.45)
    y = Inches(1.75 + (i // 2) * 1.75)
    pic(s, nm, x, y, Inches(3.35), Inches(1.65), card=True)

# =====================================================================
# 9. TÉRMICA
# =====================================================================
s = new_slide(
    "(60 s) Bloqueamos mecánicamente el servo y medimos temperatura con un LM35. Resultado: calentamiento "
    "casi lineal de 0.214 grados por segundo, con R cuadrada de 0.993. La corriente de bloqueo es de unos 918 mA, "
    "y la carcasa llegó a 70.2 grados. Al ritmo medido, en unos 205 s se cruza el umbral de 65 grados, "
    "donde el plástico empieza a ablandarse. Por eso proponemos un watchdog de 15 s.")
header(s, "Resultado clave: el bloqueo calienta rápido", "Caracterización térmica del MG90S", 9)
pic(s, "fig_characterization_6panels.png", Inches(0.6), Inches(1.7), Inches(8.2), Inches(4.55),
    caption="Caracterización electromecánica y térmica del MG90S bajo bloqueo")
stat(s, Inches(9.1), Inches(1.7), Inches(3.6), Inches(1.15), "0.214 °C/s", "pendiente de calentamiento (R² = 0.993)", ORANGE)
stat(s, Inches(9.1), Inches(3.0), Inches(3.6), Inches(1.15), "918 mA", "corriente de bloqueo (≈ 4.4 W)", RED)
stat(s, Inches(9.1), Inches(4.3), Inches(3.6), Inches(1.15), "70.21 °C", "temperatura máx. de carcasa")
stat(s, Inches(9.1), Inches(5.6), Inches(3.6), Inches(1.15), "≈ 205 s", "para superar 65 °C desde ambiente", ORANGE)
text(s, Inches(0.6), Inches(6.45), Inches(8.2), Inches(0.5),
     "τ no es identificable con este registro → reportamos la pendiente (honestidad metodológica).",
     size=13.5, color=MUTED, italic=True)

# =====================================================================
# 10. ¿BANG-BANG?
# =====================================================================
s = new_slide(
    "(50 s) La curva térmica sola no distingue bang-bang de proporcional saturado, porque ambos meten voltaje "
    "máximo al bloqueo. Por eso medimos corriente en tres condiciones: error de 5 grados, 90 grados y bloqueo. "
    "Con 5 grados hay un pico breve y vuelve a reposo en 3 mA; con 90 grados dura más; en bloqueo satura. "
    "Conclusión: es proporcional con zona muerta, que satura solo cuando algo lo traba.")
header(s, "¿Es bang-bang? Lo medimos", "Corriente en 3 condiciones", 10)
pic(s, "fig_current_characterization.png", Inches(0.6), Inches(1.7), Inches(12.1), Inches(3.4),
    caption="Corriente del MG90S: (a) error 5°, (b) error 90°, (c) bloqueo sostenido")
conds = [
    ("Error 5°", "pico ≈ 583 mA < 50 ms\nreposo ≈ 3.1 mA", TEAL),
    ("Error 90°", "transitorio 150–180 ms\nreposo ≈ 3.5 mA", TEAL),
    ("Bloqueo", "saturación continua\n≈ 918 mA (picos 1.8 A)", RED),
]
for i, (t, d, c) in enumerate(conds):
    x = Inches(0.6 + i * 2.5)
    rect(s, x, Inches(5.45), Inches(2.35), Inches(1.45), fill=CARD, line=c)
    text(s, x, Inches(5.5), Inches(2.35), Inches(0.4), t, size=16, bold=True, color=c, align=PP_ALIGN.CENTER)
    text(s, x, Inches(5.95), Inches(2.35), Inches(0.9), d.split("\n"), size=12.5, color=MUTED, align=PP_ALIGN.CENTER)
rect(s, Inches(8.2), Inches(5.45), Inches(4.5), Inches(1.45), fill=CARD2, line=ORANGE)
text(s, Inches(8.3), Inches(5.5), Inches(4.3), Inches(1.4), [
    "Conclusión: control proporcional por PWM con zona muerta; satura solo ante restricción física persistente."],
     size=15, bold=True, anchor=MSO_ANCHOR.MIDDLE)

# =====================================================================
# 11. PROTOTIPO FÍSICO
# =====================================================================
s = new_slide(
    "(45 s) Ya integramos todo en el prototipo físico: la cámara detecta el gesto, la GUI manda por BLE al ESP32 y "
    "el módulo ejecuta. Aquí la rutina SALUDO en tres etapas. Los logs confirman conexión BLE, comandos de ángulos "
    "durante el tracking y envío de las rutinas SALUDO y CORAZÓN. Aclaramos que esto es evidencia cualitativa: "
    "falta medir precisión y latencia con cámara de alta velocidad.")
header(s, "Validación en el prototipo físico", "Resultados funcionales", 11)
pic(s, "modulo_fisico.png", Inches(0.6), Inches(1.75), Inches(4.3), Inches(2.3), caption="Módulo físico con ESP32-C3")
for i, (nm, cap) in enumerate([("sofia_saludo1.png", "Inicio"), ("sofia_saludo2.png", "Intermedio"), ("sofia_saludo3.png", "Final")]):
    pic(s, nm, Inches(5.2 + i * 2.5), Inches(1.75), Inches(2.4), Inches(1.5), caption=f"SALUDO · {cap}")
logs = [("Arranque de visión", "modelos cargados, cámara activa"),
        ("Conexión BLE", "conexión exitosa registrada"),
        ("Seguimiento de articulaciones", "comandos de ángulo variables"),
        ("Rutinas dinámicas", "SALUDO y CORAZÓN enviadas"),
        ("Coordinación", "tracking se reanuda tras el temporizador"),
        ("Apagado", "cámara detenida, BLE cerrado")]
for i, (a, b) in enumerate(logs):
    x = Inches(0.6 + (i % 2) * 6.15)
    y = Inches(4.55 + (i // 2) * 0.78)
    rect(s, x, y, Inches(5.95), Inches(0.68), fill=CARD)
    text(s, x + Inches(0.1), y, Inches(0.5), Inches(0.68), "✓", size=22, bold=True, color=TEAL, anchor=MSO_ANCHOR.MIDDLE)
    text(s, x + Inches(0.55), y, Inches(5.3), Inches(0.68), [f"{a}: {b}"], size=14.5, anchor=MSO_ANCHOR.MIDDLE)
text(s, Inches(5.2), Inches(3.55), Inches(7.5), Inches(0.9),
     "Evidencia cualitativa: los logs y fotos no cuantifican precisión, latencia ni repetibilidad (siguiente paso).",
     size=13.5, color=ORANGE, italic=True)

# =====================================================================
# 12. PROTECCIÓN + PROTOCOLO + FUTURO
# =====================================================================
s = new_slide(
    "(50 s) Con lo medido, proponemos protecciones: limitar ángulos al rango verificado, y un watchdog que, si hay "
    "bloqueo o desviación sostenida por más de 15 s, suspende el PWM de ese canal; el eje queda libre y deja de "
    "calentarse. El siguiente paso es el protocolo de seguimiento mano-servo: 10 repeticiones, error angular en "
    "grados, retardo en ms y ángulo real medido con video de alta velocidad.")
header(s, "Protecciones y protocolo de validación", "Qué sigue", 12)
rect(s, Inches(0.6), Inches(1.75), Inches(5.95), Inches(5.05), fill=CARD, line=RED)
text(s, Inches(0.85), Inches(1.85), Inches(5.5), Inches(0.5), "Protecciones propuestas", size=20, bold=True, color=RED)
bullets(s, Inches(0.85), Inches(2.45), Inches(5.5), Inches(4.3), [
    ("Saturación de comandos: ", "ángulos limitados al rango verificado."),
    ("Watchdog de bloqueo: ", "I > 450 mA o desviación > 15 s → se suspende el PWM del canal."),
    ("Resultado: ", "eje libre, sin calentamiento Joule (umbral de seguridad 55 °C)."),
    ("Limitación: ", "el LM35 mide la carcasa, no el devanado."),
], size=15.5, gap=9, dot=RED)
rect(s, Inches(6.75), Inches(1.75), Inches(5.95), Inches(5.05), fill=CARD, line=TEAL)
text(s, Inches(7.0), Inches(1.85), Inches(5.5), Inches(0.5), "Protocolo de seguimiento (siguiente)", size=20, bold=True, color=TEAL)
bullets(s, Inches(7.0), Inches(2.45), Inches(5.5), Inches(4.3), [
    ("Trayectorias: ", "oscilación senoidal 0.2–0.8 Hz y escalones de 5°, 30° y 90°."),
    ("Repeticiones: ", "N = 10 por condición."),
    ("Métricas: ", "error angular (MAE, RMSE en °) y retardo mano→servo (ms)."),
    ("Ángulo real: ", "cámara a 120 FPS con marcadores en la faceta."),
    ("Meta: ", "validar los 16 módulos y suavizar trayectorias."),
], size=15.5, gap=9)

# =====================================================================
# 13. CONCLUSIONES
# =====================================================================
s = new_slide(
    "(30 s) En resumen: SOFIA integra visión y robótica modular; el bloqueo calienta 0.214 grados por segundo; "
    "el servo es proporcional con zona muerta y no bang-bang; y ya tenemos prototipo físico respondiendo a gestos. "
    "Lo que sigue es cuantificar el seguimiento y escalar. Gracias; con gusto respondemos preguntas.")
header(s, "Conclusiones", "Resumen", 13)
concl = [
    ("Arquitectura", "SOFIA integra visión 3D con 16 módulos 2-GDL (32 MG90S) vía ESP32-C3 y PCA9685.", TEAL),
    ("Térmica", "Bloqueo sostenido → 0.214 °C/s y 70.21 °C: hacen falta límites y watchdog.", ORANGE),
    ("Actuador", "El MG90S es proporcional con zona muerta, no bang-bang; satura solo si se traba.", TEAL),
    ("Prototipo", "Ya responde a gestos (SALUDO, CORAZÓN) en el módulo físico.", ORANGE),
]
for i, (t, d, c) in enumerate(concl):
    x = Inches(0.6 + (i % 2) * 6.15)
    y = Inches(1.75 + (i // 2) * 1.75)
    rect(s, x, y, Inches(5.95), Inches(1.55), fill=CARD, line=c)
    text(s, x + Inches(0.2), y + Inches(0.1), Inches(5.5), Inches(0.45), t, size=19, bold=True, color=c)
    text(s, x + Inches(0.2), y + Inches(0.6), Inches(5.55), Inches(0.9), d, size=15, color=WHITE)
rect(s, Inches(0.6), Inches(5.4), Inches(12.1), Inches(1.45), fill=CARD2)
text(s, Inches(0.85), Inches(5.45), Inches(11.6), Inches(0.5), "Trabajo futuro", size=17, bold=True, color=ORANGE)
text(s, Inches(0.85), Inches(5.95), Inches(11.6), Inches(0.9),
     "Cuantificar precisión, latencia y repetibilidad del seguimiento · validar la PCB · "
     "escalar de 1 módulo a los 16 · suavizado de trayectorias.", size=15.5)

# =====================================================================
# 14. GRACIAS
# =====================================================================
s = new_slide("Cierre y preguntas.")
rect(s, 0, 0, W, H, fill=BG, shape=MSO_SHAPE.RECTANGLE)
rect(s, 0, 0, Inches(0.18), H, fill=TEAL, shape=MSO_SHAPE.RECTANGLE)
pic(s, "sofia_saludo2.png", Inches(8.3), Inches(1.4), Inches(4.5), Inches(2.6), card=True)
pic(s, "fig_sim_3.png", Inches(8.3), Inches(4.2), Inches(4.5), Inches(2.4), card=True)
text(s, Inches(0.8), Inches(1.8), Inches(7), Inches(1.4), "¡Gracias!", size=72, bold=True)
text(s, Inches(0.8), Inches(3.3), Inches(7), Inches(0.8), "¿Preguntas?", size=34, color=TEAL, bold=True)
rect(s, Inches(0.85), Inches(4.3), Inches(1.2), Inches(0.06), fill=ORANGE, shape=MSO_SHAPE.RECTANGLE)
text(s, Inches(0.8), Inches(4.55), Inches(7), Inches(1.6), [
    "SOFIA · Equipo 1 · LabDST · ITESO",
    "github.com/PaolaCV14/IOT-SOFIA-2026",
    "Release v0.2.0 · datos experimentales en docs/experimental-data/"], size=16, color=MUTED)

prs.save(OUT)
print("OK ->", OUT, "| slides:", len(prs.slides))
