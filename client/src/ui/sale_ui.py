# sale_ui.py: Interfície d'usuari per a la Gestió de Vendes (Client).
# Comunica amb el servidor mitjançant peticions HTTP/1.1 sobre sockets TCP.

from datetime import date
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box

from common.domain.entities import SaleEntity, MenuEntity, EmployeeEntity
from client.src.protocol.http_client import HttpClient

console = Console()


def menu_sales(client: HttpClient):
    """Menú interactiu de gestió de vendes."""
    while True:
        console.clear()
        console.print()
        console.print(Panel.fit("[bold red]Gestió de Vendes[/bold red]", border_style="red", box=box.DOUBLE))
        console.print("1. Llistar totes les vendes")
        console.print("2. Registrar nova venda")
        console.print("3. Eliminar venda")
        console.print("4. Cercar vendes per data")
        console.print("5. Cercar vendes per empleat")
        console.print("6. Cercar vendes per menú")
        console.print("7. Cercar vendes per rang de dates")
        console.print("8. Modificar venda (quantitat)")
        console.print("0. Tornar al menú principal")

        opcio = console.input("\n[bold yellow]Selecciona una opció:[/bold yellow] ")

        if opcio == "1":
            list_sales(client)
        elif opcio == "2":
            add_sale(client)
        elif opcio == "3":
            delete_sale(client)
        elif opcio == "4":
            search_by_date(client)
        elif opcio == "5":
            search_by_employee(client)
        elif opcio == "6":
            search_by_menu(client)
        elif opcio == "7":
            search_by_date_range(client)
        elif opcio == "8":
            update_sale(client)
        elif opcio == "0":
            break
        else:
            console.print("[red]Opció no vàlida.[/red]")
            console.input("Prem Enter per continuar...")


def _print_sales_table(sales: list[SaleEntity]):
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
        nom_menu = sale.menu_name if sale.menu_name else str(sale.id_menu)
        nom_empleat = sale.employee_name if sale.employee_name else str(sale.id_employee)
        table.add_row(
            str(sale.id_menu),
            nom_menu,
            str(sale.id_employee),
            nom_empleat,
            str(sale.sale_date),
            str(sale.quantity_sold)
        )

    console.print(table)
    console.print(f"[dim]Total: {len(sales)} venda(es)[/dim]")


def list_sales(client: HttpClient, pause: bool = True):
    """Llista totes les vendes obtingudes del servidor."""
    console.print("\n[bold]--- Llistat de Vendes ---[/bold]")

    resp = client.get("/sales?page=1&page_size=20")
    if not resp.is_success:
        console.print(f"[bold red]Error del servidor:[/bold red] {resp.error_message}")
    else:
        sales = [SaleEntity.from_dict(s) for s in (resp.data or [])]
        _print_sales_table(sales)

    if pause:
        console.input("\nPrem Enter per continuar...")


