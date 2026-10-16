#include <Arduino.h>
#include <Wire.h>
#include <Adafruit_PWMServoDriver.h>
#include <BLEDevice.h>
#include <BLEServer.h>
#include <BLEUtils.h>

// ===== BLUETOOTH BLE UART =====
#define SERVICE_UUID "6e400001-b5a3-f393-e0a9-e50e24dcca9e"
#define CHARACTERISTIC_UUID "6e400002-b5a3-f393-e0a9-e50e24dcca9e"
#define DEVICE_NAME "ESP32-Servos"

// ===== PCA9685 =====
Adafruit_PWMServoDriver pwm(0x40);

#define SDA_PIN 8
#define SCL_PIN 9

#define SERVO_Q1 14
#define SERVO_Q2 15

#define SERVO_MIN 150
#define SERVO_MAX 600

// ===== RANGO PERMITIDO =====
#define ANGLE_MIN 60
#define ANGLE_MAX 120

int q1Actual = -1;
int q2Actual = -1;

bool pcaDisponible = false;

// RUTINAS
// SALUDO
const int rutinaSaludo[][2] = {
    {90, 60},
    {90, 120}};

const int NUM_PASOS_SALUDO =
    sizeof(rutinaSaludo) / sizeof(rutinaSaludo[0]);

const int REPETICIONES_SALUDO = 3;
const unsigned long INTERVALO_SALUDO = 500;

bool saludoActivo = false;
int pasoSaludo = 0;
int repeticionSaludo = 0;
unsigned long tiempoUltimoPaso = 0;

// CORAZON
const int rutinaCorazon[][2] = {
    {90, 120},
    {120, 90},
    {90, 60},
    {60, 90}};

const int NUM_PASOS_CORAZON =
    sizeof(rutinaCorazon) / sizeof(rutinaCorazon[0]);

const int REPETICIONES_CORAZON = 1;

bool corazonActivo = false;
int pasoCorazon = 0;
int repeticionCorazon = 0;
unsigned long tiempoUltimoPasoCorazon = 0;

// ===== CONTROL DEL SERVO =====
void moverServo(int canal, int angulo)
{
    angulo = constrain(angulo, ANGLE_MIN, ANGLE_MAX);

    int pulso = map(angulo, 0, 180, SERVO_MIN, SERVO_MAX);

    pwm.setPWM(canal, 0, pulso);
}

// ===== INICIAR RUTINA DE SALUDO =====
void iniciarRutinaSaludo()
{
    if (!pcaDisponible)
    {
        Serial.println("ERROR: PCA9685 no disponible");
        return;
    }

    if (saludoActivo || corazonActivo)
    {
        Serial.println("Otra rutina esta en ejecucion");
        return;
    }

    saludoActivo = true;
    pasoSaludo = 0;
    repeticionSaludo = 0;

    Serial.println("=== INICIANDO RUTINA SALUDO ===");

    // Ejecutar inmediatamente el primer paso.
    ejecutarPasoSaludo();
}

// ===== EJECUTAR UN PASO DE LA RUTINA =====
void ejecutarPasoSaludo()
{
    int q1 = rutinaSaludo[pasoSaludo][0];
    int q2 = rutinaSaludo[pasoSaludo][1];

    moverServo(SERVO_Q1, q1);
    moverServo(SERVO_Q2, q2);

    q1Actual = q1;
    q2Actual = q2;

    Serial.printf(
        "Saludo: repeticion %d/%d, paso %d/%d | Q1=%d, Q2=%d\n",
        repeticionSaludo + 1,
        REPETICIONES_SALUDO,
        pasoSaludo + 1,
        NUM_PASOS_SALUDO,
        q1,
        q2);

    tiempoUltimoPaso = millis();
}

