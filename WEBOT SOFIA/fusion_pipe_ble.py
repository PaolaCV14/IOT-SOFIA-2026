
import time
import cv2
import mediapipe as mp

from detectors.hand_detector import HandDetector
from utils.drawing import dibujar_manos

# =========================================
# SOFIA - TEST SIMPLE DE CUADRANTES
# =========================================

hand_detector = HandDetector()

cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("Error: no se pudo abrir la camara.")
    hand_detector.close()
    raise SystemExit

print("SOFIA - Test de cuadrantes")
print("Mueve tu mano entre los cuatro cuadrantes.")
print("Presiona Q para salir.")

inicio = time.time()

try:
    while True:
        ret, frame = cap.read()

        if not ret:
            break

        # Espejo
        frame = cv2.flip(frame, 1)
        h, w, _ = frame.shape

        # Dividir pantalla en cuatro cuadrantes
        cv2.line(frame, (w // 2, 0), (w // 2, h), (0, 255, 255), 2)
        cv2.line(frame, (0, h // 2), (w, h // 2), (0, 255, 255), 2)

        # MediaPipe
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(
            image_format=mp.ImageFormat.SRGB,
            data=rgb
        )

        timestamp_ms = int((time.time() - inicio) * 1000)
        hands = hand_detector.detect(mp_image, timestamp_ms)

        # Dibujar landmarks de las manos
        dibujar_manos(frame, hands, w, h)

        cuadrante = "NO SE DETECTA MANO"

        # Obtener muñeca de la primera mano
        if hands and getattr(hands, "hand_landmarks", None):
            muneca = hands.hand_landmarks[0][0]

            x = muneca.x
            y = muneca.y

            px = int(x * w)
            py = int(y * h)

            cv2.circle(frame, (px, py), 10, (0, 0, 255), -1)

            if x < 0.5 and y < 0.5:
                cuadrante = "SUPERIOR IZQUIERDO"
            elif x >= 0.5 and y < 0.5:
                cuadrante = "SUPERIOR DERECHO"
            elif x < 0.5 and y >= 0.5:
                cuadrante = "INFERIOR IZQUIERDO"
            else:
                cuadrante = "INFERIOR DERECHO"

        # Mostrar resultado
        cv2.putText(
            frame,
            cuadrante,
            (15, h - 25),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 255, 0) if cuadrante != "NO SE DETECTA MANO" else (0, 0, 255),
            2
        )

        cv2.imshow("SOFIA - Test de cuadrantes", frame)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

finally:
    cap.release()
    cv2.destroyAllWindows()
    hand_detector.close()
    print("Prueba finalizada.")
