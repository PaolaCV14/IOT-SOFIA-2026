# ==============================================================
# DETECCIÓN DE MANOS CON MEDIAPIPE (HASTA 2 MANOS)
# Carga el modelo de Google para ubicar los 21 puntos clave
# de cada mano que aparezca frente a la cámara.
# ==============================================================

from mediapipe.tasks import python
from mediapipe.tasks.python import vision

class HandDetector:
    def __init__(self, model_path="models/hand_landmarker.task"):
        """Prepara el modelo de MediaPipe en modo video para rastrear 2 manos."""
        options = vision.HandLandmarkerOptions(
            base_options=python.BaseOptions(model_asset_path=model_path),
            running_mode=vision.RunningMode.VIDEO,
            num_hands=2,                       # Queremos ver hasta 2 manos a la vez
            min_hand_detection_confidence=0.7, # 70% de confianza para encontrar la mano
            min_hand_presence_confidence=0.7,  # 70% para confirmar que sigue en cuadro
            min_tracking_confidence=0.7        # 70% para no perder los puntos al moverse
        )
        self.detector = vision.HandLandmarker.create_from_options(options)

    def detect(self, image, timestamp_ms):
        """Le pasa un cuadro a MediaPipe y regresa los 21 puntos de las manos."""
        return self.detector.detect_for_video(image, timestamp_ms)

    def close(self):
        """Cierra el detector para no dejar memoria colgada."""
        self.detector.close()