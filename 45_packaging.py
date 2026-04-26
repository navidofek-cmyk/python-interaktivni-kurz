"""
LEKCE 45: Packaging – vlastní Python balíček
=============================================
Jak zabalit kód tak aby ho šlo:
  pip install ./muj_balicek
  pip install muj_balicek (z PyPI)
  importovat kdekoliv

Soubory potřebné pro moderní balíček (PEP 517/518):
  pyproject.toml  – vše v jednom (build systém, metadata, závislosti)
  src/nazev/      – zdrojový kód v src/ layoutu
  README.md       – dokumentace
  tests/          – testy

Tato lekce VYGENERUJE funkční balíček ve složce ./balicek_demo/
a ukáže jak ho nainstalovat a použít.
"""

import subprocess
import sys
from pathlib import Path
import textwrap

BALIK_DIR = Path("balicek_demo")

# ══════════════════════════════════════════════════════════════
# ČÁST 1: STRUKTURA BALÍČKU
# ══════════════════════════════════════════════════════════════

print("=== Generuji strukturu balíčku ===\n")

soubory = {
    # pyproject.toml – jediný konfigurační soubor
    "pyproject.toml": """
        [build-system]
        requires      = ["setuptools>=68", "wheel"]
        build-backend = "setuptools.backends.legacy:build"

        [project]
        name        = "pytexttools"
        version     = "0.1.0"
        description = "Nástroje pro práci s textem – ukázkový balíček"
        readme      = "README.md"
        requires-python = ">=3.11"
        license     = {text = "MIT"}
        authors     = [{name = "Míša Nováková", email = "misa@example.com"}]
        keywords    = ["text", "tools", "czech"]
        classifiers = [
            "Programming Language :: Python :: 3",
            "License :: OSI Approved :: MIT License",
        ]
        dependencies = []   # žádné externí závislosti

        [project.optional-dependencies]
        dev = ["pytest>=7", "mypy>=1.0"]

        [project.scripts]
        pytexttools = "pytexttools.cli:main"

        [tool.setuptools.packages.find]
        where = ["src"]

        [tool.mypy]
        strict = true

        [tool.pytest.ini_options]
        testpaths = ["tests"]
    """,

    # Zdrojový kód
    "src/pytexttools/__init__.py": """
        \"\"\"pytexttools – nástroje pro práci s textem.\"\"\"
        from .core import (
            je_palindrom,
            pocet_slov,
            nejcastejsi_slova,
            slug,
        )

        __version__ = "0.1.0"
        __all__ = ["je_palindrom", "pocet_slov", "nejcastejsi_slova", "slug"]
    """,

    "src/pytexttools/core.py": """
        \"\"\"Hlavní logika.\"\"\"
        import re
        import unicodedata
        from collections import Counter

        def je_palindrom(text: str) -> bool:
            \"\"\"True pokud je text palindrom (ignoruje mezery a velikost).\"\"\"
            cistý = re.sub(r"\\W", "", text.lower())
            return cistý == cistý[::-1]

        def pocet_slov(text: str) -> int:
            \"\"\"Počet slov v textu.\"\"\"
            return len(text.split())

        def nejcastejsi_slova(text: str, n: int = 5) -> list[tuple[str, int]]:
            \"\"\"Vrátí n nejčastějších slov jako [(slovo, počet), ...].\"\"\"
            slova = re.findall(r"\\b\\w+\\b", text.lower())
            return Counter(slova).most_common(n)

        def slug(text: str) -> str:
            \"\"\"Převede text na URL-bezpečný slug.
            Příklad: 'Ahoj Světe!' → 'ahoj-svete'
            \"\"\"
            norm = unicodedata.normalize("NFD", text)
            ascii_text = "".join(c for c in norm if unicodedata.category(c) != "Mn")
            return re.sub(r"[^a-z0-9]+", "-", ascii_text.lower()).strip("-")
    """,

    "src/pytexttools/cli.py": """
        \"\"\"Command-line interface.\"\"\"
        import argparse
        import sys
        from . import je_palindrom, nejcastejsi_slova, slug

        def main() -> None:
            parser = argparse.ArgumentParser(
                prog="pytexttools",
                description="Nástroje pro práci s textem",
            )
            sub = parser.add_subparsers(dest="prikaz", required=True)

            # pytexttools palindrom "racecar"
            p1 = sub.add_parser("palindrom", help="Zkontroluje palindrom")
            p1.add_argument("text")

            # pytexttools frekvence "text..." -n 3
            p2 = sub.add_parser("frekvence", help="Nejčastější slova")
            p2.add_argument("text")
            p2.add_argument("-n", type=int, default=5)

            # pytexttools slug "Ahoj Světe!"
            p3 = sub.add_parser("slug", help="Vytvoří URL slug")
            p3.add_argument("text")

            args = parser.parse_args()

            if args.prikaz == "palindrom":
                vysl = je_palindrom(args.text)
                print(f"{'✓ Palindrom' if vysl else '✗ Není palindrom'}: {args.text!r}")

            elif args.prikaz == "frekvence":
                for slovo, pocet in nejcastejsi_slova(args.text, args.n):
                    print(f"  {pocet:4d}× {slovo}")

            elif args.prikaz == "slug":
                print(slug(args.text))

        if __name__ == "__main__":
            main()
    """,

    # Testy
    "tests/__init__.py": "",

    "tests/test_core.py": """
        import pytest
        from pytexttools import je_palindrom, pocet_slov, nejcastejsi_slova, slug

        @pytest.mark.parametrize("text,ocekavano", [
            ("racecar", True),
            ("Radar",   True),
            ("A man a plan a canal Panama", True),
            ("python",  False),
            ("",        True),
        ])
        def test_je_palindrom(text, ocekavano):
            assert je_palindrom(text) == ocekavano

        def test_pocet_slov():
            assert pocet_slov("ahoj světe")    == 2
            assert pocet_slov("  mezery  ")     == 1
            assert pocet_slov("")               == 0

        def test_slug():
            assert slug("Ahoj Světe!") == "ahoj-svete"
            assert slug("Python 3.12") == "python-3-12"
            assert slug("  spaces  ")  == "spaces"

        def test_nejcastejsi():
            text = "a b a c a b"
            top = nejcastejsi_slova(text, 2)
            assert top[0] == ("a", 3)
            assert top[1] == ("b", 2)
    """,

    "README.md": """
        # pytexttools

        Nástroje pro práci s textem. Ukázkový Python balíček.

        ## Instalace

        ```bash
        pip install -e .
        ```

        ## Použití

        ```python
        from pytexttools import je_palindrom, slug

        print(je_palindrom("racecar"))  # True
        print(slug("Ahoj Světe!"))      # ahoj-svete
        ```

        ## CLI

        ```bash
        pytexttools palindrom "racecar"
        pytexttools frekvence "ahoj světe ahoj" -n 2
        pytexttools slug "Ahoj Světe!"
        ```
    """,
}

