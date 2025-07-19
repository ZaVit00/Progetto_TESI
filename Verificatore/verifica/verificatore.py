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

# --- Tipi ausiliari per la verifica --- #

# Dettagli relativi a una singola anomalia di integrità rilevata durante la verifica.
# Ogni anomalia si riferisce a un ID (es. misurazione o batch), con specifica del tipo di elemento,
# esito della verifica (True = integro, False = alterato), presenza di una modifica strutturale,
# ed eventuali note esplicative.
class DettagliVerifica(TypedDict):
    id : int                           # ID univoco dell'elemento verificato (misurazione/batch)
    tipo : str                         # Tipo di elemento ("batch", "misurazione", ecc.)
    esito : bool                       # Esito della verifica: True se integro, False se alterato
    modifica_strutturale : bool        # True se la struttura risulta compromessa (es. hash alterato, path errato)
    note : str                         # Nota esplicativa

# Risultato del confronto tra la struttura attesa da IPFS e quella ricevuta dal cloud
# basandoci unicamente sugli id. Nota bene: la tupla del batch è sempre mappata con ID logico 0
# in questo modo precede sempre le misurazioni quando effettuiamo l'ordinamento.
# Elenca gli ID mancanti (presenti nell'albero originale ma assenti nei dati ricevuti)
# e quelli aggiunti (presenti nei dati ricevuti ma non nell'albero originale).
class StrutturaVerifica(TypedDict):
    id_mancanti: list[int]             # Lista degli ID previsti ma non presenti nei dati ricevuti
    id_aggiunti: list[int]             # Lista degli ID presenti ma non previsti (anomalia strutturale)

