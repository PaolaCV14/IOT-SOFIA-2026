
import asyncio
from bleak import BleakClient

ESP32_ADDRESS = "70:AF:09:15:23:42"


async def main():
    print(f"Conectando con {ESP32_ADDRESS}...")

    async with BleakClient(ESP32_ADDRESS) as client:
        print(f"Conectado: {client.is_connected}\n")

        for service in client.services:
            print(f"SERVICIO: {service.uuid}")

            for char in service.characteristics:
                print(f"  CARACTERISTICA: {char.uuid}")
                print(f"  PROPIEDADES: {', '.join(char.properties)}")

            print("-" * 50)


if __name__ == "__main__":
    asyncio.run(main())
