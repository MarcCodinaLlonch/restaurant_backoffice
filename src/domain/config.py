#Aquest document serveix per important les variables del doc .env i convertir-les en variables d'entorn.
import os 
from dotenv import load_dotenv

load_dotenv()

ENVIROMENT = os.getenv("ENVIROMENT", "development")

DB_URL = {
    "development": os.getenv("DB_URL_DEVELOPMENT"),
    "test": os.getenv("DB_URL_TESTS"),
    "production": os.getenv("DB_URL_PRODUCTION")
}.get(ENVIROMENT)