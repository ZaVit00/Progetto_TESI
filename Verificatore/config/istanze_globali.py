#istanza del lettore blockchain
from costanti_comuni import PROVIDER_BLOCKCHAIN_URL
from gestore_blockchain import inizializza_configurazione_blockchain, LettoreBlockchain

abi, indirizzo = inizializza_configurazione_blockchain()
lettore_blockchain = LettoreBlockchain(PROVIDER_BLOCKCHAIN_URL, abi, indirizzo)