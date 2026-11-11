# unit_of_work.py: Implementa el patró Unit of Work (UoW).
# Assegura que totes les operacions d'una mateixa transacció es guarden juntes a la BD o cap.
# Si hi ha un error a mig camí, es fa rollback() automàticament.

from abc import ABC, abstractmethod

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from .repositories import (
    AllergenRepository,
    CategoryRepository,
    DishRepository,
    EmployeeRepository,
    MenuRepository,
    SaleRepository,
)


class AbstractUnitOfWork(ABC):
    """
    Classe abstracta que defineix el contracte del patró Unit of Work.
    """

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if exc_type:
            self.rollback()
        else:
            self.commit()

    @abstractmethod
    def commit(self):
        pass

    @abstractmethod
    def rollback(self):
        pass


class SqlAlchemyUnitOfWork(AbstractUnitOfWork):
    """
    Implementació concreta de Unit of Work utilitzant una sessió de SQLAlchemy.
    """

    def __init__(self, session: Session):
        self.session = session

    def __enter__(self):
        # CLAU: els 6 repositoris comparteixen la mateixa sessió -> mateixa transacció atòmica.
        self.employees = EmployeeRepository(self.session)
        self.menus = MenuRepository(self.session)
        self.dishes = DishRepository(self.session)
        self.sales = SaleRepository(self.session)
        self.categories = CategoryRepository(self.session)
        self.allergens = AllergenRepository(self.session)
        return super().__enter__()

    def __exit__(self, exc_type, exc_value, traceback):
        # CLAU: si exc_type hi ha hagut error -> rollback; si no -> commit; i close() sempre.
        try:
            super().__exit__(exc_type, exc_value, traceback)
        finally:
            self.session.close()

    def commit(self):
        self.session.commit()

    def rollback(self):
        self.session.rollback()


class UnitOfWorkFactory:
    """
    Factoria encarregada de crear instàncies de SqlAlchemyUnitOfWork
    amb la configuració de connexió a la BD.
    """

    def __init__(self, database_url: str):
        # CLAU: un sol engine (pool de connexions) al servidor; autocommit=False exigeix commit().
        self.engine = create_engine(database_url)
        self.session_class = sessionmaker(
            bind=self.engine,
            autoflush=False,
            autocommit=False,
            expire_on_commit=False,
        )

    def create(self) -> SqlAlchemyUnitOfWork:
        # CLAU: sessió nova per petició (cada petició independent; mai es comparteix entre fils).
        return SqlAlchemyUnitOfWork(self.session_class())
