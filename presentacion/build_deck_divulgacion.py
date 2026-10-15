"""Versión de DIVULGACIÓN de la presentación de SOFIA (público general: otros LabDST,
estudiantes y profesores de otras áreas). Reutiliza los helpers de build_deck.py.
Uso:  python3 build_deck_divulgacion.py
"""
import os

_here = os.path.dirname(os.path.abspath(__file__))
_src = open(os.path.join(_here, "build_deck.py"), encoding="utf-8").read()
exec(_src.split("# 1. PORTADA")[0])  # solo paleta + helpers + presentación vacía

OUT = os.path.join(HERE, "SOFIA_LabDST_Presentacion_Divulgacion.pptx")


def circle_num(s, x, y, d, label, color):
    c = s.shapes.add_shape(MSO_SHAPE.OVAL, x, y, d, d)
    c.fill.solid()
    c.fill.fore_color.rgb = color
    c.line.fill.background()
    c.shadow.inherit = False
    tf = c.text_frame
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    r = p.add_run()
    r.text = label
    r.font.size = Pt(26)
    r.font.bold = True
    r.font.color.rgb = BG
    r.font.name = FONT


def big_quote(s, x, y, w, h, content, size=26, color=WHITE, line=TEAL):
    rect(s, x, y, w, h, fill=CARD, line=line)
    text(s, x + Inches(0.3), y, w - Inches(0.6), h, content, size=size, bold=True,
         color=color, anchor=MSO_ANCHOR.MIDDLE)


# =====================================================================
# 1. PORTADA
# =====================================================================
s = new_slide(
    "(10 s) Hola, somos el Equipo 1. Les vamos a presentar SOFIA: una pared de robots que responde "
    "a los gestos de tu mano. Y les vamos a contar un problema curioso que descubrimos: "
    "los motores pueden calentarse mucho.")
rect(s, Inches(8.4), 0, Inches(4.93), H, fill=CARD, shape=MSO_SHAPE.RECTANGLE)
rect(s, 0, 0, Inches(0.18), H, fill=TEAL, shape=MSO_SHAPE.RECTANGLE)
pic(s, "sofia_solid.png", Inches(8.9), Inches(0.7), Inches(3.9), Inches(3.6))
pic(s, "modulo_fisico.png", Inches(8.9), Inches(4.5), Inches(3.9), Inches(2.1))
text(s, Inches(0.7), Inches(0.7), Inches(7), Inches(0.4), "LABDST · ITESO · OTOÑO 2026",
     size=14, color=TEAL, bold=True)
text(s, Inches(0.7), Inches(1.3), Inches(7.5), Inches(1.3), "SOFIA", size=84, bold=True)
text(s, Inches(0.7), Inches(2.85), Inches(7.4), Inches(1.4),
     "Una pared robótica que responde a los gestos de tu mano", size=28, color=WHITE)
rect(s, Inches(0.75), Inches(4.3), Inches(1.2), Inches(0.06), fill=ORANGE, shape=MSO_SHAPE.RECTANGLE)
text(s, Inches(0.7), Inches(4.5), Inches(7.5), Inches(0.4), "EQUIPO 1", size=14, color=ORANGE, bold=True)
text(s, Inches(0.7), Inches(4.85), Inches(7.5), Inches(1.6),
     ["Paola Covarrubias · Lizeth Méndez", "Juan Bernardo Orozco · Karen Sánchez", "Alan Fuentes"],
     size=19, color=WHITE)
text(s, Inches(0.7), Inches(6.5), Inches(7.5), Inches(0.5),
     "Con: Jorge A. Lizarraga · Graciela Baca · Luis E. González · Luis F. Luque-Vega",
     size=11.5, color=MUTED)

# =====================================================================
# 2. ¿QUÉ ES SOFIA?
# =====================================================================
s = new_slide(
    "(40 s) Imaginen una pared hecha de 16 piezas hexagonales, como un panal de abejas. Cada pieza puede "
    "inclinarse y girar. Una cámara ve tu mano y las piezas se mueven para responderte: saludan, hacen un "
    "corazón, juegan piedra papel o tijera. Es arte, tecnología y robótica juntos.")
