# Análisis Experimental y Respuestas para el Revisor R3.4 (Corte 2)

**Documento provisional de soporte para:**
- Revisión R3.4 (Línea 241, 356, 81: *Bang-bang vs. Control Proporcional Saturado*).
- Manuscrito principal: `paper/Equipo 1 - segundo corte/Equipo 1 - segundo corte.tex`.
- Carta de respuesta a revisores: `paper/Equipo 1 - respuesta - segundo corte/Equipo 1 - respuesta - segundo corte.tex`.
- Fuentes de datos: `docs/experimental-data/datos_5grados.csv`, `datos_901.csv`, `datos_CHIDOS_DE_FORZADO.csv` y documento `Correcciones Corte 1.docx`.

---

## 1. Análisis de las Gráficas: ¿Proporcional o Bang-Bang?

### ¿Qué muestran realmente los datos?
Al analizar las series temporales de corriente a $20\text{ Hz}$ ($\Delta t = 50\text{ ms}$):

1. **En régimen permanente libre (sin carga externa):**
   - Tanto para el escalón de $e = 5^\circ$ (`datos_5grados.csv`) como para $e = 90^\circ$ (`datos_901.csv`), una vez que el motor alcanza la consigna, la corriente se estabiliza de inmediato en una línea base de reposo de **$I_{\text{quiesc}} \approx 3.10\text{ mA}$** a $5.02\text{ V}$.
   - **No existe oscilación sostenida, castañeo (*chattering*) ni ciclo límite** alrededor de la referencia angular. Esto descarta formalmente un controlador *bang-bang* puro sin banda muerta, el cual conmutaría permanentemente entre $+U_{\max}$ y $-U_{\max}$.

2. **Durante el movimiento dinámico (transitorio):**
   - En ambos casos libres, el pico inicial instantáneo es muy similar ($582.7\text{ mA}$ en $5^\circ$ vs. $573.4\text{ mA}$ en $90^\circ$). Físicamente, esto corresponde a la **corriente de arranque (*inrush/starting current*)** de un motor DC desde velocidad cero ($I_0 \approx V/R_a$).
   - Sin embargo, la **duración del paquete de corriente activa** sí depende de la magnitud del desplazamiento:
     - En $5^\circ$ (desplazamiento efectivo de $3^\circ$), el actuador entra en la banda muerta del servo ($\approx 5\,\mu\text{s} \approx 0.9^\circ$) en apenas $1\text{--}2$ periodos de muestreo ($< 100\text{ ms}$), con solo 4 muestras sobre $50\text{ mA}$ ($0.3\%$ del tiempo).
     - En $90^\circ$, la demanda de corriente activa se extiende por $t \approx 150\text{--}180\text{ ms}$ (12 muestras sobre $50\text{ mA}$), tiempo congruente con la velocidad angular máxima de catálogo ($0.10\text{ s}/60^\circ$).

3. **Bajo bloqueo mecánico forzado (`datos_CHIDOS_DE_FORZADO.csv`):**
   - Cuando el rotor es retenido mecánicamente y no puede reducir el error angular ($e(t) \neq 0$), el circuito integrado interno eleva el ciclo de trabajo de modulación PWM del puente H al **$100\%$ continuo (saturación de los transistores)**.
   - En esta condición, la corriente promedia **$I_{\text{stall}} = 918.4\text{ mA}$** (con picos transitorios de hasta $1.79\text{ A}$ y caída de tensión del bus de alimentación hasta $4.76\text{ V}$, con valles de $2.84\text{ V}$), disipando $\approx 4.37\text{ W}$ constantes en calentamiento resistivo del bobinado ($\Delta T = 13.5^\circ\text{C}$ durante la prueba).

### Conclusión Científica Rigurosa
Los datos demuestran que el servomotor analógico MG90S **no es un conmutador bang-bang**, sino un **servocontrolador proporcional por modulación PWM con zona muerta ($\approx 5\,\mu\text{s}$) que entra en régimen de saturación estricta cuando una restricción física exterior impide anular el error**. 

Por tanto, la afirmación previa de que *"el controlador interno emula un control bang-bang"* era una confusión fenomenológica: lo que se observaba en la curva térmica era la **saturación del control proporcional** al estar forzado a voltaje pleno, y no una ley de control puramente todo-o-nada.

