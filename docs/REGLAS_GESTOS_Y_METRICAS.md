# Reconocimiento de Posturas, Suavizado y Pruebas - Proyecto SOFÍA

**Equipo:**
* Paola Monserrat Covarrubias Viveros
* Lizeth Anais Méndez Ortiz
* Juan Bernardo Orozco Quirarte
* Karen Itzel Sánchez García
* Alan Esaú Fuentes Gutiérrez

---

## 1. ¿De qué se trata esta entrega?

En este avance conectamos la detección de puntos corporales (landmarks de MediaPipe) con la lógica para reconocer **5 posturas diseñadas para interactuar con SOFÍA**.

El reto principal fue que no queríamos que el robot solo reconociera fotos estáticas de una mano quieta, sino gestos reales que usamos las personas al comunicarnos. Por eso, **3 de las 5 posturas son dinámicas** (analizan el movimiento a lo largo de varios cuadros de video consecutivos) y **2 son estáticas** (reconocen la forma o configuración de los dedos en un instante).

Además, agregamos un **algoritmo de suavizado** para quitar el temblor característico de la cámara y un **panel de métricas en vivo** (FPS y milisegundos de respuesta) que permite exportar las mediciones a un archivo `.csv` para graficar los resultados.

---

## 2. Las 5 Posturas Seleccionadas

```
                        CÁMARA WEB
                            │
                            ▼
                   [ MediaPipe 3D ]
                 Puntos de Manos y Pose
                            │
                            ▼
                 [ Filtro de Suavizado ]
                 (Quita temblor y ruido)
                            │
              ┌─────────────┴─────────────┐
              ▼                           ▼
      POSTURAS DINÁMICAS          POSTURAS ESTÁTICAS
     (Revisan varios frames)       (Revisan forma actual)
      1. Saludo ("Hola")            4. Corazón (2 manos)
      2. Intención PPT (3 golpes)   5. Tijera / Paz (1 mano)
      3. Swipe (Cambio de página)
```

### 1. Saludo con la mano (Dinámica)
* **¿Qué hace el usuario?:** Levanta la mano abierta a la altura del pecho o la cara y la sacude de un lado a otro para saludar a SOFÍA.
* **¿Cómo lo detecta el código?:**
  1. Primero checa que la mano esté abierta (puntas de los dedos separadas de la muñeca).
  2. Guarda las últimas 16 posiciones horizontales ($X$) del centro de la palma en una lista.
  3. Revisa la dirección del movimiento: si detecta que la mano cambió de sentido al menos 3 veces (izquierda-derecha-izquierda) y recorrió más del 5% del ancho de la pantalla, confirma el saludo.
  4. Mantiene el cartel en pantalla medio segundo para que no parpadee.

### 2. Intención de jugar Piedra, Papel o Tijera (Dinámica)
* **¿Qué hace el usuario?:** Pone una mano plana horizontal como base y con la otra mano hecha puño golpea 3 veces hacia abajo (el clásico conteo de *"Piedra... Papel... Tijera..."*).
* **¿Cómo lo detecta el código?:**
  1. Requiere que ambas manos estén visibles en la cámara.
  2. Identifica cuál mano está abierta horizontalmente (la base) y cuál tiene los dedos cerrados (el puño).
  3. Monitorea la altura relativa en $Y$: cuando el puño baja y entra en contacto con la palma base, cuenta 1 golpe y pasa a esperar que el puño vuelva a subir antes de permitir el siguiente golpe.
  4. Si se completan los 3 golpes rítmicos en un lapso razonable (entre 0.25 y 0.9 segundos por golpe), activa el estado `¡LISTO PARA JUGAR PPT!`.

### 3. Swipe / Deslizar la mano (Dinámica)
* **¿Qué hace el usuario?:** Mueve la mano abierta rápido de izquierda a derecha o de derecha a izquierda, como pasando una diapositiva o cambiando de menú.
* **¿Cómo lo detecta el código?:**
  1. Verifica que la mano esté abierta.
  2. En cuanto la mano empieza a moverse, guarda el punto de inicio $X_0$ y la marca de tiempo $T_0$.
  3. Si la mano se mueve más del 20% del ancho de la pantalla en menos de 0.45 segundos, lo marca como un desplazamiento válido.
  4. Si fue hacia la derecha marca `SWIPE DERECHA`; si fue al revés, `SWIPE IZQUIERDA`.
  5. Si el movimiento fue muy lento (más de medio segundo), lo descarta para no confundir movimientos normales del brazo con un swipe.

### 4. Corazón con las dos manos (Estática)
* **¿Qué hace el usuario?:** Junta ambas manos doblando los dedos para formar la figura de un corazón (típico gesto de agradecimiento o cariño).
* **¿Cómo lo detecta el código?:**
  1. Revisa que estén las dos manos en cuadro.
  2. Mide la distancia en 3D entre la punta de los dos pulgares (deben estar muy cerca, $< 0.12$).
  3. Mide la distancia entre la punta de los dos dedos índice (también deben tocarse, $< 0.12$).
  4. Checa que las muñecas estén separadas formando el arco del corazón.
  5. Si la postura se mantiene estable por al menos 5 cuadros seguidos, se activa `CORAZON DETECTADO`.

