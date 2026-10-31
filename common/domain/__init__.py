# __init__.py a common/domain
# Permet importar directament les entitats des de common.domain
from .entities import (
    AllergenEntity,
    CategoryEntity,
    DishEntity,
    EmployeeEntity,
    MenuEntity,
    SaleEntity,
)

__all__ = [
    "CategoryEntity",
    "AllergenEntity",
    "DishEntity",
    "EmployeeEntity",
    "MenuEntity",
    "SaleEntity",
]
