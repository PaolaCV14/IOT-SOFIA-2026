"""
==============================================================
ESTACIÓN DE CONTROL Y MONITOREO SOFIA
Interfaz gráfica integrada (PySide6) para Tracking de Visión + Control
==============================================================
"""

import sys
import os
import socket
from PySide6.QtCore import Qt, Slot
from PySide6.QtGui import QPixmap, QIcon
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QPushButton,
    QVBoxLayout, QHBoxLayout, QGridLayout, QGroupBox, QSlider,
    QComboBox, QTextEdit, QFrame
)

# Ajuste de path para importar módulos de tracking-vision
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
TRACKING_DIR = os.path.abspath(os.path.join(CURRENT_DIR, "..", "tracking-vision"))
if TRACKING_DIR not in sys.path:
    sys.path.append(TRACKING_DIR)

from vision_worker import VisionWorker
from styles import MODERN_DARK_THEME


class SofiaDashboard(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SOFÍA 2026 - Centro de Control y Visión 3D")
        self.resize(1180, 720)
        self.setStyleSheet(MODERN_DARK_THEME)

        # Configuración de Sockets para Unity / Hardware
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.target_ip = "127.0.0.1"
        self.target_port = 5005

        # Rutas de modelos
        self.models_dir = os.path.join(TRACKING_DIR, "models")
        self.worker = None

        self._init_ui()

    def _init_ui(self):
        main_widget = QWidget()
        main_layout = QHBoxLayout(main_widget)
        main_layout.setSpacing(16)
        main_layout.setContentsMargins(16, 16, 16, 16)
        self.setCentralWidget(main_widget)

        # -------------------------------------------------------------
        # PANEL IZQUIERDO: VISUALIZADOR DE VIDEO (STREAM EN TIEMPO REAL)
        # -------------------------------------------------------------
        left_panel = QFrame()
        left_panel.setObjectName("card")
        left_layout = QVBoxLayout(left_panel)

        # Encabezado Video
        video_header = QHBoxLayout()
        title_cam = QLabel("🎥 Transmisión en Tiempo Real")
        title_cam.setStyleSheet("font-size: 15px; font-weight: bold; color: #F8FAFC;")
        self.lbl_fps_badge = QLabel("FPS: --")
        self.lbl_fps_badge.setObjectName("badge")
        self.lbl_latency_badge = QLabel("Latencia: -- ms")
        self.lbl_latency_badge.setObjectName("badge")

        video_header.addWidget(title_cam)
        video_header.addStretch()
        video_header.addWidget(self.lbl_fps_badge)
        video_header.addWidget(self.lbl_latency_badge)
        left_layout.addLayout(video_header)

        # Visor de la cámara
        self.video_view = QLabel()
        self.video_view.setAlignment(Qt.AlignCenter)
        self.video_view.setMinimumSize(640, 440)
        self.video_view.setStyleSheet(
            "background-color: #0A0C0F; border: 2px dashed #2A303C; border-radius: 8px;"
        )
        self.video_view.setText("Cámara no iniciada.\nPresiona 'Iniciar Sistema' para comenzar.")
        left_layout.addWidget(self.video_view, stretch=1)

        # Barra de Estado Inferior de Gestos
        gesture_box = QHBoxLayout()
        lbl_g_title = QLabel("Gesto Detectado:")
        lbl_g_title.setStyleSheet("font-weight: 600; color: #94A3B8;")
        self.lbl_gesture_val = QLabel("NINGUNO")
        self.lbl_gesture_val.setObjectName("badge")
        self.lbl_gesture_val.setStyleSheet("font-size: 14px; font-weight: bold; color: #38BDF8; padding: 6px 12px;")

        gesture_box.addWidget(lbl_g_title)
        gesture_box.addWidget(self.lbl_gesture_val)
        gesture_box.addStretch()
        left_layout.addLayout(gesture_box)

        main_layout.addWidget(left_panel, stretch=6)

        # -------------------------------------------------------------
        # PANEL DERECHO: CONTROLES, TELEMETRÍA Y LOGS
        # -------------------------------------------------------------
        right_panel = QFrame()
        right_panel.setObjectName("card")
        right_layout = QVBoxLayout(right_panel)
        right_layout.setSpacing(12)

        # 1. Operación y Dispositivos
        group_op = QGroupBox("Control de Ejecución")
        op_layout = QVBoxLayout(group_op)

        btn_row = QHBoxLayout()
        self.btn_start = QPushButton("▶ Iniciar Sistema")
        self.btn_start.setObjectName("btn-start")
        self.btn_start.clicked.connect(self.start_vision)

        self.btn_stop = QPushButton("⏹ Detener")
        self.btn_stop.setObjectName("btn-stop")
        self.btn_stop.setEnabled(False)
        self.btn_stop.clicked.connect(self.stop_vision)

        btn_row.addWidget(self.btn_start)
        btn_row.addWidget(self.btn_stop)
        op_layout.addLayout(btn_row)

        combo_row = QHBoxLayout()
        combo_row.addWidget(QLabel("Modo:"))
        self.combo_mode = QComboBox()
        self.combo_mode.addItems(["Seguimiento Automático 3D", "Control Manual", "Calibración", "Reposo"])
        combo_row.addWidget(self.combo_mode)
        op_layout.addLayout(combo_row)
        right_layout.addWidget(group_op)

        # 2. Telemetría de Servomotores (q1, q2)
        group_angles = QGroupBox("Orientación Articular (Servos)")
        angles_layout = QGridLayout(group_angles)

        angles_layout.addWidget(QLabel("q1 (Yaw / Horizontal):"), 0, 0)
        self.lbl_q1_val = QLabel("0.0°")
        self.lbl_q1_val.setStyleSheet("font-weight: bold; color: #38BDF8;")
        angles_layout.addWidget(self.lbl_q1_val, 0, 1)

        self.slider_q1 = QSlider(Qt.Horizontal)
        self.slider_q1.setRange(-90, 90)
        self.slider_q1.setValue(0)
        self.slider_q1.valueChanged.connect(self.on_slider_manual)
        angles_layout.addWidget(self.slider_q1, 1, 0, 1, 2)

        angles_layout.addWidget(QLabel("q2 (Pitch / Vertical):"), 2, 0)
        self.lbl_q2_val = QLabel("0.0°")
        self.lbl_q2_val.setStyleSheet("font-weight: bold; color: #38BDF8;")
        angles_layout.addWidget(self.lbl_q2_val, 2, 1)

        self.slider_q2 = QSlider(Qt.Horizontal)
        self.slider_q2.setRange(-90, 90)
        self.slider_q2.setValue(0)
        self.slider_q2.valueChanged.connect(self.on_slider_manual)
        angles_layout.addWidget(self.slider_q2, 3, 0, 1, 2)

        right_layout.addWidget(group_angles)

        # 3. Consola de Telemetría y Eventos
        group_log = QGroupBox("Terminal de Eventos y Telemetría")
        log_layout = QVBoxLayout(group_log)
        self.log_terminal = QTextEdit()
        self.log_terminal.setObjectName("logTerminal")
        self.log_terminal.setReadOnly(True)
        log_layout.addWidget(self.log_terminal)
        right_layout.addWidget(group_log, stretch=1)

        main_layout.addWidget(right_panel, stretch=4)

        self.log_event("Sistema inicializado. Listo para operar.")

    def log_event(self, text):
        """Muestra mensajes con formato en la terminal de la GUI."""
        self.log_terminal.append(f"> {text}")

    @Slot()
    def start_vision(self):
        """Inicia el worker en segundo plano para procesar la cámara."""
        self.worker = VisionWorker(camera_id=0, models_dir=self.models_dir)
        self.worker.frame_ready.connect(self.update_video_frame)
        self.worker.metrics_ready.connect(self.update_metrics)
        self.worker.angles_ready.connect(self.update_angles)
        self.worker.status_message.connect(self.log_event)

        self.worker.start()
        self.btn_start.setEnabled(False)
        self.btn_stop.setEnabled(True)

    @Slot()
    def stop_vision(self):
        """Detiene el worker de cámara."""
        if self.worker:
            self.worker.stop()
            self.worker = None
        self.btn_start.setEnabled(True)
        self.btn_stop.setEnabled(False)
        self.video_view.setText("Sistema detenido.")

    @Slot(QPixmap)
    def update_video_frame(self, q_img):
        """Renderiza el cuadro procesado en la pantalla."""
        pixmap = QPixmap.fromImage(q_img)
        scaled_pixmap = pixmap.scaled(
            self.video_view.size(),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )
        self.video_view.setPixmap(scaled_pixmap)

    @Slot(float, float, str)
    def update_metrics(self, fps, latency, gesto):
        """Actualiza etiquetas de rendimiento y gestos."""
        self.lbl_fps_badge.setText(f"FPS: {fps:.1f}")
        self.lbl_latency_badge.setText(f"Lat: {latency:.1f} ms")
        self.lbl_gesture_val.setText(gesto)

    @Slot(float, float)
    def update_angles(self, q1, q2):
        """Actualiza telemetría y envía paquetes si estamos en modo automático."""
        if self.combo_mode.currentText() == "Seguimiento Automático 3D":
            self.lbl_q1_val.setText(f"{q1:.1f}°")
            self.lbl_q2_val.setText(f"{q2:.1f}°")
            self.slider_q1.blockSignals(True)
            self.slider_q2.blockSignals(True)
            self.slider_q1.setValue(int(q1))
            self.slider_q2.setValue(int(q2))
            self.slider_q1.blockSignals(False)
            self.slider_q2.blockSignals(False)
            self.send_udp(q1, q2)

    def on_slider_manual(self):
        """Envía ángulos en modo manual."""
        if self.combo_mode.currentText() == "Control Manual":
            q1 = float(self.slider_q1.value())
            q2 = float(self.slider_q2.value())
            self.lbl_q1_val.setText(f"{q1:.1f}°")
            self.lbl_q2_val.setText(f"{q2:.1f}°")
            self.send_udp(q1, q2)

    def send_udp(self, q1, q2):
        """Transmite coordenadas a Unity o ESP32."""
        try:
            msg = f"{q1:.2f},{q2:.2f}".encode("utf-8")
            self.sock.sendto(msg, (self.target_ip, self.target_port))
        except Exception:
            pass

    def closeEvent(self, event):
        """Asegura liberar la cámara al cerrar la ventana."""
        self.stop_vision()
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SofiaDashboard()
    window.show()
    sys.exit(app.exec())
