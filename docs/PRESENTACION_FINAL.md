# Presentación Final del Proyecto Integral: SOFÍA 2026

**Robot Cinematotrónico de Expresión Gestual (2 GDL)**  
**Laboratorio de Sistemas Ciberfísicos (LabDST) — ITESO**  
**Equipo:** Paola Monserrat Covarrubias Viveros · Lizeth Anais Méndez Ortiz · Juan Bernardo Orozco Quirarte · Karen Itzel Sánchez García · Alan Esaú Fuentes Gutiérrez  
**Repositorio:** https://github.com/PaolaCV14/IOT-SOFIA-2026

> *Nota de uso:* Cada sección corresponde a una diapositiva lista para exponer (10–12 minutos totales) e incluye los puntos visuales para la lámina y un guion breve para el expositor.

---

## Diapositiva 1: Portada
* **Título:** SOFÍA 2026 — Robot Cinematotrónico de Expresión Gestual
* **Subtítulo:** Sistema Ciberfísico de Interacción Humano-Robot por Visión 3D y BLE
* **Datos:** LabDST — ITESO | Noviembre 2026 | Integrantes del equipo

---

## Diapositiva 2: Problema y Objetivo del Proyecto
* **Reto:** Lograr interacción humano-robot fluida, determinista y sin cables entre una estación de visión en PC y un cabezal robótico físico de 2 GDL (`q1` Yaw, `q2` Pitch).
* **Objetivo alcanzado:**
  * Cerrar el ciclo completo **Percepción (MediaPipe) → Clasificación → Protocolo BLE → Control PWM (ESP32-C3 + PCA9685)**.
  * Garantizar operación **sin bloqueos**, tolerante a fallos y reproducible.
  * Implementar **7 posturas y reacciones** (superando el mínimo de 5).

---

## Diapositiva 3: Arquitectura General de 5 Capas
* **Diagrama visual:**
  1. **Percepción Visual (`VisionWorker`):** OpenCV + MediaPipe Hand/Pose + filtro EMA ($\alpha = 0.35$).
  2. **Clasificación (`PostureTrigger`):** Estabilidad de muñeca ($\le 12^\circ$), hold estático ($0.6\text{ s}$) y cooldown ($1.0\text{ s}$).
  3. **Aplicación y Telemetría (`SofiaDashboard`):** GUI PySide6, badges en vivo, `sys.excepthook` y bitácora CSV.
  4. **Enlace Inalámbrico (`SofiaBleClient`):** Nordic UART Service, tramas `$SEQ,CMD#`, reintentos y reconexión.
  5. **Control Embebido (`modulo_sofia.ino`):** Cola FreeRTOS, motor `millis()` no bloqueante y PCA9685 I2C.
* **Idea clave para decir:** *"Cada capa está desacoplada por colas y señales; si falla la cámara o el Bluetooth, la interfaz no se congela ni se cierra."*

---

## Diapositiva 4: Diseño Mecatrónico y Consideraciones Eléctricas
* **Actuación:** 2 servomotores **MG90S** (`q1` canal 14, `q2` canal 15) en driver **PCA9685** (`0x40`, 50 Hz) conectado al **ESP32-C3** (`SDA=8`, `SCL=9`).
* **Protección mecánica y térmica:**
  * Rango angular restringido a **$60^\circ$–$120^\circ$** para evitar topes mecánicos y sobrecorriente de bloqueo (*stall*).
  * Alimentación dedicada de **5 V** al bornero del PCA9685 con tierra común.
  * Retorno automático a **HOME (`90°, 90°`)** si se pierde el enlace BLE.

---

## Diapositiva 5: Visión Computacional y Filtros Anti-Chattering
* **Detección 3D:** `HandLandmarker` + `PoseLandmarker` en hilo dedicado `QThread`.
* **Estabilidad en tiempo real:**
  * Suavizado exponencial EMA ($\alpha = 0.35$) para eliminar temblor de landmarks.
  * **Posturas dinámicas** (por evento): `SALUDO`, `SWIPE`, `PPT`.
  * **Posturas estáticas** (hold `0.6 s` + variación de muñeca $\le 12^\circ$): `CORAZON`, `TIJERA`, `ROCA`, `PAPEL`.
  * **Cooldown global (`1.0 s`):** evita disparos repetidos durante transiciones de mano.

---

