"""Genera SOFIA_LabDST_Presentacion.pptx (16:9) con python-pptx.
Presentación Oficial de Avance - Segundo Corte (LabDST, ITESO, Otoño 2026).
Diseño ejecutivo de alto impacto, ultra-limpio y visual:
- Objetivo estricto de tiempo: 7 min 25 s (10 diapositivas).
- Títulos con punch (afirmaciones, no categorías de rúbrica).
- Máximo 3 bloques de texto por slide, máximo 15 palabras por bloque.
- Tipografía grande: Títulos >= 40 pt, Números >= 60 pt, Cuerpo >= 24 pt.
- Imágenes enormes (50% a 70% de área en slides de evidencia).
- Sin nombres de expositores (solo tiempo y guion conversacional).
- Notas de Slide 10 con 5 preguntas probables de jueces y respuestas breves.

Uso: python3 build_deck.py
"""
import os
import tempfile
from PIL import Image
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE, MSO_CONNECTOR
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR

HERE = os.path.dirname(os.path.abspath(__file__))
FIG = os.path.join(HERE, "..", "paper", "Equipo 1 - segundo corte", "figures")
OUT = os.path.join(HERE, "SOFIA_LabDST_Presentacion.pptx")
TMP = tempfile.mkdtemp()

# =====================================================================
# PALETA VISUAL MODERNA — DARK OBSIDIAN & VIBRANT FUCHSIA
# =====================================================================
BG = RGBColor(0x0F, 0x10, 0x16)       # Fondo oscuro neutro / Slate Obsidian (#0F1016)
CARD = RGBColor(0x18, 0x19, 0x26)     # Superficie de tarjeta oscura (#181926)
CARD_HI = RGBColor(0x2A, 0x1B, 0x38)  # Tarjeta destacada con tinte fuchsia sutil (#2A1B38)
TEAL = RGBColor(0xE0, 0x24, 0xA5)     # Acento principal: Fiusha chillón moderno (#E024A5)
AMBER = RGBColor(0xF5, 0x9E, 0x0B)    # Acento secundario: Ámbar dorado cálido (#F59E0B)
CORAL = RGBColor(0xFB, 0x71, 0x85)    # Acento de alerta térmica: Rose / Fuchsia (#FB7185)
WHITE = RGBColor(0xFA, 0xF5, 0xFF)    # Blanco puro cristalino (#FAF5FF)
MUTED = RGBColor(0xC4, 0xB5, 0xFD)    # Secundario suave (#C4B5FD)
FONT = "Calibri"

prs = Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)
W, H = prs.slide_width, prs.slide_height
BLANK = prs.slide_layouts[6]


# =====================================================================
# HELPERS
# =====================================================================
def new_slide(notes=""):
    s = prs.slides.add_slide(BLANK)
    s.background.fill.solid()
    s.background.fill.fore_color.rgb = BG
    if notes:
        s.notes_slide.notes_text_frame.text = notes
    return s


def rect(s, x, y, w, h, fill=CARD, line=None, shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.04):
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


def title_header(s, title, rubric_tag=None, n=None):
    # Franja de acento a la izquierda
    rect(s, 0, 0, Inches(0.18), H, fill=TEAL, shape=MSO_SHAPE.RECTANGLE)
    
    # Tag de rúbrica pequeño y discreto en la esquina superior
    if rubric_tag:
        text_box(s, Inches(0.8), Inches(0.35), Inches(8.5), Inches(0.3),
                 rubric_tag.upper(), size=12, color=TEAL, bold=True)
    
    # Título principal con PUNCH (>= 40 pt)
    text_box(s, Inches(0.8), Inches(0.68), Inches(11.8), Inches(0.85),
             title, size=40, color=WHITE, bold=True)
    
    # Número de slide discreto en la esquina inferior derecha
    if n:
        text_box(s, Inches(12.0), Inches(7.05), Inches(1.0), Inches(0.3),
                 f"{n}/10", size=13, color=MUTED, align=PP_ALIGN.RIGHT)


def text_box(s, x, y, w, h, content, size=24, color=WHITE, bold=False, align=PP_ALIGN.LEFT,
             anchor=MSO_ANCHOR.TOP, italic=False):
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