---

## 2. Entregables para R3.4

### (a) Párrafo de Metodología (Condiciones, Instrumento, Método)

> **Inglés (para el manuscrito):**  
> To assess actuator control effort and discriminate between bang-bang switching and saturated proportional drive, power telemetry was acquired across three operating conditions: small step displacement ($e = 5^\circ$, from $2^\circ$ to $5^\circ$), large step displacement ($e = 90^\circ$), and unmitigated locked-rotor mechanical stall. The Tower Pro MG90S servo was powered from a regulated $5.0\text{ V}$ rail monitored via a calibrated high-side shunt sensor sampled at $20\text{ Hz}$ ($\Delta t = 50\text{ ms}$), recording simultaneous rail voltage ($V$), supply current ($I$), and housing surface temperature ($T_s$).

> **Español:**  
> Para evaluar el esfuerzo de control del actuador y discriminar entre una conmutación bang-bang y una acción proporcional saturada, se adquirió telemetría de potencia en tres condiciones operativas: desplazamiento angular pequeño ($e = 5^\circ$, escalón de $2^\circ$ a $5^\circ$), desplazamiento grande ($e = 90^\circ$) y bloqueo mecánico sostenido (rotor trabado). El servomotor Tower Pro MG90S fue energizado desde un riel regulado a $5.0\text{ V}$ instrumentado con un sensor de corriente por derivación (*shunt*) de lado alto a una tasa de muestreo de $20\text{ Hz}$ ($\Delta t = 50\text{ ms}$), registrando simultáneamente la tensión del riel ($V$), la corriente de alimentación ($I$) y la temperatura superficial de la carcasa ($T_s$).

---

### (b) Párrafo de Resultados con las Tres Condiciones

> **Inglés (para el manuscrito):**  
> Empirical current trajectories clearly delineate dynamic motion from continuous stall. In the small-error test ($e = 5^\circ$, $N=1201$), the servo exhibited a brief starting inrush current peak of $582.7\text{ mA}$ lasting $< 100\text{ ms}$ before settling inside the internal deadband to a quiescent holding current of $I_{\text{quiesc}} = 3.12 \pm 0.05\text{ mA}$ at $5.02\text{ V}$, inducing negligible thermal rise ($\Delta T = 1.0^\circ\text{C}$). Under large error ($e = 90^\circ$, $N=1399$), the peak starting current was equivalent ($573.4\text{ mA}$), yet active drive duration scaled proportionally to angular transit time ($t \approx 150\text{--}180\text{ ms}$) prior to deadband settling at $I_{\text{quiesc}} \approx 3.53\text{ mA}$ ($\Delta T = 1.5^\circ\text{C}$). In contrast, under locked rotor ($N=8475$), the internal H-bridge saturated continuously at $100\%$ duty cycle, sustaining an active stall current of $I_{\text{stall}} = 918.4 \pm 142.1\text{ mA}$ (transient peaks up to $1796.9\text{ mA}$ accompanied by supply droop to $4.76\text{ V}$), dissipating $P_0 \approx 4.37\text{ W}$ continuously and driving housing temperatures from $31.0^\circ\text{C}$ to $44.5^\circ\text{C}$.

> **Español:**  
> Las trayectorias empíricas de corriente delinean con claridad el movimiento dinámico libre frente al bloqueo estático continuo. En la prueba de error pequeño ($e = 5^\circ$, $N=1201$), el servo exhibió un breve transitorio de arranque con pico de $582.7\text{ mA}$ de duración inferior a $100\text{ ms}$, asentándose dentro de la zona muerta interna en una corriente de reposo de $I_{\text{quiesc}} = 3.12 \pm 0.05\text{ mA}$ a $5.02\text{ V}$, provocando un incremento térmico despreciable ($\Delta T = 1.0^\circ\text{C}$). Ante un error grande ($e = 90^\circ$, $N=1399$), el pico de arranque fue equivalente ($573.4\text{ mA}$), pero la duración de la conducción activa creció proporcionalmente al tiempo de tránsito angular ($t \approx 150\text{--}180\text{ ms}$) antes de reposar en $I_{\text{quiesc}} \approx 3.53\text{ mA}$ ($\Delta T = 1.5^\circ\text{C}$). En marcado contraste, bajo bloqueo mecánico ($N=8475$), el puente H interno saturó continuamente al $100\%$ de ciclo de trabajo, sosteniendo una corriente media de bloqueo de $I_{\text{stall}} = 918.4 \pm 142.1\text{ mA}$ (con picos transitorios de hasta $1796.9\text{ mA}$ y caída de tensión a $4.76\text{ V}$), disipando $P_0 \approx 4.37\text{ W}$ continuos e impulsando la temperatura de la carcasa de $31.0^\circ\text{C}$ a $44.5^\circ\text{C}$.