# Risultato complessivo della verifica di un batch.
# Riassume il numero di anomalie rilevate, distinguendo tra anomalie di integrità e strutturali,
# e fornisce il dettaglio delle anomalie e delle differenze strutturali.
class RisultatoVerifica(TypedDict):
    id_batch : int                                     # ID del batch verificato
    numero_anomalie_integrita: int                     # Numero di elementi alterati nei contenuti (hash errati)
    numero_anomalie_strutturali : int                  # Numero totale di elementi mancanti o aggiunti
    anomalie_integrita: list[DettagliVerifica]         # Dettagli sulle anomalie rilevate nei contenuti
    anomalie_strutturali: StrutturaVerifica            # Dettagli sulle differenze strutturali del batch


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
        # STEP 1: Richiesta al cloud dei dati da verificare
        # Si recupera la mappa {id → hash} contenente tutti gli hash delle foglie del Merkle Tree
        # (cioè batch e misurazioni) registrati dal cloud. Questi hash rappresentano lo stato corrente
        # dei dati e saranno confrontati con la Merkle Root immutabile.
        try:
            self._recupera_dati_batch_cloud()
        except Exception as e:
            logger.exception("[ERRORE] Errore nella richiesta HTTP al cloud provider")
            raise RuntimeError(f"Errore nel recupero dei dati dal cloud: {e}")

        # STEP 2: Lettura dalla blockchain della Merkle Root salvata e del CID IPFS
        # Viene interrogata la blockchain per ottenere:
        # - la Merkle Root originale salvata on-chain
        # - il CID che punta al file JSON contenente i Merkle Path su IPFS
        try:
            self._recupera_root_e_cid_blockchain()
        except Exception as e:
            logger.exception("[ERRORE] Errore nel recupero della root e del CID da blockchain")
            raise RuntimeError(f"Errore nel recupero dei metadati blockchain: {e}")

        # STEP 2b: Controllo di integrità sui metadati ottenuti
        # Se non sono stati recuperati né Merkle Root né CID, si tratta di un errore critico.
        # Il batch potrebbe non essere mai stato registrato, oppure i metadati sono stati corrotti.
        if not self.merkle_root_immutabile or not self.cid_merkle_path:
            raise ValueError(
                f"❌ Batch ID {self.id_batch}: struttura compromessa. "
                f"Merkle root o CID assenti per il batch indicato — possibile manomissione o batch non registrato."
            )

        # STEP 3: Download del file Merkle Path da IPFS tramite CID
        # Viene scaricato il file JSON da IPFS contenente i Merkle Path relativi alle foglie,
        # ovvero le informazioni necessarie per calcolare la root a partire da ciascun hash.
        try:
            self._scarica_merkle_path_ipfs()
        except Exception as e:
            logger.exception("[ERRORE] Errore nello scaricamento dei Merkle Path da IPFS")
            raise RuntimeError(f"Errore nel download da IPFS: {e}") from e

        # STEP 4: Verifica della struttura
        # Confronta gli ID delle foglie ricevuti dal cloud con quelli presenti nei Merkle Path da IPFS.
        # L'obiettivo è rilevare eventuali manomissioni nella struttura del batch:
        # - ID mancanti (previsti da IPFS ma assenti nel cloud)
        # - ID aggiunti (presenti nel cloud ma non previsti)
        id_mancanti, id_aggiunti = self._verifica_struttura()
        self.risultato["anomalie_strutturali"] = StrutturaVerifica(
            id_mancanti=id_mancanti,
            id_aggiunti=id_aggiunti
        )

        # STEP 5: Verifica dell'integrità delle singole foglie
        # Per ogni foglia (batch o misurazione), verifica se l'hash e il Merkle Path conducono
        # correttamente alla Merkle Root. Se l'esito è negativo, viene registrata un'anomalia.
        foglie_anomale = self._verifica_foglie_con_path()
        self.risultato["anomalie_integrita"] = foglie_anomale

        # CONSIDERAZIONI IMPORTANTI:
        # Gli ID aggiunti dal cloud, per i quali non esiste un Merkle Path in IPFS,
        # non possono essere verificati → sono considerati anomalie strutturali.
        # Questo include anche i casi in cui delle misurazioni sono state assegnate manualmente
        # a un batch esistente (manomissione di id_batch), poiché il loro id non compare in IPFS

        # STEP 6: Aggiornamento finale del report
        # Si calcola il numero totale di anomalie rilevate (di integrità e strutturali).
        self.risultato["numero_anomalie_integrita"] = len(self.risultato["anomalie_integrita"])
        self.risultato["numero_anomalie_strutturali"] = len(id_mancanti) + len(id_aggiunti)

        # STEP 7: Serializzazione del risultato finale in formato JSON
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
        # anomalie strutturali (mancanza di merkle path da ipfs).
        # Quando l'id della misurazione è stata alterato
        # siamo impossibilitati nel proseguo di stabilire cosa è cambiato perché non sappiamo effettivamente a
        # quale misurazione ora corrisponde.Di conseguenza possiamo solo constatare la modifica strutturale.
        anomalie_misurazioni = [
            record for record in anomalie
            if record["tipo"] == "misurazione" and not record["modifica_strutturale"]]
        # Estrai gli ID delle misurazioni alterate
        id_alterati = [record["id"] for record in anomalie_misurazioni]
        return id_alterati

    # --- METODI PER VISUALIZZARE I METADATI DEL BATCH E DELLE MISURAZIONI EVENTUALMENTE COMPROMESSI --- #

    def _recupera_metadati_batch(self) -> MetaDatiBatch:
        """
        Recupera i metadati completi del batch identificato da `self.id_batch`.
        Questo metodo viene invocato solo se il batch risulta alterato (foglia ID 0 non integra),
        al fine di ispezionarne il contenuto originario e confrontarlo con quello ricevuto.
        """
        return richiedi_metadata_batch(self.id_batch)

    def _recupera_metadati_misurazione_sensore(self) -> list[MetaDatiMisurazioneSensore]:
        """
        Recupera i metadati completi delle sole misurazioni alterate.
        Utilizza il metodo `ottieni_id_misurazioni_alterate()` per filtrare gli ID delle
        misurazioni che risultano effettivamente compromesse **senza** errori strutturali.

        Restituisce una lista di oggetti `MetaDatiMisurazioneSensore`, ciascuno dei quali
        contiene sia i metadati della misurazione che quelli del sensore che l'ha generata.
        """
        id_list = self.ottieni_id_misurazioni_alterate()
        return richiedi_metadata_misurazione_sensore(id_list)

    def recupera_metadata_anomalie(self) -> str:
        # TODO DA CAMBIARE VISUALIZZAZIONE OUTPUT
        """
        Recupera i metadati del batch e delle misurazioni alterate, se presenti.
        Restituisce una stringa JSON serializzata con i risultati.
        """
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