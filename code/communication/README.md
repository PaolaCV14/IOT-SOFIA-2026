# 📡 Módulo de Comunicación y Telemetría - SOFÍA

Este paquete unifica los canales de transmisión hacia los actuadores físicos y los entornos virtuales de simulación.

---

## 📂 Archivos del Módulo

- **[`dispatcher.py`](dispatcher.py):**
  - **Clase:** `SofiaCommDispatcher`
  - **Función:** Conmuta de forma segura entre el canal Bluetooth (`BLE`) y la simulación por sockets (`UDP`).
  - **Seguridad:** Aplica saturación y límites mecánicos ($60^\circ$ a $120^\circ$) para proteger la integridad de los servomotores antes de despachar cada trama.

- **[`ble_sender.py`](ble_sender.py):**
  - **Clase:** `SofiaBleClient`
  - **Función:** Driver de bajo nivel para comunicación inalámbrica BLE con el microcontrolador **ESP32-C3** (MAC por defecto: `70:AF:09:15:23:42`).
  - **Rendimiento:** Utiliza un bucle asíncrono con `bleak` en segundo plano con una cola thread-safe (`queue.Queue`) y control de tasa de envío para no saturar la radio del robot.

---

## 🚀 Uso Rápido en Python

```python
from communication.dispatcher import SofiaCommDispatcher

# 1. Crear el despachador
comm = SofiaCommDispatcher()

# 2. Transmitir a la simulación (Unity / Webots)
comm.set_channel("UDP")
comm.send_angles(90, 90)

# 3. Transmitir al robot físico (ESP32)
comm.set_channel("BLE")
comm.connect_ble("70:AF:09:15:23:42")
comm.send_angles(75, 105)
```
