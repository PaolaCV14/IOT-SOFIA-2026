# Estándar de Comunicación Inalámbrica PC — ESP32 Maestro
**Proyecto SOFÍA 2026**  
**LabDST, ITESO**  
**Entregable 2:** Documento Formal del Estándar de Comunicación

**Autores:**
* Paola Monserrat Covarrubias Viveros
* Lizeth Anais Méndez Ortiz
* Juan Bernardo Orozco Quirarte
* Karen Itzel Sánchez García
* Alan Esaú Fuentes Gutiérrez

---

## 1. Introducción y Arquitectura del Enlace

El presente documento establece la especificación técnica formal del protocolo de comunicación entre la estación de control (PC) y el microcontrolador maestro (ESP32-C3) encargado de accionar los servomotores en los módulos cinemáticos de SOFÍA.

El protocolo cubre dos canales de transmisión:
1. **Canal Inalámbrico Primario (Bluetooth Low Energy - BLE):** Enlace hacia el hardware físico para posicionamiento articular y ejecución de rutinas coreográficas.
2. **Canal de Simulación (Sockets UDP):** Enlace hacia el gemelo digital en Unity / Webots para validación cinemática previa.

```
+-------------------------------------------------------------+
|             Estación de Control (PC / PySide6)              |
|   - Visualizador de Cámara a 60 FPS (MediaPipe 3D)          |
|   - Despachador de Enlace (SofiaCommDispatcher)             |
+-------------------------------------------------------------+
             │                                    │
    (Sockets UDP: 127.0.0.1:5005)       (BLE 5.0 Nordic UART)
             ▼                                    ▼
+-------------------------+          +------------------------+
|  Simulación 3D (Unity)  |          | ESP32-C3 Maestro       |
|  - Cinemática 16 pétalos|          | - PCA9685 (I2C: 0x40)  |
|  - Gemelo Digital       |          | - 2 Servos MG90S       |
+-------------------------+          +------------------------+
```

---

## 2. Parámetros de la Capa de Enlace

### 2.1 Canal de Simulación (UDP)
* **Protocolo:** UDP / IPv4.
* **Dirección IP de destino:** `127.0.0.1`.
* **Puerto:** `5005`.
* **Formato de datos:** Cadena ASCII con valores articulares delimitados por comas: `q1,q2`.

### 2.2 Canal Físico Inalámbrico (BLE Nordic UART Service)
El enlace opera bajo el perfil GATT serial estándar:

* **Nombre de difusión BLE:** `ESP32-Servos`.
* **Dirección MAC por defecto:** `70:AF:09:15:23:42` *(verificable en monitor serie / placa ESP32-C3; en macOS CoreBluetooth asigna UUID dinámico)*.
* **UUID del Servicio UART:** `6e400001-b5a3-f393-e0a9-e50e24dcca9e`.
* **UUID Característica RX (PC $\to$ ESP32):** `6e400002-b5a3-f393-e0a9-e50e24dcca9e`.
  * *Modo:* `Write` / `Write Without Response`.
* **UUID Característica TX (ESP32 $\to$ PC):** `6e400003-b5a3-f393-e0a9-e50e24dcca9e`.
  * *Modo:* `Notify` *(Canal de retorno para emisión de ACKs, NACKs, eventos EVT y telemetría).*

### 2.3 Asignación de Canales y Restricciones Mecánicas
Parámetros comprobados en el código fuente del firmware (`code/firmware-mecatronica/modulo_sofia.ino`):

* **Dirección I2C del PCA9685:** `0x40` (y dirección *All Call* `0x70`).
* **Canal Servo Q1 (Yaw horizontal):** Canal 14.
* **Canal Servo Q2 (Pitch vertical):** Canal 15.
* **Frecuencia PWM:** 50 Hz.
* **Rango angular seguro:** $60^\circ \le q \le 120^\circ$.
* **Posición neutra (Home):** $q_1 = 90^\circ, q_2 = 90^\circ$.
* **Posición de reposo:** $q_1 = 90^\circ, q_2 = 60^\circ$.

---

## 3. Estructura de las Tramas de Comunicación

Se define una estructura delimitada por caracteres centinela para garantizar integridad y evitar errores por fragmentación en el búfer serial.