def prep(name, maxw=2000):
    src = os.path.join(FIG, name)
    im = Image.open(src)
    if im.width > maxw:
        im = im.resize((maxw, int(im.height * maxw / im.width)), Image.LANCZOS)
    dst = os.path.join(TMP, name.replace(" ", "_"))
    im.convert("RGB").save(dst, quality=92)
    return dst, im.size


def pic(s, name, x, y, w, h, card=True, caption=None, white_bg=False):
    path, (iw, ih) = prep(name)
    pad = Inches(0.06)
    if card:
        rect(s, x, y, w, h, fill=RGBColor(255, 255, 255) if white_bg else CARD, radius=0.03)
    bw, bh = w - 2 * pad, h - 2 * pad
    ratio = min(bw / iw, bh / ih)
    pw, ph = int(iw * ratio), int(ih * ratio)
    s.shapes.add_picture(path, x + (w - pw) // 2, y + (h - ph) // 2, pw, ph)
    if caption:
        text_box(s, x, y + h + Inches(0.02), w, Inches(0.28), caption, size=13, color=MUTED,
                 align=PP_ALIGN.CENTER, italic=True)


def arrow(s, x1, y1, x2, y2, color=TEAL):
    c = s.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, x1, y1, x2, y2)
    c.line.color.rgb = color
    c.line.width = Pt(2.0)
    ln = c.line._get_or_add_ln()
    from lxml import etree
    tail = etree.SubElement(ln, "{http://schemas.openxmlformats.org/drawingml/2006/main}tailEnd")
    tail.set("type", "triangle")
    return c


# =====================================================================
# 1. PORTADA (15 s)
# =====================================================================
s1 = new_slide(
    "Tiempo: 15 s\n"
    "Buenos días profesores y evaluadores. Presentamos SOFÍA: una pared robótica interactiva con paneles tipo panal "
    "que te siguen con la mirada y responden a tus gestos en vivo, junto con nuestras pruebas para operarla de forma segura.")

rect(s1, 0, 0, W, H, fill=BG, shape=MSO_SHAPE.RECTANGLE)
rect(s1, 0, 0, Inches(0.18), H, fill=TEAL, shape=MSO_SHAPE.RECTANGLE)

# Kicker y Título principal
text_box(s1, Inches(0.8), Inches(0.6), Inches(11.8), Inches(0.35),
         "LABDST · ITESO · EVALUACIÓN DE SEGUNDO CORTE (OTOÑO 2026)", size=14, color=TEAL, bold=True)
text_box(s1, Inches(0.8), Inches(1.05), Inches(11.8), Inches(1.1),
         "SOFÍA: la pared que te mira", size=54, color=WHITE, bold=True)
text_box(s1, Inches(0.8), Inches(2.25), Inches(11.8), Inches(0.6),
         "Pared robótica interactiva de paneles que te siguen y hacen rutinas", size=24, color=MUTED)

# 2 Imágenes GRANDES ocupando 60% del ancho
pic(s1, "sofia_solid.png", Inches(0.8), Inches(3.05), Inches(5.7), Inches(3.7), card=True,
    caption="Diseño 3D de paneles móviles en panal")
pic(s1, "modulo_fisico.png", Inches(6.8), Inches(3.05), Inches(5.7), Inches(3.7), card=True,
    caption="Prototipo físico montado y funcional")

text_box(s1, Inches(0.8), Inches(7.05), Inches(8.0), Inches(0.3),
         "Equipo 1 · Ingeniería ITESO", size=13, color=MUTED)


# =====================================================================
# 2. EL PROBLEMA Y LO QUE QUEREMOS (45 s)
# =====================================================================
s2 = new_slide(
    "Tiempo: 45 s\n"
    "Las paredes cinéticas en museos o aeropuertos cuestan millones de pesos y si alguien las toca se queman. "
    "Nuestro objetivo es crear una pared modular accesible que te siga con la mirada y se autoproteja de sobrecalentamientos.")

title_header(s2, "Las paredes interactivas cuestan millones y se queman", "Rúbrica: Planteamiento y Marco (20%)", 2)

# Imagen de piezas impresas en 3D (Grande a la izquierda)
pic(s2, "sofia_exploded.png", Inches(0.8), Inches(1.75), Inches(4.3), Inches(5.0), card=True,
    caption="Piezas impresas en 3D")

