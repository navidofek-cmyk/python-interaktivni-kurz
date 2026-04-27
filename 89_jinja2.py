"""
LEKCE 89: Jinja2 – šablonování
================================
pip install jinja2

Jinja2 = šablonovací engine. Odděluje logiku od prezentace.
Používá ho Flask, Ansible, dbt, cookiecutter, FastAPI...

Použití:
  HTML reporty, emaily, konfigurační soubory,
  generování kódu, dokumentace, CI/CD templaty
"""

try:
    from jinja2 import Environment, FileSystemLoader, BaseLoader, select_autoescape
    from jinja2 import Template, StrictUndefined
    JINJA_OK = True
except ImportError:
    print("Jinja2 není nainstalováno: pip install jinja2")
    JINJA_OK = False

import json
import textwrap
from pathlib import Path
from datetime import datetime

if not JINJA_OK:
    exit()

# ══════════════════════════════════════════════════════════════
# ČÁST 1: Základní šablona
# ══════════════════════════════════════════════════════════════

print("=== Jinja2 základy ===\n")

# Inline šablona
sablona = Template("""\
Ahoj, {{ jmeno }}!
Máš {{ body }} bodů.
{% if body >= 90 %}Výborně!{% elif body >= 75 %}Dobře.{% else %}Nevzdávej to!{% endif %}
""")

print(sablona.render(jmeno="Míša", body=92))
print(sablona.render(jmeno="Tomáš", body=65))

# Smyčky
seznam_sablona = Template("""\
Studenti ({{ studenti|length }}):
{% for s in studenti -%}
  {{ loop.index }}. {{ s.jmeno }} – {{ s.body }}b
  {%- if loop.last %} ← poslední{% endif %}
{% endfor %}
Průměr: {{ studenti|map(attribute='body')|list|sum / studenti|length | round(1) }}
""")

studenti = [
    {"jmeno": "Míša",  "body": 87.5},
    {"jmeno": "Tomáš", "body": 92.0},
    {"jmeno": "Bára",  "body": 55.3},
]
print(seznam_sablona.render(studenti=studenti))


# ══════════════════════════════════════════════════════════════
# ČÁST 2: Filtry a testy
# ══════════════════════════════════════════════════════════════

print("=== Filtry a vlastní filtry ===\n")

env = Environment(loader=BaseLoader(), undefined=StrictUndefined)

# Vlastní filter
def format_body(body: float) -> str:
    if body >= 90: return f"⭐ {body:.1f}"
    if body >= 75: return f"✓ {body:.1f}"
    return f"✗ {body:.1f}"

def zkrat(text: str, delka: int = 30) -> str:
    return text if len(text) <= delka else text[:delka] + "..."

env.filters["format_body"] = format_body
env.filters["zkrat"]       = zkrat

sablona2 = env.from_string("""\
{% for s in studenti %}
{{ s.jmeno | upper | center(15) }} | {{ s.body | format_body }} | {{ s.popis | zkrat(20) }}
{% endfor %}
""")

studenti2 = [
    {"jmeno": "Míša",  "body": 87.5, "popis": "Výborný student s velkým zájmem o Python"},
    {"jmeno": "Tomáš", "body": 92.0, "popis": "Nejlepší v ročníku"},
    {"jmeno": "Bára",  "body": 55.3, "popis": "Potřebuje pomoc"},
]
print(sablona2.render(studenti=studenti2))


# ══════════════════════════════════════════════════════════════
# ČÁST 3: HTML report
# ══════════════════════════════════════════════════════════════

print("=== HTML report ===\n")

HTML_SABLONA = """\
<!DOCTYPE html>
<html lang="cs">
<head>
  <meta charset="utf-8">
  <title>{{ titulek }}</title>
  <style>
    body { font-family: Arial, sans-serif; max-width: 800px; margin: 2rem auto; }
    h1   { color: #2E86AB; }
    table{ border-collapse: collapse; width: 100%; }
    th   { background: #2E86AB; color: white; padding: 8px; }
    td   { padding: 8px; border-bottom: 1px solid #ddd; }
    tr:nth-child(even) { background: #f2f2f2; }
    .ok  { color: green; font-weight: bold; }
    .bad { color: red; }
    .footer { color: #888; font-size: .85em; margin-top: 2rem; }
  </style>
</head>
<body>
  <h1>{{ titulek }}</h1>
  <p>Generováno: <strong>{{ generovano }}</strong></p>

  <h2>Přehled ({{ studenti|length }} studentů)</h2>
  <table>
    <tr>
      <th>#</th><th>Jméno</th><th>Předmět</th>
      <th>Body</th><th>Výsledek</th>
    </tr>
    {% for s in studenti %}
    <tr>
      <td>{{ loop.index }}</td>
      <td><strong>{{ s.jmeno }}</strong></td>
      <td>{{ s.predmet }}</td>
      <td>{{ s.body }}</td>
      <td class="{{ 'ok' if s.body >= 75 else 'bad' }}">
        {{ "✓ Prospívá" if s.body >= 75 else "✗ Neprospívá" }}
      </td>
    </tr>
    {% endfor %}
  </table>

  <h2>Statistiky</h2>
  <ul>
    <li>Průměr: <strong>{{ prumer | round(1) }}</strong></li>
    <li>Prospívají: <strong>{{ prospivaji }}</strong> / {{ studenti|length }}</li>
    <li>Maximum: <strong>{{ maximum }}</strong></li>
  </ul>

  <div class="footer">
    Kurz Python | {{ rok }}
  </div>
</body>
</html>
"""

