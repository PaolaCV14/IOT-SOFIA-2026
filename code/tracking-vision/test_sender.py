import time
import socket
import cv2
import mediapipe as mp

from mediapipe.tasks import python
from mediapipe.tasks.python import vision


# ============================================================
# CONFIGURACIÓN
# ============================================================

MODEL_PATH = "models/hand_landmarker.task"

UNITY_IP = "127.0.0.1"
UNITY_PORT = 5005

CAMERA_ID = 0

# Rango angular para esta primera prueba
Q1_MIN = -90.0
Q1_MAX = 90.0

Q2_MIN = -90.0
Q2_MAX = 90.0


# ============================================================
# UDP
# ============================================================

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)


def enviar_unity(q1, q2):

    mensaje = f"{q1:.2f},{q2:.2f}"

    sock.sendto(
        mensaje.encode("utf-8"),
        (UNITY_IP, UNITY_PORT)
    )


# ============================================================
# MEDIA PIPE
# ============================================================

base_options = python.BaseOptions(
    model_asset_path=MODEL_PATH
)

options = vision.HandLandmarkerOptions(
    base_options=base_options,
    running_mode=vision.RunningMode.VIDEO,
    num_hands=1,
    min_hand_detection_confidence=0.7,
    min_hand_presence_confidence=0.7,
    min_tracking_confidence=0.7
)

hand_detector = vision.HandLandmarker.create_from_options(options)


# ============================================================
# CÁMARA
# ============================================================

cap = cv2.VideoCapture(CAMERA_ID)

if not cap.isOpened():
    print("ERROR: No se pudo abrir la cámara.")
    exit()


start_time = time.time()


# ============================================================
# LOOP PRINCIPAL
# ============================================================

try:

    while True:

        ret, frame = cap.read()

        if not ret:
            print("ERROR: No se pudo leer la cámara.")
            break

        # Espejo para que el movimiento sea natural
        frame = cv2.flip(frame, 1)

        h, w, _ = frame.shape

        # ----------------------------------------------------
        # OpenCV BGR → RGB
        # ----------------------------------------------------

        rgb_frame = cv2.cvtColor(
            frame,
            cv2.COLOR_BGR2RGB
        )

        mp_image = mp.Image(
            image_format=mp.ImageFormat.SRGB,
            data=rgb_frame
        )

        timestamp_ms = int(
            (time.time() - start_time) * 1000
        )

        # ----------------------------------------------------
        # MediaPipe
        # ----------------------------------------------------

        resultado = hand_detector.detect_for_video(
            mp_image,
            timestamp_ms
        )

        # Valores por defecto
        q1 = 0.0
        q2 = 0.0

        # ----------------------------------------------------
        # Si encontramos una mano
        # ----------------------------------------------------

        if resultado.hand_landmarks:

            # Landmark 0 = muñeca
            wrist = resultado.hand_landmarks[0][0]

            # Coordenadas normalizadas de MediaPipe
            x = wrist.x
            y = wrist.y

            # ------------------------------------------------
            # X → q1
            #
            # izquierda  = -90°
            # centro     =   0°
            # derecha    = +90°
            # ------------------------------------------------

            q1 = (x * 180.0) - 90.0

            # ------------------------------------------------
            # Y → q2
            #
            # arriba     = +90°
            # centro     =   0°
            # abajo      = -90°
            # ------------------------------------------------

            q2 = 90.0 - (y * 180.0)

            # Seguridad
            q1 = max(Q1_MIN, min(Q1_MAX, q1))
            q2 = max(Q2_MIN, min(Q2_MAX, q2))

            # ------------------------------------------------
            # Coordenadas de la mano en pantalla
            # ------------------------------------------------

            px = int(x * w)
            py = int(y * h)

            cv2.circle(
                frame,
                (px, py),
                12,
                (0, 255, 0),
                -1
            )

            # Centro de referencia
            cv2.circle(
                frame,
                (w // 2, h // 2),
                8,
                (255, 255, 255),
                -1
            )

            # ------------------------------------------------
            # Enviar a Unity
            # ------------------------------------------------

            enviar_unity(q1, q2)

        # ----------------------------------------------------
        # Información en pantalla
        # ----------------------------------------------------

        cv2.rectangle(
            frame,
            (15, 15),
            (300, 125),
            (20, 20, 20),
            -1
        )

        cv2.putText(
            frame,
            f"q1: {q1:+.1f} deg",
            (30, 50),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 255, 200),
            2
        )

        cv2.putText(
            frame,
            f"q2: {q2:+.1f} deg",
            (30, 85),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 255, 200),
            2
        )

        cv2.putText(
            frame,
            "Q para salir",
            (30, 110),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.45,
            (200, 200, 200),
            1
        )

        # ----------------------------------------------------
        # Mostrar cámara
        # ----------------------------------------------------

        cv2.imshow(
            "SOFIA - Hand to Q1/Q2",
            frame
        )

        key = cv2.waitKey(1) & 0xFF

        if key == ord("q"):
            break


finally:

    cap.release()
    cv2.destroyAllWindows()

    hand_detector.close()
    sock.close()

    print("Programa terminado.")