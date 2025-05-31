select m.id_misurazione, m.id_batch, m.timestamp, m.dati
from batch inner join misurazione as m on batch.id_batch = m.id_batch;