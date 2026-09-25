# ==============================================================
# GESTO ESTÁTICO: TIJERAS / SEÑAL DE LA PAZ
# Detecta cuando el usuario extiende los dedos índice y medio en "V"
# y mantiene el anular y meñique doblados.
# ==============================================================

from .finger_utils import dedo_extendido, dedo_doblado, distancia_3d

class ScissorsGesture:
    """Detecta tijera con índice y medio estirados y separados."""

    def __init__(self, min_frames=4):
        self.frames = 0
        self.min_frames = min_frames  # Requiere al menos 4 cuadros para confirmarlo

    def detect(self, hand_results):
        if not hand_results.hand_landmarks:
            self.frames = 0
            return False

        for mano in hand_results.hand_landmarks:
            tamano_mano = distancia_3d(mano[0], mano[9])
            if tamano_mano < 0.01:
                continue

            # Índice y medio deben estar bien estirados
            indice = dedo_extendido(mano, 8, 6, 5)
            medio = dedo_extendido(mano, 12, 10, 9)

            # Anular y meñique deben estar doblados hacia la palma
            anular = dedo_doblado(mano, 16, 14, 13)
            menique = dedo_doblado(mano, 20, 18, 17)

            # Debe haber separación clara entre el índice y el medio (forma de V)
            abiertos = distancia_3d(mano[8], mano[12]) > (tamano_mano * 0.18)

            if indice and medio and anular and menique and abiertos:
                self.frames += 1
                return self.frames >= self.min_frames

        self.frames = 0
        return False
