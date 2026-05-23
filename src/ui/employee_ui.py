from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box
from sqlalchemy.exc import IntegrityError

from src.domain.unit_of_work import UnitOfWorkFactory
from src.domain.models import Employee, AppCredential

import hashlib  #Aquest mòdul ens permet fer hash de contrasenyes per guardar-les de forma segura a la base de dades.

console = Console()

def menu_employees(factory: UnitOfWorkFactory):
    while True:
        console.clear()
        console.print() # Fix pel PowerShell del VS Code que talla la part superior
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
            list_employees(factory)
        elif opcio == "2":
            add_employee(factory)
        elif opcio == "3":
            view_employee_detail(factory)
        elif opcio == "4":
            update_employee(factory)
        elif opcio == "5":
            delete_employee(factory)
        elif opcio == "6":
            search_employees(factory)
        elif opcio == "7":
            filter_by_role(factory)
        elif opcio == "0":
            break
        else:
            console.print("[red]Opció no vàlida.[/red]")
            console.input("Prem Enter per continuar...")

#Mètode per opció 1. Llistar empleats (indicant de si tenen credencials o no) -> Relació 1:1 amb AppCredential
def list_employees(factory: UnitOfWorkFactory, pause: bool = True):
    console.print("\n[bold]--- Llistat d'Empleats ---[/bold]")

    with factory.create() as uow:
        employees = uow.employees.get_all()

        if not employees:
            console.print("[yellow]No hi ha cap empleat a la base de dades.[/yellow]")
        else:
            table = Table(show_header=True, header_style="bold green")
            table.add_column("ID", style="dim", width=5)
            table.add_column("Nom")
            table.add_column("Cognom")
            table.add_column("DNI")
            table.add_column("Rol")
            #Columna especial que permet veure la relació 1:1 amb AppCredential
            table.add_column("Credencials?", justify="center")

            for emp in employees:
                #Si l'empleat té credencials (relació 1:1), mostrem ✓ en verd, si no ✗ en vermell
                te_credencials = "[green]✓[/green]" if emp.credentials else "[red]✗[/red]"
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

#Mètode per opció 2. Afegir empleat (amb opció d'afegir credencials a l'app, relació 1:1)
#Si es creen les credencials, s'han de guardar en la mateixa transacció que l'empleat garantint integritat de les dades.
#Si no es creen les credencials, l'empleat es crea igualment.
def add_employee(factory: UnitOfWorkFactory):
    console.print("\n[bold]--- Nou Empleat ---[/bold]")

    nom = console.input("Nom: ")
    cognom = console.input("Cognom: ")
    dni = console.input("DNI/NIE: ")
    rol = console.input("Rol (ex: Cambrer, Cuiner, Encarregat): ")

    if not all([nom.strip(), cognom.strip(), dni.strip(), rol.strip()]):
        console.print("[red]Tots els camps són obligatoris.[/red]")
        console.input("Prem Enter per continuar...")
        return

    # Flag per saber si la transacció ha anat bé i mostrar el missatge d'èxit
    # fora del bloc 'with', quan el commit ja s'ha executat sense errors.
    creat = False

    try:
        with factory.create() as uow:
            try:
                #1.Creem l'empleat
                nou_empleat = Employee(
                    name=nom,
                    surname=cognom,
                    national_id=dni,
                    role=rol
                )
                uow.employees.add(nou_empleat)

                #2.Preguntem si vol afegir credencials d'accés (RELACIÓ 1:1)
                console.print("\n[cyan]Vols afegir credencials d'accés a l'app per aquest empleat?[/cyan]")
                vol_credencials = console.input("(s/n): ").lower()

                if vol_credencials == "s":
                    email = console.input("Email: ")
                    password = console.input("Contrasenya: ")

                    if not email.strip() or not password.strip():
                        console.print("[red]Email i contrasenya no poden estar buits. Es crearà l'empleat sense credencials.[/red]")
                    else:
                        #Fem un hash SHA256 de la contrasenya. Mai guardem contrasenyes en text pla!
                        password_hash = hashlib.sha256(password.encode()).hexdigest()

                        #Creem les credencials i les assignem directament a l'empleat.
                        #SQLAlchemy s'encarrega de posar l'id_employee automàticament per la relació 1:1.
                        nou_empleat.credentials = AppCredential(
                            email=email,
                            password_hash=password_hash
                        )

                # Marquem que tot ha anat bé dins del bloc Python.
                # El commit real passa al __exit__ del UoW en sortir del 'with'.
                creat = True

            except ValueError as e:
                # Captura errors de validació del repositori (ex: DNI duplicat)
                console.print(f"\n[bold red]Error:[/bold red] {e}")

    except IntegrityError:
        # Captura errors de la BD que arriben al commit (ex: email ja existent a app_credential)
        console.print("\n[bold red]Error:[/bold red] Ja existeix un compte amb aquest email. Prova amb un altre email.")

    # El missatge d'èxit es mostra AQUÍ, fora del 'with', quan el commit
    # ja s'ha executat correctament i no hi ha hagut cap IntegrityError.
    if creat:
        console.print(f"\n[green]✓ Empleat '{nom} {cognom}' creat amb èxit![/green]")

    console.input("\nPrem Enter per continuar...")

