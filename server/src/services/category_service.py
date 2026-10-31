# category_service.py: Gestiona la lògica de negoci per a les Categories.
#
# CONCEPTE CLAU PER A DAM (Service Layer / Capa de Serveis):
# El servei és l'intermediari entre el Router (que rep la petició HTTP)
# i el Repositori (que toca la BD).
# La seva responsabilitat és:
# 1. Validar les regles de negoci (ex: el nom no pot estar buit).
# 2. Gestionar la transacció obrint el Unit of Work (with self.uow_factory.create() as uow).
# 3. Retornar entitats netes de domini (CategoryEntity), MAI models de SQLAlchemy directament.

from typing import List, Optional

from common.domain.entities import CategoryEntity
from server.src.persistence.mappers import category_to_entity
from server.src.persistence.models import Category
from server.src.persistence.unit_of_work import UnitOfWorkFactory


class CategoryService:
    def __init__(self, uow_factory: UnitOfWorkFactory) -> None:
        self.uow_factory = uow_factory

    def get_all(self) -> List[CategoryEntity]:
        """Recupera totes les categories ordenades."""
        with self.uow_factory.create() as uow:
            categories = uow.categories.get_all()
            return [category_to_entity(category) for category in categories]

    def get_by_id(self, category_id: int) -> Optional[CategoryEntity]:
        """Recupera una categoria per la seva ID."""
        with self.uow_factory.create() as uow:
            category = uow.categories.get(category_id)
            if not category:
                return None
            return category_to_entity(category)

    def create(self, category_name: str) -> CategoryEntity:
        """Crea una nova categoria verificant que el nom sigui vàlid."""
        clean_name = (category_name or "").strip()
        if not clean_name:
            raise ValueError("El nom de la categoria no pot estar buit.")

        with self.uow_factory.create() as uow:
            new_category = Category(category_name=clean_name)
            uow.categories.add(new_category)
            # En sortir del with, el UoW fa commit()
            # Retornem l'entitat amb les dades actualitzades
            return category_to_entity(new_category)

    def update(self, category_id: int, new_name: str) -> Optional[CategoryEntity]:
        """Modifica el nom d'una categoria existent."""
        clean_name = (new_name or "").strip()
        if not clean_name:
            raise ValueError("El nou nom de la categoria no pot estar buit.")

        with self.uow_factory.create() as uow:
            category = uow.categories.get(category_id)
            if not category:
                return None
            category.category_name = clean_name
            uow.categories.update(category)
            return category_to_entity(category)

    def delete(self, category_id: int) -> bool:
        """Elimina una categoria per ID. Retorna True si s'ha eliminat, False si no existia."""
        with self.uow_factory.create() as uow:
            category = uow.categories.get(category_id)
            if not category:
                return False
            uow.categories.delete(category_id)
            return True
