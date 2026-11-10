"""
CLIENTE BLE ASINCRONO - SOFIA ESP32-C3

Compatible con el firmware que recibe comandos directos:
SALUDO, CORAZON, BAILE, NEGAR, PPT, CENTRAR,
REPOSO, DESREPOSO, HOME, REST, STOP, SCAN,
Q1, Q2 y posiciones conjuntas.

No utiliza tramas, ACK, NACK ni notificaciones TX.

Control de sincronizacion:
- Al solicitar una rutina, bloquea inmediatamente el tracking.
- Descarta posiciones pendientes.
- Da prioridad a comandos/rutinas sobre el tracking.
- Antes de transmitir un angulo vuelve a comprobar que no haya
  comenzado una rutina.
- Libera el bloqueo al cumplirse la duracion estimada de la rutina.
"""

import asyncio
import queue
import re
import sys
import threading
import time

from bleak import BleakClient


# ==========================================================
# CONFIGURACION BLE
# ==========================================================

if sys.platform == "darwin":
    ESP32_DEFAULT_MAC = "8D8CF7F2-2F26-4A93-E6ED-9D83EDEC3E6A"
else:
    ESP32_DEFAULT_MAC = "24:DC:C3:48:82:76"

UART_SERVICE_UUID = "6e400001-b5a3-f393-e0a9-e50e24dcca9e"
UART_WRITE_UUID = "6e400002-b5a3-f393-e0a9-e50e24dcca9e"

ANGULO_MIN = 60
ANGULO_MAX = 120


# ==========================================================
# RUTINAS Y DURACIONES ESTIMADAS
# ==========================================================

# Cada paso de rutina tarda aproximadamente:
# 500 ms de movimiento + 100 ms de pausa.
# Las duraciones corresponden a los pasos y repeticiones
# definidos actualmente en el firmware Arduino.

RUTINAS = {
    "SALUDO": 3600,
    "CORAZON": 2400,
    "BAILE": 4800,
    "NEGAR": 3600,
    "PPT": 3600,
    "CENTRAR": 600,
    "REPOSO": 600,
    "DESREPOSO": 600,
}

COMANDOS_SIMPLES = {
    "PING",
    "HOME",
    "REST",
    "STOP",
    "SCAN",
}

TRACKING_INTERVAL_S = 0.65


# ==========================================================
# CLIENTE BLE
# ==========================================================

