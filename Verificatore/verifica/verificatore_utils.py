import json
from typing import Dict
from Classi_comuni.merkle_tree import PathCompatto
from Verificatore.entita.modelli_verificatore import RisultatoVerifica, RisultatoMetadatiAnomalie


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
            path.set_direzione(values["dir"])
            # Imposta la lista di hash fratelli nell'esatto ordine
            path.set_hash_fratelli(values["hash"])
            # Aggiungi al dizionario finale
            paths[id_foglia] = path

        return paths

    except (ValueError, KeyError, TypeError) as e:
        # Genera errore dettagliato in caso di formato inaspettato
        raise ValueError(f"Errore nella deserializzazione dei Merkle Path da JSON: {e}")

def ottieni_report_anomalie(risultato: RisultatoVerifica) -> str:
    righe = [f"ID Batch: {risultato['id_batch']}",
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
    righe = [" REPORT ANOMALIE METADATI\n"]

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
    Genera una rappresentazione testuale leggibile delle differenze tra dati locali e cloud.
    """
    righe = ["REPORT DIFFERENZE (locale vs cloud)\n"]

    # ➤ Differenze nel batch
    if "dati_batch" in differenze:
        righe.append("Differenze nel batch:")
        for campo, val in differenze["dati_batch"].items():
            locale = val.get("locale", "N/A")
            cloud = val.get("cloud", "N/A")
            righe.append(f"  - {campo}:")
            righe.append(f"    • Locale: {locale}")
            righe.append(f"    • Cloud:  {cloud}")
        righe.append("")

    # ➤ Differenze nelle misurazioni
    if "dati_misurazioni_alterate" in differenze:
        righe.append("Differenze nelle misurazioni alterate:")
        for id_misurazione, differenze_campi in differenze["dati_misurazioni_alterate"].items():
            righe.append(f"  • ID Misurazione: {id_misurazione}")
            for campo, val in differenze_campi.items():
                locale = val.get("locale", "N/A")
                cloud = val.get("cloud", "N/A")
                righe.append(f"      - {campo}:")
                righe.append(f"        • Locale: {locale}")
                righe.append(f"        • Cloud:  {cloud}")
            righe.append("")

    return "\n".join(righe)
