# ==============================================================
# GESTO ESTÁTICO: CORAZÓN CON DOS MANOS
# Detecta cuando el usuario junta ambas manos para hacer la
# forma de un corazón con los dedos índice y pulgares.
# ==============================================================

from .finger_utils import distancia_3d

class HeartGesture:
    """Detecta la forma de corazón juntando las dos manos."""

    def __init__(self, min_frames=5):
        self.frames = 0
        self.min_frames = min_frames  # Cuadros consecutivos que debe mantenerse para no parpadear

    def detect(self, hand_results):
        # Necesitamos forzosamente que se vean 2 manos
        if not hand_results.hand_landmarks or len(hand_results.hand_landmarks) != 2:
            self.frames = 0
            return False

        m1, m2 = hand_results.hand_landmarks[0], hand_results.hand_landmarks[1]
        
        # 1. Las puntas de los índices (punto 8) deben estar casi pegadas
        indices_juntos = distancia_3d(m1[8], m2[8]) < 0.12
        # 2. Las puntas de los pulgares (punto 4) también deben tocarse
        pulgares_juntos = distancia_3d(m1[4], m2[4]) < 0.12
        # 3. Cada mano debe formar la curvatura (índice y pulgar curvados)
        forma_arco = (distancia_3d(m1[8], m1[4]) < 0.25 and distancia_3d(m2[8], m2[4]) < 0.25)

        if indices_juntos and pulgares_juntos and forma_arco:
            self.frames += 1
            return self.frames >= self.min_frames

        self.frames = 0
        return False
