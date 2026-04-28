"""Řešení – Lekce 84: Rich – krásný terminálový výstup"""

# vyžaduje: pip install rich

import time
import random
import sys

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.progress import (Progress, SpinnerColumn, BarColumn,
                                 TextColumn, TimeRemainingColumn)
    from rich.live import Live
    from rich.prompt import Prompt, Confirm
    from rich import print as rprint
    from rich.text import Text
    RICH_OK = True
except ImportError:
    print("Rich není nainstalováno: pip install rich")
    sys.exit(0)

console = Console()

# 1. Rich progress bar pro bubble sort
print()
console.print("[bold blue]=== 1. Bubble sort vizualizace s Rich ===\n[/bold blue]")

def bubble_sort_s_progress(pole: list[int]) -> list[int]:
    """Bubble sort s Rich progress barem."""
    n   = len(pole)
    pol = list(pole)
    pocet_prohozeni = 0
    celkem_operaci  = n * (n - 1) // 2

    with Progress(
        SpinnerColumn(),
        "[progress.description]{task.description}",
        BarColumn(),
        "[progress.percentage]{task.percentage:>3.0f}%",
        TextColumn("[dim]{task.fields[info]}[/dim]"),
        console=console,
        transient=False,
    ) as progress:
        ukol = progress.add_task(
            "[cyan]Bubble sort...",
            total=celkem_operaci,
            info="",
        )

        operace = 0
        for i in range(n):
            prohozeno = False
            for j in range(n - i - 1):
                operace += 1
                progress.update(ukol,
                                 advance=1,
                                 info=f"prohozeni={pocet_prohozeni}")
                if pol[j] > pol[j + 1]:
                    pol[j], pol[j + 1] = pol[j + 1], pol[j]
                    pocet_prohozeni += 1
                    prohozeno = True
                # Krátká pauza pro vizuální efekt
                if operace % 20 == 0:
                    time.sleep(0.005)
            if not prohozeno:
                progress.update(ukol, completed=celkem_operaci)
                break

    console.print(f"  [green]Hotovo![/green] Prohozeno: {pocet_prohozeni}, "
                  f"Operací: {operace}\n")
    return pol

data = random.sample(range(1, 51), 20)
console.print(f"  Vstup:  {data}")
serazeno = bubble_sort_s_progress(data)
console.print(f"  Výstup: {serazeno}")


# 2. Rich výstup pro CI/CD review (z lekce 75)
console.print("\n[bold blue]=== 2. Rich CI/CD review panel ===\n[/bold blue]")

def zobraz_review_panel(diff_soubory: list[str],
                         problémy: list[dict],
                         navrhy: list[str],
                         skore: int = 85):
    """Zobrazí výsledek AI code review jako Rich panel."""

    # Hlavní tabulka problémů
    tbl = Table(title="Code Review – Problémy", show_header=True,
                 header_style="bold red", border_style="red")
    tbl.add_column("Soubor",      style="cyan",   min_width=20)
    tbl.add_column("Řádek",       justify="right", width=8)
    tbl.add_column("Závažnost",   width=10)
    tbl.add_column("Popis")

    for p in problémy:
        zav = p["zavaznost"]
        barva = "red" if zav == "HIGH" else "yellow" if zav == "MEDIUM" else "dim"
        tbl.add_row(
            p["soubor"],
            str(p.get("radek", "?")),
            f"[{barva}]{zav}[/{barva}]",
            p["popis"],
        )

    console.print(tbl)

    # Skóre
    barva_skore = "green" if skore >= 80 else "yellow" if skore >= 60 else "red"
    skore_text = Text()
    skore_text.append(f"Kvalita kódu: ", style="bold")
    skore_text.append(f"{skore}/100", style=f"bold {barva_skore}")

    # Návrhy
    navrhy_text = "\n".join(f"  [dim]•[/dim] {n}" for n in navrhy)

    console.print(Panel(
        f"{skore_text}\n\n[bold]Návrhy na zlepšení:[/bold]\n{navrhy_text}\n\n"
        f"[dim]Změněné soubory: {', '.join(diff_soubory)}[/dim]",
        title="[bold green]AI Code Review[/bold green]",
        border_style="green" if skore >= 80 else "yellow",
        padding=(1, 2),
    ))

