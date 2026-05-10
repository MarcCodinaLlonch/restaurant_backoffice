# db.py: crea elements de connexió a la bd's

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from .config import DB_URL

# Engine: Punt d'entrada a la bd's. Rep URL connexió
engine = create_engine(DB_URL)

# sessionmaker: Crea conjunt de sessions. Si volem "parlar" amb la bd's, creem sessió a partir d'una session.
Session = sessionmaker(bind=engine) # bind=engine: Lliga la sessionmaker a engine.

# Classe base, tots els models ORM han de heretar d'aquesta classe.
# SQLAlchemy la necessita per saber quines classes ha de mapejar a taules de la BD.
class Base(DeclarativeBase):
    ...