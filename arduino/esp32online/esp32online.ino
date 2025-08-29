#include <DHT.h>
#include <Adafruit_Sensor.h>
#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h> 

#define LED_COUNT 10
#define DHTPIN 23
#define DHTTYPE DHT22
#define TDS_PIN 32
#define PH_PIN 33
#define SENSOR_READ_INTERVAL 2000

const int LED_PINS[LED_COUNT] = {2, 4, 5, 18, 19, 21, 22, 23, 25, 26};
bool ledStates[LED_COUNT] = {false};
DHT dht(DHTPIN, DHTTYPE);

const char* ssid = "Ang Bo";
const char* password = "1000000001";

// 🔹 endpoint ควรเป็น API ที่เราเขียน Flask ไว้
const char* serverUrl = "https://iotsmart.onrender.com/hardware/lamp/lampcontrol";

void setupLEDs() {
  for (int i = 0; i < LED_COUNT; i++) {
    pinMode(LED_PINS[i], OUTPUT);
    digitalWrite(LED_PINS[i], LOW);
  }
}

void controlLED(int channel, String action) {
  if (channel < 0 || channel >= LED_COUNT) return;
  if (action == "on") {
    digitalWrite(LED_PINS[channel], HIGH);
    ledStates[channel] = true;
  } else if (action == "off") {
    digitalWrite(LED_PINS[channel], LOW);
    ledStates[channel] = false;
  }
}

void setup() {
  Serial.begin(115200);
  setupLEDs();
  dht.begin();

  Serial.printf("Connecting to %s ...\n", ssid);
  WiFi.begin(ssid, password);

  int retry = 0;
  while (WiFi.status() != WL_CONNECTED) {
    delay(1000);
    Serial.print(".");
    retry++;
    if (retry > 20) { // รอ 20 วินาที
      Serial.println("Failed to connect to WiFi");
      return;
    }
  }

  Serial.println("\nWiFi connected!");
  Serial.print("IP address: ");
  Serial.println(WiFi.localIP());
}


void loop() {
  if (WiFi.status() == WL_CONNECTED) {
    HTTPClient http;
    http.begin(serverUrl);

    int httpCode = http.GET();
    if (httpCode == 200) {
      String payload = http.getString();
      Serial.println("Server Response: " + payload);

      // 🔹 parse JSON
      StaticJsonDocument<256> doc;
      DeserializationError error = deserializeJson(doc, payload);
      if (!error) {
        const char* device_id = doc["device_id"];
        const char* action = doc["action"];
        int channel = doc["channel"].as<int>();

        Serial.printf("Device:%s Action:%s Channel:%d\n", device_id, action, channel);

        // 🔹 สั่งงาน LED
        controlLED(channel, action);
      } else {
        Serial.println("JSON parse failed!");
      }
    }
    http.end();
  }

  delay(5000);  // ดึงคำสั่งใหม่ทุก 5 วิ
}
