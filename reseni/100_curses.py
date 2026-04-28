"""Řešení – Lekce 100: curses – TUI terminálové aplikace

Toto je vzorové řešení úloh z lekce 100.

POZNÁMKA: Úlohy 1–4 jsou interaktivní TUI aplikace – níže jsou
kompletní implementace. Spusť je samostatně v terminálu:

  python3 reseni/100_curses.py had        # Úloha 1 – had
  python3 reseni/100_curses.py browser    # Úloha 2 – file browser
  python3 reseni/100_curses.py pomodoro   # Úloha 3 – pomodoro timer
  python3 reseni/100_curses.py logview <soubor>  # Úloha 4 – log viewer

Bez argumentu se vypíše přehled.
"""

import sys
import os
import time
import random
import collections
from datetime import datetime, timedelta
from pathlib import Path

try:
    import curses
    CURSES_OK = True
except ImportError:
    CURSES_OK = False

# ── Úloha 1 ────────────────────────────────────────────────
# Hra had v terminálu pomocí curses.

def spust_had(stdscr):
    """Jednoduchá hra had."""
    curses.start_color()
    curses.use_default_colors()
    curses.init_pair(1, curses.COLOR_GREEN,  -1)   # had
    curses.init_pair(2, curses.COLOR_RED,    -1)   # jídlo
    curses.init_pair(3, curses.COLOR_YELLOW, -1)   # skóre
    curses.init_pair(4, curses.COLOR_CYAN,   -1)   # záhlaví
    curses.curs_set(0)
    stdscr.nodelay(True)
    stdscr.timeout(120)   # ms na tik

    rows, cols = stdscr.getmaxyx()
    hraci_rows = rows - 3
    hraci_cols = cols - 2

    def nova_hra():
        cx, cy = hraci_cols // 2, hraci_rows // 2
        had = collections.deque([(cy, cx), (cy, cx - 1), (cy, cx - 2)])
        smer = (0, 1)   # (dy, dx)
        jidlo = umisti_jidlo(had)
        return had, smer, jidlo, 0

    def umisti_jidlo(had):
        while True:
            fy = random.randint(1, hraci_rows - 2)
            fx = random.randint(1, hraci_cols - 2)
            if (fy, fx) not in had:
                return (fy, fx)

    had, smer, jidlo, skore = nova_hra()
    smery = {
        curses.KEY_UP:    (-1, 0),
        curses.KEY_DOWN:  ( 1, 0),
        curses.KEY_LEFT:  ( 0,-1),
        curses.KEY_RIGHT: ( 0, 1),
        ord("w"): (-1, 0), ord("s"): (1, 0),
        ord("a"): (0, -1), ord("d"): (0, 1),
    }
    game_over = False

    while True:
        key = stdscr.getch()
        if key == ord("q") or key == ord("Q"):
            break
        if key == ord("r") and game_over:
            had, smer, jidlo, skore = nova_hra()
            game_over = False
            continue
        if key in smery and not game_over:
            novy_smer = smery[key]
            # Zakázáme otočení o 180°
            if (novy_smer[0] + smer[0], novy_smer[1] + smer[1]) != (0, 0):
                smer = novy_smer

        stdscr.clear()
        rows, cols = stdscr.getmaxyx()

        # Záhlaví
        zahlavi = f" HAD | Skóre: {skore} | Délka: {len(had)} | q=quit r=restart "
        stdscr.addstr(0, 0, zahlavi[:cols].ljust(min(cols, len(zahlavi) + 2)),
                      curses.color_pair(4) | curses.A_BOLD)

        # Rámeček
        try:
            stdscr.addstr(1, 0, "+" + "-" * (hraci_cols) + "+")
            for y in range(2, hraci_rows + 1):
                stdscr.addstr(y, 0, "|")
                stdscr.addstr(y, hraci_cols + 1, "|")
            stdscr.addstr(hraci_rows + 1, 0, "+" + "-" * hraci_cols + "+")
        except curses.error:
            pass

        if not game_over:
            # Pohyb
            hy, hx = had[0]
            ny, nx = hy + smer[0], hx + smer[1]

            if (nx <= 0 or nx >= hraci_cols or
                    ny <= 0 or ny >= hraci_rows or
                    (ny, nx) in had):
                game_over = True
            else:
                had.appendleft((ny, nx))
                if (ny, nx) == jidlo:
                    skore += 1
                    jidlo = umisti_jidlo(had)
                else:
                    had.pop()

        # Kreslení hada
        for i, (sy, sx) in enumerate(had):
            try:
                ch = "█" if i == 0 else "▓"
                stdscr.addstr(sy + 1, sx + 1, ch, curses.color_pair(1) | curses.A_BOLD)
            except curses.error:
                pass

        # Jídlo
        try:
            stdscr.addstr(jidlo[0] + 1, jidlo[1] + 1, "◆", curses.color_pair(2) | curses.A_BOLD)
        except curses.error:
            pass

        # Game over
        if game_over:
            msg = f" GAME OVER! Skóre: {skore} | r=restart  q=quit "
            try:
                stdscr.addstr(rows // 2, max(0, (cols - len(msg)) // 2),
                              msg, curses.A_REVERSE | curses.color_pair(2))
            except curses.error:
                pass

        stdscr.refresh()