# Bloque 1: El problema (3 tarjetas punch)
y_b1 = Inches(1.75)
p_items = [
    ("💰 Carísimas", "Cuestan millones"),
    ("🔒 Motores cerrados", "Mecánica inaccesible"),
    ("🔥 Se sobrecalientan", "Riesgo al detenerse"),
]
for i, (t, sub) in enumerate(p_items):
    bx = Inches(5.4 + i * 2.45)
    rect(s2, bx, y_b1, Inches(2.3), Inches(1.2), fill=CARD, line=CORAL)
    text_box(s2, bx, y_b1 + Inches(0.12), Inches(2.3), Inches(0.4), t, size=20, bold=True, color=CORAL, align=PP_ALIGN.CENTER)
    text_box(s2, bx, y_b1 + Inches(0.58), Inches(2.3), Inches(0.4), sub, size=15, color=MUTED, align=PP_ALIGN.CENTER)

# Bloque 2: Objetivo en 1 frase + 3 de 5 palabras
rect(s2, Inches(5.4), Inches(3.15), Inches(7.2), Inches(2.1), fill=CARD_HI, line=TEAL)
text_box(s2, Inches(5.65), Inches(3.25), Inches(6.7), Inches(0.7),
         "Objetivo: crear una pared robótica accesible que te siga en tiempo real y sea segura.",
         size=22, bold=True, color=WHITE)

objs = [
    "▸ Paneles modulares en 3D",
    "▸ Sigan y reaccionen a gestos",
    "▸ Protegerse del sobrecalentamiento",
]
for idx, o in enumerate(objs):
    text_box(s2, Inches(5.65), Inches(4.05 + idx * 0.38), Inches(6.7), Inches(0.35),
             o, size=18, color=TEAL, bold=True)

# Bloque 3: Línea de tiempo D-Lab + Materiales
rect(s2, Inches(5.4), Inches(5.45), Inches(7.2), Inches(1.3), fill=CARD)
text_box(s2, Inches(5.65), Inches(5.55), Inches(6.7), Inches(0.4),
         "Corte 1: Diseño  ➔  Corte 2: Prototipo [ESTAMOS AQUÍ]  ➔  Corte 3: Pared completa",
         size=16, bold=True, color=AMBER)
text_box(s2, Inches(5.65), Inches(6.05), Inches(6.7), Inches(0.6),
         "Materiales: 16 módulos PLA SOFIA003, 32 servos MG90S, 64 tornillos M3, 2 PCA9685, 1 ESP32-C3 y cámara.", size=14, color=MUTED)


# =====================================================================
# 3. QUÉ EXISTE Y EN QUÉ SOMOS DISTINTOS (40 s)
# =====================================================================
s3 = new_slide(
    "Tiempo: 40 s\n"
    "Las obras existentes como inFORM del MIT o las esculturas de aeropuertos son carísimas o solo repiten videos sin verte. "
    "SOFÍA te ve en vivo, es modular y accesible. Nuestro diferenciador clave es el estudio térmico: como el servomotor comercial "
    "NO tiene sensor interno de temperatura, medimos su calentamiento en laboratorio con termómetro láser y osciloscopio "
    "para diseñar su corte preventivo.")

title_header(s3, "Hermosas, caras y sin ojos", "Rúbrica: Planteamiento y Marco (20%)", 3)

# 3 Columnas
cw3 = Inches(3.8)

# Col 1: MIT inFORM
rect(s3, Inches(0.8), Inches(1.8), cw3, Inches(4.9), fill=CARD)
text_box(s3, Inches(1.05), Inches(2.0), cw3 - Inches(0.5), Inches(0.5),
         "MIT inFORM", size=28, bold=True, color=WHITE)
text_box(s3, Inches(1.05), Inches(2.6), cw3 - Inches(0.5), Inches(0.4),
         "Mesas cinéticas motorizadas", size=18, color=MUTED, italic=True)
text_box(s3, Inches(1.05), Inches(3.2), cw3 - Inches(0.5), Inches(3.0),
         ["▸ 900 barras móviles",
          "",
          "▸ Millones de pesos en costo",
          "",
          "▸ Atadas a un laboratorio"], size=22, color=WHITE)

# Col 2: Esculturas de aeropuerto
rect(s3, Inches(4.8), Inches(1.8), cw3, Inches(4.9), fill=CARD)
text_box(s3, Inches(5.05), Inches(2.0), cw3 - Inches(0.5), Inches(0.5),
         "Arte Comercial", size=28, bold=True, color=WHITE)
