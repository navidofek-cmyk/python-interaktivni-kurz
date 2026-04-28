"""Řešení – Lekce 89: Jinja2 – šablonování"""

# vyžaduje: pip install jinja2

import json
from pathlib import Path
from datetime import datetime

try:
    from jinja2 import Environment, BaseLoader, StrictUndefined, Template
    JINJA_OK = True
except ImportError:
    print("Jinja2 není nainstalováno: pip install jinja2")
    import sys; sys.exit(0)

env = Environment(loader=BaseLoader(), undefined=StrictUndefined)


# 1. Jinja2 šablona pro email notifikaci (lekce 78)
print("=== 1. Email notifikace – Jinja2 šablona ===\n")

EMAIL_SABLONA = """\
Předmět: {{ predmet }}
{% if typ == "html" %}
<!DOCTYPE html>
<html lang="cs">
<head><meta charset="utf-8"><title>{{ predmet }}</title></head>
<body style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto">
  <div style="background:#2E86AB;color:white;padding:20px;border-radius:4px 4px 0 0">
    <h2 style="margin:0">{{ ikona }} {{ titulek }}</h2>
    <p style="margin:5px 0;opacity:0.85">{{ podtitulek }}</p>
  </div>
  <div style="padding:20px;border:1px solid #ddd;border-top:none">
    {% if zprava %}
    <p>{{ zprava }}</p>
    {% endif %}
    {% if tabulka %}
    <table style="width:100%;border-collapse:collapse;margin-top:15px">
      <thead>
        <tr>
          {% for sloupec in tabulka.sloupce %}
          <th style="background:#f5f5f5;padding:8px;border:1px solid #ddd;text-align:left">
            {{ sloupec }}
          </th>
          {% endfor %}
        </tr>
      </thead>
      <tbody>
        {% for radek in tabulka.radky %}
        <tr>
          {% for hodnota in radek %}
          <td style="padding:8px;border:1px solid #ddd">{{ hodnota }}</td>
          {% endfor %}
        </tr>
        {% endfor %}
      </tbody>
    </table>
    <p style="color:#888;font-size:0.9em;margin-top:10px">
      {{ tabulka.radky | length }} záznamů celkem.
    </p>
    {% endif %}
    {% if tlacitko %}
    <div style="margin-top:20px">
      <a href="{{ tlacitko.url }}"
         style="background:#2E86AB;color:white;padding:10px 20px;
                text-decoration:none;border-radius:4px;display:inline-block">
        {{ tlacitko.text }}
      </a>
    </div>
    {% endif %}
  </div>
  <div style="padding:10px 20px;font-size:0.85em;color:#888">
    Odesláno {{ datum }}. Tento email byl vygenerován automaticky.
  </div>
</body>
</html>
{% else %}
{{ titulek }}
{{ '=' * titulek | length }}

{% if zprava %}{{ zprava }}{% endif %}
{% if tabulka %}
{{ tabulka.sloupce | join(' | ') }}
{% for radek in tabulka.radky %}{{ radek | join(' | ') }}{% endfor %}
{% endif %}
{% if tlacitko %}{{ tlacitko.text }}: {{ tlacitko.url }}{% endif %}

Odesláno: {{ datum }}
{% endif %}
"""

def generuj_email(typ: str = "html", **kontext) -> str:
    """Generuje email v HTML nebo textovém formátu."""
    kontext.setdefault("datum", datetime.now().strftime("%d.%m.%Y %H:%M"))
    kontext["typ"] = typ
    return env.from_string(EMAIL_SABLONA).render(**kontext)

