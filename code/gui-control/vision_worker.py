"""
Worker de visión por computadora para la interfaz gráfica de SOFIA.
Ejecuta la captura de video y la inferencia de MediaPipe en un hilo
secundario (QThread) para no bloquear el hilo principal de la GUI.

Incluye tolerancia a fallos:
- Recuperación automática ante desconexión física de la cámara web.
- Marco visual informativo cuando el dispositivo de video no responde.
- Notificaciones de ciclo de vida para sincronizar el estado de los botones.
"""

import time
import os
import cv2
import numpy as np
import mediapipe as mp
from PySide6.QtCore import QThread, Signal
from PySide6.QtGui import QImage

# Detectores y utilidades del modulo tracking-vision
from detectors.hand_detector import HandDetector
from detectors.pose_detector import PoseDetector
from detectors.gesture_detector import GestureDetector
from utils.drawing import dibujar_pose, dibujar_manos
from utils.smoother import LandmarkSmoother


class VisionWorker(QThread):
    """
    Hilo de captura y procesamiento de video en tiempo real.
    Comunica resultados a la ventana principal mediante senales de Qt.
    """

    # Senales Qt hacia la ventana principal
    frame_ready = Signal(QImage)                  # Frame procesado listo para mostrar
    metrics_ready = Signal(float, float, str)     # FPS, latencia en ms y gesto detectado
    angles_ready = Signal(float, float)           # Angulos calculados (q1 horizontal, q2 vertical)
    status_message = Signal(str)                  # Mensajes de estado para la terminal
    camera_status = Signal(bool, str)             # Estado de conexión física de la cámara (conectada, detalle)
    worker_finished = Signal(bool, str)           # Fin del hilo (éxito_limpio, mensaje_error)

    def __init__(self, camera_id=0, models_dir=None):
        super().__init__()
        self.camera_id = camera_id
        self.models_dir = models_dir or "models"

        # Banderas de control de estado del hilo
        self._running = False
        self._paused = False
        self.use_smoothing = True
        self._camera_online = False

    def _generar_frame_aviso(self, texto_principal, subtexto=""):
        """Genera un fotograma sintético cuando la cámara física no entrega video."""
        h, w = 480, 640
        canvas = np.full((h, w, 3), 15, dtype=np.uint8)  # Fondo oscuro

        # Recuadro central
        cv2.rectangle(canvas, (30, 30), (w - 30, h - 30), (45, 50, 65), 2)

        # Texto principal
        font = cv2.FONT_HERSHEY_SIMPLEX
        cv2.putText(canvas, texto_principal, (50, int(h * 0.45)), font, 0.75, (0, 165, 255), 2, cv2.LINE_AA)

        # Subtexto
        if subtexto:
            cv2.putText(canvas, subtexto, (50, int(h * 0.55)), font, 0.55, (180, 190, 205), 1, cv2.LINE_AA)

        rgb = cv2.cvtColor(canvas, cv2.COLOR_BGR2RGB)
        return QImage(rgb.data, w, h, 3 * w, QImage.Format_RGB888).copy()

    def run(self):
        """Bucle principal de captura e inferencia con recuperación automática."""
        self._running = True
        error_fatal = None
        cap = None
        hand_detector = None
        pose_detector = None

        self.status_message.emit("Iniciando pipeline de visión...")

        # 1. Cargar modelos de MediaPipe
        try:
            hand_path = os.path.join(self.models_dir, "hand_landmarker.task")
            pose_path = os.path.join(self.models_dir, "pose_landmarker_lite.task")

            hand_detector = HandDetector(model_path=hand_path)
            pose_detector = PoseDetector(model_path=pose_path)
            gesture_detector = GestureDetector()
            smoother = LandmarkSmoother(alpha=0.35)
            self.status_message.emit("Modelos de MediaPipe cargados correctamente.")
        except Exception as e:
            error_fatal = f"Error al cargar detectores de MediaPipe: {e}"
            self.status_message.emit(error_fatal)
            self.worker_finished.emit(False, error_fatal)
            return

        # 2. Inicializar cámara con OpenCV
        cap = cv2.VideoCapture(self.camera_id)
        if not cap.isOpened():
            # Si no abre de inmediato, no matamos la GUI; informamos y permitimos reintentos
            self.camera_status.emit(False, f"No se pudo acceder a la cámara ID {self.camera_id}")
            self.status_message.emit(f"Advertencia: Cámara {self.camera_id} no disponible inicialmente. Reintentando...")
            self.frame_ready.emit(self._generar_frame_aviso(
                "[ CÁMARA NO DISPONIBLE ]",
                f"Verifica la conexión USB del sensor {self.camera_id}."
            ))
            self._camera_online = False
        else:
            self._camera_online = True
            self.camera_status.emit(True, "Cámara activa")
            self.status_message.emit("Cámara activa. Procesando frames...")

        start_time = time.time()
        prev_time = time.time()
        fps_smooth = 30.0
        consecutive_read_failures = 0
        last_reconnect_attempt = 0.0

        try:
            # 3. Bucle continuo de captura
            while self._running:
                ahora_loop = time.time()

                # Manejo de reconexión si la cámara se desconectó
                if cap is None or not cap.isOpened() or consecutive_read_failures >= 15:
                    if self._camera_online:
                        self._camera_online = False
                        self.camera_status.emit(False, "Pérdida de señal de cámara")
                        self.status_message.emit("Alerta: Pérdida de señal en cámara. Intentando reconectar...")

                    # Mostrar aviso al usuario
                    self.metrics_ready.emit(0.0, 0.0, "CÁMARA DESCONECTADA")
                    self.frame_ready.emit(self._generar_frame_aviso(
                        "[ CÁMARA DESCONECTADA ]",
                        "Reintentando enlace con el dispositivo de video..."
                    ))

                    # Reintento con intervalo de 1.5s
                    if ahora_loop - last_reconnect_attempt > 1.5:
                        last_reconnect_attempt = ahora_loop
                        if cap is not None:
                            try:
                                cap.release()
                            except Exception:
                                pass
                        cap = cv2.VideoCapture(self.camera_id)
                        if cap.isOpened():
                            ret_test, _ = cap.read()
                            if ret_test:
                                consecutive_read_failures = 0
                                self._camera_online = True
                                self.camera_status.emit(True, "Cámara reconectada exitosamente")
                                self.status_message.emit("Cámara física reconectada exitosamente.")
                                continue

                    time.sleep(0.1)
                    continue

                # Lectura normal de frame
                ret, frame = cap.read()
                if not ret or frame is None:
                    consecutive_read_failures += 1
                    time.sleep(0.02)
                    continue

                # Lectura exitosa: restablecer contador de fallos
                consecutive_read_failures = 0
                if not self._camera_online:
                    self._camera_online = True
                    self.camera_status.emit(True, "Cámara activa")

                # Espejo horizontal para interacción intuitiva
                frame = cv2.flip(frame, 1)
                h, w, _ = frame.shape

                # Si está pausado: mostrar stream pero omitir inferencia
                if self._paused:
                    cv2.putText(
                        frame,
                        "[ DETECCIÓN PAUSADA ]",
                        (max(20, int(w * 0.22)), int(h * 0.5)),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        1.0,
                        (0, 165, 255),
                        2,
                        cv2.LINE_AA,
                    )
                    self.metrics_ready.emit(0.0, 0.0, "PAUSADO")
                    rgb_render = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    q_img = QImage(rgb_render.data, w, h, 3 * w, QImage.Format_RGB888).copy()
                    self.frame_ready.emit(q_img)
                    time.sleep(0.03)
                    continue

                # Inferencia MediaPipe protegida ante frames anómalos
                try:
                    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
                    timestamp_ms = int((time.time() - start_time) * 1000)

                    t0 = time.perf_counter()
                    raw_hands = hand_detector.detect(mp_image, timestamp_ms)
                    raw_pose = pose_detector.detect(mp_image, timestamp_ms)

                    # Suavizado de landmarks
                    if self.use_smoothing:
                        hands = smoother.smooth_hands(raw_hands)
                        pose = smoother.smooth_pose(raw_pose)
                    else:
                        hands = raw_hands
                        pose = raw_pose

                    # Renderizado sobre el frame
                    dibujar_pose(frame, pose, w, h)
                    dibujar_manos(frame, hands, w, h)

                    # Clasificación de gestos
                    ppt_det, ppt_txt = gesture_detector.detectar_intencion_ppt(hands)
                    saludo_det = gesture_detector.detectar_saludo(hands)
                    swipe_det, swipe_txt = gesture_detector.detectar_swipe(hands)

                    gestos = [
                        (gesture_detector.detectar_corazon(hands), "CORAZON"),
                        (ppt_det, ppt_txt),
                        (saludo_det, "HOLA! SALUDO"),
                        (swipe_det, swipe_txt),
                        (gesture_detector.detectar_tijera(hands), "TIJERA"),
                        (gesture_detector.detectar_papel(hands), "PAPEL"),
                        (gesture_detector.detectar_roca(hands), "ROCA")
                    ]

                    gesto_activo = "NINGUNO"
                    for detectado, texto in gestos:
                        if detectado:
                            gesto_activo = texto
                            break

                    latencia_ms = (time.perf_counter() - t0) * 1000

                    # Ángulos para seguimiento (-90 a 90 grados)
                    if hands and hands.hand_landmarks:
                        muneca = hands.hand_landmarks[0][0]
                        q1 = (muneca.x - 0.5) * 180.0
                        q2 = (0.5 - muneca.y) * 180.0
                        self.angles_ready.emit(round(q1, 1), round(q2, 1))

                    # FPS suave
                    now = time.time()
                    fps_instant = 1.0 / max(now - prev_time, 1e-5)
                    prev_time = now
                    fps_smooth = 0.9 * fps_smooth + 0.1 * fps_instant

                    self.metrics_ready.emit(fps_smooth, latencia_ms, gesto_activo)

                except Exception as infer_err:
                    self.status_message.emit(f"Advertencia frame: {infer_err}")

                # Emitir frame renderizado
                rgb_render = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                q_img = QImage(rgb_render.data, w, h, 3 * w, QImage.Format_RGB888).copy()
                self.frame_ready.emit(q_img)

        finally:
            if cap is not None:
                try:
                    cap.release()
                except Exception:
                    pass
            if hand_detector is not None:
                try:
                    hand_detector.close()
                except Exception:
                    pass
            if pose_detector is not None:
                try:
                    pose_detector.close()
                except Exception:
                    pass

            self.status_message.emit("Cámara y detectores detenidos limpiamente.")
            self.worker_finished.emit(error_fatal is None, error_fatal or "OK")

    def stop(self):
        """Detiene el bucle y espera a que el hilo termine."""
        self._running = False
        self._paused = False
        self.wait(1200)

    def pause(self):
        """Pausa la detección sin apagar la cámara ni destruir el hilo."""
        self._paused = True
        self.status_message.emit("Detección pausada.")

    def resume(self):
        """Reanuda la detección de posturas y gestos."""
        self._paused = False
        self.status_message.emit("Detección reanudada.")

    def is_paused(self):
        return self._paused
