import random
import time
import requests

# Configurazione
ID_SENSORE = "temp001"
ENDPOINT_MISURAZIONE = "http://localhost:8000/misurazioni"
ENDPOINT_SENSORE = "http://localhost:8000/sensori"
INTERVALLO = 1  # secondi
RIPETIZIONI = 74  # misurazioni da inviare

# Invio dati di registrazione del sensore
try:
    dati_inviati = {
        "id_sensore": ID_SENSORE,
        "descrizione": "Sensore di temperatura simulato"
    }
    response = requests.post(ENDPOINT_SENSORE, json=dati_inviati)
    response.raise_for_status()
    risultato = response.json()
    print(f"[OK] Inviati dati del sensore: {dati_inviati}\n")
    print(f"[RISPOSTA SERVER]: {risultato}\n")
except requests.RequestException as e:
    print(f"[ERRORE REGISTRAZIONE] {e}")

# Ciclo di invio delle misurazioni
for i in range(RIPETIZIONI):
    # Dato fittizio di temperatura tra 18 e 30 gradi
    dati = {
        "id_sensore": ID_SENSORE,
        "valore": round(random.uniform(18.0, 30.0), 2)
    }

    try:
        response = requests.post(ENDPOINT_MISURAZIONE, json=dati)
        response.raise_for_status()
        risultato = response.json()
        print(f"[OK] Inviata misurazione: {dati}")
        print(f"[RISPOSTA SERVER]: {risultato}\n")
    except requests.RequestException as e:
        print(f"[ERRORE INVIO MISURAZIONE] {e}")

    time.sleep(INTERVALLO)
