import json
from typing import List, Dict, Tuple
from Classi_comuni.entita.modelli_dati import DatiBatch, DatiMisurazione
from modelli_dati import DatiSensore
from modelli_metadati import MetaDatiMisurazione, MetaDatiSensore
from Classi_comuni.utils.hashing_utils import Hashing
from Classi_comuni.config.costanti_comuni import ID_BATCH_LOGICO


class EstrattoreDatiQuery:
    """
    Classe responsabile della trasformazione dei risultati SQL in oggetti Pydantic e hash associati.
    Estrae i dati da una query INNER JOIN tra batch, misurazioni e sensori, e restituisce:
    - Oggetto DatiBatch
    - Lista di oggetti DatiMisurazione
    - Lista di oggetti DatiSensore
    - Dizionario {id_misurazione: hash concatenato sensore+misurazione}
    - Hash del batch (prima foglia del Merkle Tree)
    """

    @staticmethod
    def estrai_dati_da_query(risultati_query: List[Dict]) -> Tuple[DatiBatch, List[DatiMisurazione], List[DatiSensore], Dict[int, str], str]:
        if not risultati_query:
            raise ValueError("La query non ha restituito risultati. Verifica gli ID passati.")

        misurazioni: List[DatiMisurazione] = []
        sensori: List[DatiSensore] = []
        hash_misurazioni_sensori: Dict[int, str] = {}

        # Ordina le righe per ID misurazione
        risultati_ordinati = sorted(risultati_query, key=lambda r: r["id_misurazione"])

        prima_riga = risultati_ordinati[0]
        batch = EstrattoreDatiQuery.costruisci_dati_batch_da_query(prima_riga)
        hash_batch = batch.to_hash()

        for riga in risultati_ordinati:
            dati_misurazione = EstrattoreDatiQuery.costruisci_dati_misurazione_da_query(riga)
            dati_sensore = EstrattoreDatiQuery.costruisci_dati_sensore_da_query(riga)

            misurazioni.append(dati_misurazione)
            sensori.append(dati_sensore)

            hash_concat = Hashing.hash_concat(
                dati_sensore.to_hash(),
                dati_misurazione.to_hash()
            )
            hash_misurazioni_sensori[dati_misurazione.id_misurazione] = hash_concat

        return batch, misurazioni, sensori, hash_misurazioni_sensori, hash_batch

    @staticmethod
    def costruisci_dati_misurazione_da_query(riga: dict) -> DatiMisurazione:
        if isinstance(riga["dati"], str):
            try:
                riga["dati"] = json.loads(riga["dati"])
            except json.JSONDecodeError as e:
                raise ValueError(f"[ERRORE JSON] Errore nel parsing del campo 'dati': {e}")

        EstrattoreDatiQuery._verifica_campi(riga, ["id_misurazione", "id_batch", "id_sensore", "timestamp", "dati"])
        return DatiMisurazione(
            id_misurazione=riga["id_misurazione"],
            id_batch=riga["id_batch"],
            id_sensore=riga["id_sensore"],
            timestamp=riga["timestamp"],
            dati=riga["dati"]
        )

    @staticmethod
    def costruisci_dati_sensore_da_query(riga: dict) -> DatiSensore:
        EstrattoreDatiQuery._verifica_campi(riga, ["id_sensore", "tipo", "descrizione"])
        return DatiSensore(
            id_sensore=riga["id_sensore"],
            tipo=riga["tipo"],
            descrizione=riga["descrizione"]
        )

    @staticmethod
    def costruisci_dati_batch_da_query(riga: dict) -> DatiBatch:
        EstrattoreDatiQuery._verifica_campi(riga, ["id_batch", "timestamp_creazione", "numero_misurazioni"])
        return DatiBatch(
            id_batch=riga["id_batch"],
            timestamp_creazione=riga["timestamp_creazione"],
            numero_misurazioni=riga["numero_misurazioni"]
        )

    @staticmethod
    def costruisci_metadati_misurazione_da_query(riga: dict) -> MetaDatiMisurazione:
        EstrattoreDatiQuery._verifica_campi(riga, ["id_misurazione", "id_batch", "timestamp"])
        return MetaDatiMisurazione(
            id_misurazione=riga["id_misurazione"],
            id_batch=riga["id_batch"],
            timestamp=riga["timestamp"]
        )

    @staticmethod
    def costruisci_metadati_sensore_da_query(riga: dict) -> MetaDatiSensore:
        EstrattoreDatiQuery._verifica_campi(riga, ["id_sensore", "tipo"])
        return MetaDatiSensore(
            id_sensore=riga["id_sensore"],
            tipo=riga["tipo"]
        )

    @staticmethod
    def _verifica_campi(riga: dict, campi_attesi: List[str]) -> None:
        for campo in campi_attesi:
            if campo not in riga:
                raise KeyError(f"Campo mancante nella riga SQL: '{campo}'")
