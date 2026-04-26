"""
LEKCE 51: Pydantic – validace dat a settings
=============================================
pip install pydantic pydantic-settings python-dotenv

Pydantic = validace dat pomocí type hints.
  - Parsuje a validuje vstupní data (JSON, dict, env)
  - Generuje JSON Schema
  - Používá ho FastAPI, SQLModel, a stovky dalších knihoven

Kdy použít:
  - Validace API requestů / odpovědí
  - Načítání konfigurace z .env souborů
  - Parsování externích dat (JSON, CSV)
  - Type-safe dataclasses s validací
"""

try:
    from pydantic import (
        BaseModel, Field, field_validator, model_validator,
        ValidationError, EmailStr, HttpUrl, computed_field,
        ConfigDict,
    )
    from pydantic_settings import BaseSettings
    PYDANTIC_OK = True
except ImportError:
    print("Pydantic není nainstalováno.")
    print("Spusť: pip install pydantic pydantic-settings python-dotenv")
    print("\nUkazuji kód – install a spusť znovu pro výstup.\n")
    PYDANTIC_OK = False

from datetime import datetime, date
from typing import Annotated
from pathlib import Path
import json

# ══════════════════════════════════════════════════════════════
# ČÁST 1: BaseModel – základy
# ══════════════════════════════════════════════════════════════

print("=== Základní BaseModel ===\n")

if PYDANTIC_OK:
    class Student(BaseModel):
        jmeno:   str
        email:   str
        vek:     int = Field(ge=0, le=150, description="Věk v letech")
        body:    float = Field(default=0.0, ge=0, le=100)
        aktivni: bool = True
        tagy:    list[str] = []

    # Parsování z dict
    s1 = Student(jmeno="Míša", email="misa@example.com", vek=15, body=87.5)
    print(f"Student: {s1}")
    print(f"  jmeno={s1.jmeno!r}, vek={s1.vek}, body={s1.body}")
    print(f"  JSON: {s1.model_dump_json()}")

    # Automatická konverze typů
    s2 = Student(jmeno="Tomáš", email="t@t.cz", vek="16", body="92.0")
    print(f"\nAuto-konverze str→int: vek={s2.vek!r} (type: {type(s2.vek).__name__})")

    # Validační chyby
    print("\nValidační chyby:")
    try:
        Student(jmeno="X", email="ne-email", vek=200, body=-5)
    except ValidationError as e:
        for err in e.errors():
            print(f"  [{err['loc'][0]}] {err['msg']}")


# ══════════════════════════════════════════════════════════════
# ČÁST 2: Field validátory
# ══════════════════════════════════════════════════════════════

print("\n=== Validátory ===\n")

if PYDANTIC_OK:
    class Uzivatel(BaseModel):
        model_config = ConfigDict(str_strip_whitespace=True)

        jmeno:    str = Field(min_length=2, max_length=50)
        email:    str
        heslo:    str = Field(min_length=8, exclude=True)  # nezobrazí v JSON!
        narozen:  date | None = None

        @field_validator("email")
        @classmethod
        def validuj_email(cls, v: str) -> str:
            if "@" not in v or "." not in v.split("@")[-1]:
                raise ValueError("Neplatný email")
            return v.lower()

        @field_validator("jmeno")
        @classmethod
        def validuj_jmeno(cls, v: str) -> str:
            if not v.replace(" ", "").isalpha():
                raise ValueError("Jméno smí obsahovat jen písmena")
            return v.title()

        @model_validator(mode="after")
        def zkontroluj_vek(self):
            if self.narozen:
                vek = (date.today() - self.narozen).days // 365
                if vek < 13:
                    raise ValueError(f"Uživatel musí mít alespoň 13 let (má {vek})")
            return self

        @computed_field
        @property
        def zobrazovane_jmeno(self) -> str:
            return f"{self.jmeno} ({self.email})"

    u = Uzivatel(
        jmeno="  jan novák  ",
        email="JAN@Example.COM",
        heslo="tajneheslo",
        narozen=date(2005, 6, 15),
    )
    print(f"Uživatel: {u.model_dump()}")
    print(f"  email normalizován: {u.email!r}")
    print(f"  jmeno.title(): {u.jmeno!r}")
    print(f"  zobrazovane_jmeno: {u.zobrazovane_jmeno}")
    print(f"  heslo v JSON: {'heslo' in u.model_dump()}")  # False – exclude=True

    print("\nValidační chyby (vek < 13):")
    try:
        Uzivatel(jmeno="Dítě", email="d@d.cz", heslo="heslo123",
                 narozen=date(2020, 1, 1))
    except ValidationError as e:
        print(f"  {e.errors()[0]['msg']}")


