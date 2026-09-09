import time
import cv2
import mediapipe as mp

from mediapipe.tasks import python
from mediapipe.tasks.python import vision
from mediapipe.tasks.python.vision import HandLandmarksConnections, PoseLandmarksConnections

# ----------------------------------------
# 1. RUTAS DE MODELOS
# ----------------------------------------
hand_model_path = "models/hand_landmarker.task"
pose_model_path = "models/pose_landmarker_lite.task"

# ----------------------------------------
# 2. CONFIGURACIÓN MANOS (2 MANOS - MODO VIDEO)
# ----------------------------------------
hand_base_options = python.BaseOptions(model_asset_path=hand_model_path)
hand_options = vision.HandLandmarkerOptions(
    base_options=hand_base_options,
    running_mode=vision.RunningMode.VIDEO,
    num_hands=2,  # <--- Habilitar detección de 2 manos
    min_hand_detection_confidence=0.7,
    min_hand_presence_confidence=0.7,
    min_tracking_confidence=0.7
)
hand_detector = vision.HandLandmarker.create_from_options(hand_options)

# ----------------------------------------
# 3. CONFIGURACIÓN CUERPO (MODO VIDEO)
# ----------------------------------------
pose_base_options = python.BaseOptions(model_asset_path=pose_model_path)
pose_options = vision.PoseLandmarkerOptions(
    base_options=pose_base_options,
    running_mode=vision.RunningMode.VIDEO,
    min_pose_detection_confidence=0.7,
    min_pose_presence_confidence=0.7,
    min_tracking_confidence=0.7
)
pose_detector = vision.PoseLandmarker.create_from_options(pose_options)

# ----------------------------------------
# 4. INICIALIZAR CÁMARA
# ----------------------------------------
cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("No se pudo abrir la cámara")
    exit()

print("Cámara iniciada correctamente (2 Manos + Esqueleto de Cuerpo). Presiona Q para salir.")

start_time = time.time()

while True:
    ret, frame = cap.read()

    if not ret:
        print("No se pudo leer la cámara")
        break

    # Espejo
    frame = cv2.flip(frame, 1)
    h, w, _ = frame.shape

    # BGR -> RGB
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    # Convertir a imagen de MediaPipe
    mp_image = mp.Image(
        image_format=mp.ImageFormat.SRGB,
        data=rgb_frame
    )

    # Timestamp en milisegundos para modo VIDEO
    frame_timestamp_ms = int((time.time() - start_time) * 1000)

    # Detectar manos y cuerpo para video
    hand_results = hand_detector.detect_for_video(mp_image, frame_timestamp_ms)
    pose_results = pose_detector.detect_for_video(mp_image, frame_timestamp_ms)

    # ----------------------------------------
    # DIBUJAR ESQUELETO DE CUERPO (AMARILLO)
    # ----------------------------------------
    if pose_results.pose_landmarks:
        pose = pose_results.pose_landmarks[0]

        # 1. Dibujar conexiones / huesos del cuerpo
        for conn in PoseLandmarksConnections.POSE_LANDMARKS:
            pt1 = pose[conn.start]
            pt2 = pose[conn.end]
            cv2.line(
                frame,
                (int(pt1.x * w), int(pt1.y * h)),
                (int(pt2.x * w), int(pt2.y * h)),
                (0, 255, 255),  # Amarillo
                2
            )

        # 2. Dibujar articulaciones / puntos del cuerpo
        for landmark in pose:
            cv2.circle(
                frame,
                (int(landmark.x * w), int(landmark.y * h)),
                4,
                (0, 200, 255),  # Naranja/Amarillo
                -1
            )

    # ----------------------------------------
    # DIBUJAR ESQUELETO DE MANOS (VERDE)
    # ----------------------------------------
    if hand_results.hand_landmarks:
        for idx, hand in enumerate(hand_results.hand_landmarks):
            # 1. Dibujar conexiones / huesos de los dedos
            for conn in HandLandmarksConnections.HAND_CONNECTIONS:
                pt1 = hand[conn.start]
                pt2 = hand[conn.end]
                cv2.line(
                    frame,
                    (int(pt1.x * w), int(pt1.y * h)),
                    (int(pt2.x * w), int(pt2.y * h)),
                    (0, 255, 0),  # Verde
                    2
                )

            # 2. Dibujar articulaciones / puntos de los dedos
            for landmark in hand:
                cv2.circle(
                    frame,
                    (int(landmark.x * w), int(landmark.y * h)),
                    4,
                    (0, 255, 128),  # Verde claro
                    -1
                )

            # Imprimir coordenadas de la muñeca de cada mano
            wrist = hand[0]
            print(
                f"Mano #{idx+1} (Muñeca) -> "
                f"x={wrist.x:.3f}, "
                f"y={wrist.y:.3f}, "
                f"z={wrist.z:.3f}"
            )

    # Mostrar cámara
    cv2.imshow(
        "SOFIA - Vision (2 Manos y Esqueleto de Cuerpo)",
        frame
    )

    # Q para salir
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

# Limpieza
cap.release()
cv2.destroyAllWindows()

# Cerrar detectores
hand_detector.close()
pose_detector.close()