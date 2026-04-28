"""
LEKCE 101: cmd – interaktivní CLI shell
========================================
Naučíš se vytvářet vlastní interaktivní příkazový shell
pomocí vestavěného modulu cmd.Cmd.

cmd.Cmd = framework pro REPL (Read-Eval-Print Loop) shelly
  – jako Python REPL, SQLite CLI, debugger pdb, ...
  – automat. nápověda (help), autocomplete (Tab), historie
  – stačí podtřídit Cmd a přidat metody do_*

Jak to funguje:
  1. cmdloop() čte vstup od uživatele
  2. Parsuje první slovo = příkaz
  3. Volá do_<prikaz>(args) metodu
  4. do_help() generuje nápovědu z docstringů
  5. default() = neznámý příkaz

Klíčové atributy/metody:
  prompt       – text výzvy (default: "(Cmd) ")
  intro        – uvítací zpráva
  do_*()       – handler pro příkaz
  help_*()     – vlastní nápověda (nebo použij docstring)
  complete_*() – autocomplete pro příkaz
  default()    – neznámý příkaz
  emptyline()  – prázdný vstup (default: opakuj poslední)
  precmd()     – hook před příkazem
  postcmd()    – hook po příkazu
"""

import cmd
import sys
import os
import glob
import time
import readline
import textwrap
from pathlib import Path
from datetime import datetime

print("=== LEKCE 101: cmd – interaktivní CLI shell ===\n")

# ══════════════════════════════════════════════════════════════
# ČÁST 1: Základní příklad – minimální Cmd shell
# ══════════════════════════════════════════════════════════════

print("── Část 1: Základní Cmd shell (kód) ──\n")

ZAKLADNI_KOD = '''\
import cmd

class MujShell(cmd.Cmd):
    intro  = "Vítej v MujShell! Piš 'help' pro nápovědu."
    prompt = "(muj) "

    def do_ahoj(self, arg):
        """Pozdraví tě. Použití: ahoj [jmeno]"""
        jmeno = arg.strip() or "světe"
        print(f"Ahoj, {jmeno}!")

    def do_secti(self, arg):
        """Sečte čísla. Použití: secti 3 5 7"""
        try:
            cisla = [float(x) for x in arg.split()]
            print(f"Součet: {sum(cisla)}")
        except ValueError:
            print("Chyba: zadej čísla oddělená mezerami")

    def do_quit(self, arg):
        """Ukončí shell."""
        print("Nashledanou!")
        return True   # ← True = ukončí cmdloop()

    # Alias pro q
    do_q = do_quit

    def emptyline(self):
        pass  # prázdný Enter – nic nedělej (default by opakoval poslední)

    def default(self, line):
        print(f"Neznámý příkaz: {line!r}. Zkus 'help'.")

if __name__ == "__main__":
    MujShell().cmdloop()
'''

for radek in ZAKLADNI_KOD.splitlines():
    print(f"  {radek}")
print()

# ══════════════════════════════════════════════════════════════
# ČÁST 2: Autocomplete
# ══════════════════════════════════════════════════════════════

print("── Část 2: Autocomplete (Tab) ──\n")

AUTOCOMPLETE_KOD = '''\
import cmd

OVOCE = ["jablko", "hruška", "banán", "jahoda", "malina", "borůvka"]

class FruitShell(cmd.Cmd):
    prompt = "(ovoce) "

    def do_kup(self, arg):
        """Koupí ovoce. Použití: kup <ovoce>"""
        if arg in OVOCE:
            print(f"Koupeno: {arg}")
        else:
            print(f"Neznámé ovoce: {arg!r}")

    def complete_kup(self, text, line, begidx, endidx):
        """Autocomplete pro příkaz 'kup' – Tab doplní ovoce."""
        if not text:
            return OVOCE[:]
        return [o for o in OVOCE if o.startswith(text)]

    def do_seznam(self, arg):
        """Vypíše dostupné ovoce."""
        for o in OVOCE:
            print(f"  - {o}")

    def do_quit(self, arg):
        return True
'''

for radek in AUTOCOMPLETE_KOD.splitlines():
    print(f"  {radek}")
print()
print("  → Stiskni Tab po 'kup j' a shell nabídne 'jablko' nebo 'jahoda'")
print()

# ══════════════════════════════════════════════════════════════
# ČÁST 3: Interaktivní Python kurz shell
# ══════════════════════════════════════════════════════════════

print("── Část 3: Python kurz shell ──\n")

KURZ_DIR = Path(__file__).parent

