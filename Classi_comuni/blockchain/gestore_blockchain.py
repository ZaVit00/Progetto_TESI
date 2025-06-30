import logging

from web3 import Web3
from web3.exceptions import ContractLogicError

from costanti_comuni import PERCORSO_ABI, PERCORSO_INDIRIZZO_CONTRATTO
from file_utils import verifica_esistenza_file, carica_json, carica_file_testuale

# Logger configurato per questo modulo
logger = logging.getLogger(__name__)
# ========== FUNZIONI DI SUPPORTO NELLO STESSO FILE PER COMODITA ==========

def _carica_abi() -> dict:
    """
    Carica l'ABI del contratto da file JSON.
    """
    if not verifica_esistenza_file(PERCORSO_ABI):
        raise ValueError("File ABI mancante o vuoto.")
    logger.debug("✅ ABI caricato correttamente da file.")
    return carica_json(PERCORSO_ABI)


def _carica_indirizzo_contratto() -> str:
    """
    Carica l'indirizzo del contratto Ethereum da file.
    """
    if not verifica_esistenza_file(PERCORSO_INDIRIZZO_CONTRATTO):
        raise ValueError("File indirizzo contratto mancante o vuoto.")
    indirizzo = carica_file_testuale(PERCORSO_INDIRIZZO_CONTRATTO).strip()
    logger.debug(f"✅ Indirizzo contratto caricato: {indirizzo}")
    return indirizzo


def inizializza_configurazione_blockchain() -> tuple[dict, str]:
    """
    Carica ABI e indirizzo del contratto in un'unica chiamata.
    :return: Tuple (abi, indirizzo_contratto)
    """
    abi = _carica_abi()
    indirizzo = _carica_indirizzo_contratto()
    return abi, indirizzo


# ========== CLASSI PRINCIPALI ==========

class LettoreBlockchain:
    """
    Classe base per accedere in sola lettura al contratto smart su blockchain.
    IL Verificatore accedere sempre in sola lettura
    """

    def __init__(self, provider_url: str, abi: dict, indirizzo_contratto: str):
        self.web3 = Web3(Web3.HTTPProvider(provider_url))
        if not self.web3.is_connected():
            logger.error("❌ Connessione alla blockchain fallita.")
            raise ConnectionError("Impossibile connettersi alla blockchain.")

        logger.info("🔗 Connessione alla blockchain riuscita.")
        self.abi = abi
        self.indirizzo_contratto = self.web3.to_checksum_address(indirizzo_contratto)
        self.contract = self.web3.eth.contract(address=self.indirizzo_contratto, abi=self.abi)
        logger.debug("✅ Contratto smart caricato correttamente.")

    def leggi_valore(self, id_batch: int) -> tuple[str, str]:
        """
        Legge il batch per id_batch e restituisce Merkle Root e CID IPFS.
        """
        logger.info(f"📖 Lettura batch ID {id_batch} dalla blockchain...")
        try:
            dati = self.contract.functions.getBatch(id_batch).call()
            logger.debug(f"✅ Batch letto: MerkleRoot={dati[0]}, CID={dati[1]}")
            return dati
        except Exception as e:
            logger.error(f"❌ Errore durante la lettura del batch {id_batch}: {e}")
            raise RuntimeError(f"Errore durante la lettura del batch {id_batch}: {e}")


class ScrittoreBlockchain(LettoreBlockchain):
    """
    Estende LettoreBlockchain per consentire scritture.
    IL produttore accede sia in scrittura che in lettura
    """

    def __init__(self, provider_url: str, abi: dict, indirizzo_contratto: str, account: str, private_key: str):
        super().__init__(provider_url, abi, indirizzo_contratto)
        self.account = self.web3.to_checksum_address(account)
        self.private_key = private_key
        logger.debug("ScrittoreBlockchain inizializzato.")

    def scrivi_valore(self, id_batch: int, merkle_root: str, cid_ipfs: str) -> str:
        """
        Scrive un nuovo batch nella blockchain.
        """
        logger.info(f"📝 Scrittura batch ID {id_batch} nella blockchain...")

        try:
            nonce = self.web3.eth.get_transaction_count(self.account)
            tx = self.contract.functions.salvaBatch(id_batch, merkle_root, cid_ipfs).build_transaction({
                "from": self.account,
                "nonce": nonce,
                "gas": 300000,
                "gasPrice": self.web3.to_wei("20", "gwei")
            })

            signed_tx = self.web3.eth.account.sign_transaction(tx, self.private_key)
            tx_hash = self.web3.eth.send_raw_transaction(signed_tx.raw_transaction)
            logger.info(f"✅ Batch scritto correttamente. TX Hash: {tx_hash.hex()}")
            return tx_hash.hex()

        except ContractLogicError as e:
            logger.error(f"❌ Errore logico durante la scrittura (batch già esistente): {e}")
            raise RuntimeError(f"Errore logico durante la scrittura (batch già esistente?): {e}")

        except Exception as e:
            logger.error(f"❌ Errore generico: {e}")
            raise RuntimeError(f"Errore generico durante la scrittura: {e}")
