# config.py: Centralitza la configuració de la base de dades i del servidor.
# Llegim les variables d'entorn des del fitxer .env.

import os
from dotenv import load_dotenv

load_dotenv()

ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

DB_URL = {
    "development": os.getenv("DB_URL_DEVELOPMENT", "postgresql://postgres:secretpassword@localhost:5433/restaurant_db_dev"),
    "test":        os.getenv("DB_URL_TESTS", "sqlite:///:memory:"),
    "production":  os.getenv("DB_URL_PRODUCTION", "postgresql://postgres:secretpassword@localhost:5433/restaurant_db_prod")
}.get(ENVIRONMENT)

# Configuració de la xarxa per al Servidor TCP
SERVER_HOST = os.getenv("SERVER_HOST", "0.0.0.0")
SERVER_PORT = int(os.getenv("SERVER_PORT", "8088"))
