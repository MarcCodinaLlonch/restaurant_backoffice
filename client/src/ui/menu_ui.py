# menu_ui.py: Interfície d'usuari per a la Gestió de Menús (Client).
# Comunica amb el servidor mitjançant peticions HTTP/1.1 sobre sockets TCP.

from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from client.src.protocol.http_client import HttpClient
from common.domain.entities import DishEntity, MenuEntity

console = Console()


def menu_menus(client: HttpClient) -> None:
    """Menú interactiu de gestió de menús."""
    while True:
        console.clear()
        console.print()
        console.print(
            Panel.fit(
                "[bold magenta]Gestió de Menús[/bold magenta]",
                border_style="magenta",
                box=box.DOUBLE,
            )
        )
        console.print("1. Llistar tots els menús")
        console.print("2. Afegir nou menú")
        console.print("3. Veure detall d'un menú")
        console.print("4. Modificar menú")
        console.print("5. Eliminar menú")
        console.print("6. Afegir plat a un menú (N:M)")
        console.print("7. Eliminar plat d'un menú (N:M)")
        console.print("8. Cercar per nom")
        console.print("9. Filtrar per rang de preus")
        console.print("0. Tornar al menú principal")

        option = console.input("\n[bold yellow]Selecciona una opció:[/bold yellow] ")

        if option == "1":
            list_menus(client)
        elif option == "2":
            add_menu(client)
        elif option == "3":
            view_menu_detail(client)
        elif option == "4":
            update_menu(client)
        elif option == "5":
            delete_menu(client)
        elif option == "6":
            add_dish_to_menu(client)
        elif option == "7":
            remove_dish_from_menu(client)
        elif option == "8":
            search_menu_by_name(client)
        elif option == "9":
            filter_by_price(client)
        elif option == "0":
            break
        else:
            console.print("[red]Opció no vàlida.[/red]")
            console.input("Prem Enter per continuar...")


def list_menus(client: HttpClient, pause: bool = True) -> None:
    """Llista tots els menús i quants plats conté cadascun."""
    console.print("\n[bold]--- Llistat de Menús ---[/bold]")

    resp = client.get("/menus")
    if not resp.is_success:
        console.print(f"[bold red]Error del servidor:[/bold red] {resp.error_message}")
        if pause:
            console.input("\nPrem Enter per continuar...")
        return

    menus = [MenuEntity.from_dict(menu) for menu in (resp.data or [])]

    if not menus:
        console.print("[yellow]No hi ha cap menú a la base de dades.[/yellow]")
    else:
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("ID", style="dim", width=5)
        table.add_column("Nom del Menú")
        table.add_column("Preu", justify="right")
        table.add_column("Núm. Plats (N:M)", justify="center")

        for menu in menus:
            table.add_row(str(menu.id), menu.menu_name, f"{menu.price}€", str(len(menu.dishes)))

        console.print(table)

    if pause:
        console.input("\nPrem Enter per continuar...")


def add_menu(client: HttpClient) -> None:
    """Crea un nou menú al servidor."""
    console.print("\n[bold]--- Nou Menú ---[/bold]")

    name = console.input("Nom del menú: ")
    if not name.strip():
        console.print("[red]El nom no pot estar buit.[/red]")
        console.input("Prem Enter per continuar...")
        return

    price_text = console.input("Preu (ex: 12.50): ")
    try:
        price = float(price_text)
        if price <= 0:
            raise ValueError()
    except ValueError:
        console.print("[red]El preu ha de ser un número vàlid i positiu.[/red]")
        console.input("Prem Enter per continuar...")
        return

    resp = client.post("/menus", {"menu_name": name.strip(), "price": price})
    if resp.is_success:
        console.print(f"\n[green]✓ Menú '{name}' creat amb èxit a {price}€![/green]")
        console.print("[dim]Ara pots afegir-hi plats des de l'opció 6.[/dim]")
    else:
        console.print(f"\n[bold red]Error del servidor:[/bold red] {resp.error_message}")

    console.input("\nPrem Enter per continuar...")


