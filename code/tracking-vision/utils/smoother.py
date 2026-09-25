# ==============================================================
# FILTRO DE SUAVIZADO (SMOOTHING) - EMA (Exponential Moving Average)
# Reduce el jitter/vibración de landmarks de MediaPipe en tiempo real
# Basado en: y[k] = alpha * x[k] + (1 - alpha) * y[k-1]
# ==============================================================

class LandmarkPoint:
    """Representa un landmark con coordenadas normalizadas x, y, z."""
    __slots__ = ("x", "y", "z")
    def __init__(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z


class SmoothedHandResult:
    """Wrapper para mantener compatibilidad 100% con .hand_landmarks."""
    def __init__(self, hand_landmarks):
        self.hand_landmarks = hand_landmarks


class SmoothedPoseResult:
    """Wrapper para mantener compatibilidad 100% con .pose_landmarks."""
    def __init__(self, pose_landmarks):
        self.pose_landmarks = pose_landmarks


class LandmarkSmoother:
    """
    Filtro paso-bajo de primer orden (IIR / EMA) para estabilizar
    las coordenadas 3D de articulaciones de manos y cuerpo.
    """

    def __init__(self, alpha=0.35):
        """
        alpha: Factor de suavizado entre 0.0 y 1.0
               - Valores pequeños (0.1 - 0.3): Mayor suavizado, menor temblor.
               - Valores moderados (0.35 - 0.5): Balance óptimo velocidad-suavidad.
        """
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
