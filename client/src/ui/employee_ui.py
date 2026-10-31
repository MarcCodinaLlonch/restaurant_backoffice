# employee_ui.py: Interfície d'usuari per a la Gestió d'Empleats (Client).
# Comunica amb el servidor mitjançant peticions HTTP/1.1 sobre sockets TCP.

from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from client.src.protocol.http_client import HttpClient
from common.domain.entities import EmployeeEntity

console = Console()


def menu_employees(client: HttpClient) -> None:
    """Menú interactiu per a la gestió d'empleats."""
    while True:
        console.clear()
        console.print()
        console.print(
            Panel.fit(
                "[bold green]Gestió d'Empleats[/bold green]", border_style="green", box=box.DOUBLE
            )
        )
        console.print("1. Llistar tots els empleats")
        console.print("2. Afegir nou empleat (amb credencials opcionals)")
        console.print("3. Veure detall d'un empleat")
        console.print("4. Modificar empleat")
        console.print("5. Eliminar empleat")
        console.print("6. Cercar per nom/cognom")
        console.print("7. Filtrar per rol")
        console.print("0. Tornar al menú principal")

        option = console.input("\n[bold yellow]Selecciona una opció:[/bold yellow] ")

        if option == "1":
            list_employees(client)
        elif option == "2":
            add_employee(client)
        elif option == "3":
            view_employee_detail(client)
        elif option == "4":
            update_employee(client)
        elif option == "5":
            delete_employee(client)
        elif option == "6":
            search_employees(client)
        elif option == "7":
            filter_by_role(client)
        elif option == "0":
            break
        else:
            console.print("[red]Opció no vàlida.[/red]")
            console.input("Prem Enter per continuar...")


def list_employees(client: HttpClient, pause: bool = True) -> None:
    """Llista tots els empleats obtinguts des del servidor."""
    console.print("\n[bold]--- Llistat d'Empleats ---[/bold]")

    resp = client.get("/employees")
    if not resp.is_success:
        console.print(f"[bold red]Error del servidor:[/bold red] {resp.error_message}")
        if pause:
            console.input("\nPrem Enter per continuar...")
        return

    employees = [EmployeeEntity.from_dict(employee) for employee in (resp.data or [])]

    if not employees:
        console.print("[yellow]No hi ha cap empleat a la base de dades.[/yellow]")
    else:
        table = Table(show_header=True, header_style="bold green")
        table.add_column("ID", style="dim", width=5)
        table.add_column("Nom")
        table.add_column("Cognom")
        table.add_column("DNI")
        table.add_column("Rol")
        table.add_column("Credencials?", justify="center")

        for employee in employees:
            credentials_note = "[green]✓[/green]" if employee.has_credentials else "[red]✗[/red]"
            table.add_row(
                str(employee.id),
                employee.name,
                employee.surname,
                employee.national_id,
                employee.role,
                credentials_note,
            )

        console.print(table)

    if pause:
        console.input("\nPrem Enter per continuar...")


def add_employee(client: HttpClient) -> None:
    """Registra un nou empleat enviant les dades al servidor (POST)."""
    console.print("\n[bold]--- Nou Empleat ---[/bold]")

    name = console.input("Nom: ")
    surname = console.input("Cognom: ")
    national_id = console.input("DNI/NIE: ")
    role = console.input("Rol (ex: Cambrer, Cuiner, Encarregat): ")

    if not all([name.strip(), surname.strip(), national_id.strip(), role.strip()]):
        console.print("[red]Tots els camps són obligatoris.[/red]")
        console.input("Prem Enter per continuar...")
        return

    payload = {
        "name": name.strip(),
        "surname": surname.strip(),
        "national_id": national_id.strip(),
        "role": role.strip(),
    }

    console.print("\n[cyan]Vols afegir credencials d'accés a l'app per aquest empleat?[/cyan]")
    wants_credentials = console.input("(s/n): ").lower()

    if wants_credentials == "s":
        email = console.input("Email: ")
        password = console.input("Contrasenya: ")
        if email.strip() and password.strip():
            payload["email"] = email.strip()
            payload["password"] = password.strip()
        else:
            console.print(
                "[yellow]Email o contrasenya buits. Es crearà sense credencials.[/yellow]"
            )

    resp = client.post("/employees", payload)
    if resp.is_success:
        console.print(f"\n[green]✓ Empleat '{name} {surname}' creat amb èxit al servidor![/green]")
    else:
        console.print(f"\n[bold red]Error del servidor:[/bold red] {resp.error_message}")

    console.input("\nPrem Enter per continuar...")


