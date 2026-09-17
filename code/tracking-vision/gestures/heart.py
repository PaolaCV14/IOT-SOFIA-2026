from .finger_utils import distancia_3d

class HeartGesture:
    """Gesto de Corazón formado juntando ambas manos."""

    def __init__(self, min_frames=5):
        self.frames = 0
        self.min_frames = min_frames

    def detect(self, hand_results):
        if not hand_results.hand_landmarks or len(hand_results.hand_landmarks) != 2:
            self.frames = 0
            return False

        m1, m2 = hand_results.hand_landmarks[0], hand_results.hand_landmarks[1]
        indices = distancia_3d(m1[8], m2[8]) < 0.12
        pulgares = distancia_3d(m1[4], m2[4]) < 0.12
        arco = (distancia_3d(m1[8], m1[4]) < 0.25 and distancia_3d(m2[8], m2[4]) < 0.25)

        if indices and pulgares and arco:
            self.frames += 1
            return self.frames >= self.min_frames

        self.frames = 0
        return False
