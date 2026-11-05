"""
Mapeo de posturas reconocidas a comandos de SOFIA.

Convierte la etiqueta de gesto que emite VisionWorker (una por frame)
en, como mucho, un disparo de rutina por postura realizada. No depende
de Qt para poder probarse de forma aislada.

Reglas de disparo:
- Posturas DINAMICAS (SALUDO, SWIPE, PPT): el detector ya confirma el
  movimiento con varios frames; se disparan en el flanco de subida.
- Posturas ESTATICAS (CORAZON, TIJERA, PAPEL, ROCA): deben mantenerse
  HOLD_S segundos con la muneca quieta (rango < MAX_MOVIMIENTO_GRADOS).
  Esto evita, por ejemplo, que la mano abierta de un saludo o swipe en
  curso dispare PAPEL, o que un frame aislado mal clasificado dispare
  una rutina.
- Tras un disparo la postura debe soltarse (cambiar de etiqueta) antes
  de volver a dispararse, y se respeta un tiempo de enfriamiento global.
"""

import collections
import time
import unicodedata


# Postura -> rutina en el ESP32 (ver RUTINAS en ble_sender.py)
POSTURA_A_RUTINA = {
    "SALUDO": "SALUDO",
    "CORAZON": "CORAZON",
    "TIJERA": "BAILE",
    "SWIPE": "NEGAR",
    "ROCA": "CENTRAR",
    "PAPEL": "REPOSO",
    "PPT": "PPT",
}

POSTURAS_DINAMICAS = {"SALUDO", "SWIPE", "PPT"}
POSTURAS_ESTATICAS = {"CORAZON", "TIJERA", "PAPEL", "ROCA"}

HOLD_S = 0.6                   # Tiempo que debe sostenerse una postura estática
MAX_MOVIMIENTO_GRADOS = 12.0   # Rango máximo de la muñeca (escala de q_raw, ±90°)
COOLDOWN_S = 1.0               # Pausa mínima entre disparos


def normalizar_texto(texto):
    """Mayúsculas sin acentos ni signos de exclamación."""
    texto = unicodedata.normalize("NFD", str(texto))
    texto = "".join(c for c in texto if unicodedata.category(c) != "Mn")
    return texto.upper().replace("¡", "").replace("!", "").strip()


def clasificar_gesto(etiqueta):
    """
    Traduce la etiqueta de VisionWorker a una postura canónica.

    Ejemplos: "HOLA! SALUDO" -> SALUDO, "SWIPE IZQUIERDA" -> SWIPE,
    "¡LISTO PARA JUGAR PPT!" -> PPT. Los textos de progreso de PPT
    ("INTENCION PPT (1/3)") y NINGUNO/PAUSADO retornan None.
    """
    texto = normalizar_texto(etiqueta)

    if "LISTO PARA JUGAR PPT" in texto:
        return "PPT"
    if "PPT" in texto:
        return None   # Conteo en progreso: aún no es una postura completa
    if "SALUDO" in texto or "HOLA" in texto:
        return "SALUDO"
    if "SWIPE" in texto:
        return "SWIPE"
    for postura in ("CORAZON", "TIJERA", "PAPEL", "ROCA"):
        if postura in texto:
            return postura
    return None


class PostureTrigger:
    """Máquina de disparo de comandos a partir de etiquetas por frame."""

    def __init__(self, hold_s=HOLD_S, max_mov=MAX_MOVIMIENTO_GRADOS,
                 cooldown_s=COOLDOWN_S, clock=time.monotonic):
        self.hold_s = hold_s
        self.max_mov = max_mov
        self.cooldown_s = cooldown_s
        self.clock = clock

        self._actual = None          # Postura vista en el frame anterior
        self._desde = 0.0            # Desde cuándo se ve sin interrupción
        self._disparada = False      # Ya se disparó esta aparición
        self._ultimo_disparo = -1e9
        self._muneca = collections.deque()   # (t, q1_raw, q2_raw)

    def registrar_muneca(self, q1_raw, q2_raw):
        """Guarda la posición de la muñeca para medir estabilidad."""
        ahora = self.clock()
        self._muneca.append((ahora, q1_raw, q2_raw))
        while self._muneca and ahora - self._muneca[0][0] > self.hold_s:
            self._muneca.popleft()

    def _muneca_estable(self):
        if len(self._muneca) < 2:
            return True   # Sin datos suficientes (p. ej. CORAZON con oclusión)
        q1 = [m[1] for m in self._muneca]
        q2 = [m[2] for m in self._muneca]
        return (max(q1) - min(q1)) <= self.max_mov and \
               (max(q2) - min(q2)) <= self.max_mov

    def reset(self):
        self._actual = None
        self._disparada = False

    def actualizar(self, etiqueta, bloqueado=False):
        """
        Procesa la etiqueta de un frame.

        bloqueado=True indica que hay una rutina en ejecución: no se
        dispara nada, pero se sigue el estado para no disparar en cuanto
        se libere con una postura que ya estaba sostenida.

        Retorna (postura, rutina) cuando corresponde disparar; si no, None.
        """
        ahora = self.clock()
        postura = clasificar_gesto(etiqueta)

        if postura != self._actual:
            self._actual = postura
            self._desde = ahora
            self._disparada = False

        if postura is None or self._disparada:
            return None

        if bloqueado:
            # La postura que se ve durante una rutina no se dispara después
            self._disparada = True
            return None

        if ahora - self._ultimo_disparo < self.cooldown_s:
            return None

        if postura in POSTURAS_ESTATICAS:
            if ahora - self._desde < self.hold_s:
                return None
            if not self._muneca_estable():
                return None

        self._disparada = True
        self._ultimo_disparo = ahora
        return postura, POSTURA_A_RUTINA[postura]
