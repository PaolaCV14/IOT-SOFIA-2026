/*
 * ==============================================================
 * SOFIA 2026 - Firmware ESP32-C3 (BLE + PCA9685)
 *
 * Protocolo PC <-> ESP32 (ver docs/ESTANDAR_COMUNICACION_PC_ESP32.md)
 *
 *   Solicitud (PC -> ESP32, caracteristica RX 6e400002):
 *       $<SEQ>,<CMD>[,<P1>[,<P2>]]#
 *
 *   Respuesta (ESP32 -> PC, caracteristica TX 6e400003, Notify):
 *       $<SEQ>,ACK,<DATOS...>#
 *       $<SEQ>,NACK,ERR_xx#
 *       $<SEQ>,EVT,DONE,<RUTINA>#     (fin de una rutina)
 *
 *   Comandos: PING, ANG q1 q2, Q1 a, Q2 a, ROUTINE nombre,
 *             HOME, REST, STOP
 *
 *   Las tramas pueden llegar fragmentadas en varias escrituras BLE
 *   (MTU por defecto = 20 bytes); se reensamblan con '$' y '#'.
 *   Las respuestas se envian en fragmentos de 20 bytes por la misma
 *   razon; la PC las reensambla.
 *
 *   Compatibilidad: una escritura sin '$' (p. ej. "90,90" o "SALUDO")
 *   se procesa como comando heredado, sin respuesta.
 * ==============================================================
 */

#include <Arduino.h>
#include <Wire.h>
#include <Adafruit_PWMServoDriver.h>
#include <BLEDevice.h>
#include <BLEServer.h>
#include <BLEUtils.h>
#include <BLE2902.h>

// ===== BLUETOOTH BLE UART (Nordic UART Service) =====
#define SERVICE_UUID "6e400001-b5a3-f393-e0a9-e50e24dcca9e"
#define CHARACTERISTIC_UUID "6e400002-b5a3-f393-e0a9-e50e24dcca9e" // RX
#define TX_UUID "6e400003-b5a3-f393-e0a9-e50e24dcca9e"             // TX
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

// ===== PROTOCOLO =====
#define FRAME_MAX_LEN 64      // Longitud maxima de una trama
#define NOTIFY_CHUNK 20       // Payload seguro con MTU por defecto (23 - 3)
#define COLA_TRAMAS 8         // Tramas pendientes entre la tarea BLE y loop()

int q1Actual = -1;
int q2Actual = -1;

bool pcaDisponible = false;
bool clienteConectado = false;

BLECharacteristic *pTxCharacteristic = nullptr;

// Cola FreeRTOS: la tarea BLE produce tramas completas y loop() las
// procesa. Asi la logica de servos/rutinas corre en un solo hilo.
struct Trama
{
    char texto[FRAME_MAX_LEN];
    bool heredado; // true = comando sin '$...#' (sin respuesta)
};
QueueHandle_t colaTramas = nullptr;

// Deduplicacion: si la PC reintenta un SEQ ya ejecutado (porque se
// perdio el ACK) se reenvia la respuesta guardada sin volver a ejecutar.
long ultimoSeq = -1;
String ultimaRespuesta = "";

// ==============================================================
// RUTINAS
// Cada rutina es una lista de poses (q1, q2) que se recorre
// "repeticiones" veces con "intervalo" ms entre poses. Despues de la
// ultima pose se espera un intervalo mas y se reporta EVT,DONE.
// ==============================================================
struct Rutina
{
    const char *nombre;
    const int (*pasos)[2];
    int numPasos;
    int repeticiones;
    unsigned long intervalo;
};

// SALUDO: asentir vertical (postura SALUDO)
const int pasosSaludo[][2] = {{90, 60}, {90, 120}};
// CORAZON: recorrido circular (postura CORAZON)
const int pasosCorazon[][2] = {{90, 120}, {120, 90}, {90, 60}, {60, 90}};
// BAILE: zigzag diagonal (postura TIJERA)
const int pasosBaile[][2] = {{70, 70}, {110, 110}, {70, 110}, {110, 70}};
// NEGAR: vaiven horizontal "no" (postura SWIPE)
const int pasosNegar[][2] = {{65, 90}, {115, 90}};
// PPT: tres golpes cortos de conteo (postura PPT)
const int pasosPpt[][2] = {{90, 100}, {90, 75}};
// CENTRAR: posicion neutra sostenida (postura ROCA)
const int pasosCentrar[][2] = {{90, 90}};
// REPOSO: posicion de descanso sostenida (postura PAPEL)
const int pasosReposo[][2] = {{90, 60}};

