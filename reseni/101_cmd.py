"""Řešení – Lekce 101: cmd – interaktivní CLI shell

Toto je vzorové řešení úloh z lekce 101.

Spuštění interaktivních shellů:
  python3 reseni/101_cmd.py kurz        # Úloha 1 – KurzShell se záložkami
  python3 reseni/101_cmd.py todo        # Úloha 2 – TodoShell
  python3 reseni/101_cmd.py repl        # Úloha 3 – PythonREPL
  python3 reseni/101_cmd.py fm [dir]    # Úloha 4 – FileManagerShell
"""

import cmd
import sys
import os
import json
import glob
import readline
import textwrap
import traceback
from pathlib import Path
from datetime import datetime

# ── Úloha 1 ────────────────────────────────────────────────
# Rozšíření KurzShell o záložky (persistované do ~/.kurz_zalozky.json).

KURZ_DIR = Path(__file__).parent.parent   # adresář s lekcemi

ZALOZKY_SOUBOR = Path.home() / ".kurz_zalozky.json"


def _nacti_zalozky() -> list[int]:
    if ZALOZKY_SOUBOR.exists():
        try:
            return json.loads(ZALOZKY_SOUBOR.read_text(encoding="utf-8"))
        except Exception:
            return []
    return []


def _uloz_zalozky(zalozky: list[int]) -> None:
    ZALOZKY_SOUBOR.write_text(json.dumps(sorted(set(zalozky))), encoding="utf-8")


class KurzShellSZalozkami(cmd.Cmd):
    """KurzShell rozšířený o záložky oblíbených lekcí."""

    intro = textwrap.dedent("""\
        ╔══════════════════════════════════════════════╗
        ║   PYTHON KURZ – Shell se záložkami           ║
        ║  Příkazy: list, info, zalozka, help, quit   ║
        ╚══════════════════════════════════════════════╝
    """)
    prompt = "\033[36m(kurz)\033[0m "

    def __init__(self, kurz_dir: Path):
        super().__init__()
        self.kurz_dir = kurz_dir
        self._lekce = sorted(kurz_dir.glob("[0-9]*.py"))
        self._zalozky: list[int] = _nacti_zalozky()

    def _cislo(self, arg: str) -> int | None:
        try:
            return int(arg.strip())
        except ValueError:
            return None

    def _najdi_lekci(self, cislo: int) -> Path | None:
        for p in self._lekce:
            try:
                if int(p.stem.split("_")[0]) == cislo:
                    return p
            except ValueError:
                pass
        return None

    def do_list(self, arg):
        """Vypíše seznam lekcí. Použití: list [od] [do]"""
        args = arg.split()
        od = int(args[0]) if len(args) >= 1 else 1
        do_ = int(args[1]) if len(args) >= 2 else 9999
        print()
        n = 0
        for p in self._lekce:
            try:
                c = int(p.stem.split("_")[0])
            except ValueError:
                continue
            if od <= c <= do_:
                zal = " ★" if c in self._zalozky else ""
                print(f"  {c:>4}. {p.stem}{zal}")
                n += 1
        print(f"\n  ({n} lekcí)\n")

    def do_zalozka(self, arg):
        """Správa záložek. Použití: zalozka pridat <cislo> | seznam | odebrat <cislo>"""
        casti = arg.strip().split(maxsplit=1)
        if not casti:
            print("  Použití: zalozka pridat <cislo> | seznam | odebrat <cislo>")
            return

        prikaz = casti[0].lower()
        if prikaz == "seznam":
            if not self._zalozky:
                print("  Žádné záložky.")
            else:
                print("  Záložky:")
                for c in sorted(self._zalozky):
                    p = self._najdi_lekci(c)
                    nazev = p.stem if p else str(c)
                    print(f"    ★  {c:>4}. {nazev}")
        elif prikaz == "pridat":
            cislo = self._cislo(casti[1]) if len(casti) > 1 else None
            if cislo is None:
                print("  Použití: zalozka pridat <cislo>")
                return
            if cislo not in self._zalozky:
                self._zalozky.append(cislo)
                _uloz_zalozky(self._zalozky)
                print(f"  Záložka {cislo} přidána.")
            else:
                print(f"  Záložka {cislo} už existuje.")
        elif prikaz == "odebrat":
            cislo = self._cislo(casti[1]) if len(casti) > 1 else None
            if cislo is None:
                print("  Použití: zalozka odebrat <cislo>")
                return
            if cislo in self._zalozky:
                self._zalozky.remove(cislo)
                _uloz_zalozky(self._zalozky)
                print(f"  Záložka {cislo} odebrána.")
            else:
                print(f"  Záložka {cislo} neexistuje.")
        else:
            print(f"  Neznámý podpříkaz: {prikaz!r}")

    def do_quit(self, arg):
        """Ukončí shell."""
        print("\n  Nashledanou!\n")
        return True

    do_q = do_quit
    do_exit = do_quit

    def emptyline(self):
        pass

    def default(self, line):
        print(f"  Neznámý příkaz: {line!r}. Zkus 'help'.\n")


