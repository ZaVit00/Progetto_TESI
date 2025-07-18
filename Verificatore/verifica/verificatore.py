import logging
from typing import TypedDict, List, cast
from Classi_comuni.merkle_tree import PathCompatto, MerkleTree
from Classi_comuni.utils.dict_utils import serializza_dict
from Verificatore.api_client.api_cloud import richiedi_mappa_id_hash_batch, richiedi_metadata_batch, \
    richiedi_metadata_misurazione_sensore
from Verificatore.api_client.ipfs_client import ottieni_file_da_ipfs
from Verificatore.config.istanze_globali import lettore_blockchain
from Verificatore.verifica.verificatore_utils import carica_merkle_paths_da_stringa_json
from modelli_metadati import MetaDatiBatch, MetaDatiMisurazioneSensore

logger = logging.getLogger(__name__)

# --- Tipi ausiliari per la verifica ---#
class DettagliVerifica(TypedDict):
    id : int
    tipo : str
    esito : bool
    modifica_strutturale : bool
    note : str

class StrutturaVerifica(TypedDict):
    id_mancanti: list[int]
    id_aggiunti: list[int]

class RisultatoVerifica(TypedDict):
    id_batch : int
    numero_anomalie_integrita: int
    numero_anomalie_strutturali : int
    anomalie_integrita: list[DettagliVerifica]
    anomalie_strutturali: StrutturaVerifica

# --- Classe Verificatore ---

