"""
==============================================================
ESTILOS VISUALES (QSS) - ESTACIÓN DE CONTROL SOFIA
Tema oscuro moderno con acentos cian/menta y diseño limpio
==============================================================
"""

MODERN_DARK_THEME = """
QWidget {
    background-color: #121418;
    color: #E2E8F0;
    font-family: 'Segoe UI', 'SF Pro Text', 'Helvetica Neue', Arial, sans-serif;
    font-size: 13px;
}

/* Paneles y Tarjetas */
QFrame#card {
    background-color: #1A1D24;
    border-radius: 10px;
    border: 1px solid #282D37;
    padding: 12px;
}

QGroupBox {
    background-color: #1A1D24;
    border: 1px solid #282D37;
    border-radius: 8px;
    margin-top: 22px;
    padding-top: 15px;
    font-weight: 600;
    color: #38BDF8;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 12px;
    padding: 2px 8px;
    background-color: #121418;
    border-radius: 4px;
}

/* Botones */
QPushButton {
    background-color: #262B36;
    color: #F8FAFC;
    border: 1px solid #3B4252;
    border-radius: 6px;
    padding: 8px 16px;
    font-weight: 600;
}

QPushButton:hover {
    background-color: #323946;
    border-color: #38BDF8;
}

QPushButton:pressed {
    background-color: #1E222A;
}

QPushButton#btn-start {
    background-color: #0284C7;
    border: 1px solid #38BDF8;
}

QPushButton#btn-start:hover {
    background-color: #0369A1;
}

QPushButton#btn-stop {
    background-color: #BE123C;
    border: 1px solid #FB7185;
}

QPushButton#btn-stop:hover {
    background-color: #9F1239;
}

/* Sliders */
QSlider::groove:horizontal {
    height: 6px;
    background: #282D37;
    border-radius: 3px;
}

QSlider::sub-page:horizontal {
    background: #38BDF8;
    border-radius: 3px;
}

QSlider::handle:horizontal {
    background: #F8FAFC;
    border: 2px solid #0284C7;
    width: 16px;
    margin-top: -5px;
    margin-bottom: -5px;
    border-radius: 8px;
}

QSlider::handle:horizontal:hover {
    background: #38BDF8;
}

/* ComboBox y Inputs */
QComboBox {
    background-color: #20242D;
    border: 1px solid #2F3644;
    border-radius: 6px;
    padding: 5px 10px;
    color: #F8FAFC;
}

QComboBox::drop-down {
    border: none;
}

/* Terminal / Log */
QTextEdit#logTerminal {
    background-color: #0D0F12;
    border: 1px solid #20252E;
    border-radius: 6px;
    font-family: 'Consolas', 'Courier New', monospace;
    font-size: 11px;
    color: #34D399;
}

/* Indicadores de Estado y Badges */
QLabel#badge {
    background-color: #20242D;
    color: #94A3B8;
    border: 1px solid #2E3543;
    border-radius: 4px;
    padding: 4px 8px;
    font-weight: 600;
}

QLabel#badge-active {
    background-color: #064E3B;
    color: #34D399;
    border: 1px solid #059669;
    border-radius: 4px;
    padding: 4px 8px;
    font-weight: 600;
}
"""
