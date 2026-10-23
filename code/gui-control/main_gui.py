"""
Estacion de control y monitoreo para el proyecto SOFIA 2026.
Interfaz grafica en PySide6 que conecta la deteccion de posturas (MediaPipe),
el despacho de comunicaciones (UDP para simulacion y BLE para ESP32) y el
control manual de los servomotores.
"""

import os
import sys

from PySide6.QtCore import Qt, Slot, Signal, QObject, QTimer
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QGroupBox,
    QSlider,
    QComboBox,
    QTextEdit,
    QFrame,
    QRadioButton,
    QLineEdit,
)

# Rutas a paquetes hermanos del repositorio
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
    """
    Puente de senales Qt para eventos de Bluetooth.
    Permite que los callbacks asincronos de Bleak actualicen la GUI
    de forma segura en el hilo principal.
    """
    state_changed = Signal(bool)
    log_received = Signal(str)


class SofiaDashboard(QMainWindow):
    """Ventana principal del panel de control de SOFIA."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("SOFIA 2026 - Centro de Control, Vision 3D y Telemetria")
        self.resize(1200, 760)
        self.setStyleSheet(MODERN_DARK_THEME)

        # Puente para sincronizar eventos BLE con la interfaz
        self.ble_bridge = BleStateBridge()
        self.ble_bridge.state_changed.connect(self._set_ble_button_state)
        self.ble_bridge.log_received.connect(self.log_event)

        # Despachador de comunicaciones (UDP o BLE)
        self.comm = SofiaCommDispatcher(
            log_callback=self.ble_bridge.log_received.emit,
            ble_state_callback=self.ble_bridge.state_changed.emit,
        )

        self.models_dir = os.path.join(TRACKING_DIR, "models")
        self.worker = None

        # Banderas de estado para rutinas ejecutadas en el robot
        self.rutina_esp32_activa = False
        self.hola_detectado = False
        self.corazon_detectado = False
        self.ciclo_saludo = 0

        self._build_ui()

    # -------------------------------------------------------------------------
    # Construccion de la interfaz (layouts y componentes)
    # -------------------------------------------------------------------------
    def _build_ui(self):
        """
        Organiza la ventana en dos columnas:
        - Izquierda (60%): visualizador de video en tiempo real.
        - Derecha (40%): paneles de configuracion, controles y terminal.
        """
        main_widget = QWidget()
        main_layout = QHBoxLayout(main_widget)
        main_layout.setSpacing(16)
        main_layout.setContentsMargins(16, 16, 16, 16)
        self.setCentralWidget(main_widget)

        main_layout.addWidget(self._build_video_panel(), stretch=6)
        main_layout.addWidget(self._build_controls_panel(), stretch=4)
        
        self.log_event("Sistema inicializado. Selecciona canal de destino e inicia la camara.")

    def _build_video_panel(self):
        """Panel de video con badges de FPS, latencia y gesto detectado."""
        panel = QFrame()
        panel.setObjectName("card")
        layout = QVBoxLayout(panel)

        # Encabezado con metricas
        header = QHBoxLayout()
        title = QLabel("Transmision en Tiempo Real")
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

        # Area de renderizado de la camara
        self.video_view = QLabel("Camara inactiva.\nPresiona 'Iniciar' para activar el tracking.")
        self.video_view.setAlignment(Qt.AlignCenter)
        self.video_view.setMinimumSize(640, 440)
        self.video_view.setStyleSheet(
            "background-color: #080A10; border: 1.5px dashed #2A3047; border-radius: 4px;"
        )
        layout.addWidget(self.video_view, stretch=1)

        # Barra inferior con el gesto activo
        gesture_box = QHBoxLayout()
        lbl_title = QLabel("Gesto Detectado:")
        lbl_title.setStyleSheet("font-weight: 600; color: #94A3B8; font-size: 12px;")
        
        self.lbl_gesture_val = QLabel("NINGUNO")
        self.lbl_gesture_val.setObjectName("badge")
        self.lbl_gesture_val.setStyleSheet(
            "font-size: 12.5px; font-weight: 700; color: #A5B4FC; background-color: #1E1B4B; border: 1px solid #4F46E5; border-radius: 3px; padding: 4px 10px;"
        )
        gesture_box.addWidget(lbl_title)
        gesture_box.addWidget(self.lbl_gesture_val)
        gesture_box.addStretch()
        layout.addLayout(gesture_box)

        return panel

    def _build_controls_panel(self):
        """Panel lateral derecho con todas las secciones de control."""
        panel = QFrame()
        panel.setObjectName("card")
        layout = QVBoxLayout(panel)
        layout.setSpacing(12)

        layout.addWidget(self._build_network_section())
        layout.addWidget(self._build_mode_section())
        layout.addWidget(self._build_joints_section())
        layout.addWidget(self._build_console_section(), stretch=1)

        return panel

    def _build_network_section(self):
        """Seccion para seleccionar entre simulacion UDP y robot real BLE."""
        group = QGroupBox("Destino de Comunicacion")
        layout = QVBoxLayout(group)

        row_radio = QHBoxLayout()
        self.radio_udp = QRadioButton("Simulacion (Unity / UDP)")
        self.radio_ble = QRadioButton("Robot Fisico (ESP32 / BLE)")
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
        """Controles del hilo de vision (iniciar, pausar, detener) y modos de operacion."""
        group = QGroupBox("Control de Operacion")
        layout = QVBoxLayout(group)

        # Botones de control del ciclo de vida de la deteccion
        row_btn = QHBoxLayout()
        
        self.btn_start = QPushButton("Iniciar")
        self.btn_start.setObjectName("btn-start")
        self.btn_start.clicked.connect(self._handle_start_vision)

        self.btn_pause = QPushButton("Pausar")
        self.btn_pause.setObjectName("btn-pause")
        self.btn_pause.setEnabled(False)
        self.btn_pause.clicked.connect(self._handle_pause_resume_vision)

        self.btn_stop = QPushButton("Detener")
        self.btn_stop.setObjectName("btn-stop")
        self.btn_stop.setEnabled(False)
        self.btn_stop.clicked.connect(self._handle_stop_vision)

        row_btn.addWidget(self.btn_start)
        row_btn.addWidget(self.btn_pause)
        row_btn.addWidget(self.btn_stop)
        layout.addLayout(row_btn)

        # Selector de modo operativo
        row_combo = QHBoxLayout()
        row_combo.addWidget(QLabel("Modo:"))
        self.combo_mode = QComboBox()
        self.combo_mode.addItems([
            "Seguimiento Automatico 3D",
            "Control Manual",
            "Calibracion (Home)",
            "Reposo",
        ])
        self.combo_mode.currentIndexChanged.connect(self._handle_mode_changed)
        row_combo.addWidget(self.combo_mode)
        layout.addLayout(row_combo)

        return group

    def _build_joints_section(self):
        """Sliders manuales para q1 (horizontal) y q2 (vertical), acotados de 60 a 120 grados."""
        group = QGroupBox("Articulaciones (q1: Yaw, q2: Pitch)")
        layout = QGridLayout(group)

        # Eje q1
        layout.addWidget(QLabel("q1 (Horizontal):"), 0, 0)
        self.lbl_q1_val = QLabel("90°")
        self.lbl_q1_val.setStyleSheet("font-weight: bold; color: #818CF8;")
        layout.addWidget(self.lbl_q1_val, 0, 1)
        
        self.slider_q1 = QSlider(Qt.Horizontal)
        self.slider_q1.setRange(ANGULO_MIN, ANGULO_MAX)
        self.slider_q1.setValue(90)
        self.slider_q1.valueChanged.connect(self._handle_manual_slider)
        layout.addWidget(self.slider_q1, 1, 0, 1, 2)

        # Eje q2
        layout.addWidget(QLabel("q2 (Vertical):"), 2, 0)
        self.lbl_q2_val = QLabel("90°")
        self.lbl_q2_val.setStyleSheet("font-weight: bold; color: #818CF8;")
        layout.addWidget(self.lbl_q2_val, 2, 1)

        self.slider_q2 = QSlider(Qt.Horizontal)
        self.slider_q2.setRange(ANGULO_MIN, ANGULO_MAX)
        self.slider_q2.setValue(90)
        self.slider_q2.valueChanged.connect(self._handle_manual_slider)
        layout.addWidget(self.slider_q2, 3, 0, 1, 2)

        return group

    def _build_console_section(self):
        """Terminal de log para eventos y telemetria."""
        group = QGroupBox("Terminal de Telemetria")
        layout = QVBoxLayout(group)

        self.log_terminal = QTextEdit()
        self.log_terminal.setObjectName("logTerminal")
        self.log_terminal.setReadOnly(True)
        layout.addWidget(self.log_terminal)

        return group

    # -------------------------------------------------------------------------
    # Comunicaciones
    # -------------------------------------------------------------------------
    def log_event(self, text):
        """Escribe un mensaje en la terminal de la GUI."""
        self.log_terminal.append(f"> {text}")

    def _on_channel_radio_toggled(self):
        """Conmuta entre canal UDP y BLE segun el radio button activo."""
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
        if self.radio_udp.isChecked():
            value = text.strip() or self.txt_destination.placeholderText()
            self.comm.set_udp_target(value)

    def _handle_action_click(self):
        if self.rutina_esp32_activa:
            self.log_event("Accion bloqueada: rutina en ejecucion.")
            return

        if self.radio_udp.isChecked():
            value = self.txt_destination.text().strip() or self.txt_destination.placeholderText()
            self.comm.set_udp_target(value)
            self.log_event(f"Destino UDP guardado: {value}")
        else:
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
        """Actualiza el aspecto del boton segun el estado de conexion BLE."""
        if not self.radio_ble.isChecked():
            return
        self.btn_action.setEnabled(True)
        if is_connected:
            self.btn_action.setText("Desconectar")
            self.btn_action.setStyleSheet(
                "background-color: #312E81; border: 1px solid #6366F1; color: #EEF2FF;"
            )
        else:
            self.btn_action.setText("Conectar BLE")
            self.btn_action.setStyleSheet("")

    # -------------------------------------------------------------------------
    # Manejadores de camara y vision
    # -------------------------------------------------------------------------
    @Slot()
    def _handle_start_vision(self):
        """Inicia el worker de la camara en un hilo separado."""
        if self.worker is not None:
            return

        self.worker = VisionWorker(
            camera_id=0,
            models_dir=self.models_dir
        )
        self.worker.frame_ready.connect(self._on_frame_ready)
        self.worker.metrics_ready.connect(self._on_metrics_ready)
        self.worker.angles_ready.connect(self._on_angles_ready)
        self.worker.status_message.connect(self.log_event)
        self.worker.start()

        self.btn_start.setEnabled(False)
        self.btn_pause.setEnabled(True)
        self.btn_pause.setText("Pausar")
        self.btn_stop.setEnabled(True)

    @Slot()
    def _handle_pause_resume_vision(self):
        """Alterna entre pausar y reanudar la deteccion."""
        if not self.worker:
            return

        if self.worker.is_paused():
            self.worker.resume()
            self.btn_pause.setText("Pausar")
            self.log_event("Control: deteccion reanudada.")
        else:
            self.worker.pause()
            self.btn_pause.setText("Reanudar")
            self.log_event("Control: deteccion pausada.")

    @Slot()
    def _handle_stop_vision(self):
        """Detiene el worker y libera la camara."""
        if self.worker:
            self.worker.stop()
            self.worker = None

        self.btn_start.setEnabled(True)
        self.btn_pause.setEnabled(False)
        self.btn_pause.setText("Pausar")
        self.btn_stop.setEnabled(False)
        self.video_view.setText("Camara detenida.\nPresiona 'Iniciar' para reanudar.")

    @Slot(object)
    def _on_frame_ready(self, q_img):
        """Escala y muestra el fotograma en el QLabel."""
        pixmap = QPixmap.fromImage(q_img)
        scaled = pixmap.scaled(
            self.video_view.size(),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )
        self.video_view.setPixmap(scaled)

    @Slot(float, float, str)
    def _on_metrics_ready(self, fps, latency, gesto):
        """Actualiza telemetria y dispara rutinas al reconocer gestos clave."""
        self.lbl_fps_badge.setText(f"FPS: {fps:.1f}")
        self.lbl_latency_badge.setText(f"Lat: {latency:.1f} ms")
        self.lbl_gesture_val.setText(gesto)

        gesto_actual = str(gesto).strip().lower()
        gesto_actual = (
            gesto_actual
            .replace("á", "a")
            .replace("é", "e")
            .replace("í", "i")
            .replace("ó", "o")
            .replace("ú", "u")
        )

        es_hola = "hola" in gesto_actual or "saludo" in gesto_actual
        es_corazon = "corazon" in gesto_actual

        if not es_hola:
            self.hola_detectado = False

        if not es_corazon:
            self.corazon_detectado = False

        # Disparo unico por deteccion
        if es_hola and not self.hola_detectado:
            self.hola_detectado = True
            self._enviar_comando_rutina("SALUDO")

        elif es_corazon and not self.corazon_detectado:
            self.corazon_detectado = True
            self._enviar_comando_rutina("CORAZON")

    @Slot(float, float)
    def _on_angles_ready(self, q1_raw, q2_raw):
        """Mapea los angulos detectados al rango seguro y los despacha."""
        if self.rutina_esp32_activa:
            return

        if self.combo_mode.currentText() == "Seguimiento Automatico 3D":
            # Escalado de seguridad alrededor de 90 grados
            q1 = int(max(
                ANGULO_MIN,
                min(ANGULO_MAX, 90 + int(q1_raw * (30.0 / 90.0)))
            ))
            q2 = int(max(
                ANGULO_MIN,
                min(ANGULO_MAX, 90 + int(q2_raw * (30.0 / 90.0)))
            ))

            self._update_joint_display(q1, q2)
            self.comm.send_angles(q1, q2)

    # -------------------------------------------------------------------------
    # Rutinas locales en ESP32
    # -------------------------------------------------------------------------
    def _enviar_comando_rutina(self, comando):
        """Envia comando de rutina y bloquea seguimiento temporalmente."""
        if self.rutina_esp32_activa:
            self.log_event(f"Comando {comando} ignorado: rutina en ejecucion.")
            return

        if not self.radio_ble.isChecked():
            self.log_event(f"Gesto {comando} detectado, pero BLE no esta activo.")
            return

        if not self.comm.is_ble_connected():
            self.log_event(f"Gesto {comando} detectado, pero no hay conexion BLE.")
            return

        duracion_ms = {
            "SALUDO": 3000,
            "CORAZON": 2000,
        }.get(comando)

        if duracion_ms is None:
            self.log_event(f"Rutina desconocida: {comando}")
            return

        try:
            enviado = self.comm.send_command(comando)
            if not enviado:
                self.log_event(f"No se pudo enviar {comando}.")
                return

            self.rutina_esp32_activa = True
            self.log_event(f"{comando} enviado. ESP32 ejecutando rutina.")

            # Temporizador no bloqueante para liberar el seguimiento al finalizar
            QTimer.singleShot(duracion_ms, self._finalizar_rutina_esp32)

        except Exception as error:
            self.log_event(f"Error al enviar {comando}: {error}")

    def _finalizar_rutina_esp32(self):
        self.rutina_esp32_activa = False
        self.log_event("Rutina finalizada. Seguimiento habilitado.")

    # -------------------------------------------------------------------------
    # Control manual y modos
    # -------------------------------------------------------------------------
    def _handle_manual_slider(self):
        if self.rutina_esp32_activa:
            return
        if self.combo_mode.currentText() == "Control Manual":
            q1 = self.slider_q1.value()
            q2 = self.slider_q2.value()
            self._update_joint_display(q1, q2)
            self.comm.send_angles(q1, q2)

    def _handle_mode_changed(self, idx):
        if self.rutina_esp32_activa:
            return

        mode = self.combo_mode.currentText()
        if mode == "Calibracion (Home)":
            self._update_joint_display(90, 90)
            self.comm.send_angles(90, 90)
            self.log_event("Calibracion: servomotores centrados a 90, 90.")
        elif mode == "Reposo":
            self._update_joint_display(90, 60)
            self.comm.send_angles(90, 60)
            self.log_event("Reposo: postura de descanso activada.")

    def _update_joint_display(self, q1, q2):
        """Actualiza etiquetas y posiciones de los sliders sin disparar senales recursivas."""
        self.lbl_q1_val.setText(f"{q1}°")
        self.lbl_q2_val.setText(f"{q2}°")
        
        self.slider_q1.blockSignals(True)
        self.slider_q2.blockSignals(True)
        self.slider_q1.setValue(q1)
        self.slider_q2.setValue(q2)
        self.slider_q1.blockSignals(False)
        self.slider_q2.blockSignals(False)

    def closeEvent(self, event):
        """Cierre ordenado de hilos y conexiones al cerrar la ventana."""
        self._handle_stop_vision()
        self.comm.close()
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SofiaDashboard()
    window.show()
    sys.exit(app.exec())
