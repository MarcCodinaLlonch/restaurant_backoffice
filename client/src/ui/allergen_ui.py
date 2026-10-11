# allergen_ui.py: Interfície d'usuari per a la Gestió d'Al·lèrgens (Client).

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box

from common.domain.entities import AllergenEntity
from client.src.protocol.http_client import HttpClient

console = Console()


def menu_allergens(client: HttpClient):
    """Menú interactiu d'al·lèrgens."""
    while True:
        console.clear()
        console.print()
        console.print(Panel.fit("[bold yellow]Gestió d'Al·lèrgens[/bold yellow]", border_style="yellow", box=box.DOUBLE))
        console.print("1. Llistar Al·lèrgens")
        console.print("2. Afegir Al·lèrgen")
        console.print("3. Modificar Al·lèrgen")
        console.print("4. Eliminar Al·lèrgen")
        console.print("0. Tornar al menú principal")

        opcio = console.input("\n[bold yellow]Selecciona una opció:[/bold yellow] ")

        if opcio == "1":
            list_allergens(client)
        elif opcio == "2":
            add_allergen(client)
        elif opcio == "3":
            update_allergen(client)
        elif opcio == "4":
            delete_allergen(client)
        elif opcio == "0":
            break
        else:
            console.print("[red]Opció no vàlida.[/red]")
            console.input("Prem Enter per continuar...")


def list_allergens(client: HttpClient, pause: bool = True):
    """Llista tots els al·lèrgens demanant-los al servidor."""
    console.print("\n[bold]--- Llistat d'Al·lèrgens ---[/bold]")

    resp = client.get("/allergens")
    if not resp.is_success:
        console.print(f"[bold red]Error del servidor:[/bold red] {resp.error_message}")
        if pause:
            console.input("\nPrem Enter per continuar...")
        return

    raw_allergens = resp.data or []
    allergens = [AllergenEntity.from_dict(a) for a in raw_allergens]

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


def add_allergen(client: HttpClient):
    """Afegeix un nou al·lèrgen."""
    console.print("\n[bold]--- Nou Al·lèrgen ---[/bold]")
    nom = console.input("Nom de l'al·lèrgen: ")

    if not nom.strip():
        console.print("[red]El nom no pot estar buit.[/red]")
        console.input("Prem Enter per continuar...")
        return

    resp = client.post("/allergens", {"allergen_name": nom.strip()})
    if resp.is_success:
        console.print(f"[green]✓ Al·lèrgen '{nom}' creat amb èxit![/green]")
    else:
        console.print(f"[bold red]Error:[/bold red] {resp.error_message}")

    console.input("\nPrem Enter per continuar...")


def update_allergen(client: HttpClient):
    """Modifica el nom d'un al·lèrgen."""
    console.print("\n[bold]--- Modificar Al·lèrgen ---[/bold]")
    list_allergens(client, pause=False)

    al_id_str = console.input("Introdueix l'ID de l'al·lèrgen a modificar: ")
    if not al_id_str.isdigit():
        console.print("[red]L'ID ha de ser un número sencer.[/red]")
        console.input("Prem Enter per continuar...")
        return

    al_id = int(al_id_str)
    resp = client.get(f"/allergens/{al_id}")
    if not resp.is_success:
        console.print(f"[red]{resp.error_message}[/red]")
        console.input("Prem Enter per continuar...")
        return

    allergen = AllergenEntity.from_dict(resp.data)
    console.print(f"Nom actual: [cyan]{allergen.allergen_name}[/cyan]")
    nou_nom = console.input("Nou nom (deixa en blanc per cancel·lar): ")

    if nou_nom.strip():
        update_resp = client.put(f"/allergens/{al_id}", {"allergen_name": nou_nom.strip()})
        if update_resp.is_success:
            console.print(f"[green]✓ Al·lèrgen actualitzat a '{nou_nom}'![/green]")
        else:
            console.print(f"[bold red]Error:[/bold red] {update_resp.error_message}")
    else:
        console.print("[yellow]Operació cancel·lada.[/yellow]")

    console.input("\nPrem Enter per continuar...")


def delete_allergen(client: HttpClient):
    """Elimina un al·lèrgen."""
    console.print("\n[bold]--- Eliminar Al·lèrgen ---[/bold]")
    list_allergens(client, pause=False)

    al_id_str = console.input("Introdueix l'ID de l'al·lèrgen a eliminar: ")
    if not al_id_str.isdigit():
        console.print("[red]L'ID ha de ser un número sencer.[/red]")
        console.input("Prem Enter per continuar...")
        return

    al_id = int(al_id_str)
    resp = client.get(f"/allergens/{al_id}")
    if not resp.is_success:
        console.print(f"[red]{resp.error_message}[/red]")
        console.input("Prem Enter per continuar...")
        return

    allergen = AllergenEntity.from_dict(resp.data)
    console.print(f"Estàs a punt d'eliminar: [bold red]{allergen.allergen_name}[/bold red]")
    confirmacio = console.input("N'estàs segur? (s/n): ").lower()

    if confirmacio == "s":
        del_resp = client.delete(f"/allergens/{al_id}")
        if del_resp.is_success:
            console.print(f"[green]✓ Al·lèrgen '{allergen.allergen_name}' eliminat![/green]")
        else:
            console.print(f"[bold red]Error:[/bold red] {del_resp.error_message}")
    else:
        console.print("[yellow]Eliminació cancel·lada.[/yellow]")

    console.input("\nPrem Enter per continuar...")