#Mètode per opció 3. Veure detall d'un empleat (inclou credencials d'accés si les té, relació 1:1)
def view_employee_detail(factory: UnitOfWorkFactory):
    console.print("\n[bold]--- Detall d'Empleat ---[/bold]")

    #Validem que l'ID sigui un número enter abans de fer consulta a la bd's
    emp_id_str = console.input("Introdueix l'ID de l'empleat: ")
    if not emp_id_str.isdigit():
        console.print("[red]L'ID ha de ser un número sencer.[/red]")
        console.input("Prem Enter per continuar...")
        return

    emp_id = int(emp_id_str)

    with factory.create() as uow:
        emp = uow.employees.get(emp_id)

        if not emp:
            console.print(f"[red]No s'ha trobat cap empleat amb l'ID {emp_id}.[/red]")
        else:
            # Taula amb les dades bàsiques de l'empleat
            console.print(Panel.fit(f"[bold green]Empleat #{emp.id}[/bold green]", border_style="green"))

            table = Table(show_header=False, box=None)
            table.add_column("Camp", style="bold cyan", width=15)
            table.add_column("Valor")

            table.add_row("Nom",    emp.name)
            table.add_row("Cognom", emp.surname)
            table.add_row("DNI",    emp.national_id)
            table.add_row("Rol",    emp.role)

            console.print(table)

            # --- RELACIÓ 1:1 amb AppCredential ---
            console.print("\n[bold cyan]Credencials d'accés (relació 1:1):[/bold cyan]")

            if emp.credentials:
                cred_table = Table(show_header=False, box=None)
                cred_table.add_column("Camp", style="bold", width=15)
                cred_table.add_column("Valor")
                cred_table.add_row("Email",    emp.credentials.email)
                #Mai mostrem el hash de la contrasenya per seguretat, només indiquem que existeix un hash
                cred_table.add_row("Password", "[dim]*** (hash SHA256) ***[/dim]")
                console.print(cred_table)
            else:
                console.print("[yellow]Aquest empleat no té credencials d'accés assignades.[/yellow]")

    console.input("\nPrem Enter per continuar...")

#Mètode per opció 4. Modificar empleat (inclou modificar credencials d'accés si les té, relació 1:1)
def update_employee(factory: UnitOfWorkFactory):
    console.print("\n[bold]--- Modificar Empleat ---[/bold]")

    #Llistem empleats perquè l'usuari sàpiga quins IDs existeixen
    list_employees(factory, pause=False)

    #Validem que ID sigui un número enter abans de fer consulta a la bd's
    emp_id_str = console.input("Introdueix l'ID de l'empleat a modificar: ")
    if not emp_id_str.isdigit():
        console.print("[red]L'ID ha de ser un número sencer.[/red]")
        console.input("Prem Enter per continuar...")
        return

    emp_id = int(emp_id_str)

    with factory.create() as uow:
        emp = uow.employees.get(emp_id)

        if not emp:
            console.print(f"[red]No s'ha trobat cap empleat amb l'ID {emp_id}.[/red]")
        else:
            console.print(f"\nModificant: [cyan]{emp.name} {emp.surname}[/cyan]")
            console.print("[dim]Deixa en blanc per no canviar el camp.[/dim]\n") #Explicació per a usuari, si deixa el camp en blanc no es modificarà

            nou_nom    = console.input(f"Nom [{emp.name}]: ")
            nou_cognom = console.input(f"Cognom [{emp.surname}]: ")
            nou_dni    = console.input(f"DNI [{emp.national_id}]: ")
            nou_rol    = console.input(f"Rol [{emp.role}]: ")

            #Només actualitzem els camps que usuari ha omplert (no buits)
            if nou_nom.strip():    emp.name        = nou_nom
            if nou_cognom.strip(): emp.surname     = nou_cognom
            if nou_dni.strip():    emp.national_id = nou_dni
            if nou_rol.strip():    emp.role        = nou_rol

            #Actualitzem les credencials si existeixen
            uow.employees.update(emp)
            console.print(f"\n[green]✓ Empleat actualitzat correctament![/green]")

    console.input("\nPrem Enter per continuar...")

