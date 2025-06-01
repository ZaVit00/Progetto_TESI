/* script per ricostruire tutto il record da:
   quale sensore ha eseguito la misurazione
   le informazioni della misurazione
   le informazioni sul batch di appartenenza della misurazione
 */
select m.id_misurazione, m.id_batch, m.timestamp, m.dati
from batch inner join misurazione as m on batch.id_batch = m.id_batch;

/*
 Effettua il drop di tutte le tabelle
 (serve per distruggere lo schema)
 */
DROP TABLE misurazione;
DROP TABLE sensore;
DROP TABLE batch;

/*
 Elimina tutti i dati dalle tabelle
 e nelle tabelle di sqLite per resettare
 autoincrement delle primary key
 senza condizioni imposte
 */
DELETE FROM misurazione;
DELETE FROM batch;
DELETE FROM sensore;
DELETE FROM sqlite_sequence WHERE name='misurazione';
DELETE FROM sqlite_sequence WHERE name='batch';

/* conteggio delle misurazioni
   per batch*/
SELECT
    batch.id_batch,
    batch.timestamp_creazione,
    batch.completato,
    COUNT(*) AS num_misurazioni
FROM
    batch
INNER JOIN
    misurazione AS m ON batch.id_batch = m.id_batch
GROUP BY
    batch.id_batch;