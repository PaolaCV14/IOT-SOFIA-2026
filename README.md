# IOT-SOFIA-2026

Repositorio oficial para el desarrollo, modelado, simulación y documentación científica del proyecto **SOFIA** (Sistema Robótico Modular de Percepción e Interacción Expresiva) - LabDST, ITESO (Otoño 2026).

---

## Estructura del Repositorio

```text
IOT-SOFIA-2026/
├── paper/                       # Manuscrito científico en LaTeX (Formato IEEEtran)
│   ├── Equipo 1 - segundo corte/# Archivos fuente del artículo académico del equipo
│   └── figures/                 # Figuras y capturas del paper
│
├── code/                        # Código fuente modular de ingeniería
│   ├── tracking-vision/         # Pipeline de visión 3D, MediaPipe, gestos y filtro EMA
│   │   └── GUIA_VISION_Y_POSTURAS.md # Manual universitario de cinemática, landmarks y filtrado
│   ├── communication/           # Enlace inalámbrico BLE (ESP32-C3) y sockets UDP (Unity)
│   ├── gui-control/             # Estación de control de escritorio (PySide6 / .exe)
│   ├── firmware-mecatronica/    # Firmware embebido para microcontroladores
│   └── CODE.md                  # Mapa integral de arquitectura y guía operativa de conexión
│
├── WEBOT SOFIA/                 # Gemelo digital en Webots (Mundo .wbt, modelos CAD 3D y pruebas BLE)
│
├── unity-simulation/            # Simulación 3D en Unity (Escenario y panal de módulos en C#)
│
└── docs/                        # Documentación central, clases, entregables y datos
    ├── class-slides/            # Diapositivas de clase (Hardware, Cinemática, LaTeX, D-Lab)
    ├── catalog/                 # Catálogo de entregables documentales
    ├── prototype-cad/           # Planos y especificaciones del prototipo demostrador
    └── experimental-data/       # Registros y pruebas de caracterización de actuadores
```

---

## Arquitectura del Sistema

1. **Percepción y Cinemática (Python):** Captura de visión en tiempo real, detección de manos (21 puntos) y postura corporal 3D con MediaPipe y OpenCV, y cálculo de cinemática inversa ($q_1, q_2$).
2. **Simulación 3D (Unity / Webots):** Entorno virtual para validación de la cinemática directa/inversa de la matriz de 16 módulos.
3. **Comunicación e Interfaz:** Integración inalámbrica PC $\to$ ESP32 Maestro (Wi-Fi / Bluetooth).
4. **Bus Interno y Actuación:** Generación de señales PWM a 50 Hz vía drivers PCA9685 hacia los 32 servomotores MG90S.
