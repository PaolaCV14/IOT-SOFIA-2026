
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
# SOFIA - 9 POSICIONES + BLE
# =========================================

ESP32_BLE = "70:AF:09:15:23:42"
UART_WRITE_UUID = "6e400002-b5a3-f393-e0a9-e50e24dcca9e"

ANGULO_MIN = 60
ANGULO_MAX = 120
TIEMPO_ENTRE_ENVIOS = 1.0

# Cuadricula de 3 columnas x 3 filas.
# Cada combinacion respeta los limites de Q1 y Q2.
COMANDOS = {
    (0, 0): (90, 120),    # Superior izquierda
    (1, 0): (60, 120),    # Superior centro
    (2, 0): (60, 90),     # Superior derecha

    (0, 1): (120, 90),    # Centro izquierda
    (1, 1): (90, 90),     # Centro
    (2, 1): (120, 120),   # Centro derecha

    (0, 2): (120, 60),    # Inferior izquierda
    (1, 2): (90, 60),     # Inferior centro
    (2, 2): (60, 60),     # Inferior derecha
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
# CAMARA + MEDIAPIPE
# =========================================

hand_detector = HandDetector()
cap = cv2.VideoCapture(0)

# Reducir la resolucion para agilizar el procesamiento
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

if not cap.isOpened():
    print("Error: no se pudo abrir la camara.")
    comandos_ble.put(None)
    hand_detector.close()
    raise SystemExit

print("=== SOFIA: 9 POSICIONES ===")
print("Mueve la muneca por las nueve zonas.")
print("Presiona Q para salir.")

inicio = time.monotonic()
ultimo_envio = 0.0
ultima_celda_enviada = None

try:
    while True:
        ret, frame = cap.read()

        if not ret:
            print("Error leyendo la camara.")
            break

        frame = cv2.flip(frame, 1)
        h, w, _ = frame.shape

        # Dividir la pantalla en nueve celdas
        cv2.line(frame, (w // 3, 0), (w // 3, h), (0, 255, 255), 2)
        cv2.line(frame, (2 * w // 3, 0), (2 * w // 3, h), (0, 255, 255), 2)
        cv2.line(frame, (0, h // 3), (w, h // 3), (0, 255, 255), 2)
        cv2.line(frame, (0, 2 * h // 3), (w, 2 * h // 3), (0, 255, 255), 2)

        # Etiquetas de las nueve posiciones
        for (col, fila), (q1, q2) in COMANDOS.items():
            tx = col * w // 3 + 10
            ty = fila * h // 3 + 28

            cv2.putText(
                frame,
                f"Q1={q1} Q2={q2}",
                (tx, ty),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.52,
                (0, 255, 0),
                2
            )

        # Detectar mano
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(
            image_format=mp.ImageFormat.SRGB,
            data=rgb
        )

        timestamp_ms = int((time.monotonic() - inicio) * 1000)
        hands = hand_detector.detect(mp_image, timestamp_ms)
        dibujar_manos(frame, hands, w, h)

        celda_actual = None
        grados_cuadrante = "--"

        if hands and getattr(hands, "hand_landmarks", None):
            muneca = hands.hand_landmarks[0][0]

            x = muneca.x
            y = muneca.y

            px = int(x * w)
            py = int(y * h)

            cv2.circle(frame, (px, py), 10, (0, 0, 255), -1)

            # Determinar columna y fila (0, 1 o 2)
            col = min(2, int(x * 3))
            fila = min(2, int(y * 3))

            celda_actual = (col, fila)
            q1, q2 = COMANDOS[celda_actual]
            grados_cuadrante = f"{q1},{q2}"

            ahora = time.monotonic()

            cambio = celda_actual != ultima_celda_enviada
            espera_cumplida = (
                ahora - ultimo_envio >= TIEMPO_ENTRE_ENVIOS
            )

            if (
                cambio
                and espera_cumplida
                and ble_listo.is_set()
                and not ble_error.is_set()
            ):
                # Descartar comandos viejos pendientes
                while not comandos_ble.empty():
                    try:
                        comandos_ble.get_nowait()
                        comandos_ble.task_done()
                    except queue.Empty:
                        break

                comandos_ble.put(grados_cuadrante)

                ultimo_envio = ahora
                ultima_celda_enviada = celda_actual

                print(
                    f"[VISION] Fila {fila + 1}, columna {col + 1}"
                    f" -> Q1={q1}, Q2={q2}"
                )

        # Informacion en pantalla
        if celda_actual is not None:
            texto = f"Posicion: fila {celda_actual[1] + 1}, columna {celda_actual[0] + 1}"
            color = (0, 255, 0)
        else:
            texto = "NO SE DETECTA MANO"
            color = (0, 0, 255)

        cv2.putText(
            frame, texto, (10, h - 60),
            cv2.FONT_HERSHEY_SIMPLEX, 0.65, color, 2
        )

        cv2.putText(
            frame, f"Q1,Q2: {grados_cuadrante}",
            (10, h - 25),
            cv2.FONT_HERSHEY_SIMPLEX, 0.75, color, 2
        )

        if ble_error.is_set():
            estado = "ERROR BLE"
        elif not ble_listo.is_set():
            estado = "CONECTANDO BLE..."
        else:
            estado = "BLE CONECTADO"

        cv2.putText(
            frame, estado, (w - 200, h - 25),
            cv2.FONT_HERSHEY_SIMPLEX, 0.55,
            (0, 255, 255), 2
        )

        cv2.imshow("SOFIA - 9 posiciones", frame)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

finally:
    cap.release()
    cv2.destroyAllWindows()
    hand_detector.close()

    comandos_ble.put(None)
    thread.join(timeout=3)

    print("Prueba finalizada.")
