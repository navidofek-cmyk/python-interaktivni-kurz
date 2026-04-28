"""Reseni – Lekce 49: CLI nastroje – argparse"""

import argparse
import sys
import json
import re
import logging
from pathlib import Path
from collections import Counter


# 1. Subcommand "hledej vzor soubor" s vypisem radku

print("=== Ukol 1: pytool hledej ===\n")

# Vytvor demo soubor
DEMO_SOUBOR = Path("demo_nakup.txt")
DEMO_SOUBOR.write_text(
    "jablko 5\noranges 3\nbanany 7\npython 1\npython je skvely\n",
    encoding="utf-8",
)


def cmd_stat(args: argparse.Namespace) -> None:
    text  = Path(args.soubor).read_text(encoding="utf-8")
    slova = re.findall(r"\b\w+\b", text.lower())
    print(f"  Soubor: {args.soubor}")
    print(f"  Znaky: {len(text):,}  Slova: {len(slova):,}  Radky: {text.count(chr(10)):,}")
    print(f"  Top {args.top} slov:")
    for slovo, n in Counter(slova).most_common(args.top):
        print(f"    {n:5d}x {slovo}")


def cmd_hledej(args: argparse.Namespace) -> None:
    """Ukol 1: Hledej regex vzor v souboru – vypis odpovidajici radky."""
    flagy = re.IGNORECASE if args.ignoruj_velikost else 0
    text  = Path(args.soubor).read_text(encoding="utf-8")
    shody = 0
    for i, radek in enumerate(text.splitlines(), 1):
        if re.search(args.vzor, radek, flagy):
            print(f"  {i:4d}: {radek}")
            shody += 1
    print(f"  --- {shody} shod ---")


def vytvor_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="pytool")
    # Ukol 2: --verbose / --quiet flagy
    skupinka = parser.add_mutually_exclusive_group()
    skupinka.add_argument(
        "-v", "--verbose", action="store_true",
        help="Podrobny vystup (DEBUG level)",
    )
    skupinka.add_argument(
        "-q", "--quiet", action="store_true",
        help="Tichy rezim (pouze WARNING+)",
    )

    sub = parser.add_subparsers(dest="prikaz", metavar="PRIKAZ")
    sub.required = True

    # stat
    p_stat = sub.add_parser("stat", help="Statistika textu")
    p_stat.add_argument("soubor", help="Vstupni soubor")
    p_stat.add_argument("-n", "--top", type=int, default=5)

    # hledej
    p_hledej = sub.add_parser("hledej", help="Hledej regex v souboru")
    p_hledej.add_argument("vzor",   help="Regularni vyraz")
    p_hledej.add_argument("soubor", help="Vstupni soubor")
    p_hledej.add_argument(
        "-i", "--ignoruj-velikost", action="store_true",
        help="Ignoruj velikost pismen",
    )

    return parser


# Test subcommandy
parser = vytvor_parser()

print("pytool stat demo_nakup.txt -n 3:")
args = parser.parse_args(["stat", "demo_nakup.txt", "-n", "3"])
cmd_stat(args)

print("\npytool hledej 'python' demo_nakup.txt -i:")
args = parser.parse_args(["hledej", "python", "demo_nakup.txt", "-i"])
cmd_hledej(args)

DEMO_SOUBOR.unlink()


# 2. --verbose / --quiet meni uroven loggingu

print("\n=== Ukol 2: --verbose / --quiet ===\n")


def nastav_logging_dle_args(args: argparse.Namespace) -> None:
    """Nastavi uroven loggingu dle CLI flagu."""
    if args.verbose:
        level = logging.DEBUG
    elif args.quiet:
        level = logging.WARNING
    else:
        level = logging.INFO

    logging.basicConfig(
        level=level,
        format="%(levelname)-8s %(message)s",
        stream=sys.stdout,
        force=True,
    )
    logger = logging.getLogger("pytool")
    logger.debug("Podrobny rezim zapnut")
    logger.info("Pytool spusten")
    logger.warning("Toto je varovani")


for flag, popis in [("--verbose", "verbose"), ("--quiet", "quiet"), ("", "normalni")]:
    argv = ([flag, "stat", "x.txt"] if flag else ["stat", "x.txt"])
    args_test = argparse.Namespace(
        verbose=(flag == "--verbose"),
        quiet=(flag == "--quiet"),
        prikaz="stat",
    )
    print(f"Rezim: {popis}")
    nastav_logging_dle_args(args_test)
    print()


# 3. CLI pro nakupni seznam

print("=== Ukol 3: CLI pro nakupni seznam ===\n")

SEZNAM_SOUBOR = Path("nakupni_seznam.json")


def nacti_seznam() -> list[str]:
    if SEZNAM_SOUBOR.exists():
        return json.loads(SEZNAM_SOUBOR.read_text(encoding="utf-8"))
    return []


def uloz_seznam(seznam: list[str]) -> None:
    SEZNAM_SOUBOR.write_text(json.dumps(seznam, ensure_ascii=False), encoding="utf-8")


def nakup_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="nakup", description="Nakupni seznam")
    sub = p.add_subparsers(dest="prikaz", required=True)

    pridat  = sub.add_parser("pridat",  help="Pridat polozku")
    pridat.add_argument("polozka", help="Nazev polozky")

    odebrat = sub.add_parser("odebrat", help="Odebrat polozku")
    odebrat.add_argument("polozka")

    sub.add_parser("vypsat", help="Vypsat seznam")
    sub.add_parser("smazat", help="Smazat cely seznam")

    return p


def nakup_main(argv: list[str]) -> None:
    p = nakup_parser()
    args = p.parse_args(argv)
    seznam = nacti_seznam()

    if args.prikaz == "pridat":
        seznam.append(args.polozka)
        uloz_seznam(seznam)
        print(f"  Pridano: {args.polozka!r}")

    elif args.prikaz == "odebrat":
        if args.polozka in seznam:
            seznam.remove(args.polozka)
            uloz_seznam(seznam)
            print(f"  Odebrano: {args.polozka!r}")
        else:
            print(f"  Polozka {args.polozka!r} nenalezena")

    elif args.prikaz == "vypsat":
        if seznam:
            print(f"  Nakupni seznam ({len(seznam)} polozek):")
            for i, p in enumerate(seznam, 1):
                print(f"    {i}. {p}")
        else:
            print("  Seznam je prazdny")

    elif args.prikaz == "smazat":
        uloz_seznam([])
        print("  Seznam smazan")


# Demo nakupniho seznamu
for akce in [
    ["pridat", "jablka"],
    ["pridat", "mleko"],
    ["pridat", "chleb"],
    ["vypsat"],
    ["odebrat", "mleko"],
    ["vypsat"],
    ["smazat"],
]:
    print(f"nakup {' '.join(akce)}:")
    nakup_main(akce)

SEZNAM_SOUBOR.unlink(missing_ok=True)
