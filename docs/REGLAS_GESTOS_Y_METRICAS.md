# REPORTE TÉCNICO: RECONOCIMIENTO DE 5 POSTURAS, SUAVIZADO Y BENCHMARKING
**Proyecto SOFÍA (Smart Organic Framework for Interactive Assistance) - 2026**  
**Autores:** Paola M. Covarrubias V., Lizeth A. Méndez O., J. Bernardo Orozco Q., Karen I. Sánchez G., Alan E. Fuentes G.

---

## 1. Definición de Reglas Geométricas de las 5 Posturas

El sistema procesa coordenadas normalizadas tridimensionales $(x_i, y_i, z_i) \in [0, 1]$ generadas por MediaPipe Pose y Hand Landmarker a $30\text{ fps}$. Se seleccionaron **5 posturas prioritarias**, de las cuales **3 son dinámicas** (evaluadas temporalmente a través de ventanas de cuadros consecutivos) y **2 son estáticas**.

```
                ┌──────────────────────────────────────────┐
                │          ENTRADA: MediaPipe 3D           │
                └────────────────────┬─────────────────────┘
                                     ▼
                ┌──────────────────────────────────────────┐
                │     Filtro EMA (α = 0.35) Landmark       │
                └────────────────────┬─────────────────────┘
                                     ▼
                     ┌───────────────┴───────────────┐
                     ▼                               ▼
       ┌───────────────────────────┐   ┌───────────────────────────┐
       │   POSTURAS DINÁMICAS (3)  │   │   POSTURAS ESTÁTICAS (2)  │
       ├───────────────────────────┤   ├───────────────────────────┤
       │ 1. Saludo / Wave (Δx, N)  │   │ 4. Corazón (D(4,4), D(8,8))│
       │ 2. Intención PPT (3 Golpes│   │ 5. Tijera / Paz (θ, D)    │
       │ 3. Swipe Lateral (v_x, Δt)│   └───────────────────────────┘
       └───────────────────────────┘
```

---

### Postura 1 (Dinámica): Saludo Lateral (`WaveGesture`)
* **Propósito:** Inicio de interacción / Saludo amigable con SOFÍA.
* **Variables Geométricas:**
  * Landmark de muñeca: $W = (x_0, y_0, z_0)$.
  * Landmark de nariz (Pose): $N = (x_{nose}, y_{nose}, z_{nose})$ o condición de mano elevada ($y_0 < y_{hombro}$).
* **Regla Temporal:**
  Se analiza una cola temporal $H = \{x_0(t - k), \dots, x_0(t)\}$ de los últimos $0.8\text{ s}$.
  1. La mano debe encontrarse elevada: $y_0(t) < y_{codo}(t)$ o $y_0(t) < 0.65$.
  2. Número de oscilaciones laterales: se detectan inversiones en el signo de la derivada discreta:
     $$\text{sign}(\Delta x(t)) \neq \text{sign}(\Delta x(t-1))$$
  3. Desplazamiento mínimo por semiciclo: $|\Delta x| \ge 0.05$.
  4. Condición de activación: $\text{Cruces por cero} \ge 3$ en menos de $0.85\text{ s}$.

---

### Postura 2 (Dinámica): Intención Piedra-Papel-Tijera (`RpsIntentGesture`)
* **Propósito:** Activar la máquina de estados de juego interactivo con SOFÍA.
* **Variables Geométricas:**
  * Mano 1 (Puño dominante): Distancia entre puntas de dedos (8, 12, 16, 20) y la muñeca (0):
    $$d_{\text{puntas-muñeca}} = \frac{1}{4} \sum_{i \in \{8,12,16,20\}} \|P_i - P_0\| < \tau_{\text{puño}} = 0.22$$
  * Mano 2 (Palma base): Dedos extendidos y orientación horizontal:
    $$\|P_i - P_0\| > 0.30 \quad \forall i \in \{8, 12, 16, 20\}$$
* **Regla Temporal (Golpeteo rítmico):**
  * Se registra la distancia vertical $d_y(t) = |y_{\text{puño}}(t) - y_{\text{palma}}(t)|$.
  * Contacto o impacto detectado si $d_y(t) \le 0.12$.
  * Se requieren 3 ciclos descendentes/impactos ("Piedra...", "Papel...", "Tijera..."):
    $$N_{\text{golpes}} = 3 \quad \text{con } \Delta t_{\text{entre golpes}} \in [0.25\text{ s}, 0.90\text{ s}]$$

---

### Postura 3 (Dinámica): Deslizamiento Lateral (`SwipeGesture`)
* **Propósito:** Navegación en interfaz / cambio de menú o diapositiva.
* **Variables Geométricas:**
  * Posición de muñeca: $x(t)$.
  * Vector velocidad horizontal:
    $$v_x(t) = \frac{x(t) - x(t - \Delta t)}{\Delta t}$$
* **Regla Temporal:**
  * Desplazamiento total acumulado: $\Delta X = |x(t) - x_{\text{inicio}}| \ge 0.22$ (22% del ancho del cuadro).
  * Límite de tiempo: $\Delta t \le 0.45\text{ s}$.
  * Dirección:
    $$\begin{cases} \text{SWIPE DERECHA}, & \text{si } x(t) - x_{\text{inicio}} > 0.22 \\ \text{SWIPE IZQUIERDA}, & \text{si } x_{\text{inicio}} - x(t) > 0.22 \end{cases}$$
  * Cooldown de 0.6 s post-activación para evitar falsos positivos repetitivos.

---

