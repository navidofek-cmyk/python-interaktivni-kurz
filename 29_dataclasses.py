"""
LEKCE 29: @dataclass – třídy bez zbytečného kódu
==================================================
Normální třída pro data vyžaduje spoustu boilerplate:
    __init__, __repr__, __eq__, __hash__...

@dataclass to vygeneruje automaticky.
Python 3.12 dokumentace: dataclasses modul.
"""

from dataclasses import dataclass, field, asdict, astuple
from typing import ClassVar
import json

# ══════════════════════════════════════════════════════════════
# ČÁST 1: ZÁKLADY
# ══════════════════════════════════════════════════════════════

# Bez @dataclass – ruční práce:
class BodRucne:
    def __init__(self, x, y):
        self.x = x
        self.y = y
    def __repr__(self):
        return f"BodRucne(x={self.x}, y={self.y})"
    def __eq__(self, other):
        return self.x == other.x and self.y == other.y

# S @dataclass – Python vygeneruje __init__, __repr__, __eq__:
@dataclass
class Bod:
    x: float
    y: float

print("=== Základní @dataclass ===")
a = Bod(3.0, 4.0)
b = Bod(3.0, 4.0)
c = Bod(1.0, 2.0)
print(a)             # Bod(x=3.0, y=4.0)  ← __repr__ zdarma
print(a == b)        # True               ← __eq__ zdarma
print(a == c)        # False


# ── Výchozí hodnoty a field() ────────────────────────────────

@dataclass
class Hrac:
    jmeno:    str
    hp:       int   = 100
    utok:     int   = 15
    inventar: list  = field(default_factory=list)  # ← DŮLEŽITÉ: ne []!
    level:    int   = field(default=1, repr=False)  # skryj z repr

    # Vypočítaný atribut po __init__
    def __post_init__(self):
        self.max_hp = self.hp    # uložíme počáteční HP

    @property
    def je_nazivu(self):
        return self.hp > 0

    def lec(self, mnozstvi: int = 20):
        self.hp = min(self.max_hp, self.hp + mnozstvi)

print("\n=== Hrac dataclass ===")
h1 = Hrac("Míša")
h2 = Hrac("Tomáš", hp=80, utok=22)
h1.inventar.append("meč")   # každý hráč má VLASTNÍ seznam (díky field)
print(h1)
print(h2)
print(f"Míša naživu: {h1.je_nazivu}")


# ── frozen=True – neměnný datový objekt ──────────────────────

@dataclass(frozen=True)
class RGB:
    r: int
    g: int
    b: int

    def __str__(self):
        return f"#{self.r:02X}{self.g:02X}{self.b:02X}"

    def smichej(self, other):
        return RGB((self.r+other.r)//2, (self.g+other.g)//2, (self.b+other.b)//2)

print("\n=== Frozen dataclass (barvy) ===")
cervena  = RGB(255, 0, 0)
modra    = RGB(0, 0, 255)
fialova  = cervena.smichej(modra)
print(cervena, modra, "→", fialova)

try:
    cervena.r = 128   # TypeError – frozen!
except TypeError as e:
    print(f"Frozen: {e}")

# frozen=True umožňuje hashování (použití jako klíč slovníku/množiny)
paleta = {cervena, modra, fialova}
print(f"Paleta: {paleta}")


# ── order=True – automatické porovnávání ─────────────────────

@dataclass(order=True)
class Karta:
    # sort_index se používá pro porovnávání (field compare)
    sort_index: int = field(init=False, repr=False)
    hodnota: str
    barva:   str

    HODNOTY = "2 3 4 5 6 7 8 9 10 J Q K A".split()

    def __post_init__(self):
        self.sort_index = self.HODNOTY.index(self.hodnota)

    def __str__(self):
        return f"{self.hodnota}{self.barva}"

print("\n=== Karta s order=True ===")
ruka = [Karta("7","♥"), Karta("A","♠"), Karta("3","♣"), Karta("K","♦")]
print("Před:", [str(k) for k in ruka])
ruka.sort()
print("Po:  ", [str(k) for k in ruka])


# ══════════════════════════════════════════════════════════════
# ČÁST 2: SERIALIZACE
# ══════════════════════════════════════════════════════════════

@dataclass
class Zbran:
    nazev:   str
    utok:    int
    typ:     str = "melee"

@dataclass
class Postava:
    jmeno:  str
    hp:     int
    zbran:  Zbran
    tagy:   list[str] = field(default_factory=list)

    pocet_instanci: ClassVar[int] = 0  # sdílené mezi instancemi

    def __post_init__(self):
        Postava.pocet_instanci += 1

print("\n=== Serializace (asdict / json) ===")
hrdina = Postava(
    jmeno="Alžběta",
    hp=90,
    zbran=Zbran("Elfský luk", utok=30, typ="ranged"),
    tagy=["elf", "ranger"],
)

slovnik = asdict(hrdina)    # rekurzivně převede na dict
print(json.dumps(slovnik, ensure_ascii=False, indent=2))

# Zpět ze slovníku
obnoveny = Postava(
    jmeno=slovnik["jmeno"],
    hp=slovnik["hp"],
    zbran=Zbran(**slovnik["zbran"]),
    tagy=slovnik["tagy"],
)
print(f"\nObnoveno: {obnoveny.jmeno}, HP:{obnoveny.hp}, "
      f"Zbraň:{obnoveny.zbran.nazev}")
print(f"Celkem instancí Postava: {Postava.pocet_instanci}")


# ── Praktický příklad: konfigurace ───────────────────────────

@dataclass
class Config:
    host:    str  = "localhost"
    port:    int  = 8080
    debug:   bool = False
    timeout: float = 30.0

    def adresa(self):
        return f"http://{self.host}:{self.port}"

print("\n=== Config dataclass ===")
vychozi = Config()
produkcni = Config(host="api.example.com", port=443, timeout=10.0)
print(vychozi.adresa())
print(produkcni.adresa())
print(asdict(produkcni))

# TVOJE ÚLOHA:
# 1. Přidej do Hrac metodu do_dict() a from_dict(d) pro uložení/načtení ze souboru.
# 2. Vytvoř @dataclass Zbozi(nazev, cena, ks) a napiš funkci
#    nejdrazsi(seznam_zbozi) → vrátí nejdražší položku.
# 3. Napiš frozen @dataclass GeoPoint(lat, lon) s metodou vzdalenost(other)
#    (Haversine formula nebo jednoduchá Euclidean pro začátek).
