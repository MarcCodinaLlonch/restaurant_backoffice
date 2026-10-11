# repositories.py defineix la capa de persistència de dades mitjançant el patró Repositori.
# Crea una capa intermèdia entre la base de dades i la lògica del programa.
# El programa no parla directament amb SQL, fa servir repositoris per guardar (add),
# recuperar (get), actualitzar (update) o esborrar (delete) objectes.

from sqlalchemy.orm import Session
from collections.abc import Iterable
from .models import (
    Employee,
    Category,
    Menu,
    Dish,
    Sale,
    Allergen,
    AppCredential
)
from typing import Generic, TypeVar, Optional, List
from sqlalchemy import select, and_

# TypeVar permet definir tipus genèrics.
K = TypeVar("K")  # K: Tipus de la clau primària (int, o tupla per a Sale)
V = TypeVar("V")  # V: Tipus del model ORM (Category, Employee, Dish...)


class Repository(Generic[K, V]):
    """
    Repositori Genèric: classe base amb operacions CRUD bàsiques.
    Generic[K, V] permet reutilitzar codi per a qualsevol model.
    """

    def __init__(self, session: Session, model_class):
        self.session = session
        self.model_class = model_class

    def add(self, v: V):
        self.session.add(v)

    def delete(self, k: K):
        v = self.get(k)
        if v:
            self.session.delete(v)

    def update(self, v: V):
        return self.session.merge(v)

    def get(self, id: K) -> Optional[V]:
        return self.session.get(self.model_class, id)

    def get_all(self) -> Iterable[V]:
        stmt = select(self.model_class)
        return self.session.scalars(stmt).all()


class CategoryRepository(Repository[int, Category]):
    def __init__(self, session: Session):
        super().__init__(session, Category)

    def get_all(self) -> list[Category]:
        return list(self.session.scalars(
            select(Category).order_by(Category.id)
        ).all())

    def add(self, category: Category):
        if self.get_by_name(category.category_name):
            raise ValueError(f"Category '{category.category_name}' already exists.")
        super().add(category)

    def update(self, category: Category):
        existing = self.get_by_name(category.category_name)
        if existing and existing.id != category.id:
            raise ValueError(f"Category name '{category.category_name}' is already taken.")
        return super().update(category)

    def get_by_name(self, name: str) -> Optional[Category]:
        return self.session.scalars(
            select(Category).where(Category.category_name.ilike(name))
        ).first()


class AllergenRepository(Repository[int, Allergen]):
    def __init__(self, session: Session):
        super().__init__(session, Allergen)

    def get_all(self) -> list[Allergen]:
        return list(self.session.scalars(
            select(Allergen).order_by(Allergen.id)
        ).all())

    def get_by_name(self, name: str) -> Optional[Allergen]:
        return self.session.scalars(
            select(Allergen).where(Allergen.allergen_name.ilike(name))
        ).first()


class DishRepository(Repository[int, Dish]):
    def __init__(self, session: Session):
        super().__init__(session, Dish)

    def get_all(self) -> list[Dish]:
        return list(self.session.scalars(
            select(Dish).order_by(Dish.id)
        ).all())

    def get_active_dishes(self) -> list[Dish]:
        return list(self.session.scalars(
            select(Dish).where(Dish.is_active == True).order_by(Dish.id)
        ).all())

    def get_by_category(self, category_id: int) -> list[Dish]:
        return list(self.session.scalars(
            select(Dish).where(Dish.id_category == category_id).order_by(Dish.id)
        ).all())

    def get_by_name(self, name: str) -> list[Dish]:
        return list(self.session.scalars(
            select(Dish).where(Dish.dish_name.ilike(f"%{name}%")).order_by(Dish.id)
        ).all())

    def add_allergen_to_dish(self, dish_id: int, allergen: Allergen) -> bool:
        dish = self.get(dish_id)
        if dish is None or allergen in dish.allergens:
            return False
        dish.allergens.append(allergen)
        return True