header(s, "¿Qué es SOFIA?", "Imagina una pared que te responde", 2)
big_quote(s, Inches(0.6), Inches(1.7), Inches(6.2), Inches(1.5),
          "Una pared de 16 piezas que se mueven cuando tú mueves la mano.", size=24)
stat(s, Inches(0.6), Inches(3.5), Inches(1.95), Inches(1.5), "16", "piezas en forma de panal")
stat(s, Inches(2.7), Inches(3.5), Inches(1.95), Inches(1.5), "2", "movimientos por pieza", ORANGE)
stat(s, Inches(4.8), Inches(3.5), Inches(2.0), Inches(1.5), "32", "motores pequeños")
bullets(s, Inches(0.6), Inches(5.3), Inches(6.3), Inches(1.6), [
    "Ya existen paredes que se mueven (como inFORM, del MIT).",
    ("Lo nuestro: ", "que sean seguras y no se quemen."),
], size=17, gap=8)
pic(s, "fig_sim_3.png", Inches(7.2), Inches(1.7), Inches(5.5), Inches(2.9), caption="Simulación: las 16 piezas siguen un punto")
pic(s, "modulo_fisico.png", Inches(7.2), Inches(4.95), Inches(5.5), Inches(1.9), caption="Nuestro prototipo real")

# =====================================================================
# 3. CÓMO FUNCIONA EN 3 PASOS
# =====================================================================
s = new_slide(
    "(60 s) Funciona en tres pasos, como una persona. Uno: ve, una cámara mira tu mano. Dos: piensa, "
    "una computadora encuentra 21 puntos en tu mano y decide qué gesto es. Tres: se mueve, manda órdenes por "
    "Bluetooth a una placa que mueve los motores. Ojos, cerebro y músculos.")
header(s, "¿Cómo funciona? En 3 pasos", "Ojos · cerebro · músculos", 3)
steps = [
    ("1", "VE", "Una cámara mira tu mano en tiempo real.", "cámara web · 30 imágenes por segundo", TEAL),
    ("2", "PIENSA", "La computadora ubica 21 puntos de tu mano y decide qué gesto haces.",
     "Python + MediaPipe (de Google)", ORANGE),
    ("3", "SE MUEVE", "Manda órdenes por Bluetooth a una placa que mueve los motores.",
     "ESP32 + 32 servomotores", TEAL),
]
for i, (n, t, d, tech, c) in enumerate(steps):
    x = Inches(0.6 + i * 4.15)
    rect(s, x, Inches(1.8), Inches(3.8), Inches(3.9), fill=CARD, line=c)
    circle_num(s, x + Inches(0.3), Inches(2.0), Inches(0.85), n, c)
    text(s, x + Inches(1.3), Inches(2.0), Inches(2.4), Inches(0.85), t, size=30, bold=True, color=c,
         anchor=MSO_ANCHOR.MIDDLE)
    text(s, x + Inches(0.3), Inches(3.1), Inches(3.3), Inches(1.5), d, size=19)
    text(s, x + Inches(0.3), Inches(4.9), Inches(3.3), Inches(0.7), tech, size=12.5, color=MUTED, italic=True)
    if i < 2:
        arrow(s, x + Inches(3.8), Inches(3.75), x + Inches(4.15), Inches(3.75), ORANGE)
text(s, Inches(0.6), Inches(6.05), Inches(12.1), Inches(0.8),
     "Es lo mismo que hace tu cuerpo cuando atrapas una pelota.", size=20, color=ORANGE,
     bold=True, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)

# =====================================================================
# 4. POR DENTRO
# =====================================================================
s = new_slide(
    "(40 s) Por dentro: cada pieza se diseñó en 3D y se imprimió. Tiene dos motores pequeños, llamados servos, "
    "los mismos que mueven un carrito de control remoto: uno la inclina y otro la gira. Todo lo controla una "
    "placa llamada ESP32, y ya mandamos hacer una tarjeta de circuitos propia.")
