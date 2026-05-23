from datetime import date
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box
from sqlalchemy.exc import IntegrityError

from src.domain.unit_of_work import UnitOfWorkFactory
from src.domain.models import Sale

console = Console()


def menu_sales(factory: UnitOfWorkFactory):
    while True:
        console.clear()
        console.print() # Fix pel PowerShell del VS Code que talla la part superior
        console.print(Panel.fit("[bold red]Gestió de Vendes[/bold red]", border_style="red", box=box.DOUBLE))
        console.print("1. Llistar totes les vendes")
        console.print("2. Registrar nova venda") #(N:M amb atributs)
        console.print("3. Eliminar venda")
        console.print("4. Cercar vendes per data")
        console.print("5. Cercar vendes per empleat")
        console.print("6. Cercar vendes per menú")
        console.print("7. Cercar vendes per rang de dates")
        console.print("8. Modificar venda (quantitat)")
        console.print("0. Tornar al menú principal")

        opcio = console.input("\n[bold yellow]Selecciona una opció:[/bold yellow] ")

        if opcio == "1":
            list_sales(factory)
        elif opcio == "2":
            add_sale(factory)
        elif opcio == "3":
            delete_sale(factory)
        elif opcio == "4":
            search_by_date(factory)
        elif opcio == "5":
            search_by_employee(factory)
        elif opcio == "6":
            search_by_menu(factory)
        elif opcio == "7":
            search_by_date_range(factory)
        elif opcio == "8":
            update_sale(factory)
        elif opcio == "0":
            break
        else:
            console.print("[red]Opció no vàlida.[/red]")
            console.input("Prem Enter per continuar...")


#Mètode auxiliar per pintar una taula de vendes que reutilitzem en totes les cerques dins del menú de vendes
# Aquest mètode te una barra baixa al principi del nom perquè és un mètode "privat", 
# només per ús intern dins d'aquest fitxer, no s'ha d'importar ni usar des d'altres fitxers.
def _print_sales_table(sales):
    if not sales:
        console.print("[yellow]No s'han trobat vendes.[/yellow]")
        return

    table = Table(show_header=True, header_style="bold red")
    table.add_column("ID Menú", style="dim", width=7)
    table.add_column("Menú", style="magenta")
    table.add_column("ID Empleat", style="dim", width=10)
    table.add_column("Empleat")
    table.add_column("Data")
    #Columna de l'ATRIBUT EXTRA que fa que sigui N:M amb atributs (no simple)
    table.add_column("Quantitat", justify="center")

    for sale in sales:
        #Naveguem les relacions per mostrar noms en lloc d'IDs
        nom_menu = sale.menu.menu_name if sale.menu else str(sale.id_menu) #Si no troba el menú (per algun error), mostra l'ID en lloc del nom
        nom_empleat = f"{sale.employee.name} {sale.employee.surname}" if sale.employee else str(sale.id_employee) #Si no troba l'empleat, mostra l'ID en lloc del nom
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


#Mètode opció 1. Llista totes les vendes paginades
def list_sales(factory: UnitOfWorkFactory, pause: bool = True):
    console.print("\n[bold]--- Llistat de Vendes ---[/bold]")

    with factory.create() as uow:
        #Fem servir paginació per no carregar totes les vendes de cop
        sales = uow.sales.get_paginated(page=1, page_size=20)
        _print_sales_table(sales)

    if pause:
        console.input("\nPrem Enter per continuar...")