text_box(s3, Inches(5.05), Inches(2.6), cw3 - Inches(0.5), Inches(0.4),
         "Esculturas en aeropuertos", size=18, color=MUTED, italic=True)
text_box(s3, Inches(5.05), Inches(3.2), cw3 - Inches(0.5), Inches(3.0),
         ["▸ Coreografía en bucle fijo",
          "",
          "▸ Cero interacción viva",
          "",
          "▸ No te ven ni te siguen"], size=22, color=WHITE)

# Col 3: SOFÍA (Destacada con borde TEAL)
rect(s3, Inches(8.8), Inches(1.8), cw3, Inches(4.9), fill=CARD_HI, line=TEAL)
text_box(s3, Inches(9.05), Inches(2.0), cw3 - Inches(0.5), Inches(0.5),
         "SOFÍA (ITESO)", size=30, bold=True, color=TEAL)
text_box(s3, Inches(9.05), Inches(2.6), cw3 - Inches(0.5), Inches(0.4),
         "Pared interactiva inteligente", size=18, color=AMBER, italic=True)
text_box(s3, Inches(9.05), Inches(3.1), cw3 - Inches(0.5), Inches(1.8),
         ["⭐ Te ve y te sigue en vivo",
          "⭐ Modular en 3D (16 módulos)",
          "⭐ Sin sensor interno: medido con láser y osciloscopio"], size=18, color=WHITE, bold=True)
pic(s3, "sofia_solid.png", Inches(9.1), Inches(4.95), Inches(3.2), Inches(1.65), card=True)


# =====================================================================
# 4. CÓMO LO PROBAMOS (50 s)
# =====================================================================
s4 = new_slide(
    "Tiempo: 50 s\n"
    "Medimos velocidad de cámara, respuesta a gestos y calor del motor con termómetro láser, osciloscopio e instrumentos mecatrónicos. "
    "Nuestros criterios de aprobación son claros: más de 30 cuadros por segundo, respuesta en menos de 100 milisegundos "
    "y corte de seguridad en menos de 15 segundos si algo se atora.")

title_header(s4, "Tres cosas medidas, tres líneas rojas", "Rúbrica: Diseño de la Investigación (20%)", 4)

# Cadena horizontal superior con íconos
pipe_w = Inches(2.15)
pipe_items = [
    ("📷 Cámara web", "30 FPS"),
    ("💻 Software PC", "Detecta tu mano"),
    ("📶 Bluetooth", "Sin cables LE"),
    ("⚡ ESP32 + 2x PCA", "Control 32 canales"),
    ("🌸 16 Paneles", "32 servos MG90S"),
]
py = Inches(1.8)
for i, (p_t, p_s) in enumerate(pipe_items):
    px = Inches(0.8 + i * 2.45)
    rect(s4, px, py, pipe_w, Inches(1.15), fill=CARD, line=TEAL)
    text_box(s4, px, py + Inches(0.12), pipe_w, Inches(0.4), p_t, size=18, bold=True, color=TEAL, align=PP_ALIGN.CENTER)
    text_box(s4, px, py + Inches(0.58), pipe_w, Inches(0.4), p_s, size=14, color=MUTED, align=PP_ALIGN.CENTER)
    if i < 4:
        arrow(s4, px + pipe_w, py + Inches(0.57), Inches(0.8 + (i + 1) * 2.45), py + Inches(0.57))

# 3 Tarjetas inferiores
tc_w = Inches(3.8)
tc_y = Inches(3.25)
tc_h = Inches(3.5)

# Qué medimos
rect(s4, Inches(0.8), tc_y, tc_w, tc_h, fill=CARD)
text_box(s4, Inches(1.05), tc_y + Inches(0.2), tc_w - Inches(0.5), Inches(0.5),
         "1. Qué medimos", size=26, bold=True, color=WHITE)
text_box(s4, Inches(1.05), tc_y + Inches(0.85), tc_w - Inches(0.5), Inches(2.3),
         ["▸ Velocidad de cámara",
          "",
          "▸ Respuesta al saludo",
          "",
          "▸ Calor del motor"], size=22, color=MUTED)

# Con qué
rect(s4, Inches(4.8), tc_y, tc_w, tc_h, fill=CARD)
text_box(s4, Inches(5.05), tc_y + Inches(0.2), tc_w - Inches(0.5), Inches(0.5),
         "2. Con qué", size=26, bold=True, color=WHITE)
