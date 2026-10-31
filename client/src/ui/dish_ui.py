# dish_ui.py: Interfície d'usuari per a la Gestió de Plats (Client).
# Comunica amb el servidor a través de peticions HTTP sobre TCP.

from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from client.src.protocol.http_client import HttpClient
from common.domain.entities import AllergenEntity, CategoryEntity, DishEntity

console = Console()


def menu_dishes(client: HttpClient) -> None:
    """Menú interactiu de gestió de plats."""
    while True:
        console.clear()
        console.print()
        console.print(
            Panel.fit(
                "[bold cyan]Gestió de Plats[/bold cyan]", border_style="cyan", box=box.DOUBLE
            )
        )
        console.print("1. Llistar tots els plats")
        console.print("2. Afegir nou plat")
        console.print("3. Veure detall d'un plat")
        console.print("4. Modificar plat")
        console.print("5. Eliminar plat")
        console.print("6. Afegir al·lèrgen a un plat (N:M)")
        console.print("7. Filtrar plats actius")
        console.print("8. Cercar plat per nom")
        console.print("0. Tornar al menú principal")

        option = console.input("\n[bold yellow]Selecciona una opció:[/bold yellow] ")

        if option == "1":
            list_dishes(client)
        elif option == "2":
            add_dish(client)
        elif option == "3":
            view_dish_detail(client)
        elif option == "4":
            update_dish(client)
        elif option == "5":
            delete_dish(client)
        elif option == "6":
            add_allergen_to_dish(client)
        elif option == "7":
            list_active_dishes(client)
        elif option == "8":
            search_dish_by_name(client)
        elif option == "0":
            break
        else:
            console.print("[red]Opció no vàlida.[/red]")
            console.input("Prem Enter per continuar...")


def list_dishes(client: HttpClient, pause: bool = True) -> None:
    """Demana tots els plats al servidor i els mostra per pantalla."""
    console.print("\n[bold]--- Llistat de Plats ---[/bold]")

    resp = client.get("/dishes")
    if not resp.is_success:
        console.print(f"[bold red]Error del servidor:[/bold red] {resp.error_message}")
        if pause:
            console.input("\nPrem Enter per continuar...")
        return

    dishes = [DishEntity.from_dict(dish) for dish in (resp.data or [])]

    if not dishes:
        console.print("[yellow]No hi ha cap plat a la base de dades.[/yellow]")
    else:
        table = Table(show_header=True, header_style="bold cyan")
        table.add_column("ID", style="dim", width=5)
        table.add_column("Nom del Plat")
        table.add_column("Categoria (1:N)")
        table.add_column("Actiu?", justify="center")
        table.add_column("Núm. Al·lèrgens", justify="center")

        for dish in dishes:
            category_name = (
                dish.category_name if dish.category_name else "[red]Sense categoria[/red]"
            )
            is_active = "[green]✓[/green]" if dish.is_active else "[red]✗[/red]"
            num_allergens = str(len(dish.allergens))

            table.add_row(str(dish.id), dish.dish_name, category_name, is_active, num_allergens)

        console.print(table)

    if pause:
        console.input("\nPrem Enter per continuar...")


def add_dish(client: HttpClient) -> None:
    """Crea un nou plat seleccionant primer la seva categoria (1:N)."""
    console.print("\n[bold]--- Nou Plat ---[/bold]")

    # Demanem les categories disponibles al servidor
    categories_response = client.get("/categories")
    if not categories_response.is_success or not categories_response.data:
        console.print(
            "[red]No hi ha categories disponibles. Crea'n una primer al menú de Categories.[/red]"
        )
        console.input("Prem Enter per continuar...")
        return

    categories = [CategoryEntity.from_dict(category) for category in categories_response.data]
    console.print("\n[bold cyan]Categories disponibles:[/bold cyan]")
    categories_table = Table(show_header=True, header_style="bold cyan")
    categories_table.add_column("ID", style="dim", width=5)
    categories_table.add_column("Nom")
    for category in categories:
        categories_table.add_row(str(category.id), category.category_name)
    console.print(categories_table)

    category_id_text = console.input("\nIntrodueix l'ID de la categoria: ")
    if not category_id_text.isdigit():
        console.print("[red]L'ID ha de ser un número sencer.[/red]")
        console.input("Prem Enter per continuar...")
        return

    category_id = int(category_id_text)
    name = console.input("Nom del plat: ")
    description = console.input("Descripció (opcional, deixa en blanc per ometre): ")

    if not name.strip():
        console.print("[red]El nom del plat no pot estar buit.[/red]")
        console.input("Prem Enter per continuar...")
        return

    payload = {
        "dish_name": name.strip(),
        "id_category": category_id,
        "description": description.strip() if description.strip() else None,
        "is_active": True,
    }

    resp = client.post("/dishes", payload)
    if resp.is_success:
        console.print(f"\n[green]✓ Plat '{name}' creat amb èxit al servidor![/green]")
    else:
        console.print(f"\n[bold red]Error del servidor:[/bold red] {resp.error_message}")

    console.input("\nPrem Enter per continuar...")


