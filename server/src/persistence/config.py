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

# Límits i timeouts de concurrència i seguretat (AsyncIO)
READ_TIMEOUT_SECONDS = float(os.getenv("READ_TIMEOUT_SECONDS", "5.0"))
MAX_BODY_SIZE = int(os.getenv("MAX_BODY_SIZE", "1048576"))        # 1 MB
MAX_CONNECTIONS = int(os.getenv("MAX_CONNECTIONS", "50"))
DB_MAX_CONCURRENCY = int(os.getenv("DB_MAX_CONCURRENCY", "5"))  # = pool_size de SQLAlchemy
