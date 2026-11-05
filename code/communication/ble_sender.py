"""
==============================================================
CLIENTE BLE ASÍNCRONO MULTIHILO - SOFIA ESP32-C3

Implementa el protocolo PC <-> ESP32 descrito en
docs/ESTANDAR_COMUNICACION_PC_ESP32.md:

    PC -> ESP32 (RX, Write sin respuesta):  $<SEQ>,<CMD>[,<P1>[,<P2>]]#
    ESP32 -> PC (TX, Notify):               $<SEQ>,ACK,<DATOS>#
                                            $<SEQ>,NACK,ERR_xx#
                                            $<SEQ>,EVT,DONE,<RUTINA>#

- Número de secuencia incremental (1..65535, con vuelta a 1).
- Comandos de control (ROUTINE, HOME, REST, STOP, PING): esperan
  ACK/NACK con timeout de 200 ms y hasta 2 reintentos (el ESP32
  descarta SEQ duplicados, por lo que reintentar no repite acciones).
- Seguimiento (ANG): limitado a 5 comandos/s, sólo se conserva la
  posición más reciente y no se reintenta (una posición vieja no sirve);
  sí se mide su RTT y se cuentan los timeouts.
- Tramas fragmentadas en bloques del MTU tanto al enviar como al recibir.
- Eventos hacia la GUI mediante event_callback(dict).
==============================================================
"""

import asyncio
import collections
import queue
import re
import sys
import threading
import time

from bleak import BleakClient


# En macOS, CoreBluetooth asigna UUID en lugar de MAC física
if sys.platform == "darwin":
    ESP32_DEFAULT_MAC = "8D8CF7F2-2F26-4A93-E6ED-9D83EDEC3E6A"
else:
    ESP32_DEFAULT_MAC = "70:AF:09:15:23:42"

UART_SERVICE_UUID = "6e400001-b5a3-f393-e0a9-e50e24dcca9e"
UART_WRITE_UUID = "6e400002-b5a3-f393-e0a9-e50e24dcca9e"   # RX del ESP32
UART_NOTIFY_UUID = "6e400003-b5a3-f393-e0a9-e50e24dcca9e"  # TX del ESP32

ANGULO_MIN = 60
ANGULO_MAX = 120

# Rutinas almacenadas en el ESP32 y su duración nominal en ms.
# La duración sólo se usa como respaldo si no llega el evento DONE.
# Deben coincidir con RUTINAS[] en code/firmware-mecatronica/modulo_sofia.ino
RUTINAS = {
    "SALUDO": 3000,
    "CORAZON": 2000,
    "BAILE": 3200,
    "NEGAR": 2100,
    "PPT": 1800,
    "CENTRAR": 2000,
    "REPOSO": 2000,
}

# Comandos sin parámetros
COMANDOS_SIMPLES = {"PING", "HOME", "REST", "STOP"}

# Códigos de error del estándar
ERRORES = {
    "ERR_01": "OUT_OF_RANGE: ángulo fuera de 60-120°",
    "ERR_02": "UNKNOWN_CMD: comando o rutina no reconocido",
    "ERR_03": "BAD_FORMAT: trama mal formada",
    "ERR_04": "ROUTINE_BUSY: hay una rutina en ejecución",
    "ERR_05": "I2C_FAIL: PCA9685 no responde",
}

# Parámetros de temporización del protocolo
ACK_TIMEOUT_S = 0.200
MAX_REINTENTOS = 2
TRACKING_INTERVAL_S = 0.20    # 5 Hz para seguimiento
TIMEOUTS_PARA_ALERTA = 3      # Timeouts seguidos que indican enlace degradado
MTU_PAYLOAD_MIN = 20          # Payload seguro con MTU por defecto (23 - 3)


def construir_trama(seq, cmd, *params):
    """Ensambla "$SEQ,CMD,P1,P2#"."""
    campos = [str(seq), cmd] + [str(p) for p in params]
    return "$" + ",".join(campos) + "#"


