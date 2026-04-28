"""
LEKCE 95: tomllib – TOML konfigurace (Python 3.11+)
=====================================================
Naučíš se číst TOML konfigurační soubory pomocí
vestavěného modulu tomllib (Python 3.11+).

TOML = Tom's Obvious, Minimal Language
  – čitelnější než JSON (komentáře, víceřádkové stringy)
  – strukturovanější než INI
  – typově bezpečnější než oba
  – standard pro Python projekty (pyproject.toml)

Srovnání formátů:
  INI  → jednoduché, bez typů, jen stringy
  JSON → striktní, žádné komentáře, pro data
  TOML → konfigurace, komentáře, typy, čitelné
"""

import tomllib
import json
import configparser
import tempfile
import os
from pathlib import Path
from datetime import datetime

print("=== LEKCE 95: tomllib – TOML konfigurace ===\n")

# ══════════════════════════════════════════════════════════════
# ČÁST 1: Základní čtení TOML – tomllib.loads()
# ══════════════════════════════════════════════════════════════

print("── Část 1: tomllib.loads() ──\n")

toml_text = """
# Toto je komentář – JSON ho neumí!
title = "Moje aplikace"
verze = "1.0.0"
debug = false
max_pripojeni = 100
pi = 3.14159

[databaze]
host = "localhost"
port = 5432
jmeno = "mydb"
ssl = true

[databaze.pool]
min_size = 2
max_size = 10

[uzivatel]
jmena = ["Alice", "Bob", "Carol"]
role = {admin = true, editor = false}

[metadata]
vytvoreno = 2024-01-15T10:30:00
"""

config = tomllib.loads(toml_text)

print(f"  Název aplikace: {config['title']}")
print(f"  Verze:          {config['verze']}")
print(f"  Debug:          {config['debug']}  (bool, ne string!)")
print(f"  Max připojení:  {config['max_pripojeni']}  (int!)")
print(f"  Pi:             {config['pi']}  (float!)")
print(f"  DB host:        {config['databaze']['host']}")
print(f"  DB port:        {config['databaze']['port']}")
print(f"  Pool max:       {config['databaze']['pool']['max_size']}")
print(f"  Uživatelé:      {config['uzivatel']['jmena']}")
print(f"  Datum:          {config['metadata']['vytvoreno']}  (datetime!)")
print()

# ══════════════════════════════════════════════════════════════
# ČÁST 2: Čtení ze souboru – tomllib.load()
# ══════════════════════════════════════════════════════════════

print("── Část 2: tomllib.load() – čtení ze souboru ──\n")

# Vytvoříme ukázkový TOML soubor
TOML_SOUBOR = Path(tempfile.gettempdir()) / "app_config.toml"

toml_obsah = """\
# Konfigurace aplikace – app_config.toml

[app]
nazev = "KurzovnikPy"
verze = "2.3.1"
jazyk = "cs"
log_level = "INFO"

[server]
host = "0.0.0.0"
port = 8080
workers = 4
timeout = 30

[databaze]
url = "postgresql://localhost/kurzy"
echo = false
pool_size = 5

[cache]
backend = "redis"
host = "localhost"
port = 6379
ttl = 3600

[email]
smtp_host = "smtp.seznam.cz"
smtp_port = 587
tls = true
odesilatel = "noreply@kurzy.cz"

[features]
registrace = true
newsletter = false
beta_tester = false
"""

TOML_SOUBOR.write_text(toml_obsah, encoding="utf-8")
print(f"  Vytvořen soubor: {TOML_SOUBOR}")

# Čtení: tomllib.load() vyžaduje binární mód ("rb")
with open(TOML_SOUBOR, "rb") as f:
    app_cfg = tomllib.load(f)