# ── Úloha 2 ────────────────────────────────────────────────
# TUI file browser – procházení adresářů šipkami.

def spust_browser(stdscr, startdir: str = "."):
    curses.start_color()
    curses.use_default_colors()
    curses.init_pair(1, curses.COLOR_CYAN,   -1)   # adresáře
    curses.init_pair(2, curses.COLOR_WHITE,  -1)   # soubory
    curses.init_pair(3, curses.COLOR_BLACK,  curses.COLOR_WHITE)  # vybraná položka
    curses.init_pair(4, curses.COLOR_YELLOW, -1)   # záhlaví
    curses.curs_set(0)

    aktualni = Path(startdir).resolve()
    vybrano = 0
    scroll = 0

    while True:
        stdscr.clear()
        rows, cols = stdscr.getmaxyx()

        # Načtení obsahu adresáře
        try:
            polozky = sorted(aktualni.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))
        except PermissionError:
            polozky = []

        # Záhlaví
        zahlavi = f" [D]ir/[F]ile Browser │ {str(aktualni)[:cols-25]} │ q=quit Enter=vstup "
        try:
            stdscr.addstr(0, 0, zahlavi[:cols].ljust(cols), curses.color_pair(4) | curses.A_BOLD)
        except curses.error:
            pass

        # Přidáme ".." na začátek
        display = [(".. (nahoru)", True)] + [(p.name + ("/" if p.is_dir() else ""), p.is_dir()) for p in polozky]

        # Scrollování
        viditelne = rows - 3
        if vybrano < scroll:
            scroll = vybrano
        if vybrano >= scroll + viditelne:
            scroll = vybrano - viditelne + 1

        for i, (nazev, je_dir) in enumerate(display[scroll:scroll + viditelne]):
            idx = scroll + i
            attr = curses.color_pair(1) if je_dir else curses.color_pair(2)
            prefix = "[D] " if je_dir else "[F] "
            radek = f" {prefix}{nazev} "
            if idx == vybrano:
                attr = curses.color_pair(3) | curses.A_BOLD
            try:
                stdscr.addstr(1 + i, 0, radek[:cols].ljust(min(cols, len(radek) + 2)), attr)
            except curses.error:
                pass

        # Stavový řádek
        try:
            stav = f" {vybrano + 1}/{len(display)} | šipky=pohyb  Enter=vstup  q=quit "
            stdscr.addstr(rows - 1, 0, stav[:cols], curses.A_DIM)
        except curses.error:
            pass

        stdscr.refresh()

        key = stdscr.getch()
        if key == ord("q") or key == ord("Q"):
            break
        elif key == curses.KEY_UP:
            vybrano = max(0, vybrano - 1)
        elif key == curses.KEY_DOWN:
            vybrano = min(len(display) - 1, vybrano + 1)
        elif key in (curses.KEY_ENTER, 10, 13):
            if vybrano == 0:
                aktualni = aktualni.parent
                vybrano = 0
                scroll = 0
            else:
                cilova = polozky[vybrano - 1]
                if cilova.is_dir():
                    aktualni = cilova
                    vybrano = 0
                    scroll = 0


# ── Úloha 3 ────────────────────────────────────────────────
# Pomodoro timer – 25 min práce / 5 min pauza.