def parsear_respuesta(contenido):
    """
    Interpreta el contenido de una trama de respuesta (sin '$' ni '#').
    Retorna dict con seq, status y data, o None si es inválida.
    """
    campos = [c.strip() for c in contenido.split(",")]
    if len(campos) < 2 or not campos[0].isdigit():
        return None

    status = campos[1].upper()
    if status not in ("ACK", "NACK", "EVT"):
        return None

    return {"seq": int(campos[0]), "status": status, "data": campos[2:]}


class _Pendiente:
    """Comando enviado que espera ACK/NACK."""

    __slots__ = ("cmd", "params", "enviado_en", "future")

    def __init__(self, cmd, params, future):
        self.cmd = cmd
        self.params = params
        self.enviado_en = 0.0
        self.future = future


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

        # Carril de control (rutinas y comandos simples) en orden FIFO
        self._control_queue = queue.Queue()
        # Carril de seguimiento: sólo la posición más reciente
        self._ultimo_ang = None
        self._wake = threading.Event()

        self.is_connected = False
        self._running = False
        self._thread = None
        self._lock = threading.Lock()

        self._seq = 0
        self._pendientes = {}          # seq -> _Pendiente (dentro del loop)
        self._rx_buffer = ""
        self._last_ang_time = 0.0
        self._payload_max = MTU_PAYLOAD_MIN

        # Estadísticas del enlace (útiles como evidencia de pruebas)
        self.stats = collections.Counter()
        self.ultimo_rtt_ms = None
        self._timeouts_seguidos = 0
        self._ultimo_log_nack_ang = 0.0

    # ---------------------------------------------------------
    # Utilidades
    # ---------------------------------------------------------
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

    def _siguiente_seq(self):
        self._seq = self._seq + 1 if self._seq < 65535 else 1
        return self._seq

    # ---------------------------------------------------------
    # Ciclo de vida
    # ---------------------------------------------------------
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

    def stop(self):
        with self._lock:
            if not self._running:
                self._notify_connection(False)
                return
            self._running = False
            self._vaciar_colas()
            self._wake.set()

        self._notify_connection(False)

        if (
            self._thread
            and self._thread.is_alive()
            and threading.current_thread() != self._thread
        ):
            self._thread.join(timeout=2.0)

        self._log("Desconexión BLE solicitada.")

    def _vaciar_colas(self):
        self._ultimo_ang = None
        while True:
            try:
                self._control_queue.get_nowait()
            except queue.Empty:
                break

    # ---------------------------------------------------------
    # API pública (llamada desde el hilo de la GUI)
    # ---------------------------------------------------------
    def _puede_enviar(self):
        if not self._running or not self.is_connected:
            self._log("No se puede enviar: ESP32 no conectado.")
            return False
        return True

    def send_angles(self, q1, q2):
        """Encola una posición de seguimiento (reemplaza la pendiente)."""
        try:
            q1, q2 = int(q1), int(q2)
        except (TypeError, ValueError):
            self._log(f"Ángulos inválidos: {q1!r}, {q2!r}")
            return False

        if not (ANGULO_MIN <= q1 <= ANGULO_MAX and ANGULO_MIN <= q2 <= ANGULO_MAX):
            self._log(f"Ángulos fuera de rango: {q1},{q2}")
            return False

        with self._lock:
            if not self._puede_enviar():
                return False
            self._ultimo_ang = (q1, q2)
        self._wake.set()
        return True

    def send_routine(self, nombre):
        """Encola ROUTINE,<nombre>. Descarta el seguimiento pendiente."""
        nombre = str(nombre).strip().upper()
        if nombre not in RUTINAS:
            self._log(f"Rutina desconocida: {nombre!r}")
            return False

        with self._lock:
            if not self._puede_enviar():
                return False
            self._ultimo_ang = None
            self._control_queue.put(("ROUTINE", (nombre,)))
        self._wake.set()
        return True

    def send_simple(self, cmd):
        """Encola PING, HOME, REST o STOP."""
        cmd = str(cmd).strip().upper()
        if cmd not in COMANDOS_SIMPLES:
            self._log(f"Comando inválido: {cmd!r}")
            return False

        with self._lock:
            if not self._puede_enviar():
                return False
            if cmd == "STOP":
                self._ultimo_ang = None
            self._control_queue.put((cmd, ()))
        self._wake.set()
        return True

    def send_command(self, cmd_str):
        """
        Compatibilidad con la API anterior: acepta "q1,q2", "Q1,a",
        "Q2,a", un nombre de rutina o un comando simple.
        """
        if not isinstance(cmd_str, str):
            return False
        command = cmd_str.strip().upper()

        if command in RUTINAS:
            return self.send_routine(command)
        if command in COMANDOS_SIMPLES:
            return self.send_simple(command)

        match = re.fullmatch(r"(-?\d+)\s*,\s*(-?\d+)", command)
        if match:
            return self.send_angles(match.group(1), match.group(2))

        match = re.fullmatch(r"(Q1|Q2)\s*,\s*(-?\d+)", command)
        if match:
            angle = int(match.group(2))
            if not ANGULO_MIN <= angle <= ANGULO_MAX:
                self._log(f"Ángulo fuera de rango: {command}")
                return False
            with self._lock:
                if not self._puede_enviar():
                    return False
                self._control_queue.put((match.group(1), (angle,)))
            self._wake.set()
            return True

        self._log(f"Comando inválido: {cmd_str!r}")
        return False

    # ---------------------------------------------------------
    # Recepción (se ejecuta en el loop asyncio del hilo BLE)
    # ---------------------------------------------------------
    def _on_notify(self, _sender, data):
        try:
            self._rx_buffer += bytes(data).decode("utf-8", errors="replace")
        except Exception:
            return

        # Reensamblar tramas "$...#" que pueden llegar fragmentadas
        while True:
            inicio = self._rx_buffer.find("$")
            if inicio < 0:
                self._rx_buffer = ""
                return
            fin = self._rx_buffer.find("#", inicio)
            if fin < 0:
                # Trama incompleta; evitar crecimiento indefinido
                self._rx_buffer = self._rx_buffer[inicio:][-256:]
                return
            contenido = self._rx_buffer[inicio + 1:fin]
            self._rx_buffer = self._rx_buffer[fin + 1:]
            self._procesar_respuesta(contenido)

    def _procesar_respuesta(self, contenido):
        resp = parsear_respuesta(contenido)
        if resp is None:
            self.stats["tramas_invalidas"] += 1
            self._log(f"Trama de respuesta inválida: ${contenido}#")
            return

        seq, status, data = resp["seq"], resp["status"], resp["data"]

        # Evento asíncrono de fin de rutina
        if status == "EVT":
            if data and data[0].upper() == "DONE":
                rutina = data[1] if len(data) > 1 else "?"
                self.stats["rutinas_terminadas"] += 1
                self._log(f"ESP32: rutina {rutina} terminada (SEQ {seq}).")
                self._emit(type="DONE", seq=seq, routine=rutina)
            return

        pendiente = self._pendientes.pop(seq, None)
        if pendiente is None:
            # ACK tardío (ya expiró) o NACK de trama sin SEQ válido
            self.stats["respuestas_huerfanas"] += 1
            if status == "NACK":
                codigo = data[0] if data else "?"
                self._log(f"NACK sin comando asociado (SEQ {seq}): {codigo}")
            return

        rtt_ms = (time.monotonic() - pendiente.enviado_en) * 1000.0
        self.ultimo_rtt_ms = rtt_ms
        self._timeouts_seguidos = 0

        if pendiente.future is not None and not pendiente.future.done():
            pendiente.future.set_result((status, data, rtt_ms))

        if pendiente.cmd == "ANG":
            # El seguimiento no reporta cada ACK a la GUI (30+ por segundo
            # saturarían la terminal); sólo estadísticas y NACK limitados.
            if status == "ACK":
                self.stats["ang_ack"] += 1
            else:
                self.stats["ang_nack"] += 1
                ahora = time.monotonic()
                if ahora - self._ultimo_log_nack_ang > 1.0:
                    self._ultimo_log_nack_ang = ahora
                    codigo = data[0] if data else "?"
                    self._log(f"Seguimiento rechazado: {codigo} {ERRORES.get(codigo, '')}")
            self._emit(type="RTT", seq=seq, cmd="ANG", rtt_ms=rtt_ms)

    def _expirar_pendientes(self):
        """Elimina comandos ANG cuyo ACK no llegó a tiempo."""
        ahora = time.monotonic()
        for seq, p in list(self._pendientes.items()):
            if p.future is None and ahora - p.enviado_en > ACK_TIMEOUT_S:
                del self._pendientes[seq]
                self.stats["ang_timeout"] += 1
                self._registrar_timeout()

    def _registrar_timeout(self):
        self._timeouts_seguidos += 1
        if self._timeouts_seguidos == TIMEOUTS_PARA_ALERTA:
            self._log(
                f"Advertencia: {TIMEOUTS_PARA_ALERTA} respuestas seguidas "
                f"sin ACK. Posible pérdida de comunicación."
            )
            self._emit(type="LINK_DEGRADED", timeouts=self._timeouts_seguidos)

    # ---------------------------------------------------------
    # Envío (loop asyncio)
    # ---------------------------------------------------------
    async def _write_frame(self, client, trama):
        """Escribe una trama fragmentándola al tamaño de payload del MTU."""
        datos = trama.encode("utf-8")
        for i in range(0, len(datos), self._payload_max):
            await client.write_gatt_char(
                UART_WRITE_UUID,
                datos[i:i + self._payload_max],
                response=False
            )

    async def _enviar_control(self, client, cmd, params):
        """Envía un comando de control y espera ACK/NACK con reintentos."""
        seq = self._siguiente_seq()
        trama = construir_trama(seq, cmd, *params)
        descripcion = f"{cmd} {' '.join(map(str, params))}".strip()

        for intento in range(MAX_REINTENTOS + 1):
            future = asyncio.get_running_loop().create_future()
            pendiente = _Pendiente(cmd, params, future)
            self._pendientes[seq] = pendiente
            pendiente.enviado_en = time.monotonic()

            try:
                await self._write_frame(client, trama)
                self.stats["tramas_enviadas"] += 1
            except Exception as error:
                self._pendientes.pop(seq, None)
                self.stats["errores_escritura"] += 1
                self._log(f"Error de transmisión ({descripcion}): {error}")
                self._emit(type="ERROR", seq=seq, cmd=cmd, params=params,
                           error=str(error))
                return

            try:
                status, data, rtt_ms = await asyncio.wait_for(
                    future, timeout=ACK_TIMEOUT_S
                )
            except asyncio.TimeoutError:
                self._pendientes.pop(seq, None)
                self.stats["control_timeout"] += 1
                self._registrar_timeout()
                if intento < MAX_REINTENTOS:
                    self.stats["reintentos"] += 1
                    self._log(
                        f"Sin ACK para {trama} en {int(ACK_TIMEOUT_S * 1000)} ms; "
                        f"reintento {intento + 1}/{MAX_REINTENTOS}."
                    )
                    continue
                self._log(f"Sin respuesta del ESP32 para {descripcion} (SEQ {seq}).")
                self._emit(type="TIMEOUT", seq=seq, cmd=cmd, params=params)
                return

            if status == "ACK":
                self.stats["control_ack"] += 1
                self._log(f"ACK {descripcion} (SEQ {seq}, {rtt_ms:.0f} ms): {','.join(data)}")
                self._emit(type="ACK", seq=seq, cmd=cmd, params=params,
                           data=data, rtt_ms=rtt_ms)
            else:
                codigo = data[0] if data else "?"
                self.stats["control_nack"] += 1
                self._log(
                    f"NACK {descripcion} (SEQ {seq}): {codigo} "
                    f"{ERRORES.get(codigo, '')}"
                )
                self._emit(type="NACK", seq=seq, cmd=cmd, params=params,
                           code=codigo, rtt_ms=rtt_ms)
            return

    async def _enviar_ang(self, client, q1, q2):
        """Envía una posición de seguimiento sin esperar el ACK."""
        espera = TRACKING_INTERVAL_S - (time.monotonic() - self._last_ang_time)
        if espera > 0:
            await asyncio.sleep(espera)

        seq = self._siguiente_seq()
        pendiente = _Pendiente("ANG", (q1, q2), None)
        self._pendientes[seq] = pendiente
        pendiente.enviado_en = time.monotonic()

        try:
            await self._write_frame(client, construir_trama(seq, "ANG", q1, q2))
            self.stats["tramas_enviadas"] += 1
        except Exception as error:
            self._pendientes.pop(seq, None)
            self.stats["errores_escritura"] += 1
            self._log(f"Error de transmisión (ANG {q1},{q2}): {error}")

        self._last_ang_time = time.monotonic()

    async def _worker(self):
        reconnect_delay = 2.5
        attempt = 0

        while self._running:
            attempt += 1
            if attempt == 1:
                self._log(f"Conectando con {self.mac_address}...")
            else:
                self._log(f"Reconexión automática (intento {attempt}) con {self.mac_address}...")
                self._emit(type="RECONNECTING", attempt=attempt)

            try:
                def _on_ble_disconnect(_client):
                    self._log("Bleak notificó desconexión del ESP32.")
                    self._notify_connection(False)
                    self._emit(type="DISCONNECTED")

                async with BleakClient(
                    self.mac_address,
                    timeout=8.0,
                    disconnected_callback=_on_ble_disconnect
                ) as client:

                    if not client.is_connected:
                        raise ConnectionError("No se pudo conectar al ESP32.")

                    # Éxito de conexión: resetear contador de intentos
                    attempt = 0

                    try:
                        mtu = int(getattr(client, "mtu_size", 23) or 23)
                        self._payload_max = max(MTU_PAYLOAD_MIN, mtu - 3)
                    except Exception:
                        self._payload_max = MTU_PAYLOAD_MIN

                    try:
                        await client.start_notify(UART_NOTIFY_UUID, self._on_notify)
                    except Exception as error:
                        self._log(
                            f"No se pudo suscribir a respuestas del ESP32 ({error}). "
                            f"¿Firmware sin característica TX?"
                        )
                        raise

                    self._notify_connection(True)
                    self._log(
                        f"Conectado exitosamente a SOFIA "
                        f"(payload {self._payload_max} B)."
                    )
                    self._emit(type="CONNECTED")

                    # Prueba de vida inicial y tiempo de latido
                    self._control_queue.put(("PING", ()))
                    self._wake.set()
                    last_heartbeat = time.monotonic()

                    while self._running and client.is_connected:
                        self._expirar_pendientes()

                        # 1) Prioridad: comandos de control
                        try:
                            cmd, params = self._control_queue.get_nowait()
                        except queue.Empty:
                            cmd = None

                        if cmd is not None:
                            await self._enviar_control(client, cmd, params)
                            last_heartbeat = time.monotonic()
                            continue

                        # 2) Seguimiento: última posición disponible
                        with self._lock:
                            ang = self._ultimo_ang
                            self._ultimo_ang = None

                        if ang is not None:
                            await self._enviar_ang(client, *ang)
                            last_heartbeat = time.monotonic()
                            continue

                        # 3) Latido preventivo (heartbeat): cada 4.0s de inactividad
                        now = time.monotonic()
                        if now - last_heartbeat > 4.0:
                            last_heartbeat = now
                            self._control_queue.put(("PING", ()))
                            continue

                        # 4) Nada pendiente: esperar sin bloquear el loop
                        self._wake.clear()
                        await asyncio.to_thread(self._wake.wait, 0.05)

                    if self._running and not client.is_connected:
                        self._log("El enlace con el ESP32 se perdió.")

            except Exception as error:
                self._log(f"Fallo de conexión BLE: {error}")
                self.stats["fallos_conexion"] += 1

            finally:
                # Resolver futuros pendientes para no dejar corrutinas colgadas
                for p in list(self._pendientes.values()):
                    if p.future is not None and not p.future.done():
                        p.future.cancel()
                self._pendientes.clear()
                self._notify_connection(False)

            if not self._running or not self.auto_reconnect:
                break

            self._log(f"Esperando {reconnect_delay}s antes del siguiente reintento...")
            # Espera no bloqueante cancelable por stop()
            for _ in range(int(reconnect_delay * 10)):
                if not self._running:
                    break
                await asyncio.sleep(0.1)

        self._log(f"Sesión BLE cerrada. Estadísticas: {dict(self.stats)}")
