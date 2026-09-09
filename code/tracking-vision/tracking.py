import cv2
import mediapipe as mp

from mediapipe.tasks import python
from mediapipe.tasks.python import vision

# ----------------------------------------
# 1. RUTAS DE MODELOS
# ----------------------------------------
hand_model_path = "models/hand_landmarker.task"
pose_model_path = "models/pose_landmarker_lite.task"  # Asegúrate de tener este archivo

# ----------------------------------------
# 2. CONFIGURACIÓN MANOS
# ----------------------------------------
hand_base_options = python.BaseOptions(model_asset_path=hand_model_path)
hand_options = vision.HandLandmarkerOptions(
    base_options=hand_base_options,
    num_hands=1,
    min_hand_detection_confidence=0.7,
    min_hand_presence_confidence=0.7,
    min_tracking_confidence=0.7
)
hand_detector = vision.HandLandmarker.create_from_options(hand_options)

# ----------------------------------------
# 3. CONFIGURACIÓN CUERPO
# ----------------------------------------
pose_base_options = python.BaseOptions(model_asset_path=pose_model_path)
pose_options = vision.PoseLandmarkerOptions(
    base_options=pose_base_options,
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

print("Cámara iniciada. Presiona Q para salir.")

while True:

    ret, frame = cap.read()

    if not ret:
        print("No se pudo leer la cámara")
        break

    # Espejo
    frame = cv2.flip(frame, 1)

    # BGR -> RGB
    rgb_frame = cv2.cvtColor(
        frame,
        cv2.COLOR_BGR2RGB
    )

    # Convertir a imagen de MediaPipe
    mp_image = mp.Image(
        image_format=mp.ImageFormat.SRGB,
        data=rgb_frame
    )

    # Detectar mano y cuerpo
    hand_results = hand_detector.detect(mp_image)
    pose_results = pose_detector.detect(mp_image)

    # ----------------------------------------
    # DIBUJAR CUERPO (AMARILLO)
    # ----------------------------------------
    if pose_results.pose_landmarks:
        
        # Tomar la primera persona detectada
        pose = pose_results.pose_landmarks[0]

        # Dibujar los 33 puntos del cuerpo
        for landmark in pose:
            x = int(landmark.x * frame.shape[1])
            y = int(landmark.y * frame.shape[0])

            cv2.circle(
                frame,
                (x, y),
                5,
                (0, 255, 255), # Amarillo
                -1
            )

    # ----------------------------------------
    # DIBUJAR MANOS (VERDE)
    # ----------------------------------------
    if hand_results.hand_landmarks:

        # Tomar la primera mano detectada
        hand = hand_results.hand_landmarks[0]

        # Dibujar los 21 puntos
        for landmark in hand:
            x = int(landmark.x * frame.shape[1])
            y = int(landmark.y * frame.shape[0])

            cv2.circle(
                frame,
                (x, y),
                5,
                (0, 255, 0), # Verde
                -1
            )

        # Imprimir coordenadas de la muñeca
        wrist = hand[0]
        print(
            f"Muñeca -> "
            f"x={wrist.x:.3f}, "
            f"y={wrist.y:.3f}, "
            f"z={wrist.z:.3f}"
        )

    # Mostrar cámara
    cv2.imshow(
        "SOFIA - Vision (Manos y Cuerpo)",
        frame
    )

    # Q para salir
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

# Limpieza
cap.release()
cv2.destroyAllWindows()

# Cerrar ambos detectores
hand_detector.close()
pose_detector.close()