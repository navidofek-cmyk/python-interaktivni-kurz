"""
LEKCE 73: uv a Poetry – moderní správa závislostí
===================================================
pip je základní nástroj, ale má limity:
  - Pomalá resoluce závislostí
  - Žádná automatická správa virtuálního prostředí
  - Žádný lock file (requirements.txt není deterministický)

UV (od Astral, autoři Ruff)
  - Napsaný v Rustu → 10–100× rychlejší než pip
  - Nahrazuje pip, pip-tools, virtualenv, pyenv
  - Kompatibilní s pip (pip install → uv pip install)
  - uv.lock – deterministický lock file

Poetry
  - pyproject.toml jako jediný konfigurační soubor
  - Automatická správa virtuálního prostředí
  - Build a publish na PyPI
  - Sémantické verzování závislostí

Tato lekce generuje ukázkové projekty a ukazuje příkazy.
"""

import subprocess
import sys
import textwrap
from pathlib import Path

def spust(cmd: str, popis: str = ""):
    print(f"  $ {cmd}")
    r = subprocess.run(cmd.split(), capture_output=True, text=True)
    vystup = (r.stdout + r.stderr).strip()
    if vystup:
        for radek in vystup.splitlines()[:5]:
            print(f"    {radek}")
    return r.returncode == 0

def dostupny(nastroj: str) -> bool:
    return subprocess.run(["which", nastroj], capture_output=True).returncode == 0

# ══════════════════════════════════════════════════════════════
# ČÁST 1: UV – rychlý správce balíčků
# ══════════════════════════════════════════════════════════════

print("=== uv – ultra-fast Python package manager ===\n")

if dostupny("uv"):
    print("  uv je nainstalovaný!\n")
    spust("uv --version", "verze")
else:
    print("  uv není nainstalovaný.")
    print("  Instalace: curl -LsSf https://astral.sh/uv/install.sh | sh")
    print("  nebo: pip install uv\n")

print("""
  # Instalace uv
  curl -LsSf https://astral.sh/uv/install.sh | sh   # Linux/Mac
  pip install uv                                       # přes pip

  # Základní příkazy (nahrazují pip)
  uv pip install requests              # instaluj balíček
  uv pip install -r requirements.txt   # ze souboru
  uv pip uninstall requests            # odinstaluj
  uv pip list                          # seznam balíčků
  uv pip freeze > requirements.txt     # exportuj

  # Nový projekt
  uv init muj-projekt                  # vytvoří strukturu
  cd muj-projekt
  uv add requests                      # přidá závislost + aktualizuje uv.lock
  uv add --dev pytest ruff             # vývojové závislosti
  uv run python main.py                # spusť ve virtuálním prostředí
  uv run pytest                        # spusť testy

  # Správa Python verzí
  uv python install 3.12               # instaluj Python verzi
  uv python install 3.13
  uv python list                       # seznam dostupných verzí
  uv venv --python 3.12                # virtualenv s konkrétní verzí
""")

# ── uv.lock vs requirements.txt ──────────────────────────────
print("=== uv.lock – deterministický lock file ===\n")

UV_LOCK_UKAZKA = """\
version = 1
requires-python = ">=3.11"

[[package]]
name = "requests"
version = "2.31.0"
source = { registry = "https://pypi.org/simple" }
dependencies = [
    { name = "certifi" },
    { name = "charset-normalizer" },
    { name = "idna" },
    { name = "urllib3" },
]
sdist = { url = "...", hash = "sha256:abc123..." }
wheels = [
    { url = "...", hash = "sha256:def456..." },
]

[[package]]
name = "certifi"
version = "2024.2.2"
...
"""
print("  uv.lock (deterministický – každý dostane PŘESNĚ stejné verze):")
print(textwrap.indent(UV_LOCK_UKAZKA.strip()[:300] + "\n  ...", "  "))

print("""
  requirements.txt vs uv.lock:
    requirements.txt  → jen jméno a verze, závislosti závislostí chybí
    uv.lock           → celý strom závislostí s hashy → 100% reprodukovatelné
""")


# ══════════════════════════════════════════════════════════════
# ČÁST 2: Poetry – správa projektů
# ══════════════════════════════════════════════════════════════

