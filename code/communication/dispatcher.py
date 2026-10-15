
"""
==============================================================
DESPACHADOR DE COMUNICACIÓN Y TELEMETRÍA (COMMUNICATION DISPATCHER)

Módulo desacoplado para enrutar datos de control hacia:
- Robot físico ESP32-C3 mediante Bluetooth Low Energy (BLE)
- Simulación virtual (Unity / Webots) mediante sockets UDP

Soporta:
- Envío de ángulos: "90,90", "Q1,90", "Q2,90"
- Rutinas BLE: "SALUDO", "CORAZON"
==============================================================
"""

import socket

try:
    from .ble_sender import SofiaBleClient, ANGULO_MIN, ANGULO_MAX
except ImportError:
    from ble_sender import SofiaBleClient, ANGULO_MIN, ANGULO_MAX


class SofiaCommDispatcher:
    """Gestiona los canales de comunicación de SOFÍA."""

    MODE_UDP = "UDP"
    MODE_BLE = "BLE"

    RUTINAS_BLE = {"SALUDO", "CORAZON"}

    def __init__(
        self,
        target_ip="127.0.0.1",
        target_port=5005,
        log_callback=None,
        ble_state_callback=None
    ):
        self.target_ip = target_ip
        self.target_port = target_port

        self.log = log_callback or (lambda msg: None)
        self.ble_state_callback = (
            ble_state_callback or (lambda is_connected: None)
        )

        self.current_channel = self.MODE_UDP
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.ble_client = None
        self._closed = False

    # ---------------------------------------------------------
    # REGISTRO DE EVENTOS
    # ---------------------------------------------------------
    def _log(self, message):
        try:
            self.log(message)
        except Exception:
            pass

    # ---------------------------------------------------------
    # CONFIGURACIÓN DEL CANAL
    # ---------------------------------------------------------
    def set_channel(self, channel_type):
        """Selecciona el canal UDP o BLE."""
        channel = str(channel_type).strip().upper()

        if channel not in (self.MODE_UDP, self.MODE_BLE):
            self._log(f"Canal no válido: {channel_type}")
            return False

        if self._closed:
            self._log("No se puede cambiar el canal: dispatcher cerrado.")
            return False

        self.current_channel = channel
        self._log(f"Canal de transmisión activo: {channel}")
        return True

    def set_udp_target(self, ip_port_str):
        """Configura la IP y el puerto UDP."""
        try:
            value = str(ip_port_str).strip()

            if not value:
                raise ValueError("La dirección está vacía.")

            if ":" in value:
                ip, port = value.rsplit(":", 1)
                port = int(port)

                if not 1 <= port <= 65535:
                    raise ValueError("El puerto debe estar entre 1 y 65535.")

                self.target_ip = ip.strip()
                self.target_port = port
            else:
                self.target_ip = value

            self._log(
                f"Destino UDP configurado: "
                f"{self.target_ip}:{self.target_port}"
            )
            return True

        except (ValueError, TypeError) as error:
            self._log(f"Error al configurar IP/Puerto UDP: {error}")
            return False

    # ---------------------------------------------------------
    # GESTIÓN BLE: ESP32-C3 FÍSICO
    # ---------------------------------------------------------
    def connect_ble(self, mac_address):
        """Inicia la conexión BLE con el ESP32."""
        if self._closed:
            self._log("No se puede conectar: dispatcher cerrado.")
            return False

        if self.ble_client and self.ble_client.is_connected:
            self._log("El ESP32 ya está conectado por BLE.")
            return True

        if self.ble_client and self.ble_client._running:
            self._log("La conexión BLE ya está iniciándose.")
            return True

        try:
            self.ble_client = SofiaBleClient(
                mac_address=mac_address,
                status_callback=self.log,
                connection_callback=self.ble_state_callback
            )

            self.ble_client.start()
            self._log(f"Iniciando conexión BLE con {mac_address}...")
            return True

        except Exception as error:
            self._log(f"Error al iniciar BLE: {error}")
            self.ble_client = None
            return False

    def disconnect_ble(self):
        """Cierra el enlace Bluetooth."""
        if self.ble_client:
            try:
                self.ble_client.stop()
            except Exception as error:
                self._log(f"Error al desconectar BLE: {error}")
            finally:
                self.ble_client = None

        try:
            self.ble_state_callback(False)
        except Exception:
            pass

        self._log("Enlace BLE desconectado.")

    def is_ble_connected(self):
        """Indica si el cliente BLE está conectado."""
        return bool(
            self.ble_client and self.ble_client.is_connected
        )

    def is_ble_active_or_trying(self):
        """Indica si el cliente BLE está activo o conectándose."""
        return bool(
            self.ble_client and self.ble_client._running
        )

    # ---------------------------------------------------------
    # ENVÍO DE ÁNGULOS
    # ---------------------------------------------------------
    def send_angles(self, q1, q2):
        """
        Envía los ángulos de ambos servos por el canal seleccionado.
        Los limita al rango mecánico configurado.
        """
        if self._closed:
            self._log("No se pueden enviar ángulos: dispatcher cerrado.")
            return False

        try:
            q1 = int(q1)
            q2 = int(q2)
        except (ValueError, TypeError, OverflowError):
            self._log("Error: los ángulos deben ser números enteros.")
            return False

        q1 = max(ANGULO_MIN, min(ANGULO_MAX, q1))
        q2 = max(ANGULO_MIN, min(ANGULO_MAX, q2))

        if self.current_channel == self.MODE_BLE:
            if not self.is_ble_connected():
                self._log("No se enviaron ángulos: ESP32 no conectado por BLE.")
                return False

            try:
                mensaje = f"{q1},{q2}"
                resultado = self.ble_client.send_command(mensaje)

                if resultado is False:
                    self._log(f"No se pudo encolar el comando: {mensaje}")
                    return False

                return True

            except Exception as error:
                self._log(f"Error al enviar ángulos por BLE: {error}")
                return False

        if self.current_channel == self.MODE_UDP:
            try:
                mensaje = f"{float(q1):.2f},{float(q2):.2f}".encode("utf-8")
                self.sock.sendto(
                    mensaje,
                    (self.target_ip, self.target_port)
                )
                return True

            except OSError as error:
                self._log(f"Error en socket UDP: {error}")
                return False

        self._log(f"Canal desconocido: {self.current_channel}")
        return False

    # ---------------------------------------------------------
    # ENVÍO DE RUTINAS BLE
    # ---------------------------------------------------------
    def send_command(self, command):
        """
        Envía una rutina al ESP32.

        Comandos admitidos:
        - SALUDO
        - CORAZON

        Las rutinas solo se envían por BLE.
        """
        if self._closed:
            self._log("No se puede enviar el comando: dispatcher cerrado.")
            return False

        comando = str(command).strip().upper()

        if comando not in self.RUTINAS_BLE:
            self._log(f"Comando de rutina no reconocido: {comando}")
            return False

        if self.current_channel != self.MODE_BLE:
            self._log(
                f"No se envió {comando}: selecciona el canal BLE."
            )
            return False

        if not self.is_ble_connected():
            self._log(
                f"No se envió {comando}: ESP32 no conectado por BLE."
            )
            return False

        try:
            resultado = self.ble_client.send_command(comando)

            if resultado is False:
                self._log(f"No se pudo encolar la rutina: {comando}")
                return False

            self._log(f"Rutina encolada para envío: {comando}")
            return True

        except Exception as error:
            self._log(f"Error al enviar la rutina {comando}: {error}")
            return False

    # ---------------------------------------------------------
    # CIERRE DE RECURSOS
    # ---------------------------------------------------------
    def close(self):
        """Libera el socket UDP y desconecta BLE."""
        if self._closed:
            return

        self.disconnect_ble()

        if self.sock:
            try:
                self.sock.close()
            except OSError as error:
                self._log(f"Error al cerrar socket UDP: {error}")
            finally:
                self.sock = None

        self._closed = True
        self._log("Dispatcher cerrado.")
