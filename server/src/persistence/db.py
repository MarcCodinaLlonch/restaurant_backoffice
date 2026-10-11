# db.py: Configura el motor (Engine) i la classe Base per a SQLAlchemy.
# Aquest mòdul només existeix al Servidor (la BD és privada del servidor).

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from .config import DB_URL

# Engine: Gestor de connexions cap a la base de dades.
engine = create_engine(DB_URL) if DB_URL else None

# Factory per generar sessions de treball amb la BD
Session = sessionmaker(bind=engine) if engine else None

# Classe base de la qual hereten tots els models ORM de la persistència
class Base(DeclarativeBase):
    pass