## Diapositiva 6: Estándar de Comunicación PC ↔ ESP32-C3
* **Canal:** BLE GATT Nordic UART Service (`ESP32-Servos`), RX `6e400002`, TX Notify `6e400003`.
* **Formato de tramas:**
  * Solicitud: `$<SEQ>,<CMD>,<PARAM_1>,<PARAM_2>#` (`ANG`, `ROUTINE`, `HOME`, `REST`, `STOP`, `PING`).
  * Respuestas: `$SEQ,ACK,...#`, `$SEQ,NACK,ERR_01..ERR_05#`, `$SEQ,EVT,DONE,<RUTINA>#`.
* **Confiabilidad:**
  * Deduplicación por `SEQ` (`1..65535`) en el ESP32 para reintentos seguros (`200 ms`).
  * Fragmentación automática en bloques de `20 bytes` para compatibilidad con MTU base.

---

## Diapositiva 7: Repertorio Completo de 7 Posturas y Rutinas (1 a 1)
| Postura / Rutina | Tipo | Movimiento ejecutado en ESP32-C3 | Duración |
|---|---|---|---|
| `SALUDO` | Dinámica | Cabeceo vertical ($q_2: 60^\circ \leftrightarrow 120^\circ$) | 3000 ms |
| `CORAZON` | Estática | Órbita circular en ambos ejes | 2000 ms |
| `PPT` | Dinámica | 3 pulsos rítmicos de conteo | 1800 ms |
| `TIJERA` | Estática | Baile en zigzag diagonal | 3200 ms |
| `ROCA` | Estática | Centrado neutro $(90^\circ, 90^\circ)$ | 2000 ms |
| `SWIPE` | Dinámica | Vaivén horizontal de negación ($q_1: 60^\circ \leftrightarrow 120^\circ$) | 2100 ms |
| `PAPEL` | Estática | Descanso sostenido $(90^\circ, 60^\circ)$ | 2000 ms |

---

## Diapositiva 8: Tolerancia a Fallos y Pruebas Realizadas
* **Recuperación ante fallos:**
  * Desconexión de cámara → pantalla de alerta sintética y reconexión cada `1.5 s`.
  * Pérdida de enlace BLE → reconexión automática cada `2.5 s` y retorno seguro a `HOME` en el robot.
  * Excepciones inesperadas → `sys.excepthook` + bitácora en `registro_eventos.csv`.
* **Bancada automatizada (`test_protocolo_estres.py`):**
  * **100% satisfactoria** en: ciclo de las 7 posturas, 60 transiciones a 20 Hz (0 falsos positivos), salto de 80° por múltiples usuarios, parpadeo por baja luz y rechazo `NACK` (`ERR_01`–`ERR_03`).

---

## Diapositiva 9: Dificultades Encontradas y Soluciones
| Dificultad | Solución implementada |
|---|---|
| *Chattering* al cambiar de una postura a otra | Hold temporal (`0.6 s`), filtro de muñeca (`<= 12°`) y cooldown (`1.0 s`). |
| Bloqueo de `loop()` durante coreografías | Motor de rutinas por marcas de tiempo `millis()` y cola FreeRTOS. |
| Pérdida de sincronía entre cliente BLE y firmware | Unificación 1 a 1 de nombres, protocolo `$SEQ,CMD#` con `EVT,DONE` y timer de respaldo en GUI. |
| Riesgo de acceso concurrente I2C al desconectar BLE | Encolado de `HOME` hacia `loop()` vía `colaTramas` desde `onDisconnect`. |

---

## Diapositiva 10: Demostración y Evidencias
* **Carpeta oficial de videos de experimentos (OneDrive ITESO):**  
  [EVIDENCIA_PRUEBAS_Y_MANEJO_DE_ERRORES](https://iteso01-my.sharepoint.com/:f:/r/personal/bernardo_orozco_iteso_mx/_layouts/15/onedrive.aspx?id=%2Fpersonal%2Fbernardo%5Forozco%5Fiteso%5Fmx%2FDocuments%2FEVIDENCIA%5FPRUEBAS%5FY%5FMANEJO%5FDE%5FERRORES&share=cgpQ%5Fc3q%2DIRlTp4mHJuUddyvEgUCUTLs0cgR5tQS59cMol0fDQ)
* **Cierre:** Sistema integrado, documentado, reproducible (`requirements.txt` + manual + estándar) y validado tanto en pruebas de estrés como en operación física.
