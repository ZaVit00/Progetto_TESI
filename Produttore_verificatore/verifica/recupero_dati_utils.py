import json
import logging
from typing import List
from Produttore.database.gestore_db import GestoreDatabase
from modelli_dati import DatiBatch
from modelli_dati import DatiMisurazione, DatiSensore, DatiMisurazioneSensore

logger = logging.getLogger(__name__)

def carica_payload_json(gestore_db : GestoreDatabase, id_batch: int) -> dict:
    """
    Recupera il campo `payload_json` dal database e lo restituisce come dizionario.
    Usa il metodo `ottieni_payload_batch()` del GestoreDatabase.
    """
    raw_payload = gestore_db.ottieni_payload_batch(id_batch)

    if not raw_payload:
        raise ValueError(f"Nessun payload JSON disponibile per il batch {id_batch}")

    try:
        return json.loads(raw_payload)
    except json.JSONDecodeError as e:
        logger.error(f"[DECODIFICA JSON] Batch {id_batch}: errore → {e}")
        raise ValueError("Errore nel parsing del payload JSON")

def estrai_lista_id_sensori_dal_payload(payload: dict) -> list[str]:
    """
    Estrae tutti gli `id_sensore` dalle misurazioni contenute nel payload JSON
    e restituisce una lista senza duplicati.
    """
    misurazioni = payload.get("misurazioni", [])
    id_sensori = {str(m.get("id_sensore")) for m in misurazioni}
    return list(id_sensori)

def estrai_dati_sensori_locali(lista_id_sensori: List[str], gestore_db: GestoreDatabase) -> List[DatiSensore]:
    """
    Dato un elenco di ID sensori, restituisce la lista degli oggetti DatiSensore corrispondenti.
    Solleva ValueError se almeno uno dei sensori non è presente nel database.
    """
    risultato = []
    for id_sensore in lista_id_sensori:
        record : DatiSensore = gestore_db.ottieni_dati_sensore(id_sensore)
        if not record:
            raise ValueError(f"Sensore con ID '{id_sensore}' non trovato nel database locale.")
        risultato.append(record)
    logger.debug(f"dati sensori estratti dal db locale {risultato}")
    return risultato

def filtra_misurazioni_alterate(payload_dict : dict, id_alterati : set[int]) -> List[DatiMisurazione]:
    """
    Filtra e restituisce solo le misurazioni del payload il cui id è presente in `id_alterati`.
    """
    misurazioni_filtrate: List[DatiMisurazione] = []
    for m in payload_dict.get("misurazioni", []):
        id_mis = m.get("id_misurazione")
        if id_mis in id_alterati:
            misurazione = DatiMisurazione(**m)
            misurazioni_filtrate.append(misurazione)

    return misurazioni_filtrate


def ricostruisci_misurazioni_sensore(
        misurazioni: List[DatiMisurazione],lista_dati_sensori: List[DatiSensore]) -> List[DatiMisurazioneSensore]:
    """
    Ricostruisce oggetti DatiMisurazioneSensore accoppiando ogni misurazione
    con il suo sensore corrispondente (tramite id_sensore).
    """
    # Costruisce una mappa ID sensore → oggetto DatiSensore
    mappa_sensori: dict[str, DatiSensore] = {s.id_sensore: s for s in lista_dati_sensori}
    lista_risultato: List[DatiMisurazioneSensore] = []

    for mis in misurazioni:
        id_sensore = mis.id_sensore

        if id_sensore not in mappa_sensori:
            raise ValueError(f"Sensore con ID '{id_sensore}' non trovato tra quelli disponibili (BUG)")

        sensore = mappa_sensori[id_sensore]
        lista_risultato.append(DatiMisurazioneSensore(dati_misurazione=mis, dati_sensore=sensore))
        logger.debug(f"Lista di misurazioni-sensori ottenuti dal cloud {lista_risultato}")

    return lista_risultato

def confronta_dati_batch(batch_locale: DatiBatch, batch_cloud: DatiBatch) -> dict:
    """
    Confronta due oggetti DatiBatch assicurandosi che abbiano lo stesso ID.
    """
    if batch_locale.id_batch != batch_cloud.id_batch:
        raise ValueError("ATTENZIONE! Non corrispondono gli ID dei batch (bug)")
    return batch_locale.differenze_con(batch_cloud)

def confronta_dati_misurazioni(m1: DatiMisurazione, m2: DatiMisurazione) -> dict:
    """
    Confronta due oggetti DatiMisurazione dopo aver verificato la corrispondenza degli ID.
    """
    if m1.id_misurazione != m2.id_misurazione:
        raise ValueError("ATTENZIONE! Non corrispondono gli ID delle misurazioni (bug programmatore)")
    return m1.differenze_con(m2)


def confronta_dati_misurazioni_sensori(id_mis_alterati : list[int],
                                       mis_locale : List[DatiMisurazioneSensore],
                                       mis_cloud : List[DatiMisurazioneSensore]) -> dict:
    # 1. Crea mappe id_misurazione → DatiMisurazioneSensore
    mappa_locale: dict[int, DatiMisurazioneSensore] = {
        m.dati_misurazione.id_misurazione: m for m in mis_locale
    }
    mappa_cloud: dict[int, DatiMisurazioneSensore] = {
        m.dati_misurazione.id_misurazione: m for m in mis_cloud
    }

    # 2. Verifica che gli ID combacino tra locale e cloud
    if set(mappa_locale.keys()) != set(mappa_cloud.keys()):
        raise ValueError("Mismatch negli ID delle misurazioni tra locale e cloud")

    # 3. Costruisci dizionario delle differenze
    differenze: dict[int, dict] = {}

    for id_mis in id_mis_alterati:

        locale = mappa_locale[id_mis]
        cloud = mappa_cloud[id_mis]

        #Confronta due oggetti DatiSensore
        diff_sensori: dict = locale.dati_sensore.differenze_con(cloud.dati_sensore)
        # Confronta due oggetti DatiMisurazione
        diff_misurazioni: dict = confronta_dati_misurazioni(locale.dati_misurazione, cloud.dati_misurazione)

        entry: dict = {}
        if diff_sensori:
            entry["dati_sensore"] = diff_sensori
        if diff_misurazioni:
            entry["dati_misurazione"] = diff_misurazioni

        if entry:
            #crea il mapping se qualcosa è cambiato
            differenze[id_mis] = entry

    return differenze