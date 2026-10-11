# menu_ui.py: Interfície d'usuari per a la Gestió de Menús (Client).
# Comunica amb el servidor mitjançant peticions HTTP/1.1 sobre sockets TCP.

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box

from common.domain.entities import MenuEntity, DishEntity
from client.src.protocol.http_client import HttpClient

console = Console()


def menu_menus(client: HttpClient):
    """Menú interactiu de gestió de menús."""
    while True:
        console.clear()
        console.print()
        console.print(Panel.fit("[bold magenta]Gestió de Menús[/bold magenta]", border_style="magenta", box=box.DOUBLE))
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

        opcio = console.input("\n[bold yellow]Selecciona una opció:[/bold yellow] ")

        if opcio == "1":
            list_menus(client)
        elif opcio == "2":
            add_menu(client)
        elif opcio == "3":
            view_menu_detail(client)
        elif opcio == "4":
            update_menu(client)
        elif opcio == "5":
            delete_menu(client)
        elif opcio == "6":
            add_dish_to_menu(client)
        elif opcio == "7":
            remove_dish_from_menu(client)
        elif opcio == "8":
            search_menu_by_name(client)
        elif opcio == "9":
            filter_by_price(client)
        elif opcio == "0":
            break
        else:
            console.print("[red]Opció no vàlida.[/red]")
            console.input("Prem Enter per continuar...")


def list_menus(client: HttpClient, pause: bool = True):
    """Llista tots els menús i quants plats conté cadascun."""
    console.print("\n[bold]--- Llistat de Menús ---[/bold]")

    resp = client.get("/menus")
    if not resp.is_success:
        console.print(f"[bold red]Error del servidor:[/bold red] {resp.error_message}")
        if pause:
            console.input("\nPrem Enter per continuar...")
        return

    menus = [MenuEntity.from_dict(m) for m in (resp.data or [])]

    if not menus:
        console.print("[yellow]No hi ha cap menú a la base de dades.[/yellow]")
    else:
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("ID", style="dim", width=5)
        table.add_column("Nom del Menú")
        table.add_column("Preu", justify="right")
        table.add_column("Núm. Plats (N:M)", justify="center")

        for m in menus:
            table.add_row(
                str(m.id),
                m.menu_name,
                f"{m.price}€",
                str(len(m.dishes))
            )

        console.print(table)

    if pause:
        console.input("\nPrem Enter per continuar...")


def add_menu(client: HttpClient):
    """Crea un nou menú al servidor."""
    console.print("\n[bold]--- Nou Menú ---[/bold]")

    nom = console.input("Nom del menú: ")
    if not nom.strip():
        console.print("[red]El nom no pot estar buit.[/red]")
        console.input("Prem Enter per continuar...")
        return

    preu_str = console.input("Preu (ex: 12.50): ")
    try:
        preu = float(preu_str)
        if preu <= 0:
            raise ValueError()
    except ValueError:
        console.print("[red]El preu ha de ser un número vàlid i positiu.[/red]")
        console.input("Prem Enter per continuar...")
        return

    resp = client.post("/menus", {"menu_name": nom.strip(), "price": preu})
    if resp.is_success:
        console.print(f"\n[green]✓ Menú '{nom}' creat amb èxit a {preu}€![/green]")
        console.print("[dim]Ara pots afegir-hi plats des de l'opció 6.[/dim]")
    else:
        console.print(f"\n[bold red]Error del servidor:[/bold red] {resp.error_message}")

    console.input("\nPrem Enter per continuar...")


