#Importem Rich per millorar la visualització del menú i el banner
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich import box

#Importem els submenús
from src.ui.category_ui import menu_categories
from src.ui.employee_ui import menu_employees
from src.ui.allergen_ui import menu_allergens
from src.ui.dish_ui import menu_dishes
from src.ui.menu_ui import menu_menus
from src.ui.sale_ui import menu_sales

# Importem la Factory i la configuració que ja tens creada
from src.domain.unit_of_work import UnitOfWorkFactory
from src.domain.config import DB_URL

# Inicialitzem Rich
console = Console()
    
# Funció nova per imprimir el banner
def print_banner():
    try:
        # Llegim el fitxer banner.txt
        with open("banner.txt", "r", encoding="utf-8") as file:
            ascii_art = file.read()
            # Ho imprimim en color cyan (podes canviar "cyan" per "green", "magenta", etc.)
            console.print(Text(ascii_art, style="bold cyan"))
    except FileNotFoundError:
        # Si no troba el fitxer, no passa res, no petarà, simplement saltarà l'error
        pass

def main_menu(uow_factory: UnitOfWorkFactory): #passem uow al menu principal per poder-lo passar després a submenús
    while True:
        # Cada vegada que mostrem el menú, netegem la consola i mostrem el banner
        console.clear()
        #Cridem funció per imprimir el banner cada vegada que mostrem el menú principal
        print_banner()

        console.print(Panel.fit("[bold blue]Restaurant BackOffice - Menú Principal[/bold blue]", border_style="blue", box=box.DOUBLE)) #Panel.fit fa que amplada de la capsa s'ajusti a la llargada del text, box.DOUBLE importa caixa amb doble línia
        console.print("1. Gestió d'Empleats") # (Inclou 1:1 amb Credencials)
        console.print("2. Gestió de Categories")
        console.print("3. Gestió de Plat") #  (1:N amb Categories i N:M amb Al·lèrgens)
        console.print("4. Gestió d'Al·lèrgens")
        console.print("5. Gestió de Menús") # (N:M amb Plats)
        console.print("6. Gestió de Vendes") # (N:M amb atributs)
        console.print("0. Sortir")
        
        opcio = console.input("\n[bold yellow]Selecciona una opció:[/bold yellow] ")
        
        if opcio == "1":
            menu_employees(uow_factory)
        elif opcio == "2":
            menu_categories(uow_factory)
        elif opcio == "3":
            menu_dishes(uow_factory)
        elif opcio == "4":
            menu_allergens(uow_factory)
        elif opcio == "5":
            menu_menus(uow_factory)
        elif opcio == "6":
            menu_sales(uow_factory)
        elif opcio == "0":
            console.print("[green]Fins aviat![/green]")
            break
        else:
            console.print("[red]Opció no vàlida.[/red]")
            console.input("Prem Enter per continuar...")

if __name__ == "__main__":
    if not DB_URL:
        console.print("[bold red]Error: No s'ha pogut configurar correctament la connexió a la BD.[/bold red]")
        exit(1)
        
    # Creem la factory fent servir URL centralitzada a config.py
    factory = UnitOfWorkFactory(DB_URL)
    
    # Iniciem el menú principal
    main_menu(factory)
