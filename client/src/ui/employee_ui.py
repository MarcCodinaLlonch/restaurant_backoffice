# employee_ui.py: Interfície d'usuari per a la Gestió d'Empleats (Client).
# Comunica amb el servidor mitjançant peticions HTTP/1.1 sobre sockets TCP.

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box

from common.domain.entities import EmployeeEntity
from client.src.protocol.http_client import HttpClient

console = Console()


def menu_employees(client: HttpClient):
    """Menú interactiu per a la gestió d'empleats."""
    while True:
        console.clear()
        console.print()
        console.print(Panel.fit("[bold green]Gestió d'Empleats[/bold green]", border_style="green", box=box.DOUBLE))
        console.print("1. Llistar tots els empleats")
        console.print("2. Afegir nou empleat (amb credencials opcionals)")
        console.print("3. Veure detall d'un empleat")
        console.print("4. Modificar empleat")
        console.print("5. Eliminar empleat")
        console.print("6. Cercar per nom/cognom")
        console.print("7. Filtrar per rol")
        console.print("0. Tornar al menú principal")

        opcio = console.input("\n[bold yellow]Selecciona una opció:[/bold yellow] ")

        if opcio == "1":
            list_employees(client)
        elif opcio == "2":
            add_employee(client)
        elif opcio == "3":
            view_employee_detail(client)
        elif opcio == "4":
            update_employee(client)
        elif opcio == "5":
            delete_employee(client)
        elif opcio == "6":
            search_employees(client)
        elif opcio == "7":
            filter_by_role(client)
        elif opcio == "0":
            break
        else:
            console.print("[red]Opció no vàlida.[/red]")
            console.input("Prem Enter per continuar...")


def list_employees(client: HttpClient, pause: bool = True):
    """Llista tots els empleats obtinguts des del servidor."""
    console.print("\n[bold]--- Llistat d'Empleats ---[/bold]")

    resp = client.get("/employees")
    if not resp.is_success:
        console.print(f"[bold red]Error del servidor:[/bold red] {resp.error_message}")
        if pause:
            console.input("\nPrem Enter per continuar...")
        return

    employees = [EmployeeEntity.from_dict(e) for e in (resp.data or [])]

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

        for emp in employees:
            te_credencials = "[green]✓[/green]" if emp.has_credentials else "[red]✗[/red]"
            table.add_row(
                str(emp.id),
                emp.name,
                emp.surname,
                emp.national_id,
                emp.role,
                te_credencials
            )

        console.print(table)

    if pause:
        console.input("\nPrem Enter per continuar...")


def add_employee(client: HttpClient):
    """Registra un nou empleat enviant les dades al servidor (POST)."""
    console.print("\n[bold]--- Nou Empleat ---[/bold]")

    nom = console.input("Nom: ")
    cognom = console.input("Cognom: ")
    dni = console.input("DNI/NIE: ")
    rol = console.input("Rol (ex: Cambrer, Cuiner, Encarregat): ")

    if not all([nom.strip(), cognom.strip(), dni.strip(), rol.strip()]):
        console.print("[red]Tots els camps són obligatoris.[/red]")
        console.input("Prem Enter per continuar...")
        return

    payload = {
        "name": nom.strip(),
        "surname": cognom.strip(),
        "national_id": dni.strip(),
        "role": rol.strip(),
    }

    console.print("\n[cyan]Vols afegir credencials d'accés a l'app per aquest empleat?[/cyan]")
    vol_credencials = console.input("(s/n): ").lower()

    if vol_credencials == "s":
        email = console.input("Email: ")
        password = console.input("Contrasenya: ")
        if email.strip() and password.strip():
            payload["email"] = email.strip()
            payload["password"] = password.strip()
        else:
            console.print("[yellow]Email o contrasenya buits. Es crearà sense credencials.[/yellow]")

    resp = client.post("/employees", payload)
    if resp.is_success:
        console.print(f"\n[green]✓ Empleat '{nom} {cognom}' creat amb èxit al servidor![/green]")
    else:
        console.print(f"\n[bold red]Error del servidor:[/bold red] {resp.error_message}")

    console.input("\nPrem Enter per continuar...")


