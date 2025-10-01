#include "network.h"
#include "joystick.h"
#include "imu_acc.h"
#include "imu_gyro.h"
#include "utils.h"

// --- Config WiFi e server ---
const char* WIFI_SSID = "Wind3 HUB - E8E3AA";
const char* WIFI_PASS = "2910ZaVitDD@@#VZ";
const char* SERVER_IP  = "192.168.1.208";  // IP del tuo PC che funge da server web
const int   SERVER_PORT = 8000;

// --- Periodi di campionamento ---
const unsigned long periodoJoystick = 500;  // ms
const unsigned long periodoAcc = 200;       // ms
const unsigned long periodoGyro = 200;      // ms

void setup() {
  Serial.begin(9600);

  // --- Connessione WiFi ---
  setupNetwork(WIFI_SSID, WIFI_PASS, SERVER_IP, SERVER_PORT);

  // --- Inizializzazione sensori ---
  setupJoystick(A0, A1, 2);
  setupIMUAccelerometro();
  setupIMUGiroscopio();

  // --- Registrazione sensori su endpoint rest (fog_api.py)
  registraSensore("JOY001", "Joystick", calcolaFrequenzaHz(periodoJoystick));
  registraSensore("ACC001", "Accelerometro", calcolaFrequenzaHz(periodoAcc));
  registraSensore("GYR001", "Giroscopio", calcolaFrequenzaHz(periodoGyro));

  delay(10000);
  Serial.print("dopo la pausa");

  // Aspetta 10 secondi per essere sicuro che il DB abbia committato le tre transazioni distinte
  // e poi parte il loop
}

void loop() {
  
  // Letture + invio misurazioni
  gestisciJoystick(periodoJoystick, "JOY001");
  gestisciAccelerometro(periodoAcc, "ACC001");
  gestisciGiroscopio(periodoGyro, "GYR001");
}
