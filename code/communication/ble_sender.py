
"""
==============================================================
CLIENTE BLE ASÍNCRONO MULTIHILO - SOFIA ESP32-C3

Driver de comunicación BLE GATT Write para ESP32-C3.
- Conexión asíncrona en hilo secundario.
- Cola de comandos.
- Control de frecuencia para movimientos.
- Prioridad para las rutinas SALUDO y CORAZON.
- Notificaciones de conexión y desconexión.
==============================================================
"""

import asyncio
import threading
import queue
import time
import re

from bleak import BleakClient


# ==========================================================
# CONFIGURACIÓN BLE
# ==========================================================

ESP32_DEFAULT_MAC = "70:AF:09:15:23:42"

UART_SERVICE_UUID = "6e400001-b5a3-f393-e0a9-e50e24dcca9e"
UART_WRITE_UUID = "6e400002-b5a3-f393-e0a9-e50e24dcca9e"

ANGULO_MIN = 60
ANGULO_MAX = 120

RUTINAS = {"SALUDO", "CORAZON"}


class SofiaBleClient:
    """
    Cliente BLE de SOFIA.

    Comandos admitidos:
        90,90
        Q1,90
        Q2,120
        SALUDO
        CORAZON

    Las rutinas tienen prioridad sobre los comandos de movimiento
    pendientes en la cola.
    """

    def __init__(
        self,
        mac_address=ESP32_DEFAULT_MAC,
        status_callback=None,
        connection_callback=None
    ):
        self.mac_address = mac_address

        self.status_callback = (
            status_callback or (lambda msg: None)
        )

        self.connection_callback = (
            connection_callback or (lambda is_connected: None)
        )

        self.cmd_queue = queue.Queue()

        self.is_connected = False
        self._running = False
        self._thread = None

        # Frecuencia mínima entre movimientos ordinarios.
        self._last_send_time = 0.0
        self._min_interval = 0.08

        # Protege el estado y la inserción de comandos.
        self._lock = threading.Lock()

    # ======================================================
    # INICIO Y REGISTRO
    # ======================================================

    def _log(self, message):
        try:
            self.status_callback(f"[BLE] {message}")
        except Exception:
            pass

    def _notify_connection(self, state):
        self.is_connected = state

        try:
            self.connection_callback(state)
        except Exception as error:
            self._log(f"Error notificando conexión: {error}")

    def start(self):
        """Inicia el hilo encargado de conectar por BLE."""
        with self._lock:
            if self._running:
                self._log("El cliente BLE ya está activo.")
                return

            self._running = True

        self._thread = threading.Thread(
            target=self._run_event_loop,
            daemon=True,
            name="SofiaBLEWorker"
        )

        self._thread.start()

    def _run_event_loop(self):
        """Ejecuta el ciclo asíncrono en el hilo secundario."""
        try:
            asyncio.run(self._worker())
        except Exception as error:
            self._log(f"Error en el hilo BLE: {error}")
        finally:
            with self._lock:
                self._running = False

            self._notify_connection(False)

    # ======================================================
    # VALIDACIÓN DE COMANDOS
    # ======================================================

    def _validate_command(self, cmd_str):
        """
        Valida el formato del comando sin modificar su significado.
        Devuelve el comando normalizado o None si es inválido.
        """
        if not isinstance(cmd_str, str):
            return None

        comando = cmd_str.strip().upper()

        if not comando:
            return None

        # Rutinas del firmware ESP32.
        if comando in RUTINAS:
            return comando

        # Movimiento individual: Q1,90 o Q2,90.
        match = re.fullmatch(r"(Q1|Q2)\s*,\s*(-?\d+)", comando)

        if match:
            angulo = int(match.group(2))

            if not ANGULO_MIN <= angulo <= ANGULO_MAX:
                return None

            return f"{match.group(1)},{angulo}"

        # Movimiento conjunto: 90,90.
        match = re.fullmatch(r"(-?\d+)\s*,\s*(-?\d+)", comando)

        if match:
            q1 = int(match.group(1))
            q2 = int(match.group(2))

            if not (
                ANGULO_MIN <= q1 <= ANGULO_MAX
                and ANGULO_MIN <= q2 <= ANGULO_MAX
            ):
                return None

            return f"{q1},{q2}"

        return None

    # ======================================================
    # PROCESAMIENTO DE LA COLA
    # ======================================================

    def _prioritize_routine(self, rutina):
        """
        Elimina movimientos pendientes para que la rutina no
        tenga que esperar detrás de una cola de seguimiento.

        No interrumpe un comando que ya se esté transmitiendo.
        """
        pendientes = []

        while True:
            try:
                comando = self.cmd_queue.get_nowait()
            except queue.Empty:
                break

            try:
                if comando is not None:
                    # Se descartan movimientos anteriores pendientes.
                    continue
            finally:
                self.cmd_queue.task_done()

        # La rutina queda en la cola para el siguiente envío.
        self.cmd_queue.put(rutina)

    async def _worker(self):
        """Mantiene la conexión BLE y transmite los comandos."""
        self._log(f"Conectando con {self.mac_address}...")

        try:
            async with BleakClient(
                self.mac_address,
                timeout=10.0
            ) as client:

                if not client.is_connected:
                    self._log("No se pudo conectar al ESP32.")
                    return

                self._notify_connection(True)
                self._log("Conectado exitosamente al robot SOFIA.")

                while self._running and client.is_connected:
                    try:
                        comando = await asyncio.to_thread(
                            self.cmd_queue.get,
                            True,
                            0.1
                        )
                    except queue.Empty:
                        continue

                    try:
                        if comando is None:
                            break

                        # Las rutinas no esperan el intervalo de movimiento.
                        if comando not in RUTINAS:
                            elapsed = (
                                time.monotonic() - self._last_send_time
                            )

                            remaining = self._min_interval - elapsed

                            if remaining > 0:
                                await asyncio.sleep(remaining)

                        await client.write_gatt_char(
                            UART_WRITE_UUID,
                            comando.encode("utf-8"),
                            response=False
                        )

                        self._last_send_time = time.monotonic()

                        self._log(f"Comando transmitido: {comando}")

                    except Exception as error:
                        self._log(
                            f"Error de transmisión de {comando}: {error}"
                        )

                    finally:
                        self.cmd_queue.task_done()

        except Exception as error:
            self._log(f"Fallo de conexión BLE: {error}")

        finally:
            self._notify_connection(False)
            self._log("Sesión BLE cerrada.")

    # ======================================================
    # ENVÍO DE COMANDOS
    # ======================================================

    def send_command(self, cmd_str):
        """
        Encola comandos para el ESP32.

        SALUDO y CORAZON:
            - No se rechazan por el límite de 80 ms.
            - Desplazan los movimientos que siguen pendientes.

        Movimientos:
            - Se conservan en la cola.
            - Se transmiten respetando el intervalo mínimo.
        """
        comando = self._validate_command(cmd_str)

        if comando is None:
            self._log(f"Comando inválido: {cmd_str!r}")
            return False

        with self._lock:
            if not self._running or not self.is_connected:
                self._log("No se puede enviar: ESP32 no conectado.")
                return False

            if comando in RUTINAS:
                self._prioritize_routine(comando)
            else:
                self.cmd_queue.put(comando)

        self._log(f"Comando aceptado: {comando}")
        return True

    # ======================================================
    # DESCONEXIÓN
    # ======================================================

    def stop(self):
        """Solicita el cierre de la conexión y del hilo BLE."""
        with self._lock:
            if not self._running:
                self._notify_connection(False)
                return

            self._running = False
            self.cmd_queue.put(None)

        self._notify_connection(False)

        if (
            self._thread
            and self._thread.is_alive()
            and threading.current_thread() != self._thread
        ):
            self._thread.join(timeout=2.0)

        self._log("Desconexión BLE solicitada.")
