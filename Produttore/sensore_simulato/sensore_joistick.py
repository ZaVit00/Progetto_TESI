import random
import time
import requests

# Configurazione
ID_SENSORE = "joy001"
ENDPOINT = "http://localhost:8000/misurazioni"
INTERVALLO = 5  # secondi
RIPETIZIONI = 40  #

# Loop principale
i = 0
while i < RIPETIZIONI:
    # Genera dati fittizi
    dati = {
        "id_sensore": ID_SENSORE,
        "x": round(random.uniform(-1, 1), 2),
        "y": round(random.uniform(-1, 1), 2),
        "pressed": random.choice([True, False])
    }

    # Invia i dati
    try:
        response = requests.post(ENDPOINT, json=dati)
        response.raise_for_status()
        risultato = response.json()  # recuperi il payload JSON di risposta
        print(f"[OK] Inviati: {dati}\n")
        print(f"[RISPOSTA]: {risultato}\n")
    except requests.RequestException as e:
        print(f"[ERRORE] {e}")

    time.sleep(INTERVALLO)
    i += 1