def view_employee_detail(client: HttpClient) -> None:
    """Mostra la informació detallada d'un empleat."""
    console.print("\n[bold]--- Detall d'Empleat ---[/bold]")

    employee_id_text = console.input("Introdueix l'ID de l'empleat: ")
    if not employee_id_text.isdigit():
        console.print("[red]L'ID ha de ser un número sencer.[/red]")
        console.input("Prem Enter per continuar...")
        return

    employee_id = int(employee_id_text)
    resp = client.get(f"/employees/{employee_id}")

    if not resp.is_success:
        console.print(f"[red]{resp.error_message}[/red]")
    else:
        employee = EmployeeEntity.from_dict(resp.data)
        console.print(
            Panel.fit(f"[bold green]Empleat #{employee.id}[/bold green]", border_style="green")
        )

        table = Table(show_header=False, box=None)
        table.add_column("Camp", style="bold cyan", width=15)
        table.add_column("Valor")
        table.add_row("Nom", employee.name)
        table.add_row("Cognom", employee.surname)
        table.add_row("DNI", employee.national_id)
        table.add_row("Rol", employee.role)
        console.print(table)

        console.print("\n[bold cyan]Credencials d'accés (relació 1:1):[/bold cyan]")
        if employee.has_credentials:
            cred_table = Table(show_header=False, box=None)
            cred_table.add_column("Camp", style="bold", width=15)
            cred_table.add_column("Valor")
            cred_table.add_row("Email", employee.email or "—")
            cred_table.add_row("Password", "[dim]*** (xifrat SHA256 al servidor) ***[/dim]")
            console.print(cred_table)
        else:
            console.print("[yellow]Aquest empleat no té credencials d'accés assignades.[/yellow]")

    console.input("\nPrem Enter per continuar...")


def update_employee(client: HttpClient) -> None:
    """Actualitza la informació d'un empleat existent."""
    console.print("\n[bold]--- Modificar Empleat ---[/bold]")
    list_employees(client, pause=False)

    employee_id_text = console.input("Introdueix l'ID de l'empleat a modificar: ")
    if not employee_id_text.isdigit():
        console.print("[red]L'ID ha de ser un número sencer.[/red]")
        console.input("Prem Enter per continuar...")
        return

    employee_id = int(employee_id_text)
    resp = client.get(f"/employees/{employee_id}")
    if not resp.is_success:
        console.print(f"[red]{resp.error_message}[/red]")
        console.input("Prem Enter per continuar...")
        return

    employee = EmployeeEntity.from_dict(resp.data)
    console.print(f"\nModificant: [cyan]{employee.name} {employee.surname}[/cyan]")
    console.print("[dim]Deixa en blanc per no canviar el camp.[/dim]\n")

    new_name = console.input(f"Nom [{employee.name}]: ")
    new_surname = console.input(f"Cognom [{employee.surname}]: ")
    new_national_id = console.input(f"DNI [{employee.national_id}]: ")
    new_role = console.input(f"Rol [{employee.role}]: ")

    payload = {}
    if new_name.strip():
        payload["name"] = new_name.strip()
    if new_surname.strip():
        payload["surname"] = new_surname.strip()
    if new_national_id.strip():
        payload["national_id"] = new_national_id.strip()
    if new_role.strip():
        payload["role"] = new_role.strip()

    if payload:
        update_response = client.put(f"/employees/{employee_id}", payload)
        if update_response.is_success:
            console.print("\n[green]✓ Empleat actualitzat correctament![/green]")
        else:
            console.print(f"\n[bold red]Error:[/bold red] {update_response.error_message}")
    else:
        console.print("[yellow]Sense canvis.[/yellow]")

    console.input("\nPrem Enter per continuar...")


