#include <AccelStepper.h>
#include <LiquidCrystal_I2C.h>
#include <PubSubClient.h>
#include <WiFi.h>

// --- Configuración de WiFi y MQTT ---
const char *ssid = "Wokwi-GUEST"; // Red por defecto en Wokwi
const char *password = "";
const char *mqtt_broker = "";
const int mqtt_port = 1883;
const char *mqtt_username = "";
const char *mqtt_password = "";

// Definición de los nuevos tópicos
const char *topic_led_set = "esp32/led/set";
const char *topic_led_status = "esp32/led/status";
const char *topic_motor_status = "esp32/motor/status";
const char *topic_motor_mover = "esp32/motor/mover";

WiFiClient espClient;
PubSubClient client(espClient);

// --- Configuración del LCD ---
// Dirección I2C 0x27, 16 columnas y 2 filas
LiquidCrystal_I2C lcd(0x27, 16, 2);

// --- Configuración del Motor Paso a Paso ---
// Usamos el modo DRIVER (ideal con A4988) para una simulación sin errores en
// Wokwi
#define PIN_STEP 15
#define PIN_DIR 2
AccelStepper stepper(AccelStepper::DRIVER, PIN_STEP, PIN_DIR);

// --- Configuración del LED ---
#define PIN_LED 4
bool estadoLed = false;

long ultimaPosicionMostrada =
    -999; // Variable para evitar que la pantalla parpadee

// Función para conectar al WiFi
void setup_wifi() {
  delay(10);
  Serial.println();
  Serial.print("Conectando a ");
  Serial.println(ssid);

  WiFi.mode(WIFI_STA);
  WiFi.begin(ssid, password);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println("");
  Serial.println("WiFi conectado!");
  Serial.print("IP: ");
  Serial.println(WiFi.localIP());
}

// Función que se ejecuta cuando llega un mensaje MQTT
void callback(char *topic, byte *payload, unsigned int length) {
  Serial.print("Mensaje recibido en el tópico: ");
  Serial.println(topic);

  // Convertimos el payload a un String para evaluarlo fácilmente
  String mensaje = "";
  for (int i = 0; i < length; i++) {
    mensaje += (char)payload[i];
  }

  // Manejo de los diferentes tópicos
  if (strcmp(topic, topic_led_set) == 0) {
    if (mensaje == "ON") {
      digitalWrite(PIN_LED, HIGH);
      estadoLed = true;
      client.publish(topic_led_status, "ON");
      Serial.println("Comando: LED Encendido");
    } else if (mensaje == "OFF") {
      digitalWrite(PIN_LED, LOW);
      estadoLed = false;
      client.publish(topic_led_status, "OFF");
      Serial.println("Comando: LED Apagado");
    }
  } else if (strcmp(topic, topic_led_status) == 0) {
    // Si consultan el estatus, lo reportamos
    client.publish(topic_led_status, estadoLed ? "ON" : "OFF");
  } else if (strcmp(topic, topic_motor_mover) == 0) {
    // Ordenamos al motor que se mueva 25 pasos
    stepper.move(25);
    Serial.println("Comando aceptado: Moviendo 25 pasos...");
  } else if (strcmp(topic, topic_motor_status) == 0) {
    // Si consultan el estatus del motor, enviamos la posición actual
    char msgPos[16];
    sprintf(msgPos, "%ld", stepper.currentPosition());
    client.publish(topic_motor_status, msgPos);
  }
}

// Función para reconectar al broker MQTT si se pierde la conexión
void reconnect() {
  while (!client.connected()) {
    Serial.print("Intentando conexión MQTT...");
    // Crear un ID de cliente aleatorio
    String clientId = "ESP32Client-Wokwi-";
    clientId += String(random(0xffff), HEX);

    // Intentar conectar con usuario y contraseña
    if (client.connect(clientId.c_str(), mqtt_username, mqtt_password)) {
      Serial.println("Conectado al broker!");
      // Nos suscribimos a los tópicos necesarios
      client.subscribe(topic_led_set);
      client.subscribe(topic_led_status);
      client.subscribe(topic_motor_mover);
      client.subscribe(topic_motor_status);
    } else {
      Serial.print("Fallo, rc=");
      Serial.print(client.state());
      Serial.println(" Intentando de nuevo en 5 segundos");
      delay(5000);
    }
  }
}

void setup() {
  Serial.begin(115200);

  // Inicializar el pin del LED
  pinMode(PIN_LED, OUTPUT);
  digitalWrite(PIN_LED, LOW);

  // 1. Inicializar LCD
  lcd.init();
  lcd.backlight();
  lcd.setCursor(0, 0);
  lcd.print("Conectando...");

  // 2. Configurar Motor
  stepper.setMaxSpeed(500.0);     // Velocidad máxima
  stepper.setAcceleration(200.0); // Aceleración para un movimiento suave

  // 3. Conectar a WiFi y configurar MQTT
  setup_wifi();
  client.setServer(mqtt_broker, mqtt_port);
  client.setCallback(callback);

  // Limpiar pantalla al estar listo
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("Sistema Listo!");
}

void loop() {
  // Mantener la conexión MQTT viva
  if (!client.connected()) {
    reconnect();
  }
  client.loop();

  // Esta función debe ejecutarse en cada ciclo de loop.
  // Es la encargada de dar el "paso" físico al motor si le faltan pasos para
  // llegar a la meta.
  stepper.run();

  // Actualizar el display LCD SOLO si la posición ha cambiado
  long posicionActual = stepper.currentPosition();
  if (posicionActual != ultimaPosicionMostrada) {
    lcd.setCursor(0, 1);
    lcd.print("Pos: ");
    lcd.print(posicionActual);
    lcd.print(" pasos   "); // Los espacios extra borran los dígitos sobrantes

    // Publicar automáticamente el nuevo estatus del motor por MQTT
    char msgPos[16];
    sprintf(msgPos, "%ld", posicionActual);
    client.publish(topic_motor_status, msgPos);

    ultimaPosicionMostrada = posicionActual;
  }
}