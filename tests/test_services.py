# test_services.py: Proves unitàries de la capa de serveis utilitzant Mocks per aïllar la base de dades.

import hashlib
from datetime import date
from unittest.mock import MagicMock
import pytest

from server.src.services.category_service import CategoryService
from server.src.services.employee_service import EmployeeService
from server.src.services.dish_service import DishService
from server.src.services.menu_service import MenuService
from server.src.services.sale_service import SaleService
from server.src.persistence.models import Category, Employee, Dish, Menu, Sale


@pytest.fixture
def mock_uow_factory():
    """Crea una factoria simulada (Mock) que retorna un UnitOfWork simulat."""
    factory = MagicMock()
    uow = MagicMock()
    # Configurem el context manager (with factory.create() as uow:)
    factory.create.return_value.__enter__.return_value = uow
    return factory, uow


def test_category_service_create_empty_name_raises_error(mock_uow_factory):
    """Comprova que no es permet crear una categoria amb nom buit."""
    factory, _ = mock_uow_factory
    service = CategoryService(factory)

    with pytest.raises(ValueError, match="El nom de la categoria no pot estar buit"):
        service.create("")


def test_category_service_create_valid(mock_uow_factory):
    """Comprova que es crea una categoria correctament i s'afegeix al repositori."""
    factory, uow = mock_uow_factory
    service = CategoryService(factory)

    cat = service.create("Begudes")
    assert cat.category_name == "Begudes"
    uow.categories.add.assert_called_once()


def test_employee_service_creates_credentials_with_sha256(mock_uow_factory):
    """Comprova que en crear un empleat amb contrasenya, aquesta es guarda com a hash SHA-256."""
    factory, uow = mock_uow_factory
    uow.employees.national_id_exists.return_value = False
    service = EmployeeService(factory)

    emp = service.create(
        name="Marc",
        surname="Garcia",
        national_id="12345678A",
        role="Cambrer",
        email="marc@restaurant.com",
        password="secretpassword"
    )

    assert emp.name == "Marc"
    assert emp.email == "marc@restaurant.com"
    # Comprovem que l'objecte afegit al repositori té les credencials amb hash SHA-256
    added_emp = uow.employees.add.call_args[0][0]
    expected_hash = hashlib.sha256("secretpassword".encode()).hexdigest()
    assert added_emp.credentials.password_hash == expected_hash


def test_dish_service_create_category_not_found(mock_uow_factory):
    """Comprova que crear un plat amb categoria inexistent llença error."""
    factory, uow = mock_uow_factory
    uow.categories.get.return_value = None
    service = DishService(factory)

    with pytest.raises(ValueError, match="No existeix cap categoria"):
        service.create(dish_name="Paella", id_category=99)


def test_menu_service_filter_price_validation(mock_uow_factory):
    """Comprova que el preu mínim no pot ser superior al màxim."""
    factory, _ = mock_uow_factory
    service = MenuService(factory)

    with pytest.raises(ValueError, match="El preu mínim no pot ser superior"):
        service.filter_by_price_range(min_price=25.0, max_price=10.0)


def test_sale_service_create_negative_quantity(mock_uow_factory):
    """Comprova que no es permet registrar una venda amb quantitat 0 o negativa."""
    factory, _ = mock_uow_factory
    service = SaleService(factory)

    with pytest.raises(ValueError, match="La quantitat venuda ha de ser superior a 0"):
        service.create(id_menu=1, id_employee=1, sale_date_val=date.today(), quantity_sold=-2)
