"""bootstrap.py: prepara la base de dades i munta les capes del servidor (serveis i Router)."""

import logging

from server.src.persistence.db import Base
from server.src.persistence.seed import ensure_database_exists, seed_initial_data
from server.src.persistence.unit_of_work import UnitOfWorkFactory
from server.src.protocol.router import Router
from server.src.services import (
    AllergenService,
    CategoryService,
    DishService,
    EmployeeService,
    MenuService,
    SaleService,
)

logger = logging.getLogger(__name__)


def create_uow_factory(db_url: str) -> UnitOfWorkFactory:
    """Crea la BD si cal, crea les taules, carrega dades de prova i retorna la factoria."""
    ensure_database_exists(db_url)
    uow_factory = UnitOfWorkFactory(db_url)
    # Fem servir el MATEIX engine per a tot: un sol pool de connexions.
    Base.metadata.create_all(bind=uow_factory.engine)
    seed_initial_data(uow_factory.session_class)
    logger.info("Database ready")
    return uow_factory


def create_router(uow_factory: UnitOfWorkFactory) -> Router:
    """Crea els 6 serveis de negoci i el Router de la Pràctica 1 (reutilitzat sense canvis)."""
    # CLAU: els 6 serveis reben la mateixa uow_factory (injecció de dependències);
    # aquest fitxer no sap res de xarxa ni d'asyncio.
    return Router(
        category_service=CategoryService(uow_factory),
        allergen_service=AllergenService(uow_factory),
        dish_service=DishService(uow_factory),
        employee_service=EmployeeService(uow_factory),
        menu_service=MenuService(uow_factory),
        sale_service=SaleService(uow_factory),
    )