class Verificatore:
    def __init__(self, id_batch: int) -> None:

        self.id_batch : int = id_batch
        self.mappa_id_hash: dict[int, str] = {}
        self.merkle_root_immutabile: str | None = None
        self.cid_merkle_path: str | None = None
        self.merkle_paths: dict[int, PathCompatto] = {}
        self.risultato: RisultatoVerifica = {
            "id_batch": self.id_batch,
            "numero_anomalie_integrita": 0,
            "numero_anomalie_strutturali" : 0,
            "anomalie_integrita": [],
            "anomalie_strutturali": {"id_mancanti": [], "id_aggiunti": []},
        }

    def _recupera_dati_batch_cloud(self) -> None:
        logger.info(f"Recupero dei dati per il batch ID {self.id_batch}")
        self.mappa_id_hash = richiedi_mappa_id_hash_batch(self.id_batch)


    def _recupera_root_e_cid_blockchain(self) -> None:
        self.merkle_root_immutabile, self.cid_merkle_path = lettore_blockchain.leggi_valore(self.id_batch)
        logger.info(f"Merkle Root attesa: {self.merkle_root_immutabile}")
        logger.info(f"CID IPFS del Merkle Path: {self.cid_merkle_path}")

    def _scarica_merkle_path_ipfs(self) -> None:
        logger.info(f"Scarico Merkle Path da IPFS tramite CID {self.cid_merkle_path}")
        stringa_json = ottieni_file_da_ipfs(self.cid_merkle_path)
        self.merkle_paths = carica_merkle_paths_da_stringa_json(stringa_json)

    def _verifica_struttura(self) -> tuple[list[int], list[int]]:
        """
        Verifica la coerenza tra gli ID delle misurazioni registrati su IPFS
        e quelli restituiti dal cloud. Restituisce due liste:
        - id_mancanti: presenti in IPFS ma assenti nel cloud
        - id_aggiunti: presenti nel cloud ma assenti in IPFS
        """
        ipfs_ids = set(self.merkle_paths.keys())
        cloud_ids = set(self.mappa_id_hash.keys())
        id_mancanti = sorted(ipfs_ids - cloud_ids)
        id_aggiunti = sorted(cloud_ids - ipfs_ids)

        if id_mancanti:
            logger.warning(f"ID mancanti nella struttura: {id_mancanti}")
        if id_aggiunti:
            logger.warning(f"ID aggiunti nella struttura: {id_aggiunti}")

        if id_mancanti or id_aggiunti:
            logger.warning("Struttura batch manomessa")
        else:
            logger.info("Struttura batch integra")

        return id_mancanti, id_aggiunti

    def _verifica_foglie_con_path(self) -> list[DettagliVerifica]:
        """
        Verifica ciascuna foglia (batch o misurazione) utilizzando i Merkle Path.
        Ritorna due liste: 'integre' e 'anomalie'.
        """
        integre, anomalie = [], []
        for foglia_id, foglia_hash in self.mappa_id_hash.items():
            tipo = "batch" if foglia_id == 0 else "misurazione"
            id = self.id_batch if foglia_id == 0 else foglia_id

            if foglia_id not in self.merkle_paths:
                anomalie.append(DettagliVerifica(
                    id = id,tipo = tipo, esito = False, modifica_strutturale= True, note = "[IPFS] Merkle Path mancante"))
                logger.error(f"[{tipo.upper()}] ID {foglia_id}: Merkle Path mancante")
                continue #salta alla prossima foglia, struttura manomessa

            path_foglia = self.merkle_paths[foglia_id]
            esito_verifica = MerkleTree.verifica_singola_foglia(foglia_hash, path_foglia, self.merkle_root_immutabile)
            entry = DettagliVerifica(id = id, tipo = tipo, esito = esito_verifica, modifica_strutturale= False,
                                     note = "nessuna compromissione" if esito_verifica else "ANOMALIA RILEVATA")
            if esito_verifica:
                # verifica okay
                integre.append(entry)
                logger.info(f"[{tipo.upper()}] ID {foglia_id} → ✔ INTEGRO")
            else:
                #anomalie rilevata
                anomalie.append(entry)
                logger.warning(f"[{tipo.upper()}] ID {foglia_id} → ✘ ALTERATO")

        return anomalie

    def esegui_verifica_integrita(self) -> str:

        # 1. Recupero mappa id - foglie (hash) dal cloud
        # Tutto ciò che è necessario per determinare l'anomalia è il confronto tra
        # l'hash ottenuto dal cloud e la merkle root immutabile salvata su Blockchain
        try:
            self._recupera_dati_batch_cloud()
        except Exception as e:
            logger.exception("[ERRORE] Errore nella richiesta HTTP al cloud provider")
            raise RuntimeError(f"Errore nel recupero dei dati dal cloud: {e}")

        # 2. Recupero root e CID da blockchain
        try:
            self._recupera_root_e_cid_blockchain()

        except Exception as e:
            logger.exception("[ERRORE] Errore nel recupero della root e del CID da blockchain")
            raise RuntimeError(f"Errore nel recupero dei metadati blockchain: {e}")

        # 2.b Verifica integrità dei metadati ottenuti
        if not self.merkle_root_immutabile or not self.cid_merkle_path:
            raise ValueError(
                f"❌ Batch ID {self.id_batch}: struttura compromessa. "
                f"Merkle root o CID assenti per il batch indicato — possibile manomissione o batch non registrato."
            )

        # 3. Scaricamento Merkle Path da IPFS
        try:
            self._scarica_merkle_path_ipfs()
        except Exception as e:
            logger.exception("[ERRORE] Errore nello scaricamento dei Merkle Path da IPFS")
            raise RuntimeError(f"Errore nel download da IPFS: {e}") from e

        # Fase 4: verifica della struttura
        id_mancanti, id_aggiunti = self._verifica_struttura()
        self.risultato["anomalie_strutturali"] = StrutturaVerifica(
            id_mancanti=id_mancanti,
            id_aggiunti=id_aggiunti
        )

        # Fase 5: verifica dell'integrità delle foglie e salvataggio dei risultati
        foglie_anomale = self._verifica_foglie_con_path()
        self.risultato["anomalie_integrita"] = foglie_anomale

        # Conteggio delle anomalie strutturali:
        # Gli ID delle misurazioni aggiunti manualmente sul cloud (non presenti nel Merkle Path)
        # vengono considerati anomalie strutturali. Questo perché non è possibile procedere alla
        # verifica dell'integrità: manca infatti il Merkle Path associato a quegli ID.

        # Rientrano in questa categoria anche le tuple di misurazioni che sono state assegnate
        # a un batch in modo manuale o scorretto (alterando il valore del campo id_batch):
        # anche in questo caso non esiste un Merkle Path associato all’ID, e la verifica fallisce.

        self.risultato["numero_anomalie_integrita"] = len(self.risultato["anomalie_integrita"])
        self.risultato["numero_anomalie_strutturali"] = len(id_mancanti) + len(id_aggiunti)

        return serializza_dict(cast(dict, self.risultato))

    def ottieni_numero_anomalie_integrita(self) -> int:
        return self.risultato["numero_anomalie_integrita"]

    def ottieni_numero_anomalie_strutturali(self) -> int:
        return self.risultato["numero_anomalie_strutturali"]

    def ottieni_esito_globale(self) -> bool:
        return (self.risultato["numero_anomalie_integrita"] == 0
                and self.risultato["numero_anomalie_strutturali"] == 0)

    def batch_alterato(self) -> bool:
        """
        Ritorna True se la prima foglia anomala è il batch (foglia ID 0), False altrimenti.
        """
        anomalie = self.risultato["anomalie_integrita"]
        return bool(anomalie) and anomalie[0]["tipo"] == "batch"

    def misurazioni_alterate(self) -> bool:
        """
        Restituisce True se ALMENO (any) una foglia di tipo 'misurazione' risulta alterata.
        """
        anomalie: List[DettagliVerifica] = self.risultato["anomalie_integrita"]
        return any(record["tipo"] == "misurazione" for record in anomalie)

    def ottieni_id_misurazioni_alterate(self) -> list[int]:
        """
        Restituisce una lista di ID delle misurazioni alterate.
        Lancia un'eccezione se nessuna misurazione risulta alterata.
        """
        if not self.misurazioni_alterate():
            raise ValueError("Nessuna misurazione risulta alterata.")

        # Estrai tutte le anomalie di integrità
        anomalie: List[DettagliVerifica] = self.risultato["anomalie_integrita"]

        # Filtra solo quelle relative alle misurazioni che sono effettivamente alterate e che non sono
        # anomalie strutturali (mancanza di merkle path)
        anomalie_misurazioni = [
            record for record in anomalie
            if record["tipo"] == "misurazione" and not record["modifica_strutturale"]]
        # Estrai gli ID delle misurazioni alterate
        id_alterati = [record["id"] for record in anomalie_misurazioni]
        return id_alterati


    # METODI PER VISUALIZZARE I METADATI DEL BATCH E DELLE MISURAZIONI EVENTUALMENTE COMPROMESSI
    def _recupera_metadati_batch(self) -> MetaDatiBatch:
        return richiedi_metadata_batch(self.id_batch)

    def _recupera_metadati_misurazione_sensore(self) -> list[MetaDatiMisurazioneSensore]:
        id_list = self.ottieni_id_misurazioni_alterate()
        return richiedi_metadata_misurazione_sensore(id_list)

    def recupera_metadata_anomalie(self) -> str:
        # TODO DA CAMBIARE VISUALIZZAZIONE OUTPUT
        risultati = {}

        if self.batch_alterato():
            try:
                metadati_batch = self._recupera_metadati_batch()
            except Exception as e:
                raise ValueError(f"❌ Errore nel recupero dei metadati batch ID {self.id_batch}: {e}")

            risultati['metadata_batch'] = metadati_batch.to_json()

        if self.misurazioni_alterate():
            try:
                metadati_mis_sens: List[MetaDatiMisurazioneSensore] = self._recupera_metadati_misurazione_sensore()
            except Exception as e:
                raise ValueError(f"Errore nel recupero dei metadati misurazioni: {e}")

            lista_serializzata = []
            for elem in metadati_mis_sens:
                dict_elem = {
                    "metadati_sensore": elem.metadati_sensore.model_dump(),
                    "metadati_misurazioni": elem.metadati_misurazione.model_dump()
                }
                lista_serializzata.append(dict_elem)
            risultati['metadata_misurazioni_sensori'] = lista_serializzata

        return serializza_dict(risultati)