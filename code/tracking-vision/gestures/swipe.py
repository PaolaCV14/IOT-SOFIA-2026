import time
from .finger_utils import es_mano_abierta, distancia_3d

class SwipeGesture:
    """
    Gesto Dinámico 3: Deslizamiento lateral rápido (Swipe / Cambio de página).
    Detecta un desplazamiento horizontal unidireccional y veloz de la mano abierta.
    Retorna (detectado, dirección: "IZQUIERDA" | "DERECHA").
    """

    def __init__(self, min_dx=0.20, max_duration=0.50):
        self.min_dx = min_dx              # Distancia mínima normalizada (~20% del ancho)
        self.max_duration = max_duration  # Tiempo máximo para considerarlo un swipe rápido
        self.tracking = False             # Si estamos rastreando un movimiento
        self.x_inicio = None
        self.t_inicio = 0
        self.hold = 0                     # Frames para mantener el letrero activo
        self.ultimo_resultado = ""

    def detect(self, hand_results):
        # 1. Si ya se activó, mantener en pantalla unos frames
        if self.hold > 0:
            self.hold -= 1
            return True, self.ultimo_resultado

        if not hand_results:
            self._reset()
            return False, ""

        # Extraemos la lista de manos (sea resultado MediaPipe, SmoothedHandResult o lista directa)
        hand_landmarks = getattr(hand_results, "hand_landmarks", hand_results)
        if not hand_landmarks:
            self._reset()
            return False, ""

        mano = hand_landmarks[0]
        ahora = time.time()

        # Solo evaluamos si la mano está abierta
        if not es_mano_abierta(mano):
            self._reset()
            return False, ""

        x_actual = mano[9].x  # Centro de la palma

        # Iniciar tracking del movimiento
        if not self.tracking:
            self.tracking = True
            self.x_inicio = x_actual
            self.t_inicio = ahora
            return False, ""

        # Verificar si excedió el tiempo límite (si es lento, no es swipe)
        dt = ahora - self.t_inicio
        if dt > self.max_duration:
            # Reiniciar ancla a la posición actual
            self.x_inicio = x_actual
            self.t_inicio = ahora
            return False, ""

        dx = x_actual - self.x_inicio
        # Evaluamos si recorrió suficiente distancia rápidamente
        if abs(dx) >= self.min_dx:
            # En video espejado: dx > 0 es hacia la derecha, dx < 0 hacia la izquierda
            direccion = "SWIPE DERECHA" if dx > 0 else "SWIPE IZQUIERDA"
            self.ultimo_resultado = direccion
            self.hold = 25  # Visible por ~25 frames (~0.8 s)
            self._reset()
            return True, direccion

        return False, ""

    def _reset(self):
        self.tracking = False
        self.x_inicio = None
        self.t_inicio = 0
