# sale_ui.py: Interfície d'usuari per a la Gestió de Vendes (Client).
# Comunica amb el servidor mitjançant peticions HTTP/1.1 sobre sockets TCP.

from datetime import date

from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from client.src.protocol.http_client import HttpClient
from common.domain.entities import EmployeeEntity, MenuEntity, SaleEntity

console = Console()


def menu_sales(client: HttpClient) -> None:
    """Menú interactiu de gestió de vendes."""
    while True:
        console.clear()
        console.print()
        console.print(
            Panel.fit("[bold red]Gestió de Vendes[/bold red]", border_style="red", box=box.DOUBLE)
        )
        console.print("1. Llistar totes les vendes")
        console.print("2. Registrar nova venda")
        console.print("3. Eliminar venda")
        console.print("4. Cercar vendes per data")
        console.print("5. Cercar vendes per empleat")
        console.print("6. Cercar vendes per menú")
        console.print("7. Cercar vendes per rang de dates")
        console.print("8. Modificar venda (quantitat)")
        console.print("0. Tornar al menú principal")

        option = console.input("\n[bold yellow]Selecciona una opció:[/bold yellow] ")

        if option == "1":
            list_sales(client)
        elif option == "2":
            add_sale(client)
        elif option == "3":
            delete_sale(client)
        elif option == "4":
            search_by_date(client)
        elif option == "5":
            search_by_employee(client)
        elif option == "6":
            search_by_menu(client)
        elif option == "7":
            search_by_date_range(client)
        elif option == "8":
            update_sale(client)
        elif option == "0":
            break
        else:
            console.print("[red]Opció no vàlida.[/red]")
            console.input("Prem Enter per continuar...")


def _print_sales_table(sales: list[SaleEntity]) -> None:
    """Funció auxiliar per pintar la taula de vendes."""
    if not sales:
        console.print("[yellow]No s'han trobat vendes.[/yellow]")
        return

    table = Table(show_header=True, header_style="bold red")
    table.add_column("ID Menú", style="dim", width=7)
    table.add_column("Menú", style="magenta")
    table.add_column("ID Empleat", style="dim", width=10)
    table.add_column("Empleat")
    table.add_column("Data")
    table.add_column("Quantitat", justify="center")

    for sale in sales:
        menu_name = sale.menu_name if sale.menu_name else str(sale.id_menu)
        employee_name = sale.employee_name if sale.employee_name else str(sale.id_employee)
        table.add_row(
            str(sale.id_menu),
            menu_name,
            str(sale.id_employee),
            employee_name,
            str(sale.sale_date),
            str(sale.quantity_sold),
        )

    console.print(table)
    console.print(f"[dim]Total: {len(sales)} venda(es)[/dim]")


def list_sales(client: HttpClient, pause: bool = True) -> None:
    """Llista totes les vendes obtingudes del servidor."""
    console.print("\n[bold]--- Llistat de Vendes ---[/bold]")

    resp = client.get("/sales?page=1&page_size=20")
    if not resp.is_success:
        console.print(f"[bold red]Error del servidor:[/bold red] {resp.error_message}")
    else:
        sales = [SaleEntity.from_dict(sale) for sale in (resp.data or [])]
        _print_sales_table(sales)

    if pause:
        console.input("\nPrem Enter per continuar...")


