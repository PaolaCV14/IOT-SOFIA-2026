import asyncio
from bleak import BleakClient, BleakScanner

# ==========================================================
# SOFIA 2026 - CONTROL BLE
# Compatible con el nuevo protocolo: $SEQ,CMD[,P1[,P2]]#
# ==========================================================

DEVICE_NAME = "ESP32-Servos"

UART_SERVICE_UUID = "6e400001-b5a3-f393-e0a9-e50e24dcca9e"
UART_WRITE_UUID = "6e400002-b5a3-f393-e0a9-e50e24dcca9e"  # RX
UART_NOTIFY_UUID = "6e400003-b5a3-f393-e0a9-e50e24dcca9e"  # TX

ANGULO_MIN = 60
ANGULO_MAX = 120
TIMEOUT_RESPUESTA = 5.0

# Nombres reales de rutina en el firmware nuevo.
RUTINAS = {
    "SALUDO": "SALUDO",
    "CORAZON": "CORAZON",
    "TIJERA": "TIJERA",
    "SWIPE": "SWIPE",
    "PPT": "PPT",
    "ROCA": "ROCA",
    "PAPEL": "PAPEL",
    # Alias que el propio firmware convierte:
    "BAILE": "TIJERA",
    "NEGAR": "SWIPE",
    "CENTRAR": "ROCA",
    "REPOSO": "PAPEL",
}

COMANDOS_SIMPLES = {"PING", "HOME", "REST", "STOP"}


def preparar_comando(entrada):
    """Devuelve (comando, parametros) o None si el formato no es valido."""
    texto = entrada.strip().upper()
    if not texto:
        return None

    if texto in RUTINAS:
        return "ROUTINE", [RUTINAS[texto]]

    if texto in COMANDOS_SIMPLES:
        return texto, []

    partes = [p.strip() for p in texto.split(",")]

    if partes[0] == "ANG":
        if len(partes) != 3:
            print("Formato correcto: ANG,90,90")
            return None
        try:
            q1, q2 = int(partes[1]), int(partes[2])
        except ValueError:
            print("Los angulos deben ser numeros enteros.")
            return None
        if not (ANGULO_MIN <= q1 <= ANGULO_MAX and ANGULO_MIN <= q2 <= ANGULO_MAX):
            print(f"Los angulos deben estar entre {ANGULO_MIN} y {ANGULO_MAX}.")
            return None
        return "ANG", [str(q1), str(q2)]

    if len(partes) == 2 and partes[0] in ("Q1", "Q2"):
        try:
            angulo = int(partes[1])
        except ValueError:
            print("El angulo debe ser un numero entero.")
            return None
        if not ANGULO_MIN <= angulo <= ANGULO_MAX:
            print(f"El angulo debe estar entre {ANGULO_MIN} y {ANGULO_MAX}.")
            return None
        return partes[0], [str(angulo)]

    # También acepta el formato heredado "90,90", pero lo envía
    # usando el protocolo nuevo con confirmación.
    if len(partes) == 2:
        try:
            q1, q2 = int(partes[0]), int(partes[1])
        except ValueError:
            print("Introduce dos angulos enteros, por ejemplo 90,90.")
            return None
        if not (ANGULO_MIN <= q1 <= ANGULO_MAX and ANGULO_MIN <= q2 <= ANGULO_MAX):
            print(f"Los angulos deben estar entre {ANGULO_MIN} y {ANGULO_MAX}.")
            return None
        return "ANG", [str(q1), str(q2)]

    print("Comando desconocido o formato incorrecto.")
    return None


async def buscar_esp32():
    print(f"\nBuscando '{DEVICE_NAME}' por BLE...")
    dispositivos = await BleakScanner.discover(timeout=10.0)
    for dispositivo in dispositivos:
        if dispositivo.name == DEVICE_NAME:
            print(f"[OK] Encontrado: {dispositivo.name} ({dispositivo.address})")
            return dispositivo

    print(f"[ERROR] No se encontro '{DEVICE_NAME}'. Dispositivos detectados:")
    for dispositivo in dispositivos:
        print(f"  {dispositivo.name or '(sin nombre)'} | {dispositivo.address}")
    if not dispositivos:
        print("  No se detectaron dispositivos BLE.")
    return None


