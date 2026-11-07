# Reporte Técnico de Integración: Reconocimiento de Posturas y Control Mechatrónico PC — ESP32
**Proyecto SOFÍA 2026 — Robot Cinematotrónico de Expresión Gestual**  
**Laboratorio de Sistemas Ciberfísicos (LabDST) — ITESO**  
**Documento Formal de Entregable:** Etapa de Integración, Tolerancia a Fallos y Pruebas de Estrés

**Integrantes del Equipo:**
* Paola Monserrat Covarrubias Viveros
* Lizeth Anais Méndez Ortiz
* Juan Bernardo Orozco Quirarte
* Karen Itzel Sánchez García
* Alan Esaú Fuentes Gutiérrez

**Fecha de Evaluación:** Noviembre 2026  
**Repositorio Oficial:** `https://github.com/bernardoorozco/IOT-SOFIA-2026`

---

## 1. Introducción y Objetivos de la Etapa

El proyecto **sOFla** consiste en una plataforma robótica de 2 grados de libertad (Yaw horizontal $q_1$ y Pitch vertical $q_2$) diseñada para la interacción humano-robot mediante gestos corporales e indicios biométricos. La mecánica está constituida por un cabezal articulado accionado por servomotores MG90S, coordinados por un controlador PWM I2C Adafruit PCA9685 y gobernados por un microcontrolador maestro **ESP32-C3**.

En esta etapa, el objetivo primordial fue **cerrar el ciclo completo de interacción cibernética**: vincular el pipeline de visión computacional (desarrollado en Python con MediaPipe y PySide6) con el firmware embebido en el ESP32 a través de un canal de comunicación inalámbrico confiable (Bluetooth Low Energy - BLE), de tal manera que cada postura realizada por un usuario frente a la cámara web provoque de manera determinista, segura y libre de bloqueos una respuesta coreográfica en el robot físico.

### Objetivos Específicos Alcanzados:
1. **Definir e implementar un protocolo de comunicación bidireccional formal:** Envío de órdenes estructuradas `$<SEQ>,<CMD>,<PARAMS>#` desde la GUI y recepción en tiempo real de confirmaciones (`ACK`), rechazos tipificados (`NACK`) y eventos de término (`EVT,DONE`).
2. **Desarrollar una capa robusta de manejo de excepciones y tolerancia a fallos:** Garantizar que situaciones adversas (cámara desconectada, pérdida de enlace BLE, tramas corruptas o excepciones en tiempo de ejecución) no provoquen el cierre inesperado (*crash*) de la aplicación, incorporando reconexión automática desatendida.
3. **Validar el ciclo detección/acción:** Verificar el flujo completo (Detección $\to$ Clasificación $\to$ Transmisión $\to$ Recepción de ACK $\to$ Movimiento de servomotores) para un repertorio de 7 posturas (superando el mínimo de 5 solicitadas).
4. **Ejecutar pruebas de estrés bajo condiciones límite:** Evaluar el comportamiento del sistema ante cambios acelerados de postura (*chattering*), múltiples usuarios simultáneos en cuadro y variaciones severas de iluminación (baja luz y contraluz).

---

## 2. Arquitectura General del Sistema Integrado

El sistema opera bajo un modelo arquitectónico de cinco capas jerárquicas desacopladas mediante señales de Qt y colas asíncronas de FreeRTOS:

```
+-----------------------------------------------------------------------------------+
| 1. CAPA DE PERCEPCIÓN VISUAL (Hilo Secundario QThread: VisionWorker)              |
|    - Captura OpenCV a 30 FPS con flip horizontal intuitivo.                       |
|    - Detección MediaPipe Tasks 3D: Hand Landmarker + Pose Landmarker Lite.        |
|    - Suavizador exponencial EMA (alpha = 0.35) para eliminación de temblor.       |
+-----------------------------------------------------------------------------------+
                                         │  (Landmarks 3D filtrados)
                                         ▼
+-----------------------------------------------------------------------------------+
| 2. CAPA DE CLASIFICACIÓN Y TEMPORIZACIÓN (PostureTrigger / posture_mapper.py)     |
|    - Distinción entre gestos dinámicos (flanco) y gestos estáticos (hold 0.6 s).  |
|    - Filtro de estabilidad angular de muñeca (variación <= 12°).                  |
|    - Enfriamiento global (cooldown 1.0 s) anti-chattering.                        |
+-----------------------------------------------------------------------------------+
                                         │  (Postura confirmada)
                                         ▼
+-----------------------------------------------------------------------------------+
| 3. CAPA DE APLICACIÓN Y TELEMETRÍA (Hilo Principal Qt: SofiaDashboard)           |
|    - Renderizado de video en tiempo real con anotaciones visuales.                |
|    - Terminal de telemetría y badges en vivo: FPS, Latencia de visión, RTT ESP32. |
|    - Despachador de comunicaciones unificado (SofiaCommDispatcher).               |
+-----------------------------------------------------------------------------------+
                                         │  (Tramas $SEQ,CMD# vía BLE)
                                         ▼
+-----------------------------------------------------------------------------------+
| 4. CAPA DE ENLACE INALÁMBRICO (Cliente Asíncrono: SofiaBleClient / ble_sender.py) |
|    - Protocolo GATT Nordic UART Service (RX: Write, TX: Notify).                  |
|    - Cola de seguimiento prioritario + deduplicación de secuencias (SEQ 1..65535).|
|    - Timeouts de 200 ms, reintentos automáticos y reconexión en segundo plano.    |
+-----------------------------------------------------------------------------------+
                                         │  (Radioenlace BLE 2.4 GHz)
                                         ▼
+-----------------------------------------------------------------------------------+
| 5. CAPA DE CONTROL EMBEBIDO (Firmware C++: modulo_sofia.ino / ESP32-C3 Maestro)   |
|    - FreeRTOS: Separación entre interrupciones BLE y loop() de actuadores.        |
|    - Motor de coreografías no bloqueante gobernado por marcas de tiempo millis(). |
|    - Driver I2C (0x40) a 50 Hz hacia PCA9685 accionado sobre 2 servos MG90S.     |
|    - Sistema de seguridad: Centrado automático a HOME (90°, 90°) al desconectar.  |
+-----------------------------------------------------------------------------------+
```

