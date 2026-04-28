"""Reseni – Lekce 45: Packaging – vlastni Python balicek"""

import subprocess
import sys
import textwrap
from pathlib import Path

# Balicek demo je generovan ve slozce balicek_reseni/
BALIK_DIR = Path("balicek_reseni")

print("=== Reseni: Rozsireni pytexttools o obrat_slova + CLI ===\n")


# 1. Pridat funkci obrat_slova(text) a test

soubory = {
    "pyproject.toml": """
        [build-system]
        requires      = ["setuptools>=68", "wheel"]
        build-backend = "setuptools.backends.legacy:build"

        [project]
        name        = "pytexttools-reseni"
        version     = "0.2.0"
        description = "Nastroje pro praci s textem – rozsireny balicek"
        readme      = "README.md"
        requires-python = ">=3.11"
        dependencies = []

        [project.scripts]
        pytexttools2 = "pytexttools2.cli:main"

        [tool.setuptools.packages.find]
        where = ["src"]
    """,

    "src/pytexttools2/__init__.py": """
        \"\"\"pytexttools2 – rozsirene nastroje pro praci s textem.\"\"\"
        from .core import (
            je_palindrom,
            pocet_slov,
            nejcastejsi_slova,
            slug,
            obrat_slova,
        )

        __version__ = "0.2.0"
        __all__ = [
            "je_palindrom", "pocet_slov", "nejcastejsi_slova",
            "slug", "obrat_slova",
        ]
    """,

    "src/pytexttools2/core.py": """
        \"\"\"Hlavni logika.\"\"\"
        import re
        import unicodedata
        from collections import Counter


        def je_palindrom(text: str) -> bool:
            \"\"\"True pokud je text palindrom (ignoruje mezery a velikost).\"\"\"
            cisty = re.sub(r"\\W", "", text.lower())
            return cisty == cisty[::-1]


        def pocet_slov(text: str) -> int:
            \"\"\"Pocet slov v textu.\"\"\"
            return len(text.split())


        def nejcastejsi_slova(text: str, n: int = 5) -> list[tuple[str, int]]:
            \"\"\"Vrati n nejcastejsich slov jako [(slovo, pocet), ...].\"\"\"
            slova = re.findall(r"\\b\\w+\\b", text.lower())
            return Counter(slova).most_common(n)


        def slug(text: str) -> str:
            \"\"\"Prevede text na URL-bezpecny slug.\"\"\"
            norm = unicodedata.normalize("NFD", text)
            ascii_text = "".join(c for c in norm if unicodedata.category(c) != "Mn")
            return re.sub(r"[^a-z0-9]+", "-", ascii_text.lower()).strip("-")


        def obrat_slova(text: str) -> str:
            \"\"\"Obrati poradi slov v textu.
            Priklad: 'Ahoj svete Python' -> 'Python svete Ahoj'
            \"\"\"
            return " ".join(reversed(text.split()))
    """,

    "src/pytexttools2/cli.py": """
        \"\"\"Command-line interface.\"\"\"
        import argparse
        from . import je_palindrom, nejcastejsi_slova, slug, obrat_slova


        def main() -> None:
            parser = argparse.ArgumentParser(
                prog="pytexttools2",
                description="Nastroje pro praci s textem (v2)",
            )
            sub = parser.add_subparsers(dest="prikaz", required=True)

            # palindrom
            p1 = sub.add_parser("palindrom", help="Zkontroluje palindrom")
            p1.add_argument("text")

            # frekvence
            p2 = sub.add_parser("frekvence", help="Nejcastejsi slova")
            p2.add_argument("text")
            p2.add_argument("-n", type=int, default=5)

            # slug
            p3 = sub.add_parser("slug", help="Vytvori URL slug")
            p3.add_argument("text")

            # Ukol 2: novy subcommand 'obrat'
            p4 = sub.add_parser("obrat", help="Obrati poradi slov")
            p4.add_argument("text")

            args = parser.parse_args()

            if args.prikaz == "palindrom":
                vysl = je_palindrom(args.text)
                print(f"{'Palindrom' if vysl else 'Neni palindrom'}: {args.text!r}")

            elif args.prikaz == "frekvence":
                for slovo, pocet in nejcastejsi_slova(args.text, args.n):
                    print(f"  {pocet:4d}x {slovo}")

            elif args.prikaz == "slug":
                print(slug(args.text))

            elif args.prikaz == "obrat":
                print(obrat_slova(args.text))


        if __name__ == "__main__":
            main()
    """,

    "tests/__init__.py": "",

    "tests/test_core.py": """
        import pytest
        from pytexttools2 import je_palindrom, pocet_slov, slug, obrat_slova


        @pytest.mark.parametrize("text,ocekavano", [
            ("racecar", True),
            ("Radar",   True),
            ("python",  False),
        ])
        def test_je_palindrom(text: str, ocekavano: bool) -> None:
            assert je_palindrom(text) == ocekavano


        def test_pocet_slov() -> None:
            assert pocet_slov("ahoj svete") == 2
            assert pocet_slov("") == 0


        def test_slug() -> None:
            assert slug("Python 3.12") == "python-3-12"


        # Ukol 1: Test pro obrat_slova
        @pytest.mark.parametrize("text,ocekavano", [
            ("Ahoj svete Python", "Python svete Ahoj"),
            ("jedno", "jedno"),
            ("a b c", "c b a"),
            ("", ""),
        ])
        def test_obrat_slova(text: str, ocekavano: str) -> None:
            assert obrat_slova(text) == ocekavano
    """,

    "README.md": "# pytexttools2\n\nRozsireny textovy balicek s funkci obrat_slova.\n",
}

