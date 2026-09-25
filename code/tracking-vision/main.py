import time
import csv
import os
import cv2
import mediapipe as mp

from detectors.hand_detector import HandDetector
from detectors.pose_detector import PoseDetector
from detectors.gesture_detector import GestureDetector
from utils.drawing import dibujar_pose, dibujar_manos
from utils.smoother import LandmarkSmoother

# ==============================================================
# PIPELINE PRINCIPAL DE VISIÓN - PROYECTO SOFIA
# Tracking 3D en tiempo real + Suavizado EMA + Métricas de Rendimiento
# ==============================================================

def main():
    # 1. Cargamos nuestros detectores modulares y suavizador
    hand_detector = HandDetector()
    pose_detector = PoseDetector()
    gesture_detector = GestureDetector()
    smoother = LandmarkSmoother(alpha=0.35)

    # 2. Conectamos con la cámara
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Error: No se pudo abrir la cámara web.")
        return

    print("=" * 55)
    print("  SOFÍA - Sistema de Visión y Reconocimiento de Gestos")
    print("  Controles del teclado:")
    print("    's' -> Activar / desactivar filtro de suavizado")
    print("    'l' -> Empezar / detener guardado de métricas en CSV")
    print("    'q' -> Salir del programa")
    print("=" * 55)

    start_time = time.time()
    prev_frame_time = time.time()
    
    # Variables de benchmarking / métricas
    fps_smooth = 30.0
    use_smoothing = True
    logging_active = False
    log_file = None
    csv_writer = None

    try:
        while True:
            t_loop_start = time.perf_counter()
            ret, frame = cap.read()
            if not ret:
                break

            # Efecto espejo para interacción natural
            frame = cv2.flip(frame, 1)
            h, w, _ = frame.shape

            # MediaPipe necesita la imagen en formato RGB y con timestamp en ms
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
            timestamp_ms = int((time.time() - start_time) * 1000)

            # Inferencia: Medimos latencia de captura + inferencia
            t_infer_start = time.perf_counter()
            raw_hands = hand_detector.detect(mp_image, timestamp_ms)
            raw_pose = pose_detector.detect(mp_image, timestamp_ms)

            # Aplicamos suavizado (EMA) para reducir temblor/ruido en landmarks
            if use_smoothing:
                hands = smoother.smooth_hands(raw_hands)
                pose = smoother.smooth_pose(raw_pose)
            else:
                hands = raw_hands
                pose = raw_pose

            # 4. Dibujamos los puntos y conexiones sobre el video
            dibujar_pose(frame, pose, w, h)
            dibujar_manos(frame, hands, w, h)

            # 5. Revisamos qué gesto está haciendo el usuario
            # Los gestos que llevan movimiento van primero para no confundirlos
            ppt_detectado, ppt_texto = gesture_detector.detectar_intencion_ppt(hands)
            saludo_detectado = gesture_detector.detectar_saludo(hands)
            swipe_detectado, swipe_texto = gesture_detector.detectar_swipe(hands)

            gestos = [
                (gesture_detector.detectar_corazon(hands), "CORAZON DETECTADO", (0, 0, 255)),     # Rojo (Corazón)
                (ppt_detectado,                            ppt_texto,            (255, 0, 255)),   # Rosa mexicano (Golpes PPT)
                (saludo_detectado,                         "HOLA! SALUDO",       (255, 255, 0)),   # Cyan (Saludo)
                (swipe_detectado,                          swipe_texto,          (0, 165, 255)),   # Naranja (Swipe)
                (gesture_detector.detectar_tijera(hands),  "TIJERA DETECTADA",   (255, 0, 0)),     # Azul (Tijera)
                (gesture_detector.detectar_papel(hands),   "PAPEL DETECTADO",    (0, 255, 0)),     # Verde (Papel)
                (gesture_detector.detectar_roca(hands),    "ROCA DETECTADA",     (0, 140, 255))    # Ámbar (Piedra)
            ]

            gesto_activo = "NINGUNO"
            color_activo = (200, 200, 200)
            for detectado, texto, color in gestos:
                if detectado:
                    gesto_activo = texto
                    color_activo = color
                    break

            t_infer_end = time.perf_counter()
            latencia_ms = (t_infer_end - t_infer_start) * 1000

            # Calculamos los FPS del video
            current_time = time.time()
            fps_instant = 1.0 / max(current_time - prev_frame_time, 1e-5)
            prev_frame_time = current_time
            fps_smooth = 0.9 * fps_smooth + 0.1 * fps_instant

            # 6. Cuadro de métricas en la esquina de la pantalla
            overlay = frame.copy()
            cv2.rectangle(overlay, (15, 15), (380, 160), (20, 20, 20), -1)
            cv2.addWeighted(overlay, 0.7, frame, 0.3, 0, frame)
            cv2.rectangle(frame, (15, 15), (380, 160), (80, 80, 80), 1)

            cv2.putText(frame, f"FPS: {fps_smooth:.1f} ({fps_instant:.0f} inst)", (25, 45),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 255, 200), 2)
            cv2.putText(frame, f"Latencia: {latencia_ms:.1f} ms", (25, 75),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 255, 200), 2)
            
            smooth_label = "EMA (alpha=0.35)" if use_smoothing else "OFF"
            smooth_col = (100, 255, 100) if use_smoothing else (100, 100, 255)
            cv2.putText(frame, f"Filtro: {smooth_label}", (25, 105),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.60, smooth_col, 2)

            log_status = "[GRABANDO CSV]" if logging_active else "[L] Iniciar Log"
            log_col = (0, 0, 255) if logging_active else (180, 180, 180)
            cv2.putText(frame, f"Log: {log_status}", (25, 135),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.55, log_col, 1)

            # Letrero abajo cuando hay una postura reconocida
            if gesto_activo != "NINGUNO":
                cv2.rectangle(frame, (15, h - 70), (450, h - 20), (30, 30, 30), -1)
                cv2.rectangle(frame, (15, h - 70), (450, h - 20), color_activo, 2)
                cv2.putText(frame, f"POSTURA: {gesto_activo}", (25, h - 35),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, color_activo, 2)

            # 7. Si activamos el log con 'L', guardamos la fila en el CSV
            if logging_active and csv_writer is not None:
                csv_writer.writerow([
                    round(timestamp_ms / 1000.0, 3),
                    round(fps_smooth, 2),
                    round(latencia_ms, 2),
                    int(use_smoothing),
                    gesto_activo
                ])

            # 8. Mostramos el video en la ventana
            cv2.imshow("SOFIA - Vision", frame)
            key = cv2.waitKey(1) & 0xFF
            if key == ord("q"):
                break
            elif key == ord("s"):
                use_smoothing = not use_smoothing
                print(f"[Filtro] Suavizado EMA: {'ACTIVADO' if use_smoothing else 'DESACTIVADO'}")
            elif key == ord("l"):
                logging_active = not logging_active
                if logging_active:
                    os.makedirs("benchmark_logs", exist_ok=True)
                    log_filename = f"benchmark_logs/metrics_{int(time.time())}.csv"
                    log_file = open(log_filename, mode="w", newline="")
                    csv_writer = csv.writer(log_file)
                    csv_writer.writerow(["time_sec", "fps", "latency_ms", "smoothing_enabled", "detected_gesture"])
                    print(f"[Log] Grabando métricas en '{log_filename}'")
                else:
                    if log_file:
                        log_file.close()
                        log_file = None
                        csv_writer = None
                    print("[Log] Archivo guardado correctamente.")

    finally:
        # Cerramos todo en orden
        if log_file:
            log_file.close()
        cap.release()
        cv2.destroyAllWindows()
        hand_detector.close()
        pose_detector.close()
        print("Programa terminado correctamente.")


if __name__ == "__main__":
    main()