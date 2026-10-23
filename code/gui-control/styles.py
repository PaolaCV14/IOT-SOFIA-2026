"""
Estilos visuales (QSS) para la estación de control de SOFÍA.
Paleta morada y azulada moderna: Índigo profundo, azul pizarra (slate) y violeta sobrio.
Diseño de instrumentación de alta fidelidad, elegante, conservador y armónico.
"""

MODERN_DARK_THEME = """
/* Estilo base y tipografía nativa nítida sin warnings de Qt */
QWidget {
    background-color: #0D0F18;
    color: #E2E8F0;
    font-family: "Helvetica Neue", Arial, sans-serif;
    font-size: 12.5px;
}

/* Paneles contenedores con micro-radio técnico */
QFrame#card {
    background-color: #131722;
    border-radius: 4px;
    border: 1px solid #23283A;
    padding: 10px;
}

/* Agrupadores estructurados en azul pizarra */
QGroupBox {
    background-color: #131722;
    border: 1px solid #23283A;
    border-radius: 4px;
    margin-top: 20px;
    padding-top: 14px;
    font-weight: 600;
    font-size: 11.5px;
    color: #818CF8;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 10px;
    padding: 2px 8px;
    background-color: #0D0F18;
    color: #A5B4FC;
    border: 1px solid #2E3654;
    border-radius: 2px;
    font-weight: 700;
    font-size: 11px;
}

/* Botones con estilo táctil y armónico */
QPushButton {
    background-color: #1A1D2B;
    color: #E2E8F0;
    border: 1px solid #2B3147;
    border-radius: 3px;
    padding: 7px 14px;
    font-weight: 600;
    font-size: 12px;
}

QPushButton:hover {
    background-color: #23273A;
    border-color: #6366F1;
    color: #FFFFFF;
}

QPushButton:pressed {
    background-color: #141622;
}

/* Botón Iniciar (Índigo real / Azul-morado moderno de alta jerarquía) */
QPushButton#btn-start {
    background-color: #4F46E5;
    border: 1px solid #6366F1;
    color: #FFFFFF;
    font-weight: 700;
}

QPushButton#btn-start:hover {
    background-color: #5D54F5;
    border-color: #818CF8;
}

QPushButton#btn-start:pressed {
    background-color: #4338CA;
}

/* Botón Pausar / Reanudar (Azul acero técnico en sintonía con la paleta) */
QPushButton#btn-pause {
    background-color: #262D42;
    border: 1px solid #3E4968;
    color: #CBD5E1;
}

QPushButton#btn-pause:hover {
    background-color: #313A54;
    border-color: #6366F1;
    color: #FFFFFF;
}

QPushButton#btn-pause:pressed {
    background-color: #1E2333;
}

/* Botón Detener (Ciruela / Vino apagado muy sobrio, sin rojos discordantes) */
QPushButton#btn-stop {
    background-color: #381E32;
    border: 1px solid #572A4E;
    color: #E9D5FF;
}

QPushButton#btn-stop:hover {
    background-color: #4A2643;
    border-color: #818CF8;
    color: #FFFFFF;
}

QPushButton#btn-stop:pressed {
    background-color: #261523;
}

/* Sliders de articulaciones (Guía lineal índigo de precisión) */
QSlider::groove:horizontal {
    height: 4px;
    background: #1F2436;
    border-radius: 2px;
}

QSlider::sub-page:horizontal {
    background: #6366F1;
    border-radius: 2px;
}

QSlider::handle:horizontal {
    background: #F8FAFC;
    border: 1px solid #4F46E5;
    width: 10px;
    margin-top: -6px;
    margin-bottom: -6px;
    border-radius: 2px;
}

QSlider::handle:horizontal:hover {
    background: #A5B4FC;
    border-color: #818CF8;
}

/* Entradas y listas desplegables */
QComboBox {
    background-color: #1A1D2B;
    border: 1px solid #2B3147;
    border-radius: 3px;
    padding: 5px 8px;
    color: #F8FAFC;
    font-size: 12px;
}

QComboBox:hover {
    border-color: #6366F1;
}

QComboBox::drop-down {
    border: none;
}

/* Terminal de logs / Consola técnica */
QTextEdit#logTerminal {
    background-color: #080A10;
    border: 1px solid #1F2436;
    border-radius: 3px;
    font-family: "SF Mono", "Menlo", "Monaco", "Consolas", monospace;
    font-size: 11px;
    color: #CBD5E1;
    padding: 6px;
}

/* Badges de estado técnicos */
QLabel#badge {
    background-color: #1A1D2B;
    color: #94A3B8;
    border: 1px solid #2B3147;
    border-radius: 3px;
    padding: 3px 8px;
    font-weight: 600;
    font-size: 11.5px;
}

QLabel#badge-active {
    background-color: #1E1B4B;
    color: #A5B4FC;
    border: 1px solid #4F46E5;
    border-radius: 3px;
    padding: 3px 8px;
    font-weight: 700;
    font-size: 11.5px;
}
"""