def add_sale(client: HttpClient) -> None:
    """Registra una nova venda demanant Menú, Empleat, Data i Quantitat."""
    console.print("\n[bold]--- Nova Venda (N:M amb atributs) ---[/bold]")

    # Menús disponibles
    menus_response = client.get("/menus")
    if not menus_response.is_success or not menus_response.data:
        console.print("[red]No hi ha cap menú disponible. Crea'n un primer.[/red]")
        console.input("Prem Enter per continuar...")
        return

    menus = [MenuEntity.from_dict(menu) for menu in menus_response.data]
    console.print("\n[bold]Menús disponibles:[/bold]")
    menus_table = Table(show_header=True, header_style="bold magenta")
    menus_table.add_column("ID", style="dim", width=5)
    menus_table.add_column("Nom")
    menus_table.add_column("Preu", justify="right")
    for menu in menus:
        menus_table.add_row(str(menu.id), menu.menu_name, f"{menu.price}€")
    console.print(menus_table)

    menu_id_str = console.input("\nID del menú venut: ")
    if not menu_id_str.isdigit():
        console.print("[red]L'ID ha de ser un número.[/red]")
        console.input("Prem Enter per continuar...")
        return
    menu_id = int(menu_id_str)

    # Empleats disponibles
    employees_response = client.get("/employees")
    if not employees_response.is_success or not employees_response.data:
        console.print("[red]No hi ha cap empleat disponible. Crea'n un primer.[/red]")
        console.input("Prem Enter per continuar...")
        return

    employees = [EmployeeEntity.from_dict(employee) for employee in employees_response.data]
    console.print("\n[bold]Empleats disponibles:[/bold]")
    employees_table = Table(show_header=True, header_style="bold green")
    employees_table.add_column("ID", style="dim", width=5)
    employees_table.add_column("Nom")
    employees_table.add_column("Rol")
    for employee in employees:
        employees_table.add_row(
            str(employee.id), f"{employee.name} {employee.surname}", employee.role
        )
    console.print(employees_table)

    employee_id_text = console.input("\nID de l'empleat que fa la venda: ")
    if not employee_id_text.isdigit():
        console.print("[red]L'ID ha de ser un número.[/red]")
        console.input("Prem Enter per continuar...")
        return
    employee_id = int(employee_id_text)

    date_text = console.input("\nData de la venda (YYYY-MM-DD) [Enter per avui]: ")
    if not date_text.strip():
        sale_date = str(date.today())
    else:
        try:
            date.fromisoformat(date_text.strip())
            sale_date = date_text.strip()
        except ValueError:
            console.print("[red]Format de data incorrecte. Usa YYYY-MM-DD.[/red]")
            console.input("Prem Enter per continuar...")
            return

    quantity_text = console.input("Quantitat venuda [1]: ")
    if not quantity_text.strip():
        quantity = 1
    elif quantity_text.isdigit() and int(quantity_text) > 0:
        quantity = int(quantity_text)
    else:
        console.print("[red]La quantitat ha de ser un número positiu.[/red]")
        console.input("Prem Enter per continuar...")
        return

    payload = {
        "id_menu": menu_id,
        "id_employee": employee_id,
        "sale_date": sale_date,
        "quantity_sold": quantity,
    }

    resp = client.post("/sales", payload)
    if resp.is_success:
        console.print("\n[green]✓ Venda registrada correctament al servidor![/green]")
        console.print(
            f"[dim]Menú ID {menu_id} | Empleat ID {employee_id} | "
            f"Data: {sale_date} | Quantitat: {quantity}[/dim]"
        )
    else:
        console.print(f"\n[bold red]Error del servidor:[/bold red] {resp.error_message}")

    console.input("\nPrem Enter per continuar...")


def delete_sale(client: HttpClient) -> None:
    """Elimina una venda identificant la seva PK composta (Menú + Empleat + Data)."""
    console.print("\n[bold]--- Eliminar Venda ---[/bold]")
    list_sales(client, pause=False)

    menu_id_str = console.input("\nID del menú: ")
    employee_id_text = console.input("ID de l'empleat: ")
    date_text = console.input("Data (YYYY-MM-DD): ")

    if not menu_id_str.isdigit() or not employee_id_text.isdigit():
        console.print("[red]Els IDs han de ser números.[/red]")
        console.input("Prem Enter per continuar...")
        return

    try:
        date.fromisoformat(date_text.strip())
    except ValueError:
        console.print("[red]Format de data incorrecte. Usa YYYY-MM-DD.[/red]")
        console.input("Prem Enter per continuar...")
        return

    # Consultem si la venda existeix
    path = f"/sales/{menu_id_str}/{employee_id_text}/{date_text.strip()}"
    resp = client.get(path)

    if not resp.is_success:
        console.print(f"[red]{resp.error_message}[/red]")
    else:
        sale = SaleEntity.from_dict(resp.data)
        console.print(
            f"\nVenda trobada: Menú '{sale.menu_name}' | "
            f"Empleat '{sale.employee_name}' | {sale.sale_date}"
        )
        confirmation = console.input("Eliminar? (s/n): ").lower()

        if confirmation == "s":
            delete_response = client.delete(path)
            if delete_response.is_success:
                console.print("[green]✓ Venda eliminada correctament![/green]")
            else:
                console.print(f"[bold red]Error:[/bold red] {delete_response.error_message}")
        else:
            console.print("[yellow]Operació cancel·lada.[/yellow]")

    console.input("\nPrem Enter per continuar...")


def search_by_date(client: HttpClient) -> None:
    """Cerca vendes per data específica."""
    console.print("\n[bold]--- Vendes per Data ---[/bold]")
    date_text = console.input("Data (YYYY-MM-DD): ")

    try:
        date.fromisoformat(date_text.strip())
    except ValueError:
        console.print("[red]Format incorrecte. Usa YYYY-MM-DD.[/red]")
        console.input("Prem Enter per continuar...")
        return

    resp = client.get(f"/sales?date={date_text.strip()}")
    if not resp.is_success:
        console.print(f"[bold red]Error:[/bold red] {resp.error_message}")
    else:
        sales = [SaleEntity.from_dict(sale) for sale in (resp.data or [])]
        _print_sales_table(sales)

    console.input("\nPrem Enter per continuar...")


