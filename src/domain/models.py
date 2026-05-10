# models.py: defineix models ORM del projecte.
# Cada classe representa una taula de la bd's, cada atribut de classe representa columna.
# SQLAlchemy tradueix les operacions Python a SQL automàticament.

from .db import Base, engine
from sqlalchemy import Integer, String, Date, Boolean, Numeric, Table, Column, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import date
from typing import Optional


class Employee(Base):
    __tablename__ = "employee"

    # PK autoincrement: SQLAlchemy assigna ID automàticament
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(64), nullable=False)
    surname: Mapped[str] = mapped_column(String(64), nullable=False)

    # unique=True impedeix que dos empleats tinguin el mateix DNI a la bd's
    national_id: Mapped[str] = mapped_column(String(20), nullable=False, unique=True)
    role: Mapped[str] = mapped_column(String(20), nullable=False)

    # Relació 1:1 amb AppCredential.
    credentials: Mapped[Optional["AppCredential"]] = relationship(
        # uselist=False indica que és un sol objecte, no una llista.
        # cascade="all, delete-orphan": Si eliminem l'empleat, elimina les seves credencials automàticament.
        back_populates="employee", uselist=False, cascade="all, delete-orphan"
    )

    # Relació 1:N amb Sale: un empleat pot tenir moltes vendes.
    sales: Mapped[list["Sale"]] = relationship(
        # cascade="all, delete-orphan": Si eliminem empleat, eliminem les seves vendes.
        back_populates="employee", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"Employee(id={self.id}, name='{self.name}', role='{self.role}')"

    def __str__(self):
        return f"{self.id}: {self.surname}, {self.name} ({self.role})"


class AppCredential(Base):
    __tablename__ = "app_credential"

    # La PK és clau forana cap Employee. Cada empleat te unes credencials -> 1:1
    id_employee: Mapped[int] = mapped_column(
        # ondelete="CASCADE": Si eliminem empleat a bd's, credencials s'eliminen també.
        Integer, ForeignKey("employee.id", ondelete="CASCADE"), primary_key=True
    )

    # unique=True impedeix que dos empleats comparteixin el mateix email
    email: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)

    # Relació inversa cap Employee per poder accedir a l'empleat des de les credencials
    employee: Mapped["Employee"] = relationship(back_populates="credentials")

    def __repr__(self):
        return f"AppCredential(id_employee={self.id_employee}, email='{self.email}')"

    def __str__(self):
        return f"Credencials de {self.email}"


