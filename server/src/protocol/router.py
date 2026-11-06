# router.py: Encamina les peticions HTTP cap al servei corresponent.
#
# CONCEPTE CLAU PER A DAM (Patró Router / Controlador):
# El Router inspecciona el mètode (GET, POST, PUT, DELETE) i la ruta (/categories, /dishes/1...)
# per determinar quina funció del Service ha d'executar.
# A més:
# - Extreu els paràmetres de la URL (com els IDs numèrics).
# - Valida tipus de dades i captura excepcions com ValueError -> 400 Bad Request.
# - Si la ruta no coincideix amb cap servei -> 404 Not Found.
# - Retorna la resposta formatejada en bytes gràcies a ResponseBuilder.

from datetime import date

from server.src.services import (
    AllergenService,
    CategoryService,
    DishService,
    EmployeeService,
    MenuService,
    SaleService,
)

from .request_parser import HttpRequest
from .response_builder import ResponseBuilder


class Router:
    """
    Enrutador principal del servidor TCP.
    Rep objectes HttpRequest i delega a la capa de serveis.
    """

    def __init__(
        self,
        category_service: CategoryService,
        allergen_service: AllergenService,
        dish_service: DishService,
        employee_service: EmployeeService,
        menu_service: MenuService,
        sale_service: SaleService,
    ):
        self.categories = category_service
        self.allergens = allergen_service
        self.dishes = dish_service
        self.employees = employee_service
        self.menus = menu_service
        self.sales = sale_service

    def handle_request(self, request: HttpRequest) -> bytes:
        """
        Punt d'entrada que processa una petició i retorna els bytes de la resposta HTTP.
        """
        if not request:
            return ResponseBuilder.bad_request("Petició invàlida o incompleta.")

        method = request.method
        path = request.raw_path.rstrip("/")
        if not path:
            path = "/"

        # Dividim la ruta en segments (ex: '/categories/5' -> ['categories', '5'])
        parts = [part for part in path.split("/") if part]

        try:
            # 1. RUTA ARREL / SALUTACIÓ
            if not parts:
                return ResponseBuilder.ok(
                    {"status": "running", "message": "Restaurant BackOffice API v3.0"}
                )

            resource = parts[0]

            # 2. CATEGORIES (/categories, /categories/{id})
            if resource == "categories":
                return self._handle_categories(method, parts, request)

            # 3. AL·LÈRGENS (/allergens, /allergens/{id})
            elif resource == "allergens":
                return self._handle_allergens(method, parts, request)

            # 4. PLATS (/dishes, /dishes/{id}, /dishes/{id}/allergens)
            elif resource == "dishes":
                return self._handle_dishes(method, parts, request)

            # 5. EMPLEATS (/employees, /employees/{id})
            elif resource == "employees":
                return self._handle_employees(method, parts, request)

            # 6. MENÚS (/menus, /menus/{id}, /menus/{id}/dishes, /menus/{id}/dishes/{dish_id})
            elif resource == "menus":
                return self._handle_menus(method, parts, request)

            # 7. VENDES (/sales, /sales/{menu_id}/{emp_id}/{date})
            elif resource == "sales":
                return self._handle_sales(method, parts, request)

            # Recurs no reconegut
            return ResponseBuilder.not_found(f"Recurs '{resource}' no trobat al servidor.")

        except ValueError as error:
            # Errors de validació de negoci controlats
            return ResponseBuilder.bad_request(str(error))
        except Exception as error:
            # Errors inesperats del servidor
            return ResponseBuilder.internal_error(f"Error inesperat: {error!s}")

    # -------------------------------------------------------------------------
    # AJUDANTS (eviten repetir el mateix "if ... else not_found" a cada recurs)
    # -------------------------------------------------------------------------

    @staticmethod
    def _ok_or_not_found(entity: object, not_found_message: str) -> bytes:
        """200 amb l'entitat si existeix; si no, 404."""
        if entity:
            return ResponseBuilder.ok(entity)
        return ResponseBuilder.not_found(not_found_message)

    @staticmethod
    def _no_content_or_not_found(done: bool, not_found_message: str) -> bytes:
        """204 si l'esborrat s'ha fet; si no, 404."""
        if done:
            return ResponseBuilder.no_content()
        return ResponseBuilder.not_found(not_found_message)

    # -------------------------------------------------------------------------
    # HANDLERS ESPECÍFICS PER A CADA RECURS
    # -------------------------------------------------------------------------

    def _handle_categories(self, method: str, parts: list, request: HttpRequest) -> bytes:
        # GET /categories -> llistar totes
        if len(parts) == 1 and method == "GET":
            categories = self.categories.get_all()
            return ResponseBuilder.ok(categories)

        # POST /categories -> crear nova
        if len(parts) == 1 and method == "POST":
            body = request.body or {}
            name = body.get("category_name", "")
            category = self.categories.create(name)
            return ResponseBuilder.created(category)

        # /categories/{id}
        if len(parts) == 2 and parts[1].isdigit():
            category_id = int(parts[1])
            if method == "GET":
                category = self.categories.get_by_id(category_id)
                return self._ok_or_not_found(category, "Categoria no trobada.")
            elif method == "PUT":
                body = request.body or {}
                name = body.get("category_name", "")
                category = self.categories.update(category_id, name)
                return self._ok_or_not_found(category, "Categoria no trobada.")
            elif method == "DELETE":
                done = self.categories.delete(category_id)
                return self._no_content_or_not_found(done, "Categoria no trobada.")

        return ResponseBuilder.not_found("Ruta o mètode no suportat per a categories.")

    def _handle_allergens(self, method: str, parts: list, request: HttpRequest) -> bytes:
        # GET /allergens
        if len(parts) == 1 and method == "GET":
            allergens = self.allergens.get_all()
            return ResponseBuilder.ok(allergens)

        # POST /allergens
        if len(parts) == 1 and method == "POST":
            body = request.body or {}
            name = body.get("allergen_name", "")
            allergen = self.allergens.create(name)
            return ResponseBuilder.created(allergen)

        # /allergens/{id}
        if len(parts) == 2 and parts[1].isdigit():
            allergen_id = int(parts[1])
            if method == "GET":
                allergen = self.allergens.get_by_id(allergen_id)
                return self._ok_or_not_found(allergen, "Al·lèrgen no trobat.")
            elif method == "PUT":
                body = request.body or {}
                name = body.get("allergen_name", "")
                allergen = self.allergens.update(allergen_id, name)
                return self._ok_or_not_found(allergen, "Al·lèrgen no trobat.")
            elif method == "DELETE":
                done = self.allergens.delete(allergen_id)
                return self._no_content_or_not_found(done, "Al·lèrgen no trobat.")

        return ResponseBuilder.not_found("Ruta o mètode no suportat per a al·lèrgens.")

    def _handle_dishes(self, method: str, parts: list, request: HttpRequest) -> bytes:
        # GET /dishes (admet filtres: ?active=true, ?name=sopa)
        if len(parts) == 1 and method == "GET":
            if request.query_params.get("active") == "true":
                dishes = self.dishes.get_active()
            elif "name" in request.query_params:
                dishes = self.dishes.search_by_name(request.query_params["name"])
            else:
                dishes = self.dishes.get_all()
            return ResponseBuilder.ok(dishes)

        # POST /dishes -> Crear plat
        if len(parts) == 1 and method == "POST":
            body = request.body or {}
            dish = self.dishes.create(
                dish_name=body.get("dish_name", ""),
                id_category=int(body.get("id_category", 0)),
                description=body.get("description"),
                is_active=bool(body.get("is_active", True)),
            )
            return ResponseBuilder.created(dish)

        # /dishes/{id}
        if len(parts) == 2 and parts[1].isdigit():
            dish_id = int(parts[1])
            if method == "GET":
                dish = self.dishes.get_by_id(dish_id)
                return self._ok_or_not_found(dish, "Plat no trobat.")
            elif method == "PUT":
                body = request.body or {}
                dish = self.dishes.update(
                    dish_id=dish_id,
                    dish_name=body.get("dish_name"),
                    description=body.get("description"),
                    is_active=body.get("is_active"),
                    id_category=body.get("id_category"),
                )
                return self._ok_or_not_found(dish, "Plat no trobat.")
            elif method == "DELETE":
                done = self.dishes.delete(dish_id)
                return self._no_content_or_not_found(done, "Plat no trobat.")

        # POST /dishes/{id}/allergens -> Afegir al·lèrgen a plat (relació N:M)
        if len(parts) == 3 and parts[1].isdigit() and parts[2] == "allergens" and method == "POST":
            dish_id = int(parts[1])
            body = request.body or {}
            allergen_id = int(body.get("id_allergen", 0))
            done = self.dishes.add_allergen(dish_id, allergen_id)
            return ResponseBuilder.ok({"added": done})

        return ResponseBuilder.not_found("Ruta o mètode no suportat per a plats.")

    def _handle_employees(self, method: str, parts: list, request: HttpRequest) -> bytes:
        # GET /employees (admet cerques: ?name=x&surname=y o ?role=z)
        if len(parts) == 1 and method == "GET":
            if "role" in request.query_params:
                employees = self.employees.get_by_role(request.query_params["role"])
            elif "name" in request.query_params or "surname" in request.query_params:
                employees = self.employees.search(
                    name=request.query_params.get("name", ""),
                    surname=request.query_params.get("surname", ""),
                )
            else:
                employees = self.employees.get_all()
            return ResponseBuilder.ok(employees)

        # POST /employees -> Crear empleat
        if len(parts) == 1 and method == "POST":
            body = request.body or {}
            employee = self.employees.create(
                name=body.get("name", ""),
                surname=body.get("surname", ""),
                national_id=body.get("national_id", ""),
                role=body.get("role", ""),
                email=body.get("email"),
                password=body.get("password"),
            )
            return ResponseBuilder.created(employee)

        # /employees/{id}
        if len(parts) == 2 and parts[1].isdigit():
            employee_id = int(parts[1])
            if method == "GET":
                employee = self.employees.get_by_id(employee_id)
                return self._ok_or_not_found(employee, "Empleat no trobat.")
            elif method == "PUT":
                body = request.body or {}
                employee = self.employees.update(
                    employee_id=employee_id,
                    name=body.get("name"),
                    surname=body.get("surname"),
                    national_id=body.get("national_id"),
                    role=body.get("role"),
                )
                return self._ok_or_not_found(employee, "Empleat no trobat.")
            elif method == "DELETE":
                done = self.employees.delete(employee_id)
                return self._no_content_or_not_found(done, "Empleat no trobat.")

        return ResponseBuilder.not_found("Ruta o mètode no suportat per a empleats.")

    def _handle_menus(self, method: str, parts: list, request: HttpRequest) -> bytes:
        # GET /menus (admet filtres: ?name=x o ?min_price=x&max_price=y)
        if len(parts) == 1 and method == "GET":
            if "name" in request.query_params:
                menus = self.menus.search_by_name(request.query_params["name"])
            elif "min_price" in request.query_params and "max_price" in request.query_params:
                min_price = float(request.query_params["min_price"])
                max_price = float(request.query_params["max_price"])
                menus = self.menus.filter_by_price_range(min_price, max_price)
            else:
                menus = self.menus.get_all()
            return ResponseBuilder.ok(menus)

        # POST /menus -> Crear menú
        if len(parts) == 1 and method == "POST":
            body = request.body or {}
            menu = self.menus.create(
                menu_name=body.get("menu_name", ""), price=float(body.get("price", 0.0))
            )
            return ResponseBuilder.created(menu)

        # /menus/{id}
        if len(parts) == 2 and parts[1].isdigit():
            menu_id = int(parts[1])
            if method == "GET":
                menu = self.menus.get_by_id(menu_id)
                return self._ok_or_not_found(menu, "Menú no trobat.")
            elif method == "PUT":
                body = request.body or {}
                menu = self.menus.update(
                    menu_id=menu_id,
                    menu_name=body.get("menu_name"),
                    price=float(body.get("price")) if body.get("price") is not None else None,
                )
                return self._ok_or_not_found(menu, "Menú no trobat.")
            elif method == "DELETE":
                done = self.menus.delete(menu_id)
                return self._no_content_or_not_found(done, "Menú no trobat.")

        # POST /menus/{id}/dishes -> Afegir plat a menú (N:M)
        if len(parts) == 3 and parts[1].isdigit() and parts[2] == "dishes" and method == "POST":
            menu_id = int(parts[1])
            body = request.body or {}
            dish_id = int(body.get("id_dish", 0))
            done = self.menus.add_dish(menu_id, dish_id)
            return ResponseBuilder.ok({"added": done})

        # DELETE /menus/{id}/dishes/{dish_id} -> Treure plat de menú (N:M)
        if (
            len(parts) == 4
            and parts[1].isdigit()
            and parts[2] == "dishes"
            and parts[3].isdigit()
            and method == "DELETE"
        ):
            menu_id = int(parts[1])
            dish_id = int(parts[3])
            done = self.menus.remove_dish(menu_id, dish_id)
            return self._no_content_or_not_found(done, "Relació Menú-Plat no trobada.")

        return ResponseBuilder.not_found("Ruta o mètode no suportat per a menús.")

    def _handle_sales(self, method: str, parts: list, request: HttpRequest) -> bytes:
        # GET /sales (admet cerques: ?date=YYYY-MM-DD, ?employee_id=X, ?menu_id=Y,
        # ?date_from=A&date_to=B, ?page=1)
        if len(parts) == 1 and method == "GET":
            params = request.query_params
            if "date" in params:
                sale_date = date.fromisoformat(params["date"])
                sales = self.sales.get_by_date(sale_date)
            elif "employee_id" in params:
                sales = self.sales.get_by_employee(int(params["employee_id"]))
            elif "menu_id" in params:
                sales = self.sales.get_by_menu(int(params["menu_id"]))
            elif "date_from" in params and "date_to" in params:
                date_from = date.fromisoformat(params["date_from"])
                date_to = date.fromisoformat(params["date_to"])
                sales = self.sales.get_by_date_range(date_from, date_to)
            else:
                page = int(params.get("page", 1))
                page_size = int(params.get("page_size", 20))
                sales = self.sales.get_paginated(page, page_size)
            return ResponseBuilder.ok(sales)

        # POST /sales -> Enregistrar venda
        if len(parts) == 1 and method == "POST":
            body = request.body or {}
            sale_date = date.fromisoformat(body.get("sale_date", str(date.today())))
            sale = self.sales.create(
                id_menu=int(body.get("id_menu", 0)),
                id_employee=int(body.get("id_employee", 0)),
                sale_date_val=sale_date,
                quantity_sold=int(body.get("quantity_sold", 1)),
            )
            return ResponseBuilder.created(sale)

        # /sales/{id_menu}/{id_employee}/{sale_date} -> PK composta
        if len(parts) == 4 and parts[1].isdigit() and parts[2].isdigit():
            menu_id = int(parts[1])
            employee_id = int(parts[2])
            sale_date = date.fromisoformat(parts[3])

            if method == "GET":
                sale = self.sales.get_by_pk(menu_id, employee_id, sale_date)
                return self._ok_or_not_found(sale, "Venda no trobada.")
            elif method == "PUT":
                body = request.body or {}
                quantity_sold = int(body.get("quantity_sold", 1))
                sale = self.sales.update(menu_id, employee_id, sale_date, quantity_sold)
                return self._ok_or_not_found(sale, "Venda no trobada.")
            elif method == "DELETE":
                done = self.sales.delete(menu_id, employee_id, sale_date)
                return self._no_content_or_not_found(done, "Venda no trobada.")

        return ResponseBuilder.not_found("Ruta o mètode no suportat per a vendes.")
