
import asyncio
from bleak import BleakScanner


async def main():
    print("Buscando dispositivos BLE cercanos...")
    print("Escaneando durante 10 segundos...\n")

    devices = await BleakScanner.discover(
        timeout=10,
        return_adv=True
    )

    if not devices:
        print("No se encontraron dispositivos BLE.")
        return

    print(f"Se encontraron {len(devices)} dispositivos:\n")

    for address, (device, advertisement) in devices.items():
        print(f"Nombre: {device.name or advertisement.local_name or 'Sin nombre'}")
        print(f"Dirección: {device.address}")
        print(f"Señal RSSI: {advertisement.rssi} dBm")
        print(f"Servicios anunciados: {advertisement.service_uuids or 'Ninguno'}")
        print("-" * 40)


if __name__ == "__main__":
    asyncio.run(main())
