import logging
from Classi_comuni.entita.modelli_dati import DatiPayload
from Verificatore.api_client.api_cloud import richiedi_mappa_id_hash_batch
from Verificatore.api_client.ipfs_client import ottieni_file_da_ipfs
from Verificatore.verifica.verificatore_utils import carica_paths_da_json_string
from typing import TypedDict
from costanti_comuni import ID_BATCH_LOGICO
from Classi_comuni.merkle_tree import PathCompatto, MerkleTree

# Logger per messaggi informativi, di errore e di debug
logger = logging.getLogger(__name__)

# TypedDict che definisce la struttura dell’output della verifica
class DettagliVerifica(TypedDict):
    integre: list[dict]
    anomalie: list[dict]

class RisultatoVerifica(TypedDict):
    esito_globale: bool
    stato_elaborazione: str
    numero_anomalie: int
    dettagli: DettagliVerifica


class Verificatore:
    """
    Classe che incapsula l’intera procedura di verifica dell’integrità di un batch,
    confrontando i dati hashati con quelli registrati tramite Merkle Root e Merkle Path.
    """

    def __init__(self, id_batch: int) -> None:
        # ID del batch da verificare
        self.id_batch = id_batch

        # Dizionario dei dati hashati {id_misurazione: hash}
        self.mappa_id_hash: dict[int, str] = {}

        # Merkle Root attesa (recuperata da blockchain)
        self.merkle_root_immutabile: str | None = None

        # CID IPFS del file contenente i Merkle Path
        self.cid_merkle_path: str | None = None

        # Dizionario dei Merkle Path {id_misurazione: PathCompatto}
        self.merkle_paths: dict[int, PathCompatto] = {}

    def _recupera_dati(self) -> None:
        """
        Recupera dal cloud provider la mappa ID → hash relativa al batch.
        """
        logger.info(f"Recupero dei dati per il batch ID {self.id_batch}")
        self.mappa_id_hash = richiedi_mappa_id_hash_batch(self.id_batch)

    def _recupera_root_e_cid(self) -> None:
        """
        Recupera dalla blockchain la Merkle Root e il CID IPFS associato.
        (Attualmente sono placeholder – da implementare)
        """
        self.merkle_root_immutabile = "873e5d26a8229de5129dca68027fe72bc6f9f185fe2d7a46f57da51b407722d1"  # placeholder da smart contract
        self.cid_merkle_path = "QmYZdrLhnKuTDLX5hoSiAGs6Rz3hmPmB3ymqo7YFZLF2UE"         # placeholder da smart contract
        logger.info(f"Merkle Root attesa: {self.merkle_root_immutabile}")
        logger.info(f"CID IPFS del Merkle Path: {self.cid_merkle_path}")

    def _scarica_merkle_path(self) -> None:
        """
        Scarica il file JSON contenente i Merkle Path da IPFS.
        """
        if not self.cid_merkle_path:
            raise ValueError("CID IPFS non inizializzato")

        logger.info(f"Scaricamento Merkle Path da IPFS tramite CID {self.cid_merkle_path}")
        json_string = ottieni_file_da_ipfs(self.cid_merkle_path)
        self.merkle_paths = carica_paths_da_json_string(json_string)

    def _verifica_struttura(self) -> bool:
        """
        Verifica che la struttura delle misurazioni ottenute dal cloud
        coincida con quella presente nel file IPFS (escludendo il nodo batch).
        """
        id_misurazioni_ipfs = set(self.merkle_paths.keys())
        id_misurazioni_cloud = set(self.mappa_id_hash.keys())

        if id_misurazioni_ipfs != id_misurazioni_cloud:
            # Individua gli ID mancanti o aggiunti
            id_mancanti = id_misurazioni_ipfs - id_misurazioni_cloud
            id_aggiunti = id_misurazioni_cloud - id_misurazioni_ipfs

            if id_mancanti:
                logger.warning(f"ID mancanti rispetto alla struttura originale: {sorted(id_mancanti)}")
            if id_aggiunti:
                logger.warning(f"ID aggiunti non presenti nella struttura originale: {sorted(id_aggiunti)}")

            logger.error("Struttura batch manomessa")
            return False

        logger.info("Struttura batch integra")
        return True

    def verifica_integrita(self) -> None:
        """
        Verifica l’integrità delle singole foglie (hash) tramite i Merkle Path.
        """
        if not self.merkle_root_immutabile:
            raise ValueError("Merkle root attesa non inizializzata")

        self._verifica_foglie_con_path()

    def _verifica_foglie_con_path(self) -> DettagliVerifica:
        """
        Verifica ogni foglia rispetto alla Merkle Root attesa usando i Merkle Path.
        Restituisce un dizionario con due liste: 'integre' e 'anomalie'.
        """
        foglie_integre = []
        foglie_anomale = []

        for id_foglia, foglia_hash in self.mappa_id_hash.items():
            tipo = "batch" if id_foglia == 0 else "misurazione"
            id_mostrato = id_foglia if id_foglia != 0 else self.id_batch

            #se l'id della foglia non compare nel merkle paths scaricato da IPFS
            #ALTERAZIONE STRUTTURA ID DELLA TUPLA
            if id_foglia not in self.merkle_paths:
                risultato = {
                    "id": id_mostrato,
                    "tipo": tipo,
                    "esito": False,
                    "note": "Merkle Path mancante"
                }
                foglie_anomale.append(risultato)
                logger.error(f"[{tipo.upper()}] ID {id_foglia}: Merkle Path mancante")
                continue #passa alla prossima foglia

            path = self.merkle_paths[id_foglia]
            esito_operazione = MerkleTree.verifica_singola_foglia(foglia_hash, path, self.merkle_root_immutabile)

            risultato = {
                "id": id_mostrato,
                "tipo": tipo,
                "esito": esito_operazione,
                "note": "nessuna compromissione" if esito_operazione else "ANOMALIA RILEVATA"
            }

            if esito_operazione:
                foglie_integre.append(risultato)
                logger.info(f"[{tipo.upper()}] ID {id_foglia} → ✔ INTEGRO")
            else:
                foglie_anomale.append(risultato)
                logger.warning(f"[{tipo.upper()}] ID {id_foglia} → ✘ ALTERATO")

        return {
            "integre": foglie_integre,
            "anomalie": foglie_anomale
        }

    def esegui_verifica_completa(self) -> RisultatoVerifica:
        """
        Procedura principale di verifica dell’integrità di un batch:
        - Recupera hash dal cloud
        - Ottiene Merkle Root e CID da blockchain
        - Scarica Merkle Path da IPFS
        - Verifica la struttura e le singole foglie

        Restituisce un dizionario con:
        - esito_globale: True/False
        - dettagli: lista di verifiche foglia per foglia
        - errore: eventuale messaggio di errore bloccante
        """
        risultati: RisultatoVerifica = {
            "esito_globale": False,
            "stato_elaborazione": "Nessun errore in fase di esecuzione",
            "numero_anomalie" : 0,
            "dettagli": {
                "integre": [],
                "anomalie": []
            }
        }

        # 1. Recupero dati hashati dal cloud
        try:
            self._recupera_dati()
        except Exception as e:
            logger.exception("[ERRORE] Errore nella richiesta HTTP al cloud provider")
            risultati["stato_elaborazione"] = f"Errore durante la richiesta dei dati al cloud: {e}"
            return risultati

        # 2. Recupero root e CID da blockchain (da implementare)
        try:
            self._recupera_root_e_cid()
        except Exception as e:
            logger.exception("[ERRORE] Errore nel recupero della root e CID da blockchain")
            risultati["stato_elaborazione"] = f"Errore durante il recupero da blockchain: {e}"
            return risultati

        # 3. Scaricamento Merkle Path da IPFS
        try:
            self._scarica_merkle_path()
        except Exception as e:
            logger.exception("[ERRORE] Errore nello scaricamento dei Merkle Path da IPFS")
            risultati["stato_elaborazione"] = f"Errore durante lo scaricamento dei Merkle Path da IPFS: {e}"
            return risultati

        # 4. Verifica coerenza tra struttura IPFS e hash cloud
        struttura_valida = self._verifica_struttura()
        if not struttura_valida:
            logger.warning("Verifica eseguita su batch con struttura manomessa")

        # 5. Verifica delle foglie rispetto alla Merkle Root
        risultati["dettagli"] = self._verifica_foglie_con_path()
        risultati["numero_anomalie"] = len (risultati["dettagli"]["anomalie"])
        risultati["esito_globale"] = True if  risultati["numero_anomalie"] == 0 else False
        logger.info(f"Processo di verifica completato – Esito: {risultati['esito_globale']}")

        return risultati
