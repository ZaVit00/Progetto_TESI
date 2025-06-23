import json
import logging
from typing import TypedDict, List

from Classi_comuni.entita.modelli_dati import DatiPayload
from Verificatore.api_client.api_cloud import richiedi_mappa_id_hash_batch, richiedi_metadata_batch, \
    richiedi_metadata_misurazioni
from Verificatore.api_client.ipfs_client import ottieni_file_da_ipfs
from Verificatore.verifica.verificatore_utils import carica_merkle_paths_da_json_string
from costanti_comuni import ID_BATCH_LOGICO
from Classi_comuni.merkle_tree import PathCompatto, MerkleTree
from modelli_dati import MetaDatiMisurazione, MetaDatiBatch

logger = logging.getLogger(__name__)

# --- Tipi per l'output della verifica ---

class StrutturaVerifica(TypedDict):
    id_mancanti: list[int]
    id_aggiunti: list[int]

class DettagliVerifica(TypedDict):
    integre: list[dict]
    anomalie: list[dict]

class RisultatoVerifica(TypedDict):
    esito_globale: bool
    stato_elaborazione: str
    numero_anomalie: int
    dettagli: DettagliVerifica
    anomalie_struttura: StrutturaVerifica

# --- Classe Verificatore ---

class Verificatore:
    def __init__(self, id_batch: int) -> None:
        self.id_batch = id_batch
        self.mappa_id_hash: dict[int, str] = {}
        self.merkle_root_immutabile: str | None = None
        self.cid_merkle_path: str | None = None
        self.merkle_paths: dict[int, PathCompatto] = {}

    def _recupera_dati(self) -> None:
        logger.info(f"Recupero dei dati per il batch ID {self.id_batch}")
        self.mappa_id_hash = richiedi_mappa_id_hash_batch(self.id_batch)

    def _recupera_root_e_cid(self) -> None:
        # TODO: implementare il recupero reale da blockchain
        self.merkle_root_immutabile = "69fc6d9eaf8f428e794bc09618072f30f4da8162b852675a9604908f79a325ea"
        self.cid_merkle_path = "Qmbt8tgsWgQgq82aKyUTJdne93KELhvEqFWeFN91J7NEYM"
        logger.info(f"Merkle Root attesa: {self.merkle_root_immutabile}")
        logger.info(f"CID IPFS del Merkle Path: {self.cid_merkle_path}")

    def _scarica_merkle_path(self) -> None:
        if not self.cid_merkle_path:
            raise ValueError("CID IPFS non inizializzato")
        logger.info(f"Scarico Merkle Path da IPFS tramite CID {self.cid_merkle_path}")
        json_string = ottieni_file_da_ipfs(self.cid_merkle_path)
        self.merkle_paths = carica_merkle_paths_da_json_string(json_string)

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

    def _verifica_foglie_con_path(self) -> DettagliVerifica:
        """
        Verifica ciascuna foglia (batch o misurazione) utilizzando i Merkle Path.
        Ritorna due liste: 'integre' e 'anomalie'.
        """
        integre, anomalie = [], []
        for foglia_id, foglia_hash in self.mappa_id_hash.items():
            tipo = "batch" if foglia_id == 0 else "misurazione"
            ident = self.id_batch if foglia_id == 0 else foglia_id

            if foglia_id not in self.merkle_paths:
                anomalie.append({
                    "id": ident,
                    "tipo": tipo,
                    "esito": False,
                    "note": "[IPFS] Merkle Path mancante"
                })
                logger.error(f"[{tipo.upper()}] ID {foglia_id}: Merkle Path mancante")
                continue

            path_foglia = self.merkle_paths[foglia_id]
            esito_verifica = MerkleTree.verifica_singola_foglia(foglia_hash, path_foglia, self.merkle_root_immutabile)
            entry = {
                "id": ident,
                "tipo": tipo,
                "esito": esito_verifica,
                "note": "nessuna compromissione" if esito_verifica else "ANOMALIA RILEVATA"
            }
            if esito_verifica:
                integre.append(entry)
                logger.info(f"[{tipo.upper()}] ID {foglia_id} → ✔ INTEGRO")
            else:
                anomalie.append(entry)
                logger.warning(f"[{tipo.upper()}] ID {foglia_id} → ✘ ALTERATO")

        return {"integre": integre, "anomalie": anomalie}

    def esegui_verifica_completa(self) -> RisultatoVerifica:
        risultato: RisultatoVerifica = {
            "esito_globale": False,
            "stato_elaborazione": "Inizializzazione",
            "numero_anomalie": 0,
            "dettagli": {
                "integre": [],
                "anomalie": []
            },
            "anomalie_struttura": {"id_mancanti": [], "id_aggiunti": []},
        }

        # 1. Recupero dati hashati dal cloud
        try:
            self._recupera_dati()
        except Exception as e:
            logger.exception("[ERRORE] Errore nella richiesta HTTP al cloud provider")
            risultato["stato_elaborazione"] = f"Errore durante la richiesta dei dati al cloud: {e}"
            return risultato

        # 2. Recupero root e CID da blockchain (placeholder)
        try:
            self._recupera_root_e_cid()
        except Exception as e:
            logger.exception("[ERRORE] Errore nel recupero della root e del CID da blockchain")
            risultato["stato_elaborazione"] = f"Errore durante il recupero da blockchain: {e}"
            return risultato

        # 3. Scaricamento Merkle Path da IPFS
        try:
            self._scarica_merkle_path()
        except Exception as e:
            logger.exception("[ERRORE] Errore nello scaricamento dei Merkle Path da IPFS")
            risultato["stato_elaborazione"] = f"Errore durante lo scaricamento dei Merkle Path da IPFS: {e}"
            return risultato

        # Fase 4: verifica di struttura
        mancanti, aggiunti = self._verifica_struttura()
        risultato["anomalie_struttura"] = StrutturaVerifica(
            id_mancanti=mancanti,
            id_aggiunti=aggiunti
        )

        # Fase 5: verifica delle foglie
        risultato_verifica : DettagliVerifica = self._verifica_foglie_con_path()
        risultato["dettagli"].update(risultato_verifica)

        # Conteggio anomalie
        #gli id aggiunti compaiono già dentro anomalie in quanto manca il merkle path per quel specifico ID
        anomalie_strutturali = len(mancanti)
        anomalie_hash = len(risultato_verifica["anomalie"])
        risultato["numero_anomalie"] = anomalie_strutturali + anomalie_hash

        # Esito globale
        risultato["esito_globale"] = risultato["numero_anomalie"] == 0
        risultato["stato_elaborazione"] = "Completato"

        logger.info(f"Verifica completata – esito: {risultato['esito_globale']}")

        return risultato

    @staticmethod
    def recupera_metadata_anomalie(risultati: RisultatoVerifica) -> str:
        """
        Recupera i metadati relativi alle anomalie dal cloud e restituisce una stringa formattata.
        Se il batch è anomalo (prima foglia), viene subito analizzato.
        Le misurazioni vengono raccolte in blocco.
        """
        output = ["\n=== METADATI DELLE FOGLIE ALTERATE ==="]
        id_misurazioni_anomale = []

        anomalie = risultati["dettagli"]["anomalie"]
        if not anomalie:
            output.append("✅ Nessuna anomalia da analizzare.")
            return "\n".join(output)

        # 1. Se il batch è anomalo, è la prima foglia: lo verifichiamo subito
        prima = anomalie[0]
        if prima["tipo"] == "batch":
            id_batch = prima["id"]
            output.append(f"\n--- BATCH ID {id_batch} ---")
            try:
                metadata_batch : MetaDatiBatch = richiedi_metadata_batch(id_batch)
                output.append(metadata_batch.to_json())
            except ValueError as e:
                output.append(f"❌ Errore nel recupero dei metadati per batch ID {id_batch}: {e}")
            anomalie = anomalie[1:]  # rimuovi il primo elemento (batch) per il resto del ciclo

        # 2. Raccogliamo tutte le misurazioni anomale
        for record in anomalie:
            #controllo di sicurezza
            if record["tipo"] == "misurazione":
                #aggrego tutti gli id di misurazioni
                id_misurazioni_anomale.append(record["id"])

        #se la lista non è vuota
        if id_misurazioni_anomale:
            output.append(f"\n--- MISURAZIONI ANOMALE ({len(id_misurazioni_anomale)} ID) ---")
            try:
                metadata_misurazioni : List[MetaDatiMisurazione] = (
                    richiedi_metadata_misurazioni(id_misurazioni_anomale))
                for mis in metadata_misurazioni:
                    output.append(f"\n>> ID {mis.id_misurazione}")
                    output.append(mis.to_json())
            except ValueError as e:
                output.append(f"❌ Errore nel recupero dei metadata delle misurazioni: {e}")

        return "\n".join(output)

