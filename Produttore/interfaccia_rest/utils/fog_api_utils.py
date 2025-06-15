import json
import logging
import requests
import costanti_produttore
from database.gestore_db import GestoreDatabase
from merkle_tree import MerkleTree, ProofCompatta
from costruttore_payload import CostruttorePayload
from misurazioni_in_ingresso import MisurazioneInIngresso

# Logger del modulo
logger = logging.getLogger(__name__)


def gestisci_misurazione(id_sensore : str, dati : MisurazioneInIngresso, db : GestoreDatabase):
    """
    db.inserisci_misurazione(id_sensore=id_sensore, dati=dati):
        return True
    return False
    """

def gestisci_batch_completo(id_batch_chiuso: int, db: GestoreDatabase, endpoint_cloud: str) -> None:
    """
    Gestisce l'intero ciclo di elaborazione di un batch completo:
    1. Estrae le misurazioni associate dal DB.
    2. Calcola la Merkle Root e ottiene il merkle path
    3. Salva i merkle path su FILEBASE
    4. Aggiorna la root e i merkle path su database per debug futuri
    5. Costruisce il payload JSON da inviare al cloud e lo salva in DB
    6. Tenta l'invio al cloud del payload. Se l'invio fallisce, il payload rimane
       in DB e viene effettuato un nuovo tentativo a intervalli periodici.
    """
    try:
        dati_query = db.estrai_dati_batch_misurazioni(id_batch_chiuso)
        if not dati_query:
            logger.error(f"Nessun dato trovato per il batch {id_batch_chiuso}")
            return

        payload_iniziale = CostruttorePayload()
        payload_iniziale.estrai_dati_da_query(dati_query)
        try:
            foglie_hash = payload_iniziale.get_foglie_hash()
            merkle_tree = MerkleTree(foglie_hash)
            mappa_id = payload_iniziale.get_id_misurazioni()
            merkle_root = merkle_tree.costruisci_albero(mappa_id=mappa_id)
            debug_stampa_proofs_json(
                proofs=merkle_tree.get_proofs(),
                verbose=True
            )
        except Exception as e:
            messaggio_errore = f"Creazione Merkle Tree fallita: {e}"
            logger.error(messaggio_errore)
            db.imposta_batch_errore_elaborazione(id_batch_chiuso, messaggio_errore,
                                                 tipo_errore=costanti_produttore.ERRORE_MERKLE_INVALIDO)
            return
        try:
            db.aggiorna_merkle_root_batch(id_batch_chiuso, merkle_root)
        except Exception as e:
            messaggio_errore = f"Aggiornamento Merkle Root fallito: {e}"
            logger.error(messaggio_errore)
            return

        try:
            payload_finale = payload_iniziale.costruisci_payload()
            # converte l'oggetto DatiPayload di Pydantic in JSON, con model dump JSON
            # La conversione è utile per il salvataggio in modo chiaro su database del payload
            payload_json = payload_finale.model_dump_json(indent=2)
            db.aggiorna_payload_json_batch(id_batch_chiuso, payload_json)
            logger.info("Payload JSON costruito:")
            logger.debug("\n" + "-"*20 + "\n" + payload_json + "\n" + "-"*20)
        except Exception as e:
            messaggio_errore = f"Costruzione del payload fallita: {e}"
            logger.error(messaggio_errore)
            db.imposta_batch_errore_elaborazione(id_batch_chiuso, messaggio_errore,
                                                 tipo_errore=costanti_produttore.ERRORE_PAYLOAD_INVALIDO)
            return

        try:
            #La struttura dati che deve essere inviata al cloud è un dizionario.
            #Con model_dump estraggo un dizionario da un oggetto pydantic
            payload_dict = payload_finale.model_dump()
            if invia_payload(payload_dict, endpoint_cloud):
                logger.debug(f"Batch {id_batch_chiuso} inviato con successo. In attesa conferma ricezione.")
            else:
                logger.warning(f"Invio del batch {id_batch_chiuso} fallito. I dati resteranno locali.")
        except Exception as e:
            logger.error(f"Invio del batch {id_batch_chiuso} fallito: {e}")

    except Exception as e:
        logger.critical(f"Errore durante l'elaborazione del batch {id_batch_chiuso}: {e}")

def invia_payload(payload_dict: dict, endpoint_cloud: str) -> bool:
    """
    Invia il payload (dizionario) al servizio cloud tramite HTTP POST.
    Ritorna True se la richiesta ha esito positivo (status code 2xx), altrimenti False.
    """
    try:
        response = requests.post(endpoint_cloud, json=payload_dict, timeout=10)
        response.raise_for_status()
        logger.info("Invio del payload al cloud riuscito.")
        return True
    except requests.exceptions.Timeout:
        logger.error("Timeout durante l'invio del payload al cloud.")
    except requests.exceptions.ConnectionError:
        logger.error("Connessione al cloud fallita.")
    except requests.RequestException as e:
        logger.error(f"Invio del payload fallito: {e}")
    return False

def debug_stampa_proofs_json(proofs: dict[int, ProofCompatta], verbose: bool = False) -> None:
    """
    METODO [DEBUG]
    Stampa compatta delle Merkle Proofs in formato JSON leggibile.
    """
    if not verbose:
        return
    json_serializzabile = {
        str(k) if k != 0 else "batch": {
            "d": p.get_direzione(),
            "h": p.get_hash_fratelli()
        }
        for k, p in proofs.items()
    }
    logger.info("📦 MERKLE PROOFS (Formato JSON)")
    separator = "-" * 80
    json_str = json.dumps(json_serializzabile, indent=2)
    logger.debug(f"\n{separator}\n{json_str}\n{separator}")