class EmployeeRepository(Repository[int, Employee]):
    def __init__(self, session: Session):
        super().__init__(session, Employee)

    def get_all(self) -> list[Employee]:
        return list(self.session.scalars(
            select(Employee).order_by(Employee.id)
        ).all())

    def add(self, employee: Employee):
        if self.national_id_exists(employee.national_id):
            raise ValueError(f"Employee with national ID '{employee.national_id}' already exists.")
        super().add(employee)

    def get_by_name(self, name: str = "", surname: str = "") -> list[Employee]:
        conditions = []
        if name:
            conditions.append(Employee.name.ilike(f"%{name}%"))
        if surname:
            conditions.append(Employee.surname.ilike(f"%{surname}%"))
        if not conditions:
            return self.get_all()
        return list(self.session.scalars(
            select(Employee).where(and_(*conditions)).order_by(Employee.id)
        ).all())

    def get_by_role(self, role: str) -> list[Employee]:
        return list(self.session.scalars(
            select(Employee).where(Employee.role == role).order_by(Employee.id)
        ).all())

    def national_id_exists(self, national_id: str) -> bool:
        result = self.session.scalars(
            select(Employee).where(Employee.national_id == national_id)
        ).first()
        return result is not None

    def get_paginated(self, page: int, page_size: int) -> list[Employee]:
        stmt = select(Employee).order_by(Employee.id).offset((page - 1) * page_size).limit(page_size)
        return list(self.session.scalars(stmt).all())


class MenuRepository(Repository[int, Menu]):
    def __init__(self, session: Session):
        super().__init__(session, Menu)

    def get_all(self) -> list[Menu]:
        return list(self.session.scalars(
            select(Menu).order_by(Menu.id)
        ).all())

    def get_by_name(self, name: str) -> list[Menu]:
        return list(self.session.scalars(
            select(Menu).where(Menu.menu_name.ilike(f"%{name}%")).order_by(Menu.id)
        ).all())

    def get_by_price_range(self, min_price: float, max_price: float) -> list[Menu]:
        return list(self.session.scalars(
            select(Menu).where(
                Menu.price >= min_price,
                Menu.price <= max_price
            ).order_by(Menu.id)
        ).all())

    def add_dish_to_menu(self, menu_id: int, dish: Dish) -> bool:
        menu = self.get(menu_id)
        if menu and dish not in menu.dishes:
            menu.dishes.append(dish)
            return True
        return False

    def remove_dish_from_menu(self, menu_id: int, dish: Dish) -> bool:
        menu = self.get(menu_id)
        if menu is None or dish not in menu.dishes:
            return False
        menu.dishes.remove(dish)
        return True


class SaleRepository(Repository[tuple, Sale]):
    def __init__(self, session: Session):
        super().__init__(session, Sale)

    def get_all(self) -> list[Sale]:
        return list(self.session.scalars(
            select(Sale).order_by(Sale.sale_date.desc())
        ).all())

    def get_paginated(self, page: int, page_size: int) -> list[Sale]:
        stmt = select(Sale).order_by(Sale.sale_date.desc()).offset((page - 1) * page_size).limit(page_size)
        return list(self.session.scalars(stmt).all())

    def get_sales_by_date(self, target_date) -> list[Sale]:
        return list(self.session.scalars(
            select(Sale).where(Sale.sale_date == target_date)
        ).all())

    def get_sales_by_employee(self, employee_id: int) -> list[Sale]:
        return list(self.session.scalars(
            select(Sale).where(Sale.id_employee == employee_id)
        ).all())

    def get_sales_by_menu(self, menu_id: int) -> list[Sale]:
        return list(self.session.scalars(
            select(Sale).where(Sale.id_menu == menu_id)
        ).all())

    def get_sales_by_date_range(self, date_from, date_to) -> list[Sale]:
        return list(self.session.scalars(
            select(Sale).where(
                Sale.sale_date >= date_from,
                Sale.sale_date <= date_to
            )
        ).all())
