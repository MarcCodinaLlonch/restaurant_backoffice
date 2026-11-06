# seed.py: Utilitats d'inicialització i càrrega de dades d'exemple per a la base de dades.
# Assegura que qualsevol persona que cloni el projecte tingui
# una base de dades a punt sense haver d'executar migracions manuals.

from datetime import date
from urllib.parse import urlparse

from sqlalchemy import create_engine, text

from .models import Allergen, AppCredential, Category, Dish, Employee, Menu, Sale


def ensure_database_exists(db_url: str):
    """
    Comprova si la base de dades destí existeix a PostgreSQL.
    Si no existeix, es connecta a la base de dades de manteniment 'postgres'
    i la crea automàticament.
    """
    if not db_url or not db_url.startswith("postgresql"):
        return

    try:
        parsed = urlparse(db_url)
        target_db = parsed.path.lstrip("/")
        if not target_db:
            return

        # Connexió de manteniment cap a la base de dades per defecte 'postgres'
        maintenance_url = db_url.rsplit("/", 1)[0] + "/postgres"
        maintenance_engine = create_engine(maintenance_url, isolation_level="AUTOCOMMIT")

        with maintenance_engine.connect() as conn:
            exists = conn.execute(
                text("SELECT 1 FROM pg_database WHERE datname = :dbname"), {"dbname": target_db}
            ).scalar()

            if not exists:
                print(f"[*] Base de dades '{target_db}' no trobada. Creant-la automàticament...")
                conn.execute(text(f'CREATE DATABASE "{target_db}"'))
                print(f"[+] Base de dades '{target_db}' creada amb èxit.")
        maintenance_engine.dispose()
    except Exception as error:
        print(f"[!] Avís en verificar o crear la base de dades: {error}")


