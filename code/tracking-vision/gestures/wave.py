from .finger_utils import es_mano_abierta

class WaveGesture:
    """Detecta saludo con la mano abierta oscilando de lado a lado."""

    def __init__(self):
        self.posiciones = []  # Historial X de la mano
        self.hold = 0         # Anti-parpadeo del cartel

    def detect(self, hand_results):
        if not hand_results.hand_landmarks:
            self.posiciones.clear()
            if self.hold > 0:
                self.hold -= 1
                return True
            return False

        mano = hand_results.hand_landmarks[0]
        if es_mano_abierta(mano):
            # Guardamos la posición horizontal de la palma (landmark 9)
            self.posiciones.append(mano[9].x)
            if len(self.posiciones) > 16:
                self.posiciones.pop(0)

            # Contamos cuántas veces cambió de dirección (izquierda <-> derecha)
            if len(self.posiciones) >= 8:
                dirs = [1 if (self.posiciones[i] - self.posiciones[i-1]) > 0.01 else -1 
                        for i in range(1, len(self.posiciones)) 
                        if abs(self.posiciones[i] - self.posiciones[i-1]) > 0.01]
                cambios = sum(1 for i in range(1, len(dirs)) if dirs[i] != dirs[i-1])
                amplitud = max(self.posiciones) - min(self.posiciones)

                # Al menos 3 cambios de sentido y movimiento lateral claro
                if cambios >= 3 and amplitud > 0.05:
                    self.hold = 12  # Mantiene el cartel activo unos frames
        else:
            self.posiciones.clear()

        if self.hold > 0:
            self.hold -= 1
            return True
        return False
