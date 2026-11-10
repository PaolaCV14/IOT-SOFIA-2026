import asyncio
from bleak import BleakClient

# ==========================================================
# SOFIA - CONTROL COMPLETO DE SERVOS Y RUTINAS POR BLE
# ESP32-C3 + PCA9685
# ==========================================================

ESP32_BLE = "24:DC:C3:48:82:76"

# Servicio BLE UART y característica RX
UART_SERVICE_UUID = "6e400001-b5a3-f393-e0a9-e50e24dcca9e"
UART_WRITE_UUID = "6e400002-b5a3-f393-e0a9-e50e24dcca9e"

# Límites mecánicos
ANGULO_MIN = 60
ANGULO_MAX = 120

# ==========================================================
# COMANDOS DISPONIBLES
# ==========================================================

RUTINAS = [
    "SALUDO",
    "CORAZON",
    "BAILE",
    "NEGAR",
    "PPT",
    "CENTRAR",
    "REPOSO",
    "DESREPOSO"
]

COMANDOS_SIMPLES = [
    "PING",
    "HOME",
    "REST",
    "STOP",
    "SCAN"
]


# ==========================================================
# VALIDAR Y PREPARAR COMANDO
# ==========================================================

def preparar_comando(comando):

    comando = comando.strip().upper()

    if not comando:
        return None

    # ------------------------------------------------------
    # 1. RUTINAS
    # ------------------------------------------------------

    if comando in RUTINAS:
        return comando

    # ------------------------------------------------------
    # 2. COMANDOS SIMPLES
    # ------------------------------------------------------

    if comando in COMANDOS_SIMPLES:
        return comando

    # ------------------------------------------------------
    # 3. CONTROL INDIVIDUAL Q1 / Q2
    # ------------------------------------------------------

    partes = comando.split(",")

    if len(partes) == 2:

        tipo = partes[0].strip()
        valor = partes[1].strip()

        if tipo in ("Q1", "Q2"):

            try:
                angulo = int(valor)

                if not ANGULO_MIN <= angulo <= ANGULO_MAX:
                    print(
                        f"Error: el ángulo debe estar entre "
                        f"{ANGULO_MIN} y {ANGULO_MAX}."
                    )
                    return None

                return f"{tipo},{angulo}"

            except ValueError:
                print("Error: introduce un ángulo entero válido.")
                return None

        # --------------------------------------------------
        # 4. MOVIMIENTO CONJUNTO
        # --------------------------------------------------

        try:
            q1 = int(partes[0].strip())
            q2 = int(partes[1].strip())

            if not (
                ANGULO_MIN <= q1 <= ANGULO_MAX
                and ANGULO_MIN <= q2 <= ANGULO_MAX
            ):
                print(
                    f"Error: ambos ángulos deben estar entre "
                    f"{ANGULO_MIN} y {ANGULO_MAX}."
                )
                return None

            return f"{q1},{q2}"

        except ValueError:
            print("Error: introduce dos ángulos enteros válidos.")
            return None

    # ------------------------------------------------------
    # 5. COMANDO ANG
    # ------------------------------------------------------

    if comando.startswith("ANG,"):

        valores = comando.split(",")

        if len(valores) != 3:
            print("Formato correcto: ANG,90,90")
            return None

        try:
            q1 = int(valores[1])
            q2 = int(valores[2])

            if not (
                ANGULO_MIN <= q1 <= ANGULO_MAX
                and ANGULO_MIN <= q2 <= ANGULO_MAX
            ):
                print("Error: los ángulos deben estar entre 60 y 120.")
                return None

            return f"ANG,{q1},{q2}"

        except ValueError:
            print("Error: introduce ángulos enteros válidos.")
            return None

    print("Comando desconocido.")
    return None


# ==========================================================
# MOSTRAR MENU
# ==========================================================

def mostrar_menu():

    print("\n" + "=" * 55)
    print("           SOFIA - CONTROL BLE")
    print("=" * 55)

    print("\n[RUTINAS]")
    print("  SALUDO      -> Ejecutar saludo")
    print("  CORAZON     -> Ejecutar corazón")
    print("  BAILE       -> Ejecutar baile")
    print("  NEGAR       -> Movimiento de negación")
    print("  PPT         -> Movimiento PPT")
    print("  CENTRAR     -> Centrar servos")
    print("  REPOSO      -> Posición de descanso")
    print("  DESREPOSO   -> Posición opuesta al descanso")

    print("\n[CONTROL DE SERVOS]")
    print("  90,90       -> Mover ambos servos")
    print("  Q1,75       -> Mover solamente Q1")
    print("  Q2,105      -> Mover solamente Q2")
    print("  ANG,90,90   -> Movimiento conjunto")

    print("\n[CONTROL DEL SISTEMA]")
    print("  PING        -> Comprobar comunicación")
    print("  HOME        -> Posición neutra")
    print("  REST        -> Posición de descanso")
    print("  STOP        -> Cancelar rutina y liberar PWM")
    print("  SCAN        -> Escanear bus I2C")

    print("\n[SALIR]")
    print("  salir       -> Desconectar BLE")

    print("-" * 55)
    print(f"Rango permitido: {ANGULO_MIN}-{ANGULO_MAX} grados")
    print("=" * 55)


# ==========================================================
# PROGRAMA PRINCIPAL
# ==========================================================

async def main():

    print("=" * 55)
    print("       SOFIA: CONTROL DE SERVOS POR BLE")
    print("=" * 55)

    print(f"\nConectando con {ESP32_BLE}...")

    try:

        async with BleakClient(
            ESP32_BLE,
            timeout=15.0
        ) as client:

            if not client.is_connected:
                print("No se pudo conectar al ESP32.")
                return

            print("\n[OK] Conectado correctamente a SOFIA.")

            mostrar_menu()

            while True:

                comando = await asyncio.to_thread(
                    input,
                    "\nSOFIA > "
                )

                comando = comando.strip()

                if not comando:
                    continue

                # Salir
                if comando.lower() in (
                    "salir",
                    "exit",
                    "quit"
                ):

                    print("\nDesconectando de SOFIA...")
                    break

                # Preparar comando
                mensaje = preparar_comando(comando)

                if mensaje is None:
                    continue

                # Enviar por BLE
                try:

                    await client.write_gatt_char(
                        UART_WRITE_UUID,
                        mensaje.encode("utf-8"),
                        response=False
                    )

                    print(f"[BLE TX] {mensaje}")

                except Exception as error:

                    print(f"[ERROR BLE] {error}")
                    break

    except Exception as error:

        print(f"\n[ERROR DE CONEXION] {error}")

    print("\nConexión finalizada.")


# ==========================================================
# EJECUCION
# ==========================================================

if __name__ == "__main__":

    asyncio.run(main())