"""
Worker de visión por computadora para la interfaz gráfica de SOFIA.
Ejecuta la captura de video y la inferencia de MediaPipe en un hilo
secundario (QThread) para no bloquear el hilo principal de la GUI.
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

    def __init__(self, camera_id=0, models_dir=None):
        super().__init__()
        self.camera_id = camera_id
        self.models_dir = models_dir or "models"

        # Banderas de control de estado del hilo
        self._running = False
        self._paused = False
        self.use_smoothing = True

    def run(self):
        """Bucle principal de captura e inferencia del hilo."""
        self._running = True
        self.status_message.emit("Iniciando pipeline de vision...")

        # 1. Cargar modelos de MediaPipe
        try:
            hand_path = os.path.join(self.models_dir, "hand_landmarker.task")
            pose_path = os.path.join(self.models_dir, "pose_landmarker_lite.task")

            hand_detector = HandDetector(model_path=hand_path)
            pose_detector = PoseDetector(model_path=pose_path)
            gesture_detector = GestureDetector()
            
            # Filtro EMA (alpha=0.35) para reducir temblor en landmarks
            smoother = LandmarkSmoother(alpha=0.35)
            self.status_message.emit("Modelos de MediaPipe cargados correctamente.")
        except Exception as e:
            self.status_message.emit(f"Error al cargar detectores: {e}")
            return

        # 2. Inicializar camara con OpenCV
        cap = cv2.VideoCapture(self.camera_id)
        if not cap.isOpened():
            self.status_message.emit(f"Error: No se pudo abrir la camara {self.camera_id}.")
            return

        self.status_message.emit("Camara activa. Procesando frames...")

        start_time = time.time()
        prev_time = time.time()
        fps_smooth = 30.0

        # 3. Bucle continuo de captura
        while self._running:
            ret, frame = cap.read()
            if not ret:
                time.sleep(0.01)
                continue

            # Espejo horizontal para que la interaccion sea intuitiva
            frame = cv2.flip(frame, 1)
            h, w, _ = frame.shape

            # Si la deteccion esta en pausa, no corremos inferencia pesada
            # pero mantenemos el stream de la camara activo
            if self._paused:
                cv2.putText(
                    frame,
                    "[ DETECCION PAUSADA ]",
                    (max(20, int(w * 0.22)), int(h * 0.5)),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1.0,
                    (0, 165, 255),
                    2,
                    cv2.LINE_AA,
                )
                self.metrics_ready.emit(0.0, 0.0, "PAUSADO")
                
                rgb_render = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                bytes_per_line = 3 * w
                q_img = QImage(rgb_render.data, w, h, bytes_per_line, QImage.Format_RGB888).copy()
                self.frame_ready.emit(q_img)
                time.sleep(0.03)
                continue

            # MediaPipe requiere formato RGB
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
            timestamp_ms = int((time.time() - start_time) * 1000)

            # Inferencia y calculo de tiempo de procesamiento
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

            # Dibujo de esqueleto sobre el frame
            dibujar_pose(frame, pose, w, h)
            dibujar_manos(frame, hands, w, h)

            # Deteccion de gestos definidos para SOFIA
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

            # Calculo de orientacion respecto al centro de la imagen (-90 a 90 grados)
            # q1: Yaw horizontal, q2: Pitch vertical usando la muneca como referencia
            q1, q2 = 0.0, 0.0
            if hands and hands.hand_landmarks:
                muneca = hands.hand_landmarks[0][0]
                q1 = (muneca.x - 0.5) * 180.0
                q2 = (0.5 - muneca.y) * 180.0
                self.angles_ready.emit(round(q1, 1), round(q2, 1))

            # Calculo de FPS con filtro suave para visualizacion estable
            now = time.time()
            fps_instant = 1.0 / max(now - prev_time, 1e-5)
            prev_time = now
            fps_smooth = 0.9 * fps_smooth + 0.1 * fps_instant

            self.metrics_ready.emit(fps_smooth, latencia_ms, gesto_activo)

            # Convertir frame de OpenCV (BGR) a QImage para pintarlo en Qt
            rgb_render = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            bytes_per_line = 3 * w
            q_img = QImage(rgb_render.data, w, h, bytes_per_line, QImage.Format_RGB888).copy()
            self.frame_ready.emit(q_img)

        # Liberar camara y detectores al salir
        cap.release()
        hand_detector.close()
        pose_detector.close()
        self.status_message.emit("Camara y detectores detenidos limpiamente.")

    # Control de ciclo de vida del hilo desde la interfaz
    def stop(self):
        """Detiene el bucle y espera a que el hilo termine."""
        self._running = False
        self._paused = False
        self.wait(1000)

    def pause(self):
        """Pausa la deteccion sin apagar la camara ni destruir el hilo."""
        self._paused = True
        self.status_message.emit("Deteccion pausada.")

    def resume(self):
        """Reanuda la deteccion de posturas y gestos."""
        self._paused = False
        self.status_message.emit("Deteccion reanudada.")

    def is_paused(self):
        """Retorna True si la deteccion esta en pausa."""
        return self._paused
