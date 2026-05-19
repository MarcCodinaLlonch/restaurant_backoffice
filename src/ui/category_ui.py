from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box

from src.domain.unit_of_work import UnitOfWorkFactory
from src.domain.models import Category

console = Console()

def menu_categories(factory: UnitOfWorkFactory):
    while True:
        console.clear()
        console.print(Panel.fit("[bold magenta]Gestió de Categories[/bold magenta]", border_style="magenta", box=box.DOUBLE))
        console.print("1. Llistar Categories (Read)")
        console.print("2. Afegir Categoria (Create)")
        console.print("3. Modificar Categoria (Update)") # Encara no funciona
        console.print("4. Eliminar Categoria (Delete)") # Encara no funciona
        console.print("0. Tornar al menú principal")
        
        opcio = console.input("\n[bold yellow]Selecciona una opció:[/bold yellow] ")
        
        if opcio == "1":
            list_categories(factory)
        elif opcio == "2":
            add_category(factory)
        elif opcio == "3":
            update_category(factory) 
        elif opcio == "4":
            delete_category(factory)
        elif opcio == "0":
            break
        else:
            console.print("[red]Opció no vàlida.[/red]")
            console.input("Prem Enter per continuar...")

#Mètode per opció 1. Llistar categories
def list_categories(factory: UnitOfWorkFactory):
    console.print("\n[bold]--- Llistat de Categories ---[/bold]")
    
    # 1. Obrim transacció a la BD
    with factory.create() as uow:
        # 2. Fem servir el teu Repositori per treure-ho tot
        categories = uow.categories.get_all()
        
        if not categories:
            console.print("[yellow]No hi ha cap categoria a la base de dades.[/yellow]")
        else:
            # 3. Creem una taula visual amb Rich
            table = Table(show_header=True, header_style="bold magenta")
            table.add_column("ID", style="dim", width=5)
            table.add_column("Nom de la Categoria")
            
            # 4. Omplim la taula
            for cat in categories:
                table.add_row(str(cat.id), cat.category_name)
                
            console.print(table)
            
    console.input("\nPrem Enter per continuar...")

#Mètode per opció 2. Afegir categoria
def add_category(factory: UnitOfWorkFactory):
    console.print("\n[bold]--- Nova Categoria ---[/bold]")
    nom = console.input("Introdueix el nom de la categoria: ")
    
    # Si el nom està buit, mostrem error i tornem al menú sense intentar inserir a BD
    if not nom.strip():
        console.print("[red]El nom no pot estar buit.[/red]")
        console.input("Prem Enter per continuar...")
        return

    # Obrim transacció
    with factory.create() as uow:
        try:
            nova_categoria = Category(category_name=nom)
            uow.categories.add(nova_categoria)
            # Com que sortim del bloc 'with' sense error, 
            # el UnitOfWork farà el uow.commit() automàticament.
            console.print(f"\n[green]✓ Categoria '{nom}' creada amb èxit![/green]")
        except ValueError as e:
            # Captura error si el nom ja existeix (validació implementada al repositori)
            console.print(f"\n[bold red]Error:[/bold red] {e}")
            
    console.input("\nPrem Enter per continuar...")

# Mètode per opció 3. Modificar categoria
def update_category(factory: UnitOfWorkFactory):
        console.print("\n[bold]--- Modificar Categoria ---[/bold]")

        # Llegim l'ID com a text i validem amb .isdigit() abans de convertir-lo a int().
        # Evita que l'aplicació peti amb un ValueError si l'usuari tecleja lletres.
        cat_id_str = console.input("Introdueix l'ID de la categoria a modificar: ")
        # Validem que ens hagin passat un número
        if not cat_id_str.isdigit():
            console.print("[red]L'ID ha de ser un número sencer.[/red]")
            console.input("Prem Enter per continuar...")
            return
        # Convertim a int després de validar que és un número
        cat_id = int(cat_id_str)
        
        with factory.create() as uow:
            # Busquem la categoria per ID
            categoria = uow.categories.get(cat_id)
            
            if not categoria:
                console.print(f"[red]No s'ha trobat cap categoria amb l'ID {cat_id}.[/red]")
            else:
                console.print(f"Categoria actual: [cyan]{categoria.category_name}[/cyan]")
                nou_nom = console.input("Introdueix el nou nom (deixa en blanc per cancel·lar): ")
                
                # Si l'usuari introdueix un nom buit, considerem que vol cancel·lar l'operació i no fem cap canvi.
                # A python si hi ha una cadena buida, la condició if nou_nom.strip() serà False, 
                # i entrarem al bloc else per mostrar missatge de cancel·lació.
                if nou_nom.strip():
                    try:
                        categoria.category_name = nou_nom
                        # Tot i que SQLAlchemy guarda els canvis automàticament en fer commit,
                        # cridem al teu mètode update() per passar per les validacions que tens fetes.
                        uow.categories.update(categoria)
                        console.print(f"[green]✓ Categoria actualitzada correctament a '{nou_nom}'![/green]")
                    except ValueError as e:
                        # Captura l'error si intentes posar un nom que ja té una altra categoria
                        console.print(f"[bold red]Error:[/bold red] {e}")
                else:
                    console.print("[yellow]Operació cancel·lada.[/yellow]")
                    
        console.input("\nPrem Enter per continuar...")

# Mètode per opció 4. Eliminar categoria
def delete_category(factory: UnitOfWorkFactory):
    console.print("\n[bold]--- Eliminar Categoria ---[/bold]")
    cat_id_str = console.input("Introdueix l'ID de la categoria a eliminar: ")
    
    if not cat_id_str.isdigit():
        console.print("[red]L'ID ha de ser un número sencer.[/red]")
        console.input("Prem Enter per continuar...")
        return
        
    cat_id = int(cat_id_str)
    
    with factory.create() as uow:
        categoria = uow.categories.get(cat_id)
        
        if not categoria:
            console.print(f"[red]No s'ha trobat cap categoria amb l'ID {cat_id}.[/red]")
        else:
            console.print(f"Estàs a punt d'eliminar la categoria: [bold red]{categoria.category_name}[/bold red]")
            confirmacio = console.input("N'estàs segur? (s/n): ").lower()
            
            if confirmacio == 's':
                uow.categories.delete(cat_id)
                console.print(f"[green]✓ Categoria '{categoria.category_name}' eliminada correctament![/green]")
            else:
                console.print("[yellow]Eliminació cancel·lada.[/yellow]")
                
    console.input("\nPrem Enter per continuar...")
