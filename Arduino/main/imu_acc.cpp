#include "imu_acc.h"
#include "utils.h"
#include "network.h"
#include <Arduino_LSM6DS3.h>

const int N_ACC = 5;
static float bufX[N_ACC] = {0}, bufY[N_ACC] = {0}, bufZ[N_ACC] = {0};
static int indexBufAcc = 0, countBufAcc = 0;
static unsigned long timerAcc = 0;

// Ultimi valori inviati
static float lastXAcc = -9999, lastYAcc = -9999, lastZAcc = -9999;
const float SOGLIA_ACC = 0.05; // m/s² differenza minima

void setupIMUAccelerometro() {
  if (!IMU.begin()) {
    Serial.println("[ERRORE] IMU non trovata!");
    while (1);
  }
}

void gestisciAccelerometro(unsigned long periodo, const char* idSensore) {
  unsigned long now = millis();
  if (now - timerAcc >= periodo) {
    timerAcc = now;

    float ax, ay, az;
    if (IMU.readAcceleration(ax, ay, az)) {
      bufX[indexBufAcc] = ax;
      bufY[indexBufAcc] = ay;
      bufZ[indexBufAcc] = az;
      indexBufAcc = (indexBufAcc + 1) % N_ACC;
      if (countBufAcc < N_ACC) countBufAcc++;

      float meanX = mediaFloat(bufX, countBufAcc);
      float meanY = mediaFloat(bufY, countBufAcc);
      float meanZ = mediaFloat(bufZ, countBufAcc);

      if (fabs(meanX - lastXAcc) > SOGLIA_ACC ||
          fabs(meanY - lastYAcc) > SOGLIA_ACC ||
          fabs(meanZ - lastZAcc) > SOGLIA_ACC) {
        lastXAcc = meanX;
        lastYAcc = meanY;
        lastZAcc = meanZ;

       String payload = String("{\"id_sensore\":\"") + idSensore +
                 "\",\"tipo\":\"accelerometro\",\"x\":" + String(meanX, 3) +
                 ",\"y\":" + String(meanY, 3) +
                 ",\"z\":" + String(meanZ, 3) + "}";

        inviaMisurazione(payload.c_str());
      }
    }
  }
}
