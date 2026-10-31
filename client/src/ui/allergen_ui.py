# allergen_ui.py: Interfície d'usuari per a la Gestió d'Al·lèrgens (Client).

from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from client.src.protocol.http_client import HttpClient
from common.domain.entities import AllergenEntity

console = Console()


def menu_allergens(client: HttpClient) -> None:
    """Menú interactiu d'al·lèrgens."""
    while True:
        console.clear()
        console.print()
        console.print(
            Panel.fit(
                "[bold yellow]Gestió d'Al·lèrgens[/bold yellow]",
                border_style="yellow",
                box=box.DOUBLE,
            )
        )
        console.print("1. Llistar Al·lèrgens")
        console.print("2. Afegir Al·lèrgen")
        console.print("3. Modificar Al·lèrgen")
        console.print("4. Eliminar Al·lèrgen")
        console.print("0. Tornar al menú principal")

        option = console.input("\n[bold yellow]Selecciona una opció:[/bold yellow] ")

        if option == "1":
            list_allergens(client)
        elif option == "2":
            add_allergen(client)
        elif option == "3":
            update_allergen(client)
        elif option == "4":
            delete_allergen(client)
        elif option == "0":
            break
        else:
            console.print("[red]Opció no vàlida.[/red]")
            console.input("Prem Enter per continuar...")


def list_allergens(client: HttpClient, pause: bool = True) -> None:
    """Llista tots els al·lèrgens demanant-los al servidor."""
    console.print("\n[bold]--- Llistat d'Al·lèrgens ---[/bold]")

    # Fem petició
    resp = client.get("/allergens")

    # Comprovem si ha anat malament per mostrar error
    if not resp.is_success:
        console.print(f"[bold red]Error del servidor:[/bold red] {resp.error_message}")
        if pause:
            console.input("\nPrem Enter per continuar...")
        return

    # Extreiem dades de Api response si ve buit hi posem llista buida per evitar errors
    raw_allergens = resp.data or []

    # Convertim cada diccionari brut del JSON en un objecte de domini
    allergens = [AllergenEntity.from_dict(allergen) for allergen in raw_allergens]

    if not allergens:  # Si llista esta buida avisem a usuari
        console.print("[yellow]No hi ha cap al·lèrgen a la base de dades.[/yellow]")
    else:  # Si hi ha dades convertim a taula rich
        table = Table(show_header=True, header_style="bold yellow")
        table.add_column("ID", style="dim", width=5)
        table.add_column("Nom de l'Al·lèrgen")

        for allergen in allergens:
            table.add_row(str(allergen.id), allergen.allergen_name)

        console.print(table)

    if pause:
        console.input("\nPrem Enter per continuar...")


def add_allergen(client: HttpClient) -> None:
    """Afegeix un nou al·lèrgen."""
    console.print("\n[bold]--- Nou Al·lèrgen ---[/bold]")
    name = console.input("Nom de l'al·lèrgen: ")

    if not name.strip():
        console.print("[red]El nom no pot estar buit.[/red]")
        console.input("Prem Enter per continuar...")
        return

    resp = client.post("/allergens", {"allergen_name": name.strip()})
    if resp.is_success:
        console.print(f"[green]✓ Al·lèrgen '{name}' creat amb èxit![/green]")
    else:
        console.print(f"[bold red]Error:[/bold red] {resp.error_message}")

    console.input("\nPrem Enter per continuar...")


def update_allergen(client: HttpClient) -> None:
    """Modifica el nom d'un al·lèrgen."""
    console.print("\n[bold]--- Modificar Al·lèrgen ---[/bold]")
    list_allergens(client, pause=False)

    allergen_id_text = console.input("Introdueix l'ID de l'al·lèrgen a modificar: ")
    if not allergen_id_text.isdigit():
        console.print("[red]L'ID ha de ser un número sencer.[/red]")
        console.input("Prem Enter per continuar...")
        return

    allergen_id = int(allergen_id_text)
    resp = client.get(f"/allergens/{allergen_id}")
    if not resp.is_success:
        console.print(f"[red]{resp.error_message}[/red]")
        console.input("Prem Enter per continuar...")
        return

    allergen = AllergenEntity.from_dict(resp.data)
    console.print(f"Nom actual: [cyan]{allergen.allergen_name}[/cyan]")
    new_name = console.input("Nou nom (deixa en blanc per cancel·lar): ")

    if new_name.strip():
        update_response = client.put(
            f"/allergens/{allergen_id}", {"allergen_name": new_name.strip()}
        )
        if update_response.is_success:
            console.print(f"[green]✓ Al·lèrgen actualitzat a '{new_name}'![/green]")
        else:
            console.print(f"[bold red]Error:[/bold red] {update_response.error_message}")
    else:
        console.print("[yellow]Operació cancel·lada.[/yellow]")

    console.input("\nPrem Enter per continuar...")


def delete_allergen(client: HttpClient) -> None:
    """Elimina un al·lèrgen."""
    console.print("\n[bold]--- Eliminar Al·lèrgen ---[/bold]")
    list_allergens(client, pause=False)

    allergen_id_text = console.input("Introdueix l'ID de l'al·lèrgen a eliminar: ")
    if not allergen_id_text.isdigit():
        console.print("[red]L'ID ha de ser un número sencer.[/red]")
        console.input("Prem Enter per continuar...")
        return

    allergen_id = int(allergen_id_text)
    resp = client.get(f"/allergens/{allergen_id}")
    if not resp.is_success:
        console.print(f"[red]{resp.error_message}[/red]")
        console.input("Prem Enter per continuar...")
        return

    allergen = AllergenEntity.from_dict(resp.data)
    console.print(f"Estàs a punt d'eliminar: [bold red]{allergen.allergen_name}[/bold red]")
    confirmation = console.input("N'estàs segur? (s/n): ").lower()

    if confirmation == "s":
        delete_response = client.delete(f"/allergens/{allergen_id}")
        if delete_response.is_success:
            console.print(f"[green]✓ Al·lèrgen '{allergen.allergen_name}' eliminat![/green]")
        else:
            console.print(f"[bold red]Error:[/bold red] {delete_response.error_message}")
    else:
        console.print("[yellow]Eliminació cancel·lada.[/yellow]")

    console.input("\nPrem Enter per continuar...")