# Vytvoř soubory
for cesta_str, obsah in soubory.items():
    cesta = BALIK_DIR / cesta_str
    cesta.parent.mkdir(parents=True, exist_ok=True)
    cesta.write_text(textwrap.dedent(obsah).lstrip(), encoding="utf-8")
    print(f"  ✓ {BALIK_DIR}/{cesta_str}")

# ══════════════════════════════════════════════════════════════
# ČÁST 2: INSTALACE A OTESTOVÁNÍ
# ══════════════════════════════════════════════════════════════

print(f"\n=== Instalace balíčku (pip install -e) ===\n")

result = subprocess.run(
    [sys.executable, "-m", "pip", "install", "-e", str(BALIK_DIR), "-q"],
    capture_output=True, text=True
)
if result.returncode == 0:
    print("  Balíček nainstalován!")
else:
    print(f"  Chyba: {result.stderr[:300]}")

# Importuj a otestuj
print("\n=== Test importu ===\n")
try:
    import importlib
    pt = importlib.import_module("pytexttools")

    testcases = [
        ("je_palindrom('racecar')",    pt.je_palindrom("racecar")),
        ("je_palindrom('python')",     pt.je_palindrom("python")),
        ("slug('Ahoj Světe!')",        pt.slug("Ahoj Světe!")),
        ("pocet_slov('ahoj světe')",   pt.pocet_slov("ahoj světe")),
    ]
    for popis, vysledek in testcases:
        print(f"  {popis:<40} = {vysledek!r}")

    print(f"\n  Nejčastější slova v 'a b a c a b':")
    for slovo, pocet in pt.nejcastejsi_slova("a b a c a b"):
        print(f"    {pocet}× {slovo!r}")

except ImportError as e:
    print(f"  Import selhal: {e}")

# ══════════════════════════════════════════════════════════════
# ČÁST 3: SPUŠTĚNÍ TESTŮ
# ══════════════════════════════════════════════════════════════

print(f"\n=== pytest ===\n")
result = subprocess.run(
    [sys.executable, "-m", "pytest", str(BALIK_DIR / "tests"), "-v", "--tb=short"],
    capture_output=True, text=True
)
for radek in result.stdout.split("\n"):
    if radek.strip():
        print(f"  {radek}")

# ══════════════════════════════════════════════════════════════
# ČÁST 4: PŘEHLED PŘÍKAZŮ
# ══════════════════════════════════════════════════════════════

print(f"""
=== Užitečné příkazy ===

  # Vývoj – editable install (změny se projeví okamžitě)
  pip install -e ./balicek_demo

  # Build distribučního balíčku
  pip install build
  python -m build ./balicek_demo
  # → vytvoří dist/*.whl a dist/*.tar.gz

  # Nahrát na PyPI (potřebuješ účet)
  pip install twine
  twine upload dist/*

  # Zkontrolovat typy
  mypy src/

  # Spustit testy
  pytest tests/ -v

  # Zobraz nainstalované balíčky
  pip list
  pip show pytexttools

  # Odinstaluj
  pip uninstall pytexttools
""")

# TVOJE ÚLOHA:
# 1. Přidej do pytexttools funkci obrát_slova(text) a napiš pro ni test.
# 2. Přidej nový CLI subcommand 'obrát'.
# 3. Napiš setup pro mypy --strict a oprav typové chyby (hint: přidej -> typy).
# 4. Vytvoř vlastní balíček ze svého oblíbeného kódu z tohoto kurzu.