#define N_PASOS(arr) (sizeof(arr) / sizeof(arr[0]))

// Duraciones resultantes (pasos * repeticiones * intervalo):
// SALUDO 3000, CORAZON 2000, BAILE 3200, NEGAR 2100, PPT 1800,
// CENTRAR 2000, REPOSO 2000 ms. Deben coincidir con RUTINAS en
// code/communication/ble_sender.py (se usan como respaldo).
const Rutina RUTINAS[] = {
    {"SALUDO", pasosSaludo, N_PASOS(pasosSaludo), 3, 500},
    {"CORAZON", pasosCorazon, N_PASOS(pasosCorazon), 1, 500},
    {"BAILE", pasosBaile, N_PASOS(pasosBaile), 2, 400},
    {"NEGAR", pasosNegar, N_PASOS(pasosNegar), 3, 350},
    {"PPT", pasosPpt, N_PASOS(pasosPpt), 3, 300},
    {"CENTRAR", pasosCentrar, N_PASOS(pasosCentrar), 1, 2000},
    {"REPOSO", pasosReposo, N_PASOS(pasosReposo), 1, 2000},
};
const int NUM_RUTINAS = sizeof(RUTINAS) / sizeof(RUTINAS[0]);

// Estado de la rutina activa
const Rutina *rutinaActiva = nullptr;
int pasoRutina = 0;
int repeticionRutina = 0;
unsigned long tiempoUltimoPaso = 0;
long seqRutina = -1; // SEQ del comando ROUTINE para el evento DONE

// ===== CONTROL DEL SERVO =====
void moverServo(int canal, int angulo)
{
    angulo = constrain(angulo, ANGLE_MIN, ANGLE_MAX);

    int pulso = map(angulo, 0, 180, SERVO_MIN, SERVO_MAX);

    pwm.setPWM(canal, 0, pulso);
}

void moverAmbos(int q1, int q2)
{
    moverServo(SERVO_Q1, q1);
    moverServo(SERVO_Q2, q2);
    q1Actual = q1;
    q2Actual = q2;
}

// ==============================================================
// RESPUESTAS AL HOST
// ==============================================================
void enviarNotificacion(const String &trama)
{
    if (pTxCharacteristic == nullptr || !clienteConectado)
    {
        return;
    }

    // Fragmentar para respetar el MTU minimo; la PC reensambla.
    for (unsigned int i = 0; i < trama.length(); i += NOTIFY_CHUNK)
    {
        String parte = trama.substring(i, i + NOTIFY_CHUNK);
        pTxCharacteristic->setValue((uint8_t *)parte.c_str(), parte.length());
        pTxCharacteristic->notify();
        delay(3); // Evita saturar la pila BLE con notificaciones seguidas
    }
}

// Envia "$SEQ,<cuerpo>#". Si seq < 0 (comando heredado) no responde.
void responder(long seq, const String &cuerpo, bool guardar = true)
{
    if (seq < 0)
    {
        Serial.printf("(heredado) %s\n", cuerpo.c_str());
        return;
    }

    String trama = "$" + String(seq) + "," + cuerpo + "#";
    Serial.printf("TX: %s\n", trama.c_str());

    if (guardar)
    {
        ultimoSeq = seq;
        ultimaRespuesta = trama;
    }

    enviarNotificacion(trama);
}

void responderNack(long seq, const char *codigo)
{
    responder(seq, String("NACK,") + codigo);
}

// ==============================================================
// MOTOR DE RUTINAS (no bloqueante)
// ==============================================================
const Rutina *buscarRutina(const String &nombre)
{
    for (int i = 0; i < NUM_RUTINAS; i++)
    {
        if (nombre.equalsIgnoreCase(RUTINAS[i].nombre))
        {
            return &RUTINAS[i];
        }
    }
    return nullptr;
}

void ejecutarPasoRutina()
{
    int q1 = rutinaActiva->pasos[pasoRutina][0];
    int q2 = rutinaActiva->pasos[pasoRutina][1];

    moverAmbos(q1, q2);

    Serial.printf(
        "%s: repeticion %d/%d, paso %d/%d | Q1=%d, Q2=%d\n",
        rutinaActiva->nombre,
        repeticionRutina + 1,
        rutinaActiva->repeticiones,
        pasoRutina + 1,
        rutinaActiva->numPasos,
        q1,
        q2);

    tiempoUltimoPaso = millis();
}

void iniciarRutina(const Rutina *rutina, long seq)
{
    rutinaActiva = rutina;
    pasoRutina = 0;
    repeticionRutina = 0;
    seqRutina = seq;

    Serial.printf("=== INICIANDO RUTINA %s ===\n", rutina->nombre);

    // Ejecutar inmediatamente el primer paso.
    ejecutarPasoRutina();
}

void actualizarRutina()
{
    if (rutinaActiva == nullptr)
    {
        return;
    }

    if (millis() - tiempoUltimoPaso < rutinaActiva->intervalo)
    {
        return;
    }

    pasoRutina++;

    if (pasoRutina >= rutinaActiva->numPasos)
    {
        pasoRutina = 0;
        repeticionRutina++;

        if (repeticionRutina >= rutinaActiva->repeticiones)
        {
            Serial.printf("=== %s TERMINADO ===\n", rutinaActiva->nombre);

            // El evento DONE no reemplaza la respuesta guardada para
            // deduplicacion (es una notificacion asincrona).
            responder(seqRutina,
                      String("EVT,DONE,") + rutinaActiva->nombre,
                      false);

            rutinaActiva = nullptr;
            seqRutina = -1;
            Serial.println("Control normal habilitado");
            return;
        }
    }

    ejecutarPasoRutina();
}

// ==============================================================
// PARSEO Y EJECUCION DE COMANDOS
// ==============================================================

// Convierte un campo a entero validando que solo tenga digitos.
bool parsearEntero(const String &campo, int &valor)
{
    if (campo.length() == 0)
    {
        return false;
    }
    for (unsigned int i = 0; i < campo.length(); i++)
    {
        char c = campo[i];
        if (!(isdigit(c) || (i == 0 && c == '-')))
        {
            return false;
        }
    }
    valor = campo.toInt();
    return true;
}

bool anguloValido(int a)
{
    return a >= ANGLE_MIN && a <= ANGLE_MAX;
}

// Separa "A,B,C" en hasta maxCampos campos. Retorna el numero de campos.
int separarCampos(const String &texto, String campos[], int maxCampos)
{
    int n = 0;
    int inicio = 0;
    while (n < maxCampos)
    {
        int coma = texto.indexOf(',', inicio);
        String campo = (coma < 0) ? texto.substring(inicio)
                                  : texto.substring(inicio, coma);
        campo.trim();
        campos[n++] = campo;
        if (coma < 0)
        {
            break;
        }
        inicio = coma + 1;
    }
    return n;
}

