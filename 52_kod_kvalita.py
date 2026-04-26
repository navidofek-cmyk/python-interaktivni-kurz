"""
LEKCE 52: Kvalita kódu – black, ruff, mypy
============================================
Nástroje které automaticky opraví nebo odhalí problémy.

black   – automatický formátovač (žádné diskuze o stylu)
ruff    – linter + formátovač v Rustu, extrémně rychlý
mypy    – statická typová kontrola
pylint  – komplexní linter (starší)
bandit  – bezpečnostní audit

Instalace:
  pip install black ruff mypy

Tato lekce ukazuje co každý nástroj dělá a jak ho nakonfigurovat.
Spustí kontroly přímo na souborech tohoto kurzu.
"""

import subprocess
import sys
import textwrap
from pathlib import Path

def spust(cmd: list[str], popis: str) -> tuple[int, str]:
    print(f"\n$ {' '.join(cmd)}")
    r = subprocess.run(cmd, capture_output=True, text=True)
    vystup = (r.stdout + r.stderr).strip()
    if vystup:
        for radek in vystup.splitlines()[:15]:
            print(f"  {radek}")
        if len(vystup.splitlines()) > 15:
            print(f"  ... ({len(vystup.splitlines())} řádků)")
    return r.returncode, vystup


# ══════════════════════════════════════════════════════════════
# ČÁST 1: Demonstrační soubor s chybami
# ══════════════════════════════════════════════════════════════

SPATNY_KOD = """\
import os,sys
import json
import re   # nevyuzity import

x=1+2
y = 3+4
z=x+y

def soucet( a,b ):
    return a+b

class mujTrida:
    def __init__(self,x,y):
        self.x=x
        self.y=y

    def vypocet(self ):
        result = self.x*self.y
        if result == True:
            return True
        else:
            return False

def spatna_bezpecnost():
    heslo = "tajneheslo123"
    vstup = input("Zadej příkaz: ")
    os.system(vstup)          # ← bezpečnostní díra!
    eval(vstup)               # ← bezpečnostní díra!

numbers = [1,2,3,4,5]
velka_list = [i for i in range(1000000)]
"""

DOBRY_KOD = """\
import os
import sys

X = 1 + 2
Y = 3 + 4
Z = X + Y


def soucet(a: int, b: int) -> int:
    return a + b


class MujTrida:
    def __init__(self, x: int, y: int) -> None:
        self.x = x
        self.y = y

    def vypocet(self) -> bool:
        return bool(self.x * self.y)


def bezpecna_funkce(hodnota: str) -> None:
    print(f"Zpracovávám: {hodnota}")


numbers = [1, 2, 3, 4, 5]
velky_range = range(1_000_000)
"""

demo_spatny = Path("demo_spatny.py")
demo_dobry  = Path("demo_dobry.py")
demo_spatny.write_text(SPATNY_KOD)
demo_dobry.write_text(DOBRY_KOD)


# ══════════════════════════════════════════════════════════════
# ČÁST 2: BLACK – formátování
# ══════════════════════════════════════════════════════════════

print("=" * 55)
print("BLACK – automatický formátovač")
print("=" * 55)
print("Black má jeden styl. Žádné volby. Žádné diskuze.")
print("'You can have any style you want, as long as it's Black.'")

spust([sys.executable, "-m", "black", "--check", "--diff",
       "demo_spatny.py"], "Kontrola stylu")

# Ukázka před/po
print("\nPřed black:")
print(textwrap.indent(SPATNY_KOD[:200], "  "))
print("\nPo black (ruční ukázka):")
print(textwrap.indent(DOBRY_KOD[:200], "  "))


# ══════════════════════════════════════════════════════════════
# ČÁST 3: RUFF – linter
# ══════════════════════════════════════════════════════════════

print("\n" + "=" * 55)
print("RUFF – ultrarychlý linter (napsaný v Rustu)")
print("=" * 55)
print("Nahrazuje: flake8, isort, pyupgrade, a dalších 50 nástrojů.")

spust([sys.executable, "-m", "ruff", "check", "demo_spatny.py"], "Linting")
spust([sys.executable, "-m", "ruff", "check", "--fix", "--diff",
       "demo_spatny.py"], "Auto-fix")