# ══════════════════════════════════════════════════════════════
# ČÁST 3: Vnořené modely a JSON parsing
# ══════════════════════════════════════════════════════════════

print("\n=== Vnořené modely ===\n")

if PYDANTIC_OK:
    class Adresa(BaseModel):
        ulice:  str
        mesto:  str
        psc:    str = Field(pattern=r"^\d{3}\s?\d{2}$")
        zeme:   str = "CZ"

    class Firma(BaseModel):
        nazev:    str
        ico:      str = Field(pattern=r"^\d{8}$")
        adresa:   Adresa
        pobocky:  list[Adresa] = []
        zalozen:  int = Field(ge=1900, le=2100)

    # Parsování z JSON stringu
    json_data = '''
    {
        "nazev": "Python s.r.o.",
        "ico": "12345678",
        "zalozen": 2020,
        "adresa": {"ulice": "Hlavní 1", "mesto": "Praha", "psc": "110 00"},
        "pobocky": [
            {"ulice": "Vedlejší 5", "mesto": "Brno", "psc": "602 00"}
        ]
    }
    '''
    f = Firma.model_validate_json(json_data)
    print(f"Firma: {f.nazev}, IČO: {f.ico}")
    print(f"  Adresa: {f.adresa.ulice}, {f.adresa.mesto}")
    print(f"  Pobočky: {len(f.pobocky)}")

    # Zpět na JSON
    print(f"\nJSON výstup:")
    print(f"  {f.model_dump_json(indent=2)[:200]}...")

    # JSON Schema (pro Swagger atd.)
    schema = Firma.model_json_schema()
    print(f"\nJSON Schema properties: {list(schema['properties'].keys())}")


# ══════════════════════════════════════════════════════════════
# ČÁST 4: BaseSettings – konfigurace z .env
# ══════════════════════════════════════════════════════════════

print("\n=== BaseSettings – konfigurace ===\n")

# Vytvoř demo .env soubor
env_soubor = Path(".env.demo")
env_soubor.write_text("""
APP_NAME=MujKurz
DEBUG=true
DATABASE_URL=sqlite:///kurz.db
MAX_STUDENTI=100
SECRET_KEY=super-tajny-klic-123
""".strip())

if PYDANTIC_OK:
    try:
        from pydantic_settings import BaseSettings, SettingsConfigDict

        class AppSettings(BaseSettings):
            model_config = SettingsConfigDict(
                env_file=".env.demo",
                env_file_encoding="utf-8",
                case_sensitive=False,
            )

            app_name:     str   = "DefaultApp"
            debug:        bool  = False
            database_url: str   = "sqlite:///default.db"
            max_studenti: int   = 50
            secret_key:   str   = Field(min_length=16)

            @computed_field
            @property
            def je_vyvoj(self) -> bool:
                return self.debug

        cfg = AppSettings()
        print(f"  app_name:     {cfg.app_name}")
        print(f"  debug:        {cfg.debug}")
        print(f"  database_url: {cfg.database_url}")
        print(f"  max_studenti: {cfg.max_studenti}")
        print(f"  je_vyvoj:     {cfg.je_vyvoj}")
        print(f"  secret_key:   {'*' * len(cfg.secret_key)}")

    except ImportError:
        print("  pydantic-settings není nainstalováno: pip install pydantic-settings")

env_soubor.unlink(missing_ok=True)

print("""
=== Kdy Pydantic vs dataclass ===

  @dataclass     → jednoduché datové třídy, žádná validace
  Pydantic       → validace, parsování JSON/dict, API modely, settings
  attrs          → výkon + validace, méně magic
  TypedDict      → jen type hints pro slovníky, žádné runtime objekty
""")

# TVOJE ÚLOHA:
# 1. Přidej do Student computed_field 'prospiva' → True pokud body >= 50.
# 2. Vytvoř model Objednavka s položkami (list[Polozka]) a computed total_cena.
# 3. Načti nastavení z reálného .env souboru a validuj přítomnost SECRET_KEY.
