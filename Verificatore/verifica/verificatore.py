import logging
from Classi_comuni.entita.modelli_dati import DatiPayload, DatiMisurazione, DatiBatch
from Verificatore.api_client.api_cloud_client import richiedi_payload_batch
from Verificatore.verifica.verificatore_utils import verifica_foglie_con_path, carica_paths_da_json_string
from Verificatore.api_client.ipfs_client import  ottieni_file_da_ipfs
from costanti_comuni import ID_BATCH_LOGICO
from merkle_tree import PathCompatto
from Classi_comuni.costruttore_payload import CostruttorePayload

# Configurazione globale del logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] [%(name)s] %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    id_batch = 7 # test con un id_batch 3 prefissato
    merkle_root_attesa = "f92f40f5ef1645bc064229eb4523d6a5dce1aff5eb8b4c3deb48c3d6a804bc1e"
    cid_merkle_path = "QmXRT2yApnWBwp7Z7PW637RhKn3GLeWXgB3tUtHWK77mr8"
    #1.Richiesta al cloud. Invio GET /batch?id=? con API key; Ricezione di DatiPayload come dizionario
    payload: DatiPayload = richiedi_payload_batch(id_batch)
    id_correnti = {riga.id_misurazione for riga in payload.misurazioni}
    #2. Ricostruzione delle foglie del Merkle Tree
    mappa_id_hash : dict[int, str] = CostruttorePayload.ricostruisci_hash_foglie(payload)

    #3. Recupero Merkle Path da IPFS. Scaricamento file JSON da IPFS usando il CID noto
    #rappresentazione sottoforma di stringa dei merkle paths
    str_merkle_paths = ottieni_file_da_ipfs(cid_merkle_path) #DA GESTIRE UNA ECCEZIONE
    merkle_paths : dict[int, PathCompatto] = carica_paths_da_json_string(str_merkle_paths)
    # Confronto ID
    # Rimuovi l'ID 0 (batch) dall'elenco originale
    id_originali = set(merkle_paths.keys()) - {ID_BATCH_LOGICO}
    id_correnti = {riga.id_misurazione for riga in payload.misurazioni}  # Quelli letti dal DB
    if id_originali != id_correnti:
        ids_mancanti = id_originali - id_correnti  # C'erano in origine, ma non ci sono più
        ids_aggiunti = id_correnti - id_originali  # Non c'erano in origine, ma sono stati aggiunti

        if ids_mancanti:
            print(f"⚠️ ID mancanti rispetto alla struttura originale: {sorted(ids_mancanti)}")
        if ids_aggiunti:
            print(f"⚠️ ID aggiunti (non presenti nella struttura originale): {sorted(ids_aggiunti)}")

        print("❌ Struttura batch manomessa.")
    else:
        print("✅ ID coerenti: struttura non alterata")

    # 4. Verifica dell’integrità delle singole misurazioni usando i Merkle Path
    verifica_foglie_con_path(mappa_id_hash, merkle_root_attesa, merkle_paths)


if __name__ == "__main__":
    main()
