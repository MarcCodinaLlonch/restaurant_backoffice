from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box

from src.domain.unit_of_work import UnitOfWorkFactory
from src.domain.models import Menu

console = Console()

def menu_menus(factory: UnitOfWorkFactory):
    while True:
        console.clear()
        console.print(Panel.fit("[bold magenta]Gestió de Menús[/bold magenta]", border_style="magenta", box=box.DOUBLE))
        console.print("1. Llistar tots els menús")
        console.print("2. Afegir nou menú")
        console.print("3. Veure detall d'un menú (N:M amb Plats)")
        console.print("4. Modificar menú")
        console.print("5. Eliminar menú")
        console.print("6. Afegir plat a un menú (N:M)")
        console.print("7. Eliminar plat d'un menú (N:M)")
        console.print("8. Cercar per nom")
        console.print("9. Filtrar per rang de preus")
        console.print("0. Tornar al menú principal")

        opcio = console.input("\n[bold yellow]Selecciona una opció:[/bold yellow] ")

        if opcio == "1":
            list_menus(factory)
        elif opcio == "2":
            add_menu(factory)
        elif opcio == "3":
            view_menu_detail(factory)
        elif opcio == "4":
            update_menu(factory)
        elif opcio == "5":
            delete_menu(factory)
        elif opcio == "6":
            add_dish_to_menu(factory)
        elif opcio == "7":
            remove_dish_from_menu(factory)
        elif opcio == "8":
            search_menu_by_name(factory)
        elif opcio == "9":
            filter_by_price(factory)
        elif opcio == "0":
            break
        else:
            console.print("[red]Opció no vàlida.[/red]")
            console.input("Prem Enter per continuar...")


#Mètode per opció 1. Llista tots els menús mostrant quants plats té cada un (RELACIÓ N:M)
def list_menus(factory: UnitOfWorkFactory):
    console.print("\n[bold]--- Llistat de Menús ---[/bold]")

    with factory.create() as uow:
        menus = uow.menus.get_all()

        if not menus:
            console.print("[yellow]No hi ha cap menú a la base de dades.[/yellow]")
        else:
            table = Table(show_header=True, header_style="bold magenta")
            table.add_column("ID", style="dim", width=5)
            table.add_column("Nom del Menú")
            table.add_column("Preu", justify="right")
            # Columna que demostra la N:M: cada menú pot tenir molts plats
            table.add_column("Núm. Plats (N:M)", justify="center")

            for m in menus:
                table.add_row(
                    str(m.id),
                    m.menu_name,
                    f"{m.price}€",
                    str(len(m.dishes))
                )

            console.print(table)

    console.input("\nPrem Enter per continuar...")


#Mètode per opció 2: Afegir un nou menú sense plats inicialment, s'afegeixen amb opció 6
def add_menu(factory: UnitOfWorkFactory):
    console.print("\n[bold]--- Nou Menú ---[/bold]")

    nom = console.input("Nom del menú: ")
    if not nom.strip():
        console.print("[red]El nom no pot estar buit.[/red]")
        console.input("Prem Enter per continuar...")
        return  

    #validem que el preu sigui un número vàlid
    preu_str = console.input("Preu (ex: 12.50): ")
    try:
        preu = float(preu_str)
        if preu <= 0:
            raise ValueError("El preu ha de ser positiu.")
    except ValueError:
        console.print("[red]El preu ha de ser un número vàlid i positiu.[/red]")
        console.input("Prem Enter per continuar...")
        return

    with factory.create() as uow:
        try:
            nou_menu = Menu(menu_name=nom, price=preu)
            uow.menus.add(nou_menu)
            console.print(f"\n[green]✓ Menú '{nom}' creat amb èxit a {preu}€![/green]")
            console.print("[dim]Ara pots afegir-hi plats des de l'opció 6.[/dim]")
        except Exception as e:
            console.print(f"[bold red]Error:[/bold red] {e}")

    console.input("\nPrem Enter per continuar...")