class SofiaBleClient:

    def __init__(
        self,
        mac_address=ESP32_DEFAULT_MAC,
        status_callback=None,
        connection_callback=None,
        event_callback=None,
        auto_reconnect=True,
    ):
        self.mac_address = mac_address

        self.status_callback = status_callback or (lambda msg: None)
        self.connection_callback = connection_callback or (lambda state: None)
        self.event_callback = event_callback or (lambda event: None)

        self.auto_reconnect = auto_reconnect

        # Cola FIFO para comandos de control y rutinas.
        self._control_queue = queue.Queue()

        # Tracking: solamente conserva la posición más reciente.
        self._ultimo_ang = None

        self._lock = threading.RLock()

        # Serializa la decision de transmitir un angulo con la solicitud
        # de una rutina. Si un angulo ya esta escribiendose, la solicitud
        # de rutina espera a que termine; despues no se envia otro angulo.
        self._tx_lock = threading.Lock()

        self._wake = threading.Event()

        self.is_connected = False
        self._running = False

        self._thread = None
        self._last_ang_time = 0.0

        # Estado interno de sincronizacion de rutinas.
        self._routine_active = False
        self._routine_pending = False
        self._routine_name = None
        self._routine_deadline = 0.0

        self.stats = {
            "comandos_enviados": 0,
            "errores_envio": 0,
            "fallos_conexion": 0,
        }

    # ======================================================
    # UTILIDADES
    # ======================================================

    def _log(self, message):
        try:
            self.status_callback(f"[BLE] {message}")
        except Exception:
            pass

    def _emit(self, **event):
        try:
            self.event_callback(event)
        except Exception:
            pass

    def _notify_connection(self, state):
        self.is_connected = state
        try:
            self.connection_callback(state)
        except Exception:
            pass

    def _puede_enviar(self):
        if not self._running or not self.is_connected:
            self._log("No se puede enviar: ESP32 no conectado.")
            return False
        return True

    def _actualizar_estado_rutina_locked(self):
        """
        Debe llamarse teniendo adquirido self._lock.
        Libera el bloqueo cuando vence la duracion estimada.
        """
        if (
            self._routine_active
            and not self._routine_pending
            and self._routine_deadline > 0
            and time.monotonic() >= self._routine_deadline
        ):
            nombre = self._routine_name

            self._routine_active = False
            self._routine_pending = False
            self._routine_name = None
            self._routine_deadline = 0.0

            self._log(
                f"Bloqueo BLE liberado: rutina {nombre} concluida por tiempo."
            )
            self._emit(
                type="ROUTINE_TIMEOUT",
                cmd=nombre,
            )

    def _rutina_activa_locked(self):
        self._actualizar_estado_rutina_locked()
        return self._routine_active

    def is_routine_active(self):
        """Indica si el sender tiene una rutina pendiente o en ejecucion."""
        with self._lock:
            return self._rutina_activa_locked()

    def release_routine(self):
        """
        Liberacion manual opcional.
        Puede llamarse desde la GUI cuando esta finalice su temporizador.
        """
        with self._lock:
            nombre = self._routine_name
            self._routine_active = False
            self._routine_pending = False
            self._routine_name = None
            self._routine_deadline = 0.0

        self._wake.set()

        if nombre:
            self._log(f"Bloqueo de rutina {nombre} liberado manualmente.")

    # ======================================================
    # CICLO DE VIDA
    # ======================================================

    def start(self):
        with self._lock:
            if self._running:
                return

            self._running = True

        self._thread = threading.Thread(
            target=self._run_event_loop,
            daemon=True,
            name="SofiaBLEWorker",
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

    def stop(self):
        with self._lock:
            self._running = False
            self._vaciar_colas()
            self._routine_active = False
            self._routine_pending = False
            self._routine_name = None
            self._routine_deadline = 0.0
            self._wake.set()

        self._notify_connection(False)

        if (
            self._thread
            and self._thread.is_alive()
            and threading.current_thread() != self._thread
        ):
            self._thread.join(timeout=3.0)

        self._log("Desconexion BLE solicitada.")

    def _vaciar_colas(self):
        self._ultimo_ang = None

        while True:
            try:
                self._control_queue.get_nowait()
            except queue.Empty:
                break

    # ======================================================
    # API PUBLICA
    # ======================================================

    def send_angles(self, q1, q2):
        """Encola una posicion conjunta si no hay una rutina activa."""
        try:
            q1 = int(q1)
            q2 = int(q2)
        except (TypeError, ValueError):
            self._log(f"Angulos invalidos: {q1}, {q2}")
            return False

        if not (
            ANGULO_MIN <= q1 <= ANGULO_MAX
            and ANGULO_MIN <= q2 <= ANGULO_MAX
        ):
            self._log(f"Angulos fuera de rango: {q1},{q2}")
            return False

        with self._lock:
            if not self._puede_enviar():
                return False

            if self._rutina_activa_locked():
                return False

            self._ultimo_ang = (q1, q2)

        self._wake.set()
        return True

    def send_routine(self, nombre):
        """Bloquea el tracking y encola una rutina."""
        nombre = str(nombre).strip().upper()

        if nombre not in RUTINAS:
            self._log(f"Rutina desconocida: {nombre}")
            return False

        # El mismo candado se usa durante la escritura de tracking.
        # Asi la rutina no puede quedar registrada a mitad de un envio.
        with self._tx_lock:
            with self._lock:
                if not self._puede_enviar():
                    return False

                if self._rutina_activa_locked():
                    self._log(
                        f"Rutina {nombre} ignorada: "
                        f"{self._routine_name} sigue activa."
                    )
                    return False

                # Bloqueo inmediato ANTES de colocar la rutina en la cola.
                self._routine_active = True
                self._routine_pending = True
                self._routine_name = nombre
                self._routine_deadline = 0.0

                # Descarta cualquier posicion de tracking pendiente.
                self._ultimo_ang = None

                self._control_queue.put(nombre)

        self._log(f"Tracking bloqueado. Preparando rutina {nombre}.")
        self._wake.set()
        return True

    def send_simple(self, cmd):
        """Envia PING, HOME, REST, STOP o SCAN."""
        cmd = str(cmd).strip().upper()

        if cmd not in COMANDOS_SIMPLES:
            self._log(f"Comando invalido: {cmd}")
            return False

        with self._lock:
            if not self._puede_enviar():
                return False

            if cmd == "STOP":
                # STOP tiene prioridad: elimina comandos pendientes
                # y libera el bloqueo local de la rutina.
                self._vaciar_colas()
                self._routine_active = False
                self._routine_pending = False
                self._routine_name = None
                self._routine_deadline = 0.0
                self._control_queue.put("STOP")

            elif cmd in {"HOME", "REST", "SCAN"}:
                if self._rutina_activa_locked():
                    self._log(
                        f"{cmd} ignorado: hay una rutina en ejecucion."
                    )
                    return False
                self._control_queue.put(cmd)

            else:  # PING
                self._control_queue.put(cmd)

        self._wake.set()
        return True

    def send_command(self, cmd_str):
        """
        Compatibilidad con main_gui.py y dispatcher.py.

        Acepta:
        SALUDO, DESREPOSO, HOME, REST, STOP, SCAN,
        Q1,75, Q2,105, 90,90 y ANG,90,90.
        """
        if not isinstance(cmd_str, str):
            return False

        command = cmd_str.strip().upper()

        if command in RUTINAS:
            return self.send_routine(command)

        if command in COMANDOS_SIMPLES:
            return self.send_simple(command)

        # Posicion conjunta: 90,90
        match = re.fullmatch(r"(\d+)\s*,\s*(\d+)", command)
        if match:
            return self.send_angles(match.group(1), match.group(2))

        # Control individual: Q1,75 o Q2,105
        match = re.fullmatch(r"(Q1|Q2)\s*,\s*(\d+)", command)
        if match:
            eje = match.group(1)
            angulo = int(match.group(2))

            if not ANGULO_MIN <= angulo <= ANGULO_MAX:
                self._log(f"Angulo fuera de rango: {command}")
                return False

            with self._lock:
                if not self._puede_enviar():
                    return False

                if self._rutina_activa_locked():
                    return False

                self._ultimo_ang = None
                self._control_queue.put(f"{eje},{angulo}")

            self._wake.set()
            return True

        # Movimiento ANG: ANG,90,90
        match = re.fullmatch(r"ANG\s*,\s*(\d+)\s*,\s*(\d+)", command)
        if match:
            return self.send_angles(match.group(1), match.group(2))

        self._log(f"Comando invalido: {cmd_str}")
        return False

    # ======================================================
    # ENVIO DIRECTO BLE
    # ======================================================

    async def _write_command(self, client, command):
        """Envia texto plano al characteristic RX del ESP32."""
        try:
            await client.write_gatt_char(
                UART_WRITE_UUID,
                command.encode("utf-8"),
                response=False,
            )

            self.stats["comandos_enviados"] += 1
            self._log(f"[TX] {command}")
            return True

        except Exception as error:
            self.stats["errores_envio"] += 1
            self._log(f"Error enviando {command}: {error}")
            self._emit(
                type="ERROR",
                cmd=command,
                error=str(error),
            )
            return False

    def _marcar_rutina_enviada(self, nombre):
        """Inicia el temporizador interno al completar el write BLE."""
        with self._lock:
            if self._routine_active and self._routine_name == nombre:
                self._routine_pending = False
                self._routine_deadline = (
                    time.monotonic() + RUTINAS[nombre] / 1000.0
                )

        self._emit(
            type="ROUTINE_SENT",
            cmd=nombre,
            duration_ms=RUTINAS[nombre],
        )

    def _cancelar_rutina_por_error(self, nombre):
        with self._lock:
            if self._routine_name == nombre:
                self._routine_active = False
                self._routine_pending = False
                self._routine_name = None
                self._routine_deadline = 0.0

    # ======================================================
    # PROCESAMIENTO DE COLAS
    # ======================================================

    async def _worker(self):
        reconnect_delay = 2.5
        attempt = 0

        while self._running:
            attempt += 1

            if attempt == 1:
                self._log(f"Conectando con {self.mac_address}...")
            else:
                self._log(f"Reconexion automatica: intento {attempt}")
                self._emit(type="RECONNECTING", attempt=attempt)

            try:
                def on_disconnect(_client):
                    self._log("Se perdio la conexion BLE.")
                    self._notify_connection(False)
                    self._emit(type="DISCONNECTED")

                async with BleakClient(
                    self.mac_address,
                    timeout=8.0,
                    disconnected_callback=on_disconnect,
                ) as client:

                    if not client.is_connected:
                        raise ConnectionError("No se pudo conectar al ESP32.")

                    attempt = 0
                    self._notify_connection(True)
                    self._log("Conectado correctamente a SOFIA.")
                    self._emit(type="CONNECTED")

                    while self._running and client.is_connected:

                        # Actualizar el temporizador de la rutina.
                        with self._lock:
                            self._actualizar_estado_rutina_locked()

                        # ----------------------------------
                        # 1. PRIORIDAD: COMANDOS Y RUTINAS
                        # ----------------------------------
                        try:
                            command = self._control_queue.get_nowait()
                        except queue.Empty:
                            command = None

                        if command is not None:
                            enviado = await self._write_command(client, command)

                            if command in RUTINAS:
                                if enviado:
                                    self._marcar_rutina_enviada(command)
                                else:
                                    self._cancelar_rutina_por_error(command)

                            if not enviado:
                                break

                            continue

                        # ----------------------------------
                        # 2. SEGUIMIENTO AUTOMATICO
                        # ----------------------------------
                        ang = None

                        with self._lock:
                            self._actualizar_estado_rutina_locked()

                            # Solo extraer angulos si no hay rutina activa.
                            if not self._routine_active:
                                ang = self._ultimo_ang
                                self._ultimo_ang = None

                        if ang is not None:
                            espera = (
                                TRACKING_INTERVAL_S
                                - (time.monotonic() - self._last_ang_time)
                            )

                            if espera > 0:
                                await asyncio.sleep(espera)

                            # Serializar la comprobacion final y la escritura
                            # frente a send_routine(). Si la rutina se solicita
                            # primero, este angulo se descarta. Si la escritura
                            # ya comenzo, termina antes de aceptar la rutina.
                            await asyncio.to_thread(self._tx_lock.acquire)
                            try:
                                with self._lock:
                                    self._actualizar_estado_rutina_locked()

                                    hay_comando = not self._control_queue.empty()
                                    bloquear = (
                                        self._routine_active or hay_comando
                                    )

                                if bloquear:
                                    # No reinsertar el angulo: es una posicion
                                    # antigua respecto a la rutina pendiente.
                                    continue

                                command = f"{ang[0]},{ang[1]}"
                                enviado = await self._write_command(
                                    client,
                                    command,
                                )
                                self._last_ang_time = time.monotonic()

                            finally:
                                self._tx_lock.release()

                            if not enviado:
                                break

                            continue

                        # ----------------------------------
                        # 3. ESPERAR NUEVOS COMANDOS
                        # ----------------------------------
                        self._wake.clear()

                        await asyncio.to_thread(
                            self._wake.wait,
                            0.05,
                        )

                    if self._running and not client.is_connected:
                        self._log("El enlace BLE se perdio.")

            except Exception as error:
                self.stats["fallos_conexion"] += 1
                self._log(f"Fallo de conexion BLE: {error}")

            finally:
                self._notify_connection(False)

            if not self._running or not self.auto_reconnect:
                break

            self._log(f"Reintentando conexion en {reconnect_delay}s...")

            for _ in range(int(reconnect_delay * 10)):
                if not self._running:
                    break
                await asyncio.sleep(0.1)

        self._log(f"Sesion BLE cerrada. Estadisticas: {self.stats}")
