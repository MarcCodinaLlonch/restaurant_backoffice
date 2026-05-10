# config.py: s'encarrega de llegir les variables del fitxer .env
# i convertir-ho en variables Python que la resta del projecte pot fer servir.
# Canviant només el .env podem connectar a una BD diferent.

import os
from dotenv import load_dotenv

# Carrega fitxer .env i converteix contingut en variables accessibles amb os.getenv().
load_dotenv()

# Llegim en quin entorn treballem. Si var ENVIRONMENT no existeix, fem servir "development" per defecte.
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

# Diccionari amb tres URLs (una per entorn).
DB_URL = {
    "development": os.getenv("DB_URL_DEVELOPMENT"),
    "test":        os.getenv("DB_URL_TESTS"),
    "production":  os.getenv("DB_URL_PRODUCTION")
}.get(ENVIRONMENT) #Agafem la que correspon a entorn actiu amb .get(ENVIRONMENT).