def add_sale(client: HttpClient):
    """Registra una nova venda demanant Menú, Empleat, Data i Quantitat."""
    console.print("\n[bold]--- Nova Venda (N:M amb atributs) ---[/bold]")

    # Menús disponibles
    m_resp = client.get("/menus")
    if not m_resp.is_success or not m_resp.data:
        console.print("[red]No hi ha cap menú disponible. Crea'n un primer.[/red]")
        console.input("Prem Enter per continuar...")
        return

    menus = [MenuEntity.from_dict(m) for m in m_resp.data]
    console.print("\n[bold]Menús disponibles:[/bold]")
    m_table = Table(show_header=True, header_style="bold magenta")
    m_table.add_column("ID", style="dim", width=5)
    m_table.add_column("Nom")
    m_table.add_column("Preu", justify="right")
    for m in menus:
        m_table.add_row(str(m.id), m.menu_name, f"{m.price}€")
    console.print(m_table)

    menu_id_str = console.input("\nID del menú venut: ")
    if not menu_id_str.isdigit():
        console.print("[red]L'ID ha de ser un número.[/red]")
        console.input("Prem Enter per continuar...")
        return
    menu_id = int(menu_id_str)

    # Empleats disponibles
    e_resp = client.get("/employees")
    if not e_resp.is_success or not e_resp.data:
        console.print("[red]No hi ha cap empleat disponible. Crea'n un primer.[/red]")
        console.input("Prem Enter per continuar...")
        return

    employees = [EmployeeEntity.from_dict(e) for e in e_resp.data]
    console.print("\n[bold]Empleats disponibles:[/bold]")
    e_table = Table(show_header=True, header_style="bold green")
    e_table.add_column("ID", style="dim", width=5)
    e_table.add_column("Nom")
    e_table.add_column("Rol")
    for emp in employees:
        e_table.add_row(str(emp.id), f"{emp.name} {emp.surname}", emp.role)
    console.print(e_table)

    emp_id_str = console.input("\nID de l'empleat que fa la venda: ")
    if not emp_id_str.isdigit():
        console.print("[red]L'ID ha de ser un número.[/red]")
        console.input("Prem Enter per continuar...")
        return
    emp_id = int(emp_id_str)

    data_str = console.input("\nData de la venda (YYYY-MM-DD) [Enter per avui]: ")
    if not data_str.strip():
        data_venda = str(date.today())
    else:
        try:
            date.fromisoformat(data_str.strip())
            data_venda = data_str.strip()
        except ValueError:
            console.print("[red]Format de data incorrecte. Usa YYYY-MM-DD.[/red]")
            console.input("Prem Enter per continuar...")
            return

    quantitat_str = console.input("Quantitat venuda [1]: ")
    if not quantitat_str.strip():
        quantitat = 1
    elif quantitat_str.isdigit() and int(quantitat_str) > 0:
        quantitat = int(quantitat_str)
    else:
        console.print("[red]La quantitat ha de ser un número positiu.[/red]")
        console.input("Prem Enter per continuar...")
        return

    payload = {
        "id_menu": menu_id,
        "id_employee": emp_id,
        "sale_date": data_venda,
        "quantity_sold": quantitat
    }

    resp = client.post("/sales", payload)
    if resp.is_success:
        console.print(f"\n[green]✓ Venda registrada correctament al servidor![/green]")
        console.print(f"[dim]Menú ID {menu_id} | Empleat ID {emp_id} | Data: {data_venda} | Quantitat: {quantitat}[/dim]")
    else:
        console.print(f"\n[bold red]Error del servidor:[/bold red] {resp.error_message}")

    console.input("\nPrem Enter per continuar...")


def delete_sale(client: HttpClient):
    """Elimina una venda identificant la seva PK composta (Menú + Empleat + Data)."""
    console.print("\n[bold]--- Eliminar Venda ---[/bold]")
    list_sales(client, pause=False)

    menu_id_str = console.input("\nID del menú: ")
    emp_id_str = console.input("ID de l'empleat: ")
    data_str = console.input("Data (YYYY-MM-DD): ")

    if not menu_id_str.isdigit() or not emp_id_str.isdigit():
        console.print("[red]Els IDs han de ser números.[/red]")
        console.input("Prem Enter per continuar...")
        return

    try:
        date.fromisoformat(data_str.strip())
    except ValueError:
        console.print("[red]Format de data incorrecte. Usa YYYY-MM-DD.[/red]")
        console.input("Prem Enter per continuar...")
        return

    # Consultem si la venda existeix
    path = f"/sales/{menu_id_str}/{emp_id_str}/{data_str.strip()}"
    resp = client.get(path)

    if not resp.is_success:
        console.print(f"[red]{resp.error_message}[/red]")
    else:
        venda = SaleEntity.from_dict(resp.data)
        console.print(f"\nVenda trobada: Menú '{venda.menu_name}' | Empleat '{venda.employee_name}' | {venda.sale_date}")
        confirmacio = console.input("Eliminar? (s/n): ").lower()

        if confirmacio == "s":
            del_resp = client.delete(path)
            if del_resp.is_success:
                console.print("[green]✓ Venda eliminada correctament![/green]")
            else:
                console.print(f"[bold red]Error:[/bold red] {del_resp.error_message}")
        else:
            console.print("[yellow]Operació cancel·lada.[/yellow]")

    console.input("\nPrem Enter per continuar...")


