from Produttore.database.gestore_db import GestoreDatabase
#istanza del connettore del database sqlite del produttore in sola lettura
gestore_db = GestoreDatabase(sola_lettura=True)