text_box(s4, Inches(5.05), tc_y + Inches(0.85), tc_w - Inches(0.5), Inches(2.3),
         ["▸ Cámara web HD (30 FPS)",
          "",
          "▸ Termómetro láser y osciloscopio",
          "",
          "▸ Sin sensor en motor (banco con tope)"], size=19, color=MUTED)

# Aprobamos si
rect(s4, Inches(8.8), tc_y, tc_w, tc_h, fill=CARD_HI, line=TEAL)
text_box(s4, Inches(9.05), tc_y + Inches(0.2), tc_w - Inches(0.5), Inches(0.5),
         "3. Aprobamos si", size=26, bold=True, color=TEAL)
text_box(s4, Inches(9.05), tc_y + Inches(0.85), tc_w - Inches(0.5), Inches(2.3),
         ["⭐ > 30 FPS y < 100 ms",
          "",
          "⭐ Bajo 55 °C",
          "",
          "⭐ Corte antes de 15 s"], size=22, color=WHITE, bold=True)


# =====================================================================
# 5. EL SOFTWARE QUE TE VE (45 s)
# =====================================================================
s5 = new_slide(
    "Tiempo: 45 s\n"
    "Nuestra estación de control procesa la mano a más de 30 cuadros por segundo en tiempo real. "
    "Reconoce gestos como saludos y corazones, y simulamos los 16 paneles en Unity para que se muevan coordinados sin chocar.")

title_header(s5, "Te sigue la mano a más de 30 cuadros por segundo", "Rúbrica: Desarrollo y Resultados (20%)", 5)

# Captura de pantalla de la GUI GRANDE a la izquierda (62% del ancho)
pic(s5, "sofia_gui.png", Inches(0.8), Inches(1.8), Inches(7.5), Inches(4.9), card=True,
    caption="Estación de control en tiempo real (PySide6)")

# Columna derecha: Stat gigante + gestos + Unity frames
rect(s5, Inches(8.6), Inches(1.8), Inches(4.0), Inches(1.6), fill=CARD_HI, line=TEAL)
text_box(s5, Inches(8.6), Inches(1.9), Inches(4.0), Inches(0.8), "30+ FPS", size=60, bold=True, color=TEAL, align=PP_ALIGN.CENTER)
text_box(s5, Inches(8.6), Inches(2.8), Inches(4.0), Inches(0.4), "Visión fluida en tiempo real", size=18, color=MUTED, align=PP_ALIGN.CENTER)

rect(s5, Inches(8.6), Inches(3.6), Inches(4.0), Inches(1.4), fill=CARD)
text_box(s5, Inches(8.8), Inches(3.72), Inches(3.6), Inches(0.35), "Gestos reconocidos:", size=18, bold=True, color=AMBER)
text_box(s5, Inches(8.8), Inches(4.15), Inches(3.6), Inches(0.7),
         "👋 Saludo   ·   💖 Corazón   ·   👊 Puño", size=18, color=WHITE, bold=True)

# Frames de Unity debajo
pic(s5, "fig_sim_1.png", Inches(8.6), Inches(5.2), Inches(1.9), Inches(1.5), card=True)
pic(s5, "fig_sim_3.png", Inches(10.7), Inches(5.2), Inches(1.9), Inches(1.5), card=True)


# =====================================================================
# 6. EL PROTOTIPO FÍSICO RESPONDE (40 s)
# =====================================================================
s6 = new_slide(
    "Tiempo: 40 s\n"
    "Aquí vemos el prototipo físico real. Cámara y Bluetooth tardan 45 a 50 milisegundos, "
    "y el servo 75 a 180 ms en moverse. Ensayos repetidos con N=10 validan la fluidez.")

title_header(s6, "Saludas, y el panel te contesta", "Rúbrica: Desarrollo y Resultados (20%)", 6)

# Secuencia de 4 fotos grandes lado a lado ocupando 65% del área
pic_w = Inches(2.8)
pic_h = Inches(3.8)
pic_y = Inches(1.8)

pic(s6, "modulo_fisico.png", Inches(0.8), pic_y, pic_w, pic_h, card=True, caption="1. Módulo físico")
pic(s6, "sofia_saludo1.png", Inches(3.8), pic_y, pic_w, pic_h, card=True, caption="2. Gesto detectado")
pic(s6, "sofia_saludo2.png", Inches(6.8), pic_y, pic_w, pic_h, card=True, caption="3. Panel oscilando")
pic(s6, "sofia_saludo3.png", Inches(9.8), pic_y, pic_w, pic_h, card=True, caption="4. Retorno a centro")