def view_menu_detail(client: HttpClient):
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
        m = MenuEntity.from_dict(resp.data)
        console.print(Panel.fit(f"[bold magenta]Menú #{m.id}: {m.menu_name} — {m.price}€[/bold magenta]", border_style="magenta"))

        console.print("\n[bold magenta]Plats d'aquest menú (relació N:M):[/bold magenta]")
        if not m.dishes:
            console.print("[yellow]Aquest menú no té cap plat assignat.[/yellow]")
        else:
            dish_table = Table(show_header=True, header_style="bold cyan")
            dish_table.add_column("ID", style="dim", width=5)
            dish_table.add_column("Nom del Plat")
            dish_table.add_column("Categoria")
            dish_table.add_column("Actiu?", justify="center")

            for dish in m.dishes:
                actiu = "[green]✓[/green]" if dish.is_active else "[red]✗[/red]"
                dish_table.add_row(str(dish.id), dish.dish_name, dish.category_name or "—", actiu)

            console.print(dish_table)

    console.input("\nPrem Enter per continuar...")


def update_menu(client: HttpClient):
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

    m = MenuEntity.from_dict(resp.data)
    console.print(f"\nModificant: [magenta]{m.menu_name}[/magenta]")
    console.print("[dim]Deixa en blanc per no canviar el camp.[/dim]\n")

    nou_nom = console.input(f"Nom [{m.menu_name}]: ")
    nou_preu = console.input(f"Preu [{m.price}]: ")

    payload = {}
    if nou_nom.strip():
        payload["menu_name"] = nou_nom.strip()
    if nou_preu.strip():
        try:
            payload["price"] = float(nou_preu)
        except ValueError:
            console.print("[red]Preu invàlid, s'ignora.[/red]")

    if payload:
        update_resp = client.put(f"/menus/{menu_id}", payload)
        if update_resp.is_success:
            console.print(f"\n[green]✓ Menú actualitzat correctament![/green]")
        else:
            console.print(f"\n[bold red]Error:[/bold red] {update_resp.error_message}")
    else:
        console.print("[yellow]Sense canvis.[/yellow]")

    console.input("\nPrem Enter per continuar...")


def delete_menu(client: HttpClient):
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

    m = MenuEntity.from_dict(resp.data)
    console.print(f"\nEstàs a punt d'eliminar el menú: [bold red]{m.menu_name}[/bold red]")
    confirmacio = console.input("N'estàs segur? (s/n): ").lower()

    if confirmacio == "s":
        del_resp = client.delete(f"/menus/{menu_id}")
        if del_resp.is_success:
            console.print(f"[green]✓ Menú '{m.menu_name}' eliminat correctament![/green]")
        else:
            console.print(f"[bold red]Error:[/bold red] {del_resp.error_message}")
    else:
        console.print("[yellow]Eliminació cancel·lada.[/yellow]")

    console.input("\nPrem Enter per continuar...")


def add_dish_to_menu(client: HttpClient):
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
    d_resp = client.get("/dishes?active=true")
    if not d_resp.is_success or not d_resp.data:
        console.print("[red]No hi ha cap plat actiu disponible.[/red]")
        console.input("Prem Enter per continuar...")
        return

    dishes = [DishEntity.from_dict(d) for d in d_resp.data]
    console.print(f"\n[bold]Plats actius disponibles:[/bold]")
    d_table = Table(show_header=True, header_style="bold cyan")
    d_table.add_column("ID", style="dim", width=5)
    d_table.add_column("Nom del Plat")
    d_table.add_column("Categoria")
    for d in dishes:
        d_table.add_row(str(d.id), d.dish_name, d.category_name or "—")
    console.print(d_table)

    dish_id_str = console.input("\nID del plat a afegir: ")
    if not dish_id_str.isdigit():
        console.print("[red]L'ID ha de ser un número sencer.[/red]")
        console.input("Prem Enter per continuar...")
        return

    dish_id = int(dish_id_str)
    post_resp = client.post(f"/menus/{menu_id}/dishes", {"id_dish": dish_id})

    if post_resp.is_success:
        console.print(f"\n[green]✓ Plat afegit correctament al menú![/green]")
    else:
        console.print(f"\n[bold red]Error:[/bold red] {post_resp.error_message}")

    console.input("\nPrem Enter per continuar...")


