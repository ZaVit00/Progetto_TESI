#include "network.h"
#include <WiFiNINA.h>
#include <ArduinoHttpClient.h>

static WiFiClient wifi;
static HttpClient* client;
static const char* _server;
static int _port;

void setupNetwork(const char* ssid, const char* password, const char* server, int port) {
  _server = server;
  _port = port;
  client = new HttpClient(wifi, _server, _port);

  Serial.print("Connessione a WiFi ");
  Serial.println(ssid);

  while (WiFi.begin(ssid, password) != WL_CONNECTED) {
    Serial.print(".");
    delay(1000);
  }
  Serial.println("\n[OK] Connesso al WiFi!");
  Serial.print("IP Arduino: ");
  Serial.println(WiFi.localIP());
}

void registraSensore(const char* id, const char* descrizione, float frequenzaHz) {
  String payload = String("{\"id_sensore\":\"") + id + "\",\"descrizione\":\"" +
                   descrizione + "\",\"frequenza_hz\":" + String(frequenzaHz, 2) + "}";
  
  client->post("/sensore", "application/json", payload);
  int statusCode = client->responseStatusCode();
  String response = client->responseBody();

  Serial.print("[REGISTRAZIONE] "); Serial.print(id);
  Serial.print(" Status: "); Serial.println(statusCode);
  Serial.print("Response: "); Serial.println(response);

  client->stop();
}

bool inviaMisurazione(const char* jsonPayload) {
  client->post("/misurazione", "application/json", jsonPayload);
  int statusCode = client->responseStatusCode();
  String response = client->responseBody();

  Serial.print("[HTTP] Status: ");
  Serial.println(statusCode);
  Serial.print("[HTTP] Body: ");
  Serial.println(response);

  client->stop();
  return (statusCode >= 200 && statusCode < 300);
}
