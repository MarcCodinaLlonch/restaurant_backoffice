from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box

from src.domain.unit_of_work import UnitOfWorkFactory
from src.domain.models import Dish

console = Console()


def menu_dishes(factory: UnitOfWorkFactory):
    while True:
        console.clear()
        console.print() # Fix pel PowerShell del VS Code que talla la part superior
        console.print(Panel.fit("[bold cyan]Gestió de Plats[/bold cyan]", border_style="cyan", box=box.DOUBLE))
        console.print("1. Llistar tots els plats")
        console.print("2. Afegir nou plat") #(1:N amb Categoria)
        console.print("3. Veure detall d'un plat") #(N:M amb Al·lèrgens)
        console.print("4. Modificar plat")
        console.print("5. Eliminar plat")
        console.print("6. Afegir al·lèrgen a un plat (N:M)")
        console.print("7. Filtrar plats actius")
        console.print("8. Cercar plat per nom")
        console.print("0. Tornar al menú principal")

        opcio = console.input("\n[bold yellow]Selecciona una opció:[/bold yellow] ")

        if opcio == "1":
            list_dishes(factory)
        elif opcio == "2":
            add_dish(factory)
        elif opcio == "3":
            view_dish_detail(factory)
        elif opcio == "4":
            update_dish(factory)
        elif opcio == "5":
            delete_dish(factory)
        elif opcio == "6":
            add_allergen_to_dish(factory)
        elif opcio == "7":
            list_active_dishes(factory)
        elif opcio == "8":
            search_dish_by_name(factory)
        elif opcio == "0":
            break
        else:
            console.print("[red]Opció no vàlida.[/red]")
            console.input("Prem Enter per continuar...")


# Opció 1: Llista tots els plats mostrant la seva categoria (RELACIÓ 1:N)
def list_dishes(factory: UnitOfWorkFactory, pause: bool = True):
    console.print("\n[bold]--- Llistat de Plats ---[/bold]")

    with factory.create() as uow:
        dishes = uow.dishes.get_all()

        if not dishes:
            console.print("[yellow]No hi ha cap plat a la base de dades.[/yellow]")
        else:
            table = Table(show_header=True, header_style="bold cyan")
            table.add_column("ID", style="dim", width=5)
            table.add_column("Nom del Plat")
            # Columna que demostra la RELACIÓ 1:N: cada plat pertany a UNA categoria
            table.add_column("Categoria (1:N)")
            table.add_column("Actiu?", justify="center")
            table.add_column("Núm. Al·lèrgens", justify="center")

            for dish in dishes:
                # Accedim a dish.category.category_name navegant la relació 1:N directament
                nom_categoria = dish.category.category_name if dish.category else "[red]Sense categoria[/red]"
                actiu = "[green]✓[/green]" if dish.is_active else "[red]✗[/red]"
                # len(dish.allergens) ens diu quants al·lèrgens té (relació N:M)
                num_allergens = str(len(dish.allergens))

                table.add_row(
                    str(dish.id),
                    dish.dish_name,
                    nom_categoria,
                    actiu,
                    num_allergens
                )

            console.print(table)

    if pause:
        console.input("\nPrem Enter per continuar...")


