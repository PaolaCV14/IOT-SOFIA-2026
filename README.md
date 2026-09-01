# IOT-SOFIA-2026

Repositorio oficial para el desarrollo, modelado, simulación y documentación científica del proyecto **SOFIA** (Sistema Robótico Modular de Percepción e Interacción Expresiva) - LabDST, ITESO (Otoño 2026).

---

## Estructura del Repositorio

```text
IOT-SOFIA-2026/
├── SOFIA-Paper/              # Manuscrito científico en LaTeX (Formato IEEEtran)
│   ├── figures/              # Figuras y capturas del paper (fig_sim_1..6)
│   ├── IEEEtran.cls          # Clase oficial de documento IEEE
│   ├── bibliography.bib      # Referencias bibliográficas
│   └── plantilla_IEEE_LabDST.tex # Archivo fuente principal del artículo
│
├── code/                     # Código fuente de ingeniería
│   ├── tracking-vision/      # Software Python para visión 3D, cinemática inversa y tracking
│   ├── gui-control/          # Interfaz gráfica de escritorio en Python (Modos de operación y monitoreo)
│   └── firmware-mecatronica/ # Firmware C++/ESP-IDF para ESP32-C3, PCA9685, servos MG90S, Modbus/RS-485
│
├── docs/                     # Entregables técnicos y documentación
│   ├── entregables/          # Fichas técnicas, diagramas de bloques, bitácoras, matrices
│   └── recursos-clase/       # Notas de diseño y acuerdos del equipo
│
└── intake/                   # Material base de referencia del curso (LabDST)
    ├── class/                # Diapositivas de clase (Hardware, Cinemática, LaTeX, D-Lab)
    ├── catalog/              # Catálogo de entregables documentales
    ├── prototype/            # Planos y especificaciones del prototipo demostrador
    └── Guia de estudio.pdf   # Guía de aprendizaje y rúbricas
```

---

## Arquitectura del Sistema

1. **Percepción y Cinemática (Python):** Captura de visión en tiempo real, detección de objetivos/postura 3D y cálculo de cinemática inversa ($q_1, q_2$).
2. **Interfaz de Control (Python GUI):** Panel de control de escritorio para selección de modos de operación y visualización de telemetría.
3. **Comunicación Inalámbrica (PC $\to$ ESP32 Maestro):** Envío de tramas de comandos por Bluetooth / Wi-Fi.
4. **Bus Interno y Actuación (ESP32 $\to$ Módulos):** Distribución de consignas vía RS-485 / Modbus y generación de señales PWM a 50 Hz mediante drivers PCA9685 hacia los servomotores MG90S.