print(f"  Aplikace:  {app_cfg['app']['nazev']} v{app_cfg['app']['verze']}")
print(f"  Server:    {app_cfg['server']['host']}:{app_cfg['server']['port']}")
print(f"  Workers:   {app_cfg['server']['workers']}")
print(f"  Cache TTL: {app_cfg['cache']['ttl']}s")
print(f"  TLS email: {app_cfg['email']['tls']}")
print()

# ══════════════════════════════════════════════════════════════
# ČÁST 3: Srovnání TOML vs INI vs JSON
# ══════════════════════════════════════════════════════════════

print("── Část 3: Srovnání TOML vs INI vs JSON ──\n")

# Stejná data ve třech formátech
data = {
    "host": "localhost",
    "port": 5432,
    "ssl": True,
    "tags": ["web", "api"],
}

# JSON – žádné komentáře, port jako číslo OK
json_str = json.dumps(data, indent=2)
json_zpet = json.loads(json_str)
print(f"  JSON port typ:  {type(json_zpet['port']).__name__} = {json_zpet['port']}")
print(f"  JSON ssl typ:   {type(json_zpet['ssl']).__name__} = {json_zpet['ssl']}")

# INI – vše jako string, žádné vnořování, žádné listy
ini_str = """\
[db]
host = localhost
port = 5432
ssl = true
"""
ini = configparser.ConfigParser()
ini.read_string(ini_str)
ini_port = ini.getint("db", "port")     # musíme explicitně konvertovat
ini_ssl  = ini.getboolean("db", "ssl")  # musíme explicitně konvertovat
print(f"  INI  port typ:  {type(ini_port).__name__} = {ini_port}  (po getint)")
print(f"  INI  ssl typ:   {type(ini_ssl).__name__} = {ini_ssl}  (po getboolean)")

# TOML – typy automaticky
toml_str = 'host = "localhost"\nport = 5432\nssl = true\ntags = ["web", "api"]\n'
toml_data = tomllib.loads(toml_str)
print(f"  TOML port typ:  {type(toml_data['port']).__name__} = {toml_data['port']}")
print(f"  TOML ssl typ:   {type(toml_data['ssl']).__name__} = {toml_data['ssl']}")
print(f"  TOML tags:      {toml_data['tags']}  (list nativně!)")
print()

# ══════════════════════════════════════════════════════════════
# ČÁST 4: Čtení pyproject.toml
# ══════════════════════════════════════════════════════════════

print("── Část 4: Simulace čtení pyproject.toml ──\n")

pyproject_toml = """\
[build-system]
requires = ["setuptools>=68", "wheel"]
build-backend = "setuptools.backends.legacy:build"

[project]
name = "muj-python-kurz"
version = "1.0.0"
description = "Interaktivní Python kurz"
readme = "README.md"
requires-python = ">=3.11"
license = {text = "MIT"}
authors = [
    {name = "Ivan", email = "ivan@example.cz"},
]
keywords = ["python", "kurz", "výuka"]
dependencies = [
    "fastapi>=0.100",
    "sqlalchemy>=2.0",
    "pydantic>=2.0",
]

[project.optional-dependencies]
dev = ["pytest", "ruff", "mypy"]
docs = ["mkdocs", "mkdocs-material"]

[tool.ruff]
line-length = 100
target-version = "py311"

[tool.mypy]
strict = true
python_version = "3.11"
"""

pp = tomllib.loads(pyproject_toml)
proj = pp["project"]

print(f"  Projekt:         {proj['name']} v{proj['version']}")
print(f"  Popis:           {proj['description']}")
print(f"  Python:          {proj['requires-python']}")
print(f"  Autoři:          {proj['authors'][0]['name']} <{proj['authors'][0]['email']}>")
print(f"  Závislosti:")
for dep in proj["dependencies"]:
    print(f"    – {dep}")
print(f"  Dev deps:        {pp['project.optional-dependencies']['dev'] if 'project.optional-dependencies' in pp else pp.get('project', {})}")

