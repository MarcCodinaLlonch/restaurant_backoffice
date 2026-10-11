# mappers.py: Tradueix entre els models ORM de SQLAlchemy i les Entitats de Domini netes.
#
# CONCEPTE CLAU PER A DAM (Mappers / Object-to-Entity Mapping):
# La persistència de la base de dades utilitza objectes 'Category', 'Employee' lligats a SQLAlchemy.
# Però el servei i el protocol només han de retornar objectes purs ('CategoryEntity', 'EmployeeEntity').
# Aquest fitxer conté funcions auxiliars per fer aquesta traducció neta i centralitzada.

from common.domain.entities import (
    CategoryEntity,
    AllergenEntity,
    DishEntity,
    EmployeeEntity,
    MenuEntity,
    SaleEntity,
)
from .models import Category, Allergen, Dish, Employee, Menu, Sale


def category_to_entity(cat: Category) -> CategoryEntity:
    """Converteix un model ORM Category a CategoryEntity."""
    if not cat:
        return None
    return CategoryEntity(
        id=cat.id,
        category_name=cat.category_name,
        last_update=cat.last_update.isoformat() if cat.last_update else None,
    )


def allergen_to_entity(al: Allergen) -> AllergenEntity:
    """Converteix un model ORM Allergen a AllergenEntity."""
    if not al:
        return None
    return AllergenEntity(
        id=al.id,
        allergen_name=al.allergen_name,
        last_update=al.last_update.isoformat() if al.last_update else None,
    )


def dish_to_entity(d: Dish) -> DishEntity:
    """Converteix un model ORM Dish a DishEntity, incloent categoria i al·lèrgens."""
    if not d:
        return None
    allergens_entities = [allergen_to_entity(a) for a in (d.allergens or [])]
    cat_name = d.category.category_name if d.category else None
    return DishEntity(
        id=d.id,
        dish_name=d.dish_name,
        description=d.description,
        is_active=bool(d.is_active),
        id_category=d.id_category,
        category_name=cat_name,
        allergens=allergens_entities,
        last_update=d.last_update.isoformat() if d.last_update else None,
    )


def employee_to_entity(emp: Employee) -> EmployeeEntity:
    """
    Converteix un model ORM Employee a EmployeeEntity.
    Nota de seguretat: No exportem mai el hash de la contrasenya cap a l'entitat.
    """
    if not emp:
        return None
    has_creds = emp.credentials is not None
    email = emp.credentials.email if emp.credentials else None
    return EmployeeEntity(
        id=emp.id,
        name=emp.name,
        surname=emp.surname,
        national_id=emp.national_id,
        role=emp.role,
        has_credentials=has_creds,
        email=email,
        last_update=emp.last_update.isoformat() if emp.last_update else None,
    )


def menu_to_entity(m: Menu) -> MenuEntity:
    """Converteix un model ORM Menu a MenuEntity, incloent els seus plats associats."""
    if not m:
        return None
    dishes_entities = [dish_to_entity(d) for d in (m.dishes or [])]
    return MenuEntity(
        id=m.id,
        menu_name=m.menu_name,
        price=float(m.price),
        dishes=dishes_entities,
        last_update=m.last_update.isoformat() if m.last_update else None,
    )


def sale_to_entity(s: Sale) -> SaleEntity:
    """Converteix un model ORM Sale a SaleEntity."""
    if not s:
        return None
    menu_name = s.menu.menu_name if s.menu else None
    emp_name = f"{s.employee.name} {s.employee.surname}" if s.employee else None
    return SaleEntity(
        id_menu=s.id_menu,
        id_employee=s.id_employee,
        sale_date=str(s.sale_date),
        quantity_sold=s.quantity_sold,
        menu_name=menu_name,
        employee_name=emp_name,
        last_update=s.last_update.isoformat() if s.last_update else None,
    )