# ── Úloha 2 ────────────────────────────────────────────────
# TodoShell – správce úkolů s persistencí do JSON.

TODO_SOUBOR = Path.home() / ".kurz_todo.json"


def _nacti_todo() -> list[dict]:
    if TODO_SOUBOR.exists():
        try:
            return json.loads(TODO_SOUBOR.read_text(encoding="utf-8"))
        except Exception:
            return []
    return []


def _uloz_todo(ukoly: list[dict]) -> None:
    TODO_SOUBOR.write_text(json.dumps(ukoly, ensure_ascii=False, indent=2), encoding="utf-8")


class TodoShell(cmd.Cmd):
    """Shell pro správu úkolů (TODO list)."""

    intro = textwrap.dedent("""\
        ╔══════════════════════════════════════════════╗
        ║   TODO Shell                                  ║
        ║  pridat, seznam, hotovo, smazat, filtruj     ║
        ╚══════════════════════════════════════════════╝
    """)
    prompt = "\033[33m(todo)\033[0m "

    def __init__(self):
        super().__init__()
        self._ukoly: list[dict] = _nacti_todo()
        self._next_id = max((u["id"] for u in self._ukoly), default=0) + 1

    def _uloz(self):
        _uloz_todo(self._ukoly)

    def _aktivni_ids(self) -> list[str]:
        return [str(u["id"]) for u in self._ukoly if not u.get("hotovo")]

    def do_pridat(self, arg):
        """Přidá nový úkol. Použití: pridat <text úkolu>"""
        if not arg.strip():
            print("  Použití: pridat <text>")
            return
        ukol = {
            "id":      self._next_id,
            "text":    arg.strip(),
            "hotovo":  False,
            "vytvoreno": datetime.now().isoformat(timespec="seconds"),
        }
        self._ukoly.append(ukol)
        self._next_id += 1
        self._uloz()
        print(f"  [+] #{ukol['id']}: {ukol['text']}")

    def do_seznam(self, arg):
        """Zobrazí všechny úkoly."""
        if not self._ukoly:
            print("  Žádné úkoly.")
            return
        for u in self._ukoly:
            stav = "✓" if u.get("hotovo") else "○"
            print(f"  [{stav}] #{u['id']:>3}  {u['text']}")
        hotove = sum(1 for u in self._ukoly if u.get("hotovo"))
        print(f"\n  Celkem: {len(self._ukoly)}, hotovo: {hotove}\n")

    def do_hotovo(self, arg):
        """Označí úkol jako hotový. Použití: hotovo <id>"""
        try:
            uid = int(arg.strip())
        except ValueError:
            print("  Použití: hotovo <id>")
            return
        for u in self._ukoly:
            if u["id"] == uid:
                u["hotovo"] = True
                self._uloz()
                print(f"  [✓] Hotovo: {u['text']}")
                return
        print(f"  Úkol #{uid} nenalezen.")

    def complete_hotovo(self, text, line, begidx, endidx):
        ids = self._aktivni_ids()
        return [i for i in ids if i.startswith(text)] if text else ids

    def do_smazat(self, arg):
        """Smaže úkol. Použití: smazat <id>"""
        try:
            uid = int(arg.strip())
        except ValueError:
            print("  Použití: smazat <id>")
            return
        pred = len(self._ukoly)
        self._ukoly = [u for u in self._ukoly if u["id"] != uid]
        if len(self._ukoly) < pred:
            self._uloz()
            print(f"  [-] Úkol #{uid} smazán.")
        else:
            print(f"  Úkol #{uid} nenalezen.")

    complete_smazat = complete_hotovo

    def do_filtruj(self, arg):
        """Filtruje úkoly dle slova. Použití: filtruj <slovo>"""
        if not arg.strip():
            print("  Použití: filtruj <slovo>")
            return
        nalezene = [u for u in self._ukoly if arg.lower() in u["text"].lower()]
        if not nalezene:
            print(f"  Nic nenalezeno pro '{arg}'.")
        else:
            for u in nalezene:
                stav = "✓" if u.get("hotovo") else "○"
                print(f"  [{stav}] #{u['id']:>3}  {u['text']}")
        print()

    def do_quit(self, arg):
        """Ukončí todo shell."""
        print("\n  Nashledanou!\n")
        return True

    do_q = do_quit
    do_exit = do_quit

    def emptyline(self):
        pass

    def default(self, line):
        print(f"  Neznámý příkaz: {line!r}. Zkus 'help'.\n")


