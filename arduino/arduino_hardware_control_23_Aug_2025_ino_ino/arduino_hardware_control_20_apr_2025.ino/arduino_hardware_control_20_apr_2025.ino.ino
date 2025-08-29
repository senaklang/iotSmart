#include <DHT.h>
#include <Adafruit_Sensor.h>

const int LED_COUNT = 10;
const int LED_PINS[LED_COUNT] = {13, 52, 51, 50, 49, 48, 47, 46, 45, 44};
const int DHTPIN = 23;  // DHT22 connected to pin 23
const int DHTTYPE = DHT22;

DHT dht(DHTPIN, DHTTYPE);

void setupLEDs() {
  for (int i = 0; i < LED_COUNT; i++) {
    pinMode(LED_PINS[i], OUTPUT);
  }
}

void setLED(int index, bool state) {
  if (index >= 0 && index < LED_COUNT) {
    digitalWrite(LED_PINS[index], state ? HIGH : LOW);
  }
}

void setAllLEDs(bool state) {
  for (int i = 0; i < LED_COUNT; i++) {
    digitalWrite(LED_PINS[i], state ? HIGH : LOW);
  }
}

void setup() {
  setupLEDs();
  dht.begin();
  Serial.begin(115200);
}

void loop() {
  // Read DHT22 sensor every 2 seconds
  static unsigned long lastReadTime = 0;
  // ในส่วน loop() ของ Arduino
  if (millis() - lastReadTime >= 2000) {
    lastReadTime = millis();
    
    float humidity = dht.readHumidity();
    float temperature = dht.readTemperature();
    
    if (!isnan(humidity) && !isnan(temperature)) {
      Serial.print("{\"air_temp\":");
      Serial.print(temperature);
      Serial.print(",\"humidity\":");
      Serial.print(humidity);
      Serial.println("}");
    } else {
      Serial.println("{\"error\":\"DHT read failed\"}");
    }
    Serial.flush(); // รอให้ข้อมูลส่งเสร็จก่อนดำเนินการต่อ
  }

  if (Serial.available() > 0) {
    String message = Serial.readStringUntil('\n');
    message.trim();
    
    if (message.startsWith("on_position")) {
      int ledIndex = message.substring(11).toInt();
      setLED(ledIndex, true);
    }
    else if (message.startsWith("off_position")) {
      int ledIndex = message.substring(12).toInt();
      setLED(ledIndex, false);
    }
    else if (message == "on_all") {
      setAllLEDs(true);
    }
    else if (message == "off_all") {
      setAllLEDs(false);
    }
  }
}