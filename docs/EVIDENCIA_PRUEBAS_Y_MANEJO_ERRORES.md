# Evidencia de Pruebas y Documentación de Manejo de Errores
**Proyecto SOFÍA 2026 — Robot Cinematotrónico de Expresión Gestual**  
**Laboratorio de Sistemas Ciberfísicos (LabDST), ITESO**  
**Entregable Formal:** Integración del Sistema de Reconocimiento y Control PC — ESP32

**Autores:**
* Paola Monserrat Covarrubias Viveros
* Lizeth Anais Méndez Ortiz
* Juan Bernardo Orozco Quirarte
* Karen Itzel Sánchez García
* Alan Esaú Fuentes Gutiérrez

---

## 1. Resumen Ejecutivo de la Etapa de Integración

En esta etapa se integró exitosamente el sistema de visión computacional y reconocimiento de posturas (desarrollado en Python / PySide6 / MediaPipe) con el microcontrolador maestro **ESP32-C3** que acciona los servomotores MG90S del robot **sOFla** a través del controlador PWM PCA9685 por I2C.

El objetivo alcanzado comprende:
1. **Protocolo bidireccional formal PC $\longleftrightarrow$ ESP32:** Transmisión de tramas estructuradas `$<SEQ>,<CMD>,<PARAMS>#` con acuses de recibo (`ACK`), rechazos tipificados (`NACK`) y eventos de fin de coreografía (`EVT,DONE`).
2. **Ciclo Detección/Acción ampliado a 7 posturas:** Mapeo unificado entre gestos dinámicos/estáticos y coreografías motrices nativas en firmware.
3. **Resiliencia ante fallos y reconexión automática:** Detección de pérdida de cámara, caída de enlace BLE con reconexión en segundo plano, y prevención de bloqueos o cierres anómalos.
4. **Bancada de pruebas y validación bajo estrés:** Evaluación ante transiciones aceleradas de postura, ruido visual y degradación de canal.

---

## 2. Protocolo de Comunicación y Flujo Detección/Acción

### 2.1 Especificación de Capa de Enlace (GATT Nordic UART)
* **UUID Servicio:** `6e400001-b5a3-f393-e0a9-e50e24dcca9e`
* **UUID Característica RX (PC $\to$ ESP32):** `6e400002-b5a3-f393-e0a9-e50e24dcca9e` (`Write Without Response`)
* **UUID Característica TX (ESP32 $\to$ PC):** `6e400003-b5a3-f393-e0a9-e50e24dcca9e` (`Notify` con descriptor `BLE2902`)

### 2.2 Diagrama de Secuencia del Ciclo Completo
```
  Cámara / Usuario         GUI (PySide6)             ESP32-C3               PCA9685 / Servos
         │                       │                      │                          │
         │── [Frame MediaPipe] ─►│                      │                          │
         │   (Postura confirmada)│                      │                          │
         │                       │── $101,ROUTINE,BAILE#►│                          │
         │                       │                      │── (Valida límites)       │
         │                       │◄── $101,ACK,STARTED,BAILE#                      │
         │                       │    [Latencia RTT ms] │                          │
         │                       │   (Seguimiento pausado)                         │
         │                       │                      │── Actualiza PWM (50Hz) ─►│ (Movimiento)
         │                       │                      │── Espera ciclo           │
         │                       │◄── $101,EVT,DONE,BAILE#                         │
         │                       │                      │                          │
         │                       │── (Seguimiento libre)│                          │
```

---

## 3. Matriz del Repertorio de Posturas y Acciones Ejecutadas

Se implementó el ciclo para el repertorio completo, superando el mínimo requerido de 5:

