from .finger_utils import dedo_extendido, dedo_doblado, distancia_3d

class ScissorsGesture:
    """Gesto de Tijera (dedos índice y medio extendidos y separados)."""

    def __init__(self, min_frames=4):
        self.frames = 0
        self.min_frames = min_frames

    def detect(self, hand_results):
        if not hand_results.hand_landmarks:
            self.frames = 0
            return False

        for mano in hand_results.hand_landmarks:
            escala = distancia_3d(mano[0], mano[9])
            if escala < 0.01:
                continue

            indice = dedo_extendido(mano, 8, 6, 5)
            medio = dedo_extendido(mano, 12, 10, 9)
            anular = dedo_doblado(mano, 16, 14, 13)
            menique = dedo_doblado(mano, 20, 18, 17)
            abiertos = distancia_3d(mano[8], mano[12]) > (escala * 0.18)

            if indice and medio and anular and menique and abiertos:
                self.frames += 1
                return self.frames >= self.min_frames

        self.frames = 0
        return False
