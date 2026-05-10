# unit_of_work.py: Implementa patró Unit of Work (UoW).
# Assegura que totes les operacions d'una mateixa acció es guarden juntes a la bd's o no es guarda res.
# Si hi ha un error a mig camí, tot es desfà automàticament (rollback).

from abc import ABC, abstractmethod
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from .repositories import (
    EmployeeRepository, MenuRepository, DishRepository,
    SaleRepository, CategoryRepository, AllergenRepository
)

# Classe abstracta que defineix que ha de complir qualsevol Unit of Work.
# ABC (Abstract Base Class) impedeix instanciar aquesta classe directament:
# obliga a crear una classe filla que implementi commit() i rollback().
class AbstractUnitOfWork(ABC):

    # __enter__ s'executa en entrar al bloc "with".
    def __enter__(self):
        return self # Retorna self per poder accedir als repositoris dins del bloc.

    # __exit__ s'executa en sortir del bloc "with", tant si hi ha error com si no.
    def __exit__(self, exc_type, exc_value, traceback):
        # Si hi ha hagut un error, desfem tots els canvis de la sessió
        if exc_type: # exc_type conté el tipus d'excepció si n'hi ha hagut, o None si tot ha anat bé.
            self.rollback()
        else:
            # Si tot ha anat bé, guardem els canvis a la bd's
            self.commit()

    # Mètode abstracte: les classes filles OBLIGATÒRIAMENT han d'implementar-lo.
    @abstractmethod
    def commit(self):
        pass

    # Mètode abstracte: les classes filles OBLIGATÒRIAMENT han d'implementar-lo.
    @abstractmethod
    def rollback(self):
        pass


# Implementació UoW amb SQLAlchemy.Fa que tot el que fem en una sessió "vagi junt" o no es guardi res.
class SqlAlchemyUnitOfWork(AbstractUnitOfWork):

    def __init__(self, session: Session):
        # Guardem la sessió. La compartiran tots els repositoris creats dins d'aquest UoW.
        self.session = session

    # En entrar a bloc "with", creem tots els repositoris passant-los la sessió.
    # Com que tots fan servir mateixa sessió, totes les operacions formen part de mateixa transacció i es guarden o descarten juntes.
    def __enter__(self):
        self.employees  = EmployeeRepository(self.session)
        self.menus      = MenuRepository(self.session)
        self.dishes     = DishRepository(self.session)
        self.sales      = SaleRepository(self.session)
        self.categories = CategoryRepository(self.session)
        self.allergens  = AllergenRepository(self.session)
        return super().__enter__()

    # En sortir del bloc "with", cridem lògica del pare (commit o rollback).
    # Tanquem la sessió a bloc finally assegurant que es tanca sempre, tant si hi ha error o no.
    def __exit__(self, exc_type, exc_value, traceback):
        try:
            super().__exit__(exc_type, exc_value, traceback)
        finally:
            # sempre tanquem la sessió per alliberar la connexió a la bd's
            self.session.close()

    # Guarda tots els canvis pendents de la sessió a la bs's.
    def commit(self):
        self.session.commit()

    # Descarta tots els canvis pendents de la sessió sense guardar res.
    def rollback(self):
        self.session.rollback()

# Factory crea instàncies de SqlAlchemyUnitOfWork.
# Encapsula la creació del motor i de les sessions per simplificar ús.
class UnitOfWorkFactory:

    def __init__(self, database_url: str):
        # Creem el motor de la bd's a partir de la URL de connexió
        self.engine = create_engine(database_url)

        # Configurem les sessions amb les opcions necessàries:
        self.session_class = sessionmaker(
            bind=self.engine, # Lliga sessionmaker al motor creat.
            autoflush=False, # No enviem canvis a la bd's fins al commit.
            autocommit=False, # Canvis no es guarden automàticament, necessitem commit().
            expire_on_commit=False, # Després de commit, podem llegir objectes (els seus atributs) sense nova sessió.
        )

    # Crea una sessió nova i la injecta dins d'un SqlAlchemyUnitOfWork nou.
    # Cada crida a create() genera una sessió independent.
    def create(self) -> SqlAlchemyUnitOfWork:
        return SqlAlchemyUnitOfWork(self.session_class())