// Ejecuta un comando ya separado: cmd + parametros. seq < 0 = heredado.
void ejecutarComando(long seq, String cmd, String params[], int nParams)
{
    cmd.toUpperCase();

    // --- PING: no requiere hardware ---
    if (cmd == "PING")
    {
        responder(seq, "ACK,PONG");
        return;
    }

    // --- STOP: cancela rutina y libera torque ---
    if (cmd == "STOP")
    {
        rutinaActiva = nullptr;
        seqRutina = -1;
        if (pcaDisponible)
        {
            pwm.setPWM(SERVO_Q1, 0, 4096); // bit FULL_OFF
            pwm.setPWM(SERVO_Q2, 0, 4096);
        }
        responder(seq, "ACK,STOPPED");
        return;
    }

    // A partir de aqui todos los comandos mueven servos
    if (!pcaDisponible)
    {
        responderNack(seq, "ERR_05");
        return;
    }

    // --- ROUTINE <nombre> ---
    if (cmd == "ROUTINE")
    {
        if (nParams < 1)
        {
            responderNack(seq, "ERR_03");
            return;
        }
        const Rutina *rutina = buscarRutina(params[0]);
        if (rutina == nullptr)
        {
            responderNack(seq, "ERR_02");
            return;
        }
        if (rutinaActiva != nullptr)
        {
            responderNack(seq, "ERR_04");
            return;
        }
        responder(seq, String("ACK,STARTED,") + rutina->nombre);
        iniciarRutina(rutina, seq);
        return;
    }

    // No permitir que movimientos directos interrumpan una rutina.
    if (rutinaActiva != nullptr)
    {
        responderNack(seq, "ERR_04");
        return;
    }

    // --- HOME / REST ---
    if (cmd == "HOME" || cmd == "REST")
    {
        int q2 = (cmd == "HOME") ? 90 : 60;
        moverAmbos(90, q2);
        responder(seq, "ACK,OK,90," + String(q2));
        return;
    }

    // --- ANG q1 q2 ---
    if (cmd == "ANG")
    {
        int q1, q2;
        if (nParams < 2 || !parsearEntero(params[0], q1) ||
            !parsearEntero(params[1], q2))
        {
            responderNack(seq, "ERR_03");
            return;
        }
        if (!anguloValido(q1) || !anguloValido(q2))
        {
            responderNack(seq, "ERR_01");
            return;
        }
        moverAmbos(q1, q2);
        responder(seq, "ACK,OK," + String(q1) + "," + String(q2));
        return;
    }

    // --- Q1 a / Q2 a ---
    if (cmd == "Q1" || cmd == "Q2")
    {
        int a;
        if (nParams < 1 || !parsearEntero(params[0], a))
        {
            responderNack(seq, "ERR_03");
            return;
        }
        if (!anguloValido(a))
        {
            responderNack(seq, "ERR_01");
            return;
        }
        if (cmd == "Q1")
        {
            moverServo(SERVO_Q1, a);
            q1Actual = a;
        }
        else
        {
            moverServo(SERVO_Q2, a);
            q2Actual = a;
        }
        responder(seq, "ACK,OK," + String(a));
        return;
    }

    responderNack(seq, "ERR_02");
}

// Procesa el contenido de una trama "$...#" (sin delimitadores).
void procesarTrama(const String &contenido)
{
    String campos[5];
    int n = separarCampos(contenido, campos, 5);

    int seqInt;
    if (n < 2 || !parsearEntero(campos[0], seqInt) || seqInt < 0 ||
        seqInt > 65535)
    {
        // Sin SEQ valido no hay a quien responder con seguridad;
        // se responde con SEQ 0 para que la PC registre el error.
        Serial.printf("Trama invalida: %s\n", contenido.c_str());
        responder(0, "NACK,ERR_03", false);
        return;
    }
    long seq = seqInt;

    // Reintento de un comando ya ejecutado: reenviar la respuesta.
    if (seq == ultimoSeq && ultimaRespuesta.length() > 0)
    {
        Serial.printf("SEQ %ld duplicado, reenviando respuesta\n", seq);
        enviarNotificacion(ultimaRespuesta);
        return;
    }

    ejecutarComando(seq, campos[1], &campos[2], n - 2);
}

// Comandos heredados sin trama: "90,90", "Q1,75", "SALUDO", etc.
void procesarHeredado(String comando)
{
    comando.trim();
    if (comando.length() == 0)
    {
        return;
    }

    String campos[3];
    int n = separarCampos(comando, campos, 3);

    if (n == 1)
    {
        // "SALUDO", "CORAZON", ... o "PING"/"HOME"/...
        if (buscarRutina(campos[0]) != nullptr)
        {
            String p[1] = {campos[0]};
            ejecutarComando(-1, "ROUTINE", p, 1);
        }
        else
        {
            ejecutarComando(-1, campos[0], nullptr, 0);
        }
        return;
    }

    String primero = campos[0];
    primero.toUpperCase();
    if (primero == "Q1" || primero == "Q2")
    {
        ejecutarComando(-1, primero, &campos[1], n - 1);
    }
    else
    {
        ejecutarComando(-1, "ANG", campos, n);
    }
}

// ==============================================================
// RECEPCION BLE (tarea BLE): reensamblado de tramas
// ==============================================================
char bufferRx[FRAME_MAX_LEN];
int largoRx = 0;
bool dentroDeTrama = false;