def view_menu_detail(client: HttpClient) -> None:
    """Mostra el detall d'un menú i els seus plats (N:M)."""
    console.print("\n[bold]--- Detall del Menú ---[/bold]")

    menu_id_str = console.input("Introdueix l'ID del menú: ")
    if not menu_id_str.isdigit():
        console.print("[red]L'ID ha de ser un número sencer.[/red]")
        console.input("Prem Enter per continuar...")
        return

    menu_id = int(menu_id_str)
    resp = client.get(f"/menus/{menu_id}")

    if not resp.is_success:
        console.print(f"[red]{resp.error_message}[/red]")
    else:
        menu = MenuEntity.from_dict(resp.data)
        console.print(
            Panel.fit(
                f"[bold magenta]Menú #{menu.id}: {menu.menu_name} — {menu.price}€[/bold magenta]",
                border_style="magenta",
            )
        )

        console.print("\n[bold magenta]Plats d'aquest menú (relació N:M):[/bold magenta]")
        if not menu.dishes:
            console.print("[yellow]Aquest menú no té cap plat assignat.[/yellow]")
        else:
            dish_table = Table(show_header=True, header_style="bold cyan")
            dish_table.add_column("ID", style="dim", width=5)
            dish_table.add_column("Nom del Plat")
            dish_table.add_column("Categoria")
            dish_table.add_column("Actiu?", justify="center")

            for dish in menu.dishes:
                is_active = "[green]✓[/green]" if dish.is_active else "[red]✗[/red]"
                dish_table.add_row(
                    str(dish.id), dish.dish_name, dish.category_name or "—", is_active
                )

            console.print(dish_table)

    console.input("\nPrem Enter per continuar...")


def update_menu(client: HttpClient) -> None:
    """Modifica les dades d'un menú."""
    console.print("\n[bold]--- Modificar Menú ---[/bold]")
    list_menus(client, pause=False)

    menu_id_str = console.input("Introdueix l'ID del menú a modificar: ")
    if not menu_id_str.isdigit():
        console.print("[red]L'ID ha de ser un número sencer.[/red]")
        console.input("Prem Enter per continuar...")
        return

    menu_id = int(menu_id_str)
    resp = client.get(f"/menus/{menu_id}")
    if not resp.is_success:
        console.print(f"[red]{resp.error_message}[/red]")
        console.input("Prem Enter per continuar...")
        return

    menu = MenuEntity.from_dict(resp.data)
    console.print(f"\nModificant: [magenta]{menu.menu_name}[/magenta]")
    console.print("[dim]Deixa en blanc per no canviar el camp.[/dim]\n")

    new_name = console.input(f"Nom [{menu.menu_name}]: ")
    new_price = console.input(f"Preu [{menu.price}]: ")

    payload = {}
    if new_name.strip():
        payload["menu_name"] = new_name.strip()
    if new_price.strip():
        try:
            payload["price"] = float(new_price)
        except ValueError:
            console.print("[red]Preu invàlid, s'ignora.[/red]")

    if payload:
        update_response = client.put(f"/menus/{menu_id}", payload)
        if update_response.is_success:
            console.print("\n[green]✓ Menú actualitzat correctament![/green]")
        else:
            console.print(f"\n[bold red]Error:[/bold red] {update_response.error_message}")
    else:
        console.print("[yellow]Sense canvis.[/yellow]")

    console.input("\nPrem Enter per continuar...")


