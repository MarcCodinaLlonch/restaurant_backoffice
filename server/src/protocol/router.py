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

import re
from datetime import date
from typing import Optional
from .request_parser import HttpRequest
from .response_builder import ResponseBuilder
from server.src.services import (
    CategoryService,
    AllergenService,
    DishService,
    EmployeeService,
    MenuService,
    SaleService,
)


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

    def handle_request(self, req: HttpRequest) -> bytes:
        """
        Punt d'entrada que processa una petició i retorna els bytes de la resposta HTTP.
        """
        if not req:
            return ResponseBuilder.bad_request("Petició invàlida o incompleta.")

        method = req.method
        path = req.raw_path.rstrip("/")
        if not path:
            path = "/"

        # Dividim la ruta en segments (ex: '/categories/5' -> ['categories', '5'])
        parts = [p for p in path.split("/") if p]

        try:
            # 1. RUTA ARREL / SALUTACIÓ
            if not parts:
                return ResponseBuilder.ok({"status": "running", "message": "Restaurant BackOffice API v2.0"})

            resource = parts[0]

            # 2. CATEGORIES (/categories, /categories/{id})
            if resource == "categories":
                return self._handle_categories(method, parts, req)

            # 3. AL·LÈRGENS (/allergens, /allergens/{id})
            elif resource == "allergens":
                return self._handle_allergens(method, parts, req)

            # 4. PLATS (/dishes, /dishes/{id}, /dishes/{id}/allergens)
            elif resource == "dishes":
                return self._handle_dishes(method, parts, req)

            # 5. EMPLEATS (/employees, /employees/{id})
            elif resource == "employees":
                return self._handle_employees(method, parts, req)

            # 6. MENÚS (/menus, /menus/{id}, /menus/{id}/dishes, /menus/{id}/dishes/{dish_id})
            elif resource == "menus":
                return self._handle_menus(method, parts, req)

            # 7. VENDES (/sales, /sales/{menu_id}/{emp_id}/{date})
            elif resource == "sales":
                return self._handle_sales(method, parts, req)

            # Recurs no reconegut
            return ResponseBuilder.not_found(f"Recurs '{resource}' no trobat al servidor.")

        except ValueError as ve:
            # Errors de validació de negoci controlats
            return ResponseBuilder.bad_request(str(ve))
        except Exception as ex:
            # Errors inesperats del servidor
            return ResponseBuilder.internal_error(f"Error inesperat: {str(ex)}")

    # -------------------------------------------------------------------------
    # HANDLERS ESPECÍFICS PER A CADA RECURS
    # -------------------------------------------------------------------------

    def _handle_categories(self, method: str, parts: list, req: HttpRequest) -> bytes:
        # GET /categories -> llistar totes
        if len(parts) == 1 and method == "GET":
            cats = self.categories.get_all()
            return ResponseBuilder.ok(cats)

        # POST /categories -> crear nova
        if len(parts) == 1 and method == "POST":
            body = req.body or {}
            nom = body.get("category_name", "")
            cat = self.categories.create(nom)
            return ResponseBuilder.created(cat)

        # /categories/{id}
        if len(parts) == 2 and parts[1].isdigit():
            cat_id = int(parts[1])
            if method == "GET":
                cat = self.categories.get_by_id(cat_id)
                return ResponseBuilder.ok(cat) if cat else ResponseBuilder.not_found("Categoria no trobada.")
            elif method == "PUT":
                body = req.body or {}
                nom = body.get("category_name", "")
                cat = self.categories.update(cat_id, nom)
                return ResponseBuilder.ok(cat) if cat else ResponseBuilder.not_found("Categoria no trobada.")
            elif method == "DELETE":
                ok = self.categories.delete(cat_id)
                return ResponseBuilder.no_content() if ok else ResponseBuilder.not_found("Categoria no trobada.")

        return ResponseBuilder.not_found("Ruta o mètode no suportat per a categories.")

    def _handle_allergens(self, method: str, parts: list, req: HttpRequest) -> bytes:
        # GET /allergens
        if len(parts) == 1 and method == "GET":
            als = self.allergens.get_all()
            return ResponseBuilder.ok(als)

        # POST /allergens
        if len(parts) == 1 and method == "POST":
            body = req.body or {}
            nom = body.get("allergen_name", "")
            al = self.allergens.create(nom)
            return ResponseBuilder.created(al)

        # /allergens/{id}
        if len(parts) == 2 and parts[1].isdigit():
            al_id = int(parts[1])
            if method == "GET":
                al = self.allergens.get_by_id(al_id)
                return ResponseBuilder.ok(al) if al else ResponseBuilder.not_found("Al·lèrgen no trobat.")
            elif method == "PUT":
                body = req.body or {}
                nom = body.get("allergen_name", "")
                al = self.allergens.update(al_id, nom)
                return ResponseBuilder.ok(al) if al else ResponseBuilder.not_found("Al·lèrgen no trobat.")
            elif method == "DELETE":
                ok = self.allergens.delete(al_id)
                return ResponseBuilder.no_content() if ok else ResponseBuilder.not_found("Al·lèrgen no trobat.")

        return ResponseBuilder.not_found("Ruta o mètode no suportat per a al·lèrgens.")

    def _handle_dishes(self, method: str, parts: list, req: HttpRequest) -> bytes:
        # GET /dishes (admet filtres: ?active=true, ?name=sopa)
        if len(parts) == 1 and method == "GET":
            if req.query_params.get("active") == "true":
                dishes = self.dishes.get_active()
            elif "name" in req.query_params:
                dishes = self.dishes.search_by_name(req.query_params["name"])
            else:
                dishes = self.dishes.get_all()
            return ResponseBuilder.ok(dishes)

        # POST /dishes -> Crear plat
        if len(parts) == 1 and method == "POST":
            b = req.body or {}
            dish = self.dishes.create(
                dish_name=b.get("dish_name", ""),
                id_category=int(b.get("id_category", 0)),
                description=b.get("description"),
                is_active=bool(b.get("is_active", True))
            )
            return ResponseBuilder.created(dish)

        # /dishes/{id}
        if len(parts) == 2 and parts[1].isdigit():
            d_id = int(parts[1])
            if method == "GET":
                dish = self.dishes.get_by_id(d_id)
                return ResponseBuilder.ok(dish) if dish else ResponseBuilder.not_found("Plat no trobat.")
            elif method == "PUT":
                b = req.body or {}
                dish = self.dishes.update(
                    dish_id=d_id,
                    dish_name=b.get("dish_name"),
                    description=b.get("description"),
                    is_active=b.get("is_active"),
                    id_category=b.get("id_category")
                )
                return ResponseBuilder.ok(dish) if dish else ResponseBuilder.not_found("Plat no trobat.")
            elif method == "DELETE":
                ok = self.dishes.delete(d_id)
                return ResponseBuilder.no_content() if ok else ResponseBuilder.not_found("Plat no trobat.")

        # POST /dishes/{id}/allergens -> Afegir al·lèrgen a plat (relació N:M)
        if len(parts) == 3 and parts[1].isdigit() and parts[2] == "allergens" and method == "POST":
            d_id = int(parts[1])
            b = req.body or {}
            al_id = int(b.get("id_allergen", 0))
            ok = self.dishes.add_allergen(d_id, al_id)
            return ResponseBuilder.ok({"added": ok})

        return ResponseBuilder.not_found("Ruta o mètode no suportat per a plats.")

    def _handle_employees(self, method: str, parts: list, req: HttpRequest) -> bytes:
        # GET /employees (admet cerques: ?name=x&surname=y o ?role=z)
        if len(parts) == 1 and method == "GET":
            if "role" in req.query_params:
                emps = self.employees.get_by_role(req.query_params["role"])
            elif "name" in req.query_params or "surname" in req.query_params:
                emps = self.employees.search(
                    name=req.query_params.get("name", ""),
                    surname=req.query_params.get("surname", "")
                )
            else:
                emps = self.employees.get_all()
            return ResponseBuilder.ok(emps)

        # POST /employees -> Crear empleat
        if len(parts) == 1 and method == "POST":
            b = req.body or {}
            emp = self.employees.create(
                name=b.get("name", ""),
                surname=b.get("surname", ""),
                national_id=b.get("national_id", ""),
                role=b.get("role", ""),
                email=b.get("email"),
                password=b.get("password")
            )
            return ResponseBuilder.created(emp)

        # /employees/{id}
        if len(parts) == 2 and parts[1].isdigit():
            e_id = int(parts[1])
            if method == "GET":
                emp = self.employees.get_by_id(e_id)
                return ResponseBuilder.ok(emp) if emp else ResponseBuilder.not_found("Empleat no trobat.")
            elif method == "PUT":
                b = req.body or {}
                emp = self.employees.update(
                    employee_id=e_id,
                    name=b.get("name"),
                    surname=b.get("surname"),
                    national_id=b.get("national_id"),
                    role=b.get("role")
                )
                return ResponseBuilder.ok(emp) if emp else ResponseBuilder.not_found("Empleat no trobat.")
            elif method == "DELETE":
                ok = self.employees.delete(e_id)
                return ResponseBuilder.no_content() if ok else ResponseBuilder.not_found("Empleat no trobat.")

        return ResponseBuilder.not_found("Ruta o mètode no suportat per a empleats.")

    def _handle_menus(self, method: str, parts: list, req: HttpRequest) -> bytes:
        # GET /menus (admet filtres: ?name=x o ?min_price=x&max_price=y)
        if len(parts) == 1 and method == "GET":
            if "name" in req.query_params:
                menus = self.menus.search_by_name(req.query_params["name"])
            elif "min_price" in req.query_params and "max_price" in req.query_params:
                p_min = float(req.query_params["min_price"])
                p_max = float(req.query_params["max_price"])
                menus = self.menus.filter_by_price_range(p_min, p_max)
            else:
                menus = self.menus.get_all()
            return ResponseBuilder.ok(menus)

        # POST /menus -> Crear menú
        if len(parts) == 1 and method == "POST":
            b = req.body or {}
            m = self.menus.create(
                menu_name=b.get("menu_name", ""),
                price=float(b.get("price", 0.0))
            )
            return ResponseBuilder.created(m)

        # /menus/{id}
        if len(parts) == 2 and parts[1].isdigit():
            m_id = int(parts[1])
            if method == "GET":
                m = self.menus.get_by_id(m_id)
                return ResponseBuilder.ok(m) if m else ResponseBuilder.not_found("Menú no trobat.")
            elif method == "PUT":
                b = req.body or {}
                m = self.menus.update(
                    menu_id=m_id,
                    menu_name=b.get("menu_name"),
                    price=float(b.get("price")) if b.get("price") is not None else None
                )
                return ResponseBuilder.ok(m) if m else ResponseBuilder.not_found("Menú no trobat.")
            elif method == "DELETE":
                ok = self.menus.delete(m_id)
                return ResponseBuilder.no_content() if ok else ResponseBuilder.not_found("Menú no trobat.")

        # POST /menus/{id}/dishes -> Afegir plat a menú (N:M)
        if len(parts) == 3 and parts[1].isdigit() and parts[2] == "dishes" and method == "POST":
            m_id = int(parts[1])
            b = req.body or {}
            d_id = int(b.get("id_dish", 0))
            ok = self.menus.add_dish(m_id, d_id)
            return ResponseBuilder.ok({"added": ok})

        # DELETE /menus/{id}/dishes/{dish_id} -> Treure plat de menú (N:M)
        if len(parts) == 4 and parts[1].isdigit() and parts[2] == "dishes" and parts[3].isdigit() and method == "DELETE":
            m_id = int(parts[1])
            d_id = int(parts[3])
            ok = self.menus.remove_dish(m_id, d_id)
            return ResponseBuilder.no_content() if ok else ResponseBuilder.not_found("Relació Menú-Plat no trobada.")

        return ResponseBuilder.not_found("Ruta o mètode no suportat per a menús.")

    def _handle_sales(self, method: str, parts: list, req: HttpRequest) -> bytes:
        # GET /sales (admet cerques: ?date=YYYY-MM-DD, ?employee_id=X, ?menu_id=Y, ?date_from=A&date_to=B, ?page=1)
        if len(parts) == 1 and method == "GET":
            q = req.query_params
            if "date" in q:
                d_val = date.fromisoformat(q["date"])
                sales = self.sales.get_by_date(d_val)
            elif "employee_id" in q:
                sales = self.sales.get_by_employee(int(q["employee_id"]))
            elif "menu_id" in q:
                sales = self.sales.get_by_menu(int(q["menu_id"]))
            elif "date_from" in q and "date_to" in q:
                d_from = date.fromisoformat(q["date_from"])
                d_to = date.fromisoformat(q["date_to"])
                sales = self.sales.get_by_date_range(d_from, d_to)
            else:
                page = int(q.get("page", 1))
                page_size = int(q.get("page_size", 20))
                sales = self.sales.get_paginated(page, page_size)
            return ResponseBuilder.ok(sales)

        # POST /sales -> Enregistrar venda
        if len(parts) == 1 and method == "POST":
            b = req.body or {}
            d_val = date.fromisoformat(b.get("sale_date", str(date.today())))
            sale = self.sales.create(
                id_menu=int(b.get("id_menu", 0)),
                id_employee=int(b.get("id_employee", 0)),
                sale_date_val=d_val,
                quantity_sold=int(b.get("quantity_sold", 1))
            )
            return ResponseBuilder.created(sale)

        # /sales/{id_menu}/{id_employee}/{sale_date} -> PK composta
        if len(parts) == 4 and parts[1].isdigit() and parts[2].isdigit():
            m_id = int(parts[1])
            e_id = int(parts[2])
            d_val = date.fromisoformat(parts[3])

            if method == "GET":
                sale = self.sales.get_by_pk(m_id, e_id, d_val)
                return ResponseBuilder.ok(sale) if sale else ResponseBuilder.not_found("Venda no trobada.")
            elif method == "PUT":
                b = req.body or {}
                q_sold = int(b.get("quantity_sold", 1))
                sale = self.sales.update(m_id, e_id, d_val, q_sold)
                return ResponseBuilder.ok(sale) if sale else ResponseBuilder.not_found("Venda no trobada.")
            elif method == "DELETE":
                ok = self.sales.delete(m_id, e_id, d_val)
                return ResponseBuilder.no_content() if ok else ResponseBuilder.not_found("Venda no trobada.")

        return ResponseBuilder.not_found("Ruta o mètode no suportat per a vendes.")
