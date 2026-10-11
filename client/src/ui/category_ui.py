# category_ui.py: Interfície d'usuari per a la Gestió de Categories (Client).
#
# CONCEPTE CLAU PER A DAM (UI Desacoblada de la BD):
# Aquesta interfície no té cap accés a la base de dades ni a SQLAlchemy.
# Tota la informació es demana a través de l'objecte 'HttpClient' per xarxa TCP.
# Les dades rebudes es transformen en objectes 'CategoryEntity' del domini net.

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box

from common.domain.entities import CategoryEntity
from client.src.protocol.http_client import HttpClient

console = Console()


def menu_categories(client: HttpClient):
    """Menú interactiu de categories per al client."""
    while True:
        console.clear()
        console.print()  # Fix per a terminals que tallen la part superior
        console.print(Panel.fit("[bold magenta]Gestió de Categories[/bold magenta]", border_style="magenta", box=box.DOUBLE))
        console.print("1. Llistar Categories")
        console.print("2. Afegir Categoria")
        console.print("3. Modificar Categoria")
        console.print("4. Eliminar Categoria")
        console.print("0. Tornar al menú principal")

        opcio = console.input("\n[bold yellow]Selecciona una opció:[/bold yellow] ")

        if opcio == "1":
            list_categories(client)
        elif opcio == "2":
            add_category(client)
        elif opcio == "3":
            update_category(client)
        elif opcio == "4":
            delete_category(client)
        elif opcio == "0":
            break
        else:
            console.print("[red]Opció no vàlida.[/red]")
            console.input("Prem Enter per continuar...")


def list_categories(client: HttpClient, pause: bool = True):
    """Demana la llista de categories al servidor i la mostra en una taula."""
    console.print("\n[bold]--- Llistat de Categories ---[/bold]")

    # 1. Petició GET al servidor sobre TCP
    resp = client.get("/categories")

    if not resp.is_success:
        console.print(f"[bold red]Error en comunicar amb el servidor:[/bold red] {resp.error_message}")
        if pause:
            console.input("\nPrem Enter per continuar...")
        return

    raw_list = resp.data or []
    categories = [CategoryEntity.from_dict(c) for c in raw_list]

    if not categories:
        console.print("[yellow]No hi ha cap categoria a la base de dades.[/yellow]")
    else:
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("ID", style="dim", width=5)
        table.add_column("Nom de la Categoria")

        for cat in categories:
            table.add_row(str(cat.id), cat.category_name)

        console.print(table)

    if pause:
        console.input("\nPrem Enter per continuar...")


def add_category(client: HttpClient):
    """Envia una nova categoria al servidor amb POST."""
    console.print("\n[bold]--- Nova Categoria ---[/bold]")
    nom = console.input("Introdueix el nom de la categoria: ")

    if not nom.strip():
        console.print("[red]El nom no pot estar buit.[/red]")
        console.input("Prem Enter per continuar...")
        return

    # Petició POST amb cos JSON
    resp = client.post("/categories", {"category_name": nom.strip()})

    if resp.is_success:
        console.print(f"\n[green]✓ Categoria '{nom}' creada amb èxit al servidor![/green]")
    else:
        console.print(f"\n[bold red]Error del servidor:[/bold red] {resp.error_message}")

    console.input("\nPrem Enter per continuar...")


def update_category(client: HttpClient):
    """Modifica una categoria existent enviant PUT al servidor."""
    console.print("\n[bold]--- Modificar Categoria ---[/bold]")
    list_categories(client, pause=False)

    cat_id_str = console.input("Introdueix l'ID de la categoria a modificar: ")
    if not cat_id_str.isdigit():
        console.print("[red]L'ID ha de ser un número sencer.[/red]")
        console.input("Prem Enter per continuar...")
        return

    cat_id = int(cat_id_str)

    # Obtenim les dades actuals de la categoria per comprovar que existeix
    resp = client.get(f"/categories/{cat_id}")
    if not resp.is_success:
        console.print(f"[red]{resp.error_message}[/red]")
        console.input("Prem Enter per continuar...")
        return

    cat = CategoryEntity.from_dict(resp.data)
    console.print(f"Categoria actual: [cyan]{cat.category_name}[/cyan]")
    nou_nom = console.input("Introdueix el nou nom (deixa en blanc per cancel·lar): ")

    if nou_nom.strip():
        update_resp = client.put(f"/categories/{cat_id}", {"category_name": nou_nom.strip()})
        if update_resp.is_success:
            console.print(f"[green]✓ Categoria actualitzada correctament a '{nou_nom}'![/green]")
        else:
            console.print(f"[bold red]Error:[/bold red] {update_resp.error_message}")
    else:
        console.print("[yellow]Operació cancel·lada.[/yellow]")

    console.input("\nPrem Enter per continuar...")


def delete_category(client: HttpClient):
    """Elimina una categoria enviant DELETE al servidor."""
    console.print("\n[bold]--- Eliminar Categoria ---[/bold]")
    list_categories(client, pause=False)

    cat_id_str = console.input("Introdueix l'ID de la categoria a eliminar: ")
    if not cat_id_str.isdigit():
        console.print("[red]L'ID ha de ser un número sencer.[/red]")
        console.input("Prem Enter per continuar...")
        return

    cat_id = int(cat_id_str)

    # Obtenim les dades abans de demanar confirmació
    resp = client.get(f"/categories/{cat_id}")
    if not resp.is_success:
        console.print(f"[red]{resp.error_message}[/red]")
        console.input("Prem Enter per continuar...")
        return

    cat = CategoryEntity.from_dict(resp.data)
    console.print(f"Estàs a punt d'eliminar la categoria: [bold red]{cat.category_name}[/bold red]")
    confirmacio = console.input("N'estàs segur? (s/n): ").lower()

    if confirmacio == "s":
        del_resp = client.delete(f"/categories/{cat_id}")
        if del_resp.is_success:
            console.print(f"[green]✓ Categoria '{cat.category_name}' eliminada correctament![/green]")
        else:
            console.print(f"[bold red]Error:[/bold red] {del_resp.error_message}")
    else:
        console.print("[yellow]Eliminació cancel·lada.[/yellow]")

    console.input("\nPrem Enter per continuar...")
