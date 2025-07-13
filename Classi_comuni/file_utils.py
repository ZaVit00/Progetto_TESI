import gzip
import json
import os
from datetime import datetime
from io import BytesIO
from Classi_comuni.utils import Hashing


def genera_contenuto_gzip(json_string: str) -> bytes:
    """
    Comprimi una stringa JSON in formato GZIP e restituisce i byte compressi.
    """
    buffer = BytesIO()
    with gzip.GzipFile(fileobj=buffer, mode='wb') as gzip_file:
        gzip_file.write(json_string.encode('utf-8'))
    return buffer.getvalue()


def salva_risultato_verifica_su_file(
    id_batch: int,
    contenuto_json: str,
    esito: bool,
    base_dir: str,
    differenze: str | None = None,  # nuovo parametro opzionale
):
    """
    Salva la verifica nella struttura:
    base_dir/id_batch{id_batch}/GG-MM-YYYY_HH-MM/esito_{esito}_{HH-MM-SS}.json
    Se `differenze_json` è presente, salva anche differenze_{HH-MM-SS}.json
    """
    esito_str = "integro" if esito else "compromesso"

    now = datetime.now()
    cartella_data = now.strftime("%d-%m-%Y_%H-%M")
    timestamp_file = now.strftime("%H-%M-%S") # per evitare conflitti tra salvataggi

    cartella_destinazione = os.path.join(base_dir, f"id_batch{id_batch}", cartella_data)
    os.makedirs(cartella_destinazione, exist_ok=True)

    # Salvataggio del file principale
    nome_file_esito = f"esito_{esito_str}_{timestamp_file}.json"
    percorso_file_esito = os.path.join(cartella_destinazione, nome_file_esito)
    salva_file_generico(percorso_file_esito, contenuto_json)

    # Salvataggio differenze, se fornite
    if differenze is not None:
        nome_file_diff = f"differenze_{timestamp_file}.json"
        percorso_file_diff = os.path.join(cartella_destinazione, nome_file_diff)
        salva_file_generico(percorso_file_diff, differenze)


def salva_file_generico(percorso_file: str, contenuto: str):
    """
    Scrive il contenuto in un file già definito. Gestisce le eccezioni.
    """
    try:
        with open(percorso_file, "w", encoding="utf-8") as f:
            f.write(contenuto)
    except OSError as e:
        raise OSError(f"Errore nella scrittura del file '{percorso_file}': {e}")
    except Exception as e:
        raise Exception(f"Errore imprevisto durante il salvataggio: {e}")

    #print(f"Verifica salvata in: {percorso_file}") #debug

def verifica_esistenza_file(percorso_file: str) -> bool:
    """
    Verifica se un file esiste e non è vuoto.
    Restituisce True se il file esiste ed è non vuoto, altrimenti False.
    """

    return os.path.exists(percorso_file) and os.path.getsize(percorso_file) > 0

def carica_file_testuale(percorso_file: str) -> str:
    """
    Carica il contenuto testuale da un file.
    """
    try:
        with open(percorso_file, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        raise FileNotFoundError(f"File non trovato: '{percorso_file}'")
    except Exception as e:
        raise Exception(f"Errore durante la lettura del file '{percorso_file}': {e}")

def carica_json(percorso_file: str) -> dict:
    """
    Carica un file JSON e restituisce un dizionario.
    """
    try:
        with open(percorso_file, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        raise FileNotFoundError(f"File JSON non trovato: '{percorso_file}'")
    except json.JSONDecodeError as e:
        raise Exception(f"Errore nel parsing JSON di '{percorso_file}': {e}")
    except Exception as e:
        raise Exception(f"Errore nella lettura del file JSON '{percorso_file}': {e}")



def genera_nome_file(json_string: str) -> str:
    """
    Genera un nome file compatto e univoco basato solo su hash:
    - Esempio: merkle_path_3ac1b2d9.json
    """
    full_hash = Hashing.calcola_hash(json_string)
    #esrae i primi 8 caratteri hash complessivo
    short_hash = full_hash[:8]
    #.json: indica il tipo di dati (Merkle Path strutturato in formato JSON).
    #.gz: indica che è stato compresso con gzip.
    return f"merkle_path_{short_hash}.json"