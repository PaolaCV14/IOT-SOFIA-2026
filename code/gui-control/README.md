# Estación de Control y Monitoreo SOFIA (PySide6 GUI)

Interfaz gráfica de escritorio moderna, intuitiva y optimizada para el monitoreo de visión por computadora en tiempo real y el control cinemático de los módulos robóticos del proyecto **SOFIA 2026**.

---

## 🚀 Características Principales

1. **Visor de Cámara a 60 FPS:** Renderizado en tiempo real con superposición de landmarks (manos, postura corporal y gestos).
2. **Arquitectura Multihilo (`QThread`) con Control de Ciclo de Vida:** El procesamiento de MediaPipe y OpenCV se ejecuta en un hilo separado con controles completos de inicio, pausa/reanudación y detención sin bloquear la interfaz.
3. **Modos de Operación:**
   - **Seguimiento Automático 3D:** Envío continuo de ángulos calculados ($q_1, q_2$) por UDP o BLE.
   - **Control Manual:** Sliders interactivos para fijar ángulos articulares.
   - **Calibración y Reposo:** Para mantenimiento del hardware.
4. **Telemetría y Logs:** Métricas de FPS, latencia en ms y terminal integrada de eventos.

---

## 🛠️ Instalación de Dependencias

```bash
cd code/gui-control
pip install -r requirements.txt
```

---

## ▶️ Ejecución en Desarrollo

```bash
python main_gui.py
```

---

## 📦 Generación del Ejecutable (`.exe`) para Windows

Para compilar todo en un único archivo ejecutable portátil:

```bash
pyinstaller build_exe.spec
```

El ejecutable resultante se generará en la carpeta `dist/SOFIA_Control_Station.exe`, listo para operar sin necesidad de tener Python instalado.
