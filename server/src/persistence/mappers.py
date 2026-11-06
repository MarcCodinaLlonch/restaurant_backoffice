# mappers.py: Tradueix entre els models ORM de SQLAlchemy i les Entitats de Domini netes.
#
# CONCEPTE CLAU PER A DAM (Mappers / Object-to-Entity Mapping):
# La persistència de la base de dades utilitza objectes 'Category', 'Employee'
# lligats a SQLAlchemy. Però el servei i el protocol només han de retornar
# objectes purs ('CategoryEntity', 'EmployeeEntity').
# Aquest fitxer conté funcions auxiliars per fer aquesta traducció neta i centralitzada.

from common.domain.entities import (
    AllergenEntity,
    CategoryEntity,
    DishEntity,
    EmployeeEntity,
    MenuEntity,
    SaleEntity,
)

from .models import Allergen, Category, Dish, Employee, Menu, Sale


def category_to_entity(category: Category) -> CategoryEntity:
    """Converteix un model ORM Category a CategoryEntity."""
    if not category:
        return None
    return CategoryEntity(
        id=category.id,
        category_name=category.category_name,
        last_update=category.last_update.isoformat() if category.last_update else None,
    )


def allergen_to_entity(allergen: Allergen) -> AllergenEntity:
    """Converteix un model ORM Allergen a AllergenEntity."""
    if not allergen:
        return None
    return AllergenEntity(
        id=allergen.id,
        allergen_name=allergen.allergen_name,
        last_update=allergen.last_update.isoformat() if allergen.last_update else None,
    )


def dish_to_entity(dish: Dish) -> DishEntity:
    """Converteix un model ORM Dish a DishEntity, incloent categoria i al·lèrgens."""
    if not dish:
        return None
    allergens_entities = [allergen_to_entity(allergen) for allergen in (dish.allergens or [])]
    category_name = dish.category.category_name if dish.category else None
    return DishEntity(
        id=dish.id,
        dish_name=dish.dish_name,
        description=dish.description,
        is_active=bool(dish.is_active),
        id_category=dish.id_category,
        category_name=category_name,
        allergens=allergens_entities,
        last_update=dish.last_update.isoformat() if dish.last_update else None,
    )


def employee_to_entity(employee: Employee) -> EmployeeEntity:
    """
    Converteix un model ORM Employee a EmployeeEntity.
    Nota de seguretat: No exportem mai el hash de la contrasenya cap a l'entitat.
    """
    if not employee:
        return None
    has_credentials = employee.credentials is not None
    email = employee.credentials.email if employee.credentials else None
    return EmployeeEntity(
        id=employee.id,
        name=employee.name,
        surname=employee.surname,
        national_id=employee.national_id,
        role=employee.role,
        has_credentials=has_credentials,
        email=email,
        last_update=employee.last_update.isoformat() if employee.last_update else None,
    )


def menu_to_entity(menu: Menu) -> MenuEntity:
    """Converteix un model ORM Menu a MenuEntity, incloent els seus plats associats."""
    if not menu:
        return None
    dishes_entities = [dish_to_entity(dish) for dish in (menu.dishes or [])]
    return MenuEntity(
        id=menu.id,
        menu_name=menu.menu_name,
        price=float(menu.price),
        dishes=dishes_entities,
        last_update=menu.last_update.isoformat() if menu.last_update else None,
    )


def sale_to_entity(sale: Sale) -> SaleEntity:
    """Converteix un model ORM Sale a SaleEntity."""
    if not sale:
        return None
    menu_name = sale.menu.menu_name if sale.menu else None
    employee_name = f"{sale.employee.name} {sale.employee.surname}" if sale.employee else None
    return SaleEntity(
        id_menu=sale.id_menu,
        id_employee=sale.id_employee,
        sale_date=str(sale.sale_date),
        quantity_sold=sale.quantity_sold,
        menu_name=menu_name,
        employee_name=employee_name,
        last_update=sale.last_update.isoformat() if sale.last_update else None,
    )