### 3.1 Trama de Solicitud (PC $\to$ ESP32)
```
$<SEQ>,<CMD>,<PARAM_1>,<PARAM_2>#
```
* `$` : Carácter de inicio de trama (Start of Frame).
* `<SEQ>` : Número de secuencia entero incremental (0 a 65535).
* `<CMD>` : Comando alfanumérico en mayúsculas.
* `<PARAM_N>` : Argumentos numéricos o de texto según el comando (opcionales).
* `#` : Carácter de fin de trama (End of Frame).

*Ejemplos:*
* Comando de ángulos coordinados: `$101,ANG,90,110#`
* Comando individual de eje horizontal: `$102,Q1,75#`
* Disparo de rutina coreográfica: `$103,ROUTINE,SALUDO#`
* Prueba de conectividad: `$104,PING#`

### 3.2 Trama de Confirmación y Eventos (ESP32 $\to$ PC)
```
$<SEQ>,<STATUS>,<DATA>#
```

* `$` : Carácter de inicio de trama.
* `<SEQ>` : Número de secuencia del comando al que se responde (`0` si la trama recibida no tenía un `SEQ` válido).
* `<STATUS>` :
  * `ACK`: el comando fue recibido, validado y aceptado/ejecutado.
  * `NACK`: el comando fue rechazado (acompañado de `ERR_01`..`ERR_05`).
  * `EVT`: evento asíncrono emitido por el firmware al concluir una acción prolongada (por ejemplo, fin de rutina coreográfica).
* `<DATA>` : Datos de confirmación, código de error o nombre del evento (`DONE,<RUTINA>`).
* `#` : Carácter de fin de trama.

*Ejemplos:*

* Confirmación de ángulos ejecutados: `$101,ACK,OK,90,110#`
* Confirmación de rutina iniciada: `$103,ACK,STARTED,SALUDO#`
* Evento de finalización de rutina: `$103,EVT,DONE,SALUDO#`
* Rechazo por ángulo fuera de rango: `$105,NACK,ERR_01#`

### 3.3 Reglas del Número de Secuencia (`SEQ`), Deduplicación y Escalabilidad
* **Rango y reinicio (*wrap-around*):** El cliente PC asigna `SEQ` de forma incremental de `1` a `65535`; al llegar a `65535`, el siguiente comando reinicia en `1`. El valor `0` queda reservado para respuestas `NACK,ERR_03` cuando una trama corrupta carece de `SEQ` válido.
* **Deduplicación en ESP32 (`ultimoSeq`):** Si un reintento llega con el mismo `SEQ` que el último comando ejecutado, el firmware **no** vuelve a accionar los servomotores y reenvía la última respuesta almacenada (`ultimaRespuesta`).
* **Respuestas repetidas o fuera de orden en PC:** El cliente BLE mantiene un mapa de transacciones pendientes por `SEQ`. Cualquier respuesta con un `SEQ` ya cerrado, duplicado o fuera de orden se descarta sin alterar la transacción activa. El comando `ANG` de seguimiento no se reintenta ante timeout porque una posición angular atrasada carece de validez.
* **Identificador de módulo (escalabilidad a 16 módulos):** La versión actual (`v1.0`) direcciona un módulo cinemático de 2 GDL por enlace GATT (`ESP32-Servos`). Para escalar al arreglo completo de 16 módulos en despliegues futuros, cada nodo se identifica mediante perfil BLE dedicado (`ESP32-Servos-M01` a `ESP32-Servos-M16`) o reservando un prefijo `<MOD_ID>` opcional sobre el campo `<CMD>` en buses compartidos.

---

## 4. Identificación de Comandos del Sistema

| Comando | Argumentos | Descripción | Respuesta del Sistema |
| :--- | :--- | :--- | :--- |
| `PING` | Ninguno | Prueba de vida del enlace inalámbrico. | `$SEQ,ACK,PONG#` |
| `ANG` | `q1,q2` (Enteros: 60 a 120) | Asigna ángulos simultáneos a $q_1$ y $q_2$. | `$SEQ,ACK,OK,q1,q2#` |
| `Q1` | `angulo` (Entero: 60 a 120) | Asigna ángulo individual al eje horizontal. | `$SEQ,ACK,OK,q1#` |
| `Q2` | `angulo` (Entero: 60 a 120) | Asigna ángulo individual al eje vertical. | `$SEQ,ACK,OK,q2#` |
| `ROUTINE` | `SALUDO` \| `CORAZON` \| `TIJERA` \| `SWIPE` \| `PPT` \| `ROCA` \| `PAPEL` | Ejecuta rutina coreográfica almacenada en el ESP32 (emite `EVT,DONE` al finalizar). | `$SEQ,ACK,STARTED,<RUTINA>#` |
| `HOME` | Ninguno | Centra ambos servomotores a posición neutra ($90^\circ, 90^\circ$). | `$SEQ,ACK,OK,90,90#` |
| `REST` | Ninguno | Coloca los actuadores en posición de reposo ($90^\circ, 60^\circ$). | `$SEQ,ACK,OK,90,60#` |
| `STOP` | Ninguno | **Parada de emergencia / protección ante atasco:** desactiva señales PWM (`FULL_OFF`) en PCA9685 para liberar torque y evitar sobrecalentamiento por *stall*. | `$SEQ,ACK,STOPPED#` |

