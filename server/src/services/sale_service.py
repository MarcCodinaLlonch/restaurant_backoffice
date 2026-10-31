# sale_service.py: Lògica de negoci per a la Gestió de Vendes.
# Relació N:M amb atributs (Menu i Employee associats amb sale_date i quantity_sold).

from datetime import date
from typing import List, Optional

from common.domain.entities import SaleEntity
from server.src.persistence.mappers import sale_to_entity
from server.src.persistence.models import Sale
from server.src.persistence.unit_of_work import UnitOfWorkFactory


class SaleService:
    def __init__(self, uow_factory: UnitOfWorkFactory) -> None:
        self.uow_factory = uow_factory

    def get_all(self) -> List[SaleEntity]:
        """Recupera totes les vendes enregistrades."""
        with self.uow_factory.create() as uow:
            sales = uow.sales.get_all()
            return [sale_to_entity(sale) for sale in sales]

    def get_paginated(self, page: int = 1, page_size: int = 20) -> List[SaleEntity]:
        """Recupera vendes paginades."""
        with self.uow_factory.create() as uow:
            sales = uow.sales.get_paginated(page, page_size)
            return [sale_to_entity(sale) for sale in sales]

    def get_by_pk(
        self, id_menu: int, id_employee: int, sale_date_val: date
    ) -> Optional[SaleEntity]:
        """Recupera una venda per la seva clau primària composta (tupla)."""
        with self.uow_factory.create() as uow:
            sale = uow.sales.get((id_menu, id_employee, sale_date_val))
            if not sale:
                return None
            return sale_to_entity(sale)

    def create(
        self, id_menu: int, id_employee: int, sale_date_val: date, quantity_sold: int = 1
    ) -> SaleEntity:
        """Enregistra una nova venda."""
        if quantity_sold <= 0:
            raise ValueError("La quantitat venuda ha de ser superior a 0.")

        with self.uow_factory.create() as uow:
            # Validem que el menú i l'empleat existeixin
            menu = uow.menus.get(id_menu)
            if not menu:
                raise ValueError(f"No existeix el menú amb ID {id_menu}.")
            employee = uow.employees.get(id_employee)
            if not employee:
                raise ValueError(f"No existeix l'empleat amb ID {id_employee}.")

            # Comprovem si ja existeix la venda en aquesta mateixa data (PK composta única)
            existing = uow.sales.get((id_menu, id_employee, sale_date_val))
            if existing:
                raise ValueError(
                    f"Ja existeix una venda per a aquest menú, empleat i data ({sale_date_val})."
                )

            new_sale = Sale(
                id_menu=id_menu,
                id_employee=id_employee,
                sale_date=sale_date_val,
                quantity_sold=quantity_sold,
            )
            uow.sales.add(new_sale)
            return sale_to_entity(new_sale)

    def update(
        self, id_menu: int, id_employee: int, sale_date_val: date, quantity_sold: int
    ) -> Optional[SaleEntity]:
        """Actualitza la quantitat d'una venda existent."""
        if quantity_sold <= 0:
            raise ValueError("La quantitat venuda ha de ser superior a 0.")

        with self.uow_factory.create() as uow:
            pk = (id_menu, id_employee, sale_date_val)
            sale = uow.sales.get(pk)
            if not sale:
                return None

            sale.quantity_sold = quantity_sold
            uow.sales.update(sale)
            return sale_to_entity(sale)

    def delete(self, id_menu: int, id_employee: int, sale_date_val: date) -> bool:
        """Elimina una venda mitjançant la seva clau primària composta."""
        with self.uow_factory.create() as uow:
            pk = (id_menu, id_employee, sale_date_val)
            sale = uow.sales.get(pk)
            if not sale:
                return False
            uow.sales.delete(pk)
            return True

    def get_by_date(self, target_date: date) -> List[SaleEntity]:
        """Cerca vendes per data específica."""
        with self.uow_factory.create() as uow:
            sales = uow.sales.get_sales_by_date(target_date)
            return [sale_to_entity(sale) for sale in sales]

    def get_by_employee(self, employee_id: int) -> List[SaleEntity]:
        """Cerca vendes fetes per un empleat."""
        with self.uow_factory.create() as uow:
            sales = uow.sales.get_sales_by_employee(employee_id)
            return [sale_to_entity(sale) for sale in sales]

    def get_by_menu(self, menu_id: int) -> List[SaleEntity]:
        """Cerca vendes d'un menú específic."""
        with self.uow_factory.create() as uow:
            sales = uow.sales.get_sales_by_menu(menu_id)
            return [sale_to_entity(sale) for sale in sales]

    def get_by_date_range(self, date_from: date, date_to: date) -> List[SaleEntity]:
        """Cerca vendes en un rang de dates."""
        if date_from > date_to:
            raise ValueError("La data d'inici no pot ser posterior a la data de fi.")
        with self.uow_factory.create() as uow:
            sales = uow.sales.get_sales_by_date_range(date_from, date_to)
            return [sale_to_entity(sale) for sale in sales]