| # | Postura Reconocida | Tipo | Criterio de Activación | Comando Transmitido | Acción Motriz en sOFla | Duración Estimada |
|---|:---|:---:|:---|:---|:---|:---:|
| 1 | **SALUDO** | Dinámica | Oscilación lateral de mano ($>3$ cruces de dirección) | `$SEQ,ROUTINE,SALUDO#` | Asentimiento vertical repetitivo ($q_2 \in [60^\circ, 120^\circ]$) | 3000 ms |
| 2 | **CORAZÓN** | Estática | 2 manos juntas, puntas de pulgares e índices a $<0.12$ | `$SEQ,ROUTINE,CORAZON#` | Trayectoria orbital circular continua | 2000 ms |
| 3 | **TIJERA** | Estática | Dedos índice y medio extendidos en "V", otros cerrados ($>0.6$ s) | `$SEQ,ROUTINE,BAILE#` | Zigzag dinámico en ejes diagonales cruzados | 3200 ms |
| 4 | **ROCA** | Estática | Puño completamente cerrado y muñeca quieta ($>0.6$ s) | `$SEQ,ROUTINE,CENTRAR#` | Centrado neutral de calibración ($90^\circ, 90^\circ$) | 2000 ms |
| 5 | **SWIPE** | Dinámica | Desplazamiento horizontal rápido ($>20\%$ ancho en $<0.45$ s) | `$SEQ,ROUTINE,NEGAR#` | Vaivén horizontal de negación ("no", $q_1 \in [65^\circ, 115^\circ]$) | 2100 ms |
| 6 | **PAPEL** | Estática | Palma completamente extendida hacia la cámara ($>0.6$ s) | `$SEQ,ROUTINE,REPOSO#` | Descenso a posición de reposo seguro ($90^\circ, 60^\circ$) | 2000 ms |
| 7 | **PPT** | Dinámica | 3 impactos rítmicos del puño sobre la palma base | `$SEQ,ROUTINE,PPT#` | Tres pulsos rítmicos de inclinación hacia el frente | 1800 ms |

---

## 4. Documentación de Errores Encontrados y Estrategias de Mitigación

A continuación se detalla el catálogo de fallos simulados y reales durante las pruebas de integración, junto con la estrategia implementada para su neutralización:

### Error 1: Pérdida o Desconexión Física de la Cámara Web
* **Condición de ocurrencia:** Desconexión del cable USB de la cámara web durante la transmisión o intento de inicio con el sensor ocupado por otra aplicación del sistema operativo.
* **Comportamiento previo:** `cap.read()` retornaba `False` indefinidamente en un bucle cerrado, congelando la interfaz gráfica a 0 FPS o dejando el botón `Iniciar` deshabilitado de forma irrecuperable.
* **Estrategia implementada:**
  1. Contador de lecturas fallidas consecutivas en `VisionWorker`. Si se acumulan 15 fallos seguidos, el hilo pasa a estado de **recuperación activa**.
  2. Generación automática de un fotograma sintético estilizado (`QImage`) informando al usuario en pantalla: `[ CÁMARA DESCONECTADA / REINTENTANDO ]`.
  3. Reintento no bloqueante de apertura (`cv2.VideoCapture`) cada 1.5 segundos. Si la cámara se vuelve a conectar físicamente, el stream se restablece de forma transparente sin reiniciar la aplicación.
  4. Emisión de señal `worker_finished(success, msg)` para asegurar que, si el usuario decide detener manualmente la búsqueda, los botones de la GUI se reactiven correctamente.

### Error 2: Desconexión o Pérdida de Cobertura del ESP32-C3
* **Condición de ocurrencia:** Corte de alimentación de la batería LiPo del robot, reseteo del microcontrolador o alejamiento más allá del rango de radiofrecuencia Bluetooth ($>10$ metros en interiores).
* **Comportamiento previo:** El cliente Bleak lanzaba excepciones no capturadas al escribir en la característica GATT, cerrando el hilo y exigiendo reconexión manual. Si el robot se desconectaba a mitad de una rutina, los servos podían quedar en una posición forzada consumiendo corriente de reposo elevada.
* **Estrategia implementada:**
  1. En firmware (`modulo_sofia.ino`): el callback `ServerCallbacks::onDisconnect()` detecta de inmediato el corte del enlace, cancela la rutina activa y posiciona ambos servomotores en **HOME de seguridad ($90^\circ, 90^\circ$)**, liberando torque indebido y reiniciando el anuncio (`BLEAdvertising`).
  2. En host (`ble_sender.py`): bucle de **reconexión automática con backoff**. Si la conexión se cae involuntariamente, se emite `RECONNECTING`, cambiando el botón de la GUI a color ámbar (`Reconectando (N)...`) y reintentando cada 2.5 s. Al restablecerse la señal, se reanuda la telemetría sin intervención humana.
  3. **Latido (Heartbeat / Keepalive):** Si pasan más de 4 segundos sin transmisión de comandos, la PC despacha un `PING` preventivo para verificar la presencia del microcontrolador.

### Error 3: Desincronización y Retransmisión de Comandos (ACK Tardío)
* **Condición de ocurrencia:** Un paquete `ACK` se pierde por interferencia de radiofrecuencia (2.4 GHz compartida con Wi-Fi). La PC asume timeout ($200$ ms) y reintenta el comando con el mismo número de secuencia `SEQ`.
* **Comportamiento previo:** El microcontrolador volvía a ejecutar la rutina o el movimiento desde cero, produciendo sacudidas mecánicas indeseadas en el mecanismo pan-tilt.
* **Estrategia implementada:**
  1. **Deduplicación en Firmware:** El ESP32 almacena `ultimoSeq` y `ultimaRespuesta`. Si recibe un `SEQ` idéntico al último procesado, no vuelve a mover los servomotores; únicamente retransmite la trama de confirmación guardada.

