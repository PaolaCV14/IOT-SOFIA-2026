import time
import cv2
import mediapipe as mp

from mediapipe.tasks import python
from mediapipe.tasks.python import vision
from mediapipe.tasks.python.vision import (
    HandLandmarksConnections,
    PoseLandmarksConnections
)


# ----------------------------------------
# 1. FUNCIONES AUXILIARES
# ----------------------------------------

def distancia_3d(p1, p2):
    return (
        (p1.x - p2.x) ** 2 +
        (p1.y - p2.y) ** 2 +
        (p1.z - p2.z) ** 2
    ) ** 0.5


def detectar_corazon(hand_results):

    # Se requieren exactamente dos manos
    if len(hand_results.hand_landmarks) != 2:
        return False

    mano1 = hand_results.hand_landmarks[0]
    mano2 = hand_results.hand_landmarks[1]

    # Landmarks importantes
    indice1 = mano1[8]
    pulgar1 = mano1[4]

    indice2 = mano2[8]
    pulgar2 = mano2[4]

    # Distancias entre los puntos
    d_indices = distancia_3d(indice1, indice2)
    d_pulgares = distancia_3d(pulgar1, pulgar2)

    d_mano1 = distancia_3d(indice1, pulgar1)
    d_mano2 = distancia_3d(indice2, pulgar2)

    # Umbrales iniciales
    indices_juntos = d_indices < 0.12
    pulgares_juntos = d_pulgares < 0.12

    dedos_forman_arco = (
        d_mano1 < 0.25 and
        d_mano2 < 0.25
    )

    return (
        indices_juntos and
        pulgares_juntos and
        dedos_forman_arco
    )


# ----------------------------------------
# 2. RUTAS DE MODELOS
# ----------------------------------------

hand_model_path = "models/hand_landmarker.task"
pose_model_path = "models/pose_landmarker_lite.task"


# ----------------------------------------
# 3. CONFIGURACIÓN DE MANOS
# ----------------------------------------

hand_base_options = python.BaseOptions(
    model_asset_path=hand_model_path
)

hand_options = vision.HandLandmarkerOptions(
    base_options=hand_base_options,
    running_mode=vision.RunningMode.VIDEO,
    num_hands=2,
    min_hand_detection_confidence=0.7,
    min_hand_presence_confidence=0.7,
    min_tracking_confidence=0.7
)

hand_detector = vision.HandLandmarker.create_from_options(
    hand_options
)


# ----------------------------------------
# 4. CONFIGURACIÓN DEL CUERPO
# ----------------------------------------

pose_base_options = python.BaseOptions(
    model_asset_path=pose_model_path
)

pose_options = vision.PoseLandmarkerOptions(
    base_options=pose_base_options,
    running_mode=vision.RunningMode.VIDEO,
    min_pose_detection_confidence=0.7,
    min_pose_presence_confidence=0.7,
    min_tracking_confidence=0.7
)

pose_detector = vision.PoseLandmarker.create_from_options(
    pose_options
)


# ----------------------------------------
# 5. INICIALIZAR CÁMARA
# ----------------------------------------

cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("No se pudo abrir la cámara")
    exit()

print(
    "Cámara iniciada correctamente "
    "(2 manos + esqueleto corporal)."
)

print("Presiona Q para salir.")

start_time = time.time()

# Contador para confirmar el gesto durante varios frames
frames_corazon = 0


# ----------------------------------------
# 6. CICLO PRINCIPAL
# ----------------------------------------

while True:

    # Capturar frame
    ret, frame = cap.read()

    if not ret:
        print("No se pudo leer la cámara")
        break

    # Efecto espejo
    frame = cv2.flip(frame, 1)

    h, w, _ = frame.shape

    # Convertir BGR a RGB
    rgb_frame = cv2.cvtColor(
        frame,
        cv2.COLOR_BGR2RGB
    )

    # Crear imagen compatible con MediaPipe
    mp_image = mp.Image(
        image_format=mp.ImageFormat.SRGB,
        data=rgb_frame
    )

    # Timestamp para modo VIDEO
    frame_timestamp_ms = int(
        (time.time() - start_time) * 1000
    )

    # Detectar manos y cuerpo
    hand_results = hand_detector.detect_for_video(
        mp_image,
        frame_timestamp_ms
    )

    pose_results = pose_detector.detect_for_video(
        mp_image,
        frame_timestamp_ms
    )


    # ----------------------------------------
    # 7. DIBUJAR ESQUELETO DEL CUERPO
    # ----------------------------------------

    if pose_results.pose_landmarks:

        pose = pose_results.pose_landmarks[0]

        # Conexiones del cuerpo
        for conn in PoseLandmarksConnections.POSE_LANDMARKS:

            pt1 = pose[conn.start]
            pt2 = pose[conn.end]

            cv2.line(
                frame,
                (int(pt1.x * w), int(pt1.y * h)),
                (int(pt2.x * w), int(pt2.y * h)),
                (0, 255, 255),
                2
            )

        # Puntos de las articulaciones
        for landmark in pose:

            cv2.circle(
                frame,
                (
                    int(landmark.x * w),
                    int(landmark.y * h)
                ),
                4,
                (0, 200, 255),
                -1
            )


    # ----------------------------------------
    # 8. DIBUJAR ESQUELETO DE LAS MANOS
    # ----------------------------------------

    if hand_results.hand_landmarks:

        for idx, hand in enumerate(
            hand_results.hand_landmarks
        ):

            # Conexiones de los dedos
            for conn in HandLandmarksConnections.HAND_CONNECTIONS:

                pt1 = hand[conn.start]
                pt2 = hand[conn.end]

                cv2.line(
                    frame,
                    (int(pt1.x * w), int(pt1.y * h)),
                    (int(pt2.x * w), int(pt2.y * h)),
                    (0, 255, 0),
                    2
                )

            # Puntos de los dedos
            for landmark in hand:

                cv2.circle(
                    frame,
                    (
                        int(landmark.x * w),
                        int(landmark.y * h)
                    ),
                    4,
                    (0, 255, 128),
                    -1
                )

            # Coordenadas de la muñeca
            wrist = hand[0]

            print(
                f"Mano #{idx + 1} (Muñeca) -> "
                f"x={wrist.x:.3f}, "
                f"y={wrist.y:.3f}, "
                f"z={wrist.z:.3f}"
            )


    # ----------------------------------------
    # 9. DETECCIÓN DEL CORAZÓN
    # ----------------------------------------

    if detectar_corazon(hand_results):

        frames_corazon += 1

    else:

        frames_corazon = 0


    # Confirmar gesto después de varios frames consecutivos
    if frames_corazon >= 5:

        cv2.putText(
            frame,
            "CORAZON DETECTADO",
            (30, 50),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 0, 255),
            2
        )

        print("CORAZON DETECTADO")


    # ----------------------------------------
    # 10. MOSTRAR RESULTADO
    # ----------------------------------------

    cv2.imshow(
        "SOFIA - Vision (2 Manos y Esqueleto de Cuerpo)",
        frame
    )

    # Salir presionando Q
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break


# ----------------------------------------
# 11. LIBERAR RECURSOS
# ----------------------------------------

cap.release()
cv2.destroyAllWindows()

hand_detector.close()
pose_detector.close()