#Mètode opció 2. Registrar nova venda. Demostra la relació N:M amb atributs.
# La venda és l'associació entre un Menú i un Empleat, amb data i quantitat com a atributs.
def add_sale(factory: UnitOfWorkFactory):
    console.print("\n[bold]--- Nova Venda (N:M amb atributs) ---[/bold]")

    creada = False

    try:
        with factory.create() as uow:
            #Buscar els menús i empleats disponibles per mostrar-los i seleccionar-los. Això demostra la N:M entre Menu i Employee.
            menus = uow.menus.get_all()
            if not menus:
                console.print("[red]No hi ha cap menú. Crea'n un primer.[/red]")
                console.input("Prem Enter per continuar...")
                return

            console.print("\n[bold]Menús disponibles:[/bold]")
            m_table = Table(show_header=True, header_style="bold magenta")
            m_table.add_column("ID", style="dim", width=5)
            m_table.add_column("Nom")
            m_table.add_column("Preu", justify="right")
            for m in menus:
                m_table.add_row(str(m.id), m.menu_name, f"{m.price}€")
            console.print(m_table)

            #Seleccionar el menú, demanant l'ID i validant que sigui un número. 
            # No validem que l'ID existeixi perquè després quan intentem crear la venda, si el menú no existeix, 
            # saltarà un error que atraparem i mostrarem.
            menu_id_str = console.input("\nID del menú venut: ")
            if not menu_id_str.isdigit():
                console.print("[red]L'ID ha de ser un número.[/red]")
                console.input("Prem Enter per continuar...")
                return
            menu_id = int(menu_id_str)

            #Buscar els empleats disponibles per mostrar-los i seleccionar-los. Això demostra la N:M entre Menu i Employee.
            employees = uow.employees.get_all()
            if not employees:
                console.print("[red]No hi ha cap empleat. Crea'n un primer.[/red]")
                console.input("Prem Enter per continuar...")
                return

            console.print("\n[bold]Empleats disponibles:[/bold]")
            e_table = Table(show_header=True, header_style="bold green")
            e_table.add_column("ID", style="dim", width=5)
            e_table.add_column("Nom")
            e_table.add_column("Rol")
            for emp in employees:
                e_table.add_row(str(emp.id), f"{emp.name} {emp.surname}", emp.role)
            console.print(e_table)

            #Seleccionar l'empleat, demanant l'ID i validant que sigui un número.
            emp_id_str = console.input("\nID de l'empleat que fa la venda: ")
            if not emp_id_str.isdigit():
                console.print("[red]L'ID ha de ser un número.[/red]")
                console.input("Prem Enter per continuar...")
                return
            emp_id = int(emp_id_str)

            #Introduir atributs de la relació, el que la fa N:M amb atributs.
            # Data: La data de la venda per defecte és avui, però es pot introduir una data concreta. Validem el format de la data.
            data_str = console.input("\nData de la venda (YYYY-MM-DD) [Enter per avui]: ")
            if not data_str.strip():
                data_venda = date.today()
            else:
                try:
                    data_venda = date.fromisoformat(data_str)
                except ValueError:
                    console.print("[red]Format de data incorrecte. Usa YYYY-MM-DD.[/red]")
                    console.input("Prem Enter per continuar...")
                    return

            # Quantitat: La quantitat venuda, per defecte 1, però es pot introduir qualsevol quantitat. Validem que sigui un número positiu.
            quantitat_str = console.input("Quantitat venuda [1]: ")
            if not quantitat_str.strip():
                quantitat = 1
            elif quantitat_str.isdigit() and int(quantitat_str) > 0:
                quantitat = int(quantitat_str)
            else:
                console.print("[red]La quantitat ha de ser un número positiu.[/red]")
                console.input("Prem Enter per continuar...")
                return

            # Creem objecte Sale: és la taula d'associació N:M amb els seus atributs extra
            try:
                nova_venda = Sale(
                    id_menu=menu_id,
                    id_employee=emp_id,
                    sale_date=data_venda,
                    quantity_sold=quantitat
                )
                uow.sales.add(nova_venda)
                creada = True
            except Exception as e:
                console.print(f"[bold red]Error:[/bold red] {e}")

    except IntegrityError:
        console.print("\n[bold red]Error:[/bold red] Ja existeix una venda per aquest menú, empleat i data. La combinació ha de ser única.")

    if creada:
        console.print(f"\n[green]✓ Venda registrada correctament![/green]")
        console.print(f"[dim]Menú ID {menu_id} | Empleat ID {emp_id} | Data: {data_venda} | Quantitat: {quantitat}[/dim]")

    console.input("\nPrem Enter per continuar...")