print("=== Poetry – správa Python projektů ===\n")

if dostupny("poetry"):
    print("  Poetry je nainstalovaná!\n")
    spust("poetry --version")
else:
    print("  Poetry není nainstalovaná.")
    print("  Instalace: curl -sSL https://install.python-poetry.org | python3\n")

print("""
  # Instalace Poetry
  curl -sSL https://install.python-poetry.org | python3 -

  # Nový projekt
  poetry new muj-projekt     # vytvoří strukturu
  cd muj-projekt

  # Správa závislostí
  poetry add requests                  # přidej závislost
  poetry add --group dev pytest ruff   # vývojové závislosti
  poetry remove requests               # odeber
  poetry update                        # aktualizuj vše

  # Virtuální prostředí
  poetry install                       # instaluj vše z poetry.lock
  poetry shell                         # aktivuj venv
  poetry run python main.py            # spusť bez aktivace

  # Build a publish
  poetry build                         # vytvoří dist/*.whl a dist/*.tar.gz
  poetry publish                       # nahraj na PyPI
  poetry publish --repository testpypi # nejprve na testpypi
""")

# ── pyproject.toml s Poetry ───────────────────────────────────
POETRY_PYPROJECT = """\
[tool.poetry]
name = "muj-projekt"
version = "0.1.0"
description = "Ukázkový Poetry projekt"
authors = ["Míša <misa@example.com>"]
readme = "README.md"
packages = [{include = "muj_projekt", from = "src"}]

[tool.poetry.dependencies]
python = "^3.11"
requests = "^2.31"
pydantic = "^2.5"

[tool.poetry.group.dev.dependencies]
pytest = "^7.4"
ruff = "^0.1"
mypy = "^1.5"

[tool.poetry.scripts]
muj-nastroj = "muj_projekt.cli:main"

[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"

[tool.ruff]
line-length = 88

[tool.mypy]
strict = true
"""

print("  pyproject.toml s Poetry:")
print(textwrap.indent(POETRY_PYPROJECT, "  "))


# ══════════════════════════════════════════════════════════════
# ČÁST 3: Srovnání nástrojů
# ══════════════════════════════════════════════════════════════

print("""
=== Srovnání: pip vs uv vs Poetry ===

                    pip      uv       Poetry
  Rychlost          ●●●      ●●●●●    ●●●●
  Lock file         ✗        ✓        ✓
  Správa venv       ✗        ✓        ✓
  Správa Python     ✗        ✓        ~
  Build/publish     ✗        ✗        ✓
  Oblíbenost        ●●●●●    ●●●●     ●●●●
  Jednoduchost      ●●●●●    ●●●●     ●●●

  Doporučení:
    Nový projekt      → uv (rychlost) nebo Poetry (kompletní)
    Jednoduchý skript → uv pip nebo pip
    Knihovna na PyPI  → Poetry nebo uv + build
    CI/CD             → uv (rychlost instalace)
    Existující pip    → uv pip (drop-in náhrada)
""")

# ── Vygeneruj ukázkový projekt ────────────────────────────────
print("=== Ukázkový uv projekt (generuji soubory) ===\n")

demo = Path("uv_demo")
demo.mkdir(exist_ok=True)
(demo / "main.py").write_text('print("Ahoj z uv projektu!")\n')
(demo / "pyproject.toml").write_text(textwrap.dedent("""\
    [project]
    name = "uv-demo"
    version = "0.1.0"
    requires-python = ">=3.11"
    dependencies = ["requests>=2.31"]

    [tool.uv]
    dev-dependencies = ["pytest>=7", "ruff>=0.1"]
"""))
(demo / ".python-version").write_text("3.12\n")

print(f"  Vytvořen ukázkový projekt: {demo}/")
print("  Soubory:")
for f in sorted(demo.iterdir()):
    print(f"    {f.name}")

import shutil
shutil.rmtree(demo)

# TVOJE ÚLOHA:
# 1. Nainstaluj uv a přeinstaluj závislosti tohoto kurzu: uv pip install -r requirements.txt
# 2. Vytvoř nový projekt pomocí uv init a přidej FastAPI jako závislost.
# 3. Porovnej čas instalace: time pip install requests vs time uv pip install requests.
