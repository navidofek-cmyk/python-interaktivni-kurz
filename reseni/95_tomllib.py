"""Řešení – Lekce 95: tomllib – TOML konfigurace

Toto je vzorové řešení úloh z lekce 95.
"""

import tomllib
import json
import time
import tempfile
from pathlib import Path

# ── Úloha 1 ────────────────────────────────────────────────
# Vytvoř TOML soubor 'muj_projekt.toml' s konfigurací a vypiš
# všechny hodnoty s jejich Python typem.

toml_obsah = """\
[server]
host = "0.0.0.0"
port = 8080
debug = true
tags = ["web", "api", "v2"]

[databaze]
url = "postgresql://localhost/mujdb"
port = 5432
ssl = false
pool_timeout = 30.5

[logging]
level = "DEBUG"
soubor = "app.log"
max_bajtu = 10485760
barvy = true
ignorovane_moduly = ["uvicorn.access", "sqlalchemy.engine"]
"""

muj_projekt = Path(tempfile.gettempdir()) / "muj_projekt.toml"
muj_projekt.write_text(toml_obsah, encoding="utf-8")

with open(muj_projekt, "rb") as f:
    cfg = tomllib.load(f)

print("Úloha 1 – čtení muj_projekt.toml")
for sekce, hodnoty in cfg.items():
    print(f"  [{sekce}]")
    for k, v in hodnoty.items():
        print(f"    {k} = {v!r}  ({type(v).__name__})")

muj_projekt.unlink()
print()


# ── Úloha 2 ────────────────────────────────────────────────
# Funkce toml_na_env(cfg) převede vnořený TOML slovník na plochý
# slovník ve stylu env proměnných (SEKCE_KLIC = "hodnota").

def toml_na_env(cfg: dict, prefix: str = "") -> dict:
    """Převede vnořený slovník na plochý ENV styl."""
    result = {}
    for k, v in cfg.items():
        klic = f"{prefix}_{k}".upper().lstrip("_")
        if isinstance(v, dict):
            result.update(toml_na_env(v, klic))
        elif isinstance(v, list):
            result[klic] = ",".join(str(i) for i in v)
        else:
            result[klic] = str(v)
    return result


ukazka = tomllib.loads("""\
[databaze]
host = "localhost"
port = 5432
ssl = true
jmena = ["Alice", "Bob"]

[server]
host = "0.0.0.0"
workers = 4
""")

env = toml_na_env(ukazka)
print("Úloha 2 – toml_na_env():")
for k, v in sorted(env.items()):
    print(f"  {k}={v!r}")
print()


# ── Úloha 3 ────────────────────────────────────────────────
# Porovnej výkon načítání přes tomllib.loads() vs json.loads()
# na 10 000 iteracích stejného konfiguračního řetězce.

toml_str = """\
title = "Benchmark"
verze = "1.0"
debug = false
max_conn = 100

[db]
host = "localhost"
port = 5432
"""

json_str = json.dumps({
    "title": "Benchmark",
    "verze": "1.0",
    "debug": False,
    "max_conn": 100,
    "db": {"host": "localhost", "port": 5432},
})

N = 10_000

start = time.perf_counter()
for _ in range(N):
    tomllib.loads(toml_str)
cas_toml = (time.perf_counter() - start) * 1000

start = time.perf_counter()
for _ in range(N):
    json.loads(json_str)
cas_json = (time.perf_counter() - start) * 1000

print(f"Úloha 3 – výkon ({N:,}× načtení):")
print(f"  tomllib.loads(): {cas_toml:.1f} ms")
print(f"  json.loads():    {cas_json:.1f} ms")
print(f"  JSON je ~{cas_toml/cas_json:.1f}× rychlejší (očekávané – JSON je jednodušší formát)")
print()


# ── Úloha 4 ────────────────────────────────────────────────
# Funkce validuj_config(cfg, schema) zkontroluje povinné klíče
# a vrátí seznam chybějících klíčů.

def validuj_config(cfg: dict, schema: dict) -> list[str]:
    """
    schema = {"server": ["host", "port"], "db": ["url"]}
    Vrátí seznam řetězců 'sekce.klic' pro chybějící klíče.
    """
    chybejici = []
    for sekce, klice in schema.items():
        if sekce not in cfg:
            for k in klice:
                chybejici.append(f"{sekce}.{k}")
        else:
            for k in klice:
                if k not in cfg[sekce]:
                    chybejici.append(f"{sekce}.{k}")
    return chybejici


schema = {
    "server":   ["host", "port", "workers"],
    "databaze": ["url", "pool_size"],
    "logging":  ["level", "soubor"],
}

kompletni_cfg = tomllib.loads("""\
[server]
host = "0.0.0.0"
port = 8080
workers = 4

[databaze]
url = "sqlite:///app.db"
pool_size = 5

[logging]
level = "INFO"
soubor = "app.log"
""")

neuplna_cfg = tomllib.loads("""\
[server]
host = "0.0.0.0"

[databaze]
url = "sqlite:///app.db"
""")

print("Úloha 4 – validuj_config():")
chyby = validuj_config(kompletni_cfg, schema)
print(f"  Kompletní konfig – chybějící klíče: {chyby or 'žádné'}")

chyby = validuj_config(neuplna_cfg, schema)
print(f"  Neúplná konfig  – chybějící klíče: {chyby}")