def mostrar_menu():
    print("\n" + "=" * 58)
    print("                 SOFIA - CONTROL BLE")
    print("=" * 58)
    print("\n[RUTINAS]")
    print("  SALUDO / CORAZON")
    print("  TIJERA (alias: BAILE)")
    print("  SWIPE (alias: NEGAR)")
    print("  PPT")
    print("  ROCA (alias: CENTRAR)")
    print("  PAPEL (alias: REPOSO)")
    print("\n[CONTROL DE SERVOS]")
    print("  90,90       -> mover ambos")
    print("  ANG,90,90   -> mover ambos")
    print("  Q1,75       -> mover Q1")
    print("  Q2,105      -> mover Q2")
    print("\n[SISTEMA]")
    print("  PING        -> comprobar comunicacion")
    print("  HOME        -> posicion (90,90)")
    print("  REST        -> posicion (90,60)")
    print("  STOP        -> cancelar rutina y liberar PWM")
    print("  salir       -> desconectar")
    print("\nRango permitido: 60 a 120 grados")
    print("=" * 58)


class ProtocoloSOFIA:
    def __init__(self):
        self.seq = 0
        self.buffer_rx = ""
        self.respuestas = asyncio.Queue()

    def siguiente_seq(self):
        self.seq = (self.seq + 1) % 65536
        return self.seq

    def notificacion(self, _sender, data):
        """Reconstruye las tramas aunque BLE las entregue fragmentadas."""
        fragmento = bytes(data).decode("utf-8", errors="ignore")
        self.buffer_rx += fragmento

        while "$" in self.buffer_rx and "#" in self.buffer_rx:
            inicio = self.buffer_rx.find("$")
            fin = self.buffer_rx.find("#", inicio)
            if fin < 0:
                self.buffer_rx = self.buffer_rx[inicio:]
                break
            trama = self.buffer_rx[inicio:fin + 1]
            self.buffer_rx = self.buffer_rx[fin + 1:]
            print(f"\n[BLE RX] {trama}")
            try:
                self.respuestas.put_nowait(trama)
            except asyncio.QueueFull:
                pass

        # Evita que basura o fragmentos incompletos hagan crecer el buffer.
        if len(self.buffer_rx) > 256:
            self.buffer_rx = self.buffer_rx[-64:]

    async def enviar(self, client, comando, parametros):
        seq = self.siguiente_seq()
        campos = [str(seq), comando] + [str(p) for p in parametros]
        trama = "$" + ",".join(campos) + "#"

        await client.write_gatt_char(
            UART_WRITE_UUID, trama.encode("utf-8"), response=False
        )
        print(f"[BLE TX] {trama}")

        # Espera la respuesta correspondiente a este SEQ.
        limite = asyncio.get_running_loop().time() + TIMEOUT_RESPUESTA
        while True:
            restante = limite - asyncio.get_running_loop().time()
            if restante <= 0:
                print("[AVISO] No llego ACK. Revisa la conexion y el monitor serial.")
                return

            try:
                respuesta = await asyncio.wait_for(self.respuestas.get(), timeout=restante)
            except asyncio.TimeoutError:
                print("[AVISO] Tiempo de espera agotado esperando respuesta.")
                return

            contenido = respuesta[1:-1].split(",", 2)
            if not contenido:
                continue

            try:
                seq_respuesta = int(contenido[0])
            except ValueError:
                continue

            # Los eventos DONE de rutinas pueden llegar después del ACK.
            if seq_respuesta != seq:
                continue

            cuerpo = ",".join(contenido[1:])
            if cuerpo.startswith("NACK"):
                print(f"[ERROR ESP32] {cuerpo}")
            else:
                print(f"[OK ESP32] {cuerpo}")
            return


async def main():
    print("=" * 58)
    print("             SOFIA 2026 - CONTROL BLE")
    print("=" * 58)

    dispositivo = await buscar_esp32()
    if dispositivo is None:
        print("\nNo se pudo localizar la ESP32. Verifica que este encendida.")
        return

    protocolo = ProtocoloSOFIA()
    try:
        async with BleakClient(dispositivo, timeout=15.0) as client:
            if not client.is_connected:
                print("[ERROR] No se pudo establecer la conexion.")
                return

            print("\n[OK] Conectado a SOFIA.")
            # Es indispensable habilitar Notify para recibir ACK y DONE.
            await client.start_notify(UART_NOTIFY_UUID, protocolo.notificacion)
            mostrar_menu()

            while True:
                entrada = await asyncio.to_thread(input, "\nSOFIA > ")
                entrada = entrada.strip()

                if entrada.lower() in ("salir", "exit", "quit"):
                    print("Desconectando...")
                    break
                if not entrada:
                    continue

                comando = preparar_comando(entrada)
                if comando is None:
                    continue

                nombre, parametros = comando
                await protocolo.enviar(client, nombre, parametros)

            await client.stop_notify(UART_NOTIFY_UUID)

    except Exception as error:
        print(f"\n[ERROR BLE] {error}")

    print("\nConexion finalizada.")


if __name__ == "__main__":
    asyncio.run(main())
