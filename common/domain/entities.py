# entities.py: Defineix les entitats pures del domini de la nostra aplicació.
#
# CONCEPTE CLAU PER A DAM (Clean Domain / Domini Net):
# Aquestes classes representen la informació del nostre negoci (plats, empleats, categories...)
# de forma 100% independent de qualsevol tecnologia de persistència
# (com SQLAlchemy o SQLite/PostgreSQL).
#
# Per què ho fem així?
# 1. Independència: El client mai ha d'importar 'sqlalchemy' ni dependre de la base de dades.
# 2. Reutilització: El mateix fitxer d'entitats pot viure a la carpeta 'common/' i ser
#    utilitzat tant pel Servidor (per crear respostes) com pel Client
#    (per rebre dades i pintar a la UI).
# 3. Serialització fàcil: Cada classe té mètodes 'to_dict()' i 'from_dict()' per convertir
#    les dades a diccionari Python -> JSON -> bytes per viatjar pel socket TCP.

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


# Entitat de domini: Classe pura de python que representa concepte clau de negoci -> Categories
# Completament independent de la base de dades
# Fa que client i servidor parlin mateixes dades convertin dades JSON a Objectes Python
@dataclass
class CategoryEntity:
    """
    Entitat de domini que representa una Categoria de plats.
    Només conté les dades pròpies de la categoria, sense dependència d'SQLAlchemy.
    """

    id: Optional[int] = None
    category_name: str = ""
    last_update: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Converteix l'entitat a un diccionari llest per ser serialitzat a JSON."""
        # Quan fem un POST o PUT al servidor, hem d'enviar un diccionari que es convertirà a JSON.
        return {
            "id": self.id,
            "category_name": self.category_name,
            "last_update": self.last_update,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CategoryEntity":
        """Crea una instància de CategoryEntity a partir d'un diccionari (deserialització JSON)."""
        # S'utilitza quan rebem JSON del servidor (resp.data), el passem a diccionari,
        # i volem "reconstruir" l'objecte en Python.
        return cls(
            id=data.get("id"),
            category_name=data.get("category_name", ""),
            last_update=data.get("last_update"),
        )

    def __repr__(self) -> str:
        return f"CategoryEntity(id={self.id}, category_name='{self.category_name}')"

    def __str__(self) -> str:
        return self.category_name


@dataclass
class AllergenEntity:
    """
    Entitat de domini per als Al·lèrgens (ex: Gluten, Lactosa, Fruits secs).
    """

    id: Optional[int] = None
    allergen_name: str = ""
    last_update: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "allergen_name": self.allergen_name,
            "last_update": self.last_update,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AllergenEntity":
        return cls(
            id=data.get("id"),
            allergen_name=data.get("allergen_name", ""),
            last_update=data.get("last_update"),
        )

    def __repr__(self) -> str:
        return f"AllergenEntity(id={self.id}, allergen_name='{self.allergen_name}')"

    def __str__(self) -> str:
        return self.allergen_name


@dataclass
class DishEntity:
    """
    Entitat de domini per a un Plat.
    Inclou les dades de la seva categoria (1:N) i la llista dels seus al·lèrgens (N:M).
    """

    id: Optional[int] = None
    dish_name: str = ""
    description: Optional[str] = None
    is_active: bool = True
    id_category: int = 0
    category_name: Optional[str] = None
    allergens: List[AllergenEntity] = field(default_factory=list)
    last_update: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "dish_name": self.dish_name,
            "description": self.description,
            "is_active": self.is_active,
            "id_category": self.id_category,
            "category_name": self.category_name,
            "allergens": [allergen.to_dict() for allergen in self.allergens],
            "last_update": self.last_update,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DishEntity":
        raw_allergens = data.get("allergens", [])
        allergens = [
            AllergenEntity.from_dict(allergen) if isinstance(allergen, dict) else allergen
            for allergen in raw_allergens
        ]
        return cls(
            id=data.get("id"),
            dish_name=data.get("dish_name", ""),
            description=data.get("description"),
            is_active=bool(data.get("is_active", True)),
            id_category=int(data.get("id_category", 0)),
            category_name=data.get("category_name"),
            allergens=allergens,
            last_update=data.get("last_update"),
        )

    def __repr__(self) -> str:
        return f"DishEntity(id={self.id}, name='{self.dish_name}', active={self.is_active})"

    def __str__(self) -> str:
        return self.dish_name


@dataclass
class EmployeeEntity:
    """
    Entitat de domini per a un Empleat del restaurant.
    Per motius de seguretat, mai viatja el hash de contrasenya cap al client.
    Només indiquem si té credencials creades (relació 1:1) i el seu email.
    """

    id: Optional[int] = None
    name: str = ""
    surname: str = ""
    national_id: str = ""
    role: str = ""
    has_credentials: bool = False
    email: Optional[str] = None
    last_update: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "surname": self.surname,
            "national_id": self.national_id,
            "role": self.role,
            "has_credentials": self.has_credentials,
            "email": self.email,
            "last_update": self.last_update,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EmployeeEntity":
        return cls(
            id=data.get("id"),
            name=data.get("name", ""),
            surname=data.get("surname", ""),
            national_id=data.get("national_id", ""),
            role=data.get("role", ""),
            has_credentials=bool(data.get("has_credentials", False)),
            email=data.get("email"),
            last_update=data.get("last_update"),
        )

    def __repr__(self) -> str:
        return f"EmployeeEntity(id={self.id}, name='{self.name}', role='{self.role}')"

    def __str__(self) -> str:
        return f"{self.id}: {self.surname}, {self.name} ({self.role})"


@dataclass
class MenuEntity:
    """
    Entitat de domini per a un Menú.
    Té un preu i una llista de plats associats (relació N:M a través de menu_dish).
    """

    id: Optional[int] = None
    menu_name: str = ""
    price: float = 0.0
    dishes: List[DishEntity] = field(default_factory=list)
    last_update: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "menu_name": self.menu_name,
            "price": float(self.price),
            "dishes": [dish.to_dict() for dish in self.dishes],
            "last_update": self.last_update,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MenuEntity":
        raw_dishes = data.get("dishes", [])
        dishes = [
            DishEntity.from_dict(dish) if isinstance(dish, dict) else dish for dish in raw_dishes
        ]
        return cls(
            id=data.get("id"),
            menu_name=data.get("menu_name", ""),
            price=float(data.get("price", 0.0)),
            dishes=dishes,
            last_update=data.get("last_update"),
        )

    def __repr__(self) -> str:
        return f"MenuEntity(id={self.id}, menu_name='{self.menu_name}', price={self.price})"

    def __str__(self) -> str:
        return f"{self.menu_name} ({self.price}€)"


@dataclass
class SaleEntity:
    """
    Entitat de domini per a una Venda (N:M amb atributs).
    Clau primària composta per (id_menu, id_employee, sale_date).
    """

    id_menu: int = 0
    id_employee: int = 0
    sale_date: str = ""  # Format ISO: 'YYYY-MM-DD'
    quantity_sold: int = 1
    menu_name: Optional[str] = None
    employee_name: Optional[str] = None
    last_update: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id_menu": self.id_menu,
            "id_employee": self.id_employee,
            "sale_date": str(self.sale_date),
            "quantity_sold": self.quantity_sold,
            "menu_name": self.menu_name,
            "employee_name": self.employee_name,
            "last_update": self.last_update,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SaleEntity":
        return cls(
            id_menu=int(data.get("id_menu", 0)),
            id_employee=int(data.get("id_employee", 0)),
            sale_date=str(data.get("sale_date", "")),
            quantity_sold=int(data.get("quantity_sold", 1)),
            menu_name=data.get("menu_name"),
            employee_name=data.get("employee_name"),
            last_update=data.get("last_update"),
        )

    def __repr__(self) -> str:
        return f"SaleEntity(menu={self.id_menu}, emp={self.id_employee}, date='{self.sale_date}')"

    def __str__(self) -> str:
        return (
            f"Venda {self.sale_date}: Menú #{self.id_menu} "
            f"venut per Empleat #{self.id_employee} (x{self.quantity_sold})"
        )
