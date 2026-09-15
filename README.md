# IOT-SOFIA-2026

Repositorio oficial para el desarrollo, modelado, simulación y documentación científica del proyecto **SOFIA** (Sistema Robótico Modular de Percepción e Interacción Expresiva) - LabDST, ITESO (Otoño 2026).

---

## Estructura del Repositorio

```text
IOT-SOFIA-2026/
├── paper/                       # Manuscrito científico en LaTeX (Formato IEEEtran)
│   ├── figures/                 # Figuras y capturas del paper
│   ├── IEEEtran.cls             # Clase oficial de documento IEEE
│   ├── bibliography.bib         # Referencias bibliográficas (BibTeX)
│   ├── plantilla_IEEE_LabDST.tex# Archivo fuente principal del artículo
│   └── plantilla_IEEE_LabDST.pdf# Manuscrito compilado en PDF
│
├── code/                        # Código fuente de ingeniería
│   └── tracking-vision/         # Módulo Python para visión 3D, cinemática inversa y tracking
│
├── unity-simulation/            # Simulación 3D en Unity (Escenario y panal de 16 módulos)
│
└── docs/                        # Documentación central, clases, entregables y datos
    ├── class-slides/            # Diapositivas de clase (Hardware, Cinemática, LaTeX, D-Lab) + Guía de estudio
    ├── catalog/                 # Catálogo de entregables documentales
    ├── prototype-cad/           # Planos y especificaciones del prototipo demostrador (SOFIA003)
    └── experimental-data/       # Registros y pruebas de caracterización de actuadores (Excel)
```

---

## Arquitectura del Sistema

1. **Percepción y Cinemática (Python):** Captura de visión en tiempo real, detección de manos (21 puntos) y postura corporal 3D con MediaPipe y OpenCV, y cálculo de cinemática inversa ($q_1, q_2$).
2. **Simulación 3D (Unity / Webots):** Entorno virtual para validación de la cinemática directa/inversa de la matriz de 16 módulos.
3. **Comunicación e Interfaz:** Integración inalámbrica PC $\to$ ESP32 Maestro (Wi-Fi / Bluetooth).
4. **Bus Interno y Actuación:** Generación de señales PWM a 50 Hz vía drivers PCA9685 hacia los 32 servomotores MG90S.