// ===== ACTUALIZAR RUTINA SIN BLOQUEAR EL ESP32 =====
void actualizarRutinaSaludo()
{
    if (!saludoActivo)
    {
        return;
    }

    if (millis() - tiempoUltimoPaso < INTERVALO_SALUDO)
    {
        return;
    }

    pasoSaludo++;

    if (pasoSaludo >= NUM_PASOS_SALUDO)
    {
        pasoSaludo = 0;
        repeticionSaludo++;

        if (repeticionSaludo >= REPETICIONES_SALUDO)
        {
            saludoActivo = false;

            Serial.println("=== SALUDO TERMINADO ===");
            Serial.println("Control normal habilitado");
            return;
        }
    }

    ejecutarPasoSaludo();
}

// ===== INICIAR RUTINA CORAZON =====
void iniciarRutinaCorazon()
{
    if (!pcaDisponible)
    {
        Serial.println("ERROR: PCA9685 no disponible");
        return;
    }

    if (saludoActivo || corazonActivo)
    {
        Serial.println("Otra rutina esta en ejecucion");
        return;
    }

    corazonActivo = true;
    pasoCorazon = 0;
    repeticionCorazon = 0;

    Serial.println("=== INICIANDO RUTINA CORAZON ===");

    ejecutarPasoCorazon();
}

// ===== EJECUTAR PASO CORAZON =====
void ejecutarPasoCorazon()
{
    int q1 = rutinaCorazon[pasoCorazon][0];
    int q2 = rutinaCorazon[pasoCorazon][1];

    moverServo(SERVO_Q1, q1);
    moverServo(SERVO_Q2, q2);

    q1Actual = q1;
    q2Actual = q2;

    Serial.printf(
        "CORAZON: repeticion %d/%d, paso %d/%d | Q1=%d, Q2=%d\n",
        repeticionCorazon + 1,
        REPETICIONES_CORAZON,
        pasoCorazon + 1,
        NUM_PASOS_CORAZON,
        q1,
        q2);

    tiempoUltimoPasoCorazon = millis();
}

// ===== ACTUALIZAR RUTINA CORAZON =====
void actualizarRutinaCorazon()
{
    if (!corazonActivo)
    {
        return;
    }

    if (millis() - tiempoUltimoPasoCorazon < INTERVALO_SALUDO)
    {
        return;
    }

    pasoCorazon++;

    if (pasoCorazon >= NUM_PASOS_CORAZON)
    {
        pasoCorazon = 0;
        repeticionCorazon++;

        if (repeticionCorazon >= REPETICIONES_CORAZON)
        {
            corazonActivo = false;

            Serial.println("=== CORAZON TERMINADO ===");
            Serial.println("Control normal habilitado");
            return;
        }
    }

    ejecutarPasoCorazon();
}

// ===== PROCESAMIENTO DE COMANDOS =====