#Mètode per opció 3: Veure detall d'un menú incloent la llista de plats (RELACIÓ N:M)
def view_menu_detail(factory: UnitOfWorkFactory):
    console.print("\n[bold]--- Detall del Menú ---[/bold]")

    menu_id_str = console.input("Introdueix l'ID del menú: ")
    if not menu_id_str.isdigit():
        console.print("[red]L'ID ha de ser un número sencer.[/red]")
        console.input("Prem Enter per continuar...")
        return

    menu_id = int(menu_id_str)

    with factory.create() as uow:
        m = uow.menus.get(menu_id)

        if not m:
            console.print(f"[red]No s'ha trobat cap menú amb l'ID {menu_id}.[/red]")
        else:
            console.print(Panel.fit(f"[bold magenta]Menú #{m.id}: {m.menu_name} — {m.price}€[/bold magenta]", border_style="magenta"))

            # --- RELACIÓ N:M amb Dish ---
            console.print("\n[bold magenta]Plats d'aquest menú (relació N:M a través de menu_dish):[/bold magenta]")

            if not m.dishes:
                console.print("[yellow]Aquest menú no té cap plat assignat.[/yellow]")
            else:
                dish_table = Table(show_header=True, header_style="bold cyan")
                dish_table.add_column("ID", style="dim", width=5)
                dish_table.add_column("Nom del Plat")
                dish_table.add_column("Categoria")
                dish_table.add_column("Actiu?", justify="center")

                for dish in m.dishes:
                    nom_cat = dish.category.category_name if dish.category else "—" #demostra la relació 1:N entre Dish i Category, un plat pot tenir una categoria o cap
                    actiu   = "[green]✓[/green]" if dish.is_active else "[red]✗[/red]"
                    dish_table.add_row(str(dish.id), dish.dish_name, nom_cat, actiu)

                console.print(dish_table)

    console.input("\nPrem Enter per continuar...")


#Mètode per opció 4: Modificar les dades bàsiques del menú
def update_menu(factory: UnitOfWorkFactory):
    console.print("\n[bold]--- Modificar Menú ---[/bold]")

    #Mostrem llistat de menús per ajudar a l'usuari a triar quin vol modificar
    list_menus(factory)

    menu_id_str = console.input("Introdueix l'ID del menú a modificar: ")
    if not menu_id_str.isdigit():
        console.print("[red]L'ID ha de ser un número sencer.[/red]")
        console.input("Prem Enter per continuar...")
        return

    menu_id = int(menu_id_str)

    with factory.create() as uow:
        m = uow.menus.get(menu_id)

        if not m:
            console.print(f"[red]No s'ha trobat cap menú amb l'ID {menu_id}.[/red]")
        else:
            console.print(f"\nModificant: [magenta]{m.menu_name}[/magenta]")
            console.print("[dim]Deixa en blanc per no canviar el camp.[/dim]\n")

            nou_nom  = console.input(f"Nom [{m.menu_name}]: ")
            nou_preu = console.input(f"Preu [{m.price}]: ")

            if nou_nom.strip():
                m.menu_name = nou_nom

            if nou_preu.strip():
                try:
                    m.price = float(nou_preu)
                except ValueError:
                    console.print("[red]Preu no vàlid, es manté l'anterior.[/red]")

            uow.menus.update(m)
            console.print(f"\n[green]✓ Menú actualitzat correctament![/green]")

    console.input("\nPrem Enter per continuar...")

