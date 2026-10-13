
import time
import cv2
import mediapipe as mp
import asyncio
import threading
import queue

from bleak import BleakClient
from detectors.hand_detector import HandDetector
from utils.drawing import dibujar_manos

# =========================================
# SOFIA - TEST DE CUADRANTES + BLE
# =========================================

ESP32_BLE = "70:AF:09:15:23:42"
UART_WRITE_UUID = "6e400002-b5a3-f393-e0a9-e50e24dcca9e"

TIEMPO_ENTRE_ENVIOS = 1.0

COMANDOS = {
    "SUPERIOR IZQUIERDO": "90,120",
    "SUPERIOR DERECHO": "60,90",
    "INFERIOR IZQUIERDO": "120,90",
    "INFERIOR DERECHO": "90,60",
}

comandos_ble = queue.Queue()
ble_listo = threading.Event()
ble_error = threading.Event()


# =========================================
# HILO BLE
# =========================================

def hilo_ble():

    async def trabajador_ble():
        try:
            print(f"[BLE] Conectando con {ESP32_BLE}...")

            async with BleakClient(
                ESP32_BLE,
                timeout=15.0
            ) as client:

                if not client.is_connected:
                    raise RuntimeError("No se pudo conectar al ESP32")

                print("[BLE] Conectado correctamente.")
                ble_listo.set()

                while True:
                    # Esperar un comando sin bloquear el bucle BLE
                    comando = await asyncio.to_thread(comandos_ble.get)

                    try:
                        if comando is None:
                            break

                        await client.write_gatt_char(
                            UART_WRITE_UUID,
                            comando.encode("utf-8"),
                            response=False
                        )

                        print(f"[BLE] Enviado: {comando}")

                    finally:
                        comandos_ble.task_done()

        except Exception as error:
            print(f"[BLE] Error: {error}")
            ble_error.set()
            ble_listo.set()

    asyncio.run(trabajador_ble())


thread = threading.Thread(target=hilo_ble, daemon=True)
thread.start()


# =========================================
# CÁMARA Y MEDIAPIPE
# =========================================

hand_detector = HandDetector()
cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("Error: no se pudo abrir la cámara.")
    comandos_ble.put(None)
    hand_detector.close()
    raise SystemExit

print("=== SOFIA: TEST DE CUADRANTES ===")
print("Presiona Q para salir.")

inicio = time.monotonic()
ultimo_envio = 0.0
ultimo_cuadrante_enviado = None

try:
    while True:
        ret, frame = cap.read()

        if not ret:
            print("Error leyendo la cámara.")
            break

        frame = cv2.flip(frame, 1)
        h, w, _ = frame.shape

        # División de pantalla
        cv2.line(
            frame, (w // 2, 0), (w // 2, h),
            (0, 255, 255), 2
        )
        cv2.line(
            frame, (0, h // 2), (w, h // 2),
            (0, 255, 255), 2
        )

        # MediaPipe
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(
            image_format=mp.ImageFormat.SRGB,
            data=rgb
        )

        timestamp_ms = int(
            (time.monotonic() - inicio) * 1000
        )

        hands = hand_detector.detect(mp_image, timestamp_ms)
        dibujar_manos(frame, hands, w, h)

        cuadrante = "NO SE DETECTA MANO"
        grados_cuadrante = "--"

        if hands and getattr(hands, "hand_landmarks", None):
            muneca = hands.hand_landmarks[0][0]

            x = muneca.x
            y = muneca.y

            px = int(x * w)
            py = int(y * h)

            cv2.circle(
                frame, (px, py), 10, (0, 0, 255), -1
            )

            if x < 0.5 and y < 0.5:
                cuadrante = "SUPERIOR IZQUIERDO"
            elif x >= 0.5 and y < 0.5:
                cuadrante = "SUPERIOR DERECHO"
            elif x < 0.5 and y >= 0.5:
                cuadrante = "INFERIOR IZQUIERDO"
            else:
                cuadrante = "INFERIOR DERECHO"

            grados_cuadrante = COMANDOS[cuadrante]

            ahora = time.monotonic()

            cambio = (
                cuadrante != ultimo_cuadrante_enviado
            )

            espera_cumplida = (
                ahora - ultimo_envio >= TIEMPO_ENTRE_ENVIOS
            )

            if (
                cambio
                and espera_cumplida
                and ble_listo.is_set()
                and not ble_error.is_set()
            ):
                # queue.put es síncrono: NO lleva await
                comandos_ble.put(grados_cuadrante)

                ultimo_envio = ahora
                ultimo_cuadrante_enviado = cuadrante

                print(
                    f"[VISION] {cuadrante} -> "
                    f"{grados_cuadrante}"
                )

        # Mostrar información
        color = (
            (0, 255, 0)
            if cuadrante != "NO SE DETECTA MANO"
            else (0, 0, 255)
        )

        cv2.putText(
            frame, cuadrante, (15, h - 65),
            cv2.FONT_HERSHEY_SIMPLEX, 0.65, color, 2
        )

        cv2.putText(
            frame, f"Q1,Q2: {grados_cuadrante}",
            (15, h - 30),
            cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2
        )

        restante = max(
            0,
            TIEMPO_ENTRE_ENVIOS
            - (time.monotonic() - ultimo_envio)
        )

        cv2.putText(
            frame, f"Espera: {restante:.1f} s",
            (w - 190, h - 25),
            cv2.FONT_HERSHEY_SIMPLEX, 0.6,
            (255, 255, 255), 2
        )

        if ble_error.is_set():
            cv2.putText(
                frame, "ERROR BLE - revisa la terminal",
                (15, 35), cv2.FONT_HERSHEY_SIMPLEX,
                0.65, (0, 0, 255), 2
            )
        elif not ble_listo.is_set():
            cv2.putText(
                frame, "Conectando BLE...",
                (15, 35), cv2.FONT_HERSHEY_SIMPLEX,
                0.65, (0, 255, 255), 2
            )

        cv2.imshow("SOFIA - Test de cuadrantes", frame)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

finally:
    cap.release()
    cv2.destroyAllWindows()
    hand_detector.close()

    # Solicitar cierre del hilo BLE
    comandos_ble.put(None)
    thread.join(timeout=3)

    print("Prueba finalizada.")
