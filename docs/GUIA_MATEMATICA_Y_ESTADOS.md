# 📘 Guía Intuitiva: Ecuaciones, Variables y Funcionamiento de la State Machine
**Proyecto SOFÍA 2026 - Control Cinemático y Gestos**

Esta guía explica en lenguaje claro, con analogías y paso a paso, qué significa cada ecuación, símbolo y variable del sistema de control y de la máquina de estados de SOFÍA. Está pensada para que entiendas al 100% el sustento teórico y puedas responder con seguridad en cualquier sustentación.

---

## 📑 Tabla de Contenidos
1. [Diccionario Completo de Variables y Símbolos](#1-diccionario-completo-de-variables-y-símbolos)
2. [Las 4 Ecuaciones Principales Explicadas con Manzanitas](#2-las-4-ecuaciones-principales-explicadas-con-manzanitas)
   - [2.1 El Límite de Paso ($D_{MAX}$)](#21-el-límite-de-paso-d_max)
   - [2.2 El Rate Limiter Articular ($y_1, y_2$)](#22-el-rate-limiter-articular-y_1-y_2)
   - [2.3 La Función de Saturación ($\text{sat}$)](#23-la-función-de-saturación-textsat)
   - [2.4 Error de Comando ($e_y$) vs Error Real Sensorico ($e_p$)](#24-error-de-comando-e_y-vs-error-real-sensorico-e_p)
3. [El Porqué de los Tiempos ($T_{ESPERA}$ y $T_{SOSTENER}$)](#3-el-porqué-de-los-tiempos-t_espera-y-t_sostener)
4. [¿Qué hace cada una de las 3 Articulaciones ($q_1, q_2, q_3$)?](#4-qué-hace-cada-una-de-las-3-articulaciones-q_1-q_2-q_3)
5. [Guía Rápida para Preguntas del Profesor](#5-guía-rápida-para-preguntas-del-profesor)

---

## 1. Diccionario Completo de Variables y Símbolos

### A. Variables de Posición Angular
| Símbolo | Nombre Técnico | ¿Qué representa en español sencillo? | Ejemplo de Valor |
| :---: | :--- | :--- | :---: |
| **$r_1, r_2$** | **Referencia** *(Reference)* | **La META:** El ángulo objetivo al que queremos llegar en este paso del gesto. | $r_1 = 0.45\text{ rad} \ (116^\circ)$ |
| **$y_1, y_2$** | **Comando de salida** | **LA ORDEN ACTUAL:** El ángulo que la computadora le está ordenando al motor en este milisegundo exacto (avanza poco a poco hacia $r$). | $y_1 = 0.12\text{ rad}$ |
| **$p_1, p_2$** | **Posición real** *(Position)* | **DÓNDE ESTÁ EL MOTOR FÍSICO:** La lectura que entregan los sensores reales (encoders o potenciómetros). | $p_1 = 0.11\text{ rad}$ |
| **$s_1, s_2$** | Sensores físicos | Los dispositivos de hardware que miden el giro de los motores (`joint_1_sensor`). | Objeto de Webots / ADC |
| **$q_1$** | Articulación 1 (Yaw) | Motor de **giro horizontal** del cuello (izquierda $\leftrightarrow$ derecha). | Rango $[60^\circ, 120^\circ]$ |
| **$q_2$** | Articulación 2 (Pitch) | Motor de **cabeceo vertical** (arriba $\leftrightarrow$ abajo). | Rango $[60^\circ, 120^\circ]$ |
| **$q_3$** | Articulación 3 (Mirror) | **Espejo mecánico:** Motor gemelo que copia exactamente a $q_2$ para mover el cuello con balance estructural. | Idéntico a $q_2$ |

---

### B. Variables de Tiempo y Velocidad
| Símbolo | Nombre Técnico | ¿Qué representa en español sencillo? | Valor en SOFÍA |
| :---: | :--- | :--- | :---: |
| **$\Delta t$ / `dt`** | Paso temporal *(Delta Time)* | Cuánto tiempo transcurre entre una actualización y la siguiente ($\approx 31$ veces por segundo). | $0.032\text{ s} \ (32\text{ ms})$ |
| **$W_{MAX}$** | Velocidad máxima de hardware | La velocidad límite física que el motor de Webots puede dar sin quemarse. | $10.47\text{ rad/s} \ (\approx 600^\circ/\text{s})$ |
| **$V_{MAX}$** | Velocidad máxima de comando | La velocidad segura que nosotros elegimos para que el robot se mueva elegante y sin violencia. | $1.5\text{ rad/s} \ (\approx 86^\circ/\text{s})$ |
| **$D_{MAX}$** | Variación máxima de paso | **El tamaño máximo de cada paso:** Lo máximo que le permitimos al motor avanzar en un solo cuadro de tiempo ($\Delta t$). | $1.5 \times 0.032 = 0.048\text{ rad}$ |
| **$TOL$** | Tolerancia de llegada | La "zona de llegada": si el sensor está a menos de esta distancia de la meta, consideramos que ya llegó. | $0.01\text{ rad} \ (\approx 0.57^\circ)$ |
| **$T_{ESPERA}$** | Tiempo de reposo | Pausa de descanso en neutro antes de arrancar un nuevo gesto. | $2.0\text{ segundos}$ |
| **$T_{SOSTENER}$** | Tiempo de sostenimiento | Tiempo que el robot congela la pose final de un gesto para que la gente lo aprecie. | $1.0\text{ segundo}$ |
| **$t$** | Tiempo actual del sistema | El reloj global que corre desde que se encendió el robot. | Segundos |
| **$t_{entrada}$** | Tiempo de entrada al estado | La hora exacta en la que el robot entró al estado actual. | Segundos |
| **$t_{estado}$** | Duración en el estado | Cuánto tiempo lleva en el estado actual ($t_{estado} = t - t_{entrada}$). | Segundos |

---

### C. Errores y Operadores Matemáticos
| Símbolo | Nombre Técnico | ¿Qué representa en español sencillo? |
| :---: | :--- | :--- |
| **$e_y$** | Error de comando numérico | ¿Cuánto le falta a la orden matemática ($y$) para llegar a la meta ($r$)? |
| **$e_p$** | Error físico mecánico | ¿Cuánto le falta al motor real ($p$) para llegar a la meta ($r$)? |
| **$\text{sat}(u, D_{MAX})$** | Función de saturación | Un limitador que frena cualquier valor que quiera exceder $\pm D_{MAX}$. |
| **$(k)$ y $(k-1)$** | Índices de tiempo discreto | $(k)$ es el **presente** (este ciclo) y $(k-1)$ es el **pasado** (el ciclo anterior). |
| **$\max(\|a\|, \|b\|)$** | Norma infinito / Máximo | Toma el error del eje que vaya más atrasado (el cuello solo avanza cuando ambos ejes cumplen). |

---

## 2. Las 4 Ecuaciones Principales Explicadas con Manzanitas

### 2.1 El Límite de Paso ($D_{MAX}$)
$$D_{MAX} = V_{MAX} \cdot \Delta t$$

* **La idea intuitiva:**
  * Si tu carro viaja a $V_{MAX} = 60\text{ km/h}$ y miras el velocímetro cada $\Delta t = 1\text{ segundo}$, en ese segundo recorriste un pedacito fijo de carretera.
  * En SOFÍA, si la velocidad máxima de comando es $1.5\text{ rad/s}$ y el bucle de control corre cada $0.032\text{ segundos}$, **lo máximo que el motor tiene permiso de avanzar en ese instante es $0.048\text{ radianes}$ (unos $2.7^\circ$)**.
* **¿Por qué se hace esto?**
  * Si no existiera $D_{MAX}$, al pedirle un cambio de $60^\circ$ a $120^\circ$, el motor intentaría dar el salto en $0$ milisegundos. Eso causaría un **latigazo mecánico violento**, ruido, vibraciones y picos excesivos de corriente en la fuente de alimentación.

---

### 2.2 El Rate Limiter Articular ($y_1, y_2$)
$$y_1(k) = y_1(k-1) + \text{sat}\Big(r_1 - y_1(k-1), \ D_{MAX}\Big)$$

* **Paso a paso con números reales:**
  1. Imagina que tu robot está mirando al centro: **$y_1(k-1) = 90^\circ$**.
  2. Llega un gesto que le pide mirar a la derecha: meta **$r_1 = 120^\circ$**.
  3. Calculamos la distancia que falta: $r_1 - y_1(k-1) = 120^\circ - 90^\circ = 30^\circ$.
  4. La función de saturación dice: *"Me pides $30^\circ$, pero tu paso máximo permitido es de solo $2.7^\circ$ ($D_{MAX}$)"*.
  5. Calculamos la nueva orden: $y_1(k) = 90^\circ + 2.7^\circ = 92.7^\circ$.
  6. En el siguiente ciclo ($32\text{ ms}$ después): $y_1(k) = 92.7^\circ + 2.7^\circ = 95.4^\circ$.
  7. Y así sucesivamente, **creando una rampa de aceleración completamente suave y orgánica**.

---

### 2.3 La Función de Saturación ($\text{sat}$)
$$\text{sat}(u, \ D_{MAX}) = \begin{cases} 
+D_{MAX} & \text{si } u > D_{MAX} \\ 
u & \text{si } -D_{MAX} \le u \le D_{MAX} \\ 
-D_{MAX} & \text{si } u < -D_{MAX} 
\end{cases}$$

* **La idea intuitiva:**
  * Es el **control de crucero o el gobernador**:
    * Si quieres avanzar más rápido que el límite $\to$ Te clava en $+D_{MAX}$.
    * Si quieres retroceder más rápido que el límite $\to$ Te clava en $-D_{MAX}$.
    * Si estás muy cerca de la meta (por ejemplo, a solo $0.5^\circ$, que es menor que $D_{MAX}$) $\to$ Te deja avanzar exactamente esos $0.5^\circ$ para llegar a la meta exacta sin pasarte de largo (*sin overshoot*).

---

### 2.4 Error de Comando ($e_y$) vs Error Real Sensorico ($e_p$)
Aquí está la diferencia técnica más importante entre la simulación y la robótica del mundo real:

```
[Computadora / Algoritmo]                           [Mundo Físico / Motores]
         │                                                      │
         ▼                                                      ▼
  Genera la orden "y"                                    El servo real "p"
(Avanza pasito a pasito)                              (Tiene inercia y peso)
         │                                                      │
         ▼                                                      ▼
   ¿y llegó a r?                                          ¿p llegó a r?
     (ey < 1e-6)                                            (ep < TOL)
         │                                                      │
         ▼                                                      ▼
Estado: MOVER -> ASENTAR                              Estado: ASENTAR -> SIGUIENTE POSE
```

#### A. Error de Comando ($e_y$)
$$e_y = \max\Big(|r_1 - y_1|, \ |r_2 - y_2|\Big) < 10^{-6}$$
* Evalúa si la rampa matemática de la computadora ya terminó de dar todos los pasos.
* Cuando $e_y < 10^{-6}$, significa que numéricamente $y_1 = r_1$ y $y_2 = r_2$.
* **Disparador:** La máquina de estados abandona **`MOVER`** y entra a **`ASENTAR`**.

#### B. Error Físico Real ($e_p$)
$$e_p = \max\Big(|r_1 - p_1|, \ |r_2 - p_2|\Big) < TOL$$
* Aunque la computadora ya terminó de ordenar la meta, **el motor físico real tarda unas milésimas de segundo más en empujar la cabeza del robot debido al peso del cuello y la gravedad**.
* Los sensores miden la posición real ($p_1, p_2$).
* Mientras la cabeza siga viajando, $e_p \ge TOL$ y el robot permanece esperando en **`ASENTAR`**.
* En cuanto $e_p < TOL$, confirmamos que mecánicamente ya llegó y se avanza a la siguiente pose del gesto o a sostenerlo.

---

## 3. El Porqué de los Tiempos ($T_{ESPERA}$ y $T_{SOSTENER}$)

> [!NOTE]
> En robótica social, el lenguaje corporal debe ser comprensible para los seres humanos.

1. **$T_{SOSTENER} = 1.0\text{ s}$:**
   * Si SOFÍA hace el gesto de **Corazón** o dice **"Sí"**, no puede regresar al centro de inmediato. Un humano tarda entre $400$ y $800\text{ ms}$ en procesar visualmente el gesto. Al sostener la pose 1 segundo completo, el usuario comprende claramente la interacción.
2. **$T_{ESPERA} = 2.0\text{ s}$:**
   * Es una pausa de neutralidad. Si un robot ejecuta gestos seguidos sin parar un solo instante, parece una máquina descalibrada o nerviosa. Los 2 segundos en neutro dan la sensación de que el robot está "atento" y esperando la siguiente acción del usuario.

---

## 4. ¿Qué hace cada una de las 3 Articulaciones ($q_1, q_2, q_3$)?

En el modelo de simulación de SOFÍA (`sofia.proto`) existen 3 servomotores:

```text
               [ CABEZA DE SOFÍA ]
                       │
       ┌───────────────┴───────────────┐
       │                               │
  Motor q2 (Pitch)               Motor q3 (Mirror)
  Lado Izquierdo                 Lado Derecho
  (Sube y baja)                  (Sube y baja sincronizado)
       │                               │
       └───────────────┬───────────────┘
                       │
                 Motor q1 (Yaw)
                 (Gira izquierda / derecha)
                       │
                   [ BASE ]
```

* **$q_1$ (Eje Yaw):** Motor en la base del cuello. Permite que SOFÍA gire la cabeza para mirar a la izquierda o derecha (como cuando decimos "NO" o seguimos una mano que se mueve horizontalmente).
* **$q_2$ (Eje Pitch Principal):** Motor en el lateral del cuello. Permite subir y bajar la cabeza (como cuando decimos "SÍ" o asentimos).
* **$q_3$ (Eje Pitch Espejo):** `q3.setPosition(y2)`. Mecánicamente, la cabeza de SOFÍA se sostiene de ambos lados para no doblar los soportes de impresión 3D. El motor $q_3$ hace exactamente el mismo movimiento que $q_2$ para repartir el peso y evitar torsiones en la estructura.

---

## 5. Guía Rápida para Preguntas del Profesor

Si el profesor te pregunta en la sustentación:

1. **"¿Por qué usan una función de saturación en lugar de enviar el ángulo directo?"**
   > *"Porque implementamos un Rate Limiter donde $D_{MAX} = V_{MAX} \cdot \Delta t$. La saturación acota la derivada temporal del comando para que los servomotores aceleren suavemente sin picos de corriente ni choques mecánicos."*

2. **"¿Por qué tienen dos estados separados, MOVER y ASENTAR?"**
   > *"Porque $MOVER$ controla la generación de la trayectoria numérica hasta que el error de comando $e_y < 10^{-6}$. Una vez completada la consigna, $ASENTAR$ comprueba mediante los sensores físicos de retroalimentación que el servomotor real haya vencido la inercia y alcanzado la pose dentro de la tolerancia $e_p < TOL$."*

3. **"¿Cómo se asegura el sistema de que las articulaciones no superen los límites mecánicos?"**
   > *"Todos los comandos pasan primero por el estado $VALIDADO$, donde verificamos que se encuentren estrictamente dentro del rango de seguridad $[60^\circ, 120^\circ]$ (o $[-\pi/6, +\pi/6]\text{ rad}$). Cualquier valor fuera de ese margen se transiciona a $DESCARTADO$ antes de interactuar con el hardware."*
