# Manual de Usuario: Arquitectura y Operación del Sistema SOFÍA 2026

**Proyecto:** SOFÍA 2026 — Robot Cinematotrónico de Expresión Gestual (2 GDL)  
**Laboratorio:** Laboratorio de Sistemas Ciberfísicos (LabDST) — ITESO  
**Integrantes del Equipo:**
- Paola Monserrat Covarrubias Viveros
- Lizeth Anais Méndez Ortiz
- Juan Bernardo Orozco Quirarte
- Karen Itzel Sánchez García
- Alan Esaú Fuentes Gutiérrez

**Repositorio Oficial:** https://github.com/PaolaCV14/IOT-SOFIA-2026  
**Fecha:** Noviembre 2026

---

## 1. Propósito y Alcance
Este manual describe la arquitectura, los componentes físicos y lógicos, el procedimiento de instalación, la operación paso a paso y las consideraciones de seguridad del sistema integral **SOFÍA 2026**. Está dirigido a usuarios, evaluadores y desarrolladores que requieran operar el robot o reproducir el entorno completo PC ↔ ESP32-C3.

---

## 2. Arquitectura General del Sistema

El sistema opera bajo una arquitectura desacoplada de **cinco capas** que enlaza la percepción visual por cámara web con el control mecatrónico en tiempo real sobre Bluetooth Low Energy (BLE):

```text
+-------------------------------------------------------------------------+
| 1. CAPA DE PERCEPCIÓN VISUAL (QThread: code/gui-control/vision_worker.py)|
|    - Captura OpenCV con espejo horizontal e inferencia MediaPipe 3D     |
|    - Suavizado exponencial EMA (alpha = 0.35)                           |
|    - Recuperación automática ante desconexión de cámara (15 frames)     |
+-------------------------------------------------------------------------+
                                    │
                                    ▼
+-------------------------------------------------------------------------+
| 2. CAPA DE CLASIFICACIÓN Y FILTRADO (posture_mapper.py)                 |
|    - Gestos dinámicos por flanco y estáticos por hold (0.6 s)           |
|    - Filtro de estabilidad de muñeca (<= 12°) y cooldown global (1.0 s) |
+-------------------------------------------------------------------------+
                                    │
                                    ▼
+-------------------------------------------------------------------------+
| 3. CAPA DE APLICACIÓN Y TELEMETRÍA (main_gui.py + error_logger.py)      |
|    - Panel PySide6, badges de FPS / Latencia / RTT ESP32                |
|    - Manejador global sys.excepthook + bitácora CSV                     |
|    - Despachador unificado BLE / UDP (dispatcher.py)                    |
+-------------------------------------------------------------------------+
                                    │
                                    ▼
+-------------------------------------------------------------------------+
| 4. CAPA DE ENLACE INALÁMBRICO (ble_sender.py)                           |
|    - Nordic UART Service (RX: 6e400002, TX Notify: 6e400003)            |
|    - Tramas $SEQ,CMD,PARAMS#, reintentos (200 ms), RTT y reconexión     |
+-------------------------------------------------------------------------+
                                    │
                                    ▼
+-------------------------------------------------------------------------+
| 5. CAPA DE CONTROL EMBEBIDO (modulo_sofia.ino en ESP32-C3)              |
|    - Cola FreeRTOS (colaTramas, 8 espacios) + motor millis()            |
|    - Controlador I2C PCA9685 (0x40, 50 Hz) sobre 2 servos MG90S         |
|    - Límites físicos [60°, 120°] y retorno seguro a HOME al desconectar |
+-------------------------------------------------------------------------+
```

---

## 3. Componentes Principales

### 3.1 Hardware (Módulo Mecatrónico)
| Componente | Función | Conexión / Parámetros |
|---|---|---|
| **ESP32-C3** | Microcontrolador maestro y servidor BLE (`ESP32-Servos`) | `SDA = GPIO 8`, `SCL = GPIO 9` |
| **Adafruit PCA9685** | Driver PWM I2C de 16 canales a 50 Hz | Dirección I2C `0x40` |
| **Servo Horizontal ($q_1$, Yaw)** | Giro lateral izquierda ↔ derecha | Canal `14` del PCA9685 (`60°`–`120°`) |
| **Servo Vertical ($q_2$, Pitch)** | Inclinación abajo ↔ arriba | Canal `15` del PCA9685 (`60°`–`120°`) |
| **Fuente externa 5 V** | Alimentación exclusiva de potencia para servomotores | Conectada al bornero `V+` del PCA9685 (tierra común con ESP32-C3) |

