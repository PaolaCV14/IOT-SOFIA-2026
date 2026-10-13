
import asyncio
from bleak import BleakClient

# ESP32-C3 SOFIA
ESP32_BLE = "70:AF:09:15:23:42"

# Servicio BLE UART y característica de escritura
UART_SERVICE_UUID = "6e400001-b5a3-f393-e0a9-e50e24dcca9e"
UART_WRITE_UUID = "6e400002-b5a3-f393-e0a9-e50e24dcca9e"

ANGULO_MIN = 60
ANGULO_MAX = 120

async def main():
    print("=== SOFIA: CONTROL DE SERVOS POR BLE ===")
    print(f"Conectando con {ESP32_BLE}...")

    async with BleakClient(ESP32_BLE) as client:
        if not client.is_connected:
            print("No se pudo conectar al ESP32.")
            return

        print("Conectado correctamente a SOFIA.")
        print("\nComandos:")
        print("  30,45  -> Q1=30°, Q2=45°")
        print("  Q1,30  -> Solo Q1 a 30°")
        print("  Q2,45  -> Solo Q2 a 45°")
        print("  salir  -> Desconectar")
        print("\nRango permitido: 60 a 120 grados.")

        while True:
            comando = await asyncio.to_thread(
                input, "\nIntroduce q1,q2 > "
            )
            comando = comando.strip()

            if comando.lower() in ("salir", "exit", "quit"):
                print("Desconectando de SOFIA...")
                break

            partes = comando.split(",")

            if len(partes) != 2:
                print("Formato incorrecto. Ejemplo: 30,45")
                continue

            tipo = partes[0].strip().upper()
            valor = partes[1].strip()

            try:
                angulo = int(valor)

                if not ANGULO_MIN <= angulo <= ANGULO_MAX:
                    print("Error: el ángulo debe estar entre 60 y 120.")
                    continue

                if tipo in ("Q1", "Q2"):
                    mensaje = f"{tipo},{angulo}"
                else:
                    q1 = int(partes[0].strip())
                    q2 = int(partes[1].strip())

                    if not (ANGULO_MIN <= q1 <= ANGULO_MAX and
                            ANGULO_MIN <= q2 <= ANGULO_MAX):
                        print("Error: ambos ángulos deben estar entre 60 y .")
                        continue

                    mensaje = f"{q1},{q2}"

            except ValueError:
                print("Error: introduce números enteros.")
                continue

            try:
                await client.write_gatt_char(
                    UART_WRITE_UUID,
                    mensaje.encode("utf-8"),
                    response=False
                )
                print(f"Enviado por BLE: {mensaje}")

            except Exception as error:
                print(f"Error al enviar: {error}")
                break


if __name__ == "__main__":
    asyncio.run(main())
