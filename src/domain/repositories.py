"""
Aquest fitxer defineix la capa de persistència de dades (Repòsitoris).
L'objectiu és crear una capa intermèdia entre la base de dades i la lògica del programa.
D'aquesta manera, el programa no parla directament amb la base de dades, sinó que
fa servir aquests repositoris per guardar (save) o recuperar (get) objectes.
"""

from sqlalchemy.orm import Session
from collections.abc import Iterable # Què fa?
from .models import (
    Employee,
    Category,
    Menu,
    Dish,
    Sale,
    Allergen
)
from typing import Generic, TypeVar, Type
from sqlalchemy import select, or_


# Definim una variable de tipus genèrica 'T'.
# Això permet que la classe Repository serveixi per a qualsevol model (Category, Employee, etc.)
K = TypeVar("K")
V = TypeVar("V")

# El Repositori Genèric és un "motlle" o classe pare.
# Serveix per no haver de repetir el mateix codi per a cada taula de la base de dades.
class Repository(Generic[K, V]):
    # El constructor rep la 'session' (la connexió activa a la DB).
    # Passem la sessió per paràmetre per poder fer tests més fàcilment (injecció de dependències).
    def __init__(self, session: Session, model_class):
        self.session = session
        self.model_class = model_class

    # Mètode genèric per afegir un objecte a la sessió de la base de dades.
    def add(self, v: V): #Passem objecte("Taula") com a paràmetre
        self.session.add(v)

    def delete(self, k: K):
        v = self.get(k)
        self.session.delete(v)

    def update(self, v: V):
        self.session.merge(v)

    # Mètode genèric per buscar un element pel seu ID (clau primària).
    def get(self, id: K):
        # .get() és un mètode propi de SQLAlchemy que busca per ID.
        return self.session.get(self.model_class, id)

    def get_all(self) -> Iterable[V]:
        stmt = select(self.model_class)
        return self.session.scalars(stmt).all()

# Repositori per a Empleats.
# Nota per a l'alumne: Utilitza la mateixa estructura que CategoryRepository per gestionar dades d'Employee.
class EmployeeRepository(Repository[int, Employee]):
    def __init__(self, session: Session):
        super().__init__(session, Employee) #Lliguem repositori a model Employee

    def get_by_name(self, name_surname: str) -> Employee:
        return self.session.scalars( #scalars desempaqueta tupla retornada  per la base de dades.
            select(Employee).where(
                or_(
                    Employee.name.ilike(f"%{name_surname}%"),
                    Employee.surname.ilike(f"%{name_surname}%")
                )
            )
        ).all() #.all() guarda tots els resulstats en una llista de python.

    def get_by_rol(self, rol: str) -> list[Employee]:
        return self.session.scalars(
            select(Employee).where(Employee.role == rol)
        ).all()

    def national_id_exist(self, national_id: str) -> bool:
        result = self.session.scalars(
            select(Employee).where(Employee.national_id == national_id)
        ).first()
        return result is not None


class MenuRepository(Repository[int, Menu]):
    def __init__(self, session: Session):
        super().__init__(session, Menu)
        
    def add_dish_to_menu(self, menu_id: int, dish: Dish):
        # Operació de domini concreta: afegir un plat a un menú existent
        menu = self.get(menu_id)
        if menu:
            menu.dishes.append(dish)

class SaleRepository(Repository[tuple, Sale]):
    def __init__(self, session: Session):
        super().__init__(session, Sale)
        
    def get_paginated(self, page: int, page_size: int) -> list[Sale]:
        # Paginació per a l'entitat que probablement tindrà més dades (Sales)
        stmt = select(Sale).offset((page - 1) * page_size).limit(page_size)
        return self.session.scalars(stmt).all()

    def get_sales_by_date(self, target_date) -> list[Sale]:
        return self.session.scalars(
            select(Sale).where(Sale.sale_date == target_date)
        ).all()

class DishRepository(Repository[int, Dish]):
    def __init__(self, session: Session):
        super().__init__(session, Dish)
        
    def get_active_dishes(self) -> list[Dish]:
        return self.session.scalars(
            select(Dish).where(Dish.is_active == True)
        ).all()

class AllergenRepository(Repository[int, Allergen]):
    def __init__(self, session: Session):
        super().__init__(session, Allergen)

class CategoryRepository(Repository[int, Category]):
    def __init__(self, session: Session):
        super().__init__(session, Category)