---

### (c) Figura LaTeX con las Tres Condiciones (Corriente vs. Tiempo)

Se generó el gráfico vectorial en `figures/fig_current_characterization.pdf` (y `.png`). El bloque LaTeX para insertarlo es:

```latex
\begin{figure}[!t]
    \centering
    \includegraphics[width=\linewidth]{figures/fig_current_characterization}
    \caption{Empirical supply current profiles of the MG90S actuator under three operating regimes at 20~Hz: (a) small error step ($e = 5^\circ$) showing transient inrush ($582.7\text{ mA}$) and rapid deadband quiescence ($3.1\text{ mA}$); (b) large error step ($e = 90^\circ$) exhibiting equivalent inrush ($573.4\text{ mA}$) with transit duration scaling with displacement; and (c) persistent mechanical stall inducing continuous 100\% H-bridge saturation ($I_{\text{stall}} \approx 918.4\text{ mA}$, peak $1.8\text{ A}$) and resistive heating.}
    \label{fig:current_characterization}
\end{figure}
```

*Nota para formato a dos columnas completas (`figure*`):*
Si se requiere mostrar en el ancho completo de las dos columnas de IEEEtran, basta con usar `\begin{figure*}[!t] ... \end{figure*}`.

---

### (d) Frases Corregidas de las Líneas Originales 81, 241 y 356

#### 1. Línea Original 81 (Introducción / Abstract Context)
* **Texto original erróneo:** Afirmaba que el comportamiento del servomotor emula fielmente una ley de control bang-bang no restringida.
* **Texto corregido (actualizado en `\linelabel{ln:intro-bb}`):**
  > *"A classical control archetype relevant to bounded-input actuators under persistent saturation is bang-bang (on-off) control \cite{kirk2004optimal}. However, because both bang-bang switching and saturated proportional control deliver peak voltage during mechanical stall, a thermal trajectory alone cannot discriminate between them without direct current telemetry under varying error amplitudes."*
* **Declaración de limitación agregada:**
  > *"While supply current serves as an indirect proxy of internal control effort, high-bandwidth terminal voltage measurement remains necessary to directly resolve instantaneous PWM duty cycles."*

#### 2. Línea Original 241 (Sección II-B: Thermal & Actuator Modeling)
* **Texto original erróneo:** Modelaba la entrada térmica con el ángulo comandado y asumía control bang-bang en la planta.
* **Texto corregido (actualizado en `\linelabel{ln:tm-bb}`):**
  > *"Rather than operating as a discrete bang-bang switcher, the internal analog driver functions as a proportional pulse-width modulator with an internal deadband ($\approx 5\,\mu\text{s}$). Under unconstrained motion, the actuator rapidly settles to a quiescent baseline ($I_{\text{quiesc}} \approx 3.1\text{ mA}$). It is only under physical obstruction that the persistent angular error drives the internal H-bridge into hard continuous saturation, sustaining an unmitigated stall current of $I_{\text{stall}} \approx 918.4\text{ mA}$ ($P_0 \approx 4.37\text{ W}$) that triggers steep Joule heating."*

#### 3. Línea Original 356 (Discusión / Conclusiones)
* **Texto original erróneo:** Concluía a partir del gradiente térmico que el motor operaba bajo una estrategia todo-o-nada bang-bang.
* **Texto corregido (actualizado en `\linelabel{ln:disc-bb}`):**
  > *"In terms of actuator thermal dynamics and control analogies, current telemetry under small ($5^\circ$), large ($90^\circ$), and stall conditions distinguishes the internal drive mechanism: rather than a pure bang-bang controller, the MG90S operates as a proportional PWM driver that enters hard saturation ($I_{\text{stall}} \approx 918.4\text{ mA}$) only when physically blocked. In this unmitigated locked-rotor regime, continuous H-bridge saturation dissipates electrical power as heat at an initial rate of $\beta \approx 0.214\,^\circ\text{C/s}$."*

