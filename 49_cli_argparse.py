"""
LEKCE 49: CLI nástroje – argparse
===================================
Každý seriózní Python nástroj má příkazovou řádku.
argparse je vestavěný – žádná instalace.

Ukážeme si:
  Poziční argumenty, volitelné přepínače, flagy
  Subcommands (jako git commit, git push)
  Validace, výchozí hodnoty, typy
  Generování nápovědy (--help) automaticky

Na konci vyrobíme funkční CLI nástroj "pytool"
který pracuje s textem a soubory.
"""

import argparse
import sys
import json
import re
from pathlib import Path
from collections import Counter

# ══════════════════════════════════════════════════════════════
# ČÁST 1: ZÁKLAD
# ══════════════════════════════════════════════════════════════

print("=== Základ argparse ===\n")

def demo_zaklad():
    parser = argparse.ArgumentParser(
        prog="demo",
        description="Ukázkový parser",
        epilog="Více info: github.com/...",
    )

    # Poziční argument (povinný)
    parser.add_argument("jmeno",
        help="Tvoje jméno")

    # Volitelný argument s hodnotou
    parser.add_argument("-v", "--vek",
        type=int,
        default=0,
        help="Tvůj věk (výchozí: %(default)s)")

    # Flag (True/False)
    parser.add_argument("--pozdrav",
        action="store_true",
        help="Přidá pozdrav")

    # Výčet povolených hodnot
    parser.add_argument("--jazyk",
        choices=["cs", "en", "de"],
        default="cs",
        help="Jazyk pozdravu")

    # Simulace argumentů (normálně přijdou z sys.argv)
    args = parser.parse_args(["Míša", "--vek", "15", "--pozdrav", "--jazyk", "en"])

    print(f"  jmeno={args.jmeno!r}, vek={args.vek}, pozdrav={args.pozdrav}, jazyk={args.jazyk!r}")
    if args.pozdrav:
        pozdravy = {"cs": "Ahoj", "en": "Hello", "de": "Hallo"}
        print(f"  {pozdravy[args.jazyk]}, {args.jmeno}!")

demo_zaklad()


# ══════════════════════════════════════════════════════════════
# ČÁST 2: SUBCOMMANDS
# ══════════════════════════════════════════════════════════════

print("\n=== Subcommands (jako git) ===\n")

def demo_subcommands(argv):
    parser = argparse.ArgumentParser(prog="pytool")
    sub    = parser.add_subparsers(dest="prikaz", metavar="PŘÍKAZ")
    sub.required = True

    # pytool stat soubor.txt
    p_stat = sub.add_parser("stat", help="Statistika textu")
    p_stat.add_argument("soubor", type=Path, help="Vstupní soubor")
    p_stat.add_argument("-n", "--top", type=int, default=5,
                         help="Počet nejčastějších slov")

    # pytool hledej vzor soubor.txt [--ignoruj-velikost]
    p_hledej = sub.add_parser("hledej", help="Hledá regex vzor v souboru")
    p_hledej.add_argument("vzor", help="Regulární výraz")
    p_hledej.add_argument("soubor", type=Path)
    p_hledej.add_argument("-i", "--ignoruj-velikost",
                           action="store_true")

    # pytool konvert vstup.txt vystup.json [--format]
    p_konv = sub.add_parser("konvert", help="Konvertuje formát")
    p_konv.add_argument("vstup",  type=Path)
    p_konv.add_argument("vystup", type=Path)
    p_konv.add_argument("--format", choices=["json", "csv"], default="json")

    args = parser.parse_args(argv)

    if args.prikaz == "stat":
        if not args.soubor.exists():
            parser.error(f"Soubor neexistuje: {args.soubor}")
        text  = args.soubor.read_text(encoding="utf-8", errors="ignore")
        slova = re.findall(r"\b\w+\b", text.lower())
        print(f"  Soubor: {args.soubor}")
        print(f"  Znaky: {len(text):,}  Slova: {len(slova):,}  Řádky: {text.count(chr(10)):,}")
        print(f"  Top {args.top} slov:")
        for slovo, n in Counter(slova).most_common(args.top):
            print(f"    {n:5d}× {slovo}")

    elif args.prikaz == "hledej":
        if not args.soubor.exists():
            parser.error(f"Soubor neexistuje: {args.soubor}")
        flags = re.IGNORECASE if args.ignoruj_velikost else 0
        text  = args.soubor.read_text(encoding="utf-8", errors="ignore")
        shody = 0
        for i, radek in enumerate(text.splitlines(), 1):
            if re.search(args.vzor, radek, flags):
                print(f"  {i:4d}: {radek}")
                shody += 1
        print(f"  --- {shody} shod ---")

    elif args.prikaz == "konvert":
        print(f"  Konvertuji {args.vstup} → {args.vystup} ({args.format})")
        print(f"  (simulace – v reálném nástroji by proběhla konverze)")

