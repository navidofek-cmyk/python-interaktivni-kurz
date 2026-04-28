"""Reseni – Lekce 51: Pydantic"""

from datetime import date
from typing import Any
from pathlib import Path

try:
    from pydantic import BaseModel, Field, field_validator, computed_field, ValidationError
    PYDANTIC_OK = True
except ImportError:
    print("Pydantic neni nainstalovano: pip install pydantic")
    PYDANTIC_OK = False


# 1. Pridat do Student computed_field 'prospiva' → True pokud body >= 50

print("=== Ukol 1: Student s computed_field prospiva ===\n")

if PYDANTIC_OK:
    class Student(BaseModel):
        jmeno:   str
        email:   str
        vek:     int = Field(ge=0, le=150)
        body:    float = Field(default=0.0, ge=0, le=100)
        aktivni: bool = True

        @computed_field
        @property
        def prospiva(self) -> bool:
            """True pokud student ma alespon 50 bodu."""
            return self.body >= 50

        @computed_field
        @property
        def znamka(self) -> str:
            """Slovni ohodnoceni dle bodu."""
            if self.body >= 90:
                return "Vyborne"
            elif self.body >= 75:
                return "Chvalitebne"
            elif self.body >= 60:
                return "Dobre"
            elif self.body >= 50:
                return "Dostatecne"
            return "Nedostatecne"

    studenti_data = [
        {"jmeno": "Misa",  "email": "m@k.cz", "vek": 15, "body": 87.5},
        {"jmeno": "Tomas", "email": "t@k.cz", "vek": 16, "body": 45.0},
        {"jmeno": "Bara",  "email": "b@k.cz", "vek": 14, "body": 60.0},
    ]

    for d in studenti_data:
        s = Student(**d)
        print(f"  {s.jmeno:<8} body={s.body:5.1f}  prospiva={s.prospiva}  znamka={s.znamka}")


# 2. Model Objednavka s polozkami a computed total_cena

print("\n=== Ukol 2: Objednavka s computed total_cena ===\n")

if PYDANTIC_OK:
    class Polozka(BaseModel):
        nazev:    str
        cena:     float = Field(gt=0, description="Cena v Kc")
        mnozstvi: int   = Field(default=1, ge=1)

        @computed_field
        @property
        def subtotal(self) -> float:
            return round(self.cena * self.mnozstvi, 2)

    class Objednavka(BaseModel):
        cislo:    str
        polozky:  list[Polozka]
        sleva_pct: float = Field(default=0.0, ge=0, le=100)

        @computed_field
        @property
        def total_cena(self) -> float:
            """Celkova cena vcetne slevy."""
            zaklad = sum(p.subtotal for p in self.polozky)
            return round(zaklad * (1 - self.sleva_pct / 100), 2)

        @computed_field
        @property
        def pocet_polozek(self) -> int:
            return sum(p.mnozstvi for p in self.polozky)

    obj = Objednavka(
        cislo="OBJ-2024-001",
        polozky=[
            Polozka(nazev="Python kurz", cena=999.0,  mnozstvi=1),
            Polozka(nazev="Kniha",       cena=350.0,  mnozstvi=2),
            Polozka(nazev="Propisky",    cena=25.50,  mnozstvi=5),
        ],
        sleva_pct=10.0,
    )

    print(f"  Objednavka: {obj.cislo}")
    for p in obj.polozky:
        print(f"    {p.nazev:<20} {p.cena:>8.2f} Kc x {p.mnozstvi} = {p.subtotal:.2f} Kc")
    print(f"  Sleva:        {obj.sleva_pct}%")
    print(f"  CELKEM:       {obj.total_cena:.2f} Kc")
    print(f"  Pocet polozek: {obj.pocet_polozek}")


# 3. Nacti nastaveni z .env souboru a validuj pritomnost SECRET_KEY

print("\n=== Ukol 3: Nastaveni z .env souboru ===\n")

env_soubor = Path(".env.reseni")
env_soubor.write_text(
    "APP_NAME=PythonKurz\nDEBUG=false\nDATABASE_URL=sqlite:///reseni.db\nSECRET_KEY=tajny-klic-min16znaku\n",
    encoding="utf-8",
)

try:
    from pydantic_settings import BaseSettings, SettingsConfigDict  # type: ignore

    class AppSettings(BaseSettings):
        model_config = SettingsConfigDict(
            env_file=".env.reseni",
            env_file_encoding="utf-8",
        )

        app_name:     str  = "DefaultApp"
        debug:        bool = False
        database_url: str  = "sqlite:///default.db"
        secret_key:   str  = Field(min_length=16)

    cfg = AppSettings()
    print(f"  app_name:     {cfg.app_name}")
    print(f"  debug:        {cfg.debug}")
    print(f"  database_url: {cfg.database_url}")
    print(f"  secret_key:   {'*' * len(cfg.secret_key)}")

    # Otestuj validaci – chybejici secret_key
    print("\n  Test bez SECRET_KEY (kratky klic):")
    try:
        class StrictSettings(BaseSettings):
            model_config = SettingsConfigDict(env_file=".nonexistent")
            secret_key: str = Field(min_length=16, default="kratky")
        s = StrictSettings()
        # Pydantic 2 validuje default hodnotu
        print(f"  secret_key delka={len(s.secret_key)} (min 16 pozadovano)")
    except Exception as e:
        print(f"  Validace selhala (ocekavano): {type(e).__name__}")

except ImportError:
    # Manualni implementace bez pydantic-settings
    print("  pydantic-settings neni: pip install pydantic-settings")
    print("  Ukazuji rucni parsovani .env:\n")

    def nacti_env(soubor: str) -> dict[str, str]:
        env: dict[str, str] = {}
        for radek in Path(soubor).read_text().splitlines():
            radek = radek.strip()
            if radek and not radek.startswith("#") and "=" in radek:
                k, _, v = radek.partition("=")
                env[k.strip().lower()] = v.strip()
        return env

    env = nacti_env(".env.reseni")
    assert len(env.get("secret_key", "")) >= 16, "SECRET_KEY musi mit alespon 16 znaku!"
    print(f"  Nacteno: app_name={env.get('app_name')!r}")
    print(f"  SECRET_KEY validovan ({len(env.get('secret_key',''))} znaku)")

env_soubor.unlink(missing_ok=True)