### Error 4: Chattering y Disparos Falsos por Transición Rápida entre Gestos
* **Condición de ocurrencia:** El usuario mueve la mano rápidamente o cambia de postura (ej. pasa de puño a mano extendida cruzando momentáneamente por tijera).
* **Comportamiento previo:** La inferencia cuadro a cuadro detectaba la postura intermedia durante un solo frame (33 ms) y disparaba comandos coreográficos equivocados.
* **Estrategia implementada:**
  1. Máquina de estados desacoplada en `posture_mapper.py` (`PostureTrigger`).
  2. **Ventana de Sostenimiento Temporal (`HOLD_S = 0.6s`):** Las posturas estáticas deben mantenerse continuas por al menos 18 cuadros consecutivos a 30 FPS.
  3. **Filtro de Inmovilidad de Muñeca:** Se calcula el rango de desplazamiento angular de la muñeca ($q_1, q_2$). Si el usuario está moviendo el brazo (variación $>12^\circ$), se bloquea el disparo de posturas estáticas, permitiendo únicamente gestos dinámicos intencionales (`SWIPE`, `SALUDO`).
  4. **Cooldown Global (`1.0s`):** Tiempo muerto obligatorio tras el disparo de una coreografía antes de permitir la siguiente.

### Error 5: Saturación y Cierres Inesperados en la GUI
* **Condición de ocurrencia:** Excepciones en slots de PySide6 debido a desconexión de dispositivos o valores nulos en el procesamiento gráfico.
* **Comportamiento previo:** Cierre instantáneo e inesperado de la ventana de la estación de control (crash).
* **Estrategia implementada:**
  1. Instalación de hook global `sys.excepthook` mediante `error_logger.py`.
  2. Captura transparente del error, almacenamiento del volcado de pila (*stacktrace*) en archivo persistente (`registro_eventos.csv`) y notificación limpia en la terminal de usuario, **evitando el cierre de la aplicación**.

---

## 5. Resultados de las Pruebas de Estrés y Métricas

Las pruebas fueron ejecutadas con el script automatizado `code/communication/test_protocolo_estres.py`. La evidencia completa se encuentra respaldada en `docs/experimental-data/registro_pruebas_ciclo.csv`.

### Resumen de Pruebas Ejecutadas:

| Categoría de Prueba | Escenario de Evaluación | Criterio de Aceptación | Resultado | Observaciones |
|:---|:---|:---|:---:|:---|
| **Ciclo 7 Posturas** | Ejecución de SALUDO, CORAZÓN, TIJERA, ROCA, SWIPE, PAPEL, PPT | Trama formal generada, recepción de ACK y duración acorde a catálogo | **100% ÉXITO** | Latencia de procesamiento de la capa de decisión $< 1.5$ ms. |
| **Estrés: Transiciones Rápidas** | 60 cambios alternados de postura a 20 Hz con movimiento continuo | Cero disparos accidentales durante la fase de ruido | **100% ÉXITO** | El filtro temporal y de inmovilidad suprimió el 100% de falsos positivos. |
| **Estrés: Parámetros Fuera de Rango** | Envío de ángulos $q < 60^\circ$ o $q > 120^\circ$ | Emisión de `NACK,ERR_01` y saturación mecánica segura | **100% ÉXITO** | El robot nunca superó los topes mecánicos de seguridad. |
| **Estrés: Comandos Desconocidos** | Envío de mnemónicos no registrados en catálogo | Emisión de `NACK,ERR_02` sin alteración de estado | **100% ÉXITO** | Descarte limpio de tramas espurias. |
| **Resiliencia de Canal** | Simulación de desconexión abrupta del periférico | Restablecimiento con `RECONNECTING` y aseguramiento en HOME | **100% ÉXITO** | Servomotores retornan a neutro y se reanuda al reconectar. |

---

## 6. Conclusiones y Estado del Entregable

El sistema integrado cumple en su totalidad con las 4 actividades requeridas:
1. El protocolo serial delimitado opera de manera bidireccional entre la GUI y el microcontrolador maestro con acuses de recibo en tiempo real.
2. Se cuenta con tolerancia a fallos ante desconexión de cámara y ESP32 con reconexión desatendida.
3. Se verificó el ciclo detección/acción para las posturas establecidas y se incluyó el catálogo extendido.
4. Las pruebas de estrés certificaron la robustez del filtrado ante condiciones adversas de operación.