class KurzShell(cmd.Cmd):
    """Interaktivní shell pro procházení Python kurzu."""

    intro = textwrap.dedent("""\
        ╔══════════════════════════════════════════════╗
        ║     PYTHON KURZ – Interaktivní Shell         ║
        ║  Příkazy: list, info, hledej, spust, help   ║
        ╚══════════════════════════════════════════════╝
        Piš 'help' pro nápovědu nebo 'list' pro lekce.
    """)
    prompt = "\033[36m(kurz)\033[0m "

    def __init__(self, kurz_dir: Path):
        super().__init__()
        self.kurz_dir = kurz_dir
        self._lekce = self._nacti_lekce()

    def _nacti_lekce(self) -> list[Path]:
        """Načte seznam lekcí setříděný podle čísla."""
        soubory = sorted(self.kurz_dir.glob("[0-9]*.py"))
        return soubory

    def _cislo_lekce(self, arg: str) -> int | None:
        """Převede argument na číslo lekce."""
        try:
            return int(arg.strip())
        except ValueError:
            return None

    def _najdi_lekci(self, cislo: int) -> Path | None:
        for p in self._lekce:
            nazev = p.stem
            if nazev.split("_")[0] == str(cislo):
                return p
        return None

    # ── do_list ──────────────────────────────────────────────

    def do_list(self, arg):
        """Vypíše seznam lekcí. Použití: list [od] [do]"""
        args = arg.split()
        od = int(args[0]) if len(args) >= 1 else 1
        do = int(args[1]) if len(args) >= 2 else 999

        print()
        vypis = 0
        for p in self._lekce:
            # Extrahuj číslo lekce
            try:
                cislo = int(p.stem.split("_")[0])
            except ValueError:
                continue
            if od <= cislo <= do:
                # Přečti první řádek docstringu (název)
                try:
                    prvni_radky = p.read_text(encoding="utf-8").splitlines()
                    nazev = ""
                    for radek in prvni_radky[1:5]:
                        radek = radek.strip().lstrip("#").strip()
                        if radek.startswith("LEKCE"):
                            nazev = radek
                            break
                except Exception:
                    nazev = p.stem
                print(f"  {cislo:>3}. {nazev or p.stem}")
                vypis += 1
        print(f"\n  Celkem: {vypis} lekcí (z {len(self._lekce)} celkem)\n")

    # ── do_info ──────────────────────────────────────────────

    def do_info(self, arg):
        """Zobrazí popis lekce. Použití: info <cislo>"""
        cislo = self._cislo_lekce(arg)
        if cislo is None:
            print("  Použití: info <číslo_lekce>")
            return
        p = self._najdi_lekci(cislo)
        if p is None:
            print(f"  Lekce {cislo} nenalezena.")
            return
        try:
            obsah = p.read_text(encoding="utf-8")
            # Vypíše docstring (první trojité uvozovky)
            if '"""' in obsah:
                zacatek = obsah.index('"""') + 3
                konec   = obsah.index('"""', zacatek)
                docstring = obsah[zacatek:konec].strip()
                print(f"\n  Soubor: {p.name}")
                print("  " + "─" * 50)
                for radek in docstring.splitlines()[:20]:
                    print(f"  {radek}")
                print()
        except Exception as e:
            print(f"  Chyba: {e}")

    # ── do_hledej ────────────────────────────────────────────

    def do_hledej(self, arg):
        """Hledá klíčové slovo v lekcích. Použití: hledej <slovo>"""
        if not arg.strip():
            print("  Použití: hledej <klíčové_slovo>")
            return
        hledane = arg.strip().lower()
        nalezeno = []
        for p in self._lekce:
            try:
                obsah = p.read_text(encoding="utf-8").lower()
                pocet = obsah.count(hledane)
                if pocet > 0:
                    nalezeno.append((pocet, p))
            except Exception:
                pass
        nalezeno.sort(reverse=True)
        print(f"\n  Výsledky hledání '{arg.strip()}':")
        if not nalezeno:
            print("  Nic nenalezeno.")
        else:
            for pocet, p in nalezeno[:10]:
                print(f"  {p.name:<35} ({pocet}× výskyt)")
        print()

    # ── do_spust ─────────────────────────────────────────────

    def do_spust(self, arg):
        """Spustí lekci. Použití: spust <cislo>"""
        cislo = self._cislo_lekce(arg)
        if cislo is None:
            print("  Použití: spust <číslo_lekce>")
            return
        p = self._najdi_lekci(cislo)
        if p is None:
            print(f"  Lekce {cislo} nenalezena.")
            return
        print(f"\n  Spouštím: python3 {p.name}\n")
        print("  " + "─" * 50)
        os.system(f'python3 "{p}"')
        print("  " + "─" * 50 + "\n")

    # ── do_stat ──────────────────────────────────────────────

    def do_stat(self, arg):
        """Zobrazí statistiky kurzu."""
        celkem_radku = 0
        celkem_bajtu = 0
        for p in self._lekce:
            try:
                text = p.read_text(encoding="utf-8")
                celkem_radku += len(text.splitlines())
                celkem_bajtu += len(text.encode("utf-8"))
            except Exception:
                pass
        print(f"\n  Statistiky kurzu:")
        print(f"    Počet lekcí:    {len(self._lekce)}")
        print(f"    Řádků kódu:     {celkem_radku:,}")
        print(f"    Velikost:       {celkem_bajtu/1024:.1f} KB")
        print(f"    Průměr/lekce:   {celkem_radku//max(len(self._lekce),1)} řádků\n")

    # ── do_cas ───────────────────────────────────────────────

    def do_cas(self, arg):
        """Zobrazí aktuální čas a datum."""
        print(f"\n  {datetime.now().strftime('%A %d.%m.%Y %H:%M:%S')}\n")

    # ── do_quit ──────────────────────────────────────────────

    def do_quit(self, arg):
        """Ukončí kurz shell."""
        print("\n  Nashledanou! Hodně štěstí s Pythonem!\n")
        return True

    do_q    = do_quit
    do_exit = do_quit
    do_bye  = do_quit

    def emptyline(self):
        pass   # prázdný Enter nic nedělá

    def default(self, line):
        print(f"  Neznámý příkaz: {line!r}")
        print("  Zkus 'help' pro seznam příkazů.\n")

    def precmd(self, line):
        """Hook před každým příkazem – přidá časové razítko do logu."""
        return line   # musí vrátit line (beze změny nebo upravené)

    # ── autocomplete ─────────────────────────────────────────

    def complete_info(self, text, line, begidx, endidx):
        cisla = []
        for p in self._lekce:
            try:
                c = str(int(p.stem.split("_")[0]))
                cisla.append(c)
            except ValueError:
                pass
        if not text:
            return cisla
        return [c for c in cisla if c.startswith(text)]

    complete_spust = complete_info