void procesarComando(String comando)
{
    unsigned long inicio = millis();

    comando.trim();

    // Comando especial para ejecutar la rutina almacenada.
    if (comando.equalsIgnoreCase("SALUDO"))
    {
        iniciarRutinaSaludo();
        return;
    }

    if (comando.equalsIgnoreCase("CORAZON"))
    {
        iniciarRutinaCorazon();
        return;
    }
    // No permitir que otros movimientos interrumpan el saludo.
    if (saludoActivo || corazonActivo)
    {
        Serial.println("Comando ignorado: rutina en ejecucion");
        return;
    }

    Serial.printf("[+%lu ms] Procesando: %s\n",
                  millis() - inicio, comando.c_str());

    int coma = comando.indexOf(',');

    if (coma < 0)
    {
        Serial.println("ERROR: usa 60,90 o Q1,75");
        return;
    }

    String primero = comando.substring(0, coma);
    String segundo = comando.substring(coma + 1);

    primero.trim();
    segundo.trim();

    if (primero.length() == 0 || segundo.length() == 0)
    {
        Serial.println("ERROR: comando incompleto");
        return;
    }

    if (primero.equalsIgnoreCase("Q1") ||
        primero.equalsIgnoreCase("Q2"))
    {

        int angulo = segundo.toInt();

        if (angulo < ANGLE_MIN || angulo > ANGLE_MAX)
        {
            Serial.println("ERROR: angulo fuera de rango");
            return;
        }

        if (!pcaDisponible)
        {
            Serial.println("ERROR: PCA9685 no disponible");
            return;
        }

        if (primero.equalsIgnoreCase("Q1"))
        {
            moverServo(SERVO_Q1, angulo);
            q1Actual = angulo;
        }
        else
        {
            moverServo(SERVO_Q2, angulo);
            q2Actual = angulo;
        }
    }
    else
    {
        int nuevoQ1 = primero.toInt();
        int nuevoQ2 = segundo.toInt();

        if (nuevoQ1 < ANGLE_MIN || nuevoQ1 > ANGLE_MAX ||
            nuevoQ2 < ANGLE_MIN || nuevoQ2 > ANGLE_MAX)
        {
            Serial.println("ERROR: q1 y q2 deben estar entre 60 y 120");
            return;
        }

        if (!pcaDisponible)
        {
            Serial.println("ERROR: PCA9685 no disponible");
            return;
        }

        moverServo(SERVO_Q1, nuevoQ1);
        moverServo(SERVO_Q2, nuevoQ2);

        q1Actual = nuevoQ1;
        q2Actual = nuevoQ2;
    }

    Serial.printf("[+%lu ms] Orden aplicada: Q1=%d, Q2=%d\n",
                  millis() - inicio, q1Actual, q2Actual);
}

// ===== RECEPCION BLE =====
class BLECallbacks : public BLECharacteristicCallbacks
{
    void onWrite(BLECharacteristic *characteristic) override
    {
        String comando = characteristic->getValue().c_str();

        if (comando.length() > 0)
        {
            Serial.print("BLE recibido: ");
            Serial.println(comando);

            procesarComando(comando);
        }
    }
};

// ===== CONEXION BLE =====
class ServerCallbacks : public BLEServerCallbacks
{
    void onConnect(BLEServer *server) override
    {
        Serial.println("Cliente BLE conectado");
    }

    void onDisconnect(BLEServer *server) override
    {
        Serial.println("Cliente BLE desconectado");
        BLEDevice::startAdvertising();
    }
};

// ===== CONFIGURACION INICIAL =====
void setup()
{
    Serial.begin(115200);
    delay(1500);

    Serial.println();
    Serial.println("=== SOFIA: BLE + PCA9685 ===");

    Wire.begin(SDA_PIN, SCL_PIN);

    pcaDisponible = pwm.begin();

    if (pcaDisponible)
    {
        pwm.setPWMFreq(50);
        Serial.println("PCA9685 RESPONDE");
    }
    else
    {
        Serial.println("ERROR: PCA9685 NO RESPONDE");
    }

    // No mover los servos automaticamente al arrancar.
    BLEDevice::init(DEVICE_NAME);

    BLEServer *server = BLEDevice::createServer();
    server->setCallbacks(new ServerCallbacks());

    BLEService *service = server->createService(SERVICE_UUID);

    BLECharacteristic *rx = service->createCharacteristic(
        CHARACTERISTIC_UUID,
        BLECharacteristic::PROPERTY_WRITE |
            BLECharacteristic::PROPERTY_WRITE_NR);

    rx->setCallbacks(new BLECallbacks());

    service->start();

    BLEAdvertising *advertising = BLEDevice::getAdvertising();
    advertising->addServiceUUID(SERVICE_UUID);
    advertising->setScanResponse(true);

    BLEDevice::startAdvertising();

    Serial.println("BLE anunciado como ESP32-Servos");
    Serial.println("Formato conjunto: 90,90");
    Serial.println("Formato individual: Q1,75 o Q2,105");
    Serial.println("Rango permitido: 60 a 120 grados");
}

void loop()
{
    actualizarRutinaSaludo();
    actualizarRutinaCorazon();
    delay(2);
}