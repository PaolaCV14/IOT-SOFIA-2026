
"""
==============================================================
CLIENTE BLE ASÍNCRONO MULTIHILO - SOFIA ESP32-C3

- Comunicación BLE GATT Write.
- Seguimiento limitado a 5 comandos por segundo.
- Cola de seguimiento: conserva la posición más reciente.
- Prioridad para SALUDO y CORAZON.
- Notificaciones de conexión.
==============================================================
"""

import asyncio
import threading
import queue
import time
import re

import sys
from bleak import BleakClient


# En macOS, CoreBluetooth asigna UUID en lugar de MAC física
if sys.platform == "darwin":
    ESP32_DEFAULT_MAC = "8D8CF7F2-2F26-4A93-E6ED-9D83EDEC3E6A"
else:
    ESP32_DEFAULT_MAC = "70:AF:09:15:23:42"

UART_SERVICE_UUID = "6e400001-b5a3-f393-e0a9-e50e24dcca9e"
UART_WRITE_UUID = "6e400002-b5a3-f393-e0a9-e50e24dcca9e"

ANGULO_MIN = 60
ANGULO_MAX = 120

RUTINAS = {"SALUDO", "CORAZON"}


class SofiaBleClient:

    def __init__(
        self,
        mac_address=ESP32_DEFAULT_MAC,
        status_callback=None,
        connection_callback=None
    ):
        self.mac_address = mac_address
        self.status_callback = status_callback or (lambda msg: None)
        self.connection_callback = connection_callback or (lambda state: None)

        # Cola para rutinas y movimientos.
        self.cmd_queue = queue.Queue()

        self.is_connected = False
        self._running = False
        self._thread = None

        # 5 comandos por segundo como máximo para seguimiento.
        self._min_interval = 0.20
        self._last_send_time = 0.0

        self._lock = threading.Lock()

    def _log(self, message):
        try:
            self.status_callback(f"[BLE] {message}")
        except Exception:
            pass

    def _notify_connection(self, state):
        self.is_connected = state
        try:
            self.connection_callback(state)
        except Exception:
            pass

    def start(self):
        with self._lock:
            if self._running:
                return
            self._running = True

        self._thread = threading.Thread(
            target=self._run_event_loop,
            daemon=True,
            name="SofiaBLEWorker"
        )
        self._thread.start()

    def _run_event_loop(self):
        try:
            asyncio.run(self._worker())
        except Exception as error:
            self._log(f"Error en hilo BLE: {error}")
        finally:
            with self._lock:
                self._running = False
            self._notify_connection(False)

    def _validate_command(self, cmd_str):
        if not isinstance(cmd_str, str):
            return None

        command = cmd_str.strip().upper()

        if command in RUTINAS:
            return command

        match = re.fullmatch(r"(Q1|Q2)\s*,\s*(-?\d+)", command)
        if match:
            angle = int(match.group(2))
            if ANGULO_MIN <= angle <= ANGULO_MAX:
                return f"{match.group(1)},{angle}"
            return None

        match = re.fullmatch(r"(-?\d+)\s*,\s*(-?\d+)", command)
        if match:
            q1 = int(match.group(1))
            q2 = int(match.group(2))

            if (
                ANGULO_MIN <= q1 <= ANGULO_MAX
                and ANGULO_MIN <= q2 <= ANGULO_MAX
            ):
                return f"{q1},{q2}"

        return None

    def _discard_pending_movements(self):
        """
        Descarta movimientos que aún no se han enviado.
        No puede cancelar una transmisión ya iniciada.
        """
        while True:
            try:
                self.cmd_queue.get_nowait()
            except queue.Empty:
                break
            else:
                self.cmd_queue.task_done()

    async def _worker(self):
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
                self._log("Conectado exitosamente a SOFIA.")

                while self._running and client.is_connected:
                    try:
                        command = await asyncio.to_thread(
                            self.cmd_queue.get,
                            True,
                            0.1
                        )
                    except queue.Empty:
                        continue

                    try:
                        if command is None:
                            break

                        # Las rutinas se transmiten sin el intervalo
                        # de seguimiento.
                        if command not in RUTINAS:
                            elapsed = time.monotonic() - self._last_send_time
                            wait_time = self._min_interval - elapsed

                            if wait_time > 0:
                                await asyncio.sleep(wait_time)

                        await client.write_gatt_char(
                            UART_WRITE_UUID,
                            command.encode("utf-8"),
                            response=False
                        )

                        self._last_send_time = time.monotonic()
                        self._log(f"Comando transmitido: {command}")

                    except Exception as error:
                        self._log(f"Error de transmisión: {error}")

                    finally:
                        self.cmd_queue.task_done()

        except Exception as error:
            self._log(f"Fallo de conexión BLE: {error}")

        finally:
            self._notify_connection(False)
            self._log("Sesión BLE cerrada.")

    def send_command(self, cmd_str):
        command = self._validate_command(cmd_str)

        if command is None:
            self._log(f"Comando inválido: {cmd_str!r}")
            return False

        with self._lock:
            if not self._running or not self.is_connected:
                self._log("No se puede enviar: ESP32 no conectado.")
                return False

            if command in RUTINAS:
                # La rutina desplaza los movimientos pendientes.
                self._discard_pending_movements()
                self.cmd_queue.put(command)

            else:
                # Seguimiento: reemplazar movimientos pendientes
                # para no reproducir posiciones obsoletas.
                self._discard_pending_movements()
                self.cmd_queue.put(command)

        return True

    def stop(self):
        with self._lock:
            if not self._running:
                self._notify_connection(False)
                return

            self._running = False
            self._discard_pending_movements()
            self.cmd_queue.put(None)

        self._notify_connection(False)

        if (
            self._thread
            and self._thread.is_alive()
            and threading.current_thread() != self._thread
        ):
            self._thread.join(timeout=2.0)

        self._log("Desconexión BLE solicitada.")
