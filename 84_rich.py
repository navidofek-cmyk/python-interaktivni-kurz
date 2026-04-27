"""
LEKCE 84: Rich – krásný terminálový výstup
============================================
pip install rich

Rich přidá do terminálu: barvy, tabulky, progress bary,
syntax highlighting, stromy, panels, markdown...

Používá ho pip, pytest, FastAPI, Textual a stovky dalších.
"""

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn
    from rich.syntax import Syntax
    from rich.tree import Tree
    from rich.markdown import Markdown
    from rich.layout import Layout
    from rich.live import Live
    from rich import print as rprint
    from rich.text import Text
    from rich.columns import Columns
    import rich
    RICH_OK = True
except ImportError:
    print("Rich není nainstalováno: pip install rich")
    RICH_OK = False

import time
import random

if not RICH_OK:
    exit()

console = Console()

# ══════════════════════════════════════════════════════════════
# ČÁST 1: Základní výstup
# ══════════════════════════════════════════════════════════════

console.print("\n[bold blue]=== Rich – základní výstup ===[/bold blue]\n")

# Markup syntax
console.print("[bold]Tučné[/bold]  [italic]Kurzíva[/italic]  [underline]Podtržené[/underline]")
console.print("[red]Červená[/red]  [green]Zelená[/green]  [yellow]Žlutá[/yellow]  [blue]Modrá[/blue]")
console.print("[bold green]✓ Úspěch[/bold green]  [bold red]✗ Chyba[/bold red]  [bold yellow]⚠ Varování[/bold yellow]")

# Emoji a unicode plně podporovány
console.print("\n🐍 Python  🚀 Rychlý  📦 Balíček  ✨ Krásný")

# Panel
console.print(Panel(
    "[green]Vše proběhlo v pořádku![/green]\n[dim]Čas: 0.42s[/dim]",
    title="[bold]Výsledek[/bold]",
    border_style="green",
))


# ══════════════════════════════════════════════════════════════
# ČÁST 2: Tabulky
# ══════════════════════════════════════════════════════════════

console.print("\n[bold blue]=== Tabulky ===[/bold blue]\n")

tabulka = Table(title="Studenti – výsledky", show_header=True,
                 header_style="bold cyan")
tabulka.add_column("#",       style="dim", width=4)
tabulka.add_column("Jméno",   style="bold")
tabulka.add_column("Předmět")
tabulka.add_column("Body",    justify="right")
tabulka.add_column("Výsledek")

studenti = [
    (1, "Míša",  "Python",      87.5, True),
    (2, "Tomáš", "Fyzika",      92.0, True),
    (3, "Bára",  "Matematika",  55.3, False),
    (4, "Ondra", "Informatika", 95.1, True),
    (5, "Klára", "Biologie",    61.0, False),
]

for cislo, jmeno, predmet, body, prospiva in studenti:
    ikona    = "[green]✓ Prospívá[/green]" if prospiva else "[red]✗ Neprospívá[/red]"
    body_str = f"[green]{body}[/green]" if body >= 75 else f"[red]{body}[/red]"
    tabulka.add_row(str(cislo), jmeno, predmet, body_str, ikona)

console.print(tabulka)


# ══════════════════════════════════════════════════════════════
# ČÁST 3: Progress bar
# ══════════════════════════════════════════════════════════════

console.print("\n[bold blue]=== Progress bar ===[/bold blue]\n")

# Jednoduchý progress
with Progress(
    SpinnerColumn(),
    "[progress.description]{task.description}",
    BarColumn(),
    "[progress.percentage]{task.percentage:>3.0f}%",
    TextColumn("[dim]{task.completed}/{task.total}[/dim]"),
    console=console,
) as progress:
    ukol1 = progress.add_task("[cyan]Stahování dat...", total=50)
    ukol2 = progress.add_task("[green]Zpracování...",  total=30)
    ukol3 = progress.add_task("[yellow]Ukládání...",   total=20)

    while not progress.finished:
        time.sleep(0.02)
        progress.update(ukol1, advance=random.uniform(0.5, 2))
        progress.update(ukol2, advance=random.uniform(0, 1.5))
        progress.update(ukol3, advance=random.uniform(0, 1))


# ══════════════════════════════════════════════════════════════
# ČÁST 4: Syntax highlighting
# ══════════════════════════════════════════════════════════════

