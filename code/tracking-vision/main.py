import time
import cv2
import mediapipe as mp

from detectors.hand_detector import HandDetector
from detectors.pose_detector import PoseDetector
from detectors.gesture_detector import GestureDetector

from utils.drawing import (
    dibujar_pose,
    dibujar_manos
)


# ----------------------------------------
# INICIALIZAR DETECTORES
# ----------------------------------------

hand_detector = HandDetector()
pose_detector = PoseDetector()
gesture_detector = GestureDetector()


# ----------------------------------------
# INICIALIZAR CÁMARA
# ----------------------------------------

cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("No se pudo abrir la cámara")
    exit()

print("Cámara iniciada correctamente.")
print("Presiona Q para salir.")

start_time = time.time()


# ----------------------------------------
# CICLO PRINCIPAL
# ----------------------------------------

try:

    while True:

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

        # Timestamp para VIDEO
        frame_timestamp_ms = int(
            (time.time() - start_time) * 1000
        )

        # ----------------------------------------
        # DETECCIÓN
        # ----------------------------------------

        hand_results = hand_detector.detect(
            mp_image,
            frame_timestamp_ms
        )

        pose_results = pose_detector.detect(
            mp_image,
            frame_timestamp_ms
        )

        # ----------------------------------------
        # DIBUJAR RESULTADOS
        # ----------------------------------------

        dibujar_pose(
            frame,
            pose_results,
            w,
            h
        )

        dibujar_manos(
            frame,
            hand_results,
            w,
            h
        )

        # ----------------------------------------
        # DETECTAR GESTOS
        # ----------------------------------------

        if gesture_detector.detectar_corazon(hand_results):

            cv2.putText(
                frame,
                "CORAZON DETECTADO",
                (30, 50),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (0, 0, 255),
                2
            )

        # ----------------------------------------
        # MOSTRAR CÁMARA
        # ----------------------------------------

        cv2.imshow(
            "SOFIA - Vision",
            frame
        )

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

finally:

    cap.release()
    cv2.destroyAllWindows()

    hand_detector.close()
    pose_detector.close()