def view_dish_detail(client: HttpClient) -> None:
    """Mostra el detall complet d'un plat i els seus al·lèrgens (N:M)."""
    console.print("\n[bold]--- Detall del Plat ---[/bold]")

    dish_id_str = console.input("Introdueix l'ID del plat: ")
    if not dish_id_str.isdigit():
        console.print("[red]L'ID ha de ser un número sencer.[/red]")
        console.input("Prem Enter per continuar...")
        return

    dish_id = int(dish_id_str)
    resp = client.get(f"/dishes/{dish_id}")

    if not resp.is_success:
        console.print(f"[red]{resp.error_message}[/red]")
    else:
        dish = DishEntity.from_dict(resp.data)
        console.print(
            Panel.fit(
                f"[bold cyan]Plat #{dish.id}: {dish.dish_name}[/bold cyan]", border_style="cyan"
            )
        )

        info_table = Table(show_header=False, box=None)
        info_table.add_column("Camp", style="bold cyan", width=15)
        info_table.add_column("Valor")
        info_table.add_row("Nom", dish.dish_name)
        info_table.add_row("Descripció", dish.description or "[dim]Sense descripció[/dim]")
        info_table.add_row("Categoria", dish.category_name or "—")
        info_table.add_row("Actiu", "[green]Sí[/green]" if dish.is_active else "[red]No[/red]")
        console.print(info_table)

        console.print("\n[bold cyan]Al·lèrgens d'aquest plat (relació N:M):[/bold cyan]")
        if not dish.allergens:
            console.print("[yellow]Aquest plat no té cap al·lèrgen assignat.[/yellow]")
        else:
            allergens_table = Table(show_header=True, header_style="bold yellow")
            allergens_table.add_column("ID", style="dim", width=5)
            allergens_table.add_column("Nom de l'Al·lèrgen")
            for allergen in dish.allergens:
                allergens_table.add_row(str(allergen.id), allergen.allergen_name)
            console.print(allergens_table)

    console.input("\nPrem Enter per continuar...")


def update_dish(client: HttpClient) -> None:
    """Modifica les dades d'un plat."""
    console.print("\n[bold]--- Modificar Plat ---[/bold]")
    list_dishes(client, pause=False)

    dish_id_str = console.input("Introdueix l'ID del plat a modificar: ")
    if not dish_id_str.isdigit():
        console.print("[red]L'ID ha de ser un número sencer.[/red]")
        console.input("Prem Enter per continuar...")
        return

    dish_id = int(dish_id_str)
    resp = client.get(f"/dishes/{dish_id}")
    if not resp.is_success:
        console.print(f"[red]{resp.error_message}[/red]")
        console.input("Prem Enter per continuar...")
        return

    dish = DishEntity.from_dict(resp.data)
    console.print(f"\nModificant: [cyan]{dish.dish_name}[/cyan]")
    console.print("[dim]Deixa en blanc per no canviar el camp.[/dim]\n")

    new_name = console.input(f"Nom [{dish.dish_name}]: ")
    new_description = console.input(f"Descripció [{dish.description or ''}]: ")

    payload = {}
    if new_name.strip():
        payload["dish_name"] = new_name.strip()
    if new_description.strip():
        payload["description"] = new_description.strip()

    current_status = "actiu" if dish.is_active else "inactiu"
    change_status = console.input(f"Canviar estat? Ara és [{current_status}] (s/n): ").lower()
    if change_status == "s":
        payload["is_active"] = not dish.is_active

    if payload:
        update_response = client.put(f"/dishes/{dish_id}", payload)
        if update_response.is_success:
            console.print("\n[green]✓ Plat actualitzat correctament![/green]")
        else:
            console.print(f"\n[bold red]Error:[/bold red] {update_response.error_message}")
    else:
        console.print("[yellow]Sense canvis realitzats.[/yellow]")

    console.input("\nPrem Enter per continuar...")


def delete_dish(client: HttpClient) -> None:
    """Elimina un plat del restaurant."""
    console.print("\n[bold]--- Eliminar Plat ---[/bold]")
    list_dishes(client, pause=False)

    dish_id_str = console.input("Introdueix l'ID del plat a eliminar: ")
    if not dish_id_str.isdigit():
        console.print("[red]L'ID ha de ser un número sencer.[/red]")
        console.input("Prem Enter per continuar...")
        return

    dish_id = int(dish_id_str)
    resp = client.get(f"/dishes/{dish_id}")
    if not resp.is_success:
        console.print(f"[red]{resp.error_message}[/red]")
        console.input("Prem Enter per continuar...")
        return

    dish = DishEntity.from_dict(resp.data)
    console.print(f"\nEstàs a punt d'eliminar el plat: [bold red]{dish.dish_name}[/bold red]")
    confirmation = console.input("N'estàs segur? (s/n): ").lower()

    if confirmation == "s":
        delete_response = client.delete(f"/dishes/{dish_id}")
        if delete_response.is_success:
            console.print(f"[green]✓ Plat '{dish.dish_name}' eliminat correctament![/green]")
        else:
            console.print(f"[bold red]Error:[/bold red] {delete_response.error_message}")
    else:
        console.print("[yellow]Eliminació cancel·lada.[/yellow]")

    console.input("\nPrem Enter per continuar...")


