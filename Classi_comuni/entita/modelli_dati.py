from typing import Dict, List
from pydantic import Field
from Classi_comuni.utils.dict_utils import canonizza_dict, serializza_dict
from modelli_astratti import ModelliHashabili


class DatiSensore(ModelliHashabili):
    """
    Modello che rappresenta i dati di un sensore memorizzati nel sistema.
    Attenzione: questa classe è distinta dalla classe `DatiSensoreInIngresso`, che viene usata
    solo durante la fase di registrazione iniziale del sensore presso il fog node (produttore)

    In particolare:
    - `DatiSensoreInIngresso` contiene anche la frequenza di invio dei dati (frequenza_hz),
      necessaria per il calcolo dinamico della soglia di batch, ma non trasmessa al cloud e non
      coinvolta nel processo di calcolo del merkle tree e quindi mantenuta solo internamente nel
      database del produttore.

    - `DatiSensore` rappresenta il modello persistente e condivisibile dei dati del sensore,
      privo di informazioni locali interne (come la frequenza) e che viene utilizzato per serializzare,
      salvare e trasmettere i dati verso il cloud provider.
    """
    id_sensore: str = Field(..., description="Identificatore del sensore."
                                             "Deve essere nel formato JOY001, TEMP042, HUM123 ecc.")
    descrizione: str = Field(..., description="Descrizione testuale del sensore.")
    tipo: str = Field(
        default="",
        description="Tipo del sensore (es. joystick, temperatura, umidità, pressione)."
    )


class DatiMisurazione(ModelliHashabili):
    """
    Rappresenta una singola misurazione arricchita con metadati interni, generata da un sensore.

    Questa classe differisce da `DatiMisurazioneInIngresso`, che rappresenta il dato grezzo
    ricevuto dal fog node (produttore) nella rete interna.

    Il processo di elaborazione interno al fog node arricchisce la misurazione con informazioni aggiuntive,
    necessarie per la tracciabilità, la gestione in batch e la verifica dell’integrità.
    In particolare, vengono aggiunti:
    - `id_misurazione`: identificativo univoco della misurazione, assegnato dal fog node internamento con un campo
                        autoincrement
    - `id_batch`: identificativo del batch di appartenenza, per raggruppare le misurazioni;
    - `timestamp`: data e ora di ricezione/elaborazione.

    Questi dati, o volendo metadati, non sono presenti nella misurazione in ingresso che
    non deve essere a conoscenza
    dello schema del database (`DatiMisurazioneInIngresso`).
    Questi dati aggiunti dal fog node sono essenziali per il funzionamento del sistema anti-manomissione
    e per la successiva trasmissione verso il cloud provider.
    """
    id_misurazione: int = Field(..., title="ID Misurazione", description="Identificativo univoco della misurazione")
    id_sensore: str = Field(..., description="Identificativo del sensore che ha generato la misurazione")
    timestamp: str = Field(..., description="Data e ora della misurazione")
    id_batch: int = Field(..., description="Identificativo del batch a cui appartiene la misurazione")
    dati: Dict = Field(
        ...,
        title="Dati rilevati",
        description=(
            "Dati effettivi inviati dal sensore, organizzati come dizionario.\n"
            "Ogni sensore invia i propri valori sotto forma di JSON (cioè un oggetto chiave-valore), "
            "che viene mantenuto integro all'interno di questo campo.\n"
            "Questo approccio consente di gestire in modo uniforme diversi tipi di misurazioni, "
            "incapsulando la parte variabile in un unico campo strutturato."
        )
    )

    def to_json(self) -> str:
        """
        Override del metodo implementato nella classe padre ModelliHashabili.
        Applica una canonizzazione (omogeneità tra valori)
        al campo `dati` per garantire coerenza di serializzazione
        tra database diversi come SQLite e PostgreSQL.
       """
        dump = self.model_dump()

        dump["dati"] = canonizza_dict(self.dati)

        return serializza_dict(dump)


class DatiBatch(ModelliHashabili):
    """
    Rappresenta i dati di un batch.
    """
    id_batch: int = Field(..., title="ID Batch", description="Identificativo univoco del batch")
    timestamp_creazione: str = Field(..., description="Data e ora di creazione del batch")
    numero_misurazioni: int = Field(..., description="Numero totale di misurazioni nel batch")

