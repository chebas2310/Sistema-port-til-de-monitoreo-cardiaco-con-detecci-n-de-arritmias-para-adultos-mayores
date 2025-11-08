#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>
#include <MAX30105.h>
#include <spo2_algorithm.h>

#define SCREEN_WIDTH 128
#define SCREEN_HEIGHT 64
#define OLED_RESET    -1
Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, OLED_RESET);

// Sensor MAX30102
MAX30105 particleSensor;

// ✅ PINES ESP32
const int ecgPin = 36;        // GPIO 36 - ADC1_CH0
const int loPlusPin = 5;      // GPIO 5  
const int loMinusPin = 4;     // GPIO 4
const int buzzerPin = 2;      // GPIO 2

int rawECG = 0;
int bpm = 0;
int spo2 = 0;
bool alarmActive = false;
const int BPM_LOW_LIMIT = 60;
const int BPM_HIGH_LIMIT = 100;

// Variables para SpO2
bool spo2Available = false;
unsigned long lastSpO2Read = 0;
const int SPO2_READ_INTERVAL = 1000;

void setup() {
  pinMode(loPlusPin, INPUT);
  pinMode(loMinusPin, INPUT);
  pinMode(buzzerPin, OUTPUT);
  
  Serial.begin(115200);
  
  // Inicializar I2C (ESP32 usa pines 21/22 por defecto)
  Wire.begin();
  
  // Inicializar MAX30102
  if (!particleSensor.begin(Wire, I2C_SPEED_FAST)) {
    spo2Available = false;
  } else {
    // Configurar MAX30102
    byte ledBrightness = 0x1F;
    byte sampleAverage = 4;
    byte ledMode = 2;
    int sampleRate = 100;
    int pulseWidth = 411;
    int adcRange = 4096;
    
    particleSensor.setup(ledBrightness, sampleAverage, ledMode, sampleRate, pulseWidth, adcRange);
    spo2Available = true;
  }
  
  // Inicializar OLED
  if(!display.begin(SSD1306_SWITCHCAPVCC, 0x3C)) {
    while(1);
  }
  
  display.clearDisplay();
  display.setTextColor(SSD1306_WHITE);
  display.setTextSize(1);
  display.setCursor(0, 0);
  display.println("ESP32 - ECG + SpO2");
  display.println("Esperando Python...");
  display.display();
  
  delay(2000);
}

void loop() {
  // Leer ECG (ESP32 ADC: 0-4095)
  rawECG = analogRead(ecgPin);
  
  // Escalar a 0-1023 para compatibilidad con Python
  int scaledECG = map(rawECG, 0, 4095, 0, 1023);
  Serial.println(scaledECG);
  
  // Leer SpO2
  if (spo2Available && millis() - lastSpO2Read > SPO2_READ_INTERVAL) {
    readSpO2();
    lastSpO2Read = millis();
  }
  
  // Recibir BPM desde Python
  if (Serial.available() > 0) {
    String received = Serial.readStringUntil('\n');
    received.trim();
    
    if (received.length() > 0) {
      bpm = received.toInt();
      controlAlarm();
      updateOLED();
    }
  }
  
  delay(20); // 50 Hz
}

void readSpO2() {
  long irValue = particleSensor.getIR();
  
  if (irValue > 50000) {
    // Simular SpO2 (en sistema real usar algoritmo completo)
    spo2 = 96 + random(0, 4);
  } else {
    spo2 = 0; // No hay dedo
  }
}

void controlAlarm() {
  bool spo2Alarm = (spo2 > 0 && spo2 < 95);
  
  if((bpm > BPM_HIGH_LIMIT && bpm < 200) || spo2Alarm) {
    if(!alarmActive) alarmActive = true;
    
    if(spo2Alarm) {
      // Alarma SpO2 bajo
      if(millis() % 500 < 250) {
        tone(buzzerPin, 1200);
      } else {
        noTone(buzzerPin);
      }
    } else {
      // Alarma taquicardia
      tone(buzzerPin, 1000);
    }
  } else if(bpm < BPM_LOW_LIMIT && bpm > 30) {
    if(!alarmActive) alarmActive = true;
    // Alarma bradicardia
    if(millis() % 1000 < 500) {
      tone(buzzerPin, 800);
    } else {
      noTone(buzzerPin);
    }
  } else {
    if(alarmActive) {
      alarmActive = false;
      noTone(buzzerPin);
    }
  }
}

void updateOLED() {
  display.clearDisplay();
  
  // BPM desde Python
  display.setTextSize(2);
  display.setCursor(0, 0);
  display.print("BPM:");
  display.setTextSize(2);
  display.setCursor(70, 0);
  if(bpm > 0) {
    if(bpm < 100) display.print(" ");
    display.println(bpm);
  } else {
    display.println("--");
  }
  
  // SpO2 desde MAX30102
  display.setTextSize(2);
  display.setCursor(0, 25);
  display.print("SpO2:");
  display.setTextSize(2);
  display.setCursor(70, 25);
  if(spo2 > 0) {
    if(spo2 < 100) display.print(" ");
    display.print(spo2);
    display.print("%");
  } else {
    display.print("--%");
  }
  
  // Estado
  display.setTextSize(1);
  display.setCursor(0, 50);
  if(alarmActive) {
    display.print("ALARMA ACTIVA");
  } else if(bpm > 0 && spo2 > 0) {
    display.print("NORMAL");
  } else {
    display.print("ESPERANDO...");
  }
  
  display.display();
}