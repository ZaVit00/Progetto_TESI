#include "utils.h"

float mediaInt(int buf[], int count) {
  float sum = 0;
  for (int i = 0; i < count; i++) sum += buf[i];
  return sum / count;
}

// Converte un periodo in ms in frequenza (Hz)
float calcolaFrequenzaHz(unsigned long periodoMs) {
  if (periodoMs == 0) return 0.0;  // evita divisione per 0
  return 1000.0 / (float)periodoMs;
}

float mediaFloat(float buf[], int count) {
  float sum = 0;
  for (int i = 0; i < count; i++) sum += buf[i];
  return sum / count;
}

