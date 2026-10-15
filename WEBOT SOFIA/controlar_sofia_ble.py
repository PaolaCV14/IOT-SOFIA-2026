
import asyncio
from bleak import BleakClient

# ==========================================================
# SOFIA - CONTROL DE SERVOS Y RUTINAS POR BLE
# ESP32-C3
# ==========================================================

ESP32_BLE = "70:AF:09:15:23:42"

# Servicio BLE UART y característica de escritura
UART_SERVICE_UUID = "6e400001-b5a3-f393-e0a9-e50e24dcca9e"
UART_WRITE_UUID = "6e400002-b5a3-f393-e0a9-e50e24dcca9e"

# Límites mecánicos de los servos
ANGULO_MIN = 60
ANGULO_MAX = 120


async def main():
    print("=" * 50)
    print("     SOFIA: CONTROL DE SERVOS POR BLE")
    print("=" * 50)

    print(f"\nConectando con {ESP32_BLE}...")

    try:
        async with BleakClient(ESP32_BLE, timeout=15.0) as client:

            if not client.is_connected:
                print("No se pudo conectar al ESP32.")
                return

            print("Conectado correctamente a SOFIA.")

            print("\nCOMANDOS DISPONIBLES:")
            print("------------------------------------------")
            print("  90,90       -> Mover Q1 y Q2")
            print("  Q1,90       -> Mover solamente Q1")
            print("  Q2,120      -> Mover solamente Q2")
            print("  SALUDO      -> Ejecutar rutina de saludo")
            print("  CORAZON     -> Ejecutar rutina de corazón")
            print("  salir       -> Desconectar")
            print("------------------------------------------")
            print(f"Rango permitido: {ANGULO_MIN} a {ANGULO_MAX} grados.")

            while True:
                comando = await asyncio.to_thread(
                    input, "\nIntroduce un comando > "
                )

                comando = comando.strip()

                if not comando:
                    continue

                if comando.lower() in ("salir", "exit", "quit"):
                    print("Desconectando de SOFIA...")
                    break

                comando_mayus = comando.upper()

                # ------------------------------------------
                # 1. COMANDOS DE RUTINA
                # ------------------------------------------
                if comando_mayus in ("SALUDO", "CORAZON"):
                    mensaje = comando_mayus

                # ------------------------------------------
                # 2. COMANDOS DE MOVIMIENTO
                # ------------------------------------------
                else:
                    partes = comando.split(",")

                    if len(partes) != 2:
                        print(
                            "Formato incorrecto. Usa alguno de estos formatos:"
                        )
                        print("  90,90")
                        print("  Q1,90")
                        print("  Q2,120")
                        print("  SALUDO")
                        print("  CORAZON")
                        continue

                    tipo = partes[0].strip().upper()
                    valor = partes[1].strip()

                    try:
                        # Movimiento individual de Q1 o Q2
                        if tipo in ("Q1", "Q2"):
                            angulo = int(valor)

                            if not ANGULO_MIN <= angulo <= ANGULO_MAX:
                                print(
                                    f"Error: el ángulo debe estar entre "
                                    f"{ANGULO_MIN} y {ANGULO_MAX}."
                                )
                                continue

                            mensaje = f"{tipo},{angulo}"

                        # Movimiento conjunto de ambos servos
                        else:
                            q1 = int(partes[0].strip())
                            q2 = int(partes[1].strip())

                            if not (
                                ANGULO_MIN <= q1 <= ANGULO_MAX
                                and ANGULO_MIN <= q2 <= ANGULO_MAX
                            ):
                                print(
                                    f"Error: ambos ángulos deben estar "
                                    f"entre {ANGULO_MIN} y {ANGULO_MAX}."
                                )
                                continue

                            mensaje = f"{q1},{q2}"

                    except ValueError:
                        print("Error: introduce números enteros válidos.")
                        continue

                # ------------------------------------------
                # 3. ENVÍO DEL COMANDO POR BLE
                # ------------------------------------------
                try:
                    await client.write_gatt_char(
                        UART_WRITE_UUID,
                        mensaje.encode("utf-8"),
                        response=False
                    )

                    print(f"Enviado por BLE: {mensaje}")

                except Exception as error:
                    print(f"Error al enviar el comando: {error}")
                    break

    except Exception as error:
        print(f"\nError de conexión BLE: {error}")

    print("Conexión finalizada.")


if __name__ == "__main__":
    asyncio.run(main())