console.print("\n[bold blue]=== Syntax highlighting ===[/bold blue]\n")

kod = '''\
def fibonacci(n: int) -> int:
    """Fibonacci s lru_cache – O(N)."""
    from functools import lru_cache

    @lru_cache(maxsize=None)
    def fib(k):
        return k if k < 2 else fib(k-1) + fib(k-2)

    return fib(n)

print([fibonacci(i) for i in range(10)])
'''

syntax = Syntax(kod, "python", theme="monokai", line_numbers=True,
                 background_color="default")
console.print(syntax)


# ══════════════════════════════════════════════════════════════
# ČÁST 5: Strom
# ══════════════════════════════════════════════════════════════

console.print("\n[bold blue]=== Strom souborů ===[/bold blue]\n")

strom = Tree("📁 [bold]python-kurz[/bold]")

zaklady = strom.add("📁 [cyan]základy[/cyan]")
for l in ["01_ahoj_svete.py", "02_promenne.py", "03_vstupy.py"]:
    zaklady.add(f"🐍 {l}")

oop = strom.add("📁 [cyan]OOP[/cyan]")
oop.add("🐍 22_tridy_zaklad.py")
oop.add("🐍 23_dedicnost.py")

web = strom.add("📁 [green]web[/green]")
web.add("📄 index.html [dim](generovaný)[/dim]")
web.add("📁 lekce/").add("[dim]... 83 souborů ...[/dim]")

strom.add("⚙️  [yellow].github/workflows/[/yellow]")
strom.add("📋 CLAUDE.md")
strom.add("📋 README.md")

console.print(strom)


# ══════════════════════════════════════════════════════════════
# ČÁST 6: Markdown
# ══════════════════════════════════════════════════════════════

console.print("\n[bold blue]=== Markdown ===[/bold blue]\n")

md_text = """\
# Python kurz

Interaktivní kurz Pythonu – **83 lekcí** od základů po produkci.

## Funkce
- Každá lekce = jeden `.py` soubor
- Spustitelné přímo: `python3 01_ahoj_svete.py`
- Generátor webu v *Pythonu*

> "Programs must be written for people to read, and only incidentally for machines to execute."
> — Harold Abelson
"""
console.print(Markdown(md_text))


# ══════════════════════════════════════════════════════════════
# ČÁST 7: Live display (real-time aktualizace)
# ══════════════════════════════════════════════════════════════

console.print("\n[bold blue]=== Live dashboard ===[/bold blue]\n")

def generuj_dashboard(krok: int) -> Table:
    t = Table(title=f"Monitoring – krok {krok}", expand=True)
    t.add_column("Služba")
    t.add_column("Status")
    t.add_column("Latence")
    t.add_column("Req/s", justify="right")

    sluzby = ["API Gateway", "Auth Service", "DB Primary", "Cache Redis"]
    for sluzba in sluzby:
        ok = random.random() > 0.1
        lat = random.randint(2, 50) if ok else random.randint(200, 2000)
        rps = random.randint(50, 500)
        t.add_row(
            sluzba,
            "[green]● OK[/green]"  if ok else "[red]● DOWN[/red]",
            f"[green]{lat}ms[/green]" if lat < 100 else f"[red]{lat}ms[/red]",
            str(rps),
        )
    return t

with Live(generuj_dashboard(0), refresh_per_second=4,
           console=console) as live:
    for i in range(1, 12):
        time.sleep(0.25)
        live.update(generuj_dashboard(i))


# ══════════════════════════════════════════════════════════════
# ČÁST 8: Inspect (debugging helper)
# ══════════════════════════════════════════════════════════════

console.print("\n[bold blue]=== rich.inspect ===[/bold blue]\n")

from rich import inspect
inspect([1, 2, 3], methods=False, title="list objekt")

console.print(Panel(
    "[bold green]Rich je nainstalován a funguje! 🎉[/bold green]\n"
    "[dim]Všechny funkce: tabulky, progress, syntax, strom, live, markdown[/dim]",
    title="Shrnutí",
    border_style="green",
    padding=(1, 2),
))

# TVOJE ÚLOHA:
# 1. Napiš rich progress bar pro lekci 36 (třídění) – vizualizuj postup bubble sortu.
# 2. Přidej rich do lekce 75 (CI/CD) – výsledek review zobraz jako Panel s barvami.
# 3. Napiš interaktivní menu s rich.prompt.Prompt a rich.table.