#Mètode opció 3. Eliminar una venda, fa falta passar la PK composta -> menu+empleat+data
def delete_sale(factory: UnitOfWorkFactory):
    console.print("\n[bold]--- Eliminar Venda ---[/bold]")
    console.print("[dim]La venda s'identifica per la combinació de Menú + Empleat + Data[/dim]\n")
    list_sales(factory, pause=False)

    from src.ui.menu_ui import list_menus
    from src.ui.employee_ui import list_employees

    list_menus(factory, pause=False)
    menu_id_str = console.input("\nID del menú: ")
    
    list_employees(factory, pause=False)
    emp_id_str  = console.input("\nID de l'empleat: ")
    
    data_str    = console.input("\nData (YYYY-MM-DD): ")

    if not menu_id_str.isdigit() or not emp_id_str.isdigit():
        console.print("[red]Els IDs han de ser números.[/red]")
        console.input("Prem Enter per continuar...")
        return

    #Validem format de data i convertim a date. Si el format és incorrecte, mostrem un error i tornemem al menú.
    try:
        data_venda = date.fromisoformat(data_str)
    except ValueError:
        console.print("[red]Format de data incorrecte. Usa YYYY-MM-DD.[/red]")
        console.input("Prem Enter per continuar...")
        return

    # La PK de Sale és una TUPLA: (id_menu, id_employee, sale_date)
    pk = (int(menu_id_str), int(emp_id_str), data_venda)

    with factory.create() as uow:
        venda = uow.sales.get(pk)

        if not venda:
            console.print(f"[red]No s'ha trobat cap venda amb aquesta combinació.[/red]")
        else:
            console.print(f"\nVenda trobada: Menú '{venda.menu.menu_name}' | Empleat '{venda.employee.name}' | {venda.sale_date} | Quantitat: {venda.quantity_sold}")
            confirmacio = console.input("Eliminar? (s/n): ").lower()
            if confirmacio == "s":
                uow.sales.delete(pk)
                console.print("[green]✓ Venda eliminada correctament![/green]")
            else:
                console.print("[yellow]Operació cancel·lada.[/yellow]")

    console.input("\nPrem Enter per continuar...")


#Mètodes opcions 4-7: Cerques personalitzades del SaleRepository
#Mètode per cercar vendes per data concreta
def search_by_date(factory: UnitOfWorkFactory):
    console.print("\n[bold]--- Vendes per Data ---[/bold]")
    data_str = console.input("Data (YYYY-MM-DD): ")
    try:
        data = date.fromisoformat(data_str)
    except ValueError:
        console.print("[red]Format incorrecte. Usa YYYY-MM-DD.[/red]")
        console.input("Prem Enter per continuar...")
        return

    with factory.create() as uow:
        sales = uow.sales.get_sales_by_date(data)
        console.print(f"\n[bold]Vendes del {data}:[/bold]")
        _print_sales_table(sales) #Reutilitzem mètode auxiliar per mostrar les vendes en taula

    console.input("\nPrem Enter per continuar...")

#Mètode per cercar vendes per empleat, demanant l'ID de l'empleat i validant que sigui un número.
def search_by_employee(factory: UnitOfWorkFactory):
    console.print("\n[bold]--- Vendes per Empleat ---[/bold]")

    with factory.create() as uow:
        employees = uow.employees.get_all()
        e_table = Table(show_header=True, header_style="bold green")
        e_table.add_column("ID", style="dim", width=5)
        e_table.add_column("Nom")
        for emp in employees:
            e_table.add_row(str(emp.id), f"{emp.name} {emp.surname}")
        console.print(e_table)

        emp_id_str = console.input("\nID de l'empleat: ")
        if not emp_id_str.isdigit():
            console.print("[red]L'ID ha de ser un número.[/red]")
            console.input("Prem Enter per continuar...")
            return

        sales = uow.sales.get_sales_by_employee(int(emp_id_str))
        console.print(f"\n[bold]Vendes de l'empleat ID {emp_id_str}:[/bold]")
        _print_sales_table(sales)

    console.input("\nPrem Enter per continuar...")