# Typy emailů
emaily = [
    {
        "predmet":    "Týdenní výsledky studentů",
        "titulek":    "Týdenní report",
        "podtitulek": "Automatický přehled výsledků",
        "ikona":      "📊",
        "zprava":     "Přehled výsledků za tento týden.",
        "tabulka": {
            "sloupce": ["Jméno", "Předmět", "Body"],
            "radky":   [
                ["Míša",  "Python",     "87.5"],
                ["Tomáš", "Fyzika",     "92.0"],
                ["Bára",  "Matematika", "55.3"],
            ],
        },
        "tlacitko": {"text": "Zobrazit plný report", "url": "https://kurz.cz/report"},
    },
    {
        "predmet":    "Alert: Deploy selhal",
        "titulek":    "CI/CD Selhání",
        "podtitulek": "Automatický alert z pipeline",
        "ikona":      "🔴",
        "zprava":     "Build na větvi main selhal. Zkontroluj logy.",
        "tlacitko":   {"text": "Zobrazit logy", "url": "https://ci.example.com/build/123"},
    },
]

for i, data in enumerate(emaily, 1):
    html = generuj_email("html", **data)
    text = generuj_email("text", **data)
    print(f"  Email {i}: {data['predmet']}")
    print(f"    HTML: {len(html):,} B")
    print(f"    Text: {len(text):,} B")
    if i == 1:
        print(f"    HTML preview (prvních 200 znaků):")
        for radek in html.splitlines()[10:14]:
            print(f"    {radek.strip()[:80]}")
    print()


# 2. Generování SQLAlchemy modelů z JSON schématu
print("\n=== 2. SQLAlchemy modely z JSON schématu ===\n")

SA_MODEL_SABLONA = """\
# Automaticky vygenerováno Jinja2 – {{ datum }}
# NEUPRAVUJ ručně – upravuj schema a spusť generátor

from __future__ import annotations
from datetime import datetime
from sqlalchemy import (
    Integer, String, Float, Boolean, DateTime, Text, ForeignKey,
    UniqueConstraint, Index,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

class Base(DeclarativeBase):
    pass

{% for model in modely %}
class {{ model.jmeno }}(Base):
    \"\"\"{{ model.popis | default('Automaticky vygenerovaný model.') }}\"\"\"
    __tablename__ = "{{ model.tabulka | default(model.jmeno | lower + 's') }}"
    {% if model.unique_constraints is defined %}
    __table_args__ = (
        {% for uc in model.unique_constraints %}
        UniqueConstraint({{ uc | map('tojson') | join(', ') }}, name="{{ model.tabulka }}_uc"),
        {% endfor %}
    )
    {% endif %}

    {% for pole in model.pole %}
    {{ pole.jmeno }}: Mapped[{{ pole.typ }}{% if not pole.required | default(true) %}| None{% endif %}] = mapped_column(
        {{ pole.sa_typ }}{% if pole.pk | default(false) %}, primary_key=True{% endif %}{% if pole.autoincrement | default(false) %}, autoincrement=True{% endif %}{% if pole.unique | default(false) %}, unique=True{% endif %}{% if pole.index | default(false) %}, index=True{% endif %}{% if pole.vychozi is defined %}, default={{ pole.vychozi }}{% endif %}{% if pole.nullable is defined %}, nullable={{ pole.nullable }}{% endif %}
    )
    {% endfor %}
    {% for rel in model.relace | default([]) %}
    {{ rel.jmeno }}: Mapped[list["{{ rel.cil }}"]] = relationship("{{ rel.cil }}", back_populates="{{ rel.zpet }}")
    {% endfor %}

    def __repr__(self) -> str:
        return f"{{ model.jmeno }}({{ model.pole[:2] | map(attribute='jmeno') | map('format', '{0}={' ~ '{' ~ 'self.' ~ '{pole.jmeno}' ~ '}' ~ '}') | join(', ') }})"

{% endfor %}
"""