# ══════════════════════════════════════════════════════════════
# ČÁST 4: readline – historie příkazů
# ══════════════════════════════════════════════════════════════

print("── Část 4: readline – historie příkazů ──\n")

HISTORIE_KOD = '''\
import cmd, readline, os
from pathlib import Path

class ShellSHistoriei(cmd.Cmd):
    prompt = "(sh) "
    HISTORIE_SOUBOR = Path.home() / ".muj_shell_history"

    def preloop(self):
        """Načte historii při startu."""
        if self.HISTORIE_SOUBOR.exists():
            readline.read_history_file(self.HISTORIE_SOUBOR)
            print(f"  Načteno {readline.get_current_history_length()} příkazů z historie")

    def postloop(self):
        """Uloží historii při ukončení."""
        readline.write_history_file(self.HISTORIE_SOUBOR)

    def do_quit(self, arg):
        return True
'''

for radek in HISTORIE_KOD.splitlines():
    print(f"  {radek}")
print()

# ══════════════════════════════════════════════════════════════
# ČÁST 5: Spuštění kurz shellu
# ══════════════════════════════════════════════════════════════

print("── Část 5: Spuštění kurz shellu ──\n")

IS_INTERACTIVE = sys.stdin.isatty() and sys.stdout.isatty()

if IS_INTERACTIVE:
    shell = KurzShell(KURZ_DIR)

    # Ukázkové spuštění bez cmdloop – předvedeme pár příkazů
    print("  Ukázka příkazů (bez interaktivního vstupu):\n")
    print("  > list 95 101")
    shell.do_list("95 101")

    print("  > hledej tomllib")
    shell.do_hledej("tomllib")

    print("  > stat")
    shell.do_stat("")

    print()
    print("  Pro interaktivní shell spusť:")
    print("    python3 101_cmd.py --shell")
    print()

    # Pokud byl předán argument --shell, spustí skutečný shell
    if "--shell" in sys.argv:
        shell.cmdloop()
else:
    # Neinteaktivní mód – jen ukázka bez cmdloop
    shell = KurzShell(KURZ_DIR)
    print("  Ukázka (neinteaktivní mód):\n")
    print("  > list 95 101")
    shell.do_list("95 101")
    print("  > stat")
    shell.do_stat("")

# ══════════════════════════════════════════════════════════════
# TVOJE ÚLOHA:
# ══════════════════════════════════════════════════════════════
print("=" * 55)
print("TVOJE ÚLOHA:")
print("=" * 55)
print("""
1. Rozšiř KurzShell o příkaz 'zalozka' pro ukládání
   oblíbených lekcí: zalozka pridat <cislo>, zalozka
   seznam, zalozka odebrat <cislo>. Záložky persistuj
   do ~/.kurz_zalozky.json (json.dump/load).

2. Napiš TodoShell pomocí cmd.Cmd:
   Příkazy: pridat <ukol>, hotovo <id>, seznam, smazat <id>,
   filtruj <slovo>. Persistuj úkoly do shelve nebo JSON.
   Přidej autocomplete pro 'hotovo' a 'smazat' (nabídni ID).

3. Implementuj PythonREPL třídu rozšiřující cmd.Cmd, která
   příkaz 'run <kod>' spustí Python kód přes exec() a zobrazí
   výsledek. Přidej 'history' (seznam spuštěných příkazů),
   'save <soubor>' (uloží historii jako .py skript),
   'clear' (vymaže historii). Ošetři SyntaxError/RuntimeError.

4. Vytvoř FileManagerShell – příkazový správce souborů:
   ls [adresar], cd <adresar>, cp <src> <dst>, mv <src> <dst>,
   rm <soubor>, cat <soubor>, mkdir <adresar>, pwd.
   Přidej autocomplete souborů/adresářů pomocí glob.glob().
   Zobraz aktuální adresář v promptu: "(fm ~/projects) ".
""")
