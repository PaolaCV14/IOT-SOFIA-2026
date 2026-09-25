# ==============================================================
# GESTO DINÁMICO: INTENCIÓN DE JUGAR PPT (3 GOLPES)
# El usuario pone una mano plana abajo como base y golpea 3 veces
# con el puño encima para empezar la partida ("Piedra, papel o tijera").
# ==============================================================

import time
from .finger_utils import es_mano_abierta, es_puno, distancia_3d

class RpsIntentGesture:
    """Detecta el conteo de 3 golpes rítmicos entre puño y palma abierta."""

    def __init__(self):
        self.pumps = 0          # Conteo de golpes completados (0 a 3)
        self.fase = "ARRIBA"    # Saber si el puño está arriba o ya bajó a la palma
        self.ultimo_tiempo = 0  # Momento en que ocurrió el último golpe
        self.hold = 0           # Cuadros para dejar el letrero final en pantalla
        self.ultimo_texto = ""  # Texto del conteo actual (1/3, 2/3, etc.)
        self.feedback_hold = 0  # Evita que parpadee si se pierde la mano 1 frame

    def detect(self, hand_results):
        # 1. Si ya se dieron los 3 golpes, dejamos el mensaje unos segundos en pantalla
        if self.hold > 0:
            self.hold -= 1
            return True, "¡LISTO PARA JUGAR PPT!"

        # Si no se ven 2 manos, o la cámara pierde una un instante, no borramos el progreso de golpe
        if not hand_results.hand_landmarks or len(hand_results.hand_landmarks) < 2:
            if self.feedback_hold > 0 and self.pumps > 0:
                self.feedback_hold -= 1
                return True, self.ultimo_texto
            return False, ""

        m1, m2 = hand_results.hand_landmarks[0], hand_results.hand_landmarks[1]

        # Identificamos cuál mano es la palma plana (base) y cuál es el puño
        palma, puno = None, None
        if es_mano_abierta(m1) and es_puno(m2):
            palma, puno = m1, m2
        elif es_mano_abierta(m2) and es_puno(m1):
            palma, puno = m2, m1
        else:
            # Si rompen la pose pero estamos en medio de golpes, damos gracia de 15 frames
            if self.feedback_hold > 0 and self.pumps > 0:
                self.feedback_hold -= 1
                return True, self.ultimo_texto
            if time.time() - self.ultimo_tiempo > 1.5:
                self.pumps = 0
                self.fase = "ARRIBA"
            return False, ""

        ahora = time.time()
        # Distancia 3D entre el centro del puño (nudillo 9) y el centro de la palma (landmark 9)
        d_puno_palma = distancia_3d(puno[9], palma[9])

        # Timeout de 2 segundos entre golpe y golpe
        if ahora - self.ultimo_tiempo > 2.0:
            self.pumps = 0
            self.fase = "ARRIBA"

        # Paso A: El puño baja y toca o se acerca a la palma abierta (< 0.17)
        if self.fase == "ARRIBA" and d_puno_palma < 0.17:
            self.fase = "ABAJO"

        # Paso B: El puño se despega hacia arriba (> 0.20) -> ¡Golpe registrado!
        elif self.fase == "ABAJO" and d_puno_palma > 0.20:
            self.fase = "ARRIBA"
            self.pumps += 1
            self.ultimo_tiempo = ahora

            # ¿Completó los 3 toques?
            if self.pumps >= 3:
                self.pumps = 0
                self.hold = 60  # Visible por 2 segundos
                return True, "¡LISTO PARA JUGAR PPT!"

        # Estabilizamos el cartel activo durante al menos 12 frames
        self.feedback_hold = 12
        if self.pumps > 0:
            self.ultimo_texto = f"INTENCION PPT ({self.pumps}/3)"
        else:
            self.ultimo_texto = "PPT: GOLPEA EL PUÑO 3 VECES"

        return True, self.ultimo_texto