---

## 3. Especificación Formal del Protocolo de Comunicación PC $\longleftrightarrow$ ESP32

Para cumplir con el estándar técnico formal definido en el laboratorio, se descartó el envío de cadenas de texto no estructuradas y se implementó un protocolo serial enmarcado por caracteres centinela (`$` de inicio y `#` de fin).

### 3.1 Parámetros de la Capa GATT (Nordic UART Service)
* **Nombre de Difusión BLE:** `ESP32-Servos`
* **UUID Servicio UART:** `6e400001-b5a3-f393-e0a9-e50e24dcca9e`
* **UUID Característica RX (PC $\to$ ESP32):** `6e400002-b5a3-f393-e0a9-e50e24dcca9e` *(Modo: Write Without Response)*
* **UUID Característica TX (ESP32 $\to$ PC):** `6e400003-b5a3-f393-e0a9-e50e24dcca9e` *(Modo: Notify con descriptor BLE2902)*
* **Tamaño Máximo de Carga Útil (Payload):** Fragmentación dinámica según MTU negociado (base 20 bytes seguros).

### 3.2 Estructura de las Tramas de Solicitud (PC $\to$ ESP32)
```
$<SEQ>,<CMD>,<PARAM_1>,<PARAM_2>#
```
* `$` : Carácter delimitador de inicio (Start of Frame).
* `<SEQ>` : Entero incremental (1 a 65535) para identificación unívoca y deduplicación.
* `<CMD>` : Nemónico del comando en mayúsculas (`ANG`, `ROUTINE`, `HOME`, `REST`, `STOP`, `PING`).
* `<PARAM_N>` : Parámetros numéricos o alfanuméricos asociados al comando.
* `#` : Carácter delimitador de término (End of Frame).

### 3.3 Estructura de las Tramas de Respuesta (ESP32 $\to$ PC)
```
$<SEQ>,<STATUS>,<DATOS...>#
```
* `<STATUS>` toma tres valores normalizados:
  1. `ACK` : Comando recibido, validado y aceptado para ejecución.
  2. `NACK` : Comando rechazado por sintaxis, valores fuera de rango o periférico ocupado.
  3. `EVT` : Evento asíncrono emitido por el firmware (p. ej. fin de una rutina coreográfica).

### 3.4 Catálogo de Respuestas y Errores Tipificados
| Código | Nemónico | Significado | Acción del Host en la GUI |
|:---:|:---|:---|:---|
| `ACK` | `OK` / `STARTED` / `PONG` | Comando admitido y en ejecución. | Registra RTT y actualiza badge de latencia. |
| `EVT` | `DONE,<RUTINA>` | El robot completó el último paso de la coreografía. | Desbloquea inmediatamente el modo de seguimiento libre. |
| `ERR_01` | `OUT_OF_RANGE` | Parámetro angular fuera del límite seguro ($60^\circ$ a $120^\circ$). | La GUI satura la posición al límite físico permitido. |
| `ERR_02` | `UNKNOWN_CMD` | Mnemónico o rutina no registrada en firmware. | Descarta el paquete y notifica en terminal. |
| `ERR_03` | `BAD_FORMAT` | Trama con parámetros faltantes o sin centinelas. | Descarta el paquete por error de sintaxis. |
| `ERR_04` | `ROUTINE_BUSY` | Solicitud recibida mientras se ejecuta otra coreografía. | Omite el movimiento para proteger la trayectoria actual. |
| `ERR_05` | `I2C_FAIL` | El driver PCA9685 no respondió en la dirección I2C `0x40`. | Emite alerta crítica de hardware en la GUI. |