void encolarTrama(const char *texto, bool heredado)
{
    if (colaTramas == nullptr)
    {
        return;
    }
    Trama t;
    strncpy(t.texto, texto, FRAME_MAX_LEN - 1);
    t.texto[FRAME_MAX_LEN - 1] = '\0';
    t.heredado = heredado;
    if (xQueueSend(colaTramas, &t, 0) != pdTRUE)
    {
        Serial.println("ADVERTENCIA: cola de tramas llena, trama descartada");
    }
}

class BLECallbacks : public BLECharacteristicCallbacks
{
    void onWrite(BLECharacteristic *characteristic) override
    {
        String datos = characteristic->getValue().c_str();
        if (datos.length() == 0)
        {
            return;
        }

        // Comando heredado: escritura completa sin delimitadores.
        if (!dentroDeTrama && datos.indexOf('$') < 0)
        {
            encolarTrama(datos.c_str(), true);
            return;
        }

        for (unsigned int i = 0; i < datos.length(); i++)
        {
            char c = datos[i];

            if (c == '$')
            {
                // Inicio de trama: descarta cualquier fragmento previo.
                dentroDeTrama = true;
                largoRx = 0;
            }
            else if (c == '#' && dentroDeTrama)
            {
                bufferRx[largoRx] = '\0';
                encolarTrama(bufferRx, false);
                dentroDeTrama = false;
                largoRx = 0;
            }
            else if (dentroDeTrama)
            {
                if (largoRx < FRAME_MAX_LEN - 1)
                {
                    bufferRx[largoRx++] = c;
                }
                else
                {
                    // Trama demasiado larga: se descarta.
                    Serial.println("ERROR: trama excede longitud maxima");
                    dentroDeTrama = false;
                    largoRx = 0;
                }
            }
            // Bytes fuera de una trama se ignoran.
        }
    }
};

// ===== CONEXION BLE =====
class ServerCallbacks : public BLEServerCallbacks
{
    void onConnect(BLEServer *server) override
    {
        clienteConectado = true;
        Serial.println("Cliente BLE conectado");
    }

    void onDisconnect(BLEServer *server) override
    {
        clienteConectado = false;
        dentroDeTrama = false;
        largoRx = 0;
        ultimoSeq = -1; // Una nueva sesion puede reiniciar la secuencia
        ultimaRespuesta = "";
        rutinaActiva = nullptr;
        seqRutina = -1;

        // Medida de seguridad: regresar servos a posición neutra HOME (90, 90)
        // para evitar torques forzados por pérdida de señal.
        if (pcaDisponible)
        {
            moverAmbos(90, 90);
        }

        Serial.println("Cliente BLE desconectado -> Servos asegurados en HOME");
        BLEDevice::startAdvertising();
    }
};

// ===== CONFIGURACION INICIAL =====
void setup()
{
    Serial.begin(115200);
    delay(1500);

    Serial.println();
    Serial.println("=== SOFIA: BLE + PCA9685 (protocolo $SEQ,CMD#) ===");

    colaTramas = xQueueCreate(COLA_TRAMAS, sizeof(Trama));

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

    pTxCharacteristic = service->createCharacteristic(
        TX_UUID,
        BLECharacteristic::PROPERTY_NOTIFY);
    pTxCharacteristic->addDescriptor(new BLE2902());

    service->start();

    BLEAdvertising *advertising = BLEDevice::getAdvertising();
    advertising->addServiceUUID(SERVICE_UUID);
    advertising->setScanResponse(true);

    BLEDevice::startAdvertising();

    Serial.println("BLE anunciado como ESP32-Servos");
    Serial.println("Trama: $SEQ,CMD[,P1[,P2]]#  (ej. $1,ANG,90,90#)");
    Serial.println("Rutinas: SALUDO CORAZON BAILE NEGAR PPT CENTRAR REPOSO");
    Serial.println("Rango permitido: 60 a 120 grados");
}

void loop()
{
    // Procesar todas las tramas pendientes recibidas por BLE
    Trama t;
    while (colaTramas != nullptr &&
           xQueueReceive(colaTramas, &t, 0) == pdTRUE)
    {
        Serial.printf("RX: %s%s\n", t.heredado ? "(heredado) " : "", t.texto);
        if (t.heredado)
        {
            procesarHeredado(String(t.texto));
        }
        else
        {
            procesarTrama(String(t.texto));
        }
    }

    actualizarRutina();
    delay(2);
}
