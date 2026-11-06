# test_persistence.py: Proves de la capa de persistència amb una BD SQLite real en memòria.

import pytest

from server.src.persistence.db import Base
from server.src.persistence.unit_of_work import UnitOfWorkFactory
from server.src.services.allergen_service import AllergenService
from server.src.services.category_service import CategoryService


@pytest.fixture
def uow_factory() -> UnitOfWorkFactory:
    """BD SQLite en memòria, amb les taules creades i buida."""
    factory = UnitOfWorkFactory("sqlite://")
    Base.metadata.create_all(bind=factory.engine)
    return factory


def test_created_category_has_id(uow_factory: UnitOfWorkFactory):
    """La resposta d'un create ha de portar l'id que ha assignat la BD (abans sortia None)."""
    category = CategoryService(uow_factory).create("Postres i cafès")

    assert category.id is not None
    assert CategoryService(uow_factory).get_by_id(category.id).category_name == "Postres i cafès"


def test_created_allergen_has_id(uow_factory: UnitOfWorkFactory):
    allergen = AllergenService(uow_factory).create("Mostassa")

    assert allergen.id is not None
