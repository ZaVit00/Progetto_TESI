import json
from typing import Dict
from Classi_comuni.merkle_tree import PathCompatto
from Verificatore.entita.modelli_verificatore import RisultatoVerifica
from costanti import MAPPING_CHIAVI_DIFFERENZE


def carica_merkle_paths_da_stringa_json(stringa_json: str) -> Dict[int, PathCompatto]:
    """
    Converte una stringa JSON proveniente da IPFS in un dizionario di PathCompatto.
    Ogni PathCompatto rappresenta il Merkle Path compatto per una foglia,
    con:
      - key: id_misurazione (o 0 per il batch), convertito da stringa a int
      - value: PathCompatto con attributi 'direzione' e 'hash_fratelli'.

    La stringa JSON deve avere questa forma:
    {
      "0": { "dir": "00101", "hash": ["h1","h2",...] },
      "1": { "dir": "10",    "hash": ["ha","hb"] },
      ...
    }
    """
    try:
        # Caricamento della stringa JSON in un dict Python
        diz = json.loads(stringa_json)
        #dizionario vuoto
        paths: Dict[int, PathCompatto] = {}

        for key_string, values in diz.items():
            # Converti la stringa chiave in un intero (es. "0" → 0)
            id_foglia = int(key_string)
            # Crea un nuovo oggetto PathCompatto
            path = PathCompatto()
            # Imposta la direzione (es. "00101")
            path.imposta_lista_direzione(values["dir"])
            # Imposta la lista di hash fratelli nell'esatto ordine
            path.imposta_hash_fratelli(values["hash"])
            # Aggiungi al dizionario finale
            paths[id_foglia] = path

        return paths

    except (ValueError, KeyError, TypeError) as e:
        # Genera errore dettagliato in caso di formato inaspettato
        raise ValueError(f"Errore nella deserializzazione dei Merkle Path da JSON: {e}")


# === Metodi di report ===#
# Questi metodi lavorano su dizionari distinti prodotti da tre operazioni distinte.
# - Processo di ottenimento delle anomalie
# - Processo di ottenimento dei metadati delle anomalie dal cloud
# - Processo di ottenimento delle differenze (confronto dati cloud vs dati locale)
# Poiché la struttura dei dizionari risultati dalle operazioni sono differenti
# si è reso necessario utilizzare tre funzione distinte.
def ottieni_report_anomalie(risultato: RisultatoVerifica) -> str:
    righe = [f"\nID Batch: {risultato['id_batch']}",
             f"Anomalie di integrità rilevate: {risultato['numero_anomalie_integrita']}",
             f"Anomalie strutturali (mancanti o aggiunti): {risultato['numero_anomalie_strutturali']}"]

    if risultato["anomalie_integrita"]:
        righe.append("\nDettagli anomalie di integrità:")
        for id_elem, dett in risultato["anomalie_integrita"].items():
            righe.append(
                f" - ID {id_elem} ({dett['tipo']}): {'INTEGRO' if dett['esito'] else 'ALTERATO'}"
                + (f" [{dett['note']}]" if dett['note'] else "")
            )

    if risultato["anomalie_strutturali"]["id_mancanti"]:
        righe.append(f"\nID mancanti: {risultato['anomalie_strutturali']['id_mancanti']}")
    if risultato["anomalie_strutturali"]["id_aggiunti"]:
        righe.append(f"ID aggiunti: {risultato['anomalie_strutturali']['id_aggiunti']}")

    return "\n".join(righe)


def ottieni_report_metadati_anomalie(anomalie: dict) -> str:
    """
    Genera una rappresentazione testuale leggibile del contenuto di un dizionario
    contenente metadati batch e misurazioni alterate.
    """
    righe = ["\nREPORT ANOMALIE METADATI\n"]

    # Batch
    if "metadata_batch" in anomalie:
        batch = anomalie["metadata_batch"]
        righe.append("Batch alterato:")
        righe.append(f"  - ID batch: {batch['id_batch']}")
        righe.append(f"  - Timestamp creazione: {batch['timestamp_creazione']}")
        righe.append(f"  - Numero misurazioni: {batch['numero_misurazioni']}\n")

    # Misurazioni
    if "metadata_misurazioni" in anomalie and anomalie["metadata_misurazioni"]:
        righe.append("⚠ Misurazioni alterate:")
        for id_mis, m in anomalie["metadata_misurazioni"].items():
            sensore = m["metadati_sensore"]
            mis = m["metadati_misurazione"]

            righe.append(f"  • ID Misurazione: {id_mis}")
            righe.append(f"    - Timestamp: {mis['timestamp']}")
            righe.append(f"    - ID Batch: {mis['id_batch']}")
            righe.append(f"    - Sensore: {sensore['id_sensore']} ({sensore['tipo']})\n")

    return "\n".join(righe)

def ottieni_report_differenze(differenze: dict) -> str:
    """
    Genera un report testuale leggibile a partire da un dizionario di differenze DeepDiff puro.
    Evita di ripetere la stampa di path duplicati per la stessa sezione.
    """
    def formatta_valori_cambiati(valori: dict, indent: int = 2) -> list[str]:
        spazi = " " * indent
        sotto_spazi = " " * (indent + 2)
        righe_locali = []
        path_stampati = set()
        for path, dettagli in valori.items():
            if path in path_stampati:
                continue
            path_stampati.add(path)
            righe_locali.append(f"{spazi}- {path}:")
            righe_locali.append(f"{sotto_spazi}• Locale: {dettagli.get('old_value', 'N/A')}")
            righe_locali.append(f"{sotto_spazi}• Cloud:  {dettagli.get('new_value', 'N/A')}")
        return righe_locali

    righe = ["\nREPORT DIFFERENZE (locale vs cloud)\n"]

    # ➤ Differenze nel batch
    if "dati_batch" in differenze:
        righe.append("Differenze nel batch:")
        valori_cambiati = differenze["dati_batch"].get("values_changed", {})
        righe += formatta_valori_cambiati(valori_cambiati)
        righe.append("")

    # ➤ Differenze nelle misurazioni alterate
    if "dati_misurazioni_alterate" in differenze:
        righe.append("Differenze nelle misurazioni alterate:")
        for id_misurazione, sezioni in differenze["dati_misurazioni_alterate"].items():
            righe.append(f"  • ID Misurazione: {id_misurazione}")
            path_stampati = set()
            for _, sotto_diff in sezioni.items():
                valori_cambiati = sotto_diff.get("values_changed", {})
                righe += formatta_valori_cambiati(
                    {k: v for k, v in valori_cambiati.items() if k not in path_stampati},
                    indent=6
                )
                path_stampati.update(valori_cambiati.keys())
            righe.append("")

    return "\n".join(righe)