# Zjednodušená šablona (bez komplexního Jinja výrazu v __repr__)
SA_MODEL_SIMPLE = """\
# Automaticky vygenerováno Jinja2 – {{ datum }}
from __future__ import annotations
from datetime import datetime
from sqlalchemy import Integer, String, Float, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

class Base(DeclarativeBase):
    pass

{% for model in modely %}
class {{ model.jmeno }}(Base):
    \"\"\"{{ model.popis }}\"\"\"
    __tablename__ = "{{ model.tabulka }}"

{% for pole in model.pole %}
    {{ pole.jmeno }}: Mapped[{{ pole.typ_python }}] = mapped_column(
        {{ pole.sa_typ }}{% if pole.pk %}, primary_key=True{% endif %}{% if pole.unique %}, unique=True{% endif %}{% if pole.index %}, index=True{% endif %}{% if pole.vychozi is not none %}, default={{ pole.vychozi }}{% endif %}, nullable={{ not pole.required }}
    )
{% endfor %}
{% for rel in model.relace %}
    {{ rel.jmeno }}: Mapped[list["{{ rel.cil }}"]] = relationship(
        "{{ rel.cil }}", back_populates="{{ rel.zpet }}"
    )
{% endfor %}

    def __repr__(self) -> str:
        return f"{{ model.jmeno }}(id={self.id})"

{% endfor %}
"""

SCHEMA = [
    {
        "jmeno":   "Student",
        "popis":   "Záznam studenta v databázi kurzu.",
        "tabulka": "studenti",
        "pole": [
            {"jmeno": "id",         "typ_python": "int",       "sa_typ": "Integer", "pk": True,  "unique": False, "index": False, "required": True,  "vychozi": None},
            {"jmeno": "jmeno",      "typ_python": "str",       "sa_typ": "String(100)", "pk": False, "unique": False, "index": True,  "required": True,  "vychozi": None},
            {"jmeno": "email",      "typ_python": "str",       "sa_typ": "String(200)", "pk": False, "unique": True,  "index": True,  "required": True,  "vychozi": None},
            {"jmeno": "body",       "typ_python": "float",     "sa_typ": "Float",   "pk": False, "unique": False, "index": False, "required": True,  "vychozi": "0.0"},
            {"jmeno": "aktivni",    "typ_python": "bool",      "sa_typ": "Boolean", "pk": False, "unique": False, "index": False, "required": True,  "vychozi": "True"},
            {"jmeno": "vytvoreno",  "typ_python": "datetime",  "sa_typ": "DateTime","pk": False, "unique": False, "index": False, "required": False, "vychozi": None},
        ],
        "relace": [
            {"jmeno": "zapisy", "cil": "Zapis", "zpet": "student"},
        ],
    },
    {
        "jmeno":   "Kurz",
        "popis":   "Kurz v nabídce školy.",
        "tabulka": "kurzy",
        "pole": [
            {"jmeno": "id",     "typ_python": "int", "sa_typ": "Integer", "pk": True,  "unique": False, "index": False, "required": True,  "vychozi": None},
            {"jmeno": "nazev",  "typ_python": "str", "sa_typ": "String(100)", "pk": False, "unique": True,  "index": True,  "required": True,  "vychozi": None},
            {"jmeno": "lektori","typ_python": "str", "sa_typ": "String(200)", "pk": False, "unique": False, "index": False, "required": False, "vychozi": None},
        ],
        "relace": [
            {"jmeno": "zapisy", "cil": "Zapis", "zpet": "kurz"},
        ],
    },
]

vygenerovany_kod = env.from_string(SA_MODEL_SIMPLE).render(
    datum=datetime.now().strftime("%Y-%m-%d"),
    modely=SCHEMA,
)

print(vygenerovany_kod)
Path("vygenerovane_modely.py").write_text(vygenerovany_kod, encoding="utf-8")
print(f"  ✓ vygenerovane_modely.py ({Path('vygenerovane_modely.py').stat().st_size:,} B)")
Path("vygenerovane_modely.py").unlink(missing_ok=True)


# 3. Generátor testovacích pytest fixtures
print("\n=== 3. Generátor pytest fixtures ===\n")

