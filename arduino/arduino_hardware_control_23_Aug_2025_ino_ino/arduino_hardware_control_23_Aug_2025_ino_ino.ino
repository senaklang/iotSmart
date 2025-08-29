#include <DHT.h>
#include <Adafruit_Sensor.h>
#include <avr/wdt.h>  // สำหรับ Watchdog Timer

// Constants
#define LED_COUNT 10
#define DHTPIN 23
#define DHTTYPE DHT22
#define TDS_PIN A0
#define PH_PIN A1
#define SENSOR_READ_INTERVAL 2000

// Globals
const int LED_PINS[LED_COUNT] = {13, 52, 51, 50, 49, 48, 47, 46, 45, 44};
float tdsValue = 0, phValue = 0;
float phOffset = 0.0, calibPh7 = 2.5, calibPh4 = 3.0;
bool ledStates[LED_COUNT] = {false};
DHT dht(DHTPIN, DHTTYPE);

// LED Setup
void setupLEDs() {
  for (int i = 0; i < LED_COUNT; i++) {
    pinMode(LED_PINS[i], OUTPUT);
    digitalWrite(LED_PINS[i], LOW);
  }
}

void setLED(int index, bool state) {
  if (index >= 0 && index < LED_COUNT) {
    digitalWrite(LED_PINS[index], state ? HIGH : LOW);
    ledStates[index] = state;
    Serial.println("\nsuccess");
  }
}

void setAllLEDs(bool state) {
  for (int i = 0; i < LED_COUNT; i++) {
    setLED(i, state);
  }
}

// Sensor Reading
float readTDS() {
  int analogValue = analogRead(TDS_PIN);
  float voltage = analogValue * (5.0 / 1024.0);
  tdsValue = (133.42 * voltage * voltage * voltage
            - 255.86 * voltage * voltage
            + 857.39 * voltage) * 0.5;
  return tdsValue;
}

float readPH() {
  float sum = 0;
  for (int i = 0; i < 10; i++) {
    sum += analogRead(PH_PIN);
    delay(10);
  }
  float voltage = (sum / 10.0) * (5.0 / 1024.0);
  phValue = ((calibPh7 - voltage) * 3.0) / (calibPh7 - calibPh4) + 7.0 + phOffset;
  return phValue;
}

void sendSensorData() {
  float humidity = dht.readHumidity();
  float temperature = dht.readTemperature();
  float tds = readTDS();
  float ph = readPH();

  if (!isnan(humidity) && !isnan(temperature)) {
    Serial.print("Temp:");
    Serial.print(temperature, 1);
    Serial.print("°C, Humidity:");
    Serial.print(humidity, 1);
    Serial.print("%, TDS:");
    Serial.print(tds, 0);
    Serial.print("ppm, PH:");
    Serial.print(ph, 2);
    Serial.println("๐");
  } else {
    Serial.println("ERROR:Failed to read DHT sensor!");
  }
}

// Command Handling
void controlLedPosition(String msg) {
  Serial.print(msg);
  msg.trim();
  if (msg.startsWith("positionon")) {
    setLED(msg.substring(10).toInt(), true);
  } else if (msg.startsWith("positionoff")) {
    setLED(msg.substring(11).toInt(), false);
  }
}

void processCalibrationCommand(String msg) {
  msg.trim();
  if (msg.startsWith("CALIB_PH:7:")) {
    calibPh7 = msg.substring(12).toFloat();
    Serial.print("ACK:CALIB_PH7_SET:");
    Serial.println(calibPh7);
  } else if (msg.startsWith("CALIB_PH:4:")) {
    calibPh4 = msg.substring(12).toFloat();
    Serial.print("ACK:CALIB_PH4_SET:");
    Serial.println(calibPh4);
  } else if (msg.startsWith("SET_PH_OFFSET:")) {
    phOffset = msg.substring(14).toFloat();
    Serial.print("ACK:PH_OFFSET_SET:");
    Serial.println(phOffset);
  }
}

void processSerialCommand(String msg) {
  msg.trim();
  if (msg.equalsIgnoreCase("GET_SENSORS")) {
    sendSensorData();
  } else if (msg.equalsIgnoreCase("ALL:ON")) {
    setAllLEDs(true);
  } else if (msg.equalsIgnoreCase("ALL:OFF")) {
    setAllLEDs(false);
  } else if (msg.startsWith("LED:")) {
    int idx1 = msg.indexOf(':');
    int idx2 = msg.indexOf(':', idx1 + 1);
    int ledIndex = msg.substring(idx1 + 1, idx2).toInt();
    String state = msg.substring(idx2 + 1);
    setLED(ledIndex, state.equalsIgnoreCase("ON"));
  } else if (msg.startsWith("CALIB_")) {
    processCalibrationCommand(msg);
  } else if (msg.equalsIgnoreCase("PING")) {
    Serial.println("PONG");
  } else {
    Serial.print("ERROR:Unknown command: ");
    Serial.println(msg);
  }
}

// Arduino Lifecycle
void setup() {
  Serial.begin(115200);
  //while (!Serial);

  setupLEDs();
  dht.begin();

  pinMode(TDS_PIN, INPUT);
  pinMode(PH_PIN, INPUT);

  wdt_enable(WDTO_8S);  // เปิด watchdog timer ที่ 8 วินาที
}

void loop() {
  wdt_reset();  // รีเซ็ต watchdog ทุกครั้งที่ loop ทำงาน

  static unsigned long lastRead = 0;

  if (millis() - lastRead >= SENSOR_READ_INTERVAL) {
    lastRead = millis();
    sendSensorData();
  }

  if (Serial.available()) {
    String msg = Serial.readStringUntil('\n');
    if (msg.startsWith("positionon") || msg.startsWith("positionoff")) {
      controlLedPosition(msg);
    } else {
      processSerialCommand(msg);
    }
  }
}