### 4.1 Equivalencia Oficial 1 a 1: Postura (Visión) $\rightarrow$ Rutina (Firmware)

| Postura detectada (Visión) | Rutina enviada (`ROUTINE`) | Duración nominal | Acción motriz en ESP32 |
| :--- | :--- | :---: | :--- |
| `SALUDO` | `SALUDO` | 3000 ms | Cabeceo vertical repetitivo ($q_2: 60^\circ \leftrightarrow 120^\circ$). |
| `CORAZON` | `CORAZON` | 2000 ms | Trayectoria orbital circular en ambos ejes. |
| `PPT` | `PPT` | 1800 ms | Tres pulsos rítmicos de conteo ($q_2: 100^\circ \leftrightarrow 75^\circ$). |
| `TIJERA` | `TIJERA` | 3200 ms | Baile en zigzag diagonal ($q_1, q_2$). |
| `ROCA` | `ROCA` | 2000 ms | Centrado neutro sostenido ($90^\circ, 90^\circ$). |
| `SWIPE` | `SWIPE` | 2100 ms | Vaivén horizontal de negación ($q_1: 60^\circ \leftrightarrow 120^\circ$, indistinto al sentido del swipe). |
| `PAPEL` | `PAPEL` | 2000 ms | Posición de reposo sostenida ($90^\circ, 60^\circ$). |

---

## 5. Códigos de Error y Respuestas de Confirmación (ACK / NACK)

Cuando el microcontrolador detecta una anomalía en la trama recibida o una instrucción no permitida, devuelve un `NACK` con un código normalizado:

| Código de Error | Nemónico | Causa del Fallo | Acción del Sistema en la GUI |
| :---: | :--- | :--- | :--- |
| `ERR_01` | `OUT_OF_RANGE` | Parámetro angular fuera del intervalo seguro ($<60^\circ$ o $>120^\circ$). | La GUI satura la posición al límite físico más cercano y registra advertencia. |
| `ERR_02` | `UNKNOWN_CMD` | Comando no registrado en el catálogo oficial. | Se descarta el comando y se notifica en la terminal de eventos. |
| `ERR_03` | `BAD_FORMAT` | Trama sin delimitadores `$` / `#` o con parámetros incompletos. | Se descarta el paquete y se registra error de sintaxis en el log. |
| `ERR_04` | `ROUTINE_BUSY` | Solicitud angular recibida mientras se ejecuta una rutina local activa. | Se omite el movimiento para proteger la trayectoria coreográfica en curso. |
| `ERR_05` | `I2C_FAIL` | El driver PCA9685 no responde en la dirección I2C `0x40`. | Se emite alerta crítica de hardware en el panel de control. |

---

## 6. Acknowledgements y Reglas de Comunicación

### 6.1 Flujo de Intercambio de Mensajes
```
     Estación PC (GUI)                             ESP32 Maestro
            │                                             │
            │─── $201,ANG,90,105# ───────────────────────►│  (Valida formato y límites)
            │                                             │  (Aplica PWM en PCA9685)
            │◄── $201,ACK,OK,90,105# ─────────────────────│  (Emite notificación TX Notify)
            │                                             │
  (Transacción completada)                                │
```

### 6.2 Parámetros de Temporización, Pérdida de Enlace y Seguridad BLE

