from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box

from src.domain.unit_of_work import UnitOfWorkFactory
from src.domain.models import Allergen

console = Console()


def menu_allergens(factory: UnitOfWorkFactory):
    while True:
        console.clear()
        console.print() # Fix pel PowerShell del VS Code que talla la part superior
        console.print(Panel.fit("[bold yellow]Gestió d'Al·lèrgens[/bold yellow]", border_style="yellow", box=box.DOUBLE))
        console.print("1. Llistar Al·lèrgens")
        console.print("2. Afegir Al·lèrgen")
        console.print("3. Modificar Al·lèrgen")
        console.print("4. Eliminar Al·lèrgen")
        console.print("0. Tornar al menú principal")

        opcio = console.input("\n[bold yellow]Selecciona una opció:[/bold yellow] ")

        if opcio == "1":
            list_allergens(factory)
        elif opcio == "2":
            add_allergen(factory)
        elif opcio == "3":
            update_allergen(factory)
        elif opcio == "4":
            delete_allergen(factory)
        elif opcio == "0":
            break
        else:
            console.print("[red]Opció no vàlida.[/red]")
            console.input("Prem Enter per continuar...")

#Mètode per opció 1. Llistar al·lèrgens
def list_allergens(factory: UnitOfWorkFactory, pause: bool = True):
    console.print("\n[bold]--- Llistat d'Al·lèrgens ---[/bold]")

    with factory.create() as uow:
        allergens = uow.allergens.get_all()

        if not allergens:
            console.print("[yellow]No hi ha cap al·lèrgen a la base de dades.[/yellow]")
        else:
            table = Table(show_header=True, header_style="bold yellow")
            table.add_column("ID", style="dim", width=5)
            table.add_column("Nom de l'Al·lèrgen")

            for al in allergens:
                table.add_row(str(al.id), al.allergen_name)

            console.print(table)

    if pause:
        console.input("\nPrem Enter per continuar...")

#Mètode per opció 2. Afegir al·lèrgen
def add_allergen(factory: UnitOfWorkFactory):
    console.print("\n[bold]--- Nou Al·lèrgen ---[/bold]")
    nom = console.input("Nom de l'al·lèrgen: ")

    if not nom.strip():
        console.print("[red]El nom no pot estar buit.[/red]")
        console.input("Prem Enter per continuar...")
        return

    with factory.create() as uow:
        try:
            nou_allergen = Allergen(allergen_name=nom)
            uow.allergens.add(nou_allergen)
            console.print(f"[green]✓ Al·lèrgen '{nom}' creat amb èxit![/green]")
        except Exception as e:
            console.print(f"[bold red]Error:[/bold red] {e}")

    console.input("\nPrem Enter per continuar...")

#Mètode per opció 3. Modificar al·lèrgen
def update_allergen(factory: UnitOfWorkFactory):
    console.print("\n[bold]--- Modificar Al·lèrgen ---[/bold]")
    list_allergens(factory, pause=False)

    #Llegim com a text i validem amb .isdigit() abans de convertir-lo a int()
    #Això evita que l'aplicació peti amb un ValueError si l'usuari tecleja lletres.
    al_id_str = console.input("Introdueix l'ID de l'al·lèrgen a modificar: ")
    if not al_id_str.isdigit():
        console.print("[red]L'ID ha de ser un número sencer.[/red]")
        console.input("Prem Enter per continuar...")
        return

    al_id = int(al_id_str)

    with factory.create() as uow:
        allergen = uow.allergens.get(al_id)

        if not allergen:
            console.print(f"[red]No s'ha trobat cap al·lèrgen amb l'ID {al_id}.[/red]")
        else:
            console.print(f"Nom actual: [cyan]{allergen.allergen_name}[/cyan]")
            nou_nom = console.input("Nou nom (deixa en blanc per cancel·lar): ")

            if nou_nom.strip():
                allergen.allergen_name = nou_nom
                uow.allergens.update(allergen)
                console.print(f"[green]✓ Al·lèrgen actualitzat a '{nou_nom}'![/green]")
            else:
                console.print("[yellow]Operació cancel·lada.[/yellow]")

    console.input("\nPrem Enter per continuar...")

#Mètode per opció 4. Eliminar al·lèrgen
def delete_allergen(factory: UnitOfWorkFactory):
    console.print("\n[bold]--- Eliminar Al·lèrgen ---[/bold]")
    list_allergens(factory, pause=False)

    al_id_str = console.input("Introdueix l'ID de l'al·lèrgen a eliminar: ")
    if not al_id_str.isdigit():
        console.print("[red]L'ID ha de ser un número sencer.[/red]")
        console.input("Prem Enter per continuar...")
        return

    al_id = int(al_id_str)

    with factory.create() as uow:
        allergen = uow.allergens.get(al_id)

        if not allergen:
            console.print(f"[red]No s'ha trobat cap al·lèrgen amb l'ID {al_id}.[/red]")
        else:
            console.print(f"Estàs a punt d'eliminar: [bold red]{allergen.allergen_name}[/bold red]")
            confirmacio = console.input("N'estàs segur? (s/n): ").lower()

            if confirmacio == "s":
                uow.allergens.delete(al_id)
                console.print(f"[green]✓ Al·lèrgen '{allergen.allergen_name}' eliminat![/green]")
            else:
                console.print("[yellow]Eliminació cancel·lada.[/yellow]")

    console.input("\nPrem Enter per continuar...")