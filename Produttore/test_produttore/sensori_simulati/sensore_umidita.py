import random
import threading
import time

import requests

import costanti_produttore

# Endpoint del server FastAPI
ENDPOINT_MISURAZIONE = "http://localhost:8000/misurazioni"
ENDPOINT_SENSORE = "http://localhost:8000/sensori"

def simula_sensore_umidita(id_sensore: str, descrizione: str, ritardo_iniziale: float = 0, ripetizioni: int = 300, intervallo: float = 1.0):
    """
    Simula un sensore di umidità che invia dati periodicamente al fog node.
    """
    time.sleep(ritardo_iniziale)

    # Registrazione del sensore
    try:
        response = requests.post(ENDPOINT_SENSORE, json={"id_sensore": id_sensore.upper(), "descrizione": descrizione})
        response.raise_for_status()
        print(f"[OK] Sensore registrato: {id_sensore}")
    except requests.RequestException as e:
        print(f"[ERRORE] Registrazione sensore {id_sensore}: {e}")

    # Invio delle misurazioni
    for i in range(ripetizioni):
        dati = {
            "id_sensore": id_sensore.upper(),
            "tipo": costanti_produttore.TIPO_SENSORE_UMIDITA,
            "valore": round(random.uniform(30.0, 90.0), 2)  # Umidità tra 30% e 90%
        }
        try:
            response = requests.post(ENDPOINT_MISURAZIONE, json=dati)
            response.raise_for_status()
            print(f"[OK] {id_sensore}: misurazione {i+1} inviata")
        except requests.RequestException as e:
            print(f"[ERRORE] Invio misurazione {id_sensore}: {e}")

        time.sleep(intervallo)

# Avvia 60 sensori di umidità in parallelo usando thread
sensori_umidita = [
    ("HUM001", "Umidità A", 0),
    ("HUM002", "Umidità B", 1),
    ("HUM003", "Umidità C", 2),
    ("HUM004", "Umidità D", 3),
    ("HUM005", "Umidità E", 4),
    ("HUM006", "Umidità F", 5),
    ("HUM007", "Umidità G", 6),
    ("HUM008", "Umidità H", 7),
    ("HUM009", "Umidità I", 8),
    ("HUM010", "Umidità J", 9),
    ("HUM011", "Umidità K", 10),
    ("HUM012", "Umidità L", 11),
    ("HUM013", "Umidità M", 12),
    ("HUM014", "Umidità N", 13),
    ("HUM015", "Umidità O", 14),
    ("HUM016", "Umidità P", 15),
    ("HUM017", "Umidità Q", 16),
    ("HUM018", "Umidità R", 17),
    ("HUM019", "Umidità S", 18),
    ("HUM020", "Umidità T", 19),
    ("HUM021", "Umidità U", 20),
    ("HUM022", "Umidità V", 21),
    ("HUM023", "Umidità W", 22),
    ("HUM024", "Umidità X", 23),
    ("HUM025", "Umidità Y", 24),
    ("HUM026", "Umidità Z", 25),
    ("HUM027", "Umidità AA", 26),
    ("HUM028", "Umidità AB", 27),
    ("HUM029", "Umidità AC", 28),
    ("HUM030", "Umidità AD", 29),
    ("HUM031", "Umidità AE", 30),
    ("HUM032", "Umidità AF", 31),
    ("HUM033", "Umidità AG", 32),
    ("HUM034", "Umidità AH", 33),
    ("HUM035", "Umidità AI", 34),
    ("HUM036", "Umidità AJ", 35),
    ("HUM037", "Umidità AK", 36),
    ("HUM038", "Umidità AL", 37),
    ("HUM039", "Umidità AM", 38),
    ("HUM040", "Umidità AN", 39),
    ("HUM041", "Umidità AO", 40),
    ("HUM042", "Umidità AP", 41),
    ("HUM043", "Umidità AQ", 42),
    ("HUM044", "Umidità AR", 43),
    ("HUM045", "Umidità AS", 44),
    ("HUM046", "Umidità AT", 45),
    ("HUM047", "Umidità AU", 46),
    ("HUM048", "Umidità AV", 47),
    ("HUM049", "Umidità AW", 48),
    ("HUM050", "Umidità AX", 49),
    ("HUM051", "Umidità AY", 50),
    ("HUM052", "Umidità AZ", 51),
    ("HUM053", "Umidità BA", 52),
    ("HUM054", "Umidità BB", 53),
    ("HUM055", "Umidità BC", 54),
    ("HUM056", "Umidità BD", 55),
    ("HUM057", "Umidità BE", 56),
    ("HUM058", "Umidità BF", 57),
    ("HUM059", "Umidità BG", 58),
    ("HUM060", "Umidità BH", 59),
]

# Avvia ogni sensore in un thread separato
for id_sensore, descrizione, ritardo in sensori_umidita:
    threading.Thread(target=simula_sensore_umidita, args=(id_sensore, descrizione, ritardo)).start()