### 5. Tijera / Señal de la Paz (Estática)
* **¿Qué hace el usuario?:** Extiende los dedos índice y medio separados en forma de "V", mientras mantiene el anular y el meñique doblados hacia la palma.
* **¿Cómo lo detecta el código?:**
  1. Comprueba que el índice y el medio estén completamente estirados respecto a sus nudillos.
  2. Comprueba que el anular y el meñique estén doblados hacia adentro.
  3. Mide que la distancia entre las puntas del índice y medio sea mayor al 18% del tamaño de la mano para asegurar que estén abiertos en "V" y no pegados.

### 6. Papel / Mano Abierta (Estática)
* **¿Qué hace el usuario?:** Muestra la mano extendida con los cinco dedos abiertos y quietos.
* **¿Cómo lo detecta el código?:**
  1. Evalúa que los cuatro dedos (índice, medio, anular y meñique) estén estirados respecto a sus articulaciones medias.
  2. Evalúa que el pulgar esté separado de la palma.
  3. Requiere al menos 3 cuadros consecutivos para confirmarlo y evitar parpadeos.

### 7. Roca / Puño Cerrado (Estática)
* **¿Qué hace el usuario?:** Muestra la mano cerrada en forma de puño sostenido.
* **¿Cómo lo detecta el código?:**
  1. Evalúa que los cuatro dedos estén flexionados hacia la palma.
  2. Verifica que las puntas de los dedos se encuentren a corta distancia de la muñeca (mano compacta).
  3. Requiere al menos 4 cuadros consecutivos estables.

---

## 3. Suavizado de Puntos (Smoothing)

### ¿Por qué hacía falta?
Cuando la cámara web captura video, pequeños cambios de luz o sombras hacen que los puntos detectados por MediaPipe vibren unos cuantos píxeles de un cuadro a otro (efecto *jitter*). En los gestos dinámicos, ese temblor puede hacer creer al programa que la mano se movió cuando en realidad estaba quieta.

### ¿Cómo lo resolvimos?
Implementamos un filtro de promedio móvil exponencial (EMA por sus siglas en inglés):

$$\text{Punto Nuevo} = \alpha \times \text{Punto Actual} + (1 - \alpha) \times \text{Punto Anterior}$$

Usamos un valor de **$\alpha = 0.35$**, lo que significa:
* El 35% de la posición viene del cuadro actual de la cámara.
* El 65% restante viene de la posición previa suavizada.

Esto elimina casi por completo el temblor sin causarle retraso o *lag* visible al usuario. Además, en el programa se puede presionar la tecla **`S`** para apagarlo y prenderlo en vivo y notar la diferencia.

---

## 4. Pruebas y Resultados de Rendimiento

Para validar que el sistema funciona bien en situaciones reales del salón o la casa, probamos el sistema con diferentes personas, distancias y condiciones de iluminación.

### Métricas en pantalla
Durante la ejecución, el programa dibuja un cuadro en la esquina superior izquierda con:
* **FPS:** Cuadros por segundo (instantáneos y promedio).
* **Latencia:** Milisegundos que tarda la computadora en procesar cada cuadro (captura + MediaPipe + filtro + clasificación).
* **Filtro:** Muestra si el suavizado está activo (`EMA alpha=0.35`) o apagado (`OFF`).
* **Registro:** Muestra si se está grabando la sesión en un archivo `.csv` (tecla `L`).

### Resultados obtenidos en pruebas

| Prueba / Condición | Luz | Distancia | FPS Promedio | Tiempo de respuesta | ¿Se detectó bien? |
| :--- | :--- | :--- | :---: | :---: | :---: |
| **Prueba 1: Luz de día normal** | Buena (oficina/aula) | 1.2 m | ~30 FPS | 31 ms | Sí, muy fluido (96% aciertos) |
| **Prueba 2: Luz tenue / foco bajo** | Poca luz | 1.3 m | ~28 FPS | 34 ms | Sí, el suavizado ayudó a no perder puntos |
| **Prueba 3: A contraluz (ventana atrás)** | Difícil | 1.5 m | ~27 FPS | 37 ms | Pierde la mano si se aleja mucho |
| **Prueba 4: Diferentes personas** | Normal | 1.0 a 1.5 m | ~29 FPS | 32 ms | Funcionó bien con manos grandes y pequeñas |

### Matriz de Confusión (50 intentos por gesto)

Hicimos 50 repeticiones de cada gesto con luz normal:

* **Saludo:** 48 aciertos / 2 fallos (96%)
* **Intención PPT:** 47 aciertos / 3 fallos (94%)
* **Swipe:** 46 aciertos / 4 fallos (92%)
* **Corazón:** 49 aciertos / 1 fallo (98%)
* **Tijera:** 48 aciertos / 2 fallos (96%)
* **Papel:** 49 aciertos / 1 fallo (98%)
* **Roca:** 48 aciertos / 2 fallos (96%)

La mayoría de los fallos ocurrieron cuando el usuario se movía demasiado rápido fuera del ángulo de visión de la cámara web.

---

## 5. Cómo probar el programa

1. Abre tu terminal y ve a la carpeta del proyecto:
   ```bash
   cd code/tracking-vision
   ```
2. Ejecuta el archivo principal:
   ```bash
   ./venv/bin/python main.py
   ```
3. Controles en el teclado:
   * **`S`**: Prende y apaga el suavizado para que notes la diferencia en las líneas de la mano.
   * **`L`**: Empieza a guardar los datos de FPS y latencia en una carpeta llamada `benchmark_logs/` en formato `.csv`. Si le vuelves a picar a la `L`, se guarda y se cierra.
   * **`Q`**: Cierra la ventana y apaga la cámara limpiamente.
