# Código Fuente del Proyecto SOFIA

Estructura modular del código del proyecto:

- **[tracking-vision/](file:///Users/bernardoorozco/Documents/GitHub/IOT-SOFIA-2026/code/tracking-vision/)**: Scripts y módulos en Python para procesamiento de imagen y visión computacional (cámara, MediaPipe/OpenCV), seguimiento del objetivo en 3D y cálculo de cinemática inversa.
- **[gui-control/](file:///Users/bernardoorozco/Documents/GitHub/IOT-SOFIA-2026/code/gui-control/)**: Interfaz gráfica de escritorio en Python para concentrar los modos de operación de SOFIA, monitoreo de estados y telemetría.
- **[firmware-mecatronica/](file:///Users/bernardoorozco/Documents/GitHub/IOT-SOFIA-2026/code/firmware-mecatronica/)**: Firmware embebido en C++/Arduino/ESP-IDF para microcontroladores ESP32-C3, drivers PCA9685, servomotores MG90S y bus RS-485/Modbus.