### 3.2 Software (Estación PC)
| Módulo | Ubicación | Función principal |
|---|---|---|
| **GUI Principal** | `code/gui-control/main_gui.py` | Interfaz PySide6, video en vivo, controles y terminal |
| **Worker de Visión** | `code/gui-control/vision_worker.py` | Hilo secundario OpenCV + MediaPipe Hand/Pose |
| **Mapeo de Posturas** | `code/gui-control/posture_mapper.py` | Temporización, estabilidad de muñeca y cooldown |
| **Despachador** | `code/communication/dispatcher.py` | Enrutamiento entre canal físico (`BLE`) y simulación (`UDP`) |
| **Cliente BLE** | `code/communication/ble_sender.py` | Protocolo `$SEQ,CMD#`, `ACK`/`NACK`/`EVT,DONE` y reconexión |
| **Logger de Errores** | `code/gui-control/error_logger.py` | Registro en `docs/experimental-data/registro_eventos.csv` |
| **Firmware ESP32** | `code/firmware-mecatronica/modulo_sofia.ino` | Parser de tramas, cola FreeRTOS y 7 rutinas no bloqueantes |

---

## 4. Instalación y Reproducción

### 4.1 Preparación del Firmware (ESP32-C3)
1. Abrir `code/firmware-mecatronica/modulo_sofia.ino` en **Arduino IDE**.
2. Instalar la librería **Adafruit PWM Servo Driver Library** desde el Gestor de Librerías.
3. Seleccionar la placa **ESP32C3 Dev Module**.
4. En **Tools → Partition Scheme**, seleccionar **`Huge APP (3MB No OTA/1MB SPIFFS)`** (recomendado por el tamaño del stack BLE).
5. Compilar y cargar al ESP32-C3. Al iniciar en el Monitor Serie (`115200 baud`) debe mostrarse:
   - `PCA9685 RESPONDE`
   - `BLE anunciado como ESP32-Servos`

### 4.2 Preparación del Entorno en PC (Python)
Desde la raíz del repositorio:

```bash
python -m venv .venv
# En Windows (PowerShell):
.\.venv\Scripts\Activate.ps1
# Instalar dependencias:
pip install -r requirements.txt
```

Para ejecutar la aplicación principal:

```bash
python code/gui-control/main_gui.py
```

Para ejecutar la bancada automatizada de pruebas del protocolo y filtros sin hardware físico:

```bash
python code/communication/test_protocolo_estres.py
```

---

## 5. Procedimiento de Operación

### 5.1 Arranque y Conexión
1. Energizar el módulo mecatrónico (fuente de 5 V al PCA9685 y alimentación USB/5 V al ESP32-C3).
2. Abrir la interfaz gráfica (`main_gui.py`).
3. En el panel derecho, seleccionar el canal **ESP32 Físico (BLE)** (por defecto apunta a `ESP32-Servos`; en Windows usa la MAC configurada y en macOS el UUID de CoreBluetooth).
4. Hacer clic en **Conectar ESP32**. El botón cambiará a verde (`Desconectar`) y el badge mostrará el estado del enlace y el **RTT en ms**.
5. *(Opcional)* Si se desea probar sin robot físico, seleccionar **Simulación (UDP)** hacia `127.0.0.1:5005`.

### 5.2 Inicio de Visión y Modos de Control
1. Hacer clic en **Iniciar Cámara** para activar el flujo OpenCV + MediaPipe.
2. Seleccionar en el selector **Modo**:
   - **Seguimiento Automatico 3D**: la muñeca detectada controla $q_1$ y $q_2$ en tiempo real (acotado a `60°–120°`, envío a 5 Hz) y las posturas confirmadas disparan rutinas.
   - **Control Manual**: habilita los sliders de $q_1$ (Horizontal) y $q_2$ (Vertical).
   - **Calibracion (Home)**: envía `HOME` para centrar ambos ejes en `(90°, 90°)`.
   - **Reposo**: envía `REST` para llevar al robot a `(90°, 60°)`.
   - **Desreposo**: envía `(90°, 120°)` para elevar la vista.
3. En cualquier momento se puede usar **Pausar** (congela inferencia sin cerrar la cámara) o **Detener** para cerrar ordenadamente cámara y enlace.

### 5.3 Repertorio de Posturas y Reacciones del Robot

Todas las rutinas se ejecutan localmente en el ESP32-C3 de forma no bloqueante. Mientras dura una rutina, la GUI pausa el seguimiento de muñeca y lo reactiva al recibir `$SEQ,EVT,DONE,<RUTINA>#` (con respaldo automático por temporizador).

