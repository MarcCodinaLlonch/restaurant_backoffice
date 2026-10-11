# allergen_service.py: Lògica de negoci per als Al·lèrgens.

from typing import List, Optional
from common.domain.entities import AllergenEntity
from server.src.persistence.unit_of_work import UnitOfWorkFactory
from server.src.persistence.models import Allergen
from server.src.persistence.mappers import allergen_to_entity


class AllergenService:
    def __init__(self, uow_factory: UnitOfWorkFactory):
        self.uow_factory = uow_factory

    def get_all(self) -> List[AllergenEntity]:
        """Recupera tots els al·lèrgens."""
        with self.uow_factory.create() as uow:
            allergens = uow.allergens.get_all()
            return [allergen_to_entity(a) for a in allergens]

    def get_by_id(self, allergen_id: int) -> Optional[AllergenEntity]:
        """Recupera un al·lèrgen per ID."""
        with self.uow_factory.create() as uow:
            al = uow.allergens.get(allergen_id)
            if not al:
                return None
            return allergen_to_entity(al)

    def create(self, allergen_name: str) -> AllergenEntity:
        """Crea un nou al·lèrgen."""
        clean_name = (allergen_name or "").strip()
        if not clean_name:
            raise ValueError("El nom de l'al·lèrgen no pot estar buit.")

        with self.uow_factory.create() as uow:
            existing = uow.allergens.get_by_name(clean_name)
            if existing:
                raise ValueError(f"L'al·lèrgen '{clean_name}' ja existeix.")

            nou = Allergen(allergen_name=clean_name)
            uow.allergens.add(nou)
            return allergen_to_entity(nou)

    def update(self, allergen_id: int, new_name: str) -> Optional[AllergenEntity]:
        """Actualitza el nom d'un al·lèrgen."""
        clean_name = (new_name or "").strip()
        if not clean_name:
            raise ValueError("El nom no pot estar buit.")

        with self.uow_factory.create() as uow:
            al = uow.allergens.get(allergen_id)
            if not al:
                return None

            existing = uow.allergens.get_by_name(clean_name)
            if existing and existing.id != allergen_id:
                raise ValueError(f"Ja existeix un altre al·lèrgen amb el nom '{clean_name}'.")

            al.allergen_name = clean_name
            uow.allergens.update(al)
            return allergen_to_entity(al)

    def delete(self, allergen_id: int) -> bool:
        """Elimina un al·lèrgen."""
        with self.uow_factory.create() as uow:
            al = uow.allergens.get(allergen_id)
            if not al:
                return False
            uow.allergens.delete(allergen_id)
            return True
