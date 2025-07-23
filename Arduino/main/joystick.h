#ifndef JOYSTICK_H
#define JOYSTICK_H

#include <Arduino.h>

void setupJoystick(int pinX, int pinY, int pinSW);
void gestisciJoystick(unsigned long periodo, const char* idSensore);

#endif