# 3 Puntos punch debajo en barra horizontal
rect(s6, Inches(0.8), Inches(5.95), Inches(11.8), Inches(0.9), fill=CARD)
p6_items = [
    "⏱️ Cámara + BLE: ~45–50 ms",
    "🔄 Ensayos repetidos (N=10)",
    "🛡️ Corte < 15 s diseñado",
]
for i, pt in enumerate(p6_items):
    text_box(s6, Inches(0.9 + i * 3.9), Inches(6.15), Inches(3.8), Inches(0.5),
             pt, size=20, bold=True, color=WHITE, align=PP_ALIGN.CENTER)


# =====================================================================
# 7. EL HALLAZGO CLAVE (50 s)
# =====================================================================
s7 = new_slide(
    "Tiempo: 50 s\n"
    "Este es nuestro hallazgo experimental más importante: sin carga el motor no se calienta. "
    "Pero atorado con un tope, sube unos 13 grados por minuto hasta llegar a 64.8 grados en menos de cuatro minutos; "
    "a los 3 minutos ya pasa de 55 grados, entrando a zona de riesgo. Con corte a 15 segundos solo sube unos 3 grados.")

title_header(s7, "Si un panel se atora, en menos de 4 minutos se quema", "Rúbrica: Desarrollo y Resultados (20%)", 7)

# Gráfica térmica real ocupando el 60% del slide a la izquierda
pic(s7, "fig_thermal_response.png", Inches(0.8), Inches(1.8), Inches(7.5), Inches(4.9), card=True,
    caption="Medición en banco con termómetro láser y osciloscopio (el motor no tiene sensor interno)")

# Columna derecha: 2 números enormes + frase punch
# Número 1: 64.8 °C
rect(s7, Inches(8.6), Inches(1.8), Inches(4.0), Inches(1.5), fill=CARD, line=CORAL)
text_box(s7, Inches(8.6), Inches(1.9), Inches(4.0), Inches(0.75), "64.8 °C", size=60, bold=True, color=CORAL, align=PP_ALIGN.CENTER)
text_box(s7, Inches(8.6), Inches(2.75), Inches(4.0), Inches(0.4), "a los 226 s (engrane forzado)", size=16, color=MUTED, align=PP_ALIGN.CENTER)

# Número 2: 13 °C / min
rect(s7, Inches(8.6), Inches(3.5), Inches(4.0), Inches(1.5), fill=CARD, line=AMBER)
text_box(s7, Inches(8.6), Inches(3.6), Inches(4.0), Inches(0.75), "13 °C/min", size=52, bold=True, color=AMBER, align=PP_ALIGN.CENTER)
text_box(s7, Inches(8.6), Inches(4.45), Inches(4.0), Inches(0.4), "a 3 min: 55 °C límite seguro", size=16, color=MUTED, align=PP_ALIGN.CENTER)

# Frase de decisión punch
rect(s7, Inches(8.6), Inches(5.2), Inches(4.0), Inches(1.5), fill=CARD_HI, line=TEAL)
text_box(s7, Inches(8.8), Inches(5.4), Inches(3.6), Inches(1.1),
         "Con corte a 15 s: sube solo ~3 °C", size=24, bold=True, color=TEAL, align=PP_ALIGN.CENTER)


# =====================================================================
# 8. POR QUÉ TODAVÍA NO VA A UN MUSEO (I) - GENTE Y ENTORNO (40 s)
# =====================================================================
s8 = new_slide(
    "Tiempo: 40 s\n"
    "¿Por qué SOFÍA todavía no puede operar en un museo? En el laboratorio probamos con 1 persona a 1 metro y luz controlada. "
    "En un museo hay multitud de personas cruzando manos, luz solar cambiante y se necesita un sistema embebido dentro del marco.")

title_header(s8, "El laboratorio es fácil. Un museo no", "Rúbrica: Brecha con el Entorno Real (20%)", 8)

# Encabezados de tabla
rect(s8, Inches(0.8), Inches(1.8), Inches(5.7), Inches(0.6), fill=CARD)
text_box(s8, Inches(0.8), Inches(1.9), Inches(5.7), Inches(0.4), "Hoy en Laboratorio", size=22, bold=True, color=TEAL, align=PP_ALIGN.CENTER)

