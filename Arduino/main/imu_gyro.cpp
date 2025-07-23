#include "imu_gyro.h"
#include "utils.h"
#include "network.h"
#include <Arduino_LSM6DS3.h>

const int N_GYR = 5;
static float bufXGyro[N_GYR] = {0}, bufYGyro[N_GYR] = {0}, bufZGyro[N_GYR] = {0};
static int indexBufGyro = 0, countBufGyro = 0;
static unsigned long timerGyro = 0;

// Ultimi valori inviati
static float lastXGyro = -9999, lastYGyro = -9999, lastZGyro = -9999;
const float SOGLIA_GYR = 1.0; // °/s differenza minima

void setupIMUGiroscopio() {
  if (!IMU.begin()) {
    Serial.println("[ERRORE] IMU non trovata!");
    while (1);
  }
}

void gestisciGiroscopio(unsigned long periodo, const char* idSensore) {
  unsigned long now = millis();
  if (now - timerGyro >= periodo) {
    timerGyro = now;

    float gx, gy, gz;
    if (IMU.readGyroscope(gx, gy, gz)) {
      bufXGyro[indexBufGyro] = gx;
      bufYGyro[indexBufGyro] = gy;
      bufZGyro[indexBufGyro] = gz;
      indexBufGyro = (indexBufGyro + 1) % N_GYR;
      if (countBufGyro < N_GYR) countBufGyro++;

      float meanX = mediaFloat(bufXGyro, countBufGyro);
      float meanY = mediaFloat(bufYGyro, countBufGyro);
      float meanZ = mediaFloat(bufZGyro, countBufGyro);

      if (fabs(meanX - lastXGyro) > SOGLIA_GYR ||
          fabs(meanY - lastYGyro) > SOGLIA_GYR ||
          fabs(meanZ - lastZGyro) > SOGLIA_GYR) {
        lastXGyro = meanX;
        lastYGyro = meanY;
        lastZGyro = meanZ;

        String payload = String("{\"id_sensore\":\"") + idSensore +
                 "\",\"tipo\":\"giroscopio\",\"x\":" + String(meanX, 3) +
                 ",\"y\":" + String(meanY, 3) +
                 ",\"z\":" + String(meanZ, 3) + "}";


        inviaMisurazione(payload.c_str());
      }
    }
  }
}