| Postura frente a cámara | Cómo realizarla | Rutina (`ROUTINE`) | Reacción física en SOFÍA | Duración |
|---|---|---|---|---|
| **SALUDO** | Mano abierta oscilando lateralmente (≥ 3 cambios de sentido). | `SALUDO` | Cabeceo vertical repetitivo ($q_2: 60^\circ \leftrightarrow 120^\circ$). | 3000 ms |
| **CORAZON** | Unir ambas manos formando un corazón (puntas de índices y pulgares juntas). | `CORAZON` | Trayectoria orbital circular en $q_1$ y $q_2$. | 2000 ms |
| **PPT** | Una palma base y la otra mano en puño dando 3 golpes rítmicos hacia abajo. | `PPT` | Tres pulsos rítmicos de conteo ($q_2: 100^\circ \leftrightarrow 75^\circ$). | 1800 ms |
| **TIJERA** | Dedos índice y medio extendidos en "V", anular y meñique doblados (sostener 0.6 s). | `TIJERA` | Baile dinámico en zigzag diagonal. | 3200 ms |
| **ROCA** | Puño completamente cerrado sostenido 0.6 s. | `ROCA` | Centrado neutro sostenido en $(90^\circ, 90^\circ)$. | 2000 ms |
| **SWIPE** | Deslizar la mano abierta horizontalmente (> 20% del cuadro en < 0.5 s). | `SWIPE` | Vaivén horizontal de negación ($q_1: 60^\circ \leftrightarrow 120^\circ$). | 2100 ms |
| **PAPEL** | Palma abierta completamente extendida sostenida 0.6 s. | `PAPEL` | Posición de descanso sostenida en $(90^\circ, 60^\circ)$. | 2000 ms |

---

## 6. Consideraciones de Uso, Seguridad y Solución de Problemas

### 6.1 Consideraciones Mecánicas y Eléctricas
* **Rango seguro:** nunca enviar ni forzar ángulos fuera de **`60°` a `120°`**. El firmware rechaza valores fuera de rango con `NACK,ERR_01` para evitar colisiones mecánicas o bloqueo (`stall`) de los MG90S.
* **Alimentación:** alimentar los servos desde una fuente dedicada de 5 V en el PCA9685; no alimentarlos desde el regulador de 3.3 V ni desde el pin USB del ESP32-C3.
* **Desconexión segura:** si el enlace BLE se pierde de forma abrupta, el ESP32 encola automáticamente `HOME` (`90°, 90°`) y vuelve a anunciarse para permitir reconexión automática.

### 6.2 Solución Rápida de Fallos
| Síntoma | Causa probable | Acción recomendada |
|---|---|---|
| Badge `ESP32: RECONECTANDO` | ESP32 apagado o fuera de alcance BLE | Verificar alimentación del ESP32-C3 y esperar 2.5 s a que reconecte solo. |
| Terminal muestra `ERR_05 (I2C_FAIL)` | PCA9685 desconectado o sin alimentación | Revisar cables `SDA=8`, `SCL=9`, GND común y dirección `0x40`. |
| Mensaje `[ CÁMARA DESCONECTADA ]` | Cámara desconectada u ocupada por otra app | Cerrar otras apps que usen webcam o reconectar el USB (reintenta cada 1.5 s). |
| No dispara postura estática | Movimiento excesivo de muñeca (> 12°) o menos de 0.6 s | Mantener la mano quieta durante ~0.6 s frente a la cámara con buena iluminación. |

---

## 7. Evidencia en Video de Pruebas Integrales

> **Carpeta oficial de evidencias en OneDrive (ITESO):**  
> [EVIDENCIA_PRUEBAS_Y_MANEJO_DE_ERRORES](https://iteso01-my.sharepoint.com/:f:/r/personal/bernardo_orozco_iteso_mx/_layouts/15/onedrive.aspx?id=%2Fpersonal%2Fbernardo%5Forozco%5Fiteso%5Fmx%2FDocuments%2FEVIDENCIA%5FPRUEBAS%5FY%5FMANEJO%5FDE%5FERRORES&share=cgpQ%5Fc3q%2DIRlTp4mHJuUddyvEgUCUTLs0cgR5tQS59cMol0fDQ)

En la carpeta se almacenan **7 clips individuales por postura** (15–30 s cada uno, mostrando usuario + GUI + robot físico) y las pruebas de tolerancia a fallos:
1. `EVIDENCIA_01_SALUDO`
2. `EVIDENCIA_02_CORAZON`
3. `EVIDENCIA_03_TIJERA_BAILE`
4. `EVIDENCIA_04_ROCA_HOME`
5. `EVIDENCIA_05_SWIPE_NEGAR`
6. `EVIDENCIA_06_PAPEL_REPOSO`
7. `EVIDENCIA_07_PPT_RITMICO`
8. `EVIDENCIA_08_RECUPERACION_CAMARA` / `EVIDENCIA_09_RECONEXION_BLE_ESP32` / `EVIDENCIA_10_VIDEO_DEMOSTRACION_COMPLETO`