# ── Úloha 3 ────────────────────────────────────────────────
# PythonREPL – spouštění Python kódu přes exec().

class PythonREPL(cmd.Cmd):
    """Mini Python REPL s historií a ukládáním."""

    intro = textwrap.dedent("""\
        ╔══════════════════════════════════════════════╗
        ║   Python Mini REPL                            ║
        ║  run, history, save, clear, quit             ║
        ╚══════════════════════════════════════════════╝
        Příklady: run print('ahoj')   run 2+2
    """)
    prompt = "\033[32m(repl)\033[0m "

    def __init__(self):
        super().__init__()
        self._history: list[str] = []
        self._globals: dict = {"__builtins__": __builtins__}

    def do_run(self, arg):
        """Spustí Python kód. Použití: run <python_kód>"""
        if not arg.strip():
            print("  Použití: run <kód>")
            return
        self._history.append(arg)
        try:
            # Nejprve zkusíme eval (pro výrazy)
            try:
                vysledek = eval(arg, self._globals)   # noqa: S307
                if vysledek is not None:
                    print(f"  → {vysledek!r}")
            except SyntaxError:
                exec(arg, self._globals)              # noqa: S102
        except SyntaxError as e:
            print(f"  SyntaxError: {e}")
        except Exception as e:
            print(f"  {type(e).__name__}: {e}")

    def do_history(self, arg):
        """Zobrazí historii příkazů."""
        if not self._history:
            print("  Historie je prázdná.")
            return
        for i, prikaz in enumerate(self._history, 1):
            print(f"  {i:>3}. {prikaz}")

    def do_save(self, arg):
        """Uloží historii jako .py skript. Použití: save <soubor.py>"""
        soubor = arg.strip() or "repl_history.py"
        if not soubor.endswith(".py"):
            soubor += ".py"
        obsah = "\n".join(self._history) + "\n"
        Path(soubor).write_text(obsah, encoding="utf-8")
        print(f"  Historie uložena do {soubor} ({len(self._history)} příkazů).")

    def do_clear(self, arg):
        """Vymaže historii a namespace."""
        self._history.clear()
        self._globals = {"__builtins__": __builtins__}
        print("  Historie a namespace vymazány.")

    def do_quit(self, arg):
        """Ukončí REPL."""
        print("\n  Nashledanou!\n")
        return True

    do_q = do_quit
    do_exit = do_quit

    def emptyline(self):
        pass

    def default(self, line):
        # Zkusíme spustit přímo jako Python kód (bez "run" prefixu)
        self.do_run(line)


# ── Úloha 4 ────────────────────────────────────────────────
# FileManagerShell – příkazový správce souborů s autocomplete.

