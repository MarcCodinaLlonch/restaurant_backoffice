# dish_service.py: Lògica de negoci per a la Gestió de Plats.
# Gestiona la relació 1:N amb Category i N:M amb Allergen.

from typing import List, Optional
from common.domain.entities import DishEntity
from server.src.persistence.unit_of_work import UnitOfWorkFactory
from server.src.persistence.models import Dish
from server.src.persistence.mappers import dish_to_entity


class DishService:
    def __init__(self, uow_factory: UnitOfWorkFactory):
        self.uow_factory = uow_factory

    def get_all(self) -> List[DishEntity]:
        """Recupera tots els plats del restaurant."""
        with self.uow_factory.create() as uow:
            dishes = uow.dishes.get_all()
            return [dish_to_entity(d) for d in dishes]

    def get_by_id(self, dish_id: int) -> Optional[DishEntity]:
        """Recupera un plat pel seu identificador."""
        with self.uow_factory.create() as uow:
            dish = uow.dishes.get(dish_id)
            if not dish:
                return None
            return dish_to_entity(dish)

    def get_active(self) -> List[DishEntity]:
        """Recupera únicament els plats que estan en estat actiu."""
        with self.uow_factory.create() as uow:
            dishes = uow.dishes.get_active_dishes()
            return [dish_to_entity(d) for d in dishes]

    def search_by_name(self, name: str) -> List[DishEntity]:
        """Cerca plats pel seu nom o part del nom."""
        clean_name = (name or "").strip()
        if not clean_name:
            return self.get_all()
        with self.uow_factory.create() as uow:
            dishes = uow.dishes.get_by_name(clean_name)
            return [dish_to_entity(d) for d in dishes]

    def create(
        self,
        dish_name: str,
        id_category: int,
        description: Optional[str] = None,
        is_active: bool = True
    ) -> DishEntity:
        """Crea un nou plat associat a una categoria existent (1:N)."""
        clean_name = (dish_name or "").strip()
        if not clean_name:
            raise ValueError("El nom del plat no pot estar buit.")

        with self.uow_factory.create() as uow:
            # Validació de clau forana: la categoria ha d'existir
            cat = uow.categories.get(id_category)
            if not cat:
                raise ValueError(f"No existeix cap categoria amb ID {id_category}.")

            nou_plat = Dish(
                dish_name=clean_name,
                description=description.strip() if description and description.strip() else None,
                id_category=id_category,
                is_active=is_active
            )
            uow.dishes.add(nou_plat)
            return dish_to_entity(nou_plat)

    def update(
        self,
        dish_id: int,
        dish_name: Optional[str] = None,
        description: Optional[str] = None,
        is_active: Optional[bool] = None,
        id_category: Optional[int] = None
    ) -> Optional[DishEntity]:
        """Actualitza les propietats d'un plat."""
        with self.uow_factory.create() as uow:
            dish = uow.dishes.get(dish_id)
            if not dish:
                return None

            if dish_name is not None and dish_name.strip():
                dish.dish_name = dish_name.strip()
            if description is not None:
                dish.description = description.strip() if description.strip() else None
            if is_active is not None:
                dish.is_active = is_active
            if id_category is not None:
                cat = uow.categories.get(id_category)
                if not cat:
                    raise ValueError(f"No existeix cap categoria amb ID {id_category}.")
                dish.id_category = id_category

            uow.dishes.update(dish)
            return dish_to_entity(dish)

    def delete(self, dish_id: int) -> bool:
        """Elimina un plat per ID."""
        with self.uow_factory.create() as uow:
            dish = uow.dishes.get(dish_id)
            if not dish:
                return False
            uow.dishes.delete(dish_id)
            return True

    def add_allergen(self, dish_id: int, allergen_id: int) -> bool:
        """Associa un al·lèrgen a un plat (relació N:M). Retorna True si s'ha afegit."""
        with self.uow_factory.create() as uow:
            dish = uow.dishes.get(dish_id)
            if not dish:
                raise ValueError(f"No s'ha trobat el plat amb ID {dish_id}.")

            allergen = uow.allergens.get(allergen_id)
            if not allergen:
                raise ValueError(f"No s'ha trobat l'al·lèrgen amb ID {allergen_id}.")

            return uow.dishes.add_allergen_to_dish(dish_id, allergen)