# Konfigurace v pyproject.toml
RUFF_CONFIG = """\
[tool.ruff]
line-length = 88
target-version = "py311"

[tool.ruff.lint]
select = [
    "E",   # pycodestyle errors
    "W",   # pycodestyle warnings
    "F",   # pyflakes
    "I",   # isort
    "N",   # pep8-naming
    "UP",  # pyupgrade
    "B",   # flake8-bugbear
    "S",   # flake8-bandit (bezpečnost)
    "RUF", # ruff-specific
]
ignore = ["S101"]  # assert je ok v testech

[tool.ruff.lint.per-file-ignores]
"tests/**" = ["S"]  # bezpečnostní pravidla přeskakuj v testech
"""
print("\npyproject.toml konfigurace:")
print(textwrap.indent(RUFF_CONFIG, "  "))


# ══════════════════════════════════════════════════════════════
# ČÁST 4: MYPY – typová kontrola
# ══════════════════════════════════════════════════════════════

print("\n" + "=" * 55)
print("MYPY – statická typová kontrola")
print("=" * 55)
print("Odhalí typové chyby před spuštěním programu.")

MYPY_DEMO = """\
def pozdrav(jmeno: str) -> str:
    return f"Ahoj, {jmeno}!"

def secti(a: int, b: int) -> int:
    return a + b

# Typové chyby:
vysledek: int = pozdrav("Míša")   # str → int: chyba!
cislo = secti("5", 10)             # str místo int: chyba!

seznam: list[int] = [1, 2, "tři"] # str v list[int]: chyba!
"""

mypy_soubor = Path("demo_mypy.py")
mypy_soubor.write_text(MYPY_DEMO)

spust([sys.executable, "-m", "mypy", "demo_mypy.py", "--strict"], "Typová kontrola")

MYPY_CONFIG = """\
[tool.mypy]
python_version = "3.11"
strict = true          # nejpřísnější nastavení
warn_return_any = true
disallow_untyped_defs = true

[[tool.mypy.overrides]]
module = ["requests.*", "bs4.*"]
ignore_missing_imports = true  # pro knihovny bez stubs
"""
print("\nmypy konfigurace v pyproject.toml:")
print(textwrap.indent(MYPY_CONFIG, "  "))


# ══════════════════════════════════════════════════════════════
# ČÁST 5: Pre-commit hooks
# ══════════════════════════════════════════════════════════════

print("\n" + "=" * 55)
print("PRE-COMMIT – automatická kontrola před každým commitem")
print("=" * 55)

PRECOMMIT_CONFIG = """\
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-json
      - id: check-merge-conflict
      - id: debug-statements    # odhalí zapomenuté breakpoint()

  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.1.0
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.7.0
    hooks:
      - id: mypy
        args: [--strict]
"""

precommit_soubor = Path(".pre-commit-config.yaml")
precommit_soubor.write_text(PRECOMMIT_CONFIG)
print(f"  Vytvořen .pre-commit-config.yaml")
print("\nInstalace a použití:")
print("  pip install pre-commit")
print("  pre-commit install    # jednou po klonování repozitáře")
print("  pre-commit run --all-files  # ručně na všechny soubory")
print("  git commit ...        # automaticky spustí hooky")


# ══════════════════════════════════════════════════════════════
# ČÁST 6: Souhrn – doporučené nastavení projektu
# ══════════════════════════════════════════════════════════════

PYPROJECT_TEMPLATE = """\
[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.backends.legacy:build"

[project]
name = "muj-projekt"
version = "0.1.0"
requires-python = ">=3.11"

[project.optional-dependencies]
dev = [
    "black>=23",
    "ruff>=0.1",
    "mypy>=1.5",
    "pytest>=7",
    "pytest-cov>=4",
    "pre-commit>=3",
]

[tool.black]
line-length = 88
target-version = ["py311"]

[tool.ruff]
line-length = 88
[tool.ruff.lint]
select = ["E", "W", "F", "I", "N", "UP", "B"]

[tool.mypy]
strict = true

[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "--cov=src --cov-report=term-missing"
"""

print("\n=== Kompletní pyproject.toml template ===")
print(textwrap.indent(PYPROJECT_TEMPLATE, "  "))

# Úklid
for f in ["demo_spatny.py", "demo_dobry.py", "demo_mypy.py"]:
    Path(f).unlink(missing_ok=True)

# TVOJE ÚLOHA:
# 1. Spusť `python -m ruff check 01_ahoj_svete.py` – co najde?
# 2. Přidej mypy type hints do lekce 8 (funkce) a spusť mypy.
# 3. Nainstaluj pre-commit a spusť na celém kurzu.