# Vytvor soubory
for cesta_str, obsah in soubory.items():
    cesta = BALIK_DIR / cesta_str
    cesta.parent.mkdir(parents=True, exist_ok=True)
    cesta.write_text(textwrap.dedent(obsah).lstrip(), encoding="utf-8")
    print(f"  OK {BALIK_DIR}/{cesta_str}")

# Instalace
print(f"\n=== Instalace balicku ===\n")
result = subprocess.run(
    [sys.executable, "-m", "pip", "install", "-e", str(BALIK_DIR), "-q"],
    capture_output=True, text=True,
)
if result.returncode == 0:
    print("  Balicek nainstalovan!")
else:
    print(f"  Chyba: {result.stderr[:300]}")

# Test importu a funkce obrat_slova
print("\n=== Test importu ===\n")
try:
    import importlib
    pt = importlib.import_module("pytexttools2")

    testcases = [
        ("je_palindrom('racecar')", pt.je_palindrom("racecar")),
        ("slug('Ahoj Svete!')",     pt.slug("Ahoj Svete!")),
        ("obrat_slova('a b c')",    pt.obrat_slova("a b c")),
        ("obrat_slova('Ahoj svete Python')", pt.obrat_slova("Ahoj svete Python")),
    ]
    for popis, vysledek in testcases:
        print(f"  {popis:<45} = {vysledek!r}")

except ImportError as e:
    print(f"  Import selhal: {e}")

# Spusteni testu
print(f"\n=== pytest ===\n")
result = subprocess.run(
    [sys.executable, "-m", "pytest", str(BALIK_DIR / "tests"), "-v", "--tb=short"],
    capture_output=True, text=True,
)
for radek in result.stdout.split("\n"):
    if radek.strip():
        print(f"  {radek}")

# Uklid (volitelny)
import shutil
shutil.rmtree(BALIK_DIR, ignore_errors=True)
print("\nDemo slozka uklizena.")

# 3. Ukol 3 – mypy --strict typy jsou pridan v core.py vyse (return type anotace)
print("""
=== Ukol 3: mypy --strict ===

  Vsechny funkce v core.py maji return type anotace:
    def je_palindrom(text: str) -> bool:
    def pocet_slov(text: str) -> int:
    def nejcastejsi_slova(text: str, n: int = 5) -> list[tuple[str, int]]:
    def slug(text: str) -> str:
    def obrat_slova(text: str) -> str:

  Spusteni:
    mypy src/ --strict
""")