#Mètode per opció 5: Eliminar un menú
def delete_menu(factory: UnitOfWorkFactory):
    console.print("\n[bold]--- Eliminar Menú ---[/bold]")

    list_menus(factory)

    menu_id_str = console.input("Introdueix l'ID del menú a eliminar: ")
    if not menu_id_str.isdigit():
        console.print("[red]L'ID ha de ser un número sencer.[/red]")
        console.input("Prem Enter per continuar...")
        return

    menu_id = int(menu_id_str)

    with factory.create() as uow:
        m = uow.menus.get(menu_id)

        if not m:
            console.print(f"[red]No s'ha trobat cap menú amb l'ID {menu_id}.[/red]")
        else:
            console.print(f"\nEstàs a punt d'eliminar el menú: [bold red]{m.menu_name}[/bold red]")
            confirmacio = console.input("N'estàs segur? (s/n): ").lower()

            if confirmacio == "s":
                uow.menus.delete(menu_id)
                console.print(f"[green]✓ Menú '{m.menu_name}' eliminat correctament![/green]")
            else:
                console.print("[yellow]Eliminació cancel·lada.[/yellow]")

    console.input("\nPrem Enter per continuar...")


#Mètode per opció 6: Afegir un plat a un menú. Demostra la RELACIÓ N:M a través de menu_dish.
def add_dish_to_menu(factory: UnitOfWorkFactory):
    console.print("\n[bold]--- Afegir Plat a un Menú (N:M) ---[/bold]")

    with factory.create() as uow:
        #Comprova que hi ha menús disponibles per afegir-hi plats
        menus = uow.menus.get_all()
        if not menus:
            console.print("[red]No hi ha cap menú. Crea'n un primer.[/red]")
            console.input("Prem Enter per continuar...")
            return

        # Mostrem els menús disponibles
        m_table = Table(show_header=True, header_style="bold magenta")
        m_table.add_column("ID", style="dim", width=5)
        m_table.add_column("Nom del Menú")
        m_table.add_column("Plats actuals")
        for m in menus:
            noms_plats = ", ".join([d.dish_name for d in m.dishes]) or "—"
            m_table.add_row(str(m.id), m.menu_name, noms_plats)
        console.print(m_table)

        menu_id_str = console.input("\nID del menú al qual vols afegir un plat: ")
        if not menu_id_str.isdigit():
            console.print("[red]L'ID ha de ser un número sencer.[/red]")
            console.input("Prem Enter per continuar...")
            return

        menu_id = int(menu_id_str)
        m = uow.menus.get(menu_id)

        if not m:
            console.print(f"[red]No s'ha trobat cap menú amb l'ID {menu_id}.[/red]")
            console.input("Prem Enter per continuar...")
            return

        # Mostrem els plats actius disponibles per afegir
        dishes = uow.dishes.get_active_dishes()
        if not dishes:
            console.print("[red]No hi ha cap plat actiu. Crea'n un primer des del menú de Plats.[/red]")
            console.input("Prem Enter per continuar...")
            return

        console.print(f"\n[bold]Plats actius disponibles per afegir a '{m.menu_name}':[/bold]")
        d_table = Table(show_header=True, header_style="bold cyan")
        d_table.add_column("ID", style="dim", width=5)
        d_table.add_column("Nom del Plat")
        d_table.add_column("Categoria")
        for d in dishes:
            nom_cat = d.category.category_name if d.category else "—"
            d_table.add_row(str(d.id), d.dish_name, nom_cat)
        console.print(d_table)

        dish_id_str = console.input("\nID del plat a afegir: ")
        if not dish_id_str.isdigit():
            console.print("[red]L'ID ha de ser un número sencer.[/red]")
            console.input("Prem Enter per continuar...")
            return

        dish_id = int(dish_id_str)
        dish = uow.dishes.get(dish_id)

        if not dish:
            console.print(f"[red]No s'ha trobat cap plat amb l'ID {dish_id}.[/red]")
        else:
            # add_dish_to_menu() del repositori gestiona la taula intermèdia menu_dish
            # SQLAlchemy insereix la fila a menu_dish automàticament
            uow.menus.add_dish_to_menu(menu_id, dish)
            console.print(f"\n[green]✓ Plat '{dish.dish_name}' afegit al menú '{m.menu_name}'![/green]")
            console.print("[dim](<SQLAlchemy ha inserit automàticament la fila a la taula intermèdia menu_dish>)[/dim]")

    console.input("\nPrem Enter per continuar...")