def seed_initial_data(session_factory):
    """
    Carrega les dades de demostració del restaurant si la base de dades està buida.
    Permet provar immediatament totes les consultes i pantalles del client sense dades prèvies.
    """
    if not session_factory:
        return

    with session_factory() as session:
        # Si ja hi ha categories, assumim que la base de dades ja està poblada
        if session.query(Category).count() > 0:
            return

        print("[*] Base de dades buida detectada. Carregant dades de demostració inicials...")

        # 1. Categories
        category_names = ["Entrants", "Plats Principals", "Postres", "Begudes", "Tapes", "Salses"]
        categories = {}
        for name in category_names:
            category = Category(category_name=name)
            session.add(category)
            session.flush()
            categories[name] = category

        # 2. Al·lèrgens
        allergen_names = [
            "Gluten",
            "Lactis",
            "Fruits secs",
            "Crustacis",
            "Ou",
            "Soja",
            "Peix",
            "Sèsam",
        ]
        allergens = {}
        for name in allergen_names:
            allergen = Allergen(allergen_name=name)
            session.add(allergen)
            session.flush()
            allergens[name] = allergen

        # 3. Empleats i credencials (1:1)
        employees_data = [
            ("Joan", "Pérez", "11111111A", "Cambrer", "joan@restaurant.cat", "hash_joan_123"),
            ("Maria", "García", "22222222B", "Cuinera", "maria@restaurant.cat", "hash_maria_456"),
            ("Marc", "Vila", "33333333C", "Encarregat", "marc@restaurant.cat", "hash_marc_789"),
            ("Anna", "Serra", "44444444D", "Cambrera", "anna@restaurant.cat", "hash_anna_321"),
            ("Lluís", "Font", "55555555E", "Cuiner", "lluis@restaurant.cat", "hash_lluis_654"),
            ("Marta", "Roca", "66666666F", "Cambrera", "marta@restaurant.cat", "hash_marta_987"),
        ]
        employees = {}
        for name, surname, national_id, role, email, password_hash in employees_data:
            employee = Employee(name=name, surname=surname, national_id=national_id, role=role)
            employee.credentials = AppCredential(email=email, password_hash=password_hash)
            session.add(employee)
            session.flush()
            employees[national_id] = employee

        # 4. Plats i relació N:M amb Al·lèrgens
        dishes_data = [
            {
                "name": "Amanida Cèsar",
                "desc": "Amanida fresca amb pollastre i crostons",
                "category": "Entrants",
                "allergens": ["Gluten", "Lactis", "Ou"],
            },
            {
                "name": "Macarrons a la bolonyesa",
                "desc": "Pasta amb salsa de tomàquet i carn picada",
                "category": "Plats Principals",
                "allergens": ["Gluten"],
            },
            {
                "name": "Lluç al forn",
                "desc": "Lluç fresc amb patates fornades",
                "category": "Plats Principals",
                "allergens": [],
            },
            {
                "name": "Pastís de formatge",
                "desc": "Cheesecake casolà",
                "category": "Postres",
                "allergens": ["Lactis", "Ou", "Gluten"],
            },
            {
                "name": "Aigua mineral",
                "desc": "Ampolla de 500ml",
                "category": "Begudes",
                "allergens": [],
            },
            {
                "name": "Patates Braves",
                "desc": "Patates cruixents amb salsa brava casolana",
                "category": "Tapes",
                "allergens": [],
            },
            {
                "name": "Calamars a la romana",
                "desc": "Anelles de calamar arrebossades",
                "category": "Tapes",
                "allergens": ["Gluten", "Peix", "Ou"],
            },
            {
                "name": "Entrecot a la brasa",
                "desc": "Entrecot de vedella de 300g amb guarnició",
                "category": "Plats Principals",
                "allergens": [],
            },
            {
                "name": "Coulant de xocolata",
                "desc": "Coulant calent amb interior líquid",
                "category": "Postres",
                "allergens": ["Gluten", "Lactis", "Ou"],
            },
            {
                "name": "Vi negre DO Penedès",
                "desc": "Copa de vi negre",
                "category": "Begudes",
                "allergens": [],
            },
        ]
        dishes = {}
        for item in dishes_data:
            dish = Dish(
                dish_name=item["name"],
                description=item["desc"],
                is_active=True,
                id_category=categories[item["category"]].id,
            )
            dish.allergens = [allergens[allergen_name] for allergen_name in item["allergens"]]
            session.add(dish)
            session.flush()
            dishes[item["name"]] = dish

        # 5. Menús i relació N:M amb Plats
        menus_data = [
            ("Menú Diari", 12.50, ["Amanida Cèsar", "Macarrons a la bolonyesa", "Aigua mineral"]),
            (
                "Menú Nit",
                18.00,
                ["Amanida Cèsar", "Lluç al forn", "Pastís de formatge", "Aigua mineral"],
            ),
            (
                "Menú Cap de Setmana",
                25.00,
                [
                    "Patates Braves",
                    "Entrecot a la brasa",
                    "Coulant de xocolata",
                    "Vi negre DO Penedès",
                ],
            ),
            (
                "Menú Tapes",
                15.00,
                ["Patates Braves", "Calamars a la romana", "Pastís de formatge", "Aigua mineral"],
            ),
        ]
        menus = {}
        for menu_name, price, menu_dishes in menus_data:
            menu = Menu(menu_name=menu_name, price=price)
            menu.dishes = [dishes[dish_name] for dish_name in menu_dishes]
            session.add(menu)
            session.flush()
            menus[menu_name] = menu

        # 6. Vendes
        sales_data = [
            ("Menú Diari", "11111111A", date(2026, 3, 26), 2),
            ("Menú Nit", "11111111A", date(2026, 3, 26), 1),
            ("Menú Diari", "33333333C", date(2026, 3, 25), 4),
            ("Menú Cap de Setmana", "44444444D", date(2026, 3, 28), 2),
            ("Menú Tapes", "66666666F", date(2026, 3, 28), 3),
            ("Menú Nit", "11111111A", date(2026, 3, 29), 2),
            ("Menú Cap de Setmana", "33333333C", date(2026, 3, 29), 5),
        ]
        for menu_name, employee_national_id, sale_date, quantity in sales_data:
            sale = Sale(
                id_menu=menus[menu_name].id,
                id_employee=employees[employee_national_id].id,
                sale_date=sale_date,
                quantity_sold=quantity,
            )
            session.add(sale)

        session.commit()
        print("[+] Dades inicials de demostració carregades correctament a la base de dades.")
