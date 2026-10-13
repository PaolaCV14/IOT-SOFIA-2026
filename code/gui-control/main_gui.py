"""
==============================================================
ESTACIÓN DE CONTROL Y MONITOREO SOFIA (PySide6)
Interfaz gráfica modular: Desacoplada de lógica de video y comunicaciones
==============================================================
"""

import sys
import os
from PySide6.QtCore import Qt, Slot, Signal, QObject
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QPushButton,
    QVBoxLayout, QHBoxLayout, QGridLayout, QGroupBox, QSlider,
    QComboBox, QTextEdit, QFrame, QRadioButton, QButtonGroup, QLineEdit
)

# Inclusión de rutas de módulos hermanos
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
CODE_DIR = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
TRACKING_DIR = os.path.join(CODE_DIR, "tracking-vision")
COMM_DIR = os.path.join(CODE_DIR, "communication")

for path in (TRACKING_DIR, COMM_DIR):
    if path not in sys.path:
        sys.path.append(path)

from vision_worker import VisionWorker
from dispatcher import SofiaCommDispatcher
from ble_sender import ANGULO_MIN, ANGULO_MAX, ESP32_DEFAULT_MAC
from styles import MODERN_DARK_THEME


class BleStateBridge(QObject):
    """Puente thread-safe de señales Qt para eventos BLE."""
    state_changed = Signal(bool)
    log_received = Signal(str)