# Spuštění s různými argumenty
demo_soubor = Path("demo_text.txt")
demo_soubor.write_text(
    "Python je skvělý jazyk. Python umí vše. "
    "Naučíme se Python pořádně. Python Python Python!\n"
    "Algoritmy jsou zábavné. Rekurze je cool.",
    encoding="utf-8"
)

print("pytool stat demo_text.txt -n 3:")
demo_subcommands(["stat", "demo_text.txt", "-n", "3"])

print("\npytool hledej 'python' demo_text.txt -i:")
demo_subcommands(["hledej", "python", "demo_text.txt", "-i"])

demo_soubor.unlink()


# ══════════════════════════════════════════════════════════════
# ČÁST 3: VLASTNÍ TYPY A VALIDACE
# ══════════════════════════════════════════════════════════════

print("\n=== Vlastní typy a validace ===\n")

def kladne_cislo(hodnota: str) -> int:
    """Vlastní typ pro argparse."""
    n = int(hodnota)
    if n <= 0:
        raise argparse.ArgumentTypeError(f"{n} musí být kladné číslo")
    return n

def existujici_soubor(cesta: str) -> Path:
    p = Path(cesta)
    if not p.exists():
        raise argparse.ArgumentTypeError(f"Soubor neexistuje: {cesta}")
    return p

def ip_adresa(hodnota: str) -> str:
    if not re.fullmatch(r"\d{1,3}(\.\d{1,3}){3}", hodnota):
        raise argparse.ArgumentTypeError(f"Neplatná IP: {hodnota}")
    return hodnota

parser_val = argparse.ArgumentParser()
parser_val.add_argument("--port",    type=kladne_cislo, default=8080)
parser_val.add_argument("--workers", type=kladne_cislo, default=4)
parser_val.add_argument("--ip",      type=ip_adresa,    default="127.0.0.1")

args = parser_val.parse_args(["--port", "3000", "--ip", "192.168.1.1"])
print(f"  port={args.port}, workers={args.workers}, ip={args.ip}")

try:
    parser_val.parse_args(["--port", "-5"])
except SystemExit:
    print("  --port -5 → správně odmítnuto")

try:
    parser_val.parse_args(["--ip", "999.x.y.z"])
except SystemExit:
    print("  --ip 999.x.y.z → správně odmítnuto")


# ══════════════════════════════════════════════════════════════
# ČÁST 4: KOMPLETNÍ NÁSTROJ – pytool jako skript
# ══════════════════════════════════════════════════════════════

PYTOOL_SKRIPT = '''\
#!/usr/bin/env python3
"""pytool – Swiss-army knife pro textové soubory."""
import argparse, re, sys, json
from pathlib import Path
from collections import Counter

def cmd_stat(args):
    text  = sys.stdin.read() if args.soubor == "-" else Path(args.soubor).read_text()
    slova = re.findall(r"\\b\\w+\\b", text.lower())
    if args.json:
        import json
        print(json.dumps({"znaky": len(text), "slova": len(slova),
                          "radky": text.count("\\n"),
                          "top": dict(Counter(slova).most_common(args.top))},
                         ensure_ascii=False, indent=2))
    else:
        print(f"Znaky: {len(text):,}  Slova: {len(slova):,}  Řádky: {text.count(chr(10)):,}")
        for s, n in Counter(slova).most_common(args.top):
            print(f"  {n:5d}× {s}")

def main():
    p = argparse.ArgumentParser(prog="pytool", description=__doc__)
    p.add_argument("--version", action="version", version="pytool 1.0.0")
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("stat", help="Statistika textu")
    s.add_argument("soubor", nargs="?", default="-", help="Soubor nebo - pro stdin")
    s.add_argument("-n", "--top",  type=int, default=10)
    s.add_argument("--json", action="store_true")
    s.set_defaults(func=cmd_stat)

    args = p.parse_args()
    args.func(args)

if __name__ == "__main__":
    main()
'''

Path("pytool.py").write_text(PYTOOL_SKRIPT, encoding="utf-8")
print("Vytvořen pytool.py")
print("\nPoužití:")
print("  python3 pytool.py stat soubor.txt")
print("  python3 pytool.py stat soubor.txt --json")
print("  cat soubor.txt | python3 pytool.py stat -")
print("  python3 pytool.py --help")

Path("pytool.py").unlink()

print("""
=== Kdy argparse vs alternativy ===

  argparse  – vestavěný, dostačující pro většinu nástrojů ✓
  click     – dekorátory, příjemnější API (pip install click)
  typer     – click + type hints, automaticky z funkce
  docopt    – popis v docstringu → automatický parser
""")

# TVOJE ÚLOHA:
# 1. Přidej do pytool subcommand "hledej vzor soubor" s výpisem řádků.
# 2. Přidej --verbose / --quiet flagy které mění úroveň loggingu.
# 3. Napiš CLI pro nákupní seznam z lekce 7 (přidat/odebrat/vypsat/uložit).
