// esp32code/esp32code.ino
#include <WiFi.h>
#include <PubSubClient.h>
#include <AccelStepper.h>
#include <LiquidCrystal_I2C.h>
#include "config.h"

// ==========================================
// OBJETOS GLOBALES
// ==========================================
WiFiClient espClient;
PubSubClient mqttClient(espClient);

// Motor a pasos (Half-step config = 8)
AccelStepper motor(
    AccelStepper::HALF4WIRE, 
    PIN_IN1, PIN_IN3, PIN_IN2, PIN_IN4
);

// Display LCD (Dirección I2C 0x27 genérica, 16 columnas, 2 filas)
LiquidCrystal_I2C lcd(0x27, 16, 2);

// ==========================================
// ESTADO DEL SISTEMA
// ==========================================
int posicionActual = 1;         // Compartimiento 1 al 8
int compartimientoActivo = -1;  // Último compartimiento que se mandó mover
bool esperandoConfirmacion = false;

// Variables para alarma (Non-blocking)
unsigned long ultimoParpadeo = 0;
const unsigned long intervaloAlarma = 500; // ms
bool estadoAlarma = false;

// Variables para Debounce de Botón
bool lastDebounceState = HIGH;
bool buttonState = HIGH;
unsigned long lastDebounceTime = 0;
const unsigned long debounceDelay = 50;

// ==========================================
// DECLARACIÓN DE FUNCIONES
// ==========================================
void setupWiFi();
void reconnectMQTT();
void mqttCallback(char* topic, byte* payload, unsigned int length);
void goToCompartment(int id);
void handleButton();
void confirmDrugTaken();
void updateAlarm();

// ==========================================
// INIT SETUP
// ==========================================
void setup() {
    Serial.begin(115200);

    // Pines
    pinMode(PIN_BOTON, INPUT_PULLUP);
    pinMode(PIN_LED, OUTPUT);
    pinMode(PIN_BUZZER, OUTPUT);
    digitalWrite(PIN_LED, LOW);
    digitalWrite(PIN_BUZZER, LOW);

    // Init LCD
    lcd.init();
    lcd.backlight();
    lcd.clear();
    lcd.setCursor(0, 0);
    lcd.print("Iniciando...");

    // Setup Motor
    motor.setMaxSpeed(1000.0);
    motor.setAcceleration(500.0);
    // Asumimos que inicia físicamente en compartimiento 1 -> Posición = 0 pasos
    motor.setCurrentPosition(0); 

    // Setup Red
    setupWiFi();
    mqttClient.setServer(MQTT_SERVER, MQTT_PORT);
    mqttClient.setCallback(mqttCallback);

    lcd.clear();
    lcd.setCursor(0, 0);
    lcd.print("Listo!");
}

// ==========================================
// MAIN LOOP
// ==========================================
void loop() {
    if (!mqttClient.connected()) {
        reconnectMQTT();
    }
    mqttClient.loop();

    // Actualiza el motor de forma no bloqueante
    motor.run();

    // Chequeo de botón
    handleButton();

    // Actualiza indicadores (Alarma)
    updateAlarm();
}

// ==========================================
// FUNCIONES DE HARDWARE Y ESTADO
// ==========================================

void updateAlarm() {
    if (esperandoConfirmacion) {
        if (millis() - ultimoParpadeo > intervaloAlarma) {
            ultimoParpadeo = millis();
            estadoAlarma = !estadoAlarma;
            digitalWrite(PIN_LED, estadoAlarma ? HIGH : LOW);
            digitalWrite(PIN_BUZZER, estadoAlarma ? HIGH : LOW);
        }
    } else {
        // Asegurar apagar si no está esperando
        digitalWrite(PIN_LED, LOW);
        digitalWrite(PIN_BUZZER, LOW);
        estadoAlarma = false;
    }
}

void handleButton() {
    bool reading = digitalRead(PIN_BOTON);

    if (reading != lastDebounceState) {
        lastDebounceTime = millis();
    }

    if ((millis() - lastDebounceTime) > debounceDelay) {
        if (reading != buttonState) {
            buttonState = reading;
            
            // Si transición a LOW (botón presionado pq es PULLUP)
            if (buttonState == LOW) {
                if (esperandoConfirmacion) {
                    confirmDrugTaken();
                }
            }
        }
    }
    lastDebounceState = reading;
}

