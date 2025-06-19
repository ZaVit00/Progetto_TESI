import logging
from Classi_comuni.entita.modelli_dati import DatiPayload, DatiMisurazione, DatiBatch
from Verificatore.api_client.api_cloud_client import richiedi_payload_batch
from Verificatore.verifica.verificatore_utils import verifica_foglie_con_path, carica_paths_da_json_string
from Verificatore.api_client.ipfs_client import  ottieni_file_da_ipfs
from merkle_tree import PathCompatto
from Classi_comuni.costruttore_payload import CostruttorePayload

# Configurazione globale del logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] [%(name)s] %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    id_batch = 3  # test con un id_batch 3 prefissato
    merkle_root_attesa = "1e671ae536084cffe0fdc0debab008589f245a5d85f7a0849be9435aa97655e4"
    cid_merkle_path = "QmXGKMZrF78seRxtLjGxPeYqUhVFxiwFXQ4L9gPotGyWqz"
    #1.Richiesta al cloud. Invio GET /batch?id=? con API key; Ricezione di DatiPayload come dizionario
    payload: DatiPayload = richiedi_payload_batch(id_batch)
    #2. Ricostruzione delle foglie del Merkle Tree
    mappa_id_hash : dict[int, str] = CostruttorePayload.ricostruisci_hash_foglie(payload)

    #3. Recupero Merkle Path da IPFS. Scaricamento file JSON da IPFS usando il CID noto
    #rappresentazione sottoforma di stringa dei merkle paths
    str_merkle_paths = ottieni_file_da_ipfs(cid_merkle_path) #DA GESTIRE UNA ECCEZIONE
    merkle_paths : dict[int, PathCompatto] = carica_paths_da_json_string(str_merkle_paths)

    # 4. Verifica dell’integrità delle singole misurazioni usando i Merkle Path
    risultati_verifica = verifica_foglie_con_path(mappa_id_hash, merkle_root_attesa, merkle_paths)


if __name__ == "__main__":
    main()
