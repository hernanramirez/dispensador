// esp32code/config.h
#ifndef CONFIG_H
#define CONFIG_H

// ==========================================
// CONFIGURACIÓN DE RED Y MQTT
// ==========================================
#define WIFI_SSID       "TU_WIFI_SSID"
#define WIFI_PASSWORD   "TU_WIFI_PASSWORD"

#define MQTT_SERVER     "TU_MQTT_BROKER_IP" // ej: "192.168.1.100" o IP de tu server
#define MQTT_PORT       1883
#define MQTT_CLIENT_ID  "esp32_dispensador_01" // O idealmente la MAC para que sea único

// ==========================================
// MAPEO DE PINES (ESP32)
// ==========================================

// Motor a Pasos 28BYJ-48 (ULN2003)
#define PIN_IN1 19
#define PIN_IN2 18
#define PIN_IN3 5
#define PIN_IN4 17

// Display LCD I2C 1602 (usa pines estandar I2C en ESP32: SDA=21, SCL=22)
// No es necesario definirlos explícitamente si se usan los default, 
// pero recuerda conectar a esos pines.

// Botón e Indicadores
#define PIN_BOTON   4   // Pin para el botón físico (usar pulldown/pullup, aquí asumiremos PULLUP)
#define PIN_LED     2   // Pin para el LED indicador (puede ser el LED integrado en la placa)
#define PIN_BUZZER  15  // Pin para el Buzzer

#endif // CONFIG_H