void confirmDrugTaken() {
    // 1. Apagar alertas de inmediato
    esperandoConfirmacion = false;
    digitalWrite(PIN_LED, LOW);
    digitalWrite(PIN_BUZZER, LOW);

    // 2. Reportar en LCD
    lcd.clear();
    lcd.setCursor(0, 0);
    lcd.print("Medicamento");
    lcd.setCursor(0, 1);
    lcd.print("Tomado");

    // 3. Publicar MQTT confirmation
    // JSON: {"compartimiento": <id>, "status": "ok"}
    String payload = "{\"compartimiento\": " + String(compartimientoActivo) + ", \"status\": \"ok\"}";
    mqttClient.publish("esp32/confirmacion", payload.c_str());
    Serial.println("Confirmación publicada: " + payload);
}

void goToCompartment(int id) {
    if (id < 1 || id > 8) return;
    
    // Cálculo: Cada comp está a 512 pasos del anterior
    // Si queremos el compartimiento 1, es pos = (1-1)*512 = 0
    // Si queremos el compartimiento 8, es pos = (8-1)*512 = 3584
    long targetSteps = (id - 1) * 512;
    motor.moveTo(targetSteps);
    posicionActual = id;
    compartimientoActivo = id;
}

// ==========================================
// FUNCIONES DE RED (WIFI / MQTT)
// ==========================================

void setupWiFi() {
    delay(10);
    Serial.println();
    Serial.print("Conectando a ");
    Serial.println(WIFI_SSID);

    WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

    while (WiFi.status() != WL_CONNECTED) {
        delay(500);
        Serial.print(".");
    }

    Serial.println("\nWiFi conectado");
    Serial.print("IP: ");
    Serial.println(WiFi.localIP());
}

void reconnectMQTT() {
    // Intenta conectar en un ciclo (ojo, es bloqueante en la reconexión inicial si falla)
    // Para entornos reales donde la red es inestable es mejor usar millis() tmb aquí.
    while (!mqttClient.connected()) {
        Serial.print("Intentando conexión MQTT...");
        if (mqttClient.connect(MQTT_CLIENT_ID)) {
            Serial.println("conectado");
            // Suscripciones
            mqttClient.subscribe("esp32/cargar/+");
            mqttClient.subscribe("esp32/mover/+");
        } else {
            Serial.print("falló, rc=");
            Serial.print(mqttClient.state());
            Serial.println(" intentando en 5 segundos");
            delay(5000);
        }
    }
}

void mqttCallback(char* topic, byte* payload, unsigned int length) {
    String topicStr = String(topic);
    
    // Convertir Payload a String (temporal para logging si hace falta)
    String message = "";
    for (unsigned int i = 0; i < length; i++) {
        message += (char)payload[i];
    }
    
    Serial.print("Mensaje recibido: ");
    Serial.print(topicStr);
    Serial.print(" -> ");
    Serial.println(message);

    // Analizar Tópico para extraer comando y/o compartimiento
    // Formato: esp32/cargar/<id> o esp32/mover/<id>
    
    // esp32/cargar/ -> longitud de 13
    if (topicStr.startsWith("esp32/cargar/")) {
        int id = topicStr.substring(13).toInt();
        if (id >= 1 && id <= 8) {
            goToCompartment(id);
            lcd.clear();
            lcd.setCursor(0, 0);
            lcd.print("Cargando: Comp");
            lcd.setCursor(0, 1);
            lcd.print(id);
        }
    }
    // esp32/mover/ -> longitud de 12
    else if (topicStr.startsWith("esp32/mover/")) {
        int id = topicStr.substring(12).toInt();
        if (id >= 1 && id <= 8) {
            goToCompartment(id);
            lcd.clear();
            lcd.setCursor(0, 0);
            lcd.print("HORA DE MEDICINA");
            lcd.setCursor(0, 1);
            lcd.print("Presione Boton  ");
            
            // Activa alerta para que el bucle principal lo gestione
            esperandoConfirmacion = true;
        }
    }
}