#Mètode per opció 5. Eliminar empleat (inclou eliminar credencials si les té, relació 1:1 amb cascade)
def delete_employee(factory: UnitOfWorkFactory):
    console.print("\n[bold]--- Eliminar Empleat ---[/bold]")

    #Llistem empleats perquè l'usuari sàpiga quines ID existeixen
    list_employees(factory, pause=False)

    #Validem que ID sigui un número enter abans de fer consulta a la bd's
    emp_id_str = console.input("Introdueix l'ID de l'empleat a eliminar: ")
    if not emp_id_str.isdigit():
        console.print("[red]L'ID ha de ser un número sencer.[/red]")
        console.input("Prem Enter per continuar...")
        return

    emp_id = int(emp_id_str)

    with factory.create() as uow:
        emp = uow.employees.get(emp_id)

        if not emp:
            console.print(f"[red]No s'ha trobat cap empleat amb l'ID {emp_id}.[/red]")
        else:
            #si l'empleat té credencials, ho indiquem a missatge de confirmació.
            te_credencials = "i les seves credencials." if emp.credentials else ""
            
            console.print(f"\nEstàs a punt d'eliminar l'empleat [bold red]{emp.name} {emp.surname}[/bold red] {te_credencials}")
            
            #Recordatori d'eliminació en cascada 
            # si l'empleat té credencials, s'eliminaran automàticament.
            if emp.credentials:
                console.print("[yellow]⚠ Les credencials s'eliminaran automàticament (CASCADE definit al model).[/yellow]")

            confirmacio = console.input("N'estàs segur? (s/n): ").lower()

            if confirmacio == "s":
                uow.employees.delete(emp_id)
                console.print(f"[green]✓ Empleat '{emp.name} {emp.surname}' eliminat correctament![/green]")
            else:
                console.print("[yellow]Eliminació cancel·lada.[/yellow]")

    console.input("\nPrem Enter per continuar...")

#Mètode per opció 6. Cerca empleats per nom i/o cognom
#Fa servir mètode get_by_name() del repositori.
def search_employees(factory: UnitOfWorkFactory):
    console.print("\n[bold]--- Cercar Empleats per Nom/Cognom ---[/bold]")
    console.print("[dim]Pots cercar per nom, per cognom, o per tots dos alhora. Deixa en blanc per ignorar el camp.[/dim]\n")

    nom = console.input("Nom (o en blanc per ignorar): ")
    cognom = console.input("Cognom (o en blanc per ignorar): ")

    if not nom.strip() and not cognom.strip():
        console.print("[red]Has d'introduir almenys un criteri de cerca.[/red]")
        console.input("Prem Enter per continuar...")
        return

    with factory.create() as uow:
        #get_by_name() accepta nom i cognom com a paràmetres opcionals
        resultats = uow.employees.get_by_name(name=nom, surname=cognom)

        if not resultats:
            console.print("[yellow]No s'ha trobat cap empleat amb aquests criteris.[/yellow]")
        else:
            console.print(f"\n[green]{len(resultats)} resultat(s) trobat(s):[/green]")

            table = Table(show_header=True, header_style="bold green")
            table.add_column("ID", style="dim", width=5)
            table.add_column("Nom")
            table.add_column("Cognom")
            table.add_column("DNI")
            table.add_column("Rol")
            table.add_column("Credencials?", justify="center")

            for emp in resultats:
                #Si te credencials mostrem ok en verd, si no en vermell
                te_credencials = "[green]✓[/green]" if emp.credentials else "[red]✗[/red]"
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


#Mètode per opció 7. Filtra empleats per rol
#Fa servir mètode get_by_role() del repositori.
def filter_by_role(factory: UnitOfWorkFactory):
    console.print("\n[bold]--- Filtrar Empleats per Rol ---[/bold]")
    rol = console.input("Introdueix el rol a filtrar (ex: Cambrer, Cuiner, Encarregat): ")

    if not rol.strip():
        console.print("[red]El rol no pot estar buit.[/red]")
        console.input("Prem Enter per continuar...")
        return

    with factory.create() as uow:
        resultats = uow.employees.get_by_role(rol)

        if not resultats:
            console.print(f"[yellow]No s'ha trobat cap empleat amb el rol '{rol}'.[/yellow]")
        else:
            console.print(f"\n[green]{len(resultats)} empleat(s) amb rol '{rol}':[/green]")

            table = Table(show_header=True, header_style="bold green")
            table.add_column("ID", style="dim", width=5)
            table.add_column("Nom")
            table.add_column("Cognom")
            table.add_column("DNI")
            table.add_column("Rol")

            for emp in resultats:
                table.add_row(
                    str(emp.id),
                    emp.name,
                    emp.surname,
                    emp.national_id,
                    emp.role,
                )

            console.print(table)

    console.input("\nPrem Enter per continuar...")