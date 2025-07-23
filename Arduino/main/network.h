#ifndef NETWORK_H
#define NETWORK_H

void setupNetwork(const char* ssid, const char* password, const char* server, int port);
void registraSensore(const char* id, const char* descrizione, float frequenzaHz);
bool inviaMisurazione(const char* jsonPayload);

#endif
