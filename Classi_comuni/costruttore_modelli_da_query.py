import json
from typing import List, Dict, Tuple
from Classi_comuni.entita.modelli_dati import DatiBatch, DatiMisurazione
from modelli_dati import DatiSensore
from modelli_metadati import MetaDatiMisurazione, MetaDatiSensore
from Classi_comuni.utils.hashing_utils import Hashing

class CostruttoreModelliDaQuery:
    """
    Classe responsabile della trasformazione dei risultati SQL in oggetti Pydantic
    """
    @staticmethod
    def costruisci_modelli_da_query(risultati_query: List[Dict]) -> Tuple[DatiBatch, List[DatiMisurazione], Dict[int, str], str]:
        """
        Estrae i dati da una query INNER JOIN tra batch, misurazioni e sensori, e restituisce:
        - Oggetto DatiBatch
        - Lista di oggetti DatiMisurazione
        - Dizionario {id_misurazione: hash concatenato tupla sensore + misurazione}
        - Hash del batch (prima foglia del Merkle Tree)
        """
        misurazioni: List[DatiMisurazione] = []

        #mappa intero (id_misurazione) --> hash (misurazione inner join sensore)
        hash_misurazioni_sensori: Dict[int, str] = {}

        # Ordina le righe per ID misurazione
        risultati_ordinati = sorted(risultati_query, key=lambda r: r["id_misurazione"])
        prima_riga = risultati_ordinati[0]
        # dalla prima riga dei risultati estraggo la tupla corrispondente al batch
        # risultato sql --> DatiBatch
        batch : DatiBatch = CostruttoreModelliDaQuery.costruisci_dati_batch_da_query(prima_riga)
        # hash dell'istanza del batch
        hash_batch = batch.to_hash()

        for riga in risultati_ordinati:
            # risultato sql --> DatiMisurazione
            dati_misurazione : DatiMisurazione = CostruttoreModelliDaQuery.costruisci_dati_misurazione_da_query(riga)
            # risultato sql --> DatiSensore
            dati_sensore : DatiSensore = CostruttoreModelliDaQuery.costruisci_dati_sensore_da_query(riga)
            misurazioni.append(dati_misurazione)
            hash_concat = Hashing.hash_concat(
                dati_sensore.to_hash(),
                dati_misurazione.to_hash()
            )
            hash_misurazioni_sensori[dati_misurazione.id_misurazione] = hash_concat

        return batch, misurazioni, hash_misurazioni_sensori, hash_batch

    @staticmethod
    def costruisci_dati_misurazione_da_query(riga: dict) -> DatiMisurazione:
        """
        Costruisce un oggetto DatiMisurazione da una riga SQL.
        Esegue anche il parsing del campo 'dati' se è una stringa JSON.
        """
        CostruttoreModelliDaQuery._verifica_campi(riga, ["id_misurazione", "id_batch", "id_sensore", "timestamp", "dati"])

        if isinstance(riga["dati"], str):
            try:
                riga["dati"] = json.loads(riga["dati"])
            except json.JSONDecodeError as e:
                raise ValueError(f"[ERRORE JSON] Errore nel parsing del campo 'dati': {e}")

        return DatiMisurazione(
            id_misurazione=riga["id_misurazione"],
            id_batch=riga["id_batch"],
            id_sensore=riga["id_sensore"],
            timestamp=riga["timestamp"],
            dati=riga["dati"]
        )

    @staticmethod
    def costruisci_dati_sensore_da_query(riga: dict) -> DatiSensore:
        """
        Costruisce un oggetto DatiSensore da una riga SQL.
        """
        CostruttoreModelliDaQuery._verifica_campi(riga, ["id_sensore", "tipo", "descrizione"])
        return DatiSensore(
            id_sensore=riga["id_sensore"],
            tipo=riga["tipo"],
            descrizione=riga["descrizione"]
        )

    @staticmethod
    def costruisci_dati_batch_da_query(riga: dict) -> DatiBatch:
        """
        Costruisce un oggetto DatiBatch dalla prima riga della query.
        """
        CostruttoreModelliDaQuery._verifica_campi(riga, ["id_batch", "timestamp_creazione", "numero_misurazioni"])
        return DatiBatch(
            id_batch=riga["id_batch"],
            timestamp_creazione=riga["timestamp_creazione"],
            numero_misurazioni=riga["numero_misurazioni"]
        )

    @staticmethod
    def costruisci_metadati_misurazione_da_query(riga: dict) -> MetaDatiMisurazione:
        """
        Costruisce un oggetto MetaDatiMisurazione da una riga SQL.
        """
        CostruttoreModelliDaQuery._verifica_campi(riga, ["id_misurazione", "id_batch", "timestamp"])
        return MetaDatiMisurazione(
            id_misurazione=riga["id_misurazione"],
            id_batch=riga["id_batch"],
            timestamp=riga["timestamp"]
        )

    @staticmethod
    def costruisci_metadati_sensore_da_query(riga: dict) -> MetaDatiSensore:
        """
        Costruisce un oggetto MetaDatiSensore da una riga SQL.
        """
        CostruttoreModelliDaQuery._verifica_campi(riga, ["id_sensore", "tipo"])
        return MetaDatiSensore(
            id_sensore=riga["id_sensore"],
            tipo=riga["tipo"]
        )

    @staticmethod
    def _verifica_campi(riga: dict, campi_attesi: List[str]):
        for campo in campi_attesi:
            if campo not in riga:
                raise KeyError(f"Campo mancante nella riga SQL: '{campo}'")