# Opció 2: Afegir plat. Demostra RELACIÓ 1:N: l'usuari ha de seleccionar una categoria existent.
def add_dish(factory: UnitOfWorkFactory):
    console.print("\n[bold]--- Nou Plat ---[/bold]")

    with factory.create() as uow:
        # Primer mostrem les categories disponibles perquè l'usuari en pugui triar una
        categories = uow.categories.get_all()

        if not categories:
            console.print("[red]No hi ha categories. Crea'n una primer des del menú de Categories.[/red]")
            console.input("Prem Enter per continuar...")
            return

        # Mostrem la llista de categories per facilitar la selecció (RELACIÓ 1:N)
        console.print("\n[bold cyan]Categories disponibles (selecciona'n una per al nou plat):[/bold cyan]")
        cat_table = Table(show_header=True, header_style="bold cyan")
        cat_table.add_column("ID", style="dim", width=5)
        cat_table.add_column("Nom")
        for cat in categories:
            cat_table.add_row(str(cat.id), cat.category_name)
        console.print(cat_table)

        # Validem l'ID de categoria introduït
        cat_id_str = console.input("\nIntrodueix l'ID de la categoria: ")
        if not cat_id_str.isdigit():
            console.print("[red]L'ID ha de ser un número sencer.[/red]")
            console.input("Prem Enter per continuar...")
            return

        cat_id = int(cat_id_str)
        categoria = uow.categories.get(cat_id)

        if not categoria:
            console.print(f"[red]No s'ha trobat cap categoria amb l'ID {cat_id}.[/red]")
            console.input("Prem Enter per continuar...")
            return

        # Recollim les dades del nou plat
        nom         = console.input("Nom del plat: ")
        descripcio  = console.input("Descripció (opcional, deixa en blanc per ometre): ")

        if not nom.strip():
            console.print("[red]El nom del plat no pot estar buit.[/red]")
            console.input("Prem Enter per continuar...")
            return

        try:
            nou_plat = Dish(
                dish_name=nom,
                description=descripcio if descripcio.strip() else None,
                id_category=cat_id,  # RELACIÓ 1:N: assignem la FK de la categoria seleccionada
                is_active=True
            )
            uow.dishes.add(nou_plat)
            console.print(f"\n[green]✓ Plat '{nom}' creat amb èxit a la categoria '{categoria.category_name}'![/green]")

        except Exception as e:
            console.print(f"[bold red]Error:[/bold red] {e}")

    console.input("\nPrem Enter per continuar...")


# Opció 3: Veure detall d'un plat, incloent la seva llista d'al·lèrgens (RELACIÓ N:M)
def view_dish_detail(factory: UnitOfWorkFactory):
    console.print("\n[bold]--- Detall del Plat ---[/bold]")

    # Programació Defensiva: llegim com a text i validem amb .isdigit() abans de convertir-lo a int()
    dish_id_str = console.input("Introdueix l'ID del plat: ")
    if not dish_id_str.isdigit():
        console.print("[red]L'ID ha de ser un número sencer.[/red]")
        console.input("Prem Enter per continuar...")
        return

    dish_id = int(dish_id_str)

    with factory.create() as uow:
        dish = uow.dishes.get(dish_id)

        if not dish:
            console.print(f"[red]No s'ha trobat cap plat amb l'ID {dish_id}.[/red]")
        else:
            console.print(Panel.fit(f"[bold cyan]Plat #{dish.id}: {dish.dish_name}[/bold cyan]", border_style="cyan"))

            # Dades bàsiques del plat
            info_table = Table(show_header=False, box=None)
            info_table.add_column("Camp", style="bold cyan", width=15)
            info_table.add_column("Valor")

            info_table.add_row("Nom",        dish.dish_name)
            info_table.add_row("Descripció", dish.description or "[dim]Sense descripció[/dim]")
            # Naveguem la RELACIÓ 1:N per mostrar el nom de la categoria directament
            info_table.add_row("Categoria",  dish.category.category_name if dish.category else "—")
            info_table.add_row("Actiu",      "[green]Sí[/green]" if dish.is_active else "[red]No[/red]")
            console.print(info_table)

            # --- RELACIÓ N:M amb Allergen ---
            console.print("\n[bold cyan]Al·lèrgens d'aquest plat:[/bold cyan]") #(relació N:M amb dish_allergen)

            if not dish.allergens:
                console.print("[yellow]Aquest plat no té cap al·lèrgen assignat.[/yellow]")
            else:
                al_table = Table(show_header=True, header_style="bold yellow")
                al_table.add_column("ID", style="dim", width=5)
                al_table.add_column("Nom de l'Al·lèrgen")

                for al in dish.allergens:
                    al_table.add_row(str(al.id), al.allergen_name)

                console.print(al_table)

    console.input("\nPrem Enter per continuar...")