def remove_dish_from_menu(client: HttpClient):
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

    m = MenuEntity.from_dict(resp.data)
    if not m.dishes:
        console.print(f"[yellow]El menú '{m.menu_name}' no té cap plat assignat.[/yellow]")
        console.input("Prem Enter per continuar...")
        return

    console.print(f"\nPlats actuals del menú '[magenta]{m.menu_name}[/magenta]':")
    d_table = Table(show_header=True, header_style="bold cyan")
    d_table.add_column("ID", style="dim", width=5)
    d_table.add_column("Nom del Plat")
    for d in m.dishes:
        d_table.add_row(str(d.id), d.dish_name)
    console.print(d_table)

    dish_id_str = console.input("\nID del plat a eliminar del menú: ")
    if not dish_id_str.isdigit():
        console.print("[red]L'ID ha de ser un número sencer.[/red]")
        console.input("Prem Enter per continuar...")
        return

    dish_id = int(dish_id_str)
    del_resp = client.delete(f"/menus/{menu_id}/dishes/{dish_id}")

    if del_resp.is_success:
        console.print(f"[green]✓ Plat eliminat del menú correctament![/green]")
    else:
        console.print(f"[bold red]Error:[/bold red] {del_resp.error_message}")

    console.input("\nPrem Enter per continuar...")


def search_menu_by_name(client: HttpClient):
    """Cerca menús per nom."""
    console.print("\n[bold]--- Cercar Menú per Nom ---[/bold]")
    nom = console.input("Introdueix el nom o part del nom a cercar: ")

    if not nom.strip():
        console.print("[red]Has d'introduir algun text per cercar.[/red]")
        console.input("Prem Enter per continuar...")
        return

    resp = client.get(f"/menus?name={nom.strip()}")
    if not resp.is_success:
        console.print(f"[bold red]Error:[/bold red] {resp.error_message}")
    else:
        menus = [MenuEntity.from_dict(m) for m in (resp.data or [])]
        if not menus:
            console.print(f"[yellow]No s'ha trobat cap menú que contingui '{nom}'.[/yellow]")
        else:
            console.print(f"\n[green]{len(menus)} resultat(s) trobat(s):[/green]")
            table = Table(show_header=True, header_style="bold magenta")
            table.add_column("ID", style="dim", width=5)
            table.add_column("Nom del Menú")
            table.add_column("Preu", justify="right")
            table.add_column("Núm. Plats", justify="center")
            for m in menus:
                table.add_row(str(m.id), m.menu_name, f"{m.price}€", str(len(m.dishes)))
            console.print(table)

    console.input("\nPrem Enter per continuar...")


def filter_by_price(client: HttpClient):
    """Filtra menús per rang de preus."""
    console.print("\n[bold]--- Filtrar Menús per Rang de Preus ---[/bold]")

    try:
        preu_min = float(console.input("Preu mínim (ex: 5.00): "))
        preu_max = float(console.input("Preu màxim (ex: 20.00): "))
    except ValueError:
        console.print("[red]Els preus han de ser números vàlids.[/red]")
        console.input("Prem Enter per continuar...")
        return

    if preu_min > preu_max:
        console.print("[red]El preu mínim no pot ser superior al màxim.[/red]")
        console.input("Prem Enter per continuar...")
        return

    resp = client.get(f"/menus?min_price={preu_min}&max_price={preu_max}")
    if not resp.is_success:
        console.print(f"[bold red]Error:[/bold red] {resp.error_message}")
    else:
        menus = [MenuEntity.from_dict(m) for m in (resp.data or [])]
        if not menus:
            console.print(f"[yellow]No hi ha cap menú entre {preu_min}€ i {preu_max}€.[/yellow]")
        else:
            console.print(f"\n[green]{len(menus)} menú(s) trobat(s) entre {preu_min}€ i {preu_max}€:[/green]")
            table = Table(show_header=True, header_style="bold magenta")
            table.add_column("ID", style="dim", width=5)
            table.add_column("Nom del Menú")
            table.add_column("Preu", justify="right")
            for m in menus:
                table.add_row(str(m.id), m.menu_name, f"{m.price}€")
            console.print(table)

    console.input("\nPrem Enter per continuar...")
