"""
LEKCE 100: curses – TUI terminálové aplikace
=============================================
Naučíš se vytvářet interaktivní terminálové aplikace
s barvami, okny a live aktualizací – jako htop nebo vim.

curses = vestavěná knihovna (Linux/Mac)
Windows: pip install windows-curses

Základní koncepty:
  stdscr   – hlavní obrazovka (standardní screen)
  window   – okno nebo podokno (subwin/derwin)
  addstr() – vypiš text na souřadnice (y, x)  ← pozor: Y první!
  refresh()– přepíše terminál (double buffering)
  getch()  – čekej na klávesu (blokující)
  getkey() – čekej na klávesu (vrátí string)
  wrapper()– inicializace + úklid automaticky

Souřadnicový systém: (row=y, col=x), (0,0) = levý horní roh
"""

import sys
import os
import time
import random
import textwrap
from datetime import datetime

print("=== LEKCE 100: curses – TUI aplikace ===\n")

# ══════════════════════════════════════════════════════════════
# FALLBACK: Detekce curses dostupnosti
# ══════════════════════════════════════════════════════════════

try:
    import curses
    CURSES_OK = True
except ImportError:
    CURSES_OK = False
    print("  curses není dostupný na tomto systému.")
    print("  Windows: pip install windows-curses")
    print()

# ══════════════════════════════════════════════════════════════
# ČÁST 1: Základní koncepty – bez spouštění TUI
# ══════════════════════════════════════════════════════════════

print("── Část 1: Základní koncepty curses ──\n")

print("""\
  INICIALIZACE:
    curses.wrapper(main)          # inicializuje + volá main(stdscr)
    curses.initscr()              # manuální inicializace
    curses.endwin()               # manuální úklid (vždy volat!)

  ZÁKLADNÍ OPERACE:
    stdscr.clear()                # vymaže obrazovku (do bufferu)
    stdscr.addstr(y, x, "text")  # napiš text na pozici
    stdscr.addstr(y, x, "text", attr)  # s atributem (barva, bold...)
    stdscr.refresh()              # buffer → terminál

  KLÁVESNICE:
    key = stdscr.getch()          # vrátí int (ord nebo curses.KEY_*)
    key = stdscr.getkey()         # vrátí string ('q', 'KEY_UP', ...)
    stdscr.nodelay(True)          # getch() = non-blocking (vrátí -1)

  BARVY:
    curses.start_color()          # aktivace barev
    curses.init_pair(1, fg, bg)  # definuj pár č.1
    attr = curses.color_pair(1)  # získej atribut
    curses.COLOR_RED/GREEN/...   # předefinované barvy

  ATRIBUTY:
    curses.A_BOLD       # tučné
    curses.A_UNDERLINE  # podtržené
    curses.A_REVERSE    # inverzní barvy
    curses.A_BLINK      # blikání
    attr1 | attr2       # kombinace atributů

  VELIKOST OBRAZOVKY:
    rows, cols = stdscr.getmaxyx()  # výška, šířka

  OKNA:
    win = curses.newwin(height, width, y, x)
    win.box()            # rámeček
    win.subwin(h, w, y, x)  # podokno
""")

# ══════════════════════════════════════════════════════════════
# ČÁST 2: Ukázka kódu – základní aplikace
# ══════════════════════════════════════════════════════════════

print("── Část 2: Základní TUI aplikace (kód) ──\n")

ZAKLADNI_PRIKLAD = '''\
import curses

def main(stdscr):
    # Inicializace barev
    curses.start_color()
    curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_BLACK)
    curses.init_pair(2, curses.COLOR_RED,   curses.COLOR_BLACK)
    curses.init_pair(3, curses.COLOR_CYAN,  curses.COLOR_BLACK)

    # Skryj kurzor
    curses.curs_set(0)

    rows, cols = stdscr.getmaxyx()

    stdscr.clear()

    # Nadpis (tučně, centrovaně)
    nadpis = "=== MOJE TUI APLIKACE ==="
    stdscr.addstr(0, (cols - len(nadpis)) // 2, nadpis,
                  curses.A_BOLD | curses.color_pair(3))

    # Zelený text
    stdscr.addstr(2, 2, "Stav: BĚŽÍ", curses.color_pair(1))

    # Červené varování
    stdscr.addstr(3, 2, "Chyba: disk 90%", curses.color_pair(2))

    # Podtržený text
    stdscr.addstr(5, 2, "Stiskni Q pro ukončení", curses.A_UNDERLINE)

    stdscr.refresh()

    # Smyčka
    while True:
        key = stdscr.getkey()
        if key.lower() == 'q':
            break

curses.wrapper(main)
'''

for radek in ZAKLADNI_PRIKLAD.splitlines():
    print(f"  {radek}")
print()

# ══════════════════════════════════════════════════════════════
# ČÁST 3: Ukázka – live monitoring dashboard
# ══════════════════════════════════════════════════════════════

