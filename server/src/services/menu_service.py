# menu_service.py: Lògica de negoci per a la Gestió de Menús.
# Gestiona la relació N:M amb Dish a través de la taula intermèdia menu_dish.

from typing import List, Optional

from common.domain.entities import MenuEntity
from server.src.persistence.mappers import menu_to_entity
from server.src.persistence.models import Menu
from server.src.persistence.unit_of_work import UnitOfWorkFactory


class MenuService:
    def __init__(self, uow_factory: UnitOfWorkFactory) -> None:
        self.uow_factory = uow_factory

    def get_all(self) -> List[MenuEntity]:
        """Recupera tots els menús disponibles."""
        with self.uow_factory.create() as uow:
            menus = uow.menus.get_all()
            return [menu_to_entity(menu) for menu in menus]

    def get_by_id(self, menu_id: int) -> Optional[MenuEntity]:
        """Recupera un menú pel seu ID."""
        with self.uow_factory.create() as uow:
            menu = uow.menus.get(menu_id)
            if not menu:
                return None
            return menu_to_entity(menu)

    def search_by_name(self, name: str) -> List[MenuEntity]:
        """Cerca menús pel seu nom."""
        clean_name = (name or "").strip()
        if not clean_name:
            return self.get_all()
        with self.uow_factory.create() as uow:
            menus = uow.menus.get_by_name(clean_name)
            return [menu_to_entity(menu) for menu in menus]

    def filter_by_price_range(self, min_price: float, max_price: float) -> List[MenuEntity]:
        """Filtra menús dins d'un interval de preus."""
        if min_price > max_price:
            raise ValueError("El preu mínim no pot ser superior al preu màxim.")
        with self.uow_factory.create() as uow:
            menus = uow.menus.get_by_price_range(min_price, max_price)
            return [menu_to_entity(menu) for menu in menus]

    def create(self, menu_name: str, price: float) -> MenuEntity:
        """Crea un nou menú."""
        clean_name = (menu_name or "").strip()
        if not clean_name:
            raise ValueError("El nom del menú no pot estar buit.")
        if price <= 0:
            raise ValueError("El preu ha de ser un número positiu.")

        with self.uow_factory.create() as uow:
            new_menu = Menu(menu_name=clean_name, price=price)
            uow.menus.add(new_menu)
            return menu_to_entity(new_menu)

    def update(
        self, menu_id: int, menu_name: Optional[str] = None, price: Optional[float] = None
    ) -> Optional[MenuEntity]:
        """Actualitza el nom o el preu d'un menú."""
        with self.uow_factory.create() as uow:
            menu = uow.menus.get(menu_id)
            if not menu:
                return None

            if menu_name is not None and menu_name.strip():
                menu.menu_name = menu_name.strip()
            if price is not None:
                if price <= 0:
                    raise ValueError("El preu ha de ser un número positiu.")
                menu.price = price

            uow.menus.update(menu)
            return menu_to_entity(menu)

    def delete(self, menu_id: int) -> bool:
        """Elimina un menú."""
        with self.uow_factory.create() as uow:
            menu = uow.menus.get(menu_id)
            if not menu:
                return False
            uow.menus.delete(menu_id)
            return True

    def add_dish(self, menu_id: int, dish_id: int) -> bool:
        """Afegeix un plat a un menú (relació N:M)."""
        with self.uow_factory.create() as uow:
            menu = uow.menus.get(menu_id)
            if not menu:
                raise ValueError(f"No s'ha trobat el menú amb ID {menu_id}.")
            dish = uow.dishes.get(dish_id)
            if not dish:
                raise ValueError(f"No s'ha trobat el plat amb ID {dish_id}.")
            return uow.menus.add_dish_to_menu(menu_id, dish)

    def remove_dish(self, menu_id: int, dish_id: int) -> bool:
        """Elimina un plat d'un menú (relació N:M)."""
        with self.uow_factory.create() as uow:
            menu = uow.menus.get(menu_id)
            if not menu:
                raise ValueError(f"No s'ha trobat el menú amb ID {menu_id}.")
            dish = uow.dishes.get(dish_id)
            if not dish:
                raise ValueError(f"No s'ha trobat el plat amb ID {dish_id}.")
            return uow.menus.remove_dish_from_menu(menu_id, dish)