# Opció 4: Modificar les dades bàsiques del plat
def update_dish(factory: UnitOfWorkFactory):
    console.print("\n[bold]--- Modificar Plat ---[/bold]")
    list_dishes(factory, pause=False)

    dish_id_str = console.input("Introdueix l'ID del plat a modificar: ")
    if not dish_id_str.isdigit():
        console.print("[red]L'ID ha de ser un número sencer.[/red]")
        console.input("Prem Enter per continuar...")
        return

    dish_id = int(dish_id_str)

    with factory.create() as uow:
        dish = uow.dishes.get(dish_id)

        if not dish:
            console.print(f"[red]No s'ha trobat cap plat amb l'ID {dish_id}.[/red]")
        else:
            console.print(f"\nModificant: [cyan]{dish.dish_name}[/cyan]")
            console.print("[dim]Deixa en blanc per no canviar el camp.[/dim]\n")

            nou_nom  = console.input(f"Nom [{dish.dish_name}]: ")
            nova_desc = console.input(f"Descripció [{dish.description or ''}]: ")

            # .strip() elimina espais. A Python, text buit "" = False, text amb contingut = True
            if nou_nom.strip():   dish.dish_name   = nou_nom
            if nova_desc.strip(): dish.description = nova_desc

            # Preguntem si vol canviar l'estat actiu/inactiu
            estat_actual = "actiu" if dish.is_active else "inactiu"
            canvi_estat = console.input(f"Canviar estat? Ara és [{estat_actual}] (s/n): ").lower()
            if canvi_estat == "s":
                dish.is_active = not dish.is_active

            uow.dishes.update(dish)
            console.print(f"\n[green]✓ Plat actualitzat correctament![/green]")

    console.input("\nPrem Enter per continuar...")


# Opció 5: Eliminar un plat
def delete_dish(factory: UnitOfWorkFactory):
    console.print("\n[bold]--- Eliminar Plat ---[/bold]")
    list_dishes(factory, pause=False)

    dish_id_str = console.input("Introdueix l'ID del plat a eliminar: ")
    if not dish_id_str.isdigit():
        console.print("[red]L'ID ha de ser un número sencer.[/red]")
        console.input("Prem Enter per continuar...")
        return

    dish_id = int(dish_id_str)

    with factory.create() as uow:
        dish = uow.dishes.get(dish_id)

        if not dish:
            console.print(f"[red]No s'ha trobat cap plat amb l'ID {dish_id}.[/red]")
        else:
            console.print(f"\nEstàs a punt d'eliminar el plat: [bold red]{dish.dish_name}[/bold red]")
            confirmacio = console.input("N'estàs segur? (s/n): ").lower()

            if confirmacio == "s":
                uow.dishes.delete(dish_id)
                console.print(f"[green]✓ Plat '{dish.dish_name}' eliminat correctament![/green]")
            else:
                console.print("[yellow]Eliminació cancel·lada.[/yellow]")

    console.input("\nPrem Enter per continuar...")