print("── Část 3: Live monitoring dashboard (kód) ──\n")

DASHBOARD_KOD = '''\
import curses, time, random, os

def get_system_stats():
    """Simulace systémových statistik (nahraď psutil pro reálná data)."""
    return {
        "cpu":    random.uniform(10, 95),
        "ram":    random.uniform(40, 85),
        "disk":   random.uniform(20, 70),
        "net_in": random.uniform(0, 100),
        "net_out":random.uniform(0, 50),
    }

def nakresli_bar(win, y, x, hodnota, sirka=20, max_val=100):
    """Vykreslí progress bar."""
    filled = int((hodnota / max_val) * sirka)
    bar = "█" * filled + "░" * (sirka - filled)
    if hodnota > 80:
        attr = curses.color_pair(2)   # červená
    elif hodnota > 60:
        attr = curses.color_pair(3)   # žlutá
    else:
        attr = curses.color_pair(1)   # zelená
    win.addstr(y, x, f"[{bar}] {hodnota:5.1f}%", attr)

def main(stdscr):
    curses.start_color()
    curses.init_pair(1, curses.COLOR_GREEN,  curses.COLOR_BLACK)
    curses.init_pair(2, curses.COLOR_RED,    curses.COLOR_BLACK)
    curses.init_pair(3, curses.COLOR_YELLOW, curses.COLOR_BLACK)
    curses.init_pair(4, curses.COLOR_CYAN,   curses.COLOR_BLACK)
    curses.curs_set(0)
    stdscr.nodelay(True)   # neblokující getch

    while True:
        rows, cols = stdscr.getmaxyx()
        stdscr.clear()
        stats = get_system_stats()
        cas = time.strftime("%Y-%m-%d %H:%M:%S")

        # Záhlaví
        nadpis = f" SYSTEM MONITOR │ {cas} │ q=quit "
        stdscr.addstr(0, 0, nadpis.center(cols), curses.A_REVERSE)

        # Statistiky
        metrika = [
            ("CPU",     stats["cpu"]),
            ("RAM",     stats["ram"]),
            ("Disk",    stats["disk"]),
            ("Net IN",  stats["net_in"]),
            ("Net OUT", stats["net_out"]),
        ]
        for i, (nazev, val) in enumerate(metrika):
            stdscr.addstr(2 + i, 2, f"{nazev:<8}", curses.A_BOLD)
            nakresli_bar(stdscr, 2 + i, 10, val)

        stdscr.addstr(rows - 1, 0, " q=quit  r=refresh ", curses.A_DIM)
        stdscr.refresh()

        key = stdscr.getch()
        if key == ord("q"):
            break
        time.sleep(1)

curses.wrapper(main)
'''

for radek in DASHBOARD_KOD.splitlines():
    print(f"  {radek}")
print()

# ══════════════════════════════════════════════════════════════
# ČÁST 4: Interaktivní demonstrace (pouze pokud máme terminál)
# ══════════════════════════════════════════════════════════════

print("── Část 4: Spuštění live ukázky ──\n")

def spust_demo(stdscr):
    """Jednoduchá TUI ukázka – press q pro ukončení."""
    curses.start_color()
    curses.use_default_colors()
    curses.init_pair(1, curses.COLOR_GREEN,  -1)
    curses.init_pair(2, curses.COLOR_RED,    -1)
    curses.init_pair(3, curses.COLOR_CYAN,   -1)
    curses.init_pair(4, curses.COLOR_YELLOW, -1)
    curses.curs_set(0)
    stdscr.nodelay(True)
    stdscr.timeout(500)   # getch() čeká max 500 ms

    iterace = 0
    while True:
        rows, cols = stdscr.getmaxyx()
        stdscr.clear()

        cas = datetime.now().strftime("%H:%M:%S")
        nadpis = f" LEKCE 100 – curses DEMO │ {cas} "
        try:
            stdscr.addstr(0, 0, nadpis.ljust(cols)[:cols], curses.A_REVERSE)
        except curses.error:
            pass

        metriky = [
            ("CPU",     random.uniform(10, 90)),
            ("RAM",     random.uniform(30, 80)),
            ("Disk",    random.uniform(20, 60)),
        ]

        for i, (nazev, val) in enumerate(metriky):
            y = 2 + i * 2
            filled = int(val / 100 * 30)
            bar = "█" * filled + "░" * (30 - filled)
            if val > 75:
                barva = curses.color_pair(2)
            elif val > 50:
                barva = curses.color_pair(4)
            else:
                barva = curses.color_pair(1)
            try:
                stdscr.addstr(y, 2, f"{nazev:<6}", curses.A_BOLD)
                stdscr.addstr(y, 8, f"[{bar}] {val:5.1f}%", barva)
            except curses.error:
                pass

        try:
            stdscr.addstr(9, 2, f"Iterace: {iterace}", curses.color_pair(3))
            stdscr.addstr(10, 2, "Stiskni  q  pro ukončení", curses.A_DIM)
        except curses.error:
            pass

        stdscr.refresh()
        key = stdscr.getch()
        if key == ord("q") or key == ord("Q"):
            break
        if iterace >= 10:   # automatické ukončení po 10 iteracích
            break
        iterace += 1

