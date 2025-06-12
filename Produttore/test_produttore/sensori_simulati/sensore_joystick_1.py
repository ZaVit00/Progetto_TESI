import random
import time
import requests

# Configurazione
ID_SENSORE = "joy001"
ENDPOINT_MISURAZIONE = "http://localhost:8000/misurazioni"
ENDPOINT_SENSORE = "http://localhost:8000/sensori"
INTERVALLO = 1  # secondi
RIPETIZIONI = 50 # misurazioni


""" invio i dati del sensore al server"""
try:
    dati_inviati = {
        "id_sensore": ID_SENSORE,
        "descrizione": "Joystick di test_produttore"
    }
    response = requests.post(ENDPOINT_SENSORE, json=dati_inviati)
    response.raise_for_status()
    risultato = response.json()  # recuperi il payload_richiesta_cloud JSON di payload_richiesta_cloud
    print(f"[OK] Inviati dati del sensore: {dati_inviati}\n")
    print(f"[RISPOSTA SERVER]: {risultato}\n")
except requests.RequestException as e:
    print(f"[ERRORE] {e}")

""" Loop per inviare i dati al server"""
i = 0
while i < RIPETIZIONI:
    # Genera dati fittizi
    dati = {
        "id_sensore": ID_SENSORE,
        "x": round(random.uniform(-1, 1), 2),
        "y": round(random.uniform(-1, 1), 2),
        "pressed": random.choice([True, False])
    }

    # Invia i dati della misurazione_in_ingresso al server
    try:
        response = requests.post(ENDPOINT_MISURAZIONE, json=dati)
        response.raise_for_status()
        risultato = response.json()  # recuperi il payload_richiesta_cloud JSON di payload_richiesta_cloud
        print(f"[OK] Inviati dati misurazione registrata: {dati}\n")
        print(f"[RISPOSTA SERVER]: {risultato}\n")
    except requests.RequestException as e:
        print(f"[ERRORE] {e}")

    time.sleep(INTERVALLO)
    i += 1
