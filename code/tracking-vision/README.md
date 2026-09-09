# Tracking, Visión y Cinemática (Sistemas / Software)

Espacio destinado a los módulos de software en Python para percepción y control cinemático:
- Procesamiento de imagen y visión por computadora (detección y tracking del objetivo/cuerpo en 3D).
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

### 5. Ejecutar el script

```bash
python tracking.py
```