rect(s8, Inches(6.8), Inches(1.8), Inches(5.7), Inches(0.6), fill=CARD)
text_box(s8, Inches(6.8), Inches(1.9), Inches(5.7), Inches(0.4), "Exigencia de un Museo", size=22, bold=True, color=AMBER, align=PP_ALIGN.CENTER)

# 4 Filas de comparación
b1_rows = [
    ("👤 1 persona quieta", "👥 Multitud de visitantes cruzando manos"),
    ("💡 Luz controlada", "☀️ Sol directo, reflejos y sombras dinámicas"),
    ("📏 Distancia fija a 1 m", "📐 Público pasando a 3 o 5 metros"),
    ("💻 Laptop con cables", "📦 Sistema embebido oculto en el marco"),
]
for i, (hoy, mus) in enumerate(b1_rows):
    ry = Inches(2.6 + i * 1.05)
    # Celda Hoy
    rect(s8, Inches(0.8), ry, Inches(5.7), Inches(0.9), fill=CARD)
    text_box(s8, Inches(1.1), ry + Inches(0.25), Inches(5.2), Inches(0.5), hoy, size=22, color=WHITE)
    
    # Celda Museo
    rect(s8, Inches(6.8), ry, Inches(5.7), Inches(0.9), fill=CARD_HI, line=AMBER)
    text_box(s8, Inches(7.1), ry + Inches(0.25), Inches(5.2), Inches(0.5), mus, size=22, color=WHITE, bold=True)


# =====================================================================
# 9. POR QUÉ TODAVÍA NO VA A UN MUSEO (II) - OPERACIÓN Y SEGURIDAD (40 s)
# =====================================================================
s9 = new_slide(
    "Tiempo: 40 s\n"
    "La segunda brecha se basa en nuestros datos: un museo opera 12 horas seguidas, los niños van a jalar los pétalos "
    "demandando 0.9 amperes y disipando 4.6 watts de calor. Los 32 motores piden hasta 23 amperes al arrancar juntos "
    "requiriendo fuente de 25 amperes. Aun sin público, los pétalos se rozan por tolerancias de impresión (±0.4 mm); "
    "falta un acople mecánico que ceda sin romper engranes.")

title_header(s9, "10 minutos vs 12 horas", "Rúbrica: Brecha con el Entorno Real (20%)", 9)

# Encabezados de tabla
rect(s9, Inches(0.8), Inches(1.8), Inches(5.7), Inches(0.6), fill=CARD)
text_box(s9, Inches(0.8), Inches(1.9), Inches(5.7), Inches(0.4), "Nuestros Datos de Prueba", size=22, bold=True, color=TEAL, align=PP_ALIGN.CENTER)

rect(s9, Inches(6.8), Inches(1.8), Inches(5.7), Inches(0.6), fill=CARD)
text_box(s9, Inches(6.8), Inches(1.9), Inches(5.7), Inches(0.4), "Exigencia de un Museo", size=22, bold=True, color=CORAL, align=PP_ALIGN.CENTER)

# 4 Filas de comparación
b2_rows = [
    ("⏱️ Pruebas de 10 min", "⏳ 8 a 12 horas diarias ininterrumpidas"),
    ("🚫 Nadie toca la pared", "👶 Niños jalando pétalos (atasco: 0.9 A y 4.6 W)"),
    ("🔌 1 módulo probado", "⚡ 32 motores: ~23 A al arrancar (fuente 25 A)"),
    ("🛠️ Reinicia un ingeniero", "🔄 Se auto-recupera sola ante fallas"),
]
for i, (hoy, mus) in enumerate(b2_rows):
    ry = Inches(2.6 + i * 1.05)
    # Celda Hoy
    rect(s9, Inches(0.8), ry, Inches(5.7), Inches(0.9), fill=CARD)
    text_box(s9, Inches(1.1), ry + Inches(0.25), Inches(5.2), Inches(0.5), hoy, size=22, color=WHITE)
    
    # Celda Museo
    rect(s9, Inches(6.8), ry, Inches(5.7), Inches(0.9), fill=CARD_HI, line=CORAL)
    text_box(s9, Inches(7.1), ry + Inches(0.25), Inches(5.2), Inches(0.5), mus, size=22, color=WHITE, bold=True)


