# repositories.py defineix capa de persistència de dades mitjançant el patró Repositori.
# Crea capa intermèdia entre la bd's i la lògica del programa.
# El programa no parla directament amb la bd's, fa servir repositoris per guardar (add) o recuperar (get) objectes.

from sqlalchemy.orm import Session
from collections.abc import Iterable
from .models import (
    Employee,
    Category,
    Menu,
    Dish,
    Sale,
    Allergen
)
from typing import Generic, TypeVar
from sqlalchemy import select, or_, and_

# TypeVar permet definir tipus genèrics.
K = TypeVar("K") # K: Tipus de la clau primària (normalment int, però tuple per a Sale)
V = TypeVar("V") # V: Tipus del model (Category, Employee, Dish...)

# Repositori Genèric: classe pare que conté operacions CRUD bàsiques.
# Amb Generic[K, V], aquesta classe funciona per qualsevol model sense repetir el mateix codi a cada fill.
class Repository(Generic[K, V]):

    # El constructor rep sessió activa i classe del model que gestionarà.
    def __init__(self, session: Session, model_class):
        self.session = session
        self.model_class = model_class

    # Indica objecte a inserit a la bd's. Executa INSERT quan es fa commit (a Unit of Work).
    def add(self, v: V):
        self.session.add(v)

    # Busca l'objecte per ID, l'eliminació no s'executa fins que es fa commit.
    def delete(self, k: K):
        v = self.get(k)
        self.session.delete(v)

    # Sincronitza objecte modificat amb bd's.
    def update(self, v: V):
        self.session.merge(v) # merge() és útil quan l'objecte pot estar "desconnectat" de la sessió actual.

    # Busca objecte per clau primària. Retorna l'objecte si existeix, o None si no es troba.
    def get(self, id: K):
        return self.session.get(self.model_class, id)

    # Retorna tots els registres de la taula associada al model.
    def get_all(self) -> Iterable[V]:
        stmt = select(self.model_class)
        return self.session.scalars(stmt).all() # scalars() desempaqueta les tuples que retorna la BD i .all() les guarda en una llista.

class CategoryRepository(Repository[int, Category]):
    def __init__(self, session: Session):
        super().__init__(session, Category)
    
    # Sobreescriure un mètode del pare perque get_all retorni les categories ordenades per ID.
    def get_all(self) -> list[Category]:
        # 2. Has demostrat que entens com fer consultes SQL específiques
        return self.session.scalars(
            select(Category).order_by(Category.id)
        ).all()

    def add(self, category: Category):
        # Validació: no permetem categories amb el mateix nom. Comprovem abans d'inserir per evitar errors de la bd's.
        if self.get_by_name(category.category_name):
            raise ValueError(f"Category '{category.category_name}' already exists.")
        super().add(category)

    def update(self, category: Category):
        # Validació: comprovem que el nou nom no existeixi en altra categoria.
        existing = self.get_by_name(category.category_name)
        # existing.id != category.id assegura que no comparem la categoria amb si mateixa.
        if existing and existing.id != category.id:
            raise ValueError(f"Category name '{category.category_name}' is already taken.")
        super().update(category)

    # Busca nom exacte, insensible a majúscules gràcies a ilike().
    def get_by_name(self, name: str) -> Category | None:
        return self.session.scalars(
            select(Category).where(Category.category_name.ilike(name))
        ).first() # first() retorna el primer resultat o None si no hi ha cap.


class AllergenRepository(Repository[int, Allergen]):
    def __init__(self, session: Session):
        super().__init__(session, Allergen)

    # Cerca per nom exacte.
    def get_by_name(self, name: str) -> Allergen | None:
        return self.session.scalars(
            select(Allergen).where(Allergen.allergen_name.ilike(name))
        ).first()


class DishRepository(Repository[int, Dish]):
    def __init__(self, session: Session):
        super().__init__(session, Dish)

    # Retorna només els plats que estan marcats com a actius (is_active = True).
    def get_active_dishes(self) -> list[Dish]:
        return self.session.scalars(
            select(Dish).where(Dish.is_active == True)
        ).all() # all() retorna una llista amb tots els plats actius. Si no hi ha cap, retorna una llista buida.

    # Filtra els plats per la seva categoria.
    def get_by_category(self, category_id: int) -> list[Dish]:
        return self.session.scalars(
            select(Dish).where(Dish.id_category == category_id)
        ).all()

    # Cerca parcial de nom: '%'' permeten trobar text en qualsevol posició del nom.
    def get_by_name(self, name: str) -> list[Dish]:
        return self.session.scalars(
            select(Dish).where(Dish.dish_name.ilike(f"%{name}%"))
        ).all()

    # Afegeix un al·lèrgen a un plat sense actualitzar tot l'objecte.
    def add_allergen_to_dish(self, dish_id: int, allergen: Allergen) -> bool:
        dish = self.get(dish_id)
        #Retorna False si el plat no existeix o si l'al·lèrgen ja hi era.
        if dish is None or allergen in dish.allergens:
            return False
        dish.allergens.append(allergen) # SQLAlchemy insereix fila a taula intermèdia dish_allergen.
        return True


