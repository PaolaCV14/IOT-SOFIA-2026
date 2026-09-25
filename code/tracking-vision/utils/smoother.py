# ==============================================================
# FILTRO DE SUAVIZADO (SMOOTHING) - PROYECTO SOFÍA
# Este archivo ayuda a quitarle el temblor o "ruido" a los puntos
# de la mano y del cuerpo que nos da la cámara web.
#
# ¿Cómo funciona?
# En vez de saltar de golpe a la nueva coordenada, calculamos:
# punto_filtrado = (alpha * nuevo) + ((1 - alpha) * anterior)
# Así el esqueleto se mueve fluido y no parece que tiembla la mano.
# ==============================================================

class LandmarkPoint:
    """Guarda un punto tridimensional simple con coordenadas x, y, z."""
    __slots__ = ("x", "y", "z")
    def __init__(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z


class SmoothedHandResult:
    """
    Guarda los puntos de las manos ya suavizados.
    Tiene los métodos mágicos (__getitem__, __len__, etc.) para que se pueda
    usar como una lista normal o acceder mediante .hand_landmarks sin errores.
    """
    def __init__(self, hand_landmarks):
        self.hand_landmarks = hand_landmarks

    def __getitem__(self, idx):
        return self.hand_landmarks[idx]

    def __len__(self):
        return len(self.hand_landmarks)

    def __bool__(self):
        return bool(self.hand_landmarks)

    def __iter__(self):
        return iter(self.hand_landmarks)


class SmoothedPoseResult:
    """Guarda los puntos del cuerpo ya suavizados con soporte de lista y atributo."""
    def __init__(self, pose_landmarks):
        self.pose_landmarks = pose_landmarks

    def __getitem__(self, idx):
        return self.pose_landmarks[idx]

    def __len__(self):
        return len(self.pose_landmarks)

    def __bool__(self):
        return bool(self.pose_landmarks)

    def __iter__(self):
        return iter(self.pose_landmarks)


class LandmarkSmoother:
    """
    Filtro paso-bajo sencillo (EMA) para manos y cuerpo.
    """

    def __init__(self, alpha=0.35):
        # alpha controla qué tanto peso le damos a la medición actual vs la anterior:
        # - alpha = 0.35: buen balance entre no tener lag y que no vibre.
        self.alpha = alpha
        self.manos_previas = []
        self.pose_previa = None

    def smooth_hands(self, hand_results):
        """Aplica EMA sobre cada landmark de cada mano detectada."""
        if not hand_results or not hand_results.hand_landmarks:
            self.manos_previas.clear()
            return SmoothedHandResult([])

        manos_filtradas = []
        for i, mano in enumerate(hand_results.hand_landmarks):
            tiene_previo = i < len(self.manos_previas) and len(self.manos_previas[i]) == len(mano)
            mano_suavizada = []

            for j, lm in enumerate(mano):
                if tiene_previo:
                    prev = self.manos_previas[i][j]
                    sx = self.alpha * lm.x + (1.0 - self.alpha) * prev.x
                    sy = self.alpha * lm.y + (1.0 - self.alpha) * prev.y
                    sz = self.alpha * lm.z + (1.0 - self.alpha) * prev.z
                    mano_suavizada.append(LandmarkPoint(sx, sy, sz))
                else:
                    mano_suavizada.append(LandmarkPoint(lm.x, lm.y, lm.z))

            manos_filtradas.append(mano_suavizada)

        self.manos_previas = manos_filtradas
        return SmoothedHandResult(manos_filtradas)

    def smooth_pose(self, pose_results):
        """Aplica EMA sobre los landmarks corporales de Pose."""
        if not pose_results or not pose_results.pose_landmarks:
            self.pose_previa = None
            return SmoothedPoseResult([])

        pose = pose_results.pose_landmarks[0]
        tiene_previo = self.pose_previa is not None and len(self.pose_previa) == len(pose)
        pose_suavizada = []

        for j, lm in enumerate(pose):
            if tiene_previo:
                prev = self.pose_previa[j]
                sx = self.alpha * lm.x + (1.0 - self.alpha) * prev.x
                sy = self.alpha * lm.y + (1.0 - self.alpha) * prev.y
                sz = self.alpha * lm.z + (1.0 - self.alpha) * prev.z
                pose_suavizada.append(LandmarkPoint(sx, sy, sz))
            else:
                pose_suavizada.append(LandmarkPoint(lm.x, lm.y, lm.z))

        self.pose_previa = pose_suavizada
        return SmoothedPoseResult([pose_suavizada])