# === MODELLI PER TRASMISSIONE DI DATI
class BatchPayload(ModelliHashabili):
    """
    Rappresenta il payload completo da inviare al cloud provider per ogni batch di misurazioni.
    Il payload è composto da:
    - un'istanza di `DatiBatch`, che contiene i metadati del batch (es. ID, timestamp, merkle root);
    - una lista di oggetti `DatiMisurazione`, che rappresentano le singole misurazioni associate a quel batch.
    Il numero di misurazioni incluse nel payload può variare dinamicamente, in base alla soglia di aggregazione
    definita nel fog node al momento dell'esecuzione.
    Questa struttura compatta consente al cloud di validare sia il batch che le misurazioni associate,
    e rappresenta l'unità fondamentale per la trasmissione e la verifica dell'integrità.
    Viene denotata con il termine 'BatchPayload' ad indicare il ruolo logico del batch
    come un raggruppamento di misurazioni.
    """
    batch: DatiBatch = Field(..., title="Batch", description="Metadata del batch")
    misurazioni: List[DatiMisurazione] = Field(..., title="Lista di Misurazioni", description="Lista delle misurazioni associate al batch")


class DatiListaSensoriPayload(ModelliHashabili):
    """
    Rappresenta un insieme di sensori attualmente noti o registrati nel sistema.
    Questa classe viene utilizzata per inviare o ricevere una lista completa di sensori,
    durante una richiesta di sincronizzazione tra nodi (fog ↔ cloud),
    Tutti i sensori sono rappresentati tramite oggetti `DatiSensore`,
    che includono gli attributi identificativi e strutturali di ciascun nodo sensore.
    """
    sensori: List[DatiSensore] = Field(
        ...,
        title="Lista di Sensori",
        description="Elenco dei sensori attualmente presenti nel sistema, ciascuno rappresentato come DatiSensore."
    )


class DatiMisurazioneSensorePayload(ModelliHashabili):
    """
    Rappresenta l'associazione tra una misurazione e i dati del sensore che l'ha generata.

    Questa classe è utilizzata esclusivamente durante il processo di verifica dell'integrità dei dati.
    Non viene usata durante l'invio dei dati dal fog node al cloud provider, dove i flussi di registrazione
    sono separati:
    - i sensori vengono registrati in modo indipendente;
    - tutte le misurazioni (con la relativa tupla del batch) seguono un canale distinto. Ovviamente non è
    necessario spedire insieme alle misurazioni, le informazioni del sensore che lo ha prodotto perché queste
    sono già memorizzate all'interno del database del cloud provider e inviate dal fog node insieme alle informazioni
    di altri sensori in blocco. Quindi prima inviamo le informazioni sui sensori e dopo possiamo inviare le misurazioni
    che avranno il campo id_sensore su cui è definito il vincolo di integrità referenziale.

    Tuttavia, in fase di verifica, è fondamentale controllare non solo la correttezza della misurazione,
    ma anche che le informazioni associate al sensore non siano state manomesse.
    Ad esempio, una misurazione potrebbe
    sembrare valida, ma essere stata associata a un sensore con tipo alterato (es. da "umidità" a "joystick").
    Questo tipo di alterazione la possiamo considerare dal punto di vista semantico.
    La misurazione cambia la sua semantica
    essendo quest'ultima riferita al sensore che ha prodotto la misurazione.

    Per questo motivo, durante la verifica, viene effettuata una `INNER JOIN` tra le tabelle
    delle misurazioni e dei sensori sul campo `id_sensore` (chiave esterna). Il risultato_verifica di questa
    associazione viene incapsulato in questa classe, che consente di confrontare la tupla estesa
    (misurazione + sensore) con la versione originale posseduta dal produttore dei dati.

    Ovviamente per poter essere possibile nella fase di creazione della merkle root lato produttore
    dobbiamo tenere conto che esiste la tupla del batch e ogni tupla di misurazioni è accompagnata dalla tupla
    del sensore. Solo in questo modo siamo in grado di determinare anomalie sulla tupla misurazione + sensore.
    In caso di progettazione diversa, questo non sarebbe stato possibile.

    Questa struttura è necessaria per:
    - generare e confrontare l’hash della tupla completa (incluso il sensore);
    - evidenziare eventuali modifiche occulte nei metadati del sensore;
    - garantire la coerenza tra ciò che è stato originariamente registrato e ciò che si sta verificando.
    """
    dati_sensore : DatiSensore = Field(..., description="dati del sensore")
    dati_misurazione : DatiMisurazione = Field(..., description="dati della misurazioni")
