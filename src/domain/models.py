from .db import Base, engine
from sqlalchemy import Integer, String, Date, Boolean, Numeric, Table, Column, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship, sessionmaker, Session
from datetime import date
from typing import Optional

class Employee(Base):
    __tablename__ = "employee"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(64), nullable=False)
    surname: Mapped[str] = mapped_column(String(64), nullable=False)
    national_id: Mapped[str] = mapped_column(String(20), nullable=False, unique=True)
    role: Mapped[str] = mapped_column(String(20), nullable=False)

    credentials: Mapped[Optional["AppCredential"]] = relationship(back_populates="employee", uselist=False)

    sales: Mapped[list["Sale"]] = relationship(back_populates="employee")


class AppCredential(Base):
    __tablename__ = "app_credential"

    id_employee: Mapped[int] = mapped_column(Integer, ForeignKey("employee.id", ondelete="CASCADE"), primary_key=True)

    email: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)

    employee: Mapped["Employee"] = relationship(back_populates="credentials")


class Category(Base):
    __tablename__ = "category"

    id: Mapped[int] = mapped_column(primary_key=True)
    category_name: Mapped[str] = mapped_column(String(64), nullable=False)

    dishes: Mapped[list["Dish"]] = relationship(back_populates="category")

dish_allergen = Table(
    "dish_allergen",
    Base.metadata,
    Column("id_dish", ForeignKey("dish.id", ondelete="CASCADE"), primary_key=True),
    Column("id_allergen", ForeignKey("allergen.id", ondelete="CASCADE"), primary_key=True),
)

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
    description: Mapped[Optional[str]] = mapped_column(String)
    is_active: Mapped[bool] = mapped_column(default=True)

    id_category: Mapped[int] = mapped_column(ForeignKey("category.id"), nullable=False)

    category: Mapped["Category"] = relationship(back_populates="dishes")

    allergens: Mapped[list["Allergen"]] = relationship(
        secondary=dish_allergen, back_populates="dishes"
    )
    menus: Mapped[list["Menu"]] = relationship(
        secondary=menu_dish, back_populates="dishes"
    )


class Allergen(Base):
    __tablename__ = "allergen"

    id: Mapped[int] = mapped_column(primary_key=True)
    allergen_name: Mapped[str] = mapped_column(String(64), nullable=False)

    dishes: Mapped[list["Dish"]] = relationship(
        secondary=dish_allergen, back_populates="allergens"
    )


class Menu(Base):
    __tablename__ = "menu"

    id: Mapped[int] = mapped_column(primary_key=True)
    menu_name: Mapped[str] = mapped_column(String(64), nullable=False)
    price: Mapped[float] = mapped_column(Numeric(4, 2), nullable=False)

    dishes: Mapped[list["Dish"]] = relationship(
        secondary=menu_dish, back_populates="menus"
    )

    sales: Mapped[list["Sale"]] = relationship(back_populates="menu")


class Sale(Base):
    __tablename__ = "sale"

    # Clau primària composta per id_menu i id_employee
    id_menu: Mapped[int] = mapped_column(ForeignKey("menu.id"), primary_key=True)
    id_employee: Mapped[int] = mapped_column(ForeignKey("employee.id"), primary_key=True)

    sale_date: Mapped[date] = mapped_column(Date, primary_key=True)
    quantity_sold: Mapped[int] = mapped_column(Integer, default=1)

    menu: Mapped["Menu"] = relationship(back_populates="sales")
    employee: Mapped["Employee"] = relationship(back_populates="sales")