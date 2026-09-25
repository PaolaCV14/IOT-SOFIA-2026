# ==============================================================
# GESTO ESTÁTICO: PAPEL / MANO ABIERTA
# Detecta cuando el usuario muestra la mano quieta con los 5 dedos estirados.
# ==============================================================

from .finger_utils import es_mano_abierta

class PaperGesture:
    """Detecta mano abierta sostenida."""

    def __init__(self, min_frames=3):
        self.frames = 0
        self.min_frames = min_frames  # Mínimo de cuadros seguidos para confirmar

    def detect(self, hand_results):
        if not hand_results.hand_landmarks:
            self.frames = 0
            return False

        for mano in hand_results.hand_landmarks:
            if es_mano_abierta(mano):
                self.frames += 1
                return self.frames >= self.min_frames

        self.frames = 0
        return False
