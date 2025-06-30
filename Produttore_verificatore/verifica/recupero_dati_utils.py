import json
import logging
from typing import List
from Produttore_verificatore.config.istanze_globali import gestore_db
from modelli_dati import DatiBatch, DatiMisurazione, DatiSensore, DatiMisurazioneSensore

logger = logging.getLogger(__name__)

def carica_payload_json(id_batch: int) -> dict:
    """
    Recupera il campo `payload_json` dal database, lo decodifica da stringa JSON
    e lo restituisce come dizionario Python.
    """
    raw_payload = gestore_db.ottieni_payload_batch(id_batch)

    if not raw_payload:
        raise ValueError(f"Nessun payload JSON disponibile per il batch {id_batch} BUG LOGICO")

    try:
        #converte la stringa in dict con json.loads
        return json.loads(raw_payload)
    except json.JSONDecodeError as e:
        logger.error(f"[DECODIFICA JSON] Batch {id_batch}: errore → {e}")
        raise ValueError("Errore nel parsing del payload JSON")


def estrai_lista_id_sensori_dal_payload(payload: dict) -> list[str]:
    """
    Estrae tutti gli `id_sensore` presenti nelle misurazioni del payload.
    Restituisce una lista senza duplicati (grazie alla struttura dati insieme)
    """
    misurazioni = payload.get("misurazioni", [])
    id_sensori = set(str(m.get("id_sensore")) for m in misurazioni)
    return list(id_sensori)


def estrai_dati_sensori_locali(lista_id_sensori: List[str]) -> List[DatiSensore]:
    """
    Dato un elenco di ID sensori, restituisce gli oggetti `DatiSensore`
    corrispondenti recuperati dal database locale.
    Solleva eccezione se almeno uno dei sensori non è presente.
    """
    risultato = []
    for id_sensore in lista_id_sensori:
        record: DatiSensore = gestore_db.ottieni_dati_sensore(id_sensore)
        if not record:
            raise ValueError(f"Sensore con ID '{id_sensore}' non trovato nel database locale.")
        risultato.append(record)
    logger.debug(f"dati sensori estratti dal db locale {risultato}")
    return risultato


def filtra_misurazioni_alterate(payload_dict: dict, id_alterati: set[int]) -> List[DatiMisurazione]:
    """
    Filtra e restituisce solo le misurazioni presenti nel payload
    che hanno un ID incluso nell'insieme `id_alterati`.
    """
    misurazioni_filtrate: List[DatiMisurazione] = []
    for m in payload_dict.get("misurazioni", []):
        id_mis = m.get("id_misurazione")
        if id_mis in id_alterati:
            misurazione = DatiMisurazione(**m)
            misurazioni_filtrate.append(misurazione)

    logger.debug(f"Misurazioni filtrate dal payload JSON {misurazioni_filtrate}")
    return misurazioni_filtrate


def ricostruisci_misurazioni_sensore(
        misurazioni: List[DatiMisurazione],
        lista_dati_sensori: List[DatiSensore]) -> List[DatiMisurazioneSensore]:
    """
    Ricostruisce oggetti `DatiMisurazioneSensore`, associando ogni misurazione
    con il sensore corrispondente, in base al campo `id_sensore`.
    """
    # Crea una mappa: id_sensore → DatiSensore
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
    Confronta due oggetti `DatiBatch`, assicurandosi che abbiano lo stesso ID.
    Restituisce un dizionario con le differenze rilevate.
    """
    if batch_locale.id_batch != batch_cloud.id_batch:
        raise ValueError("ATTENZIONE! Non corrispondono gli ID dei batch (bug)")
    return batch_locale.differenze_con(batch_cloud)


def confronta_dati_misurazioni(m1: DatiMisurazione, m2: DatiMisurazione) -> dict:
    """
    Confronta due oggetti `DatiMisurazione` (stesso ID) e restituisce le differenze.
    """
    if m1.id_misurazione != m2.id_misurazione:
        raise ValueError("ATTENZIONE! Non corrispondono gli ID delle misurazioni (bug)")
    return m1.differenze_con(m2)


def confronta_dati_misurazioni_sensori(
    id_mis_alterati: list[int],
    mis_locale: List[DatiMisurazioneSensore],
    mis_cloud: List[DatiMisurazioneSensore]) -> dict:
    """
    Confronta tutte le misurazioni alterate tra locale e cloud.

    Restituisce un dizionario con ID della misurazione come chiave
    e differenze nei dati del sensore e della misurazione come valore.
    """
    # Crea dizionari: id_misurazione → DatiMisurazioneSensore
    mappa_locale = {m.dati_misurazione.id_misurazione: m for m in mis_locale}
    mappa_cloud = {m.dati_misurazione.id_misurazione: m for m in mis_cloud}

    # Verifica che gli insiemi di ID coincidano
    if set(mappa_locale.keys()) != set(mappa_cloud.keys()):
        raise ValueError("Mismatch negli ID delle misurazioni tra locale e cloud")

    differenze: dict[int, dict] = {}

    for id_mis in id_mis_alterati:
        locale = mappa_locale[id_mis]
        cloud = mappa_cloud[id_mis]

        # Confronta i dati del sensore
        diff_sensori = locale.dati_sensore.differenze_con(cloud.dati_sensore)

        # Confronta i dati della misurazione
        diff_misurazioni = confronta_dati_misurazioni(locale.dati_misurazione, cloud.dati_misurazione)

        entry = {}
        if diff_sensori:
            entry["dati_sensore"] = diff_sensori
        if diff_misurazioni:
            entry["dati_misurazione"] = diff_misurazioni

        # Aggiunge al dizionario solo se ci sono differenze
        if entry:
            differenze[id_mis] = entry

    return differenze