def search_by_date(client: HttpClient):
    """Cerca vendes per data específica."""
    console.print("\n[bold]--- Vendes per Data ---[/bold]")
    data_str = console.input("Data (YYYY-MM-DD): ")

    try:
        date.fromisoformat(data_str.strip())
    except ValueError:
        console.print("[red]Format incorrecte. Usa YYYY-MM-DD.[/red]")
        console.input("Prem Enter per continuar...")
        return

    resp = client.get(f"/sales?date={data_str.strip()}")
    if not resp.is_success:
        console.print(f"[bold red]Error:[/bold red] {resp.error_message}")
    else:
        sales = [SaleEntity.from_dict(s) for s in (resp.data or [])]
        _print_sales_table(sales)

    console.input("\nPrem Enter per continuar...")


def search_by_employee(client: HttpClient):
    """Cerca vendes per empleat."""
    console.print("\n[bold]--- Vendes per Empleat ---[/bold]")

    emp_id_str = console.input("ID de l'empleat: ")
    if not emp_id_str.isdigit():
        console.print("[red]L'ID ha de ser un número.[/red]")
        console.input("Prem Enter per continuar...")
        return

    resp = client.get(f"/sales?employee_id={emp_id_str.strip()}")
    if not resp.is_success:
        console.print(f"[bold red]Error:[/bold red] {resp.error_message}")
    else:
        sales = [SaleEntity.from_dict(s) for s in (resp.data or [])]
        _print_sales_table(sales)

    console.input("\nPrem Enter per continuar...")


def search_by_menu(client: HttpClient):
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
        sales = [SaleEntity.from_dict(s) for s in (resp.data or [])]
        _print_sales_table(sales)

    console.input("\nPrem Enter per continuar...")


def search_by_date_range(client: HttpClient):
    """Cerca vendes per rang de dates."""
    console.print("\n[bold]--- Vendes per Rang de Dates ---[/bold]")

    d_ini = console.input("Data inici (YYYY-MM-DD): ").strip()
    d_fi = console.input("Data fi    (YYYY-MM-DD): ").strip()

    try:
        date.fromisoformat(d_ini)
        date.fromisoformat(d_fi)
    except ValueError:
        console.print("[red]Format incorrecte. Usa YYYY-MM-DD.[/red]")
        console.input("Prem Enter per continuar...")
        return

    resp = client.get(f"/sales?date_from={d_ini}&date_to={d_fi}")
    if not resp.is_success:
        console.print(f"[bold red]Error:[/bold red] {resp.error_message}")
    else:
        sales = [SaleEntity.from_dict(s) for s in (resp.data or [])]
        _print_sales_table(sales)

    console.input("\nPrem Enter per continuar...")


def update_sale(client: HttpClient):
    """Modifica la quantitat venuda d'una venda existent."""
    console.print("\n[bold]--- Modificar Venda ---[/bold]")
    list_sales(client, pause=False)

    menu_id_str = console.input("\nID del menú: ")
    emp_id_str = console.input("ID de l'empleat: ")
    data_str = console.input("Data (YYYY-MM-DD): ")

    if not menu_id_str.isdigit() or not emp_id_str.isdigit():
        console.print("[red]Els IDs han de ser números.[/red]")
        console.input("Prem Enter per continuar...")
        return

    try:
        date.fromisoformat(data_str.strip())
    except ValueError:
        console.print("[red]Format de data incorrecte.[/red]")
        console.input("Prem Enter per continuar...")
        return

    path = f"/sales/{menu_id_str}/{emp_id_str}/{data_str.strip()}"
    resp = client.get(path)

    if not resp.is_success:
        console.print(f"[red]{resp.error_message}[/red]")
    else:
        venda = SaleEntity.from_dict(resp.data)
        console.print(f"\nVenda trobada: Menú '{venda.menu_name}' | Empleat '{venda.employee_name}' | {venda.sale_date}")
        console.print(f"Quantitat actual: [cyan]{venda.quantity_sold}[/cyan]")

        nova_q_str = console.input("Nova quantitat (deixa en blanc per cancel·lar): ")
        if nova_q_str.strip():
            if nova_q_str.isdigit() and int(nova_q_str) > 0:
                put_resp = client.put(path, {"quantity_sold": int(nova_q_str)})
                if put_resp.is_success:
                    console.print("[green]✓ Quantitat actualitzada correctament![/green]")
                else:
                    console.print(f"[bold red]Error:[/bold red] {put_resp.error_message}")
            else:
                console.print("[red]La quantitat ha de ser un número positiu.[/red]")
        else:
            console.print("[yellow]Operació cancel·lada.[/yellow]")

    console.input("\nPrem Enter per continuar...")
