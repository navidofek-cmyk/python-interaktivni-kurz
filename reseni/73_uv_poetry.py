"""Řešení – Lekce 73: uv a Poetry – moderní správa závislostí"""

import subprocess
import sys
import time
import tempfile
import shutil
from pathlib import Path

def spust(cmd: list[str], cwd: str | None = None) -> tuple[int, str]:
    r = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd)
    return r.returncode, (r.stdout + r.stderr).strip()

def dostupny(nastroj: str) -> bool:
    return subprocess.run(["which", nastroj], capture_output=True).returncode == 0

# 1. Porovnání rychlosti: pip vs uv (simulace měření)
print("=== 1. Porovnání rychlosti pip vs uv ===\n")

print("Příkazy pro reálné měření:")
print("  time pip install requests --quiet")
print("  time uv pip install requests --quiet")
print()

if dostupny("uv"):
    print("uv je nainstalovaný – měřím rychlost download/cache:\n")

    # Měř čas uv pip
    t0 = time.perf_counter()
    code, out = spust(["uv", "pip", "install", "--dry-run", "requests"])
    t_uv = time.perf_counter() - t0
    print(f"  uv pip install requests (dry-run): {t_uv*1000:.0f}ms")
    print(f"  (reálná instalace: uv je typicky 10-100× rychlejší než pip)\n")
else:
    print("  uv není nainstalováno.")
    print("  Instalace: curl -LsSf https://astral.sh/uv/install.sh | sh")
    print("  nebo:      pip install uv\n")
    print("  Typický benchmark:")
    print("    pip install requests:    ~2.5s")
    print("    uv pip install requests: ~0.1s (z cache)\n")

# 2. Vytvoření projektu s uv init a přidání FastAPI
print("=== 2. Nový uv projekt s FastAPI ===\n")

demo_dir = Path(tempfile.mkdtemp(prefix="uv_fastapi_demo_"))
try:
    if dostupny("uv"):
        # Vytvoř projekt
        code, out = spust(["uv", "init", "muj_api", "--no-workspace"], cwd=str(demo_dir))
        projekt = demo_dir / "muj_api"
        if not projekt.exists():
            # Starší verze uv – vytvoř ručně
            projekt = demo_dir / "muj_api"
            projekt.mkdir()

        # Ukázka pyproject.toml s FastAPI
        pyproject = projekt / "pyproject.toml"
        pyproject.write_text("""\
[project]
name = "muj-api"
version = "0.1.0"
description = "Demo FastAPI projekt"
requires-python = ">=3.11"
dependencies = [
    "fastapi>=0.110",
    "uvicorn[standard]>=0.27",
    "pydantic>=2.5",
]

[project.optional-dependencies]
dev = [
    "pytest>=8",
    "httpx>=0.27",
    "ruff>=0.3",
]

[tool.uv]
dev-dependencies = [
    "pytest>=8",
    "httpx>=0.27",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
""")

        # Vytvoř main.py
        main_py = projekt / "main.py"
        main_py.write_text("""\
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="Muj API", version="0.1.0")

class Student(BaseModel):
    jmeno: str
    body: float

@app.get("/")
def root():
    return {"zprava": "Ahoj z FastAPI!"}

@app.post("/studenti")
def vytvor_studenta(student: Student):
    return {"id": 1, **student.model_dump()}
""")

        print(f"Projekt vytvořen: {projekt}")
        print(f"  Soubory:")
        for f in sorted(projekt.iterdir()):
            print(f"    {f.name}")

        print("\n  Příkazy pro práci s projektem:")
        print("    uv add fastapi          # přidá závislost do pyproject.toml")
        print("    uv add --dev pytest     # vývojová závislost")
        print("    uv run python main.py   # spustí ve venv")
        print("    uv run pytest           # spustí testy")
        print("    uv sync                 # synchronizuje venv s pyproject.toml")
    else:
        print("  uv není dostupné – ukázka struktury projektu:\n")
        print("  muj_api/")
        print("  ├── pyproject.toml  (závislosti: fastapi, uvicorn, pydantic)")
        print("  ├── main.py         (FastAPI aplikace)")
        print("  ├── .python-version (3.12)")
        print("  └── uv.lock         (deterministický lock file)")
finally:
    shutil.rmtree(demo_dir, ignore_errors=True)

# 3. Porovnání pip vs uv s vizuálním výstupem
print("\n=== 3. Srovnání nástrojů ===\n")

srovnani = [
    ("Funkce",          "pip",       "uv",        "Poetry"),
    ("Rychlost",        "●●●",       "●●●●●",     "●●●●"),
    ("Lock file",       "✗",         "✓",         "✓"),
    ("Správa venv",     "✗",         "✓",         "✓"),
    ("Správa Pythonu",  "✗",         "✓",         "~"),
    ("Build/publish",   "~",         "✗",         "✓"),
    ("Instalace",       "vestavěný", "curl|pip",  "curl"),
]

sirky = [20, 12, 12, 12]
oddelovac = "+" + "+".join("-"*(s+2) for s in sirky) + "+"
print(oddelovac)
for i, radek in enumerate(srovnani):
    print("| " + " | ".join(str(h).ljust(s) for h, s in zip(radek, sirky)) + " |")
    if i == 0:
        print(oddelovac)
print(oddelovac)

print("\nDoporučení:")
print("  Nový projekt:     uv (rychlost) nebo Poetry (kompletní ekosystém)")
print("  Existující pip:   uv pip (drop-in náhrada, stejná syntaxe)")
print("  Knihovna na PyPI: Poetry (build + publish v jednom nástroji)")
print("  CI/CD:            uv (nejrychlejší instalace závislostí)")
