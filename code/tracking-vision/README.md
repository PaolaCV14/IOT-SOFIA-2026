# Tracking, Visión y Cinemática (Sistemas / Software)

Espacio destinado a los módulos de software en Python para percepción y control cinemático:
- Procesamiento de imagen y visión por computadora (detección y tracking del objetivo/cuerpo en 3D).
- Detección de gestos en tiempo real: Corazón, Saludo dinámico, Intención PPT (3 bombas con puño), Tijera, Papel y Roca.
- Algoritmos de cinemática inversa y directa para el panal de 16 módulos.
- Conexión y envío de comandos de orientación vía **Bluetooth / Wi-Fi** hacia el ESP32 maestro.
- Scripts de simulación y visualización de trayectorias.

## Configuración del Entorno (Python)

> [!IMPORTANT]
> **Requisito de versión de Python:** MediaPipe requiere **Python 3.11 o 3.12** para instalarse correctamente (Python 3.14 es muy reciente y aún no cuenta con wheels pre-compilados de MediaPipe).

### 1. Consultar versiones de Python instaladas y sus rutas

Antes de crear el entorno, verifica dónde está instalado Python 3.11 o 3.12 en tu sistema:

* **En macOS / Linux:**
  ```bash
  # Listar la ruta del ejecutable específico:
  which python3.12
  which python3.11

  # O ver la versión de un ejecutable en particular:
  python3.12 --version
  ```

* **En Windows (Usando Python Launcher `py` o CMD/PowerShell):**
  ```cmd
  :: Listar todas las versiones instaladas y sus rutas completas:
  py -0p

  :: O verificar la ruta desde CMD/PowerShell:
  where python
  ```

---

### 2. Crear el entorno virtual (venv) especificando la versión

Si tu versión predeterminada (`python3` o `python`) es **Python 3.14**, debes indicarle explícitamente qué ejecutable utilizar para que el `venv` se cree con Python 3.11 o 3.12:

* **En macOS / Linux:**
  ```bash
  # Si el ejecutable está en el PATH (ej. con Homebrew o instalador oficial):
  python3.12 -m venv venv
  # O indicando la ruta absoluta hallada con 'which':
  /opt/homebrew/bin/python3.12 -m venv venv
  ```

* **En Windows:**
  ```cmd
  :: Opción recomendada usando el ejecutable "py" (Python Launcher):
  py -3.12 -m venv venv
  :: o con 3.11:
  py -3.11 -m venv venv

  :: Opción indicando la ruta absoluta (según el resultado de py -0p):
  C:\Users\TuUsuario\AppData\Local\Programs\Python\Python312\python.exe -m venv venv
  ```

### 3. Activar el entorno virtual

* **macOS / Linux:**
  ```bash
  source venv/bin/activate
  ```
* **Windows (CMD):**
  ```cmd
  .\venv\Scripts\activate
  ```
* **Windows (PowerShell):**
  ```powershell
  .\venv\Scripts\Activate.ps1
  ```

---

### 4. Instalar dependencias

Con el entorno activado (verás `(venv)` al inicio de la línea en tu terminal), instala las librerías necesarias:
```bash
pip install -r requirements.txt
```

---

## Reconocimiento de Posturas y Suavizado (Avance Actual)

El sistema ahora reconoce las **5 posturas diseñadas** (3 dinámicas y 2 estáticas), cuenta con un **filtro de suavizado (EMA)** para eliminar el temblor de la cámara y un panel en pantalla con FPS, latencia y exportador a CSV.

* **5 Posturas Implementadas:**
  1. **Saludo / Wave (Dinámica):** Sacudir la mano abierta de lado a lado.
  2. **Intención PPT (Dinámica):** Golpear 3 veces con el puño sobre la palma abierta.
  3. **Swipe / Deslizar (Dinámica):** Desplazar la mano abierta rápido hacia la izquierda o derecha.
  4. **Corazón (Estática):** Juntar las dos manos curvando índices y pulgares.
  5. **Tijera / Paz (Estática):** Dedos índice y medio abiertos en "V" con los demás doblados.

* **Documento de Reglas y Métricas:**
  Consulta la explicación completa de reglas, variables, umbrales y pruebas en:  
  👉 **[`docs/REGLAS_GESTOS_Y_METRICAS.md`](../../docs/REGLAS_GESTOS_Y_METRICAS.md)**

---

### 5. Ejecutar el script en vivo

Con el entorno activado, corre:
```bash
python main.py
```

**Controles en vivo durante el video:**
* **`S`** -> Activar / desactivar el suavizado de esqueleto (para comparar en vivo el temblor).
* **`L`** -> Iniciar / detener el guardado de métricas (FPS y latencia en ms) en un archivo `.csv` dentro de `benchmark_logs/`.
* **`Q`** -> Salir y apagar la cámara.