# =====================================================================
# 10. QUÉ CORREGIMOS Y QUÉ SIGUE (40 s + PREGUNTAS DE JUECES)
# =====================================================================
notes_10 = (
    "Tiempo: 40 s\n"
    "Atendimos las observaciones del Corte 1 con objetivos delimitados y mediciones reales de calor. "
    "Para el Corte 3 fabricaremos la PCB de potencia, el corte automático y montaremos los 16 paneles. "
    "Muchas gracias, abrimos la sesión de preguntas.\n\n"
    "--- PREGUNTAS PROBABLES DE LOS JUECES Y RESPUESTAS BREVES ---\n"
    "1. ¿Por qué el servomotor MG90S?\n"
    "R: Por engranaje metálico, bajo costo comercial, accesibilidad y facilidad de reemplazo modular en 32 actuadores.\n\n"
    "2. ¿Cómo detecta el atasco si el motor no tiene sensor de temperatura?\n"
    "R: El motor comercial NO tiene sensor térmico interno ni avisa que está forzado. En laboratorio caracterizamos su curva con termómetro láser y osciloscopio mecatrónico. En la pared final, la placa monitorea la corriente y el ESP32 corta la señal PWM tras 15 s para proteger la estructura de PLA.\n\n"
    "3. ¿Cuánto cuesta frente a una pared comercial?\n"
    "R: Una instalación comercial cuesta cientos de miles de pesos; SOFÍA cuesta una fracción gracias a impresión 3D y componentes IoT accesibles.\n\n"
    "4. ¿Qué pasa con varias personas frente a la cámara?\n"
    "R: Hoy prioriza a la persona más cercana al centro del encuadre; la siguiente etapa filtrará por usuario dominante.\n\n"
    "5. ¿Cómo cierran la brecha hacia el espacio público real?\n"
    "R: Con la PCB de potencia para 25 A, acoples mecánicos de desacople seguro y firmware con auto-recuperación."
)

s10 = new_slide(notes_10)

title_header(s10, "De prototipo a pared completa", "Rúbrica: Revisión y Pasos (10%)", 10)

# Columna izquierda: Corregimos del Corte 1
rect(s10, Inches(0.8), Inches(1.8), Inches(5.7), Inches(4.3), fill=CARD, line=TEAL)
text_box(s10, Inches(1.1), Inches(2.0), Inches(5.1), Inches(0.5),
         "Corregimos del Corte 1", size=26, bold=True, color=TEAL)
text_box(s10, Inches(1.1), Inches(2.7), Inches(5.1), Inches(3.2),
         ["▸ Objetivos claros y delimitados",
          "",
          "▸ Mediciones reales: 682 lecturas, 0.9 A atorado",
          "",
          "▸ Comparativa con MIT y comercial"], size=21, color=WHITE)

# Columna derecha: Para el Corte 3
rect(s10, Inches(6.8), Inches(1.8), Inches(5.7), Inches(4.3), fill=CARD_HI, line=AMBER)
text_box(s10, Inches(7.1), Inches(2.0), Inches(5.1), Inches(0.5),
         "Para el Corte 3", size=26, bold=True, color=AMBER)
text_box(s10, Inches(7.1), Inches(2.6), Inches(5.1), Inches(1.8),
         ["▸ PCB de potencia definitiva (25 A)",
          "▸ Apagado automático por software",
          "▸ Colmena completa de 16 paneles"], size=20, color=WHITE, bold=True)
pic(s10, "PCB1.png", Inches(7.2), Inches(4.5), Inches(4.9), Inches(1.5), card=True, caption="Diseño PCB de potencia para 32 motores")

# Pie con enlace a GitHub y preguntas
rect(s10, Inches(0.8), Inches(6.25), Inches(11.7), Inches(0.7), fill=CARD)
text_box(s10, Inches(1.05), Inches(6.38), Inches(8.5), Inches(0.4),
         "github.com/PaolaCV14/IOT-SOFIA-2026", size=18, color=TEAL, bold=True)
text_box(s10, Inches(9.5), Inches(6.38), Inches(2.8), Inches(0.4),
         "¿Preguntas?", size=22, color=WHITE, bold=True, align=PP_ALIGN.RIGHT)

prs.save(OUT)
print("OK -> Presentación generada exitosamente en:", OUT, "| Diapositivas:", len(prs.slides))