def view_employee_detail(client: HttpClient):
    """Mostra la informació detallada d'un empleat."""
    console.print("\n[bold]--- Detall d'Empleat ---[/bold]")

    emp_id_str = console.input("Introdueix l'ID de l'empleat: ")
    if not emp_id_str.isdigit():
        console.print("[red]L'ID ha de ser un número sencer.[/red]")
        console.input("Prem Enter per continuar...")
        return

    emp_id = int(emp_id_str)
    resp = client.get(f"/employees/{emp_id}")

    if not resp.is_success:
        console.print(f"[red]{resp.error_message}[/red]")
    else:
        emp = EmployeeEntity.from_dict(resp.data)
        console.print(Panel.fit(f"[bold green]Empleat #{emp.id}[/bold green]", border_style="green"))

        table = Table(show_header=False, box=None)
        table.add_column("Camp", style="bold cyan", width=15)
        table.add_column("Valor")
        table.add_row("Nom", emp.name)
        table.add_row("Cognom", emp.surname)
        table.add_row("DNI", emp.national_id)
        table.add_row("Rol", emp.role)
        console.print(table)

        console.print("\n[bold cyan]Credencials d'accés (relació 1:1):[/bold cyan]")
        if emp.has_credentials:
            cred_table = Table(show_header=False, box=None)
            cred_table.add_column("Camp", style="bold", width=15)
            cred_table.add_column("Valor")
            cred_table.add_row("Email", emp.email or "—")
            cred_table.add_row("Password", "[dim]*** (xifrat SHA256 al servidor) ***[/dim]")
            console.print(cred_table)
        else:
            console.print("[yellow]Aquest empleat no té credencials d'accés assignades.[/yellow]")

    console.input("\nPrem Enter per continuar...")


def update_employee(client: HttpClient):
    """Actualitza la informació d'un empleat existent."""
    console.print("\n[bold]--- Modificar Empleat ---[/bold]")
    list_employees(client, pause=False)

    emp_id_str = console.input("Introdueix l'ID de l'empleat a modificar: ")
    if not emp_id_str.isdigit():
        console.print("[red]L'ID ha de ser un número sencer.[/red]")
        console.input("Prem Enter per continuar...")
        return

    emp_id = int(emp_id_str)
    resp = client.get(f"/employees/{emp_id}")
    if not resp.is_success:
        console.print(f"[red]{resp.error_message}[/red]")
        console.input("Prem Enter per continuar...")
        return

    emp = EmployeeEntity.from_dict(resp.data)
    console.print(f"\nModificant: [cyan]{emp.name} {emp.surname}[/cyan]")
    console.print("[dim]Deixa en blanc per no canviar el camp.[/dim]\n")

    nou_nom = console.input(f"Nom [{emp.name}]: ")
    nou_cognom = console.input(f"Cognom [{emp.surname}]: ")
    nou_dni = console.input(f"DNI [{emp.national_id}]: ")
    nou_rol = console.input(f"Rol [{emp.role}]: ")

    payload = {}
    if nou_nom.strip():
        payload["name"] = nou_nom.strip()
    if nou_cognom.strip():
        payload["surname"] = nou_cognom.strip()
    if nou_dni.strip():
        payload["national_id"] = nou_dni.strip()
    if nou_rol.strip():
        payload["role"] = nou_rol.strip()

    if payload:
        update_resp = client.put(f"/employees/{emp_id}", payload)
        if update_resp.is_success:
            console.print(f"\n[green]✓ Empleat actualitzat correctament![/green]")
        else:
            console.print(f"\n[bold red]Error:[/bold red] {update_resp.error_message}")
    else:
        console.print("[yellow]Sense canvis.[/yellow]")

    console.input("\nPrem Enter per continuar...")


