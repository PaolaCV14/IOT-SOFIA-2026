# ==============================================================
# COORDINADOR DE GESTOS - PROYECTO SOFÍA
# Aquí juntamos todos los detectores de gestos para que desde
# el archivo main.py solo tengamos que llamar una función limpia.
# ==============================================================

from gestures import (
    HeartGesture,
    WaveGesture,
    RpsIntentGesture,
    ScissorsGesture,
    PaperGesture,
    RockGesture,
    SwipeGesture
)

class GestureDetector:
    """Clase principal que contiene las instancias de cada gesto."""

    def __init__(self):
        # Inicializamos cada detector individual
        self.heart = HeartGesture()
        self.wave = WaveGesture()
        self.rps_intent = RpsIntentGesture()
        self.swipe = SwipeGesture()
        self.scissors = ScissorsGesture()
        self.paper = PaperGesture()
        self.rock = RockGesture()

    # Métodos directos para consultar cada postura desde el ciclo principal
    def detectar_corazon(self, hand_results):
        return self.heart.detect(hand_results)

    def detectar_saludo(self, hand_results):
        return self.wave.detect(hand_results)

    def detectar_intencion_ppt(self, hand_results):
        return self.rps_intent.detect(hand_results)

    def detectar_swipe(self, hand_results):
        return self.swipe.detect(hand_results)

    def detectar_tijera(self, hand_results):
        return self.scissors.detect(hand_results)

    def detectar_papel(self, hand_results):
        return self.paper.detect(hand_results)

    def detectar_roca(self, hand_results):
        return self.rock.detect(hand_results)