class FileManagerShell(cmd.Cmd):
    """Příkazový správce souborů s autocomplete."""

    def __init__(self, start_dir: str = "."):
        super().__init__()
        self._cwd = Path(start_dir).resolve()
        self._aktualizuj_prompt()

    def _aktualizuj_prompt(self):
        zkracena = str(self._cwd).replace(str(Path.home()), "~")
        self.prompt = f"\033[35m(fm {zkracena})\033[0m "

    @property
    def intro(self):
        return textwrap.dedent("""\
            ╔══════════════════════════════════════════════╗
            ║   File Manager Shell                          ║
            ║  ls  cd  cp  mv  rm  cat  mkdir  pwd  quit  ║
            ╚══════════════════════════════════════════════╝
        """)

    def _abs(self, rel: str) -> Path:
        """Převede relativní cestu na absolutní vůči cwd."""
        p = Path(rel)
        return (self._cwd / p).resolve() if not p.is_absolute() else p

    def _glob_complete(self, text: str, prefix: str = "") -> list[str]:
        """Generuje autocomplete pro soubory/adresáře."""
        vzor = str(self._cwd / (text or "*"))
        matches = glob.glob(vzor + "*")
        result = []
        for m in matches:
            p = Path(m)
            rel = p.name + ("/" if p.is_dir() else "")
            result.append(rel)
        return result

    def do_pwd(self, arg):
        """Zobrazí aktuální adresář."""
        print(f"  {self._cwd}")

    def do_ls(self, arg):
        """Výpis obsahu adresáře. Použití: ls [adresář]"""
        cil = self._abs(arg.strip()) if arg.strip() else self._cwd
        try:
            polozky = sorted(cil.iterdir(), key=lambda p: (not p.is_dir(), p.name))
            for p in polozky:
                if p.is_dir():
                    print(f"  \033[36m[D]\033[0m {p.name}/")
                else:
                    velikost = p.stat().st_size
                    print(f"  [F] {p.name:<40} {velikost:>10,} B")
            print(f"\n  ({len(polozky)} položek)\n")
        except PermissionError:
            print(f"  Přístup odepřen: {cil}")
        except FileNotFoundError:
            print(f"  Adresář nenalezen: {cil}")

    def do_cd(self, arg):
        """Změní adresář. Použití: cd <adresář>"""
        if not arg.strip():
            self._cwd = Path.home()
        elif arg.strip() == "..":
            self._cwd = self._cwd.parent
        else:
            novy = self._abs(arg.strip())
            if novy.is_dir():
                self._cwd = novy
            else:
                print(f"  Adresář nenalezen: {novy}")
                return
        self._aktualizuj_prompt()

    def do_mkdir(self, arg):
        """Vytvoří adresář. Použití: mkdir <název>"""
        if not arg.strip():
            print("  Použití: mkdir <název>")
            return
        novy = self._abs(arg.strip())
        try:
            novy.mkdir(parents=True, exist_ok=True)
            print(f"  Vytvořen: {novy}")
        except OSError as e:
            print(f"  Chyba: {e}")

    def do_cat(self, arg):
        """Zobrazí obsah souboru. Použití: cat <soubor>"""
        if not arg.strip():
            print("  Použití: cat <soubor>")
            return
        soubor = self._abs(arg.strip())
        try:
            obsah = soubor.read_text(encoding="utf-8", errors="replace")
            for i, radek in enumerate(obsah.splitlines()[:50], 1):
                print(f"  {i:>4}  {radek}")
            if len(obsah.splitlines()) > 50:
                print(f"  ... ({len(obsah.splitlines())} řádků celkem)")
        except IsADirectoryError:
            print(f"  Je to adresář, použij 'ls {arg}'.")
        except FileNotFoundError:
            print(f"  Soubor nenalezen: {soubor}")
        except OSError as e:
            print(f"  Chyba: {e}")

    def do_cp(self, arg):
        """Zkopíruje soubor. Použití: cp <src> <dst>"""
        casti = arg.split(maxsplit=1)
        if len(casti) < 2:
            print("  Použití: cp <src> <dst>")
            return
        src, dst = self._abs(casti[0]), self._abs(casti[1])
        try:
            import shutil
            shutil.copy2(src, dst)
            print(f"  Zkopírováno: {src.name} → {dst}")
        except OSError as e:
            print(f"  Chyba: {e}")

    def do_mv(self, arg):
        """Přesune/přejmenuje soubor. Použití: mv <src> <dst>"""
        casti = arg.split(maxsplit=1)
        if len(casti) < 2:
            print("  Použití: mv <src> <dst>")
            return
        src, dst = self._abs(casti[0]), self._abs(casti[1])
        try:
            src.rename(dst)
            print(f"  Přesunuto: {src.name} → {dst}")
        except OSError as e:
            print(f"  Chyba: {e}")

    def do_rm(self, arg):
        """Smaže soubor. Použití: rm <soubor>"""
        if not arg.strip():
            print("  Použití: rm <soubor>")
            return
        soubor = self._abs(arg.strip())
        try:
            soubor.unlink()
            print(f"  Smazáno: {soubor.name}")
        except IsADirectoryError:
            print(f"  Je to adresář. Pro smazání adresáře použij rmdir.")
        except FileNotFoundError:
            print(f"  Soubor nenalezen: {soubor}")
        except OSError as e:
            print(f"  Chyba: {e}")

    # Autocomplete
    def complete_cd(self, text, line, begidx, endidx):
        return [m for m in self._glob_complete(text) if m.endswith("/")]

    complete_ls  = _glob_complete
    complete_cat = _glob_complete
    complete_rm  = _glob_complete

    def do_quit(self, arg):
        """Ukončí file manager."""
        print("\n  Nashledanou!\n")
        return True

    do_q = do_quit
    do_exit = do_quit

    def emptyline(self):
        pass

    def default(self, line):
        print(f"  Neznámý příkaz: {line!r}. Zkus 'help'.\n")


