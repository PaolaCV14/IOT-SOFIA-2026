"""
==============================================================
CLIENTE BLE ASÍNCRONO MULTIHILO - SOFIA ESP32-C3
Driver de radio Bluetooth puro (GATT Write).
Responsabilidad única: Conexión y envío por radio sin bloquear la app.
==============================================================
"""

import asyncio
import threading
import queue
import time
from bleak import BleakClient

ESP32_DEFAULT_MAC = "70:AF:09:15:23:42"
UART_SERVICE_UUID = "6e400001-b5a3-f393-e0a9-e50e24dcca9e"
UART_WRITE_UUID = "6e400002-b5a3-f393-e0a9-e50e24dcca9e"

# Rango mecánico seguro del servomotor en el hardware de SOFÍA
ANGULO_MIN = 60
ANGULO_MAX = 120


class SofiaBleClient:
    """
    Driver de bajo nivel para comunicación Bluetooth con el ESP32.
    Corre en un hilo secundario con asyncio y cola no bloqueante.
    """
    def __init__(self, mac_address=ESP32_DEFAULT_MAC, status_callback=None):
        self.mac_address = mac_address
        self.status_callback = status_callback or (lambda msg: None)
        self.cmd_queue = queue.Queue()
        self.is_connected = False
        self._running = False
        self._thread = None
        self._last_send_time = 0
        self._min_interval = 0.08  # Máximo ~12 envíos/segundo para no saturar el buffer del ESP32

    def start(self):
        """Inicia el hilo de conexión BLE."""
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._run_event_loop, daemon=True)
        self._thread.start()

    def _log(self, msg):
        self.status_callback(f"[BLE] {msg}")

    def _run_event_loop(self):
        asyncio.run(self._worker())

    async def _worker(self):
        self._log(f"Conectando con {self.mac_address}...")
        try:
            async with BleakClient(self.mac_address, timeout=12.0) as client:
                if not client.is_connected:
                    self._log("No se pudo conectar al ESP32.")
                    self.is_connected = False
                    return

                self.is_connected = True
                self._log("Conectado exitosamente al robot SOFIA.")

                while self._running:
                    try:
                        comando = await asyncio.to_thread(self.cmd_queue.get, timeout=0.1)
                    except queue.Empty:
                        continue

                    if comando is None:
                        break

                    try:
                        # Envío por GATT Write sin respuesta para mínima latencia
                        await client.write_gatt_char(
                            UART_WRITE_UUID,
                            comando.encode("utf-8"),
                            response=False
                        )
                        self._log(f"Enviado -> {comando}")
                    except Exception as e:
                        self._log(f"Error de transmisión: {e}")
                    finally:
                        self.cmd_queue.task_done()

        except Exception as e:
            self._log(f"Desconectado o error: {e}")
        finally:
            self.is_connected = False
            self._log("Sesión BLE finalizada.")

    def send_command(self, cmd_str):
        """
        Encola un comando de texto para el robot (ej. '90,90').
        Aplica control de tasa para proteger la antena.
        """
        now = time.time()
        if now - self._last_send_time < self._min_interval:
            return False
        self.cmd_queue.put(cmd_str.strip())
        self._last_send_time = now
        return True

    def stop(self):
        """Detiene la conexión y libera el hilo."""
        self._running = False
        self.cmd_queue.put(None)
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.5)
