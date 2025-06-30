#Path assoluto al file .env
import os

from dotenv import load_dotenv

from Cloud_Service_Provider.database.gestore_db import GestoreDatabase

env_path = os.path.join(os.path.dirname(__file__), "..", "config", ".env")
load_dotenv(dotenv_path=os.path.abspath(env_path))
config_db = {
    "host": os.getenv("DB_HOST"),
    "port": int(os.getenv("DB_PORT")),
    "database": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD")
}
#istanza del db
gestore_db = GestoreDatabase(config_db)
