import math


class GestureDetector:

    def __init__(self):
        self.heart_frames = 0

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
    # DETECTAR CORAZÓN
    # ----------------------------------------

    def detectar_corazon(self, hand_results):

        # Se requieren exactamente dos manos
        if (
            not hand_results.hand_landmarks or
            len(hand_results.hand_landmarks) != 2
        ):
            self.heart_frames = 0
            return False

        mano1 = hand_results.hand_landmarks[0]
        mano2 = hand_results.hand_landmarks[1]

        # ----------------------------------------
        # LANDMARKS IMPORTANTES
        # ----------------------------------------

        indice1 = mano1[8]
        pulgar1 = mano1[4]

        indice2 = mano2[8]
        pulgar2 = mano2[4]

        # ----------------------------------------
        # DISTANCIAS ENTRE LOS PUNTOS
        # ----------------------------------------

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

        # ----------------------------------------
        # IMPRIMIR COORDENADAS Y DISTANCIAS
        # ----------------------------------------

        print("\n" + "=" * 50)

        print("MANOS DETECTADAS: 2")

        print(
            f"Índice 1: x={indice1.x:.3f}, "
            f"y={indice1.y:.3f}, "
            f"z={indice1.z:.3f}"
        )

        print(
            f"Pulgar 1: x={pulgar1.x:.3f}, "
            f"y={pulgar1.y:.3f}, "
            f"z={pulgar1.z:.3f}"
        )

        print(
            f"Índice 2: x={indice2.x:.3f}, "
            f"y={indice2.y:.3f}, "
            f"z={indice2.z:.3f}"
        )

        print(
            f"Pulgar 2: x={pulgar2.x:.3f}, "
            f"y={pulgar2.y:.3f}, "
            f"z={pulgar2.z:.3f}"
        )

        print("\nDISTANCIAS:")

        print(f"Índices:   {d_indices:.4f}")
        print(f"Pulgares:  {d_pulgares:.4f}")
        print(f"Mano 1:    {d_mano1:.4f}")
        print(f"Mano 2:    {d_mano2:.4f}")

        # ----------------------------------------
        # UMBRALES ORIGINALES
        # ----------------------------------------

        indices_juntos = d_indices < 0.12

        pulgares_juntos = d_pulgares < 0.12

        dedos_forman_arco = (
            d_mano1 < 0.25 and
            d_mano2 < 0.25
        )

        # ----------------------------------------
        # MOSTRAR CONDICIONES
        # ----------------------------------------

        print("\nCONDICIONES:")

        print(f"indices_juntos:    {indices_juntos}")
        print(f"pulgares_juntos:   {pulgares_juntos}")
        print(f"dedos_forman_arco: {dedos_forman_arco}")

        cumple = (
            indices_juntos and
            pulgares_juntos and
            dedos_forman_arco
        )

        print(f"\n¿CUMPLE?: {cumple}")

        # ----------------------------------------
        # CONFIRMACIÓN TEMPORAL
        # ----------------------------------------

        if cumple:
            self.heart_frames += 1
        else:
            self.heart_frames = 0

        print(f"Heart frames: {self.heart_frames}")
        print("=" * 50)

        return self.heart_frames >= 5