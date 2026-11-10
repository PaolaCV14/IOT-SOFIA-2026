"""
DESPACHADOR DE COMUNICACION SOFIA

Enruta comandos hacia:
- ESP32-C3 mediante BLE.
- Simulación Unity mediante UDP.

Compatible con el firmware BLE de comandos directos.
"""

import socket

try:
    from .ble_sender import (
        SofiaBleClient,
        ANGULO_MIN,
        ANGULO_MAX,
        RUTINAS
    )

except ImportError:

    from ble_sender import (
        SofiaBleClient,
        ANGULO_MIN,
        ANGULO_MAX,
        RUTINAS
    )


class SofiaCommDispatcher:

    MODE_UDP = "UDP"
    MODE_BLE = "BLE"

    RUTINAS_BLE = set(RUTINAS.keys())

    # Posiciones equivalentes para simulación UDP
    POSES_UDP = {
        "HOME": (90, 90),
        "REST": (90, 60),
        "REPOSO": (90, 60),
        "DESREPOSO": (90, 120),
        "CENTRAR": (90, 90)
    }

    def __init__(
        self,
        target_ip="127.0.0.1",
        target_port=5005,
        log_callback=None,
        ble_state_callback=None,
        ble_event_callback=None
    ):

        self.target_ip = target_ip
        self.target_port = target_port

        self.log = log_callback or (
            lambda msg: None
        )

        self.ble_state_callback = ble_state_callback or (
            lambda state: None
        )

        self.ble_event_callback = ble_event_callback or (
            lambda event: None
        )

        self.current_channel = self.MODE_UDP

        self.sock = socket.socket(
            socket.AF_INET,
            socket.SOCK_DGRAM
        )

        self.ble_client = None
        self._closed = False

    # ======================================================
    # LOG
    # ======================================================

    def _log(self, message):

        try:
            self.log(message)

        except Exception:
            pass

    # ======================================================
    # CONFIGURACION DE CANAL
    # ======================================================

    def set_channel(self, channel_type):

        channel = str(channel_type).strip().upper()

        if channel not in (
            self.MODE_UDP,
            self.MODE_BLE
        ):

            self._log(
                f"Canal no válido: {channel_type}"
            )

            return False

        if self._closed:

            self._log(
                "Dispatcher cerrado."
            )

            return False

        self.current_channel = channel

        self._log(
            f"Canal activo: {channel}"
        )

        return True

    def set_udp_target(self, ip_port_str):

        try:

            value = str(ip_port_str).strip()

            if not value:
                raise ValueError("Dirección vacía.")

            if ":" in value:

                ip, port = value.rsplit(":", 1)

                port = int(port)

                if not 1 <= port <= 65535:
                    raise ValueError("Puerto inválido.")

                self.target_ip = ip.strip()
                self.target_port = port

            else:

                self.target_ip = value

            self._log(
                f"Destino UDP: {self.target_ip}:{self.target_port}"
            )

            return True

        except (ValueError, TypeError) as error:

            self._log(
                f"Error configurando UDP: {error}"
            )

            return False

    # ======================================================
    # CONEXION BLE
    # ======================================================

    def connect_ble(self, mac_address):

        if self._closed:
            return False

        if (
            self.ble_client
            and self.ble_client.is_connected
        ):

            self._log(
                "El ESP32 ya está conectado."
            )

            return True

        if (
            self.ble_client
            and self.ble_client._running
        ):

            self._log(
                "La conexión BLE ya está iniciándose."
            )

            return True

        try:

            self.ble_client = SofiaBleClient(
                mac_address=mac_address,
                status_callback=self.log,
                connection_callback=self.ble_state_callback,
                event_callback=self.ble_event_callback
            )

            self.ble_client.start()

            self._log(
                f"Iniciando conexión BLE con {mac_address}..."
            )

            return True

        except Exception as error:

            self._log(
                f"Error iniciando BLE: {error}"
            )

            self.ble_client = None

            return False

    def disconnect_ble(self):

        if self.ble_client:

            try:
                self.ble_client.stop()

            except Exception as error:

                self._log(
                    f"Error desconectando BLE: {error}"
                )

            finally:
                self.ble_client = None

        try:
            self.ble_state_callback(False)

        except Exception:
            pass

        self._log(
            "Enlace BLE desconectado."
        )

    def is_ble_connected(self):

        return bool(
            self.ble_client
            and self.ble_client.is_connected
        )

    def is_ble_active_or_trying(self):

        return bool(
            self.ble_client
            and self.ble_client._running
        )

    # ======================================================
    # ENVIO DE ANGULOS
    # ======================================================

    def send_angles(self, q1, q2):

        if self._closed:
            return False

        try:

            q1 = int(q1)
            q2 = int(q2)

        except (ValueError, TypeError, OverflowError):

            self._log(
                "Los ángulos deben ser enteros."
            )

            return False

        q1 = max(
            ANGULO_MIN,
            min(ANGULO_MAX, q1)
        )

        q2 = max(
            ANGULO_MIN,
            min(ANGULO_MAX, q2)
        )

        if self.current_channel == self.MODE_BLE:

            if not self.is_ble_connected():

                self._log(
                    "ESP32 no conectado por BLE."
                )

                return False

            return self.ble_client.send_angles(q1, q2)

        if self.current_channel == self.MODE_UDP:

            return self._send_udp(
                f"{q1},{q2}"
            )

        return False

    # ======================================================
    # ENVIO UDP
    # ======================================================

    def _send_udp(self, mensaje):

        if self.sock is None:
            return False

        try:

            self.sock.sendto(
                mensaje.encode("utf-8"),
                (
                    self.target_ip,
                    self.target_port
                )
            )

            return True

        except OSError as error:

            self._log(
                f"Error UDP: {error}"
            )

            return False

    # ======================================================
    # ENVIO DE RUTINAS
    # ======================================================

    def send_command(self, command):

        if self._closed:
            return False

        comando = str(command).strip().upper()

        if comando not in self.RUTINAS_BLE:

            self._log(
                f"Rutina no reconocida: {comando}"
            )

            return False

        if self.current_channel == self.MODE_UDP:

            if self._send_udp(comando):

                self._log(
                    f"[UDP] Rutina enviada: {comando}"
                )

                return True

            return False

        if self.current_channel == self.MODE_BLE:

            if not self.is_ble_connected():

                self._log(
                    f"No se envió {comando}: ESP32 desconectado."
                )

                return False

            resultado = self.ble_client.send_routine(
                comando
            )

            if resultado:

                self._log(
                    f"[BLE] Rutina enviada: {comando}"
                )

            return resultado

        return False

    # ======================================================
    # COMANDOS DE CONTROL
    # ======================================================

    def send_control(self, command):

        if self._closed:
            return False

        comando = str(command).strip().upper()

        # En simulación, las poses se traducen a ángulos
        if self.current_channel == self.MODE_UDP:

            pose = self.POSES_UDP.get(comando)

            if pose is None:

                self._log(
                    f"{comando} no aplica a UDP."
                )

                return False

            return self.send_angles(*pose)

        # En el ESP32, DESREPOSO y CENTRAR son rutinas
        if comando in self.RUTINAS_BLE:

            return self.send_command(comando)

        if self.current_channel == self.MODE_BLE:

            if not self.is_ble_connected():

                self._log(
                    f"No se envió {comando}: ESP32 desconectado."
                )

                return False

            resultado = self.ble_client.send_simple(
                comando
            )

            if resultado:

                self._log(
                    f"[BLE] Comando enviado: {comando}"
                )

            return resultado

        return False

    # ======================================================
    # CIERRE
    # ======================================================

    def close(self):

        if self._closed:
            return

        self.disconnect_ble()

        if self.sock:

            try:
                self.sock.close()

            except OSError as error:

                self._log(
                    f"Error cerrando UDP: {error}"
                )

            finally:
                self.sock = None

        self._closed = True

        self._log(
            "Dispatcher cerrado."
        )