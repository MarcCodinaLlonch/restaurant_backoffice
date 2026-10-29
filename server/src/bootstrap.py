"""
bootstrap.py: Inicialització de la persistència, serveis i enrutador del servidor.
"""
import logging
from server.src.persistence.config import DB_URL
from server.src.persistence.db import Base, engine, Session
from server.src.persistence.seed import ensure_database_exists, seed_initial_data
from server.src.persistence.unit_of_work import UnitOfWorkFactory
from server.src.services import (
    CategoryService,
    AllergenService,
    DishService,
    EmployeeService,
    MenuService,
    SaleService,
)
from server.src.protocol.router import Router

logger = logging.getLogger(__name__)


def init_database(db_url: str = DB_URL) -> None:
    """Assegura l'existència de la BD, crea les taules i carrega les dades inicials si cal."""
    if not db_url:
        raise RuntimeError("No s'ha definit cap URL de connexió a la base de dades.")

    logger.info("Verificant connexió a la BD (%s)...", db_url.split('@')[-1] if '@' in db_url else db_url)
    ensure_database_exists(db_url)

    if engine:
        Base.metadata.create_all(bind=engine)
        seed_initial_data(Session)
    logger.info("Base de dades llesta.")


def create_router(db_url: str = DB_URL) -> Router:
    """Instancia la factoria d'Unit of Work, els 6 serveis i configura el Router."""
    uow_factory = UnitOfWorkFactory(db_url)
    category_svc = CategoryService(uow_factory)
    allergen_svc = AllergenService(uow_factory)
    dish_svc = DishService(uow_factory)
    employee_svc = EmployeeService(uow_factory)
    menu_svc = MenuService(uow_factory)
    sale_svc = SaleService(uow_factory)

    return Router(
        category_service=category_svc,
        allergen_service=allergen_svc,
        dish_service=dish_svc,
        employee_service=employee_svc,
        menu_service=menu_svc,
        sale_service=sale_svc,
    )