def delete_employee(client: HttpClient):
    """Elimina un empleat."""
    console.print("\n[bold]--- Eliminar Empleat ---[/bold]")
    list_employees(client, pause=False)

    emp_id_str = console.input("Introdueix l'ID de l'empleat a eliminar: ")
    if not emp_id_str.isdigit():
        console.print("[red]L'ID ha de ser un número sencer.[/red]")
        console.input("Prem Enter per continuar...")
        return

    emp_id = int(emp_id_str)
    resp = client.get(f"/employees/{emp_id}")
    if not resp.is_success:
        console.print(f"[red]{resp.error_message}[/red]")
        console.input("Prem Enter per continuar...")
        return

    emp = EmployeeEntity.from_dict(resp.data)
    te_credencials = "i les seves credencials." if emp.has_credentials else ""
    console.print(f"\nEstàs a punt d'eliminar l'empleat [bold red]{emp.name} {emp.surname}[/bold red] {te_credencials}")
    if emp.has_credentials:
        console.print("[yellow]⚠ Les credencials s'eliminaran automàticament (CASCADE definit al servidor).[/yellow]")

    confirmacio = console.input("N'estàs segur? (s/n): ").lower()
    if confirmacio == "s":
        del_resp = client.delete(f"/employees/{emp_id}")
        if del_resp.is_success:
            console.print(f"[green]✓ Empleat '{emp.name} {emp.surname}' eliminat correctament![/green]")
        else:
            console.print(f"[bold red]Error:[/bold red] {del_resp.error_message}")
    else:
        console.print("[yellow]Eliminació cancel·lada.[/yellow]")

    console.input("\nPrem Enter per continuar...")


def search_employees(client: HttpClient):
    """Cerca empleats per nom i/o cognom via query parameters."""
    console.print("\n[bold]--- Cercar Empleats per Nom/Cognom ---[/bold]")
    nom = console.input("Nom (o en blanc per ignorar): ")
    cognom = console.input("Cognom (o en blanc per ignorar): ")

    if not nom.strip() and not cognom.strip():
        console.print("[red]Has d'introduir almenys un criteri de cerca.[/red]")
        console.input("Prem Enter per continuar...")
        return

    query = f"/employees?name={nom.strip()}&surname={cognom.strip()}"
    resp = client.get(query)
    if not resp.is_success:
        console.print(f"[bold red]Error:[/bold red] {resp.error_message}")
    else:
        employees = [EmployeeEntity.from_dict(e) for e in (resp.data or [])]
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

            for emp in employees:
                te_credencials = "[green]✓[/green]" if emp.has_credentials else "[red]✗[/red]"
                table.add_row(
                    str(emp.id),
                    emp.name,
                    emp.surname,
                    emp.national_id,
                    emp.role,
                    te_credencials
                )
            console.print(table)

    console.input("\nPrem Enter per continuar...")


def filter_by_role(client: HttpClient):
    """Filtra empleats segons el rol utilitzant query parameter."""
    console.print("\n[bold]--- Filtrar Empleats per Rol ---[/bold]")
    rol = console.input("Introdueix el rol a filtrar (ex: Cambrer, Cuiner, Encarregat): ")

    if not rol.strip():
        console.print("[red]El rol no pot estar buit.[/red]")
        console.input("Prem Enter per continuar...")
        return

    resp = client.get(f"/employees?role={rol.strip()}")
    if not resp.is_success:
        console.print(f"[bold red]Error:[/bold red] {resp.error_message}")
    else:
        employees = [EmployeeEntity.from_dict(e) for e in (resp.data or [])]
        if not employees:
            console.print(f"[yellow]No s'ha trobat cap empleat amb el rol '{rol}'.[/yellow]")
        else:
            console.print(f"\n[green]{len(employees)} empleat(s) amb rol '{rol}':[/green]")
            table = Table(show_header=True, header_style="bold green")
            table.add_column("ID", style="dim", width=5)
            table.add_column("Nom")
            table.add_column("Cognom")
            table.add_column("DNI")
            table.add_column("Rol")

            for emp in employees:
                table.add_row(str(emp.id), emp.name, emp.surname, emp.national_id, emp.role)
            console.print(table)

    console.input("\nPrem Enter per continuar...")
