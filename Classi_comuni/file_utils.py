import gzip
from io import BytesIO
import os
from datetime import datetime
import os
from datetime import datetime

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
    differenze_json: str | None = None  # nuovo parametro opzionale
):
    """
    Salva la verifica nella struttura:
    base_dir/id_batch{id_batch}/GG-MM-YYYY_HH-MM/esito_{esito}_{HH-MM-SS}.json
    Se `differenze_json` è presente, salva anche differenze_{HH-MM-SS}.json
    """
    esito_str = "integro" if esito else "compromesso"

    now = datetime.now()
    cartella_data = now.strftime("%d-%m-%Y_%H-%M")
    timestamp_file = now.strftime("%H-%M-%S")

    cartella_destinazione = os.path.join(base_dir, f"id_batch{id_batch}", cartella_data)
    os.makedirs(cartella_destinazione, exist_ok=True)

    # Salvataggio del file principale
    nome_file_esito = f"esito_{esito_str}_{timestamp_file}.json"
    percorso_file_esito = os.path.join(cartella_destinazione, nome_file_esito)
    salva_file(percorso_file_esito, contenuto_json)

    # Salvataggio differenze, se fornite
    if differenze_json is not None:
        nome_file_diff = f"differenze_{timestamp_file}.json"
        percorso_file_diff = os.path.join(cartella_destinazione, nome_file_diff)
        salva_file(percorso_file_diff, differenze_json)


def salva_file(percorso_file: str, contenuto_json: str):
    """
    Scrive il contenuto in un file già definito. Gestisce le eccezioni.
    """
    try:
        with open(percorso_file, "w", encoding="utf-8") as f:
            f.write(contenuto_json)
    except OSError as e:
        raise OSError(f"Errore nella scrittura del file '{percorso_file}': {e}")
    except Exception as e:
        raise Exception(f"Errore imprevisto durante il salvataggio: {e}")

    #print(f"Verifica salvata in: {percorso_file}") #debug