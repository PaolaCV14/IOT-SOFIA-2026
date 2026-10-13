"""
==============================================================
WORKER DE VISIÓN POR COMPUTADORA (QThread)
Ejecuta la cámara y MediaPipe en un hilo secundario para no congelar la UI
==============================================================
"""

import time
import os
import cv2
import numpy as np
import mediapipe as mp
from PySide6.QtCore import QThread, Signal
from PySide6.QtGui import QImage

# Importamos los detectores y utilidades del módulo tracking-vision
from detectors.hand_detector import HandDetector
from detectors.pose_detector import PoseDetector
from detectors.gesture_detector import GestureDetector
from utils.drawing import dibujar_pose, dibujar_manos
from utils.smoother import LandmarkSmoother


class VisionWorker(QThread):
    """
    Hilo de trabajo independiente para procesamiento de video en tiempo real.
    Emite señales Qt a la ventana principal para mantener 60 FPS estables.
    """
    # Señales para comunicación fluida con la GUI
    frame_ready = Signal(QImage)
    metrics_ready = Signal(float, float, str)     # fps, latencia_ms, gesto_activo
    angles_ready = Signal(float, float)           # q1, q2 calculados
    status_message = Signal(str)                  # Mensajes de log para la consola

    def __init__(self, camera_id=0, models_dir=None):
        super().__init__()
        self.camera_id = camera_id
        self.models_dir = models_dir or "models"
        self._running = False
        self.use_smoothing = True

    def run(self):
        """Bucle principal de captura e inferencia de visión artificial."""
        self._running = True
        self.status_message.emit("Iniciando pipeline de visión...")

        # 1. Cargar modelos de detección
        try:
            hand_path = os.path.join(self.models_dir, "hand_landmarker.task")
            pose_path = os.path.join(self.models_dir, "pose_landmarker_lite.task")

            hand_detector = HandDetector(model_path=hand_path)
            pose_detector = PoseDetector(model_path=pose_path)
            gesture_detector = GestureDetector()
            smoother = LandmarkSmoother(alpha=0.35)
            self.status_message.emit("Modelos de MediaPipe cargados correctamente.")
        except Exception as e:
            self.status_message.emit(f"Error al cargar detectores: {e}")
            return

        # 2. Inicializar cámara
        cap = cv2.VideoCapture(self.camera_id)
        if not cap.isOpened():
            self.status_message.emit(f"Error: No se pudo abrir la cámara {self.camera_id}.")
            return

        self.status_message.emit("Cámara activa. Procesando frames...")

        start_time = time.time()
        prev_time = time.time()
        fps_smooth = 30.0

        while self._running:
            ret, frame = cap.read()
            if not ret:
                time.sleep(0.01)
                continue

            # Espejo horizontal para ergonomía de usuario
            frame = cv2.flip(frame, 1)
            h, w, _ = frame.shape

            # MediaPipe requiere formato RGB
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
            timestamp_ms = int((time.time() - start_time) * 1000)

            # Inferencia y medición de latencia
            t0 = time.perf_counter()
            raw_hands = hand_detector.detect(mp_image, timestamp_ms)
            raw_pose = pose_detector.detect(mp_image, timestamp_ms)

            # Suavizado EMA
            if self.use_smoothing:
                hands = smoother.smooth_hands(raw_hands)
                pose = smoother.smooth_pose(raw_pose)
            else:
                hands = raw_hands
                pose = raw_pose

            # Dibujo de esqueleto sobre el frame
            dibujar_pose(frame, pose, w, h)
            dibujar_manos(frame, hands, w, h)

            # Detección de Gestos
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

            # Cálculo de orientación de seguimiento (q1 horizontal, q2 vertical)
            # Usamos la muñeca o centro de la mano como vector normalizado (-90 a 90 grados)
            q1, q2 = 0.0, 0.0
            if hands and hands.hand_landmarks:
                muñeca = hands.hand_landmarks[0][0]  # Landmark 0: Wrist
                q1 = (muñeca.x - 0.5) * 180.0        # Yaw (-90 a +90)
                q2 = (0.5 - muñeca.y) * 180.0        # Pitch (-90 a +90)
                self.angles_ready.emit(round(q1, 1), round(q2, 1))

            # FPS suave
            now = time.time()
            fps_instant = 1.0 / max(now - prev_time, 1e-5)
            prev_time = now
            fps_smooth = 0.9 * fps_smooth + 0.1 * fps_instant

            self.metrics_ready.emit(fps_smooth, latencia_ms, gesto_activo)

            # Convertir frame de OpenCV (BGR) a QImage para la GUI
            rgb_render = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            bytes_per_line = 3 * w
            q_img = QImage(rgb_render.data, w, h, bytes_per_line, QImage.Format_RGB888).copy()
            self.frame_ready.emit(q_img)

        # Liberar recursos al detener
        cap.release()
        hand_detector.close()
        pose_detector.close()
        self.status_message.emit("Cámara y detectores detenidos limpiamente.")

    def stop(self):
        """Detiene la ejecución del hilo de forma segura."""
        self._running = False
        self.wait(1000)