def add_allergen_to_dish(client: HttpClient) -> None:
    """Associa un al·lèrgen a un plat (relació N:M)."""
    console.print("\n[bold]--- Afegir Al·lèrgen a un Plat (N:M) ---[/bold]")

    list_dishes(client, pause=False)
    dish_id_str = console.input("\nID del plat al qual vols afegir un al·lèrgen: ")
    if not dish_id_str.isdigit():
        console.print("[red]L'ID ha de ser un número sencer.[/red]")
        console.input("Prem Enter per continuar...")
        return

    dish_id = int(dish_id_str)

    # Llistem els al·lèrgens disponibles
    allergens_response = client.get("/allergens")
    if not allergens_response.is_success or not allergens_response.data:
        console.print("[red]No hi ha cap al·lèrgen registrat al servidor.[/red]")
        console.input("Prem Enter per continuar...")
        return

    allergens = [AllergenEntity.from_dict(allergen) for allergen in allergens_response.data]
    allergens_table = Table(show_header=True, header_style="bold yellow")
    allergens_table.add_column("ID", style="dim", width=5)
    allergens_table.add_column("Nom de l'Al·lèrgen")
    for allergen in allergens:
        allergens_table.add_row(str(allergen.id), allergen.allergen_name)
    console.print(allergens_table)

    allergen_id_text = console.input("\nID de l'al·lèrgen a afegir: ")
    if not allergen_id_text.isdigit():
        console.print("[red]L'ID ha de ser un número sencer.[/red]")
        console.input("Prem Enter per continuar...")
        return

    allergen_id = int(allergen_id_text)
    post_response = client.post(f"/dishes/{dish_id}/allergens", {"id_allergen": allergen_id})

    if post_response.is_success:
        if post_response.data and post_response.data.get("added"):
            console.print("\n[green]✓ Al·lèrgen afegit correctament al plat![/green]")
        else:
            console.print("\n[yellow]L'al·lèrgen ja estava associat a aquest plat.[/yellow]")
    else:
        console.print(f"\n[bold red]Error:[/bold red] {post_response.error_message}")

    console.input("\nPrem Enter per continuar...")


def list_active_dishes(client: HttpClient) -> None:
    """Filtra només els plats en estat actiu utilitzant query param."""
    console.print("\n[bold]--- Plats Actius ---[/bold]")

    resp = client.get("/dishes?active=true")
    if not resp.is_success:
        console.print(f"[bold red]Error:[/bold red] {resp.error_message}")
    else:
        dishes = [DishEntity.from_dict(dish) for dish in (resp.data or [])]
        if not dishes:
            console.print("[yellow]No hi ha cap plat actiu.[/yellow]")
        else:
            console.print(f"[green]{len(dishes)} plat(s) actiu(s):[/green]")
            table = Table(show_header=True, header_style="bold cyan")
            table.add_column("ID", style="dim", width=5)
            table.add_column("Nom del Plat")
            table.add_column("Categoria")
            table.add_column("Al·lèrgens", justify="center")

            for dish in dishes:
                table.add_row(
                    str(dish.id),
                    dish.dish_name,
                    dish.category_name or "—",
                    str(len(dish.allergens)),
                )
            console.print(table)

    console.input("\nPrem Enter per continuar...")


def search_dish_by_name(client: HttpClient) -> None:
    """Cerca plats pel seu nom utilitzant query param."""
    console.print("\n[bold]--- Cercar Plat per Nom ---[/bold]")
    name = console.input("Introdueix el nom o part del nom a cercar: ")

    if not name.strip():
        console.print("[red]Has d'introduir algun text per cercar.[/red]")
        console.input("Prem Enter per continuar...")
        return

    resp = client.get(f"/dishes?name={name.strip()}")
    if not resp.is_success:
        console.print(f"[bold red]Error:[/bold red] {resp.error_message}")
    else:
        dishes = [DishEntity.from_dict(dish) for dish in (resp.data or [])]
        if not dishes:
            console.print(f"[yellow]No s'ha trobat cap plat que contingui '{name}'.[/yellow]")
        else:
            console.print(f"\n[green]{len(dishes)} resultat(s) trobat(s):[/green]")
            table = Table(show_header=True, header_style="bold cyan")
            table.add_column("ID", style="dim", width=5)
            table.add_column("Nom del Plat")
            table.add_column("Categoria")
            table.add_column("Actiu?", justify="center")

            for dish in dishes:
                is_active = "[green]✓[/green]" if dish.is_active else "[red]✗[/red]"
                table.add_row(str(dish.id), dish.dish_name, dish.category_name or "—", is_active)
            console.print(table)

    console.input("\nPrem Enter per continuar...")
