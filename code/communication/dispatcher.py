
"""
==============================================================
DESPACHADOR DE COMUNICACIÓN Y TELEMETRÍA (COMMUNICATION DISPATCHER)

Módulo desacoplado para enrutar datos de control hacia:
- Robot físico ESP32-C3 mediante Bluetooth Low Energy (BLE)
- Simulación virtual (Unity / Webots) mediante sockets UDP

Soporta:
- Envío de ángulos: "90,90" (UDP) / "$SEQ,ANG,90,90#" (BLE)
- Rutinas (BLE o UDP): SALUDO, CORAZON, BAILE, NEGAR, PPT, CENTRAR, REPOSO
- Comandos de control: HOME, REST, STOP, PING
==============================================================
"""

import socket

try:
    from .ble_sender import SofiaBleClient, ANGULO_MIN, ANGULO_MAX, RUTINAS
except ImportError:
    from ble_sender import SofiaBleClient, ANGULO_MIN, ANGULO_MAX, RUTINAS


class SofiaCommDispatcher:
    """Gestiona los canales de comunicación de SOFÍA."""

    MODE_UDP = "UDP"
    MODE_BLE = "BLE"

    # Rutinas almacenadas en el ESP32 (nombre -> duración nominal en ms)
    RUTINAS_BLE = set(RUTINAS)

    # Posiciones fijas para comandos HOME / REST en el canal UDP
    POSES_UDP = {"HOME": (90, 90), "REST": (90, 60)}

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

        self.log = log_callback or (lambda msg: None)
        self.ble_state_callback = (
            ble_state_callback or (lambda is_connected: None)
        )
        # Eventos del protocolo (ACK, NACK, DONE, TIMEOUT, RTT, ...)
        self.ble_event_callback = (
            ble_event_callback or (lambda event: None)
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
                connection_callback=self.ble_state_callback,
                event_callback=self.ble_event_callback
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
                resultado = self.ble_client.send_angles(q1, q2)

                if resultado is False:
                    self._log(f"No se pudo encolar el comando: {q1},{q2}")
                    return False

                return True

            except Exception as error:
                self._log(f"Error al enviar ángulos por BLE: {error}")
                return False

        if self.current_channel == self.MODE_UDP:
            # Mismo formato entero "q1,q2" que en BLE. No se registra cada
            # envío exitoso para no saturar la terminal (~30 envíos/s).
            return self._send_udp(f"{q1},{q2}")

        self._log(f"Canal desconocido: {self.current_channel}")
        return False

    # ---------------------------------------------------------
    # ENVÍO UDP (SIMULACIÓN)
    # ---------------------------------------------------------
    def _send_udp(self, mensaje):
        """Envía una cadena ASCII al destino UDP configurado."""
        if self.sock is None:
            self._log("No se pudo enviar por UDP: socket cerrado.")
            return False

        try:
            self.sock.sendto(
                mensaje.encode("utf-8"),
                (self.target_ip, self.target_port)
            )
            return True

        except OSError as error:
            self._log(f"Error en socket UDP: {error}")
            return False

    # ---------------------------------------------------------
    # ENVÍO DE RUTINAS (BLE o UDP)
    # ---------------------------------------------------------
    def send_command(self, command):
        """
        Envía una rutina por el canal activo.

        Comandos admitidos: las rutinas de RUTINAS_BLE
        (SALUDO, CORAZON, BAILE, NEGAR, PPT, CENTRAR, REPOSO).

        En BLE se encola hacia el ESP32; en UDP se envía a la
        simulación (Unity / Webots) al destino configurado.
        """
        if self._closed:
            self._log("No se puede enviar el comando: dispatcher cerrado.")
            return False

        comando = str(command).strip().upper()

        if comando not in self.RUTINAS_BLE:
            self._log(f"Comando de rutina no reconocido: {comando}")
            return False

        if self.current_channel == self.MODE_UDP:
            if self._send_udp(comando):
                self._log(
                    f"[UDP] Rutina enviada a "
                    f"{self.target_ip}:{self.target_port}: {comando}"
                )
                return True
            return False

        if self.current_channel != self.MODE_BLE:
            self._log(f"Canal desconocido: {self.current_channel}")
            return False

        if not self.is_ble_connected():
            self._log(
                f"No se envió {comando}: ESP32 no conectado por BLE."
            )
            return False

        try:
            resultado = self.ble_client.send_routine(comando)

            if resultado is False:
                self._log(f"No se pudo encolar la rutina: {comando}")
                return False

            self._log(f"Rutina encolada para envío: {comando}")
            return True

        except Exception as error:
            self._log(f"Error al enviar la rutina {comando}: {error}")
            return False

    # ---------------------------------------------------------
    # COMANDOS DE CONTROL (HOME, REST, STOP, PING)
    # ---------------------------------------------------------
    def send_control(self, command):
        """
        Envía un comando simple del protocolo.

        En BLE se transmite como trama ($SEQ,HOME#, ...) y se espera
        ACK. En UDP, HOME y REST se traducen a la pose equivalente;
        STOP y PING no aplican a la simulación.
        """
        if self._closed:
            self._log("No se puede enviar el comando: dispatcher cerrado.")
            return False

        comando = str(command).strip().upper()

        if self.current_channel == self.MODE_UDP:
            pose = self.POSES_UDP.get(comando)
            if pose is None:
                self._log(f"{comando} no aplica al canal UDP.")
                return False
            return self.send_angles(*pose)

        if not self.is_ble_connected():
            self._log(f"No se envió {comando}: ESP32 no conectado por BLE.")
            return False

        try:
            return bool(self.ble_client.send_simple(comando))
        except Exception as error:
            self._log(f"Error al enviar {comando}: {error}")
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