def search_by_employee(client: HttpClient) -> None:
    """Cerca vendes per empleat."""
    console.print("\n[bold]--- Vendes per Empleat ---[/bold]")

    employee_id_text = console.input("ID de l'empleat: ")
    if not employee_id_text.isdigit():
        console.print("[red]L'ID ha de ser un número.[/red]")
        console.input("Prem Enter per continuar...")
        return

    resp = client.get(f"/sales?employee_id={employee_id_text.strip()}")
    if not resp.is_success:
        console.print(f"[bold red]Error:[/bold red] {resp.error_message}")
    else:
        sales = [SaleEntity.from_dict(sale) for sale in (resp.data or [])]
        _print_sales_table(sales)

    console.input("\nPrem Enter per continuar...")


def search_by_menu(client: HttpClient) -> None:
    """Cerca vendes per menú."""
    console.print("\n[bold]--- Vendes per Menú ---[/bold]")

    menu_id_str = console.input("ID del menú: ")
    if not menu_id_str.isdigit():
        console.print("[red]L'ID ha de ser un número.[/red]")
        console.input("Prem Enter per continuar...")
        return

    resp = client.get(f"/sales?menu_id={menu_id_str.strip()}")
    if not resp.is_success:
        console.print(f"[bold red]Error:[/bold red] {resp.error_message}")
    else:
        sales = [SaleEntity.from_dict(sale) for sale in (resp.data or [])]
        _print_sales_table(sales)

    console.input("\nPrem Enter per continuar...")


def search_by_date_range(client: HttpClient) -> None:
    """Cerca vendes per rang de dates."""
    console.print("\n[bold]--- Vendes per Rang de Dates ---[/bold]")

    date_from = console.input("Data inici (YYYY-MM-DD): ").strip()
    date_to = console.input("Data fi    (YYYY-MM-DD): ").strip()

    try:
        date.fromisoformat(date_from)
        date.fromisoformat(date_to)
    except ValueError:
        console.print("[red]Format incorrecte. Usa YYYY-MM-DD.[/red]")
        console.input("Prem Enter per continuar...")
        return

    resp = client.get(f"/sales?date_from={date_from}&date_to={date_to}")
    if not resp.is_success:
        console.print(f"[bold red]Error:[/bold red] {resp.error_message}")
    else:
        sales = [SaleEntity.from_dict(sale) for sale in (resp.data or [])]
        _print_sales_table(sales)

    console.input("\nPrem Enter per continuar...")


def update_sale(client: HttpClient) -> None:
    """Modifica la quantitat venuda d'una venda existent."""
    console.print("\n[bold]--- Modificar Venda ---[/bold]")
    list_sales(client, pause=False)

    menu_id_str = console.input("\nID del menú: ")
    employee_id_text = console.input("ID de l'empleat: ")
    date_text = console.input("Data (YYYY-MM-DD): ")

    if not menu_id_str.isdigit() or not employee_id_text.isdigit():
        console.print("[red]Els IDs han de ser números.[/red]")
        console.input("Prem Enter per continuar...")
        return

    try:
        date.fromisoformat(date_text.strip())
    except ValueError:
        console.print("[red]Format de data incorrecte.[/red]")
        console.input("Prem Enter per continuar...")
        return

    path = f"/sales/{menu_id_str}/{employee_id_text}/{date_text.strip()}"
    resp = client.get(path)

    if not resp.is_success:
        console.print(f"[red]{resp.error_message}[/red]")
    else:
        sale = SaleEntity.from_dict(resp.data)
        console.print(
            f"\nVenda trobada: Menú '{sale.menu_name}' | "
            f"Empleat '{sale.employee_name}' | {sale.sale_date}"
        )
        console.print(f"Quantitat actual: [cyan]{sale.quantity_sold}[/cyan]")

        new_quantity_text = console.input("Nova quantitat (deixa en blanc per cancel·lar): ")
        if new_quantity_text.strip():
            if new_quantity_text.isdigit() and int(new_quantity_text) > 0:
                put_response = client.put(path, {"quantity_sold": int(new_quantity_text)})
                if put_response.is_success:
                    console.print("[green]✓ Quantitat actualitzada correctament![/green]")
                else:
                    console.print(f"[bold red]Error:[/bold red] {put_response.error_message}")
            else:
                console.print("[red]La quantitat ha de ser un número positiu.[/red]")
        else:
            console.print("[yellow]Operació cancel·lada.[/yellow]")

    console.input("\nPrem Enter per continuar...")