header(s, "Por dentro de una pieza", "Hardware", 4)
pic(s, "sofia_solid.png", Inches(0.6), Inches(1.7), Inches(3.4), Inches(3.4), caption="La pieza armada")
pic(s, "sofia_exploded.png", Inches(4.2), Inches(1.7), Inches(2.6), Inches(3.4), caption="Sus partes, separadas")
cards = [("Dos motores (servos)", "Como los de un carrito RC: uno inclina, otro gira.", TEAL),
         ("Una placa ESP32", "El 'cerebrito' que recibe órdenes y mueve los motores.", ORANGE),
         ("Impresa en 3D", "Cuerpo de plástico PLA, hecho en nuestro laboratorio.", TEAL)]
for i, (t, d, c) in enumerate(cards):
    y = Inches(1.7 + i * 1.2)
    rect(s, Inches(7.2), y, Inches(5.5), Inches(1.05), fill=CARD, line=c)
    text(s, Inches(7.4), y + Inches(0.05), Inches(5.2), Inches(0.4), t, size=18, bold=True, color=c)
    text(s, Inches(7.4), y + Inches(0.48), Inches(5.2), Inches(0.55), d, size=14, color=MUTED)
pic(s, "sofia_pcb_layout.png", Inches(7.2), Inches(5.4), Inches(2.6), Inches(1.5), caption="Nuestra tarjeta de circuitos")
text(s, Inches(10.0), Inches(5.4), Inches(2.7), Inches(1.5),
     "Ya la mandamos a fabricar. Falta probarla.", size=15, color=ORANGE, bold=True, anchor=MSO_ANCHOR.MIDDLE)
text(s, Inches(0.6), Inches(5.45), Inches(6.3), Inches(1.4),
     "Cada pieza = 2 motores. 16 piezas = 32 motores moviéndose coordinados.", size=17, color=WHITE)

# =====================================================================
# 5. CÓMO ENTIENDE GESTOS
# =====================================================================
s = new_slide(
    "(50 s) ¿Cómo entiende tu mano? La computadora encuentra 21 puntos: las puntas de los dedos, "
    "los nudillos, la muñeca. Con eso sabe si tu mano está abierta o cerrada. Ya reconoce el saludo, el corazón con "
    "dos manos y piedra, papel o tijera. Esta es la pantalla de control que usamos.")
header(s, "¿Cómo entiende tu mano?", "Visión por computadora", 5)
pic(s, "sofia_gui.png", Inches(0.6), Inches(1.7), Inches(7.0), Inches(4.6), caption="Nuestra pantalla de control")
text(s, Inches(8.0), Inches(1.7), Inches(4.7), Inches(0.5), "Gestos que ya reconoce", size=21, bold=True, color=TEAL)
for i, (g, d) in enumerate([("Saludo", "mueves la mano de lado a lado"),
                            ("Corazón", "juntas las dos manos"),
                            ("Piedra, papel o tijera", "juegas con las dos manos"),
                            ("Palma abierta · puño · victoria", "poses simples")]):
    y = Inches(2.35 + i * 1.05)
    rect(s, Inches(8.0), y, Inches(4.7), Inches(0.9), fill=CARD)
    text(s, Inches(8.15), y + Inches(0.03), Inches(4.4), Inches(0.4), g, size=16.5, bold=True)
    text(s, Inches(8.15), y + Inches(0.45), Inches(4.4), Inches(0.4), d, size=13.5, color=MUTED)
text(s, Inches(0.6), Inches(6.4), Inches(12.1), Inches(0.5),
     "Detecta 21 puntos en cada mano, sin necesitar una computadora especial.", size=16, color=ORANGE, italic=True)

# =====================================================================
# 6. SIMULACIÓN
# =====================================================================
s = new_slide(
    "(35 s) Antes de construir las 16 piezas, hicimos una simulación en la computadora con Unity, el programa "
    "de videojuegos. Ahí vemos cómo las 16 piezas se orientan hacia un punto que se mueve, como girasoles "
    "siguiendo al sol. Así probamos la idea sin gastar en piezas.")
