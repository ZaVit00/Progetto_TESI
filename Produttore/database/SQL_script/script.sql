/* script per ricostruire tutto il record da:
   quale sensore ha eseguito la misurazione_in_ingresso
   le informazioni della misurazione_in_ingresso
   le informazioni sul batch di appartenenza della misurazione_in_ingresso
 */
select m.id_misurazione,m.timestamp,b.id_batch,b.completato, b.merkle_root,m.dati
from batch as b inner join misurazione as m on b.id_batch = m.id_batch;

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
    batch.merkle_root,
    batch.conferma_ricezione,
    COUNT(*) AS num_misurazioni
FROM
    batch
INNER JOIN
    misurazione AS m ON batch.id_batch = m.id_batch
GROUP BY
    batch.id_batch;