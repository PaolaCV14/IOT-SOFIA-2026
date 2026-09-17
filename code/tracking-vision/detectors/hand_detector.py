from mediapipe.tasks import python
from mediapipe.tasks.python import vision

# ==============================================================
# DETECTOR DE MANOS - GOOGLE MEDIAPIPE (HASTA 2 MANOS)
# ==============================================================

class HandDetector:
    def __init__(self, model_path="models/hand_landmarker.task"):
        """Configura el modelo para detectar hasta 2 manos en tiempo real (Modo Video)."""
        options = vision.HandLandmarkerOptions(
            base_options=python.BaseOptions(model_asset_path=model_path),
            running_mode=vision.RunningMode.VIDEO,
            num_hands=2,                       # Detecta izquierda y derecha simultáneamente
            min_hand_detection_confidence=0.7, # 70% de certeza para detectar la mano
            min_hand_presence_confidence=0.7,  # 70% de certeza de que sigue ahí
            min_tracking_confidence=0.7        # 70% de certeza para seguir los 21 puntos
        )
        self.detector = vision.HandLandmarker.create_from_options(options)

    def detect(self, image, timestamp_ms):
        """Procesa un frame y devuelve los 21 puntos 3D de cada mano."""
        return self.detector.detect_for_video(image, timestamp_ms)

    def close(self):
        """Libera la memoria del modelo al cerrar."""
        self.detector.close()