def spust_pomodoro(stdscr):
    curses.start_color()
    curses.use_default_colors()
    curses.init_pair(1, curses.COLOR_GREEN,  -1)   # práce
    curses.init_pair(2, curses.COLOR_YELLOW, -1)   # pauza
    curses.init_pair(3, curses.COLOR_RED,    -1)   # čas končí
    curses.init_pair(4, curses.COLOR_CYAN,   -1)   # záhlaví
    curses.curs_set(0)
    stdscr.timeout(500)

    PRACE_SEC  = 25 * 60
    PAUZA_SEC  = 5  * 60

    fazе = "práce"
    celkem = PRACE_SEC
    zbyva = celkem
    pauzovano = False
    kolo = 1

    zacatek = time.time()
    cas_pausy = 0.0

    while True:
        stdscr.clear()
        rows, cols = stdscr.getmaxyx()

        # Aktualizace času
        if not pauzovano:
            elapsed = time.time() - zacatek
            zbyva = max(0, celkem - int(elapsed))

        if zbyva == 0:
            if fazе == "práce":
                fazе = "pauza"
                celkem = PAUZA_SEC
            else:
                fazе = "práce"
                kolo += 1
                celkem = PRACE_SEC
            zacatek = time.time()
            zbyva = celkem

        minuty = zbyva // 60
        sekundy = zbyva % 60
        cas_str = f"{minuty:02d}:{sekundy:02d}"

        barva = curses.color_pair(1) if fazе == "práce" else curses.color_pair(2)
        if zbyva < 60:
            barva = curses.color_pair(3)

        # Záhlaví
        zahlavi = f" POMODORO | Kolo {kolo} | p=pause/resume  q=quit "
        try:
            stdscr.addstr(0, 0, zahlavi[:cols].ljust(cols), curses.color_pair(4) | curses.A_BOLD)
        except curses.error:
            pass

        # Fáze
        faze_str = f"{'▶ PRÁCE' if fazе == 'práce' else '☕ PAUZA'}"
        try:
            stdscr.addstr(rows // 2 - 3, (cols - len(faze_str)) // 2, faze_str,
                          barva | curses.A_BOLD)
        except curses.error:
            pass

        # Velký čas
        try:
            stdscr.addstr(rows // 2, (cols - len(cas_str)) // 2, cas_str,
                          barva | curses.A_BOLD)
        except curses.error:
            pass

        if pauzovano:
            msg = "  ⏸ PAUZA  "
            try:
                stdscr.addstr(rows // 2 + 2, (cols - len(msg)) // 2, msg, curses.A_REVERSE)
            except curses.error:
                pass

        # Progress bar
        sirka = min(40, cols - 4)
        progress = 1.0 - (zbyva / celkem) if celkem > 0 else 0.0
        filled = int(progress * sirka)
        bar = "█" * filled + "░" * (sirka - filled)
        try:
            stdscr.addstr(rows // 2 + 4, (cols - sirka) // 2, bar, barva)
        except curses.error:
            pass

        stdscr.refresh()

        key = stdscr.getch()
        if key == ord("q") or key == ord("Q"):
            break
        elif key == ord("p") or key == ord("P"):
            if pauzovano:
                # Obnovení – posuneme zacatek o dobu pauzy
                zacatek += time.time() - cas_pausy
                pauzovano = False
            else:
                cas_pausy = time.time()
                pauzovano = True


# ── Úloha 4 ────────────────────────────────────────────────
# Log viewer – scrollování, hledání, q=quit.

def spust_logviewer(stdscr, soubor: str):
    curses.start_color()
    curses.use_default_colors()
    curses.init_pair(1, curses.COLOR_GREEN,  -1)   # normální
    curses.init_pair(2, curses.COLOR_RED,    -1)   # ERROR
    curses.init_pair(3, curses.COLOR_YELLOW, -1)   # WARN
    curses.init_pair(4, curses.COLOR_CYAN,   -1)   # záhlaví
    curses.init_pair(5, curses.COLOR_BLACK, curses.COLOR_YELLOW)   # nalezený text
    curses.curs_set(0)
    stdscr.timeout(200)

    def nacti_radky():
        try:
            return Path(soubor).read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            return [f"CHYBA: nelze otevřít soubor {soubor!r}"]

    radky = nacti_radky()
    scroll = max(0, len(radky) - 1)
    hledane = ""
    hledani_mode = False
    hledani_buf = ""

    while True:
        stdscr.clear()
        rows, cols = stdscr.getmaxyx()
        viditelne = rows - 2

        # Záhlaví
        zahlavi = f" LOG: {soubor[:cols-30]} | ↑↓ PgUp PgDn | /=hledej  q=quit "
        try:
            stdscr.addstr(0, 0, zahlavi[:cols].ljust(cols), curses.color_pair(4) | curses.A_BOLD)
        except curses.error:
            pass

        # Zobrazení řádků
        for i in range(viditelne):
            idx = scroll + i
            if idx >= len(radky):
                break
            radek = radky[idx]
            # Barva podle obsahu
            if "ERROR" in radek or "CRITICAL" in radek:
                barva = curses.color_pair(2)
            elif "WARN" in radek:
                barva = curses.color_pair(3)
            else:
                barva = curses.color_pair(1)
            try:
                stdscr.addstr(1 + i, 0, radek[:cols], barva)
                # Zvýraznění hledaného textu
                if hledane and hledane.lower() in radek.lower():
                    pos = radek.lower().find(hledane.lower())
                    if pos < cols:
                        stdscr.addstr(1 + i, pos,
                                      radek[pos:pos + len(hledane)][:cols - pos],
                                      curses.color_pair(5) | curses.A_BOLD)
            except curses.error:
                pass

        # Stavový řádek
        if hledani_mode:
            stav = f" Hledej: {hledani_buf}_ "
        else:
            stav = f" Řádek {scroll + 1}/{len(radky)} | /=hledej  n=další  q=quit "
        try:
            stdscr.addstr(rows - 1, 0, stav[:cols], curses.A_REVERSE)
        except curses.error:
            pass

        stdscr.refresh()

        key = stdscr.getch()
        if hledani_mode:
            if key in (10, 13, 27):     # Enter nebo Esc
                hledane = hledani_buf
                hledani_mode = False
            elif key in (curses.KEY_BACKSPACE, 127, 8):
                hledani_buf = hledani_buf[:-1]
            elif 32 <= key < 127:
                hledani_buf += chr(key)
            continue

        if key == ord("q") or key == ord("Q"):
            break
        elif key == curses.KEY_UP:
            scroll = max(0, scroll - 1)
        elif key == curses.KEY_DOWN:
            scroll = min(max(0, len(radky) - viditelne), scroll + 1)
        elif key == curses.KEY_PPAGE:
            scroll = max(0, scroll - viditelne)
        elif key == curses.KEY_NPAGE:
            scroll = min(max(0, len(radky) - viditelne), scroll + viditelne)
        elif key == ord("/"):
            hledani_mode = True
            hledani_buf = ""
        elif key == ord("n") and hledane:
            # Hledej další výskyt
            for i in range(scroll + 1, len(radky)):
                if hledane.lower() in radky[i].lower():
                    scroll = i
                    break
        elif key == ord("r"):
            # Tail -f mód – znovu načteme soubor
            radky = nacti_radky()
            scroll = max(0, len(radky) - viditelne)


# ── Hlavní spouštěcí logika ────────────────────────────────

def main():
    if not CURSES_OK:
        print("curses není dostupný. Windows: pip install windows-curses")
        return

    arg = sys.argv[1] if len(sys.argv) > 1 else ""

    if arg == "had":
        print("Spouštím hada... (q=quit)")
        time.sleep(0.5)
        curses.wrapper(spust_had)
    elif arg == "browser":
        startdir = sys.argv[2] if len(sys.argv) > 2 else "."
        print(f"Spouštím file browser v {startdir}...")
        time.sleep(0.3)
        curses.wrapper(spust_browser, startdir)
    elif arg == "pomodoro":
        print("Spouštím Pomodoro timer... (p=pauza, q=quit)")
        time.sleep(0.3)
        curses.wrapper(spust_pomodoro)
    elif arg == "logview":
        soubor = sys.argv[2] if len(sys.argv) > 2 else "/var/log/syslog"
        print(f"Spouštím log viewer: {soubor}...")
        time.sleep(0.3)
        curses.wrapper(spust_logviewer, soubor)
    else:
        print("Řešení lekce 100 – curses TUI aplikace\n")
        print("Použití:")
        print("  python3 100_curses.py had                     # Hra had")
        print("  python3 100_curses.py browser [adresář]       # File browser")
        print("  python3 100_curses.py pomodoro                # Pomodoro timer")
        print("  python3 100_curses.py logview <soubor>        # Log viewer")
        print()
        print("Všechny čtyři úlohy jsou implementovány v tomto souboru.")
        print("Spusť s odpovídajícím argumentem v interaktivním terminálu.")


if __name__ == "__main__":
    main()
else:
    # Při importu nebo spuštění bez terminálu (např. python3 soubor.py)
    main()
