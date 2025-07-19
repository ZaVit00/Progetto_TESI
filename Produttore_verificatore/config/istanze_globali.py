import logging

from Produttore.database.gestore_db import GestoreDatabase

#istanza del connettore del database sqlite del produttore in sola lettura
gestore_db = GestoreDatabase(sola_lettura=True)

# Configurazione globale del logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] [%(name)s] %(message)s'
)