* **Timeout de Respuesta ($T_{\text{timeout}}$):** 200 ms. Si tras 200 ms no se recibe la trama de confirmación para un comando de control, la PC considera el paquete no atendido.
* **Política de Reintentos:** Máximo 2 reintentos para comandos de control (`ROUTINE`, `HOME`, `REST`, `STOP`, `PING`) antes de reportar pérdida de respuesta.
* **Limitación de Tasa (Rate Limiting):** Durante el modo de seguimiento automático 3D por BLE, la tasa de transmisión de `ANG` se limita a `5 Hz` (`200 ms` entre envíos, conservando solo la última posición) para evitar la saturación de la cola BLE del ESP32-C3.
* **Comportamiento ante Pérdida de Enlace y Atasco:** Al detectarse desconexión (`ServerCallbacks::onDisconnect`), el firmware cancela la rutina activa, limpia el estado de secuencia y encola `HOME` (`90°, 90°`) para regresar ambos ejes a posición neutra segura. Dado que los servomotores MG90S no poseen sensor de corriente ni *encoder* integrado para detectar bloqueo mecánico (*stall*) por sí solos, ante un atasco físico la protección activa consiste en enviar `STOP` (que libera torque PWM) o cortar la alimentación externa de 5 V.
* **Seguridad del Enlace BLE:** En esta versión de laboratorio (`LabDST`), el servidor GATT opera sin emparejamiento obligatorio ni cifrado en capa de aplicación (*BLE Just Works*) para agilizar la reconexión automática desatendida (`2.5 s`). Para despliegue en entornos abiertos, se recomienda habilitar **BLE Secure Connections (LE Pairing / Passkey)** y filtrado por dirección MAC autorizada.

---

## 7. Implementación de Referencia en Código

### 7.1 Módulo de Transmisión en Python (`code/communication/ble_sender.py`)
```python
# Suscripción a la característica TX para recepción de confirmaciones
await client.start_notify(TX_CHARACTERISTIC_UUID, self._handle_ble_notification)

# Ensamblado de trama delimitada
trama = f"${self.seq_counter},{cmd},{params}#"
await client.write_gatt_char(RX_CHARACTERISTIC_UUID, trama.encode("utf-8"), response=False)
```

### 7.2 Implementación de la Característica TX en Firmware ESP32
Configuración implementada en el archivo de firmware (`code/firmware-mecatronica/modulo_sofia.ino`):
```cpp
#include <BLE2902.h>

// Puntero para la característica de transmisión TX
BLECharacteristic *pTxCharacteristic = nullptr;

#define TX_UUID "6e400003-b5a3-f393-e0a9-e50e24dcca9e"

// Configuración en setup():
pTxCharacteristic = service->createCharacteristic(
    TX_UUID,
    BLECharacteristic::PROPERTY_NOTIFY
);
pTxCharacteristic->addDescriptor(new BLE2902());

// Emisión de confirmación ACK / NACK:
void responderACK(String seq, String status, String info) {
    if (pTxCharacteristic != nullptr) {
        String respuesta = "$" + seq + "," + status + "," + info + "#";
        pTxCharacteristic->setValue(respuesta.c_str());
        pTxCharacteristic->notify();
    }
}
```

---

## 8. Resumen de Pruebas del Protocolo y Estrés

Los resultados verificados de la bancada automatizada (`code/communication/test_protocolo_estres.py`, exportados a `docs/experimental-data/registro_pruebas_ciclo.csv`) validan el protocolo y la capa de decisión bajo condiciones límite:

| Prueba ejecutada | Condición evaluada | Latencia de decisión medida | Resultado |
| :--- | :--- | :---: | :---: |
| **Ciclo Detección/Acción (7 posturas)** | `SALUDO`, `CORAZON`, `TIJERA`, `ROCA`, `SWIPE`, `PAPEL`, `PPT` | $< 0.20\text{ ms}$ (pipeline PC) | **100% EXITOSA** |
| **Estrés: Chattering rápido** | 60 transiciones aleatorias a 20 Hz con muñeca en movimiento | $0.05\text{ ms}$ | **0 falsos disparos** |
| **Estrés: Múltiples usuarios** | 2 personas en cuadro y salto angular de $80^\circ$ seguido de reposo | $0.12\text{ ms}$ | **Salto rechazado** |
| **Estrés: Iluminación variable** | 50% *dropouts* intercalados seguidos de recuperación estable | $0.10\text{ ms}$ | **Sin disparos espurios** |
| **Validación sintáctica y NACKs** | Ángulos fuera de rango (`50°`, `130°`), comando `VOLAR`, trama sin `q2` | $0.08\text{ ms}$ | **`ERR_01`, `ERR_02`, `ERR_03`** |

En enlace BLE físico, cada transacción de control mide el **RTT (Round-Trip Time)** mediante `time.monotonic()` al recibir el `ACK` correspondiente (con ventana de timeout de `200 ms`) y lo despliega en tiempo real en el badge de telemetría de la GUI (`ESP32: <RTT> ms`).
