import logging
from Produttore.database.gestore_db import GestoreDatabaseProduttore
from costanti_comuni import PROVIDER_BLOCKCHAIN_URL
from costanti_produttore import PRIVATE_KEY_BLOCKCHAIN, ACCOUNT_ADDRESS_BLOCKCHAIN
from gestore_blockchain import inizializza_configurazione_blockchain, ScrittoreBlockchain

#istanza singleton globale al progetto Produttore dello scrittore blockchain
abi, indirizzo = inizializza_configurazione_blockchain()
scrittore_blockchain = ScrittoreBlockchain(PROVIDER_BLOCKCHAIN_URL, abi, indirizzo, ACCOUNT_ADDRESS_BLOCKCHAIN,
                                           PRIVATE_KEY_BLOCKCHAIN)

# Istanza globale del database del produttore (SQLITE)
gestore_db = GestoreDatabaseProduttore()

