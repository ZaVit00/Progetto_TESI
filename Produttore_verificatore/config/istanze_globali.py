"""
istanza del connettore del database sqlite "dati_nodo_fog.sqlite"
del produttore in sola lettura. Il produttore verificatore è l'unico che può accedere
a questo database.
"""
from Produttore.database.gestore_db import GestoreDatabase
gestore_db = GestoreDatabase(sola_lettura=True)
