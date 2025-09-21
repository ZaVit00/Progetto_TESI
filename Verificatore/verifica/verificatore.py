import logging
from typing import List
from Classi_comuni.merkle_tree import PathCompatto, MerkleTree
from Classi_comuni.utils.dict_utils import serializza_dict
from Verificatore.api_client.api_cloud import richiedi_mappa_id_hash_batch, richiedi_metadata_batch, \
    richiedi_metadata_misurazione_sensore
from Verificatore.api_client.ipfs_client import ottieni_file_da_ipfs
from Verificatore.config.istanze_globali import lettore_blockchain
from Verificatore.verifica.verificatore_utils import carica_merkle_paths_da_stringa_json, \
    ottieni_report_metadati_anomalie
from costanti_comuni import TipoServizio
from registro_log import setup_logger
from tipi_verifica import DettagliVerifica, StrutturaVerifica, RisultatoVerifica
from modelli_metadati import MetaDatiBatchPayload, MetaDatiMisurazioneSensorePayload

logger = setup_logger(TipoServizio.VERIFICATORE, module=__name__, level=logging.DEBUG)

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
            "anomalie_integrita": {},
            "anomalie_strutturali": {"id_mancanti": [], "id_aggiunti": []},
        }

    def esegui_verifica_integrita(self) -> RisultatoVerifica:
        # STEP 1: Richiesta al cloud dei dati da verificare
        # Si recupera la mappa {id → hash} contenente tutti gli hash delle foglie associate ad un
        # particolare batch (inteso come raggruppamento di misurazioni) registrati dal cloud.
        # Questi hash rappresentano lo stato corrente dei dati memorizzati dal cloud e
        # saranno confrontati con la Merkle Root immutabile salvata su blockchain.
        # Se viene rilevata una violazione, i dati sono cambiati e siamo in grado di determinare
        # l'anomalia in modo deterministico.
        try:
            self._recupera_dati_batch_cloud()
        except Exception as e:
            logger.exception("[ERRORE] Errore nella richiesta HTTP al cloud provider")
            raise RuntimeError(f"Errore nel recupero dei dati dal cloud: {e}")

        # STEP 2: Lettura dalla blockchain della Merkle Root salvata e del CID IPFS
        # Viene interrogata la blockchain per ottenere:
        # - la Merkle Root originale salvata on-chain
        # - il CID che punta al file JSON contenente i Merkle Path caricato IPFS
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
                f"Merkle root o CID assenti per il batch indicato — possibile manomissione dell'identificativo"
                f"del batch o batch non registrato."
            )

        # STEP 3: Download del file Merkle Path da IPFS tramite CID
        # Viene scaricato il file JSON da IPFS contenente i Merkle Path relativi alle foglie,
        # ovvero le informazioni necessarie per calcolare la prova di integrità per ciascuna
        # foglia.
        try:
            self._scarica_merkle_path_ipfs()
        except Exception as e:
            logger.exception("[ERRORE] Errore nello scaricamento dei Merkle Path da IPFS")
            raise RuntimeError(f"Errore nel download da IPFS: {e}") from e

        """
        STEP 4: Verifica della struttura
        Confronta gli ID delle foglie ricevuti dal cloud con quelli presenti
        nei Merkle Path ottenuti dal file `merkle_paths` caricato su IPFS.
        Obiettivo:
        - rilevare eventuali manomissioni nella struttura del raggruppamento di misurazioni.
        Tipologie di anomalie rilevate:
        - ID Misurazione mancanti → presenti nel file `merkle_paths` ma assenti nella lista di ID ottenuti dal cloud
        - ID Misurazione aggiunti → presenti nella lista di ID forniti dal cloud ma non previsti nella struttura di ID del file `merkle_paths`
        Nota:
        Questo problema riguarda esclusivamente le **misurazioni** e non i batch.
        Infatti i batch vengono mappati internamente, durante la costruzione del Merkle Tree
        e dei Merkle Path, all’ID logico 0.
        """
        id_mancanti, id_aggiunti = self._verifica_struttura()
        self.risultato["anomalie_strutturali"] = StrutturaVerifica(
            id_mancanti=id_mancanti,
            id_aggiunti=id_aggiunti
        )

        # STEP 5: Verifica dell'integrità delle singole foglie
        # Per ogni foglia (batch o misurazion che sia), verifica se l'hash e il Merkle Path conducono
        # correttamente alla Merkle Root immutabile ottenuta da blockchain.
        # Se l'esito è negativo, viene registrata un'anomalia.
        foglie_anomale : dict [int, DettagliVerifica] = self._verifica_foglie_con_path()
        self.risultato["anomalie_integrita"] = foglie_anomale

        # CONSIDERAZIONI IMPORTANTI:
        # Gli ID Misurazione aggiunti dal cloud, per i quali non esiste un Merkle Path in IPFS,
        # non possono essere verificati → sono considerati anomalie strutturali.
        # Questo include anche i casi in cui delle misurazioni sono state assegnate
        # manualmente a un batch esistente (manomissione di id_batch di una determinata misurazione).

        # STEP 6: Aggiornamento finale del report
        # Si calcola il numero totale di anomalie rilevate (di integrità e strutturali).
        self.risultato["numero_anomalie_integrita"] = len(foglie_anomale)
        self.risultato["numero_anomalie_strutturali"] = len(id_mancanti) + len(id_aggiunti)

        # STEP 7: Restituzione dell'oggetto
        return self.risultato

    def _recupera_dati_batch_cloud(self) -> None:
        logger.info(f"Recupero dei dati per il batch ID {self.id_batch}")
        self.mappa_id_hash = richiedi_mappa_id_hash_batch(self.id_batch)
        if not self.mappa_id_hash:
            #Controllo di Errore
            logger.error(f"[RECUPERO DATI BATCH CLOUD] Nessuna mappa id→hash trovata per il batch {self.id_batch}.")
            raise ValueError(
                f"Batch ID {self.id_batch}: nessuna mappatura id→hash trovata "
                f"(batch inesistente o dati corrotti)."
            )


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
        Verifica la coerenza tra gli ID delle misurazioni registrati su file caricato su ipfs
        merkle paths e gli ID misurazioni ottenuti dal cloud. Restituisce due liste:
        - id_mancanti: presenti in IPFS ma assenti nel cloud
        - id_aggiunti: presenti nel cloud ma assenti in IPFS
        """
        ipfs_id_mis = set(self.merkle_paths.keys())
        cloud_id_mis = set(self.mappa_id_hash.keys())
        id_mancanti = sorted(ipfs_id_mis - cloud_id_mis)
        id_aggiunti = sorted(cloud_id_mis - ipfs_id_mis)

        if id_mancanti:
            logger.warning(f"ID mancanti nella struttura: {id_mancanti}")
        if id_aggiunti:
            logger.warning(f"ID aggiunti nella struttura: {id_aggiunti}")

        if id_mancanti or id_aggiunti:
            logger.debug("[ATTENZIONE] Struttura batch manomessa")
        else:
            logger.info("Struttura batch integra")

        return id_mancanti, id_aggiunti

    def _verifica_foglie_con_path(self) -> dict[int, DettagliVerifica]:
        """
        Verifica ogni foglia confrontando il suo hash con la Merkle Root attraverso il Merkle Path.
        Restituisce un dizionario con le anomalie riscontrate, mappate sugli ID corretti:
        - `id_batch` per il batch (foglia 0)
        - `id_misurazione` per le misurazioni
        """
        anomalie : dict[int, DettagliVerifica] = {}

        for foglia_id, foglia_hash in self.mappa_id_hash.items():
            # mappatura vero id del batch con id 0
            chiave_anomalia = self.id_batch if foglia_id == 0 else foglia_id
            tipo = "batch" if foglia_id == 0 else "misurazione"

            #logghiamo tutte le foglie che non sono presenti nel merkle paths
            #con un errore specifico
            if foglia_id not in self.merkle_paths:
                anomalie[chiave_anomalia] = DettagliVerifica(
                    tipo=tipo,
                    esito=False,
                    modifica_strutturale=True,
                    note="[IPFS] Merkle Path mancante"
                )
                logger.error(f"[{tipo.upper()}] ID {chiave_anomalia}: Merkle Path mancante")
                continue #salta il processo di verifica che non sarebbe possibile da eseguire

            # Verifica di integrità
            path_foglia : PathCompatto = self.merkle_paths[foglia_id]
            esito_verifica : bool = MerkleTree.verifica_integrita_foglia(
                foglia_hash, path_foglia, merkle_root_prevista=self.merkle_root_immutabile
            )

            record = DettagliVerifica(
                tipo=tipo,
                esito=esito_verifica,
                modifica_strutturale=False,
                note="nessuna compromissione" if esito_verifica else "ANOMALIA RILEVATA"
            )

            if esito_verifica:
                logger.info(f"[{tipo.upper()}] ID {chiave_anomalia} → ✔ INTEGRO")
            else:
                #aggiornamento della struttura dati contenente le anomalie
                anomalie[chiave_anomalia] = record
                logger.warning(f"[{tipo.upper()}] ID {chiave_anomalia} → ✘ ALTERATO")

        return anomalie

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
        anomalie: dict[int, DettagliVerifica] = self.risultato["anomalie_integrita"]
        record = anomalie.get(self.id_batch, 0)

        return bool(record) and record["tipo"] == "batch" and not record["esito"]

    def misurazioni_alterate(self) -> bool:
        """
        Restituisce True se ALMENO (any) una foglia di tipo 'misurazione' risulta alterata.
        """
        anomalie: dict[int, DettagliVerifica] = self.risultato["anomalie_integrita"]
        return any(record["tipo"] == "misurazione" for record in anomalie.values())

    def ottieni_id_misurazioni_alterate(self) -> list[int]:
        """
        Restituisce una lista di ID delle misurazioni alterate (non strutturalmente).
        Lancia un'eccezione se nessuna misurazione risulta alterata.

        Le misurazioni alterate sono quelle:
        - con tipo 'misurazione'
        - che NON presentano una modifica strutturale (cioè il Merkle Path è valido ma il contenuto è stato modificato)
        """
        if not self.misurazioni_alterate():
            raise ValueError("Nessuna misurazione risulta alterata.")

        anomalie: dict[int, DettagliVerifica] = self.risultato["anomalie_integrita"]

        # Filtra e restituisce solo gli ID con tipo 'misurazione' e modifica NON strutturale
        id_alterati = [
            id_misurazione for id_misurazione, record in anomalie.items()
            if record["tipo"] == "misurazione" and not record["modifica_strutturale"]
        ]

        return id_alterati

    # --- METODI PER VISUALIZZARE I METADATI DEL BATCH E DELLE MISURAZIONI EVENTUALMENTE COMPROMESSI --- #

    def _recupera_metadati_batch(self) -> MetaDatiBatchPayload:
        """
        Recupera i metadati completi del batch identificato da `self.id_batch`.
        Questo metodo viene invocato solo se il batch risulta alterato (foglia ID 0 non integra),
        al fine di ispezionarne il contenuto originario e confrontarlo con quello ricevuto.
        """
        return richiedi_metadata_batch(self.id_batch)

    def _recupera_metadati_misurazione_sensore(self) -> list[MetaDatiMisurazioneSensorePayload]:
        """
        Recupera i metadati completi delle sole misurazioni alterate.
        Utilizza il metodo `ottieni_id_misurazioni_alterate()` per filtrare gli ID delle
        misurazioni che risultano effettivamente compromesse **senza** errori strutturali.

        Restituisce una lista di oggetti `MetaDatiMisurazioneSensorePayload`, ciascuno dei quali
        contiene sia i metadati della misurazione che quelli del sensore che l'ha generata.
        """
        id_list = self.ottieni_id_misurazioni_alterate()
        return richiedi_metadata_misurazione_sensore(id_list)

    def _recupera_metadati_anomalie(self) -> dict:
        """
        Recupera i metadati del batch e delle misurazioni alterate, se presenti.
        Restituisce un oggetto RisultatoMetadatiAnomalie
        """
        metadati_anomalie: dict = {}

        # Recupera i metadati del batch, se alterato
        if self.batch_alterato():
            try:
                metadati_batch = self._recupera_metadati_batch().model_dump()
                metadati_anomalie["metadata_batch"] = metadati_batch
            except Exception as e:
                raise ValueError(f"Errore nel recupero dei metadati batch ID {self.id_batch}: {e}")

        # Recupera i metadati delle misurazioni, se alterate
        if self.misurazioni_alterate():
            try:
                metadati_mis_sens: List[MetaDatiMisurazioneSensorePayload] = self._recupera_metadati_misurazione_sensore()
                # Costruisci il dizionario con chiave = id_misurazione, valore = oggetto MetaDatiMisurazioneSensorePayload
                metadata_dict = {
                    m.metadati_misurazione.id_misurazione: m.to_dict()
                    for m in metadati_mis_sens
                }
                metadati_anomalie["metadata_misurazioni"] = metadata_dict
            except Exception as e:
                raise ValueError(f"Errore nel recupero dei metadati misurazioni: {e}")

        return metadati_anomalie

    def ottieni_output_metadati(self) -> tuple[str, str]:
        """Restituisce: (report_utente, json_serializzato)"""
        metadati_anomalie: dict = self._recupera_metadati_anomalie()
        return (
            ottieni_report_metadati_anomalie(metadati_anomalie),
            serializza_dict(metadati_anomalie),
        )

    def ottieni_output_differenze(self) -> tuple[str, str]:
        """Versione base: non restituisce differenze per classe Verificatore"""
        return "", ""
