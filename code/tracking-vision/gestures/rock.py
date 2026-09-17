from .finger_utils import es_puno

class RockGesture:
    """Gesto de Roca (puño cerrado estático)."""

    def __init__(self, min_frames=4):
        self.frames = 0
        self.min_frames = min_frames

    def detect(self, hand_results):
        if not hand_results.hand_landmarks:
            self.frames = 0
            return False

        for mano in hand_results.hand_landmarks:
            if es_puno(mano):
                self.frames += 1
                return self.frames >= self.min_frames

        self.frames = 0
        return False