# Opció 6: Afegir un al·lèrgen a un plat. Demostra la RELACIÓ N:M a través de la taula dish_allergen.
def add_allergen_to_dish(factory: UnitOfWorkFactory):
    console.print("\n[bold]--- Afegir Al·lèrgen a un Plat (N:M) ---[/bold]")

    with factory.create() as uow:
        # Mostrem els plats disponibles
        dishes = uow.dishes.get_all()
        if not dishes:
            console.print("[red]No hi ha cap plat. Crea'n un primer.[/red]")
            console.input("Prem Enter per continuar...")
            return

        dish_table = Table(show_header=True, header_style="bold cyan")
        dish_table.add_column("ID", style="dim", width=5)
        dish_table.add_column("Nom del Plat")
        dish_table.add_column("Al·lèrgens actuals")
        for d in dishes:
            noms_allergens = ", ".join([a.allergen_name for a in d.allergens]) or "—"
            dish_table.add_row(str(d.id), d.dish_name, noms_allergens)
        console.print(dish_table)

        dish_id_str = console.input("\nID del plat al qual vols afegir un al·lèrgen: ")
        if not dish_id_str.isdigit():
            console.print("[red]L'ID ha de ser un número sencer.[/red]")
            console.input("Prem Enter per continuar...")
            return

        dish_id = int(dish_id_str)
        dish = uow.dishes.get(dish_id)

        if not dish:
            console.print(f"[red]No s'ha trobat cap plat amb l'ID {dish_id}.[/red]")
            console.input("Prem Enter per continuar...")
            return

        # Mostrem els al·lèrgens disponibles
        allergens = uow.allergens.get_all()
        if not allergens:
            console.print("[red]No hi ha cap al·lèrgen. Crea'n un primer des del menú d'Al·lèrgens.[/red]")
            console.input("Prem Enter per continuar...")
            return

        console.print(f"\n[bold]Al·lèrgens disponibles per afegir a '{dish.dish_name}':[/bold]")
        al_table = Table(show_header=True, header_style="bold yellow")
        al_table.add_column("ID", style="dim", width=5)
        al_table.add_column("Nom")
        for al in allergens:
            al_table.add_row(str(al.id), al.allergen_name)
        console.print(al_table)

        al_id_str = console.input("\nID de l'al·lèrgen a afegir: ")
        if not al_id_str.isdigit():
            console.print("[red]L'ID ha de ser un número sencer.[/red]")
            console.input("Prem Enter per continuar...")
            return

        al_id = int(al_id_str)
        allergen = uow.allergens.get(al_id)

        if not allergen:
            console.print(f"[red]No s'ha trobat cap al·lèrgen amb l'ID {al_id}.[/red]")
        else:
            # add_allergen_to_dish() del repositori gestiona la taula intermèdia dish_allergen
            # SQLAlchemy insereix la fila a dish_allergen sense que ho haguem de fer manualment
            resultat = uow.dishes.add_allergen_to_dish(dish_id, allergen)

            if resultat:
                console.print(f"\n[green]✓ Al·lèrgen '{allergen.allergen_name}' afegit al plat '{dish.dish_name}'![/green]")
            else:
                console.print(f"[yellow]L'al·lèrgen '{allergen.allergen_name}' ja estava assignat a aquest plat.[/yellow]")

    console.input("\nPrem Enter per continuar...")


# Opció 7: Filtrar només els plats actius (cerca personalitzada del repositori)
def list_active_dishes(factory: UnitOfWorkFactory):
    console.print("\n[bold]--- Plats Actius ---[/bold]")

    with factory.create() as uow:
        # Fa servir el mètode get_active_dishes() del DishRepository
        dishes = uow.dishes.get_active_dishes()

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
                nom_cat = dish.category.category_name if dish.category else "—"
                num_al  = str(len(dish.allergens))
                table.add_row(str(dish.id), dish.dish_name, nom_cat, num_al)

            console.print(table)

    console.input("\nPrem Enter per continuar...")


# Opció 8: Cerca de plats per nom parcial (cerca personalitzada del repositori)
def search_dish_by_name(factory: UnitOfWorkFactory):
    console.print("\n[bold]--- Cercar Plat per Nom ---[/bold]")
    nom = console.input("Introdueix el nom o part del nom a cercar: ")

    if not nom.strip():
        console.print("[red]Has d'introduir algun text per cercar.[/red]")
        console.input("Prem Enter per continuar...")
        return

    with factory.create() as uow:
        # get_by_name() del DishRepository fa cerca parcial amb ilike (insensible a majúscules)
        resultats = uow.dishes.get_by_name(nom)

        if not resultats:
            console.print(f"[yellow]No s'ha trobat cap plat que contingui '{nom}'.[/yellow]")
        else:
            console.print(f"\n[green]{len(resultats)} resultat(s) trobat(s):[/green]")

            table = Table(show_header=True, header_style="bold cyan")
            table.add_column("ID", style="dim", width=5)
            table.add_column("Nom del Plat")
            table.add_column("Categoria")
            table.add_column("Actiu?", justify="center")

            for dish in resultats:
                nom_cat = dish.category.category_name if dish.category else "—"
                actiu   = "[green]✓[/green]" if dish.is_active else "[red]✗[/red]"
                table.add_row(str(dish.id), dish.dish_name, nom_cat, actiu)

            console.print(table)

    console.input("\nPrem Enter per continuar...")