#Mètode per opció 7: Eliminar un plat d'un menú (gestió inversa de la N:M)
def remove_dish_from_menu(factory: UnitOfWorkFactory):
    console.print("\n[bold]--- Eliminar Plat d'un Menú (N:M) ---[/bold]")

    menu_id_str = console.input("Introdueix l'ID del menú: ")
    if not menu_id_str.isdigit():
        console.print("[red]L'ID ha de ser un número sencer.[/red]")
        console.input("Prem Enter per continuar...")
        return

    menu_id = int(menu_id_str)

    with factory.create() as uow:
        m = uow.menus.get(menu_id)

        #si el menu no existeix o no té plats, mostrem missatge i no deixem triar plat a eliminar
        if not m:
            console.print(f"[red]No s'ha trobat cap menú amb l'ID {menu_id}.[/red]")
        elif not m.dishes:
            console.print(f"[yellow]El menú '{m.menu_name}' no té cap plat assignat.[/yellow]")
        else:
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
            dish = uow.dishes.get(dish_id)

            if not dish:
                console.print(f"[red]No s'ha trobat cap plat amb l'ID {dish_id}.[/red]")
            else:
                # remove_dish_from_menu() elimina la fila de menu_dish automàticament
                resultat = uow.menus.remove_dish_from_menu(menu_id, dish)
                if resultat:
                    console.print(f"[green]✓ Plat '{dish.dish_name}' eliminat del menú '{m.menu_name}'![/green]")
                else:
                    console.print(f"[yellow]El plat '{dish.dish_name}' no estava en aquest menú.[/yellow]")

    console.input("\nPrem Enter per continuar...")


#Mètode per opció 8: Cerca de menús per nom parcial
def search_menu_by_name(factory: UnitOfWorkFactory):
    console.print("\n[bold]--- Cercar Menú per Nom ---[/bold]")
    nom = console.input("Introdueix el nom o part del nom a cercar: ")

    if not nom.strip():
        console.print("[red]Has d'introduir algun text per cercar.[/red]")
        console.input("Prem Enter per continuar...")
        return

    with factory.create() as uow:
        resultats = uow.menus.get_by_name(nom)

        if not resultats:
            console.print(f"[yellow]No s'ha trobat cap menú que contingui '{nom}'.[/yellow]")
        else:
            console.print(f"\n[green]{len(resultats)} resultat(s) trobat(s):[/green]")
            table = Table(show_header=True, header_style="bold magenta")
            table.add_column("ID", style="dim", width=5)
            table.add_column("Nom del Menú")
            table.add_column("Preu", justify="right")
            table.add_column("Núm. Plats", justify="center")
            for m in resultats:
                table.add_row(str(m.id), m.menu_name, f"{m.price}€", str(len(m.dishes)))
            console.print(table)

    console.input("\nPrem Enter per continuar...")


#Mètode per opció 9: Filtrar menús per rang de preus
def filter_by_price(factory: UnitOfWorkFactory):
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

    with factory.create() as uow:
        resultats = uow.menus.get_by_price_range(preu_min, preu_max)

        if not resultats:
            console.print(f"[yellow]No hi ha cap menú entre {preu_min}€ i {preu_max}€.[/yellow]")
        else:
            console.print(f"\n[green]{len(resultats)} menú(s) trobat(s) entre {preu_min}€ i {preu_max}€:[/green]")
            table = Table(show_header=True, header_style="bold magenta")
            table.add_column("ID", style="dim", width=5)
            table.add_column("Nom del Menú")
            table.add_column("Preu", justify="right")
            for m in resultats:
                table.add_row(str(m.id), m.menu_name, f"{m.price}€")
            console.print(table)

    console.input("\nPrem Enter per continuar...")