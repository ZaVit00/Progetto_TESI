from costanti_comuni import PROVIDER_URL
from costanti_produttore import PRIVATE_KEY_BLOCKCHAIN, ACCOUNT_ADDRESS_BLOCKCHAIN
from gestore_blockchain import inizializza_configurazione_blockchain, ScrittoreBlockchain

abi, indirizzo = inizializza_configurazione_blockchain()
scrittore_blockchain = ScrittoreBlockchain(PROVIDER_URL, abi, indirizzo, ACCOUNT_ADDRESS_BLOCKCHAIN,
                                           PRIVATE_KEY_BLOCKCHAIN)