class Category(Base):
    __tablename__ = "category"

    id: Mapped[int] = mapped_column(primary_key=True)
    category_name: Mapped[str] = mapped_column(String(64), nullable=False)

    # 1:N amb Dish: una categoria pot tenir molts plats.
    dishes: Mapped[list["Dish"]] = relationship(
        # cascade="all, delete-orphan": Si eliminem categoria, eliminem els seus plats.
        back_populates="category", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"Category(id={self.id}, name='{self.category_name}')"

    def __str__(self):
        return self.category_name

# Taula intermèdia per relació N:M Dish i Allergen.
# SQLAlchemy la gestiona automàticament: quan fem dish.allergens.append(allergen),
# insereix la fila corresponent a aquesta taula sense que ho haguem de fer manualment.
dish_allergen = Table(
    "dish_allergen",
    Base.metadata,
    Column("id_dish",    ForeignKey("dish.id",    ondelete="CASCADE"), primary_key=True),
    Column("id_allergen", ForeignKey("allergen.id", ondelete="CASCADE"), primary_key=True),
)

# Taula intermèdia per relació N:M Menu i Dish.
# Un menú pot tenir molts plats, i un plat pot pertànyer a molts menús.
menu_dish = Table(
    "menu_dish",
    Base.metadata,
    Column("id_menu", ForeignKey("menu.id", ondelete="CASCADE"), primary_key=True),
    Column("id_dish", ForeignKey("dish.id", ondelete="CASCADE"), primary_key=True),
)

class Dish(Base):
    __tablename__ = "dish"

    id: Mapped[int] = mapped_column(primary_key=True)
    dish_name: Mapped[str] = mapped_column(String(64), nullable=False)

    # Optional[str] indica que descripció pot ser None (camp no obligatori)
    description: Mapped[Optional[str]] = mapped_column(String)
    
    # is_active permet desactivar plats sense eliminar-los de la bd's
    is_active: Mapped[bool] = mapped_column(default=True)

    # FK cap a Category: cada plat pertany a una categoria
    id_category: Mapped[int] = mapped_column(ForeignKey("category.id"), nullable=False)

    # Relació inversa cap a Category
    category: Mapped["Category"] = relationship(back_populates="dishes")

    # Relació N:M amb Allergen a través de taula intermèdia dish_allergen
    allergens: Mapped[list["Allergen"]] = relationship(
        secondary=dish_allergen, back_populates="dishes"
    )

    # Relació N:M amb Menu a través de taula intermèdia menu_dish
    menus: Mapped[list["Menu"]] = relationship(
        secondary=menu_dish, back_populates="dishes"
    )

    def __repr__(self):
        return f"Dish(id={self.id}, name='{self.dish_name}')"

    def __str__(self):
        return self.dish_name

class Allergen(Base):
    __tablename__ = "allergen"

    id: Mapped[int] = mapped_column(primary_key=True)
    allergen_name: Mapped[str] = mapped_column(String(64), nullable=False)

    # Relació N:M inversa amb Dish a través de taula intermèdia dish_allergen
    dishes: Mapped[list["Dish"]] = relationship(
        secondary=dish_allergen, back_populates="allergens"
    )

    def __repr__(self):
        return f"Allergen(id={self.id}, name='{self.allergen_name}')"

    def __str__(self):
        return self.allergen_name

class Menu(Base):
    __tablename__ = "menu"

    id: Mapped[int] = mapped_column(primary_key=True)
    menu_name: Mapped[str] = mapped_column(String(64), nullable=False)

    # Numeric(4, 2) permet guardar preus fins a 4 dígits totals i 2 decimals (ex: 99.99)
    price: Mapped[float] = mapped_column(Numeric(4, 2), nullable=False)

    # Relació N:M amb Dish a través de taula intermèdia menu_dish
    dishes: Mapped[list["Dish"]] = relationship(
        secondary=menu_dish, back_populates="menus"
    )

    # Relació 1:N amb Sale: un menú pot haver estat venut moltes vegades
    sales: Mapped[list["Sale"]] = relationship(
        back_populates="menu", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"Menu(id={self.id}, name='{self.menu_name}', price={self.price})"

    def __str__(self):
        return f"{self.menu_name} ({self.price}€)"

class Sale(Base):
    __tablename__ = "sale"

    # PK composta per tres camps: id_menu, id_employee i sale_date.
    # La combinació dels tres ha de ser única: Mateix empleat no pot vendre mateix menú dues vegades el mateix dia.
    id_menu: Mapped[int] = mapped_column(ForeignKey("menu.id"), primary_key=True)
    id_employee: Mapped[int] = mapped_column(ForeignKey("employee.id"), primary_key=True)
    sale_date: Mapped[date] = mapped_column(Date, primary_key=True)

    # Quantitat menús venuts en aquesta venda. Per defecte 1.
    quantity_sold: Mapped[int] = mapped_column(Integer, default=1)

    # Relacions inverses per accedir al menú i a l'empleat des d'una venda
    menu: Mapped["Menu"] = relationship(back_populates="sales")
    employee: Mapped["Employee"] = relationship(back_populates="sales")

    def __repr__(self):
        return f"Sale(menu={self.id_menu}, emp={self.id_employee}, date={self.sale_date})"

    def __str__(self):
        return f"Venda del {self.sale_date}: Menú ID {self.id_menu} venut per Empleat ID {self.id_employee}"