dev_deps = pp.get("project", {}).get("optional-dependencies", {}).get("dev", [])
print(f"  Dev závislosti:  {dev_deps}")
print(f"  Ruff max délka:  {pp['tool']['ruff']['line-length']}")
print(f"  mypy strict:     {pp['tool']['mypy']['strict']}")
print()

# ══════════════════════════════════════════════════════════════
# ČÁST 5: Praktický helper – načtení config s výchozími hodnotami
# ══════════════════════════════════════════════════════════════

print("── Část 5: Config helper s výchozími hodnotami ──\n")

class AppConfig:
    """Načte TOML konfiguraci a zpřístupní ji přes atributy."""

    VYCHOZI = {
        "app": {"nazev": "Aplikace", "verze": "0.0.1", "debug": False},
        "server": {"host": "127.0.0.1", "port": 8000, "workers": 1},
        "databaze": {"url": "sqlite:///db.sqlite3", "pool_size": 3},
    }

    def __init__(self, toml_soubor: Path | None = None):
        self._cfg = {}
        # Nejprve výchozí hodnoty
        for sekce, hodnoty in self.VYCHOZI.items():
            self._cfg[sekce] = dict(hodnoty)
        # Přepis z souboru
        if toml_soubor and toml_soubor.exists():
            with open(toml_soubor, "rb") as f:
                nactene = tomllib.load(f)
            for sekce, hodnoty in nactene.items():
                if sekce in self._cfg:
                    self._cfg[sekce].update(hodnoty)
                else:
                    self._cfg[sekce] = hodnoty

    def get(self, sekce: str, klic: str, vychozi=None):
        return self._cfg.get(sekce, {}).get(klic, vychozi)

    def vypis(self):
        for sekce, hodnoty in self._cfg.items():
            print(f"  [{sekce}]")
            for k, v in hodnoty.items():
                print(f"    {k} = {v!r}")

cfg = AppConfig(TOML_SOUBOR)
print("  Načtená konfigurace (výchozí + soubor):")
cfg.vypis()
print()
print(f"  server.workers = {cfg.get('server', 'workers')}")
print(f"  neexistuje     = {cfg.get('sekce', 'klic', 'VÝCHOZÍ')}")
print()

# Úklid
TOML_SOUBOR.unlink(missing_ok=True)
print(f"  Soubor {TOML_SOUBOR.name} smazán.\n")

# ══════════════════════════════════════════════════════════════
# TVOJE ÚLOHA:
# ══════════════════════════════════════════════════════════════
print("=" * 55)
print("TVOJE ÚLOHA:")
print("=" * 55)
print("""
1. Vytvoř TOML soubor 'muj_projekt.toml' s konfigurací pro
   smyšlenou aplikaci – musí obsahovat: [server], [databaze],
   [logging] sekce s aspoň 3 klíči každá (různé typy: str,
   int, bool, list). Přečti ho přes tomllib.load() a vypiš
   všechny hodnoty s jejich Python typem.

2. Napiš funkci `toml_na_env(cfg: dict) -> dict`, která
   převede vnořený TOML slovník na plochý slovník ve stylu
   env proměnných: {"databaze": {"port": 5432}} →
   {"DATABAZE_PORT": "5432"}. Otestuj na ukázkovém TOML.

3. Porovnej výkon načítání konfigurace: změř (timeit nebo
   time.perf_counter), jak dlouho trvá 10 000× načíst
   stejný konfigurační řetězec přes tomllib.loads() vs
   json.loads() (ekvivalentní JSON). Vypiš výsledky v ms.

4. Napiš funkci `validuj_config(cfg: dict, schema: dict)
   -> list[str]`, která zkontroluje, zda TOML konfigurace
   obsahuje všechny požadované klíče (schema = {sekce:
   [klic1, klic2, ...]}). Vrátí seznam chybějících klíčů.
   Ukázka: schema = {"server": ["host", "port"], ...}
""")
