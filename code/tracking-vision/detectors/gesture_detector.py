import math


class GestureDetector:

    def __init__(self):
        self.heart_frames = 0
        self.scissors_frames = 0
        self.paper_frames = 0
        self.rock_frames = 0

    # ----------------------------------------
    # DISTANCIA ENTRE DOS LANDMARKS
    # ----------------------------------------

    @staticmethod
    def distancia_3d(p1, p2):
        return (
            (p1.x - p2.x) ** 2 +
            (p1.y - p2.y) ** 2 +
            (p1.z - p2.z) ** 2
        ) ** 0.5

    # ----------------------------------------
    # DETECTAR SI UN DEDO ESTÁ DOBLADO
    # ----------------------------------------

    @staticmethod
    def dedo_doblado(mano, punta, articulacion):

        distancia_punta = GestureDetector.distancia_3d(
            mano[punta],
            mano[0]
        )

        distancia_articulacion = GestureDetector.distancia_3d(
            mano[articulacion],
            mano[0]
        )

        return distancia_punta < distancia_articulacion

    # ----------------------------------------
    # DETECTAR SI UN DEDO ESTÁ EXTENDIDO
    # ----------------------------------------

    @staticmethod
    def dedo_extendido(mano, punta, articulacion):

        return mano[punta].y < mano[articulacion].y

    # ----------------------------------------
    # DETECTAR CORAZÓN
    # ----------------------------------------

    def detectar_corazon(self, hand_results):

        if (
            not hand_results.hand_landmarks or
            len(hand_results.hand_landmarks) != 2
        ):
            self.heart_frames = 0
            return False

        mano1 = hand_results.hand_landmarks[0]
        mano2 = hand_results.hand_landmarks[1]

        indice1 = mano1[8]
        pulgar1 = mano1[4]

        indice2 = mano2[8]
        pulgar2 = mano2[4]

        d_indices = self.distancia_3d(
            indice1,
            indice2
        )

        d_pulgares = self.distancia_3d(
            pulgar1,
            pulgar2
        )

        d_mano1 = self.distancia_3d(
            indice1,
            pulgar1
        )

        d_mano2 = self.distancia_3d(
            indice2,
            pulgar2
        )

        indices_juntos = d_indices < 0.12

        pulgares_juntos = d_pulgares < 0.12

        dedos_forman_arco = (
            d_mano1 < 0.25 and
            d_mano2 < 0.25
        )

        cumple = (
            indices_juntos and
            pulgares_juntos and
            dedos_forman_arco
        )

        if cumple:
            self.heart_frames += 1
        else:
            self.heart_frames = 0

        return self.heart_frames >= 5
    # ----------------------------------------
    # DETECTAR TIJERA
    # ----------------------------------------

    def detectar_tijera(self, hand_results):

        if not hand_results.hand_landmarks:
            self.scissors_frames = 0
            return False

        for mano in hand_results.hand_landmarks:

            # Índice y medio extendidos
            indice_extendido = (
                mano[8].y < mano[6].y
            )

            medio_extendido = (
                mano[12].y < mano[10].y
            )

            # Anular y meñique doblados
            anular_doblado = (
                mano[16].y > mano[14].y
            )

            menique_doblado = (
                mano[20].y > mano[18].y
            )

            # Distancia entre índice y medio
            distancia_indice_medio = self.distancia_3d(
                mano[8],
                mano[12]
            )

            escala = self.distancia_3d(
                mano[0],
                mano[9]
            )

            if escala < 0.01:
                continue

            dedos_separados = (
                distancia_indice_medio > escala * 0.18
            )

            cumple = (
                indice_extendido and
                medio_extendido and
                anular_doblado and
                menique_doblado and
                dedos_separados
            )

            print(
                f"TIJERA | "
                f"Índice: {indice_extendido} | "
                f"Medio: {medio_extendido} | "
                f"Anular: {anular_doblado} | "
                f"Meñique: {menique_doblado} | "
                f"Separados: {dedos_separados} | "
                f"Resultado: {cumple}"
            )

            if cumple:
                self.scissors_frames += 1
                return self.scissors_frames >= 4

        self.scissors_frames = 0
        return False
    # ----------------------------------------
    # DETECTAR PAPEL
    # ----------------------------------------

    def detectar_papel(self, hand_results):

        if not hand_results.hand_landmarks:
            self.paper_frames = 0
            return False

        for mano in hand_results.hand_landmarks:

            # Índice extendido
            indice_extendido = (
                mano[8].y < mano[6].y
            )

            # Medio extendido
            medio_extendido = (
                mano[12].y < mano[10].y
            )

            # Anular extendido
            anular_extendido = (
                mano[16].y < mano[14].y
            )

            # Meñique extendido
            menique_extendido = (
                mano[20].y < mano[18].y
            )

            # Pulgar extendido
            pulgar_extendido = (
                self.distancia_3d(mano[4], mano[0])
                >
                self.distancia_3d(mano[3], mano[0])
            )

            cumple = (
                indice_extendido and
                medio_extendido and
                anular_extendido and
                menique_extendido and
                pulgar_extendido
            )

            print(
                f"PAPEL | "
                f"Índice: {indice_extendido} | "
                f"Medio: {medio_extendido} | "
                f"Anular: {anular_extendido} | "
                f"Meñique: {menique_extendido} | "
                f"Pulgar: {pulgar_extendido} | "
                f"Resultado: {cumple}"
            )

            if cumple:
                self.paper_frames += 1
                return self.paper_frames >= 3

        self.paper_frames = 0

        return False

    # ----------------------------------------
    # DETECTAR ROCA
    # ----------------------------------------

    # ----------------------------------------
    # DETECTAR ROCA
    # ----------------------------------------

    def detectar_roca(self, hand_results):

        if not hand_results.hand_landmarks:
            self.rock_frames = 0
            return False

        for mano in hand_results.hand_landmarks:

            # ----------------------------------------
            # LOS CUATRO DEDOS DEBEN ESTAR DOBLADOS
            # ----------------------------------------

            indice_doblado = (
                mano[8].y > mano[6].y
            )

            medio_doblado = (
                mano[12].y > mano[10].y
            )

            anular_doblado = (
                mano[16].y > mano[14].y
            )

            menique_doblado = (
                mano[20].y > mano[18].y
            )

            # ----------------------------------------
            # EL PULGAR DEBE ESTAR RECOGIDO
            # ----------------------------------------

            pulgar_retraido = (
                self.distancia_3d(mano[4], mano[0])
                <
                self.distancia_3d(mano[3], mano[0]) * 1.15
            )

            # ----------------------------------------
            # DISTANCIA ENTRE LAS PUNTAS DE LOS DEDOS
            # ----------------------------------------

            escala = self.distancia_3d(
                mano[0],
                mano[9]
            )

            if escala < 0.01:
                continue

            dedos_cerrados = (
                self.distancia_3d(mano[8], mano[0]) < escala * 2.2 and
                self.distancia_3d(mano[12], mano[0]) < escala * 2.2 and
                self.distancia_3d(mano[16], mano[0]) < escala * 2.2 and
                self.distancia_3d(mano[20], mano[0]) < escala * 2.2
            )

            cumple = (
                indice_doblado and
                medio_doblado and
                anular_doblado and
                menique_doblado and
                pulgar_retraido and
                dedos_cerrados
            )

            print(
                f"ROCA | "
                f"Índice: {indice_doblado} | "
                f"Medio: {medio_doblado} | "
                f"Anular: {anular_doblado} | "
                f"Meñique: {menique_doblado} | "
                f"Pulgar: {pulgar_retraido} | "
                f"Cerrados: {dedos_cerrados} | "
                f"Resultado: {cumple}"
            )

            if cumple:
                self.rock_frames += 1
                return self.rock_frames >= 4

        self.rock_frames = 0
        return False