class EmployeeRepository(Repository[int, Employee]):
    def __init__(self, session: Session):
        super().__init__(session, Employee)

    def add(self, employee: Employee):
        # Validació: DNI és únic, no podem tenir dos empleats amb el mateix.
        if self.national_id_exists(employee.national_id):
            raise ValueError(f"Employee with national ID '{employee.national_id}' already exists.")
        super().add(employee)

    # Cerca per nom o cognom amb cerca parcial insensible a majúscules.
    def get_by_name(self, name: str = "", surname: str = "") -> list[Employee]:
        conditions = []
        if name:
            conditions.append(Employee.name.ilike(f"%{name}%"))
        if surname:
            conditions.append(Employee.surname.ilike(f"%{surname}%"))
        return self.session.scalars(
            select(Employee).where(and_(*conditions))
        ).all()

    # Filtra els empleats per rol ()"Cambrer", "Cuiner", "Encarregat"...).
    def get_by_role(self, role: str) -> list[Employee]:
        return self.session.scalars(
            select(Employee).where(Employee.role == role)
        ).all()

    # Comprova si ja existeix un empleat amb aquest DNI.
    def national_id_exists(self, national_id: str) -> bool:
        result = self.session.scalars(
            select(Employee).where(Employee.national_id == national_id)
        ).first()
        return result is not None # Retorna True si existeix, False si no. Valida abans d'inserir

    # Paginació: retorna només una "pàgina" d'empleats.
    def get_paginated(self, page: int, page_size: int) -> list[Employee]:
        # offset() salta registres de pàgines anteriors. limit() limita el nombre de resultats.
        stmt = select(Employee).offset((page - 1) * page_size).limit(page_size)
        return self.session.scalars(stmt).all() # all() retorna llista amb empleats de la pàgina. Si no hi ha, retornallista buida.

class MenuRepository(Repository[int, Menu]):
    def __init__(self, session: Session):
        super().__init__(session, Menu)

    # Cerca parcial per nom de menú, insensible a majúscules.
    def get_by_name(self, name: str) -> list[Menu]:
        return self.session.scalars(
            select(Menu).where(Menu.menu_name.ilike(f"%{name}%"))
        ).all()

    # Filtra menús per rang de preus.
    def get_by_price_range(self, min_price: float, max_price: float) -> list[Menu]:
        return self.session.scalars(
            select(Menu).where(
                Menu.price >= min_price,
                Menu.price <= max_price
            )
        ).all()

    # Afegeix plat a un menú sense actualitzar tot l'objecte.
    def add_dish_to_menu(self, menu_id: int, dish: Dish):
        menu = self.get(menu_id)
        # Comprova que el plat no hi sigui per evitar duplicats a la taula menu_dish.
        if menu and dish not in menu.dishes:
            menu.dishes.append(dish)

    # Elimina un plat de menú.
    def remove_dish_from_menu(self, menu_id: int, dish: Dish) -> bool:
        menu = self.get(menu_id)
        if menu is None or dish not in menu.dishes:
            return False # Retorna False si el menú no existeix o si el plat no hi és.
        menu.dishes.remove(dish)
        return True 

# SaleRepository hereta de Repository[tuple, Sale] perquè PK de Sale és composta (id_menu, id_employee, sale_date)
# Per fer un get() cal passar tupla: uow.sales.get((id_menu, id_employee, date)).
class SaleRepository(Repository[tuple, Sale]):
    def __init__(self, session: Session):
        super().__init__(session, Sale)

    # Paginació per vendes
    def get_paginated(self, page: int, page_size: int) -> list[Sale]:
        stmt = select(Sale).offset((page - 1) * page_size).limit(page_size)
        return self.session.scalars(stmt).all()

    # Retorna totes les vendes d'un dia concret.
    def get_sales_by_date(self, target_date) -> list[Sale]:
        return self.session.scalars(
            select(Sale).where(Sale.sale_date == target_date)
        ).all()

    # Retorna totes les vendes fetes per un empleat concret.
    def get_sales_by_employee(self, employee_id: int) -> list[Sale]:
        return self.session.scalars(
            select(Sale).where(Sale.id_employee == employee_id)
        ).all()

    # Retorna totes les vendes d'un menú concret.
    def get_sales_by_menu(self, menu_id: int) -> list[Sale]:
        return self.session.scalars(
            select(Sale).where(Sale.id_menu == menu_id)
        ).all()

    # Retorna les vendes dins de rang de dates.
    def get_sales_by_date_range(self, date_from, date_to) -> list[Sale]:
        return self.session.scalars(
            select(Sale).where(
                Sale.sale_date >= date_from,
                Sale.sale_date <= date_to
            )
        ).all()