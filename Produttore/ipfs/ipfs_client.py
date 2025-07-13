# Import delle librerie per l'interazione con Filebase (via S3), gestione eccezioni,
import logging

import boto3
import botocore.exceptions

from Classi_comuni.file_utils import genera_contenuto_gzip, genera_nome_file
from costanti_produttore import AWS_SECRET_ACCESS_KEY, AWS_ACCESS_KEY_ID
logger = logging.getLogger(__name__)
logging.getLogger("botocore").setLevel(logging.CRITICAL)
logging.getLogger("boto3").setLevel(logging.CRITICAL)
logging.getLogger("urllib3").setLevel(logging.CRITICAL)


#ErroreCaricamento: nella put_object → quando upload fallisce.
#ErroreRecuperoCID: nella head_object → se ipfs-hash non esiste nei metadata.
class ErroreCaricamentoIPFS(Exception):
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
risposta["Metadata"]["cid"]
Questo è possibile solo se l'oggetto è presente nel bucket dell'utente autenticato,
e non può essere fatto su oggetti esterni o appartenenti ad altri account.
"""
class IpfsClient:
    """
    Classe per caricare file JSON su Filebase (IPFS) e recuperare il CID associato.
    """
    def __init__(self):
        #load_dotenv()
        #access_key = os.getenv("AWS_ACCESS_KEY_ID")
        #secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")
        access_key = AWS_ACCESS_KEY_ID
        secret_key = AWS_SECRET_ACCESS_KEY
        self.s3 = boto3.client(
            's3',
            endpoint_url='https://s3.filebase.com',
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key
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
            raise ErroreCaricamentoIPFS("Errore durante la creazione o verifica del bucket.")

    def carica_stringa_json(self, nome_bucket: str, stringa_json: str, comprimi_dimensione: bool = False) -> str:
        """
        Carica un file JSON su IPFS (tramite Filebase), usando come nome file
        un hash deterministico del contenuto. Se il caricamento fallisce, solleva eccezione personalizzata ErroreCaricamento.
        """
        self.verifica_o_crea_bucket(nome_bucket)
        nome_file = genera_nome_file(stringa_json)
        if comprimi_dimensione:
            contenuto = genera_contenuto_gzip(stringa_json)
            nome_file += ".gz"
        else:
            contenuto = stringa_json.encode("utf-8")
        try:
            logger.info(f"Caricamento '{nome_file}' nel bucket '{nome_bucket}'...")
            params = {
                "Bucket": nome_bucket,
                "Key": nome_file,
                "Body": contenuto,
            }
            if comprimi_dimensione:
                params["ContentType"] = "application/gzip"
            else:
                params["ContentType"] = "application/json"

            #usando un dizionario (params), puoi aggiungere parametri solo quando servono
            #con ** sto creando un nuovo dizionario
            self.s3.put_object(**params)
            logger.info("✅ Upload completato.")
            return nome_file

        except botocore.exceptions.ClientError as e:
            logger.error(f"❌ Errore durante upload: {e}")
            raise ErroreCaricamentoIPFS(f"Errore nel caricamento di '{nome_file}'")

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
            cid = metadata_file.get("cid")
            if not cid:
                raise ErroreRecuperoCID(f"CID non trovato nei metadata per il file '{nome_file}'")
            logger.info(f"🔑 CID recuperato: {cid}")
            return cid
        except botocore.exceptions.ClientError as e:
            logger.error(f"❌ Errore nel recupero del CID: {e}")
            raise ErroreRecuperoCID(f"Impossibile ottenere CID per il file '{nome_file}'")