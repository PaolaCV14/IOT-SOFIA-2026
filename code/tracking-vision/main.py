import time
import cv2
import mediapipe as mp

from detectors.hand_detector import HandDetector
from detectors.pose_detector import PoseDetector
from detectors.gesture_detector import GestureDetector
from utils.drawing import dibujar_pose, dibujar_manos

# ==============================================================
# PIPELINE PRINCIPAL DE VISIÓN - PROYECTO SOFIA
# Tracking 3D en tiempo real + Clasificación de Gestos
# ==============================================================

def main():
    # 1. Cargamos nuestros detectores modulares
    hand_detector = HandDetector()
    pose_detector = PoseDetector()
    gesture_detector = GestureDetector()

    # 2. Conectamos con la cámara
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("❌ Error: No se pudo abrir la cámara web.")
        return

    print("🚀 Cámara iniciada. Muestra tus manos o presiona 'Q' para salir.")
    start_time = time.time()

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            # Efecto espejo para interacción natural (como verse en un espejo)
            frame = cv2.flip(frame, 1)
            h, w, _ = frame.shape

            # MediaPipe necesita la imagen en formato RGB y con timestamp en ms
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
            timestamp_ms = int((time.time() - start_time) * 1000)

            # 3. Inferencia: rastreamos cuerpo y hasta 2 manos
            hands = hand_detector.detect(mp_image, timestamp_ms)
            pose = pose_detector.detect(mp_image, timestamp_ms)

            # 4. Dibujamos los esqueletos sobre el video
            dibujar_pose(frame, pose, w, h)
            dibujar_manos(frame, hands, w, h)

            # 5. Reconocimiento de gestos dinámicos y estáticos
            # Evaluamos intención dinámica PPT (1, 2, 3 bombas de puño)
            ppt_detectado, ppt_texto = gesture_detector.detectar_intencion_ppt(hands)
            saludo_detectado = gesture_detector.detectar_saludo(hands)

            # Prioridad de gestos (los dinámicos van antes que los estáticos para no confundirse)
            gestos = [
                (gesture_detector.detectar_corazon(hands), "CORAZON DETECTADO", (0, 0, 255)),     # Rojo
                (ppt_detectado,                            ppt_texto,            (255, 0, 255)),   # Magenta
                (saludo_detectado,                         "HOLA! SALUDO",       (255, 255, 0)),   # Cyan
                (gesture_detector.detectar_tijera(hands),  "TIJERA DETECTADA",  (255, 0, 0)),     # Azul
                (gesture_detector.detectar_papel(hands),   "PAPEL DETECTADO",   (0, 255, 0)),     # Verde
                (gesture_detector.detectar_roca(hands),    "ROCA DETECTADA",    (0, 140, 255))    # Naranja vibrante
            ]

            # Mostramos el gesto activo en pantalla con su color representativo
            for detectado, texto, color in gestos:
                if detectado:
                    cv2.putText(frame, texto, (30, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)
                    break

            # 6. Renderizamos la ventana interactiva
            cv2.imshow("SOFIA - Vision", frame)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

    finally:
        # Limpieza ordenada de recursos
        cap.release()
        cv2.destroyAllWindows()
        hand_detector.close()
        pose_detector.close()
        print("👋 Sistema cerrado correctamente.")


if __name__ == "__main__":
    main()