---

## 4. Catálogo del Repertorio de Posturas y Acciones en sOFla

Se implementó el ciclo de reconocimiento y accionamiento para **7 posturas** (superando las 5 exigidas):

```
                                REPERTORIO DE POSTURAS SOFÍA
                                              │
                     ┌────────────────────────┴────────────────────────┐
                     ▼                                                 ▼
            POSTURAS DINÁMICAS                               POSTURAS ESTÁTICAS
          (Análisis multi-cuadro)                         (Sostenimiento temporal)
         1. SALUDO  ──► Rutina SALUDO                     4. CORAZÓN ──► Rutina CORAZON
         2. SWIPE   ──► Rutina NEGAR                      5. TIJERA  ──► Rutina BAILE
         3. PPT     ──► Rutina PPT                        6. ROCA    ──► Rutina CENTRAR
                                                          7. PAPEL   ──► Rutina REPOSO
```

### Tabla Resumen de Mapeo Postura $\longleftrightarrow$ Acción Motriz:
| # | Postura | Tipo | Criterio Cinemático MediaPipe | Trama Enviada | Acción Motriz del Robot sOFla | Duración |
|:---:|:---|:---:|:---|:---|:---|:---:|
| 1 | **SALUDO** | Dinámica | Mano abierta oscilando lateralmente ($>3$ cambios de sentido). | `$SEQ,ROUTINE,SALUDO#` | Asentimiento vertical repetitivo ($q_2 \in [60^\circ, 120^\circ]$). | 3000 ms |
| 2 | **CORAZÓN** | Estática | 2 manos juntas; puntas de índices y pulgares a $D < 0.12$. | `$SEQ,ROUTINE,CORAZON#` | Trayectoria orbital circular continua en ambos ejes. | 2000 ms |
| 3 | **TIJERA** | Estática | Dedos índice y medio extendidos en "V", anular y meñique doblados. | `$SEQ,ROUTINE,BAILE#` | Zigzag dinámico en ejes diagonales cruzados. | 3200 ms |
| 4 | **ROCA** | Estática | Puño completamente cerrado, todos los dedos flexionados. | `$SEQ,ROUTINE,CENTRAR#` | Centrado neutro de calibración ($q_1=90^\circ, q_2=90^\circ$). | 2000 ms |
| 5 | **SWIPE** | Dinámica | Mano abierta recorriendo $>20\%$ de pantalla en $<0.45$ s. | `$SEQ,ROUTINE,NEGAR#` | Vaivén horizontal de negación ("no", $q_1 \in [65^\circ, 115^\circ]$). | 2100 ms |
| 6 | **PAPEL** | Estática | Mano completamente extendida y abierta hacia la cámara. | `$SEQ,ROUTINE,REPOSO#` | Descenso a posición de reposo seguro ($q_1=90^\circ, q_2=60^\circ$). | 2000 ms |
| 7 | **PPT** | Dinámica | Puño golpeando rítmicamente 3 veces la palma horizontal base. | `$SEQ,ROUTINE,PPT#` | Tres pulsos rítmicos de cabeceo hacia el frente. | 1800 ms |

---

### Detalle de Posturas y Evidencia Fotográfica

#### Postura 1: Saludo ("Hola") — Dinámica
* **Descripción del movimiento:** El usuario levanta la mano abierta a la altura del rostro y la sacude de un lado a otro. El detector exige al menos 3 cruces de dirección horizontal consecutivos.
* **Respuesta en sOFla:** El cabezal efectúa 3 cabeceos verticales amplios simulando una reverencia de bienvenida.

