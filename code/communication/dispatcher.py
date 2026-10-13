"""
==============================================================
DESPACHADOR DE COMUNICACIÓN Y TELEMETRÍA (COMMUNICATION DISPATCHER)
Módulo desacoplado para enrutar datos de control hacia:
- Robot físico ESP32-C3 mediante Bluetooth Low Energy (BLE)
- Simulación virtual (Unity / Webots) mediante sockets UDP
==============================================================
"""

import socket
try:
    from .ble_sender import SofiaBleClient, ANGULO_MIN, ANGULO_MAX
except ImportError:
    from ble_sender import SofiaBleClient, ANGULO_MIN, ANGULO_MAX


class SofiaCommDispatcher:
    """
    Gestiona y aísla los canales de comunicación de SOFÍA.
    Permite cambiar entre hardware físico y simulación sin tocar la UI.
    """
    MODE_UDP = "UDP"
    MODE_BLE = "BLE"

    def __init__(self, target_ip="127.0.0.1", target_port=5005, log_callback=None):
        self.target_ip = target_ip
        self.target_port = target_port
        self.log = log_callback or (lambda msg: None)

        self.current_channel = self.MODE_UDP
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.ble_client = None

    def set_channel(self, channel_type):
        """Cambia el canal activo entre 'UDP' y 'BLE'."""
        self.current_channel = channel_type
        self.log(f"Canal de transmisión activo: {channel_type}")

    # -------------------------------------------------------------
    # GESTIÓN BLE (ESP32 FÍSICO)
    # -------------------------------------------------------------
    def connect_ble(self, mac_address):
        """Inicia conexión Bluetooth hacia el ESP32."""
        if self.ble_client and self.ble_client.is_connected:
            return True

        self.ble_client = SofiaBleClient(mac_address=mac_address, status_callback=self.log)
        self.ble_client.start()
        return True

    def disconnect_ble(self):
        """Cierra el enlace Bluetooth."""
        if self.ble_client:
            self.ble_client.stop()
            self.ble_client = None
            self.log("Enlace BLE desconectado.")

    def is_ble_connected(self):
        return bool(self.ble_client and self.ble_client.is_connected)

    # -------------------------------------------------------------
    # TRANSMISIÓN UNIFICADA DE COMANDOS
    # -------------------------------------------------------------
    def send_angles(self, q1, q2):
        """
        Envía los ángulos (q1, q2) al canal que esté seleccionado.
        Aplica los límites mecánicos del robot.
        """
        # Aseguramos límites seguros de servomotores (60° a 120°)
        q1_clamped = max(ANGULO_MIN, min(ANGULO_MAX, int(q1)))
        q2_clamped = max(ANGULO_MIN, min(ANGULO_MAX, int(q2)))

        if self.current_channel == self.MODE_BLE:
            if self.is_ble_connected():
                self.ble_client.send_command(f"{q1_clamped},{q2_clamped}")
        elif self.current_channel == self.MODE_UDP:
            try:
                msg = f"{float(q1_clamped):.2f},{float(q2_clamped):.2f}".encode("utf-8")
                self.sock.sendto(msg, (self.target_ip, self.target_port))
            except Exception as e:
                self.log(f"Error en socket UDP: {e}")

    def close(self):
        """Libera sockets y antenas."""
        self.disconnect_ble()
        if self.sock:
            self.sock.close()