def delete_menu(client: HttpClient) -> None:
    """Elimina un menú del servidor."""
    console.print("\n[bold]--- Eliminar Menú ---[/bold]")
    list_menus(client, pause=False)

    menu_id_str = console.input("Introdueix l'ID del menú a eliminar: ")
    if not menu_id_str.isdigit():
        console.print("[red]L'ID ha de ser un número sencer.[/red]")
        console.input("Prem Enter per continuar...")
        return

    menu_id = int(menu_id_str)
    resp = client.get(f"/menus/{menu_id}")
    if not resp.is_success:
        console.print(f"[red]{resp.error_message}[/red]")
        console.input("Prem Enter per continuar...")
        return

    menu = MenuEntity.from_dict(resp.data)
    console.print(f"\nEstàs a punt d'eliminar el menú: [bold red]{menu.menu_name}[/bold red]")
    confirmation = console.input("N'estàs segur? (s/n): ").lower()

    if confirmation == "s":
        delete_response = client.delete(f"/menus/{menu_id}")
        if delete_response.is_success:
            console.print(f"[green]✓ Menú '{menu.menu_name}' eliminat correctament![/green]")
        else:
            console.print(f"[bold red]Error:[/bold red] {delete_response.error_message}")
    else:
        console.print("[yellow]Eliminació cancel·lada.[/yellow]")

    console.input("\nPrem Enter per continuar...")


def add_dish_to_menu(client: HttpClient) -> None:
    """Afegeix un plat actiu a un menú (relació N:M)."""
    console.print("\n[bold]--- Afegir Plat a un Menú (N:M) ---[/bold]")

    list_menus(client, pause=False)
    menu_id_str = console.input("\nID del menú al qual vols afegir un plat: ")
    if not menu_id_str.isdigit():
        console.print("[red]L'ID ha de ser un número sencer.[/red]")
        console.input("Prem Enter per continuar...")
        return

    menu_id = int(menu_id_str)

    # Obtenim plats actius des del servidor
    dishes_response = client.get("/dishes?active=true")
    if not dishes_response.is_success or not dishes_response.data:
        console.print("[red]No hi ha cap plat actiu disponible.[/red]")
        console.input("Prem Enter per continuar...")
        return

    dishes = [DishEntity.from_dict(dish) for dish in dishes_response.data]
    console.print("\n[bold]Plats actius disponibles:[/bold]")
    dishes_table = Table(show_header=True, header_style="bold cyan")
    dishes_table.add_column("ID", style="dim", width=5)
    dishes_table.add_column("Nom del Plat")
    dishes_table.add_column("Categoria")
    for dish in dishes:
        dishes_table.add_row(str(dish.id), dish.dish_name, dish.category_name or "—")
    console.print(dishes_table)

    dish_id_str = console.input("\nID del plat a afegir: ")
    if not dish_id_str.isdigit():
        console.print("[red]L'ID ha de ser un número sencer.[/red]")
        console.input("Prem Enter per continuar...")
        return

    dish_id = int(dish_id_str)
    post_response = client.post(f"/menus/{menu_id}/dishes", {"id_dish": dish_id})

    if post_response.is_success:
        console.print("\n[green]✓ Plat afegit correctament al menú![/green]")
    else:
        console.print(f"\n[bold red]Error:[/bold red] {post_response.error_message}")

    console.input("\nPrem Enter per continuar...")


def remove_dish_from_menu(client: HttpClient) -> None:
    """Elimina un plat d'un menú (relació N:M)."""
    console.print("\n[bold]--- Eliminar Plat d'un Menú (N:M) ---[/bold]")

    list_menus(client, pause=False)
    menu_id_str = console.input("Introdueix l'ID del menú: ")
    if not menu_id_str.isdigit():
        console.print("[red]L'ID ha de ser un número sencer.[/red]")
        console.input("Prem Enter per continuar...")
        return

    menu_id = int(menu_id_str)
    resp = client.get(f"/menus/{menu_id}")
    if not resp.is_success:
        console.print(f"[red]{resp.error_message}[/red]")
        console.input("Prem Enter per continuar...")
        return

    menu = MenuEntity.from_dict(resp.data)
    if not menu.dishes:
        console.print(f"[yellow]El menú '{menu.menu_name}' no té cap plat assignat.[/yellow]")
        console.input("Prem Enter per continuar...")
        return

    console.print(f"\nPlats actuals del menú '[magenta]{menu.menu_name}[/magenta]':")
    dishes_table = Table(show_header=True, header_style="bold cyan")
    dishes_table.add_column("ID", style="dim", width=5)
    dishes_table.add_column("Nom del Plat")
    for dish in menu.dishes:
        dishes_table.add_row(str(dish.id), dish.dish_name)
    console.print(dishes_table)

    dish_id_str = console.input("\nID del plat a eliminar del menú: ")
    if not dish_id_str.isdigit():
        console.print("[red]L'ID ha de ser un número sencer.[/red]")
        console.input("Prem Enter per continuar...")
        return

    dish_id = int(dish_id_str)
    delete_response = client.delete(f"/menus/{menu_id}/dishes/{dish_id}")

    if delete_response.is_success:
        console.print("[green]✓ Plat eliminat del menú correctament![/green]")
    else:
        console.print(f"[bold red]Error:[/bold red] {delete_response.error_message}")

    console.input("\nPrem Enter per continuar...")


