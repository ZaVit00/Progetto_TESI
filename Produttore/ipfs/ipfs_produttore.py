# Import delle librerie per l'interazione con Filebase (via S3), gestione eccezioni,
# logging e variabili ambiente
import boto3
import botocore.exceptions
import logging
from dotenv import load_dotenv
from Classi_comuni.hash_utils import Hashing
logger = logging.getLogger(__name__)
"""
LOGGER SE SERVE UTILIZZARE ESEGUIRE LA CLASSE IN MODO STANDALONE
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter('[%(levelname)s] %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
"""


#ErroreCaricamento: nella put_object → quando upload fallisce.
#ErroreRecuperoCID: nella head_object → se ipfs-hash non esiste nei metadata.
class ErroreCaricamento(Exception):
    """Eccezione sollevata quando il caricamento su Filebase/IPFS fallisce."""
    pass

class ErroreRecuperoCID(Exception):
    """Eccezione sollevata quando il CID non può essere recuperato dai metadati del file."""
    pass

"""
Alcuni dettagli tecnici sul metodo head_object
Il metodo `head_object` di boto3 restituisce un dizionario con informazioni dettagliate
sull'oggetto memorizzato nel bucket. Tra le varie chiavi restituite, è presente 'Metadata',
che contiene un ulteriore dizionario con i metadata personalizzati dell'oggetto.
Filebase, nel caso di file caricati sulla rete IPFS tramite il suo endpoint S3-compatibile,
inserisce automaticamente in 'Metadata' una chiave denominata 'ipfs-hash', il cui valore è
il CID IPFS associato al contenuto caricato. Accediamo a tale valore tramite:
risposta["Metadata"]["ipfs-hash"]
Questo è possibile solo se l'oggetto è presente nel bucket dell'utente autenticato,
e non può essere fatto su oggetti esterni o appartenenti ad altri account.
"""

class ProduttoreIPFS:
    """
    Classe per caricare file JSON su Filebase (IPFS) e recuperare il CID associato.
    """
    def __init__(self, chiave_accesso: str, chiave_segreta: str):
        load_dotenv()
        #access_key = os.getenv("AWS_ACCESS_KEY_ID")
        #secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")
        self.s3 = boto3.client(
            's3',
            endpoint_url='https://s3.filebase.com',
            aws_access_key_id=chiave_accesso,
            aws_secret_access_key=chiave_segreta
        )

    def verifica_o_crea_bucket(self, nome_bucket: str):
        """
        Controlla se il bucket esiste, altrimenti lo crea.
        """
        try:
            risposta = self.s3.list_buckets()
            buckets_esistenti = [b["Name"] for b in risposta["Buckets"]]
            if nome_bucket not in buckets_esistenti:
                self.s3.create_bucket(Bucket=nome_bucket)
                logger.info(f"🪣 Bucket '{nome_bucket}' creato.")
            else:
                logger.debug(f"Bucket '{nome_bucket}' già esistente.")
        except botocore.exceptions.ClientError as e:
            logger.error(f"❌ Errore nella verifica/creazione del bucket: {e}")
            raise ErroreCaricamento("Errore durante la creazione o verifica del bucket.")

    def carica_json(self, nome_bucket: str, stringa_json: str) -> str:
        """
        Carica un file JSON su IPFS (tramite Filebase).
        Solleva ErroreCaricamento se upload fallisce.
        """
        self.verifica_o_crea_bucket(nome_bucket)
        nome_file = ProduttoreIPFS._genera_nome_file(stringa_json)
        try:
            logger.info(f"Caricamento '{nome_file}' nel bucket '{nome_bucket}'...")
            self.s3.put_object(
                Bucket=nome_bucket,
                Key=nome_file,
                Body=stringa_json,
                ContentType='application/json'
            )
            logger.info("✅ Upload completato.")
            return nome_file
        except botocore.exceptions.ClientError as e:
            logger.error(f"❌ Errore durante upload: {e}")
            raise ErroreCaricamento(f"Errore nel caricamento di '{nome_file}'")

    def recupera_cid_file_bucket(self, nome_bucket: str, nome_file: str) -> str:
        """
        Recupera il CID IPFS associato a un file precedentemente caricato nel proprio bucket Filebase.
        ⚠️ Attenzione:
        Questo metodo funziona solo per file:
        - che sono stati caricati nel tuo bucket Filebase (via API compatibile S3),
        - di cui conosci il nome esatto (object key),
        - e per cui Filebase ha generato il metadata 'ipfs-hash' nei metadata dell'oggetto.
        ❌ Non può essere usato per ottenere il CID da file arbitrari su IPFS o caricati da altri utenti.
        """
        try:
            #recupera il file
            risposta = self.s3.head_object(Bucket=nome_bucket, Key=nome_file)
            metadata_file = risposta.get("Metadata", {})
            cid = metadata_file.get("cid", {})  # ✅ questo è il campo corretto
            logger.info(f"🔑 CID recuperato: {cid}")
            return cid
        except botocore.exceptions.ClientError as e:
            logger.error(f"❌ Errore nel recupero del CID: {e}")
            raise ErroreRecuperoCID(f"Impossibile ottenere CID per il file '{nome_file}'")


    @staticmethod
    def _genera_nome_file(json_string: str) -> str:
        """
        Genera un nome file compatto e univoco basato solo su hash:
        - Esempio: merkle_path_3ac1b2d9.json
        """
        full_hash = Hashing.calcola_hash(json_string)
        #esrae i primi 8 caratteri hash complessivo
        short_hash = full_hash[:8]
        return f"merkle_path_{short_hash}.json"


"""
FUNZIONE DI AUSILIO/DEBUG (serve per testare il comportamento della classe in modo indipendente)
def main():
    load_dotenv()
    access_key = os.getenv("AWS_ACCESS_KEY_ID")
    secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")
    uploader = ProduttoreIPFS(access_key, secret_key)
    data =  {
        1: {"directions": "0101", "siblings": ["aaa", "bbb"]},
        3: {"directions": "0011", "siblings": ["ccc", "ddd"]}
    }

    data_JSON = json.dumps(
        data,
        sort_keys=True,  # ordine prevedibile delle chiavi
        separators=(",", ":"),  # compatto ma leggibile
        indent=2  # indentazione per leggibilità
    )
    try:
        nome_file_caricare = uploader.carica_json("merkle-path-batch", stringa_json=data_JSON)
        cid_ottenuto = uploader.recupera_cid_file_bucket("merkle-path-batch", nome_file_caricare)
        logger.info(f"✅ Caricamento completato con CID: {cid_ottenuto}")
    except (ErroreCaricamento, ErroreRecuperoCID) as e:
        logger.error(f"‼️ Operazione fallita: {e}")

if __name__ == "__main__":
"""