data = {
    "titulek":    "Výsledky studentů – Jaro 2024",
    "generovano": datetime.now().strftime("%d.%m.%Y %H:%M"),
    "rok":        datetime.now().year,
    "studenti": [
        {"jmeno": "Míša",  "predmet": "Python",      "body": 87.5},
        {"jmeno": "Tomáš", "predmet": "Fyzika",       "body": 92.0},
        {"jmeno": "Bára",  "predmet": "Matematika",   "body": 55.3},
        {"jmeno": "Ondra", "predmet": "Informatika",  "body": 95.1},
        {"jmeno": "Klára", "predmet": "Biologie",     "body": 61.0},
    ],
}
data["prumer"]    = sum(s["body"] for s in data["studenti"]) / len(data["studenti"])
data["prospivaji"] = sum(1 for s in data["studenti"] if s["body"] >= 75)
data["maximum"]   = max(s["body"] for s in data["studenti"])

html = env.from_string(HTML_SABLONA).render(**data)
Path("report.html").write_text(html, encoding="utf-8")
print(f"  ✓ report.html ({Path('report.html').stat().st_size:,} B)")


# ══════════════════════════════════════════════════════════════
# ČÁST 4: Generování kódu
# ══════════════════════════════════════════════════════════════

print("\n=== Generování Python kódu ===\n")

DATACLASS_SABLONA = """\
# Automaticky vygenerováno Jinja2 – {{ datum }}
from dataclasses import dataclass, field
from typing import Optional
{% if validace %}from pydantic import BaseModel, Field{% endif %}


{% if validace %}
class {{ jmeno }}(BaseModel):
{% else %}
@dataclass
class {{ jmeno }}:
{% endif %}
    \"\"\"{{ popis }}\"\"\"
{% for pole in pole %}
    {{ pole.jmeno }}: {{ pole.typ }}{% if pole.vychozi is not none %} = {{ pole.vychozi }}{% endif %}
    {%- if validace and pole.min is defined %}
    # Field(ge={{ pole.min }}, le={{ pole.max }})
    {%- endif %}

{% endfor %}
    def __str__(self) -> str:
        return f"{{ jmeno }}({% for p in pole %}{{ p.jmeno }}={{'{self.' + p.jmeno + '}'}}{% if not loop.last %}, {% endif %}{% endfor %})"
"""

schema = {
    "jmeno":    "Student",
    "popis":    "Záznam studenta v databázi kurzu.",
    "datum":    datetime.now().strftime("%Y-%m-%d"),
    "validace": True,
    "pole": [
        {"jmeno": "id",       "typ": "int",   "vychozi": None},
        {"jmeno": "jmeno",    "typ": "str",   "vychozi": None},
        {"jmeno": "email",    "typ": "str",   "vychozi": None},
        {"jmeno": "body",     "typ": "float", "vychozi": "0.0", "min": 0, "max": 100},
        {"jmeno": "aktivni",  "typ": "bool",  "vychozi": "True"},
    ],
}

vygenerovany_kod = env.from_string(DATACLASS_SABLONA).render(**schema)
print(vygenerovany_kod)

# ── Generuj Ansible-like konfiguraci ─────────────────────────
print("=== Generování konfigurace (YAML-like) ===\n")

KONFIG_SABLONA = """\
# Konfigurace pro {{ prostredi }} prostředí
# Vygenerováno: {{ datum }}

app:
  name: python-kurz
  version: "{{ verze }}"
  debug: {{ "true" if debug else "false" }}

database:
  host: {{ db.host }}
  port: {{ db.port }}
  name: {{ db.name }}
  pool_size: {{ db.pool | default(5) }}

services:
{% for sluzba in sluzby %}
  - name: {{ sluzba.jmeno }}
    replicas: {{ sluzba.repliky }}
    memory: "{{ sluzba.pamet }}"
{% endfor %}

features:
{% for funkce, povolena in features.items() %}
  {{ funkce }}: {{ "enabled" if povolena else "disabled" }}
{% endfor %}
"""

konfig = env.from_string(KONFIG_SABLONA).render(
    prostredi="production",
    datum=datetime.now().strftime("%Y-%m-%d"),
    verze="2.1.0",
    debug=False,
    db={"host": "db.example.com", "port": 5432, "name": "kurz_prod", "pool": 10},
    sluzby=[
        {"jmeno": "api",    "repliky": 3, "pamet": "512Mi"},
        {"jmeno": "worker", "repliky": 2, "pamet": "256Mi"},
    ],
    features={"ai_review": True, "dark_mode": True, "beta_features": False},
)
print(konfig)

Path("report.html").unlink(missing_ok=True)

# TVOJE ÚLOHA:
# 1. Napiš Jinja2 šablonu pro email notifikaci z lekce 78.
# 2. Generuj SQLAlchemy modely z JSON schématu (jméno, pole, typy).
# 3. Napiš generátor testovacích fixtures – z dataclass def vygeneruj pytest fixtures.
