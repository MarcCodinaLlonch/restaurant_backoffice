# allergen_service.py: Lògica de negoci per als Al·lèrgens.

from typing import List, Optional

from common.domain.entities import AllergenEntity
from server.src.persistence.mappers import allergen_to_entity
from server.src.persistence.models import Allergen
from server.src.persistence.unit_of_work import UnitOfWorkFactory


class AllergenService:
    def __init__(self, uow_factory: UnitOfWorkFactory) -> None:
        self.uow_factory = uow_factory

    def get_all(self) -> List[AllergenEntity]:
        """Recupera tots els al·lèrgens."""
        with self.uow_factory.create() as uow:
            allergens = uow.allergens.get_all()
            return [allergen_to_entity(allergen) for allergen in allergens]

    def get_by_id(self, allergen_id: int) -> Optional[AllergenEntity]:
        """Recupera un al·lèrgen per ID."""
        with self.uow_factory.create() as uow:
            allergen = uow.allergens.get(allergen_id)
            if not allergen:
                return None
            return allergen_to_entity(allergen)

    def create(self, allergen_name: str) -> AllergenEntity:
        """Crea un nou al·lèrgen."""
        clean_name = (allergen_name or "").strip()
        if not clean_name:
            raise ValueError("El nom de l'al·lèrgen no pot estar buit.")

        with self.uow_factory.create() as uow:
            existing = uow.allergens.get_by_name(clean_name)
            if existing:
                raise ValueError(f"L'al·lèrgen '{clean_name}' ja existeix.")

            new_allergen = Allergen(allergen_name=clean_name)
            uow.allergens.add(new_allergen)
            return allergen_to_entity(new_allergen)

    def update(self, allergen_id: int, new_name: str) -> Optional[AllergenEntity]:
        """Actualitza el nom d'un al·lèrgen."""
        clean_name = (new_name or "").strip()
        if not clean_name:
            raise ValueError("El nom no pot estar buit.")

        with self.uow_factory.create() as uow:
            allergen = uow.allergens.get(allergen_id)
            if not allergen:
                return None

            existing = uow.allergens.get_by_name(clean_name)
            if existing and existing.id != allergen_id:
                raise ValueError(f"Ja existeix un altre al·lèrgen amb el nom '{clean_name}'.")

            allergen.allergen_name = clean_name
            uow.allergens.update(allergen)
            return allergen_to_entity(allergen)

    def delete(self, allergen_id: int) -> bool:
        """Elimina un al·lèrgen."""
        with self.uow_factory.create() as uow:
            allergen = uow.allergens.get(allergen_id)
            if not allergen:
                return False
            uow.allergens.delete(allergen_id)
            return True