def delete_employee(client: HttpClient) -> None:
    """Elimina un empleat."""
    console.print("\n[bold]--- Eliminar Empleat ---[/bold]")
    list_employees(client, pause=False)

    employee_id_text = console.input("Introdueix l'ID de l'empleat a eliminar: ")
    if not employee_id_text.isdigit():
        console.print("[red]L'ID ha de ser un número sencer.[/red]")
        console.input("Prem Enter per continuar...")
        return

    employee_id = int(employee_id_text)
    resp = client.get(f"/employees/{employee_id}")
    if not resp.is_success:
        console.print(f"[red]{resp.error_message}[/red]")
        console.input("Prem Enter per continuar...")
        return

    employee = EmployeeEntity.from_dict(resp.data)
    credentials_note = "i les seves credencials." if employee.has_credentials else ""
    console.print(
        f"\nEstàs a punt d'eliminar l'empleat "
        f"[bold red]{employee.name} {employee.surname}[/bold red] {credentials_note}"
    )
    if employee.has_credentials:
        console.print(
            "[yellow]⚠ Les credencials s'eliminaran automàticament "
            "(CASCADE definit al servidor).[/yellow]"
        )

    confirmation = console.input("N'estàs segur? (s/n): ").lower()
    if confirmation == "s":
        delete_response = client.delete(f"/employees/{employee_id}")
        if delete_response.is_success:
            console.print(
                f"[green]✓ Empleat '{employee.name} {employee.surname}' "
                "eliminat correctament![/green]"
            )
        else:
            console.print(f"[bold red]Error:[/bold red] {delete_response.error_message}")
    else:
        console.print("[yellow]Eliminació cancel·lada.[/yellow]")

    console.input("\nPrem Enter per continuar...")


def search_employees(client: HttpClient) -> None:
    """Cerca empleats per nom i/o cognom via query parameters."""
    console.print("\n[bold]--- Cercar Empleats per Nom/Cognom ---[/bold]")
    name = console.input("Nom (o en blanc per ignorar): ")
    surname = console.input("Cognom (o en blanc per ignorar): ")

    if not name.strip() and not surname.strip():
        console.print("[red]Has d'introduir almenys un criteri de cerca.[/red]")
        console.input("Prem Enter per continuar...")
        return

    query = f"/employees?name={name.strip()}&surname={surname.strip()}"
    resp = client.get(query)
    if not resp.is_success:
        console.print(f"[bold red]Error:[/bold red] {resp.error_message}")
    else:
        employees = [EmployeeEntity.from_dict(employee) for employee in (resp.data or [])]
        if not employees:
            console.print("[yellow]No s'ha trobat cap empleat amb aquests criteris.[/yellow]")
        else:
            console.print(f"\n[green]{len(employees)} resultat(s) trobat(s):[/green]")
            table = Table(show_header=True, header_style="bold green")
            table.add_column("ID", style="dim", width=5)
            table.add_column("Nom")
            table.add_column("Cognom")
            table.add_column("DNI")
            table.add_column("Rol")
            table.add_column("Credencials?", justify="center")

            for employee in employees:
                credentials_note = (
                    "[green]✓[/green]" if employee.has_credentials else "[red]✗[/red]"
                )
                table.add_row(
                    str(employee.id),
                    employee.name,
                    employee.surname,
                    employee.national_id,
                    employee.role,
                    credentials_note,
                )
            console.print(table)

    console.input("\nPrem Enter per continuar...")


def filter_by_role(client: HttpClient) -> None:
    """Filtra empleats segons el rol utilitzant query parameter."""
    console.print("\n[bold]--- Filtrar Empleats per Rol ---[/bold]")
    role = console.input("Introdueix el rol a filtrar (ex: Cambrer, Cuiner, Encarregat): ")

    if not role.strip():
        console.print("[red]El rol no pot estar buit.[/red]")
        console.input("Prem Enter per continuar...")
        return

    resp = client.get(f"/employees?role={role.strip()}")
    if not resp.is_success:
        console.print(f"[bold red]Error:[/bold red] {resp.error_message}")
    else:
        employees = [EmployeeEntity.from_dict(employee) for employee in (resp.data or [])]
        if not employees:
            console.print(f"[yellow]No s'ha trobat cap empleat amb el rol '{role}'.[/yellow]")
        else:
            console.print(f"\n[green]{len(employees)} empleat(s) amb rol '{role}':[/green]")
            table = Table(show_header=True, header_style="bold green")
            table.add_column("ID", style="dim", width=5)
            table.add_column("Nom")
            table.add_column("Cognom")
            table.add_column("DNI")
            table.add_column("Rol")

            for employee in employees:
                table.add_row(
                    str(employee.id),
                    employee.name,
                    employee.surname,
                    employee.national_id,
                    employee.role,
                )
            console.print(table)

    console.input("\nPrem Enter per continuar...")