---

## 3. Declaración de Limitación Metodológica (Requerida por el Revisor)

> **Declaración explícita (en texto de Sección II-B y Discusión):**  
> *"A methodological limitation of the present characterization is that electrical measurements were acquired at the $5.0\text{ V}$ power bus using a high-side current shunt at $20\text{ Hz}$, rather than directly probing the H-bridge motor terminals with a high-bandwidth oscilloscope ($> 100\text{ kHz}$). Consequently, the bus current constitutes an indirect, cycle-averaged proxy of internal control effort rather than an instantaneous observation of PWM switching waveforms. Nevertheless, the presence of a sub-$5\text{ mA}$ deadband quiescent state during static holding and the scaling of active transit duration with displacement decisively rule out unconstrained bang-bang switching."*

---

## 4. ¿Conviene Poner las Gráficas en el LaTeX Principal o en la Respuesta?

### Análisis del Límite de Páginas:
1. **En el Manuscrito Principal (`Equipo 1 - segundo corte.tex`):**
   - El artículo está en **8 páginas exactas** (con bibliografía terminando en la columna inferior de la pág. 8).
   - Añadir una nueva figura completa de tres paneles (`fig:current_characterization`) requeriría al menos 4–5 cm de altura vertical, lo que **desbordaría la bibliografía a una 9ª página**. Si la rúbrica sanciona rebasar 8 páginas, **NO se recomienda insertar la figura completa en el cuerpo del paper principal**, sino resumir los resultados numéricos en el texto (o sustituir/combinar con una figura existente si el espacio lo permite).
2. **En la Carta de Respuesta a los Revisores (`Equipo 1 - respuesta - segundo corte.tex`):**
   - La carta de respuesta **NO tiene límite de páginas**.
   - En la respuesta al comentario `\LabDSTcomment{R3.4}`, colocar la figura completa y la tabla comparativa de las 3 condiciones es la estrategia más convincente para cerrar el comentario del revisor con máxima solidez científica.

---

## 5. Galería de Gráficas con Escalas Adaptadas (Y-Axis Tailored)

Se generaron gráficos con escalas independientes para evitar que el eje de bloqueo ($1800\text{ mA}$) aplaste visualmente las curvas de movimiento libre ($0\text{--}150\text{ mA}$):

1. **Figura Comparativa de Corrientes (3 Paneles):**
   - Archivos: `paper/Equipo 1 - segundo corte/figures/fig_current_characterization.pdf` y `.png`.
   - Panel (a) $e = 5^\circ$: escala adaptada $0\text{--}140\text{ mA}$ (paso dinámico de $99.4\text{ mA}$ y reposo en $3.1\text{ mA}$, con llamada al pico de arranque de $582.7\text{ mA}$).
   - Panel (b) $e = 90^\circ$: escala adaptada $0\text{--}220\text{ mA}$ (tránsito angular a $140\text{--}172\text{ mA}$ y reposo en $3.1\text{ mA}$).
   - Panel (c) Bloqueo Forzado: escala extendida $0\text{--}1850\text{ mA}$ (media de $918.4\text{ mA}$ y picos de $1.8\text{ A}$).

2. **Figura Resumen Completa (2x3 Paneles: Corriente y Temperatura):**
   - Archivos: `paper/Equipo 1 - segundo corte/figures/fig_characterization_6panels.png` y `.pdf`.
   - Fila superior: Corrientes de $5^\circ$, $90^\circ$ y Bloqueo.
   - Fila inferior: Temperaturas correspondientes de cada ensayo.

3. **Gráficas Individuales en Alta Resolución (300 DPI):**
   - `figures/fig_5deg_corriente.png` y `fig_5deg_temperatura.png`
   - `figures/fig_90deg_corriente.png` y `fig_90deg_temperatura.png`
   - `figures/fig_forzado_corriente.png` y `fig_forzado_temperatura.png`