### Postura 4 (Estática): Corazón con Dos Manos (`HeartGesture`)
* **Propósito:** Empatía / Feedback afectivo positivo.
* **Variables Geométricas (2 Manos simultáneas):**
  * Pulgares de mano izquierda ($L_4$) y mano derecha ($R_4$):
    $$d_{\text{pulgares}} = \|L_4 - R_4\| \le 0.08$$
  * Índices de mano izquierda ($L_8$) y mano derecha ($R_8$):
    $$d_{\text{índices}} = \|L_8 - R_8\| \le 0.08$$
  * Curvatura de corazón: Muñecas separadas $d_{\text{muñecas}} = \|L_0 - R_0\| \ge 0.15$ con los índices ubicados en la parte superior respecto a las muñecas ($y_8 < y_0$).

---

### Postura 5 (Estática): Tijera / Victoria (`ScissorsGesture`)
* **Propósito:** Selección de jugada en Piedra-Papel-Tijera y comando de confirmación "V".
* **Variables Geométricas (1 Mano):**
  * Dedos extendidos: Índice (8) y Medio (12):
    $$\|P_8 - P_0\| > 1.3 \times \|P_6 - P_0\|, \quad \|P_{12} - P_0\| > 1.3 \times \|P_{10} - P_0\|$$
  * Dedos retraídos: Anular (16) y Meñique (20):
    $$\|P_{16} - P_0\| < \|P_{14} - P_0\|, \quad \|P_{20} - P_0\| < \|P_{18} - P_0\|$$
  * Ángulo de apertura entre índice y medio:
    $$\theta = \arccos\left(\frac{(P_8 - P_6) \cdot (P_{12} - P_{10})}{\|P_8 - P_6\| \|P_{12} - P_{10}\|}\right) \in [15^\circ, 65^\circ]$$

---

## 2. Técnica de Suavizado Implementada (Smoothing)

Para mitigar el temblor de detección (*jitter*) derivado de variaciones de iluminación y ruido del sensor CMOS sin inducir latencia excesiva, se implementó un **Filtro de Media Móvil Exponencial (EMA - Exponential Moving Average)** de primer orden:

$$\hat{P}_k = \alpha P_k + (1 - \alpha) \hat{P}_{k-1}$$

Donde:
* $P_k$: Vector de coordenadas tridimensionales en el cuadro actual $(\tilde{x}, \tilde{y}, \tilde{z})$.
* $\hat{P}_{k-1}$: Posición suavizada del cuadro anterior.
* $\alpha \in (0, 1]$: Factor de suavizado configurado en **$\alpha = 0.35$**.

### Comparativa:
* **Con $\alpha = 0.35$:** Atenúa el ruido de alta frecuencia en un 65%, eliminando oscilaciones espurias entre cuadros consecutivos mientras mantiene la respuesta de seguimiento dinámico en menos de $33\text{ ms}$ (1 cuadro).
* El usuario puede alternar el filtro en tiempo real presionando la tecla **`S`** para comprobar la diferencia visual de estabilidad de los esqueletos.

---

## 3. Métricas de Rendimiento y Evaluación Experimental

### 3.1. Métricas en Tiempo Real (HUD Overlay)
El script `main.py` incorpora una tarjeta de telemetría en tiempo real:
1. **FPS Instantáneo y Suavizado:** Calculado mediante medición precisa con `time.perf_counter()`.
2. **Latencia / Tiempo de Respuesta ($T_{\text{lat}}$):** Intervalo desde la adquisición del cuadro hasta la resolución de la máquina de estados de gestos.
3. **Estado del Filtro:** Indicador activo `EMA (alpha=0.35)` vs `OFF`.
4. **Exportador CSV:** Al presionar **`L`**, el sistema genera registros en `benchmark_logs/metrics_<timestamp>.csv`.

### 3.2. Matriz de Pruebas Experimentales

| Escenario | Condición de Iluminación | Distancia Usuario-Cámara | FPS Promedio | Latencia Promedio (ms) | Tasa de Acierto (%) |
| :--- | :--- | :--- | :---: | :---: | :---: |
| **Escenario A** | Luz Óptima Interior (500 lux) | 1.2 m - 1.5 m | 29.8 | 31.4 ms | 96.5% |
| **Escenario B** | Luz Tenue / Sombras (80 lux) | 1.2 m - 1.5 m | 28.5 | 34.2 ms | 88.0% |
| **Escenario C** | Contraluz Pronunciado | 1.5 m | 27.2 | 36.8 ms | 82.5% |
| **Escenario D** | Usuario Infantil / Manos Pequeñas | 1.0 m | 29.5 | 31.8 ms | 91.0% |
| **Escenario E** | Movimiento Rápido Dinámico | 1.2 m | 29.0 | 33.1 ms | 89.5% |

### 3.3. Matriz de Confusión Experimental (N = 50 repeticiones por postura)

| Postura Real \ Detectada | Saludo (Wave) | Intención PPT | Swipe | Corazón | Tijera | Ninguno / Error | Precisión |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Saludo (Wave)** | **48** | 0 | 1 | 0 | 0 | 1 | **96.0%** |
| **Intención PPT** | 0 | **47** | 1 | 0 | 1 | 1 | **94.0%** |
| **Swipe** | 1 | 0 | **46** | 0 | 0 | 3 | **92.0%** |
| **Corazón** | 0 | 0 | 0 | **49** | 0 | 1 | **98.0%** |
| **Tijera** | 0 | 1 | 0 | 0 | **48** | 1 | **96.0%** |

---

## 4. Instrucciones de Ejecución

Para iniciar el sistema de visión con la nueva arquitectura y telemetría:

```bash
cd code/tracking-vision
./venv/bin/python main.py
```

* Presiona **`S`** para encender o apagar el filtro suavizador.
* Presiona **`L`** para iniciar o detener la grabación de datos de benchmark a CSV.
* Presiona **`Q`** para salir limpiamente.
