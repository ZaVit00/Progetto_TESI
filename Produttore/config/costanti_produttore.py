# =========================
# COSTANTI DI CONFIGURAZIONE
# =========================
import os
from dotenv import load_dotenv
from enum import Enum

load_dotenv()

# -------------------------
# Chiavi API e credenziali
# -------------------------

# Chiave API per autenticare il nodo produttore verso il cloud provider.
API_KEY_PRODUTTORE = os.getenv("API_KEY_PRODUTTORE")

# Credenziali AWS per l'accesso al bucket Filebase (compatibile con S3).
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")

# -------------------------
# Configurazione blockchain
# -------------------------
# Chiave privata usata per firmare le transazioni sulla blockchain locale (es. Ganache).
PRIVATE_KEY_BLOCKCHAIN = os.getenv("PRIVATE_KEY_BLOCKCHAIN")

# Indirizzo pubblico dell’account Ethereum usato dal nodo produttore.
ACCOUNT_ADDRESS_BLOCKCHAIN = os.getenv("ACCOUNT_ADDRESS_BLOCKCHAIN")

# =========================
# COSTANTI DI ERRORE
# =========================

# Identificatori di errore durante le fasi di invio ed elaborazione batch.
ERRORE_IPFS = "ERRORE_IPFS"             # Errore nel caricamento file su IPFS
ERRORE_BLOCKCHAIN = "ERRORE_BLOCKCHAIN" # Errore nella scrittura su blockchain
ERRORE_HTTP = "ERRORE_HTTP"             # Errore di comunicazione con endpoint HTTP

# =========================
# SOGLIA PER COMPLETAMENTO BATCH
# =========================

# =========================
# TIPI DI SENSORE
# =========================

# Costanti che rappresentano i principali tipi di sensori supportati dal sistema.
TIPO_SENSORE_JOYSTICK: str = "JOYSTICK"
TIPO_SENSORE_TEMPERATURA: str = "TEMPERATURA"
TIPO_SENSORE_UMIDITA: str = "UMIDITA"

class TipoSensore(str, Enum):
    JOYSTICK = TIPO_SENSORE_JOYSTICK
    TEMPERATURA = TIPO_SENSORE_TEMPERATURA
    UMIDITA = TIPO_SENSORE_UMIDITA

# =========================
# ENDPOINT CLOUD PROVIDER
# =========================

# URL degli endpoint REST esposti dal cloud provider per ricevere:
# - i metadati dei sensori
# - i batch di misurazioni aggregati
ENDPOINT_CLOUD_SENSORI = "http://localhost:8080/sensori"
ENDPOINT_CLOUD_BATCH = "http://localhost:8080/batch"

# =========================
# IPFS (FILEBASE)
# =========================

# Nome del bucket (su Filebase o compatibile S3) dove vengono salvati i Merkle Path JSON.
BUCKET_MERKLE_PATH = "merkle-path-batch"
ENDPOINT_S3_FILEBASE = "https://s3.filebase.com"

# =========================
# CONFIGURAZIONE DB SQLITE
# =========================

# Percorso assoluto del file SQLite che contiene i dati locali del fog node.
# Il file si trova nella root del progetto (due livelli sopra questo script).
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DBPATH = os.path.join(BASE_DIR, "dati_fog_node.sqlite")

# =========================
# VALIDAZIONE ID SENSORE
# =========================

# Mappatura prefisso → tipo sensore, utilizzata per dedurre automaticamente
# il tipo sensore dall'ID durante la registrazione.
MAPPING_PREFISSO_TIPO_SENSORE = {
    "JOY": "joystick",
    "TEMP": "temperatura",
    "HUM": "umidità",
    "PRESS": "pressione"
}

# Prefissi validi che identificano le principali categorie di sensori.
# Ogni ID sensore deve iniziare con uno di questi prefissi (in lettere maiuscole).
# Esempi: JOY001 → joystick, TEMP042 → temperatura, HUM123 → umidità, PRESS999 → pressione
PREFIX_VALIDI_SENSORE = ("JOY", "TEMP", "HUM", "PRESS")

# Espressione regolare per validare l'ID del sensore.
# La stringa deve:
# - iniziare con uno dei prefissi elencati in PREFIX_VALIDI_SENSORE
# - essere seguita da esattamente tre cifre numeriche (0–9)
# Esempi validi: JOY001, TEMP123, HUM045, PRESS999
REGEX_ID_SENSORE = r"(" + "|".join(PREFIX_VALIDI_SENSORE) + r")\d{3}"

# COSTANTI BATCH
# K_BATCH_SCALING Costante moltiplicativa per scalare la dimensione del batch
# serve per aumentare la dimensione del batch in modo artificiale

K_BATCH_SCALING = 32
FATTORE_SCALAMENTO_FREQUENZA = 16    # aumenta l'esponente prima di calcolare il batch
SOGLIA_BATCH_MINIMA = 127            # fallback (es. 2^7 - 1)