IS_INTERACTIVE = sys.stdin.isatty() and sys.stdout.isatty()

if CURSES_OK and IS_INTERACTIVE:
    print("  Spouštím live demo (q = ukončit, max 10 iterací)...")
    print("  " + "-" * 40)
    time.sleep(0.5)
    try:
        curses.wrapper(spust_demo)
        print("\n  Demo ukončeno.")
    except Exception as e:
        print(f"  Demo nelze spustit: {e}")
else:
    print("  Demo přeskočeno – terminál není interaktivní (spouštíme přes pipe).")
    print("  Pro spuštění živého demo: python3 100_curses.py přímo v terminálu.")
print()

# ══════════════════════════════════════════════════════════════
# ČÁST 5: Subwindows a panely (kód)
# ══════════════════════════════════════════════════════════════

print("── Část 5: Subwindows a panels (kód) ──\n")

SUBWIN_KOD = '''\
import curses

def nakresli_okno(win, nadpis: str, obsah: list[str]):
    """Vykreslí okno s rámečkem, nadpisem a obsahem."""
    win.box()
    h, w = win.getmaxyx()
    # Nadpis do rámečku
    win.addstr(0, 2, f" {nadpis} ", curses.A_BOLD)
    # Obsah
    for i, radek in enumerate(obsah[:h-2], start=1):
        win.addstr(i, 2, radek[:w-4])
    win.refresh()

def main(stdscr):
    curses.curs_set(0)
    rows, cols = stdscr.getmaxyx()

    # Dvě okna vedle sebe
    levy_win  = curses.newwin(rows - 2, cols // 2,     1, 0)
    pravy_win = curses.newwin(rows - 2, cols - cols // 2, 1, cols // 2)

    nakresli_okno(levy_win,  "PROCESY", ["python3  12%", "firefox  8%", "code  5%"])
    nakresli_okno(pravy_win, "LOG",     ["INFO server start", "WARN disk 80%", "ERROR conn timeout"])

    stdscr.addstr(0, 0, " Stiskni q ", curses.A_REVERSE)
    stdscr.refresh()

    while stdscr.getkey().lower() != "q":
        pass

curses.wrapper(main)
'''

for radek in SUBWIN_KOD.splitlines():
    print(f"  {radek}")
print()

# ══════════════════════════════════════════════════════════════
# ČÁST 6: Windows fallback
# ══════════════════════════════════════════════════════════════

print("── Část 6: Přenositelnost ──\n")
print("""\
  LINUX / macOS:
    curses je součástí standardní knihovny – funguje okamžitě.

  WINDOWS:
    pip install windows-curses
    import curses  # pak funguje stejně

  ALTERNATIVY pro cross-platform TUI:
    rich       – krásný výstup, progress bary, tabulky (pip install rich)
    textual    – React-like TUI framework nad rich (pip install textual)
    urwid      – nízkoúrovňové TUI (pip install urwid)
    blessed    – curses wrapper s lepším API (pip install blessed)

  Kdy curses vs alternativy?
    curses  → nízkoúrovňová kontrola, žádné závislosti, systémové nástroje
    rich    → krásný výstup bez interaktivity
    textual → moderní TUI aplikace s widgety a layoutem
""")

# ══════════════════════════════════════════════════════════════
# TVOJE ÚLOHA:
# ══════════════════════════════════════════════════════════════
print("=" * 55)
print("TVOJE ÚLOHA:")
print("=" * 55)
print("""
1. Napiš TUI aplikaci 'had_curses.py' – jednoduchá hra had
   v terminálu. Had se pohybuje šipkami, jí jídlo (+1 délka),
   narazí-li do stěny nebo do sebe, game over. Zobraz skóre
   v záhlaví. Použij curses.wrapper() a nodelay(True).

2. Implementuj TUI file browser: zobrazí obsah adresáře,
   šipkami nahoru/dolů se pohybuj po souborech, Enter vstoupí
   do adresáře (nebo otevře soubor přes os.system), q=quit.
   Zobraz ikony: 📁 pro adresáře, 📄 pro soubory (nebo [D]/[F]).

3. Vytvoř TUI „pomodoro timer": odpočítává 25 minut práce,
   pak 5 minut pauzy. Live zobrazuje odpočet ve velkých
   číslicích (ASCII art nebo aspoň MM:SS tučně), barvou
   odlišuje práci (zelená) a pauzu (žlutá). p=pause, q=quit.

4. Napiš curses-based log viewer: načte textový soubor,
   zobrazí ho po obrazovkách, šipky/PgUp/PgDn pro scrollování,
   / pro hledání (zvýrazní nalezené), q=quit. Bonus: tail -f
   mód (sleduj nové řádky přidávané na konec souboru).
""")
