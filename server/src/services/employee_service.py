# employee_service.py: Lògica de negoci per a la Gestió d'Empleats.
# Inclou la gestió de la relació 1:1 amb AppCredential i el hashing de contrasenyes amb SHA-256.

import hashlib
from typing import List, Optional
from common.domain.entities import EmployeeEntity
from server.src.persistence.unit_of_work import UnitOfWorkFactory
from server.src.persistence.models import Employee, AppCredential
from server.src.persistence.mappers import employee_to_entity


class EmployeeService:
    def __init__(self, uow_factory: UnitOfWorkFactory):
        self.uow_factory = uow_factory

    def get_all(self) -> List[EmployeeEntity]:
        """Recupera tots els empleats de la plantilla."""
        with self.uow_factory.create() as uow:
            employees = uow.employees.get_all()
            return [employee_to_entity(e) for e in employees]

    def get_by_id(self, employee_id: int) -> Optional[EmployeeEntity]:
        """Recupera un empleat concret pel seu identificador."""
        with self.uow_factory.create() as uow:
            emp = uow.employees.get(employee_id)
            if not emp:
                return None
            return employee_to_entity(emp)

    def search(self, name: str = "", surname: str = "") -> List[EmployeeEntity]:
        """Cerca empleats per nom i/o cognom."""
        with self.uow_factory.create() as uow:
            employees = uow.employees.get_by_name(name=name.strip(), surname=surname.strip())
            return [employee_to_entity(e) for e in employees]

    def get_by_role(self, role: str) -> List[EmployeeEntity]:
        """Filtra empleats segons el seu rol professional."""
        with self.uow_factory.create() as uow:
            employees = uow.employees.get_by_role(role=role.strip())
            return [employee_to_entity(e) for e in employees]

    def create(
        self,
        name: str,
        surname: str,
        national_id: str,
        role: str,
        email: Optional[str] = None,
        password: Optional[str] = None
    ) -> EmployeeEntity:
        """
        Crea un nou empleat. Si es passen email i password, crea també les credencials
        en la mateixa transacció (relació 1:1).
        """
        name = (name or "").strip()
        surname = (surname or "").strip()
        national_id = (national_id or "").strip()
        role = (role or "").strip()

        if not all([name, surname, national_id, role]):
            raise ValueError("Tots els camps de l'empleat són obligatoris.")

        with self.uow_factory.create() as uow:
            if uow.employees.national_id_exists(national_id):
                raise ValueError(f"Ja existeix un empleat amb el DNI '{national_id}'.")

            nou_empleat = Employee(
                name=name,
                surname=surname,
                national_id=national_id,
                role=role
            )

            # Si s'han facilitat credencials d'accés (relació 1:1)
            if email and email.strip() and password and password.strip():
                # Protecció: mai emmagatzemar contrasenyes en text pla!
                pwd_hash = hashlib.sha256(password.strip().encode()).hexdigest()
                nou_empleat.credentials = AppCredential(
                    email=email.strip(),
                    password_hash=pwd_hash
                )

            uow.employees.add(nou_empleat)
            return employee_to_entity(nou_empleat)

    def update(
        self,
        employee_id: int,
        name: Optional[str] = None,
        surname: Optional[str] = None,
        national_id: Optional[str] = None,
        role: Optional[str] = None
    ) -> Optional[EmployeeEntity]:
        """Actualitza les dades d'un empleat."""
        with self.uow_factory.create() as uow:
            emp = uow.employees.get(employee_id)
            if not emp:
                return None

            if name is not None and name.strip():
                emp.name = name.strip()
            if surname is not None and surname.strip():
                emp.surname = surname.strip()
            if national_id is not None and national_id.strip():
                if national_id.strip() != emp.national_id and uow.employees.national_id_exists(national_id.strip()):
                    raise ValueError(f"Ja existeix un altre empleat amb el DNI '{national_id}'.")
                emp.national_id = national_id.strip()
            if role is not None and role.strip():
                emp.role = role.strip()

            uow.employees.update(emp)
            return employee_to_entity(emp)

    def delete(self, employee_id: int) -> bool:
        """Elimina un empleat (les seves credencials s'esborren en cascada)."""
        with self.uow_factory.create() as uow:
            emp = uow.employees.get(employee_id)
            if not emp:
                return False
            uow.employees.delete(employee_id)
            return True
