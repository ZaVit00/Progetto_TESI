#include "joystick.h"
#include "utils.h"
#include "network.h"


static int _pinX;
static int _pinY;
static int _pinSW;

const int N = 5;
static int bufX[N] = {0}, bufY[N] = {0};
static int indexBuf = 0, countBuf = 0;
static unsigned long _timer = 0;

// Ultimi valori inviati
static float lastX = -9999;
static float lastY = -9999;
const int SOGLIA = 10;

// Debounce pulsante
static bool lastPressedState = false;
static bool stablePressedState = false;
static unsigned long lastDebounceTime = 0;
const unsigned long debounceDelay = 50;

void setupJoystick(int pinX, int pinY, int pinSW) {
  _pinX = pinX;
  _pinY = pinY;
  _pinSW = pinSW;
  pinMode(_pinSW, INPUT_PULLUP);
}

void gestisciJoystick(unsigned long periodo, const char* idSensore) {
  unsigned long now = millis();
  if (now - _timer >= periodo) {
    _timer = now;

    int x = analogRead(_pinX);
    int y = analogRead(_pinY);

    // --- Debounce pulsante ---
    bool rawPressed = (digitalRead(_pinSW) == LOW);
    if (rawPressed != lastPressedState) {
      lastDebounceTime = now;
    }
    if ((now - lastDebounceTime) > debounceDelay) {
      stablePressedState = rawPressed;
    }
    lastPressedState = rawPressed;

    // Salva nei buffer per media mobile
    bufX[indexBuf] = x;
    bufY[indexBuf] = y;
    indexBuf = (indexBuf + 1) % N;
    if (countBuf < N) countBuf++;

    float meanX = mediaInt(bufX, countBuf);
    float meanY = mediaInt(bufY, countBuf);

    // Controlla se è cambiato abbastanza
    if (fabs(meanX - lastX) > SOGLIA || fabs(meanY - lastY) > SOGLIA || stablePressedState) {
      lastX = meanX;
      lastY = meanY;
      String payload = String("{\"id_sensore\":\"") + idSensore +
                 "\",\"tipo\":\"joystick\",\"x\":" + String(meanX, 3) +
                 ",\"y\":" + String(meanY, 3) +
                 ",\"pressed\":" + (stablePressedState ? "true" : "false") + "}";


      Serial.print("["); Serial.print(idSensore); Serial.print("] ");
      Serial.print("X="); Serial.print(meanX);
      Serial.print(" Y="); Serial.print(meanY);
      Serial.print(" Pressed="); Serial.println(stablePressedState ? "true" : "false");

      // invio della misurazione all'endpoint locale (fog api)
      inviaMisurazione(payload.c_str());      
    }
  }
}