class SofiaDashboard(QMainWindow):
    """Ventana principal del panel de control de SOFÍA."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("SOFÍA 2026 - Centro de Control, Visión 3D y Telemetría")
        self.resize(1200, 760)
        self.setStyleSheet(MODERN_DARK_THEME)

        # Puente de eventos entre hilos
        self.ble_bridge = BleStateBridge()
        self.ble_bridge.state_changed.connect(self._set_ble_button_state)
        self.ble_bridge.log_received.connect(self.log_event)

        # 1. Módulos Desacoplados
        self.comm = SofiaCommDispatcher(
            log_callback=self.ble_bridge.log_received.emit,
            ble_state_callback=self.ble_bridge.state_changed.emit
        )
        self.models_dir = os.path.join(TRACKING_DIR, "models")
        self.worker = None

        self._build_ui()

    # -------------------------------------------------------------
    # CONSTRUCCIÓN VISUAL (UI LAYOUT)
    # -------------------------------------------------------------
    def _build_ui(self):
        main_widget = QWidget()
        main_layout = QHBoxLayout(main_widget)
        main_layout.setSpacing(16)
        main_layout.setContentsMargins(16, 16, 16, 16)
        self.setCentralWidget(main_widget)

        # Panel de Cámara (Izquierda)
        left_panel = self._build_video_panel()
        main_layout.addWidget(left_panel, stretch=6)

        # Panel de Mandos y Telemetría (Derecha)
        right_panel = self._build_controls_panel()
        main_layout.addWidget(right_panel, stretch=4)

        self.log_event("Sistema inicializado. Selecciona canal de destino e inicia la cámara.")

    def _build_video_panel(self):
        panel = QFrame()
        panel.setObjectName("card")
        layout = QVBoxLayout(panel)

        header = QHBoxLayout()
        title = QLabel("🎥 Transmisión en Tiempo Real")
        title.setStyleSheet("font-size: 15px; font-weight: bold; color: #F8FAFC;")
        self.lbl_fps_badge = QLabel("FPS: --")
        self.lbl_fps_badge.setObjectName("badge")
        self.lbl_latency_badge = QLabel("Latencia: -- ms")
        self.lbl_latency_badge.setObjectName("badge")

        header.addWidget(title)
        header.addStretch()
        header.addWidget(self.lbl_fps_badge)
        header.addWidget(self.lbl_latency_badge)
        layout.addLayout(header)

        # Viewport de video
        self.video_view = QLabel("Cámara inactiva.\nPresiona 'Iniciar Cámara' para activar el tracking.")
        self.video_view.setAlignment(Qt.AlignCenter)
        self.video_view.setMinimumSize(640, 440)
        self.video_view.setStyleSheet("background-color: #0A0C0F; border: 2px dashed #2A303C; border-radius: 8px;")
        layout.addWidget(self.video_view, stretch=1)

        # Barra inferior de gestos
        gesture_box = QHBoxLayout()
        lbl_title = QLabel("Gesto Detectado:")
        lbl_title.setStyleSheet("font-weight: 600; color: #94A3B8;")
        self.lbl_gesture_val = QLabel("NINGUNO")
        self.lbl_gesture_val.setObjectName("badge")
        self.lbl_gesture_val.setStyleSheet("font-size: 14px; font-weight: bold; color: #38BDF8; padding: 6px 12px;")

        gesture_box.addWidget(lbl_title)
        gesture_box.addWidget(self.lbl_gesture_val)
        gesture_box.addStretch()
        layout.addLayout(gesture_box)

        return panel

    def _build_controls_panel(self):
        panel = QFrame()
        panel.setObjectName("card")
        layout = QVBoxLayout(panel)
        layout.setSpacing(12)

        # 1. Sección de Conectividad (BLE / UDP)
        layout.addWidget(self._build_network_section())

        # 2. Control de Cámara y Modos
        layout.addWidget(self._build_mode_section())

        # 3. Orientación Articular
        layout.addWidget(self._build_joints_section())

        # 4. Consola de Logs
        layout.addWidget(self._build_console_section(), stretch=1)

        return panel

    def _build_network_section(self):
        group = QGroupBox("Destino de Comunicación")
        layout = QVBoxLayout(group)

        row_radio = QHBoxLayout()
        self.radio_udp = QRadioButton("Simulación (Unity / UDP)")
        self.radio_ble = QRadioButton("Robot Físico (ESP32 / BLE)")
        self.radio_udp.setChecked(True)

        self.radio_udp.toggled.connect(self._on_channel_radio_toggled)
        self.radio_ble.toggled.connect(self._on_channel_radio_toggled)

        row_radio.addWidget(self.radio_udp)
        row_radio.addWidget(self.radio_ble)
        layout.addLayout(row_radio)

        row_dest = QHBoxLayout()
        self.txt_destination = QLineEdit()
        self.txt_destination.setPlaceholderText("127.0.0.1:5005")
        self.txt_destination.setText("127.0.0.1:5005")
        self.txt_destination.textChanged.connect(self._on_destination_text_changed)

        self.btn_action = QPushButton("Guardar Destino")
        self.btn_action.clicked.connect(self._handle_action_click)

        row_dest.addWidget(self.txt_destination)
        row_dest.addWidget(self.btn_action)
        layout.addLayout(row_dest)

        return group

    def _build_mode_section(self):
        group = QGroupBox("Control de Operación")
        layout = QVBoxLayout(group)

        row_btn = QHBoxLayout()
        self.btn_start = QPushButton("▶ Iniciar Cámara")
        self.btn_start.setObjectName("btn-start")
        self.btn_start.clicked.connect(self._handle_start_vision)

        self.btn_stop = QPushButton("⏹ Detener")
        self.btn_stop.setObjectName("btn-stop")
        self.btn_stop.setEnabled(False)
        self.btn_stop.clicked.connect(self._handle_stop_vision)

        row_btn.addWidget(self.btn_start)
        row_btn.addWidget(self.btn_stop)
        layout.addLayout(row_btn)

        row_combo = QHBoxLayout()
        row_combo.addWidget(QLabel("Modo:"))
        self.combo_mode = QComboBox()
        self.combo_mode.addItems(["Seguimiento Automático 3D", "Control Manual", "Calibración (Home)", "Reposo"])
        self.combo_mode.currentIndexChanged.connect(self._handle_mode_changed)
        row_combo.addWidget(self.combo_mode)
        layout.addLayout(row_combo)

        return group

    def _build_joints_section(self):
        group = QGroupBox("Articulaciones (q1: Yaw, q2: Pitch)")
        layout = QGridLayout(group)

        layout.addWidget(QLabel("q1 (Horizontal):"), 0, 0)
        self.lbl_q1_val = QLabel("90.0°")
        self.lbl_q1_val.setStyleSheet("font-weight: bold; color: #38BDF8;")
        layout.addWidget(self.lbl_q1_val, 0, 1)

        self.slider_q1 = QSlider(Qt.Horizontal)
        self.slider_q1.setRange(ANGULO_MIN, ANGULO_MAX)
        self.slider_q1.setValue(90)
        self.slider_q1.valueChanged.connect(self._handle_manual_slider)
        layout.addWidget(self.slider_q1, 1, 0, 1, 2)

        layout.addWidget(QLabel("q2 (Vertical):"), 2, 0)
        self.lbl_q2_val = QLabel("90.0°")
        self.lbl_q2_val.setStyleSheet("font-weight: bold; color: #38BDF8;")
        layout.addWidget(self.lbl_q2_val, 2, 1)

        self.slider_q2 = QSlider(Qt.Horizontal)
        self.slider_q2.setRange(ANGULO_MIN, ANGULO_MAX)
        self.slider_q2.setValue(90)
        self.slider_q2.valueChanged.connect(self._handle_manual_slider)
        layout.addWidget(self.slider_q2, 3, 0, 1, 2)

        return group

    def _build_console_section(self):
        group = QGroupBox("Terminal de Telemetría")
        layout = QVBoxLayout(group)
        self.log_terminal = QTextEdit()
        self.log_terminal.setObjectName("logTerminal")
        self.log_terminal.setReadOnly(True)
        layout.addWidget(self.log_terminal)
        return group

    # -------------------------------------------------------------
    # CONTROLADORES DE EVENTOS Y ACCIONES (HANDLERS)
    # -------------------------------------------------------------
    def log_event(self, text):
        self.log_terminal.append(f"> {text}")

    def _on_channel_radio_toggled(self):
        """Alterna el placeholder y el texto del botón al cambiar entre UDP y BLE."""
        if self.radio_udp.isChecked():
            self.comm.set_channel(SofiaCommDispatcher.MODE_UDP)
            self.txt_destination.setPlaceholderText("127.0.0.1:5005")
            self.txt_destination.setText("127.0.0.1:5005")
            self.btn_action.setText("Guardar Destino")
            self.btn_action.setStyleSheet("")
            self.btn_action.setEnabled(True)
        else:
            self.comm.set_channel(SofiaCommDispatcher.MODE_BLE)
            self.txt_destination.setPlaceholderText(ESP32_DEFAULT_MAC)
            self.txt_destination.setText(ESP32_DEFAULT_MAC)
            self._set_ble_button_state(self.comm.is_ble_connected())

    def _on_destination_text_changed(self, text):
        """Si es UDP y el usuario edita la IP/puerto, se guarda de inmediato."""
        if self.radio_udp.isChecked():
            val = text.strip() or self.txt_destination.placeholderText()
            self.comm.set_udp_target(val)

    def _handle_action_click(self):
        """Maneja el clic del botón según el canal activo."""
        if self.radio_udp.isChecked():
            val = self.txt_destination.text().strip() or self.txt_destination.placeholderText()
            self.comm.set_udp_target(val)
            self.log_event(f"Destino UDP guardado: {val}")
        else:
            # Canal BLE
            if self.comm.is_ble_active_or_trying() or self.comm.is_ble_connected():
                self.comm.disconnect_ble()
                self._set_ble_button_state(False)
            else:
                mac = self.txt_destination.text().strip() or self.txt_destination.placeholderText()
                self.btn_action.setText("Conectando...")
                self.btn_action.setEnabled(True)
                self.comm.connect_ble(mac)

    @Slot(bool)
    def _set_ble_button_state(self, is_connected):
        """Actualiza la apariencia del botón BLE según el estado real."""
        if not self.radio_ble.isChecked():
            return

        self.btn_action.setEnabled(True)
        if is_connected:
            self.btn_action.setText("Desconectar")
            self.btn_action.setStyleSheet("background-color: #065F46; border: 1px solid #10B981;")
        else:
            self.btn_action.setText("Conectar BLE")
            self.btn_action.setStyleSheet("")

    @Slot()
    def _handle_start_vision(self):
        self.worker = VisionWorker(camera_id=0, models_dir=self.models_dir)
        self.worker.frame_ready.connect(self._on_frame_ready)
        self.worker.metrics_ready.connect(self._on_metrics_ready)
        self.worker.angles_ready.connect(self._on_angles_ready)
        self.worker.status_message.connect(self.log_event)

        self.worker.start()
        self.btn_start.setEnabled(False)
        self.btn_stop.setEnabled(True)

    @Slot()
    def _handle_stop_vision(self):
        if self.worker:
            self.worker.stop()
            self.worker = None
        self.btn_start.setEnabled(True)
        self.btn_stop.setEnabled(False)
        self.video_view.setText("Cámara detenida.")

    @Slot(object)
    def _on_frame_ready(self, q_img):
        pixmap = QPixmap.fromImage(q_img)
        scaled = pixmap.scaled(self.video_view.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.video_view.setPixmap(scaled)

    @Slot(float, float, str)
    def _on_metrics_ready(self, fps, latency, gesto):
        self.lbl_fps_badge.setText(f"FPS: {fps:.1f}")
        self.lbl_latency_badge.setText(f"Lat: {latency:.1f} ms")
        self.lbl_gesture_val.setText(gesto)

    @Slot(float, float)
    def _on_angles_ready(self, q1_raw, q2_raw):
        if self.combo_mode.currentText() == "Seguimiento Automático 3D":
            # Normalizar a rango seguro (60 a 120, centro 90)
            q1 = int(max(ANGULO_MIN, min(ANGULO_MAX, 90 + int(q1_raw * (30.0 / 90.0)))))
            q2 = int(max(ANGULO_MIN, min(ANGULO_MAX, 90 + int(q2_raw * (30.0 / 90.0)))))

            self._update_joint_display(q1, q2)
            self.comm.send_angles(q1, q2)

    def _handle_manual_slider(self):
        if self.combo_mode.currentText() == "Control Manual":
            q1 = self.slider_q1.value()
            q2 = self.slider_q2.value()
            self._update_joint_display(q1, q2)
            self.comm.send_angles(q1, q2)

    def _handle_mode_changed(self, idx):
        mode = self.combo_mode.currentText()
        if mode == "Calibración (Home)":
            self._update_joint_display(90, 90)
            self.comm.send_angles(90, 90)
            self.log_event("Calibración: Servomotores centrados a 90°, 90°.")
        elif mode == "Reposo":
            self._update_joint_display(90, 60)
            self.comm.send_angles(90, 60)
            self.log_event("Reposo: Postura de descanso y bajo consumo activada.")

    def _update_joint_display(self, q1, q2):
        self.lbl_q1_val.setText(f"{q1}°")
        self.lbl_q2_val.setText(f"{q2}°")
        self.slider_q1.blockSignals(True)
        self.slider_q2.blockSignals(True)
        self.slider_q1.setValue(q1)
        self.slider_q2.setValue(q2)
        self.slider_q1.blockSignals(False)
        self.slider_q2.blockSignals(False)

    def closeEvent(self, event):
        self._handle_stop_vision()
        self.comm.close()
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SofiaDashboard()
    window.show()
    sys.exit(app.exec())