# ── Hlavní spouštěcí logika ─────────────────────────────────

def ukazka_bez_interaktivity():
    """Ukázka funkčnosti bez interaktivního vstupu."""
    print("Řešení lekce 101 – cmd interaktivní CLI shelly\n")
    print("Implementované shelly:")
    print("  1. KurzShellSZalozkami – kurz shell se záložkami (zalozka pridat/seznam/odebrat)")
    print("  2. TodoShell           – správce úkolů s persistencí do ~/.kurz_todo.json")
    print("  3. PythonREPL          – mini Python REPL (run, history, save, clear)")
    print("  4. FileManagerShell    – file manager (ls, cd, cp, mv, rm, cat, mkdir, pwd)")
    print()
    print("Spuštění:")
    print("  python3 101_cmd.py kurz     # KurzShell se záložkami")
    print("  python3 101_cmd.py todo     # TodoShell")
    print("  python3 101_cmd.py repl     # PythonREPL")
    print("  python3 101_cmd.py fm [dir] # FileManagerShell")
    print()

    # Ukázka TodoShell metod bez interaktivního vstupu
    print("── Ukázka TodoShell (bez interaktivního vstupu) ──\n")
    todo = TodoShell()
    todo.do_pridat("Prostudovat lekci 101 – cmd modul")
    todo.do_pridat("Napsat vlastní shell pro projekt")
    todo.do_pridat("Projít dokumentaci cmd.Cmd")
    todo.do_seznam("")
    todo.do_hotovo("1")
    todo.do_filtruj("cmd")
    print()

    # Ukázka PythonREPL
    print("── Ukázka PythonREPL (bez interaktivního vstupu) ──\n")
    repl = PythonREPL()
    repl.do_run("x = [i**2 for i in range(5)]")
    repl.do_run("x")
    repl.do_run("sum(x)")
    repl.do_run("import math; math.pi")
    repl.do_history("")
    print()


def main():
    arg = sys.argv[1] if len(sys.argv) > 1 else ""
    is_interactive = sys.stdin.isatty() and sys.stdout.isatty()

    if arg == "kurz" and is_interactive:
        KurzShellSZalozkami(KURZ_DIR).cmdloop()
    elif arg == "todo" and is_interactive:
        TodoShell().cmdloop()
    elif arg == "repl" and is_interactive:
        PythonREPL().cmdloop()
    elif arg == "fm" and is_interactive:
        startdir = sys.argv[2] if len(sys.argv) > 2 else "."
        FileManagerShell(startdir).cmdloop()
    else:
        ukazka_bez_interaktivity()


if __name__ == "__main__":
    main()
else:
    main()