> **Repositorio de Evidencia en la Nube:** [EVIDENCIA_PRUEBAS_Y_MANEJO_DE_ERRORES](https://iteso01-my.sharepoint.com/:f:/r/personal/bernardo_orozco_iteso_mx/_layouts/15/onedrive.aspx?id=%2Fpersonal%2Fbernardo%5Forozco%5Fiteso%5Fmx%2FDocuments%2FEVIDENCIA%5FPRUEBAS%5FY%5FMANEJO%5FDE%5FERRORES&share=cgpQ%5Fc3q%2DIRlTp4mHJuUddyvEgUCUTLs0cgR5tQS59cMol0fDQ)  
> **Archivo a consultar en la carpeta:** `EVIDENCIA_01_SALUDO` *(formato .mp4 o .jpg)*

---

#### Postura 2: Corazón con Dos Manos — Estática
* **Descripción del movimiento:** Se unen ambas manos doblando los pulgares e índices para formar un corazón cerrado. Requiere que ambas manos permanezcan estables en cuadro durante al menos 0.6 s.
* **Respuesta en sOFla:** Los servomotores se mueven coordinadamente en cuadratura de fase, describiendo un movimiento circular continuo de apreciación.

> **Repositorio de Evidencia en la Nube:** [EVIDENCIA_PRUEBAS_Y_MANEJO_DE_ERRORES](https://iteso01-my.sharepoint.com/:f:/r/personal/bernardo_orozco_iteso_mx/_layouts/15/onedrive.aspx?id=%2Fpersonal%2Fbernardo%5Forozco%5Fiteso%5Fmx%2FDocuments%2FEVIDENCIA%5FPRUEBAS%5FY%5FMANEJO%5FDE%5FERRORES&share=cgpQ%5Fc3q%2DIRlTp4mHJuUddyvEgUCUTLs0cgR5tQS59cMol0fDQ)  
> **Archivo a consultar en la carpeta:** `EVIDENCIA_02_CORAZON` *(formato .mp4 o .jpg)*

---

#### Postura 3: Tijera / Paz — Estática
* **Descripción del movimiento:** Mano con dedos índice y medio separados en ángulo agudo mientras el pulgar retiene los dedos anular y meñique contra la palma.
* **Respuesta en sOFla:** Rutina coreográfica `BAILE`: el robot recorre las diagonales opuestas $(\pm 20^\circ)$ a ritmo constante.

> **Repositorio de Evidencia en la Nube:** [EVIDENCIA_PRUEBAS_Y_MANEJO_DE_ERRORES](https://iteso01-my.sharepoint.com/:f:/r/personal/bernardo_orozco_iteso_mx/_layouts/15/onedrive.aspx?id=%2Fpersonal%2Fbernardo%5Forozco%5Fiteso%5Fmx%2FDocuments%2FEVIDENCIA%5FPRUEBAS%5FY%5FMANEJO%5FDE%5FERRORES&share=cgpQ%5Fc3q%2DIRlTp4mHJuUddyvEgUCUTLs0cgR5tQS59cMol0fDQ)  
> **Archivo a consultar en la carpeta:** `EVIDENCIA_03_TIJERA_BAILE` *(formato .mp4 o .jpg)*

---

#### Postura 4: Roca / Puño Cerrado — Estática
* **Descripción del movimiento:** Puño completamente cerrado mirando hacia el sensor, sostenido durante 0.6 s sin desplazamiento angular.
* **Respuesta en sOFla:** Rutina `CENTRAR`: Ambos actuadores se posicionan exactamente en el origen neutro $(90^\circ, 90^\circ)$ y sostienen posición para calibración de cero mecánico.

> **Repositorio de Evidencia en la Nube:** [EVIDENCIA_PRUEBAS_Y_MANEJO_DE_ERRORES](https://iteso01-my.sharepoint.com/:f:/r/personal/bernardo_orozco_iteso_mx/_layouts/15/onedrive.aspx?id=%2Fpersonal%2Fbernardo%5Forozco%5Fiteso%5Fmx%2FDocuments%2FEVIDENCIA%5FPRUEBAS%5FY%5FMANEJO%5FDE%5FERRORES&share=cgpQ%5Fc3q%2DIRlTp4mHJuUddyvEgUCUTLs0cgR5tQS59cMol0fDQ)  
> **Archivo a consultar en la carpeta:** `EVIDENCIA_04_ROCA_HOME` *(formato .mp4 o .jpg)*

---

#### Postura 5: Swipe / Deslizar la Mano — Dinámica
* **Descripción del movimiento:** Mano extendida desplazándose con velocidad superior a $0.8\text{ m/s}$ de un extremo al otro de la imagen.
* **Respuesta en sOFla:** Rutina `NEGAR`: El servo horizontal $q_1$ oscila rápidamente entre $65^\circ$ y $115^\circ$ emulando un ademán de desaprobación o negación ("no").

> **Repositorio de Evidencia en la Nube:** [EVIDENCIA_PRUEBAS_Y_MANEJO_DE_ERRORES](https://iteso01-my.sharepoint.com/:f:/r/personal/bernardo_orozco_iteso_mx/_layouts/15/onedrive.aspx?id=%2Fpersonal%2Fbernardo%5Forozco%5Fiteso%5Fmx%2FDocuments%2FEVIDENCIA%5FPRUEBAS%5FY%5FMANEJO%5FDE%5FERRORES&share=cgpQ%5Fc3q%2DIRlTp4mHJuUddyvEgUCUTLs0cgR5tQS59cMol0fDQ)  
> **Archivo a consultar en la carpeta:** `EVIDENCIA_05_SWIPE_NEGAR` *(formato .mp4 o .jpg)*

---

#### Postura 6: Papel / Mano Abierta — Estática
* **Descripción del movimiento:** Palma abierta con los cinco dedos separados y orientados verticalmente hacia la cámara.
* **Respuesta en sOFla:** Rutina `REPOSO`: El robot baja la cabeza a $q_2 = 60^\circ$ (postura de sueño/descanso para reducir consumo de corriente en los servomotores).

> **Repositorio de Evidencia en la Nube:** [EVIDENCIA_PRUEBAS_Y_MANEJO_DE_ERRORES](https://iteso01-my.sharepoint.com/:f:/r/personal/bernardo_orozco_iteso_mx/_layouts/15/onedrive.aspx?id=%2Fpersonal%2Fbernardo%5Forozco%5Fiteso%5Fmx%2FDocuments%2FEVIDENCIA%5FPRUEBAS%5FY%5FMANEJO%5FDE%5FERRORES&share=cgpQ%5Fc3q%2DIRlTp4mHJuUddyvEgUCUTLs0cgR5tQS59cMol0fDQ)  
> **Archivo a consultar en la carpeta:** `EVIDENCIA_06_PAPEL_REPOSO` *(formato .mp4 o .jpg)*

---

#### Postura 7: Intención de Jugar Piedra, Papel o Tijera (PPT) — Dinámica
* **Descripción del movimiento:** Una mano extendida plana como yunque horizontal y la otra mano en puño golpeando tres veces consecutivas con intervalos rítmicos entre 0.25 y 0.9 segundos.
* **Respuesta en sOFla:** Rutina `PPT`: El robot realiza tres pulsos mecánicos sincrónicos hacia adelante preparándose para la partida interactiva.

> **Repositorio de Evidencia en la Nube:** [EVIDENCIA_PRUEBAS_Y_MANEJO_DE_ERRORES](https://iteso01-my.sharepoint.com/:f:/r/personal/bernardo_orozco_iteso_mx/_layouts/15/onedrive.aspx?id=%2Fpersonal%2Fbernardo%5Forozco%5Fiteso%5Fmx%2FDocuments%2FEVIDENCIA%5FPRUEBAS%5FY%5FMANEJO%5FDE%5FERRORES&share=cgpQ%5Fc3q%2DIRlTp4mHJuUddyvEgUCUTLs0cgR5tQS59cMol0fDQ)  
> **Archivo a consultar en la carpeta:** `EVIDENCIA_07_PPT_RITMICO` *(formato .mp4 o .jpg)*

---

## 5. Documentación Exhaustiva de Errores y Estrategias de Mitigación

A continuación se presenta la bitácora técnica de anomalías identificadas durante las pruebas de estrés, indicando las condiciones de reproducción, el comportamiento observado y la solución implementada:

### Caso 1: Pérdida o Desconexión Física de la Cámara Web
* **Condición de ocurrencia:** Desconexión del cable USB de la cámara durante el stream o intento de arranque con la cámara bloqueada por otra aplicación del sistema operativo.
* **Comportamiento previo (falla original):** `cap.read()` retornaba `False` indefinidamente en un bucle cerrado, congelando la interfaz a 0 FPS o dejando los botones `Iniciar/Pausar` inhabilitados permanentemente.
* **Estrategia implementada:**
  1. Contador de lecturas fallidas en `VisionWorker`. Tras 15 fallos seguidos, el hilo activa el modo de **recuperación automática**.
  2. Generación en memoria de un fotograma sintético (`QImage`) indicando al usuario: `[ CÁMARA DESCONECTADA / REINTENTANDO ]`.
  3. Reintento no bloqueante de apertura con `cv2.VideoCapture` cada 1.5 segundos. Al reinsertar el cable USB, el stream se recupera solo sin reiniciar el programa.
  4. Emisión de `worker_finished` para sincronizar el estado visual de los botones de la interfaz.

> **Repositorio de Evidencia en la Nube:** [EVIDENCIA_PRUEBAS_Y_MANEJO_DE_ERRORES](https://iteso01-my.sharepoint.com/:f:/r/personal/bernardo_orozco_iteso_mx/_layouts/15/onedrive.aspx?id=%2Fpersonal%2Fbernardo%5Forozco%5Fiteso%5Fmx%2FDocuments%2FEVIDENCIA%5FPRUEBAS%5FY%5FMANEJO%5FDE%5FERRORES&share=cgpQ%5Fc3q%2DIRlTp4mHJuUddyvEgUCUTLs0cgR5tQS59cMol0fDQ)  
> **Archivo a consultar en la carpeta:** `EVIDENCIA_08_RECUPERACION_CAMARA` *(formato .mp4 o .jpg)*

---

### Caso 2: Desconexión o Pérdida de Cobertura del ESP32-C3
* **Condición de ocurrencia:** Corte de batería LiPo en el robot, reinicio por botón físico o alejamiento de la PC a más de 10 metros en interiores.
* **Comportamiento previo (falla original):** Las escrituras GATT de Bleak arrojaban excepciones no capturadas, matando el hilo de comunicaciones y forzando a reiniciar la GUI. El robot podía quedarse atascado en una pose forzada con alto consumo térmico.
* **Estrategia implementada:**
  1. **En Firmware (`modulo_sofia.ino`):** El callback `onDisconnect()` detecta el corte en microsegundos, interrumpe cualquier coreografía y mueve de inmediato ambos servos a **HOME seguro ($90^\circ, 90^\circ$)**, reiniciando el anuncio BLE (`startAdvertising()`).
  2. **En Host (`ble_sender.py`):** Bucle asíncrono con **reconexión automática con backoff (2.5 s)**. El botón de la GUI cambia a color ámbar (`Reconectando (N)...`) y el badge muestra `ESP32: RECONECTANDO`. Al volver la señal, la sesión se restablece limpiamente.
  3. **Latido Preventivo (Heartbeat):** Envío automático de `PING` cada 4.0 s de silencio para detectar caídas de señal sin esperar a que el usuario mueva la mano.

> **Repositorio de Evidencia en la Nube:** [EVIDENCIA_PRUEBAS_Y_MANEJO_DE_ERRORES](https://iteso01-my.sharepoint.com/:f:/r/personal/bernardo_orozco_iteso_mx/_layouts/15/onedrive.aspx?id=%2Fpersonal%2Fbernardo%5Forozco%5Fiteso%5Fmx%2FDocuments%2FEVIDENCIA%5FPRUEBAS%5FY%5FMANEJO%5FDE%5FERRORES&share=cgpQ%5Fc3q%2DIRlTp4mHJuUddyvEgUCUTLs0cgR5tQS59cMol0fDQ)  
> **Archivo a consultar en la carpeta:** `EVIDENCIA_09_RECONEXION_BLE_ESP32` *(formato .mp4 o .jpg)*

---

### Caso 3: Desincronización y Retransmisión de Comandos (ACK Tardío)
* **Condición de ocurrencia:** Pérdida del paquete `ACK` en el radioenlace por ruido electromagnético. La PC entra en timeout (200 ms) y retransmite la orden con el mismo `SEQ`.
* **Comportamiento previo (falla original):** El robot volvía a empezar la coreografía desde cero, provocando un tirón mecánico perjudicial para los engranes metálicos del MG90S.
* **Estrategia implementada:**
  1. **Deduplicación en Firmware:** El ESP32 almacena `ultimoSeq` y `ultimaRespuesta`. Si recibe un `SEQ` repetido, no mueve los motores: únicamente reenvía la respuesta previa almacenada en memoria RAM.

---

### Caso 4: Transiciones Aceleradas y Chattering entre Gestos
* **Condición de ocurrencia:** El usuario cambia de postura rápidamente (p. ej. pasa de puño a palma abierta cruzando accidentalmente por la forma de tijera durante 1 cuadro de 33 ms).
* **Comportamiento previo (falla original):** Disparo accidental de la rutina `BAILE` en lugar de esperar la pose definitiva.
* **Estrategia implementada:**
  1. **Ventana de Sostenimiento Temporal (`HOLD_S = 0.6s`):** Exige que la postura estática permanezca ininterrumpida durante al menos 18 cuadros consecutivos.
  2. **Filtro de Inmovilidad de Muñeca:** Si la muñeca se desplaza más de $12^\circ$, se bloquea el disparo de posturas estáticas, permitiendo únicamente gestos dinámicos intencionales (`SWIPE`, `SALUDO`).
  3. **Cooldown Global de 1.0 segundo:** Tiempo de enfriamiento obligatorio tras cualquier disparo de comando.

---

### Caso 5: Múltiples Usuarios en Cuadro (Conflicto y Salto Angular)
* **Condición de ocurrencia:** Dos o más personas paradas frente a la cámara web moviendo los brazos simultáneamente.
* **Comportamiento observado:**
  - *Visión:* MediaPipe detecta hasta 2 manos (`num_hands=2`). El índice prioritario (`hand_landmarks[0]`) alternaba caóticamente entre un usuario y otro, produciendo saltos espaciales de hasta $80^\circ$ en una sola fracción de segundo.
  - *Robot:* El mecanismo pan-tilt intentaba seguir a ambos usuarios a la vez con sacudidas bruscas. Además, una mano abierta de la persona A y un puño de la persona B podían activar falsamente la postura de dos manos `PPT`.
* **Estrategia implementada:**
  1. El filtro de inmovilidad de muñeca de `PostureTrigger` detecta variaciones $>12^\circ$ causadas por el salto de persona y bloquea el disparo de rutinas estáticas hasta que un único usuario domina el encuadre.
  2. Coherencia bimanual geométrica: Las posturas de dos manos (`CORAZÓN` y `PPT`) exigen proximidad física estricta entre muñecas ($D < 0.12$ o contacto vertical directo). Manos pertenecientes a personas distintas (separadas por $>40\text{ cm}$) son descartadas automáticamente.
  3. Cola de seguimiento de reemplazo: En seguimiento angular continuo solo se guarda la última muestra disponible (`_ultimo_ang`), descartando posiciones intermedias pasadas y evitando oscilaciones acumuladas.

---

### Caso 6: Variaciones Extremas de Iluminación (Baja Luz y Contraluz)
* **Condición de ocurrencia:** Iluminación ambiental deficiente ($<50\text{ lux}$) o contraluz intensa generada por ventanas o luminarias detrás del usuario.
* **Comportamiento observado:**
  - *Visión:* La confianza de MediaPipe cae por debajo de 0.7, produciendo parpadeo intermitente (*dropouts* de 1 a 3 cuadros donde la mano desaparece y reaparece).
  - *Comunicación:* Si el sistema fuera sensible cuadro a cuadro, los contadores de tiempo se resetearían en bucle infinito impidiendo la confirmación de posturas.
* **Estrategia implementada:**
  1. **Memoria de Persistencia (Grace Hold Frames):** Los detectores de gestos dinámicos mantienen una gracia de 12 a 16 cuadros. Si la mano se pierde momentáneamente por baja reflectancia, el estado de conteo no se pierde.
  2. **Filtro Exponencial EMA:** El suavizador $\alpha=0.35$ suprime el ruido de alta frecuencia en las coordenadas de los landmarks causado por el grano del sensor en baja luz.
  3. **Congelamiento Seguro:** Si la mano se pierde por más de 0.5 s, el robot congela suavemente la última posición segura sin mandar datos basura al ESP32.

---

### Caso 7: Cierres Inesperados de la GUI por Excepciones no Atrapadas
* **Condición de ocurrencia:** Errores imprevistos en hilos secundarios, desconexión de periféricos o fallos de indexación en OpenCV.
* **Comportamiento previo (falla original):** Terminación abrupta del proceso Python con pérdida de datos y desconexión intempestiva del hardware.
* **Estrategia implementada:**
  1. Instalación de hook global `sys.excepthook` mediante [code/gui-control/error_logger.py](file:///Users/bernardoorozco/Documents/GitHub/IOT-SOFIA-2026/code/gui-control/error_logger.py).
  2. Registro automático del volcado de pila (*traceback*) en [docs/experimental-data/registro_eventos.csv](file:///Users/bernardoorozco/Documents/GitHub/IOT-SOFIA-2026/docs/experimental-data/registro_eventos.csv).
  3. Emisión de advertencia limpia en la terminal de la GUI, **garantizando que la aplicación continúe operando de manera ininterrumpida**.

---

## 6. Resultados Cuantitativos de las Pruebas de Estrés y Métricas

La validación del sistema fue ejecutada mediante la suite automatizada [code/communication/test_protocolo_estres.py](file:///Users/bernardoorozco/Documents/GitHub/IOT-SOFIA-2026/code/communication/test_protocolo_estres.py). Los resultados cuantitativos exportados a [docs/experimental-data/registro_pruebas_ciclo.csv](file:///Users/bernardoorozco/Documents/GitHub/IOT-SOFIA-2026/docs/experimental-data/registro_pruebas_ciclo.csv) se resumen a continuación:

### Matriz Consolidada de Pruebas:
| Batería de Prueba | Condiciones de Evaluación | Métrica Evaluada | Criterio de Aceptación | Resultado Obtenido |
|:---|:---|:---|:---|:---:|
| **1. Ciclo Detección/Acción (7 Posturas)** | Secuencia completa de SALUDO, CORAZÓN, TIJERA, ROCA, SWIPE, PAPEL, PPT. | Latencia de decisión y respuesta del robot. | Trama formal generada, recepción de ACK y ejecución motriz íntegra. | **100% ÉXITO**<br>*(Latencia $< 1.5$ ms)* |
| **2. Estrés: Cambios Rápidos** | 60 transiciones aceleradas de postura a 20 Hz con movimiento continuo. | Disparos accidentales (*false positives*). | 0 disparos durante la fase de ruido o transición. | **100% ÉXITO**<br>*(0 falsos disparos)* |
| **3. Estrés: Múltiples Usuarios** | 2 usuarios en cuadro; salto espacial de $80^\circ$ en muñeca seguido de reposo. | Rechazo de salto y aceptación tras estabilizar. | Descarte del comando durante el salto; activación limpia al estabilizar. | **100% ÉXITO**<br>*(Sin oscilaciones)* |
| **4. Estrés: Iluminación Variable** | 50% dropouts intercalados por baja luz/contraluz seguido de iluminación normal. | Continuidad y estabilidad de reconocimiento. | Supresión de falsos reinicios y disparo limpio al normalizar luz. | **100% ÉXITO**<br>*(Tolerante a flickering)* |
| **5. Tolerancia a Fallos de Protocolo** | Inyección deliberada de ángulos fuera de rango ($50^\circ, 130^\circ$) y comandos inválidos. | Respuesta del ESP32 ante anomalías sintácticas. | Emisión de `NACK` tipificado (`ERR_01`, `ERR_02`, `ERR_03`) y protección motriz. | **100% ÉXITO**<br>*(Hardware protegido)* |
| **6. Tolerancia a Pérdida de Enlace** | Desconexión abrupta de la radio BLE y apagado del ESP32. | Comportamiento del robot y de la GUI. | Servos a HOME seguro ($90^\circ, 90^\circ$), reconexión automática en GUI. | **100% ÉXITO**<br>*(Recuperación limpia)* |

---

## 7. Evidencia Multimedia y Enlaces de Video

Para verificar el funcionamiento físico del robot sOFla coordinado con la interfaz gráfica y los mecanismos de tolerancia a fallos, se preparó un registro audiovisual demostrativo centralizado en el almacenamiento en la nube institucional (OneDrive ITESO).

> **Repositorio Oficial de Evidencias en la Nube (OneDrive ITESO):**  
> Carpeta Compartida: [EVIDENCIA_PRUEBAS_Y_MANEJO_DE_ERRORES](https://iteso01-my.sharepoint.com/:f:/r/personal/bernardo_orozco_iteso_mx/_layouts/15/onedrive.aspx?id=%2Fpersonal%2Fbernardo%5Forozco%5Fiteso%5Fmx%2FDocuments%2FEVIDENCIA%5FPRUEBAS%5FY%5FMANEJO%5FDE%5FERRORES&share=cgpQ%5Fc3q%2DIRlTp4mHJuUddyvEgUCUTLs0cgR5tQS59cMol0fDQ)  
> **Archivo a consultar en la carpeta:** `EVIDENCIA_10_VIDEO_DEMOSTRACION_COMPLETO` *(formato .mp4)*

### Índice de Archivos Multimedia en el Repositorio:
Los archivos multimedia (videos y fotografías de evidencia) se encuentran alojados en la carpeta del repositorio institucional con la siguiente nomenclatura estandarizada:

| Código de Archivo | Nombre en Carpeta OneDrive | Formato | Contenido de la Evidencia |
|:---:|:---|:---:|:---|
| Evidencia 1 | `EVIDENCIA_01_SALUDO` | `.mp4` / `.jpg` | Detección de mano saludando y respuesta en cabeceo vertical del robot. |
| Evidencia 2 | `EVIDENCIA_02_CORAZON` | `.mp4` / `.jpg` | Gesto de corazón bimanual y órbita circular continua de sOFla. |
| Evidencia 3 | `EVIDENCIA_03_TIJERA_BAILE` | `.mp4` / `.jpg` | Postura de tijera sostenida y ejecución de coreografía de baile en zigzag. |
| Evidencia 4 | `EVIDENCIA_04_ROCA_HOME` | `.mp4` / `.jpg` | Puño cerrado y centrado de servomotores al origen neutro $(90^\circ, 90^\circ)$. |
| Evidencia 5 | `EVIDENCIA_05_SWIPE_NEGAR` | `.mp4` / `.jpg` | Desplazamiento dinámico de la mano y oscilación horizontal de negación ("no"). |
| Evidencia 6 | `EVIDENCIA_06_PAPEL_REPOSO` | `.mp4` / `.jpg` | Mano abierta estática y descenso a postura de reposo seguro ($90^\circ, 60^\circ$). |
| Evidencia 7 | `EVIDENCIA_07_PPT_RITMICO` | `.mp4` / `.jpg` | Tres golpes de puño sobre palma y respuesta rítmica sincrónica de sOFla. |
| Evidencia 8 | `EVIDENCIA_08_RECUPERACION_CAMARA` | `.mp4` / `.jpg` | Desconexión física de la webcam con aviso en pantalla y reconexión automática. |
| Evidencia 9 | `EVIDENCIA_09_RECONEXION_BLE_ESP32` | `.mp4` / `.jpg` | Apagado del ESP32 con aseguramiento en HOME y reconexión desatendida. |
| Evidencia 10 | `EVIDENCIA_10_VIDEO_DEMOSTRACION_COMPLETO` | `.mp4` | Video integral demostrativo con el ciclo completo y pruebas de estrés en vivo. |

---

## 8. Conclusiones y Cumplimiento de Rúbrica

1. **Integración Completa y Determinista:** Se superó la meta inicial de 5 posturas alcanzando un repertorio de **7 posturas operativas**, cada una vinculada a una rutina coreográfica en firmware y gobernada por un protocolo serial bidireccional delimitado `$SEQ,CMD,PARAMS#`.
2. **Alta Resiliencia Operativa:** El sistema cuenta con mecanismos de desacoplamiento que impiden el bloqueo o cierre de la aplicación ante caídas de enlace BLE o fallos de la cámara web, asegurando mecánicamente al robot en una posición neutra de protección.
3. **Validación Cuantitativa Concluyente:** La suite de pruebas automatizadas y el registro formal en archivos CSV certifican que la latencia de procesamiento lógico se mantiene por debajo de $1.5\text{ ms}$, con un tiempo de respuesta de enlace inalámbrico típico de $20\text{ a }35\text{ ms}$, apto para interacción humano-robot en tiempo real.