#Mètode per cercar vendes per menú, demanant l'ID del menú i validant que sigui un número.
def search_by_menu(factory: UnitOfWorkFactory):
    console.print("\n[bold]--- Vendes per Menú ---[/bold]")

    with factory.create() as uow:
        menus = uow.menus.get_all()
        m_table = Table(show_header=True, header_style="bold magenta")
        m_table.add_column("ID", style="dim", width=5)
        m_table.add_column("Nom")
        for m in menus:
            m_table.add_row(str(m.id), m.menu_name)
        console.print(m_table)

        menu_id_str = console.input("\nID del menú: ")
        if not menu_id_str.isdigit():
            console.print("[red]L'ID ha de ser un número.[/red]")
            console.input("Prem Enter per continuar...")
            return

        sales = uow.sales.get_sales_by_menu(int(menu_id_str))
        console.print(f"\n[bold]Vendes del menú ID {menu_id_str}:[/bold]")
        _print_sales_table(sales)

    console.input("\nPrem Enter per continuar...")

#Mètode per cercar vendes per rang de dates, demanant data d'inici i data de fi, 
# validant format de data i que la data d'inici no sigui posterior a la de fi.
def search_by_date_range(factory: UnitOfWorkFactory):
    console.print("\n[bold]--- Vendes per Rang de Dates ---[/bold]")

    try:
        data_ini = date.fromisoformat(console.input("Data inici (YYYY-MM-DD): "))
        data_fi  = date.fromisoformat(console.input("Data fi    (YYYY-MM-DD): "))
    except ValueError:
        console.print("[red]Format incorrecte. Usa YYYY-MM-DD.[/red]")
        console.input("Prem Enter per continuar...")
        return

    if data_ini > data_fi:
        console.print("[red]La data d'inici no pot ser posterior a la de fi.[/red]")
        console.input("Prem Enter per continuar...")
        return

    with factory.create() as uow:
        sales = uow.sales.get_sales_by_date_range(data_ini, data_fi)
        console.print(f"\n[bold]Vendes del {data_ini} al {data_fi}:[/bold]")
        _print_sales_table(sales)

    console.input("\nPrem Enter per continuar...")

#Mètode opció 8: Modificar una venda (només l'atribut extra: quantity_sold)
def update_sale(factory: UnitOfWorkFactory):
    console.print("\n[bold]--- Modificar Venda ---[/bold]")
    console.print("[dim]Només es pot modificar la quantitat d'una venda ja existent.[/dim]\n")
    list_sales(factory, pause=False)

    from src.ui.menu_ui import list_menus
    from src.ui.employee_ui import list_employees

    list_menus(factory, pause=False)
    menu_id_str = console.input("\nID del menú: ")

    list_employees(factory, pause=False)
    emp_id_str  = console.input("\nID de l'empleat: ")

    data_str    = console.input("\nData (YYYY-MM-DD): ")

    if not menu_id_str.isdigit() or not emp_id_str.isdigit():
        console.print("[red]Els IDs han de ser números.[/red]")
        console.input("Prem Enter per continuar...")
        return

    try:
        data_venda = date.fromisoformat(data_str)
    except ValueError:
        console.print("[red]Format de data incorrecte. Usa YYYY-MM-DD.[/red]")
        console.input("Prem Enter per continuar...")
        return

    #tupla amb la PK composta per recuperar la venda que volem modificar
    pk = (int(menu_id_str), int(emp_id_str), data_venda)

    with factory.create() as uow:
        venda = uow.sales.get(pk)

        if not venda:
            console.print(f"[red]No s'ha trobat cap venda amb aquesta combinació.[/red]")
        else:
            console.print(f"\nVenda trobada: Menú '{venda.menu.menu_name}' | Empleat '{venda.employee.name}' | {venda.sale_date}")
            console.print(f"Quantitat actual: [cyan]{venda.quantity_sold}[/cyan]")
            
            nova_quantitat_str = console.input("Nova quantitat (deixa en blanc per cancel·lar): ")
            
            if nova_quantitat_str.strip():
                #Amb isdigit() validem que sigui un número i amb int(nova_quantitat_str) > 0 validem que sigui positiu. 
                # Si no és un número positiu, mostrem un error.
                if nova_quantitat_str.isdigit() and int(nova_quantitat_str) > 0:
                    venda.quantity_sold = int(nova_quantitat_str)
                    uow.sales.update(venda)
                    console.print("[green]✓ Quantitat actualitzada correctament![/green]")
                else:
                    console.print("[red]La quantitat ha de ser un número positiu.[/red]")
            else:
                console.print("[yellow]Operació cancel·lada.[/yellow]")

    console.input("\nPrem Enter per continuar...")