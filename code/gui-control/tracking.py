import cv2
import mediapipe as mp

from mediapipe.tasks import python
from mediapipe.tasks.python import vision

# Modelo de MediaPipe
model_path = "models/hand_landmarker.task"

# Configuración
base_options = python.BaseOptions(
    model_asset_path=model_path
)

options = vision.HandLandmarkerOptions(
    base_options=base_options,
    num_hands=1,
    min_hand_detection_confidence=0.7,
    min_hand_presence_confidence=0.7,
    min_tracking_confidence=0.7
)

# Crear detector
detector = vision.HandLandmarker.create_from_options(options)

# Cámara
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

    # Detectar mano
    results = detector.detect(mp_image)

    # Si encontró una mano
    if results.hand_landmarks:

        hand = results.hand_landmarks[0]

        # Dibujar los 21 puntos
        for landmark in hand:

            x = int(
                landmark.x * frame.shape[1]
            )

            y = int(
                landmark.y * frame.shape[0]
            )

            cv2.circle(
                frame,
                (x, y),
                5,
                (0, 255, 0),
                -1
            )

        # Muñeca
        wrist = hand[0]

        print(
            f"Muñeca -> "
            f"x={wrist.x:.3f}, "
            f"y={wrist.y:.3f}, "
            f"z={wrist.z:.3f}"
        )

    # Mostrar cámara
    cv2.imshow(
        "SOFIA - Vision",
        frame
    )

    # Q para salir
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break


cap.release()
cv2.destroyAllWindows()

detector.close()