header(s, "Primero lo probamos en la compu", "Simulación", 6)
for i, nm in enumerate(["fig_sim_1.png", "fig_sim_2.png", "fig_sim_3.png", "fig_sim_4.png", "fig_sim_5.png", "fig_sim_6.png"]):
    x = Inches(0.6 + (i % 3) * 4.15)
    y = Inches(1.7 + (i // 3) * 2.3)
    pic(s, nm, x, y, Inches(3.95), Inches(2.15))
big_quote(s, Inches(0.6), Inches(6.35), Inches(12.1), Inches(0.6),
          "Como girasoles: las 16 piezas siguen un punto que se mueve.", size=19, line=ORANGE)

# =====================================================================
# 7. EL PROBLEMA ESCONDIDO
# =====================================================================
s = new_slide(
    "(50 s) Aquí viene el problema. Un motor de estos recibe la orden 've a este ángulo'. Pero ¿qué pasa si algo "
    "lo traba? Es como empujar una puerta que está atorada: sigues haciendo fuerza y te cansas. El motor hace "
    "lo mismo: jala corriente al máximo y se calienta, como tu celular cuando juega algo pesado. Con 32 motores "
    "pegados, eso es un riesgo. Nuestra pregunta: ¿cuánto tiempo aguanta?")
header(s, "El problema escondido", "¿Qué pasa si un motor se atora?", 7)
rect(s, Inches(0.6), Inches(1.75), Inches(5.9), Inches(2.5), fill=CARD, line=ORANGE)
text(s, Inches(0.85), Inches(1.85), Inches(5.4), Inches(0.5), "Es como empujar una puerta atorada", size=21, bold=True, color=ORANGE)
text(s, Inches(0.85), Inches(2.45), Inches(5.4), Inches(1.7),
     "Sigues haciendo fuerza… y te cansas. El motor hace lo mismo: no llega a su posición, "
     "sigue empujando y se calienta.", size=17.5)
rect(s, Inches(6.8), Inches(1.75), Inches(5.9), Inches(2.5), fill=CARD, line=RED)
text(s, Inches(7.05), Inches(1.85), Inches(5.4), Inches(0.5), "Como un celular jugando algo pesado", size=21, bold=True, color=RED)
text(s, Inches(7.05), Inches(2.45), Inches(5.4), Inches(1.7),
     "Con 32 motores pegados en una pared, el calor se acumula y puede derretir el plástico.", size=17.5)
big_quote(s, Inches(0.6), Inches(4.65), Inches(12.1), Inches(1.5),
          "Nuestra pregunta: si un motor se atora, ¿cuánto tiempo puede aguantar antes de calentarse demasiado?",
          size=24)
text(s, Inches(0.6), Inches(6.35), Inches(12.1), Inches(0.5),
     "Por eso, además de mover la pared, medimos qué pasa con los motores.", size=16, color=MUTED,
     align=PP_ALIGN.CENTER, italic=True)

# =====================================================================
# 8. LO QUE MEDIMOS
# =====================================================================
s = new_slide(
    "(55 s) Entonces lo medimos. Trabamos un motor a propósito y le pusimos un sensor de temperatura. "
    "La gráfica sube casi en línea recta: unos 0.2 grados cada segundo. Llegó a 70 grados. El plástico "
    "empieza a ablandarse como a los 60. A ese ritmo, en unos tres minutos y medio se pasa de lo seguro. "
    "No es mucho tiempo.")
header(s, "Lo que medimos: el calor sube rápido", "Experimento", 8)
pic(s, "fig_characterization_6panels.png", Inches(0.6), Inches(1.7), Inches(8.2), Inches(4.6),
    caption="Trabamos un motor a propósito y medimos todo")
stat(s, Inches(9.1), Inches(1.7), Inches(3.6), Inches(1.5), "0.2 °C", "sube cada segundo", ORANGE)
stat(s, Inches(9.1), Inches(3.4), Inches(3.6), Inches(1.5), "70 °C", "temperatura máxima alcanzada", RED)
stat(s, Inches(9.1), Inches(5.1), Inches(3.6), Inches(1.5), "≈ 3.5 min", "para llegar a zona de peligro (65 °C)", ORANGE)
text(s, Inches(0.6), Inches(6.45), Inches(8.2), Inches(0.5),
     "El plástico de las piezas empieza a ablandarse alrededor de los 60 °C.", size=14.5, color=MUTED, italic=True)

# =====================================================================
# 9. SORPRESA: ¿BANG-BANG?
# =====================================================================
s = new_slide(
    "(55 s) Nos preguntamos cómo trabaja el motor por dentro. Hay dos formas: como un interruptor, "
    "encendido o apagado, a toda potencia; o como el acelerador de un coche, que da más o menos según lo que "
    "necesita. Medimos cuánta corriente gasta en tres casos: poquito error, mucho error y atorado. "
    "Resultado: es como un acelerador. Gasta poquito normalmente y solo se pone al máximo cuando se atora.")
header(s, "¿Interruptor o acelerador?", "Cómo piensa el motor por dentro", 9)
for i, (t, d, c) in enumerate([("Interruptor", "Todo o nada: a toda potencia o apagado.", RED),
                               ("Acelerador", "Da más o menos según lo que necesita.", TEAL)]):
    x = Inches(0.6 + i * 6.15)
    rect(s, x, Inches(1.7), Inches(5.95), Inches(1.0), fill=CARD, line=c)
    text(s, x + Inches(0.2), Inches(1.72), Inches(5.6), Inches(0.45), t, size=20, bold=True, color=c)
    text(s, x + Inches(0.2), Inches(2.17), Inches(5.6), Inches(0.5), d, size=14.5, color=MUTED)
pic(s, "fig_current_characterization.png", Inches(0.6), Inches(2.95), Inches(12.1), Inches(2.9),
    caption="Corriente del motor: (a) error pequeño · (b) error grande · (c) atorado")
big_quote(s, Inches(0.6), Inches(6.2), Inches(12.1), Inches(0.75),
          "Resultado: es un ACELERADOR. Solo se pone al máximo cuando se atora.", size=21, line=ORANGE)

# =====================================================================
# 10. YA FUNCIONA
# =====================================================================
s = new_slide(
    "(45 s) Y lo mejor: ya funciona. Aquí está nuestro módulo real. Se conecta por Bluetooth, sigue la mano, "
    "y cuando haces el gesto de saludo, ejecuta una rutina de saludo. Estas son tres fotos de ese movimiento. "
    "Aún nos falta medir qué tan preciso y rápido es, eso es lo siguiente.")
header(s, "¡Ya funciona! El prototipo saluda", "Prototipo real", 10)
pic(s, "modulo_fisico.png", Inches(0.6), Inches(1.7), Inches(4.6), Inches(2.4), caption="Nuestro módulo real")
for i, (nm, cap) in enumerate([("sofia_saludo1.png", "Inicio"), ("sofia_saludo2.png", "A la mitad"), ("sofia_saludo3.png", "Final")]):
    pic(s, nm, Inches(5.5 + i * 2.45), Inches(1.7), Inches(2.35), Inches(1.5), caption=f"Saludo · {cap}")
checks = ["Se conecta por Bluetooth", "Sigue el movimiento de tu mano", "Hace el saludo y el corazón",
          "Se detiene y se reanuda sin enredarse", "Se apaga y desconecta bien"]
for i, c in enumerate(checks):
    y = Inches(4.5 + (i % 3) * 0.75)
    x = Inches(0.6 + (i // 3) * 6.15)
    rect(s, x, y, Inches(5.95), Inches(0.65), fill=CARD)
    text(s, x + Inches(0.1), y, Inches(0.5), Inches(0.65), "✓", size=22, bold=True, color=TEAL, anchor=MSO_ANCHOR.MIDDLE)
    text(s, x + Inches(0.6), y, Inches(5.3), Inches(0.65), c, size=17, anchor=MSO_ANCHOR.MIDDLE)
text(s, Inches(5.5), Inches(3.75), Inches(7.2), Inches(0.6),
     "Falta medir qué tan preciso y rápido es.", size=14.5, color=ORANGE, italic=True)

# =====================================================================
# 11. PROTECCIÓN Y SIGUIENTES PASOS
# =====================================================================
s = new_slide(
    "(45 s) Con lo que medimos, ponemos un guardián: si un motor lleva 15 segundos atorado, se apaga solo ese "
    "motor, así queda libre y se enfría. Y lo que sigue: medir qué tan rápido y preciso sigue tu mano, "
    "probar la tarjeta de circuitos y construir las 16 piezas.")
header(s, "Un guardián y lo que sigue", "Protección y futuro", 11)
rect(s, Inches(0.6), Inches(1.75), Inches(5.95), Inches(5.0), fill=CARD, line=RED)
text(s, Inches(0.9), Inches(1.9), Inches(5.4), Inches(0.5), "El guardián del motor", size=24, bold=True, color=RED)
bullets(s, Inches(0.9), Inches(2.6), Inches(5.4), Inches(4.0), [
    "Vigila cuánto tiempo lleva atorado cada motor.",
    "Si pasan 15 segundos, apaga solo ese motor.",
    "El motor queda libre y se enfría.",
    "Nunca llega a la zona de peligro.",
], size=18, gap=14, dot=RED)
rect(s, Inches(6.75), Inches(1.75), Inches(5.95), Inches(5.0), fill=CARD, line=TEAL)
text(s, Inches(7.05), Inches(1.9), Inches(5.4), Inches(0.5), "Lo que sigue", size=24, bold=True, color=TEAL)
bullets(s, Inches(7.05), Inches(2.6), Inches(5.4), Inches(4.0), [
    "Medir qué tan rápido y preciso sigue tu mano.",
    "Probar nuestra tarjeta de circuitos.",
    "Construir las 16 piezas completas.",
    "Que el movimiento sea aún más suave.",
], size=18, gap=14)

# =====================================================================
# 12. IDEAS PARA LLEVARTE
# =====================================================================
s = new_slide(
    "(30 s) Si se quedan con tres ideas: una, SOFIA es una pared que responde a gestos usando una cámara; "
    "dos, descubrimos que un motor atorado se calienta muy rápido, y por eso lo protegemos; "
    "tres, el motor es como un acelerador, no un interruptor. Y ya hay un prototipo que saluda.")
header(s, "3 ideas para llevarte", "Resumen", 12)
takeaways = [
    ("1", "Una pared que responde", "SOFIA ve tu mano con una cámara y mueve sus 16 piezas.", TEAL),
    ("2", "Un motor atorado se calienta rápido", "Subió 0.2 °C por segundo. Por eso lo protegemos con un guardián.", ORANGE),
    ("3", "El motor es como un acelerador", "Solo se pone al máximo cuando se atora.", TEAL),
]
for i, (n, t, d, c) in enumerate(takeaways):
    y = Inches(1.75 + i * 1.7)
    rect(s, Inches(0.6), y, Inches(12.1), Inches(1.5), fill=CARD, line=c)
    circle_num(s, Inches(0.9), y + Inches(0.3), Inches(0.9), n, c)
    text(s, Inches(2.1), y + Inches(0.12), Inches(10.4), Inches(0.55), t, size=24, bold=True, color=c)
    text(s, Inches(2.1), y + Inches(0.75), Inches(10.4), Inches(0.7), d, size=17.5)
text(s, Inches(0.6), Inches(6.85), Inches(12.1), Inches(0.4),
     "Y ya tenemos un prototipo físico que saluda.", size=16, color=ORANGE, bold=True, align=PP_ALIGN.CENTER)

# =====================================================================
# 13. GRACIAS
# =====================================================================
s = new_slide("Cierre. Pregunta para el público: ¿qué gesto le enseñarías a SOFIA? Abrir a preguntas.")
rect(s, 0, 0, Inches(0.18), H, fill=TEAL, shape=MSO_SHAPE.RECTANGLE)
pic(s, "sofia_saludo2.png", Inches(8.3), Inches(1.4), Inches(4.5), Inches(2.6))
pic(s, "fig_sim_3.png", Inches(8.3), Inches(4.2), Inches(4.5), Inches(2.4))
text(s, Inches(0.8), Inches(1.5), Inches(7), Inches(1.4), "¡Gracias!", size=76, bold=True)
text(s, Inches(0.8), Inches(3.0), Inches(7.2), Inches(1.4), "¿Qué gesto le enseñarías a SOFIA?",
     size=34, color=TEAL, bold=True)
rect(s, Inches(0.85), Inches(4.7), Inches(1.2), Inches(0.06), fill=ORANGE, shape=MSO_SHAPE.RECTANGLE)
text(s, Inches(0.8), Inches(4.95), Inches(7), Inches(1.6), [
    "SOFIA · Equipo 1 · LabDST · ITESO",
    "github.com/PaolaCV14/IOT-SOFIA-2026"], size=17, color=MUTED)

prs.save(OUT)
print("OK ->", OUT, "| slides:", len(prs.slides))