# Demo
zobraz_review_panel(
    diff_soubory=["api/views.py", "models/student.py"],
    problémy=[
        {"soubor": "api/views.py",      "radek": 45, "zavaznost": "HIGH",
         "popis": "SQL injection – nepoužíváš parametrizované dotazy"},
        {"soubor": "api/views.py",      "radek": 78, "zavaznost": "MEDIUM",
         "popis": "Chybí autentizace pro DELETE endpoint"},
        {"soubor": "models/student.py", "radek": 12, "zavaznost": "LOW",
         "popis": "Chybí type hint pro parametr 'body'"},
    ],
    navrhy=[
        "Použij SQLAlchemy ORM místo raw SQL dotazů",
        "Přidej @requires_auth dekorátor na DELETE endpoint",
        "Přidej type hints: body: float = 0.0",
    ],
    skore=72,
)


# 3. Interaktivní menu s Rich.Prompt + Rich.Table
console.print("\n[bold blue]=== 3. Interaktivní menu ===\n[/bold blue]")

STUDENTI_DB = [
    {"id": 1, "jmeno": "Míša",  "predmet": "Python",      "body": 87.5},
    {"id": 2, "jmeno": "Tomáš", "predmet": "Fyzika",       "body": 92.0},
    {"id": 3, "jmeno": "Bára",  "predmet": "Matematika",   "body": 55.3},
    {"id": 4, "jmeno": "Ondra", "predmet": "Informatika",  "body": 95.1},
    {"id": 5, "jmeno": "Klára", "predmet": "Biologie",     "body": 61.0},
]

def zobraz_studenty(studenti: list[dict]):
    """Zobrazí tabulku studentů."""
    tbl = Table(title="Studenti", show_header=True,
                 header_style="bold cyan", border_style="blue")
    tbl.add_column("ID",        style="dim",   width=5)
    tbl.add_column("Jméno",     style="bold")
    tbl.add_column("Předmět",   style="cyan")
    tbl.add_column("Body",      justify="right")
    tbl.add_column("Výsledek")

    for s in studenti:
        body = s["body"]
        vysledek = "✓ Prospívá" if body >= 75 else "✗ Neprospívá"
        barva    = "green" if body >= 75 else "red"
        tbl.add_row(
            str(s["id"]),
            s["jmeno"],
            s["predmet"],
            f"[{barva}]{body}[/{barva}]",
            f"[{barva}]{vysledek}[/{barva}]",
        )

    console.print(tbl)

def interaktivni_menu(studenti: list[dict]):
    """
    Interaktivní menu pro správu studentů.
    Při spuštění s non-TTY vstupem (pipeline) použije hardcoded volby.
    """
    MOZNOSTI = {
        "1": "Zobrazit všechny studenty",
        "2": "Filtrovat (pouze prospívající)",
        "3": "Přidat studenta",
        "q": "Konec",
    }

    # Zjisti, zda je terminál interaktivní
    je_interaktivni = sys.stdin.isatty()

    # Hardcoded demo průchod pro neinteraktivní spuštění
    demo_volby = ["1", "2", "q"]
    demo_idx   = [0]

    def ziskej_volbu() -> str:
        if je_interaktivni:
            return Prompt.ask(
                "\n[bold]Volba[/bold]",
                choices=list(MOZNOSTI.keys()),
                default="1",
            )
        else:
            # Automatický demo průchod
            if demo_idx[0] < len(demo_volby):
                v = demo_volby[demo_idx[0]]
                demo_idx[0] += 1
                console.print(f"  [dim]> {v}[/dim]")
                return v
            return "q"

    while True:
        console.print("\n[bold]MENU:[/bold]")
        for k, v in MOZNOSTI.items():
            console.print(f"  [cyan]{k}[/cyan]  {v}")

        volba = ziskej_volbu()

        if volba == "1":
            zobraz_studenty(studenti)

        elif volba == "2":
            prospivajici = [s for s in studenti if s["body"] >= 75]
            console.print(Panel(
                f"Prospívající: {len(prospivajici)}/{len(studenti)}",
                style="green"
            ))
            zobraz_studenty(prospivajici)

        elif volba == "3":
            if je_interaktivni:
                jmeno   = Prompt.ask("  Jméno")
                predmet = Prompt.ask("  Předmět")
                body    = float(Prompt.ask("  Body", default="75"))
            else:
                jmeno, predmet, body = "Nový Student", "Python", 80.0
                console.print(f"  [dim](Demo: přidávám {jmeno})[/dim]")

            novy = {"id": max(s["id"] for s in studenti) + 1,
                    "jmeno": jmeno, "predmet": predmet, "body": body}
            studenti.append(novy)
            console.print(f"  [green]✓ Student {jmeno} přidán[/green]")

        elif volba == "q":
            console.print("[dim]Konec.[/dim]")
            break

interaktivni_menu(STUDENTI_DB)

console.print(Panel(
    "[bold green]Všechny Rich demo úspěšně proběhly![/bold green]",
    title="Shrnutí",
    border_style="green",
))
