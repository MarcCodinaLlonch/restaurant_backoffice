from abc import ABC, abstractmethod
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from .repositories import (
    EmployeeRepository, MenuRepository, DishRepository,
    SaleRepository, CategoryRepository, AllergenRepository
)

# Aquesta és la "Interfície" o Contracte.
# Diu que qualsevol Unit of Work ha de saber fer commit i rollback.
class AbstractUnitOfWork(ABC):
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        # Si hi ha un error (exc_type no és None), fem rollback
        if exc_type:
            self.rollback()
        else:
            # Si tot ha anat bé, el professor sol fer el commit automàtic!
            self.commit()

    @abstractmethod
    def commit(self):
        pass

    @abstractmethod
    def rollback(self):
        pass

#La nostra Unit of work s'encarrega que tot el que fem en una sessió de base de dades "vagi junt" o no es guarda res.
class SqlAlchemyUnitOfWork(AbstractUnitOfWork):
    def __init__(self, session: Session):
        # Aquest 'session_factory' és el que ens permetrà crear sessions noves
        self.session=session

    #Mètode que obre la sessió
    def __enter__(self):
        # Aquí instanciem els repositoris passant-los la sessió que acabem de crear
        self.employees = EmployeeRepository(self.session)
        self.menus = MenuRepository(self.session)
        self.dishes = DishRepository(self.session)
        self.sales = SaleRepository(self.session)
        self.categories = CategoryRepository(self.session)
        self.allergens = AllergenRepository(self.session)

        return super().__enter__()

    #Mètode que assegura que la base de dades no es quedi "penjada". Si hi ha un error (excepció) fa un rollback automatic per seguretat i tanca sessió passi el que passi.
    def __exit__(self, exc_type, exc_value, traceback):
        try:
            # Cridem a la lògica de l'__exit__ de la classe pare (commit/rollback)
            super().__exit__(exc_type, exc_value, traceback)
        finally:
            # SEMPRE tanquem la sessió al final
            self.session.close()

    #Guarda canvis de forma manual
    def commit(self):
        self.session.commit()

    #Cancela els canvis de forma manual
    def rollback(self):
        self.session.rollback()

class UnitOfWorkFactory:
    def __init__(self, database_url: str):
        # Creem el motor de la base de dades
        self.engine = create_engine(database_url)
        # Configurem com es crearan les sessions
        self.session_class = sessionmaker(
            bind=self.engine,
            autoflush=False,
            autocommit=False,
            expire_on_commit=False,
        )

    def create(self) -> SqlAlchemyUnitOfWork:
        # Aquest mètode crea una sessió nova i la injecta en un nou UoW
        return SqlAlchemyUnitOfWork(self.session_class())