FIXTURE_SABLONA = """\
# Automaticky vygenerované pytest fixtures – {{ datum }}
# Zdroj: {{ zdroj }}

import pytest
from dataclasses import dataclass
from typing import Generator
{% if pouzit_db %}
import sqlite3
{% endif %}

{% for model in modely %}
# ── Fixtures pro {{ model.jmeno }} ─────────────────────────────────

@pytest.fixture
def {{ model.jmeno | lower }}_data() -> dict:
    \"\"\"Testovací data pro {{ model.jmeno }}.\"\"\"
    return {
{% for pole in model.pole %}{% if not pole.pk %}
        "{{ pole.jmeno }}": {{ pole.testovaci_hodnota }},
{% endif %}{% endfor %}
    }

@pytest.fixture
def {{ model.jmeno | lower }}_seznam() -> list[dict]:
    \"\"\"Seznam testovacích {{ model.jmeno }} objektů.\"\"\"
    return [
{% for i in range(3) %}
        {
{% for pole in model.pole %}{% if not pole.pk %}
            "{{ pole.jmeno }}": {{ pole.testovaci_hodnota_vzor.format(i=i+1) }},
{% endif %}{% endfor %}
        },
{% endfor %}
    ]

{% if pouzit_db %}
@pytest.fixture
def {{ model.jmeno | lower }}_db(tmp_path) -> Generator:
    \"\"\"SQLite databáze s {{ model.jmeno }} tabulkou.\"\"\"
    db_cesta = tmp_path / "test_{{ model.tabulka }}.db"
    conn = sqlite3.connect(str(db_cesta))
    conn.execute(\"\"\"
        CREATE TABLE {{ model.tabulka }} (
{% for pole in model.pole %}
            {{ pole.jmeno }} {{ pole.db_typ }}{% if pole.pk %} PRIMARY KEY{% endif %}{% if not loop.last %},{% endif %}

{% endfor %}
        )
    \"\"\")
    conn.commit()
    yield conn
    conn.close()
{% endif %}

{% endfor %}
"""

FIXTURES_SCHEMA = [
    {
        "jmeno":   "Student",
        "tabulka": "studenti",
        "pole": [
            {"jmeno": "id",      "pk": True,  "testovaci_hodnota": "1",            "testovaci_hodnota_vzor": "{i}",            "db_typ": "INTEGER"},
            {"jmeno": "jmeno",   "pk": False, "testovaci_hodnota": '"Testovaci Student"', "testovaci_hodnota_vzor": '"Student {i}"',   "db_typ": "TEXT NOT NULL"},
            {"jmeno": "email",   "pk": False, "testovaci_hodnota": '"test@example.com"',  "testovaci_hodnota_vzor": '"student{i}@test.cz"',"db_typ": "TEXT UNIQUE"},
            {"jmeno": "body",    "pk": False, "testovaci_hodnota": "75.0",          "testovaci_hodnota_vzor": "{i}0.0",         "db_typ": "REAL DEFAULT 0"},
        ],
    },
]

fixtures_kod = env.from_string(FIXTURE_SABLONA).render(
    datum=datetime.now().strftime("%Y-%m-%d"),
    zdroj="89_jinja2.py::generuj_fixtures()",
    modely=FIXTURES_SCHEMA,
    pouzit_db=True,
)

print(fixtures_kod[:800])
print("  ...")

Path("conftest_generated.py").write_text(fixtures_kod, encoding="utf-8")
print(f"\n  ✓ conftest_generated.py ({Path('conftest_generated.py').stat().st_size:,} B)")
Path("conftest_generated.py").unlink(missing_ok=True)

print("\n=== Shrnutí ===")
print("  1. Email šablona    – HTML + text verze, tabulka, tlačítko")
print("  2. SQLAlchemy model – generování z JSON schématu")
print("  3. Pytest fixtures  – generování conftest.py z datového modelu")
