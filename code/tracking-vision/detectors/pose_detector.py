from mediapipe.tasks import python
from mediapipe.tasks.python import vision

# ==============================================================
# DETECTOR DE CUERPO - GOOGLE MEDIAPIPE (33 PUNTOS)
# ==============================================================

class PoseDetector:
    def __init__(self, model_path="models/pose_landmarker_lite.task"):
        """Configura el modelo lite de postura para detección rápida en CPU."""
        options = vision.PoseLandmarkerOptions(
            base_options=python.BaseOptions(model_asset_path=model_path),
            running_mode=vision.RunningMode.VIDEO,
            min_pose_detection_confidence=0.7, # 70% certeza para encontrar el cuerpo
            min_pose_presence_confidence=0.7,  # 70% certeza de permanencia
            min_tracking_confidence=0.7        # 70% certeza en el tracking
        )
        self.detector = vision.PoseLandmarker.create_from_options(options)

    def detect(self, image, timestamp_ms):
        """Procesa un frame y devuelve los 33 landmarks corporales en 3D."""
        return self.detector.detect_for_video(image, timestamp_ms)

    def close(self):
        """Libera la memoria del modelo al cerrar."""
        self.detector.close()