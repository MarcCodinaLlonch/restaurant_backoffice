# __init__.py a client/src/ui
from .category_ui import menu_categories
from .allergen_ui import menu_allergens
from .dish_ui import menu_dishes
from .employee_ui import menu_employees
from .menu_ui import menu_menus
from .sale_ui import menu_sales

__all__ = [
    "menu_categories",
    "menu_allergens",
    "menu_dishes",
    "menu_employees",
    "menu_menus",
    "menu_sales",
]
