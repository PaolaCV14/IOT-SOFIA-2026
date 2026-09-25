# ==============================================================
# DETECCIÓN DE POSTURA CORPORAL (POSE) CON MEDIAPIPE
# Carga el modelo ligero para obtener los 33 puntos del cuerpo
# (hombros, codos, muñecas, cara) sin saturar la CPU.
# ==============================================================

from mediapipe.tasks import python
from mediapipe.tasks.python import vision

class PoseDetector:
    def __init__(self, model_path="models/pose_landmarker_lite.task"):
        """Prepara el modelo lite de cuerpo para que corra rápido en cualquier laptop."""
        options = vision.PoseLandmarkerOptions(
            base_options=python.BaseOptions(model_asset_path=model_path),
            running_mode=vision.RunningMode.VIDEO,
            min_pose_detection_confidence=0.7, # 70% de certeza inicial
            min_pose_presence_confidence=0.7,  # 70% de que la persona sigue frente a la cámara
            min_tracking_confidence=0.7        # 70% para no perder el esqueleto entre cuadros
        )
        self.detector = vision.PoseLandmarker.create_from_options(options)

    def detect(self, image, timestamp_ms):
        """Procesa el frame actual y regresa los puntos del esqueleto."""
        return self.detector.detect_for_video(image, timestamp_ms)

    def close(self):
        """Cierra el modelo y libera recursos del sistema."""
        self.detector.close()