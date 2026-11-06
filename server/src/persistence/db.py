# db.py: Classe Base de la qual hereten tots els models ORM.
# L'engine (connexió a la BD) el crea UnitOfWorkFactory: així només n'hi ha UN a tot el servidor.

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass
