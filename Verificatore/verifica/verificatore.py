import logging
from typing import TypedDict, List
from Classi_comuni.merkle_tree import PathCompatto, MerkleTree
from Verificatore.api_client.api_cloud import richiedi_mappa_id_hash_batch, richiedi_metadata_batch, \
    richiedi_metadata_misurazione_sensore
from Verificatore.api_client.ipfs_client import ottieni_file_da_ipfs
from Verificatore.verifica.verificatore_utils import carica_merkle_paths_da_json_string
from modelli_metadati import MetaDatiBatch, MetaDatiMisurazioneSensore

logger = logging.getLogger(__name__)

# --- Tipi per l'output della verifica ---
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
    numero_anomalie: int
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
            "numero_anomalie": 0,
            "anomalie_integrita": [],
            "anomalie_strutturali": {"id_mancanti": [], "id_aggiunti": []},
        }

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

    def esegui_verifica_completa(self):

        # 1. Recupero dati hashati dal cloud
        try:
            self._recupera_dati()
        except Exception as e:
            logger.exception("[ERRORE] Errore nella richiesta HTTP al cloud provider")
            raise RuntimeError(f"Errore nel recupero dei dati dal cloud: {e}") from e

        # 2. Recupero root e CID da blockchain (placeholder)
        try:
            self._recupera_root_e_cid()
        except Exception as e:
            logger.exception("[ERRORE] Errore nel recupero della root e del CID da blockchain")
            raise RuntimeError(f"Errore nel recupero dei metadati blockchain: {e}") from e

        # 3. Scaricamento Merkle Path da IPFS
        try:
            self._scarica_merkle_path()
        except Exception as e:
            logger.exception("[ERRORE] Errore nello scaricamento dei Merkle Path da IPFS")
            raise RuntimeError(f"Errore nel download da IPFS: {e}") from e

        # Fase 4: verifica di struttura
        id_mancanti, id_aggiunti = self._verifica_struttura()
        self.risultato["anomalie_strutturali"] = StrutturaVerifica(
            id_mancanti=id_mancanti,
            id_aggiunti=id_aggiunti
        )

        # Fase 5: verifica delle foglie
        foglie_anomale = self._verifica_foglie_con_path()
        self.risultato["anomalie_integrita"] = foglie_anomale

        # Conteggio anomalie
        #gli id aggiunti compaiono già dentro anomalie in quanto manca il merkle path per quel specifico ID
        anomalie_strutturali = len(id_mancanti)
        anomalie_integrita = len(self.risultato["anomalie_integrita"])
        self.risultato["numero_anomalie"] = anomalie_strutturali + anomalie_integrita

    def ottieni_numero_anomalie(self) -> int:
        return self.risultato["numero_anomalie"]

    def ottieni_esito_globale(self) -> bool:
        return self.risultato["numero_anomalie"] == 0

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

        # Filtra solo quelle relative alle misurazioni
        anomalie_misurazioni = [
            record for record in anomalie
            if record["tipo"] == "misurazione" and not record["modifica_strutturale"]]
        # Estrai gli ID delle misurazioni alterate
        id_alterati = [record["id"] for record in anomalie_misurazioni]
        return id_alterati





    @staticmethod
    def recupera_metadata_anomalie(risultati: RisultatoVerifica) -> str:

        # TODO DA FIXARE NON PIU FUNZIONANTE

        """
        Recupera i metadati relativi alle anomalie dal cloud e restituisce una stringa formattata.
        Se il batch è anomalo (prima foglia), viene subito analizzato.
        Le misurazioni vengono raccolte in blocco.
        """
        output = ["\n=== METADATI DELLE FOGLIE ALTERATE ==="]
        id_misurazioni_anomale = []

        anomalie = risultati["dettagli"]["anomalie_integrita"]
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
                metadata_mis_sens : List[MetaDatiMisurazioneSensore] = (
                    richiedi_metadata_misurazione_sensore(id_misurazioni_anomale))
                for mis in metadata_mis_sens:
                    output.append(f"\n>> ID {mis.metadati_misurazione.id_misurazione}")
                    output.append(mis.to_json())
            except ValueError as e:
                output.append(f"❌ Errore nel recupero dei metadata delle misurazioni: {e}")

        return "\n".join(output)