def search_menu_by_name(client: HttpClient) -> None:
    """Cerca menús per nom."""
    console.print("\n[bold]--- Cercar Menú per Nom ---[/bold]")
    name = console.input("Introdueix el nom o part del nom a cercar: ")

    if not name.strip():
        console.print("[red]Has d'introduir algun text per cercar.[/red]")
        console.input("Prem Enter per continuar...")
        return

    resp = client.get(f"/menus?name={name.strip()}")
    if not resp.is_success:
        console.print(f"[bold red]Error:[/bold red] {resp.error_message}")
    else:
        menus = [MenuEntity.from_dict(menu) for menu in (resp.data or [])]
        if not menus:
            console.print(f"[yellow]No s'ha trobat cap menú que contingui '{name}'.[/yellow]")
        else:
            console.print(f"\n[green]{len(menus)} resultat(s) trobat(s):[/green]")
            table = Table(show_header=True, header_style="bold magenta")
            table.add_column("ID", style="dim", width=5)
            table.add_column("Nom del Menú")
            table.add_column("Preu", justify="right")
            table.add_column("Núm. Plats", justify="center")
            for menu in menus:
                table.add_row(
                    str(menu.id), menu.menu_name, f"{menu.price}€", str(len(menu.dishes))
                )
            console.print(table)

    console.input("\nPrem Enter per continuar...")


def filter_by_price(client: HttpClient) -> None:
    """Filtra menús per rang de preus."""
    console.print("\n[bold]--- Filtrar Menús per Rang de Preus ---[/bold]")

    try:
        min_price = float(console.input("Preu mínim (ex: 5.00): "))
        max_price = float(console.input("Preu màxim (ex: 20.00): "))
    except ValueError:
        console.print("[red]Els preus han de ser números vàlids.[/red]")
        console.input("Prem Enter per continuar...")
        return

    if min_price > max_price:
        console.print("[red]El preu mínim no pot ser superior al màxim.[/red]")
        console.input("Prem Enter per continuar...")
        return

    resp = client.get(f"/menus?min_price={min_price}&max_price={max_price}")
    if not resp.is_success:
        console.print(f"[bold red]Error:[/bold red] {resp.error_message}")
    else:
        menus = [MenuEntity.from_dict(menu) for menu in (resp.data or [])]
        if not menus:
            console.print(f"[yellow]No hi ha cap menú entre {min_price}€ i {max_price}€.[/yellow]")
        else:
            console.print(
                f"\n[green]{len(menus)} menú(s) trobat(s) "
                f"entre {min_price}€ i {max_price}€:[/green]"
            )
            table = Table(show_header=True, header_style="bold magenta")
            table.add_column("ID", style="dim", width=5)
            table.add_column("Nom del Menú")
            table.add_column("Preu", justify="right")
            for menu in menus:
                table.add_row(str(menu.id), menu.menu_name, f"{menu.price}€")
            console.print(table)

    console.input("\nPrem Enter per continuar...")
