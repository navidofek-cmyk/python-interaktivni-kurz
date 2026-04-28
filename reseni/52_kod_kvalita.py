"""Reseni – Lekce 52: Kvalita kodu – black, ruff, mypy"""

import subprocess
import sys
import textwrap
from pathlib import Path


def spust(cmd: list[str]) -> tuple[int, str]:
    print(f"\n$ {' '.join(cmd)}")
    r = subprocess.run(cmd, capture_output=True, text=True)
    vystup = (r.stdout + r.stderr).strip()
    if vystup:
        for radek in vystup.splitlines()[:12]:
            print(f"  {radek}")
    return r.returncode, vystup


# 1. Spust ruff check na 01_ahoj_svete.py

print("=== Ukol 1: ruff check na prvni lekci ===\n")

lekce_01 = Path("../01_ahoj_svete.py")
if not lekce_01.exists():
    lekce_01 = Path("/home/ivand/projects/learning_python/interactive/01_ahoj_svete.py")

if lekce_01.exists():
    kod, vystup = spust([sys.executable, "-m", "ruff", "check", str(lekce_01)])
    if kod == 0:
        print("  Zadne nalezene problémy!")
    else:
        print(f"\n  Ruff nasel problemy v {lekce_01.name}")
else:
    print("  Soubor 01_ahoj_svete.py nenalezen – preskakuji")


# 2. Pridat mypy type hints do jednoduche funkce

print("\n=== Ukol 2: mypy type hints ===\n")

TYPED_FUNKCE = Path("_typed_funkce.py")
TYPED_FUNKCE.write_text("""\
def pozdrav(jmeno: str, pocet: int = 1) -> str:
    return (jmeno + "! ") * pocet


def secti(a: int, b: int) -> int:
    return a + b


def prumer(cisla: list[float]) -> float:
    if not cisla:
        return 0.0
    return sum(cisla) / len(cisla)


def najdi(seznam: list[str], hledat: str) -> int | None:
    try:
        return seznam.index(hledat)
    except ValueError:
        return None
""", encoding="utf-8")

kod, vystup = spust([sys.executable, "-m", "mypy", str(TYPED_FUNKCE)])
if kod == 0:
    print("  mypy: vsechny typy jsou spravne!")
TYPED_FUNKCE.unlink(missing_ok=True)


# 3. Ukazka pre-commit konfigurace

print("\n=== Ukol 3: pre-commit konfigurace ===\n")

PRECOMMIT_YAML = """\
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-json
      - id: debug-statements

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
        additional_dependencies: [pydantic, types-requests]
"""

print("Vzorova .pre-commit-config.yaml:")
print(textwrap.indent(PRECOMMIT_YAML, "  "))

# Ukaz jak nainstalovat
print("Instalace a spusteni:")
print("  pip install pre-commit")
print("  pre-commit install          # jednou po clonu")
print("  pre-commit run --all-files  # okamzite na vsechno")
print("  git commit ...              # automaticky spusti hooky")

# Kontrola zda je pre-commit dostupny
vysledek = subprocess.run(
    [sys.executable, "-m", "pre_commit", "--version"],
    capture_output=True, text=True,
)
if vysledek.returncode == 0:
    print(f"\n  pre-commit je nainstalovan: {vysledek.stdout.strip()}")
else:
    print("\n  pre-commit neni nainstalovan (pip install pre-commit)")


# Bonus: Demonstrace ruff --fix na prikladu

print("\n=== Bonus: ruff --fix demo ===\n")

SPATNY = Path("_spatny_kod.py")
SPATNY.write_text("""\
import os,sys
import re   # nevyuzity import

x=1+2
y =3+4

def soucet( a,b ):
    return a+b

class mujTrida:
    def __init__(self,x):
        self.x=x
""", encoding="utf-8")

print("Pred ruff:")
print(textwrap.indent(SPATNY.read_text(), "  "))

spust([sys.executable, "-m", "ruff", "check", "--fix", str(SPATNY)])

print("\nPo ruff --fix:")
try:
    print(textwrap.indent(SPATNY.read_text(), "  "))
except Exception:
    pass

SPATNY.unlink(missing_ok=True)
