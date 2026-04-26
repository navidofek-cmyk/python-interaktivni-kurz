"""
LEKCE 33: Metaklasy – třídy tříd
===================================
Z dokumentace: "Determining the appropriate metaclass" (3.3.3.4)

Normální hierarchie:
  instance  → třída     (Míša je Hrac)
  třída     → metaklasa (Hrac je type)

Třída je objekt. `type` je třída, která vyrábí třídy.
Metaklasa je třída, která vyrábí třídy jinak než `type`.

Kdy to potřebuješ?
  - Automatická registrace podtříd (pluginy, ORM)
  - Validace třídy při definici
  - Přidání metod/atributů ke všem třídám v hierarchii
  - Implementace singletonů, ABCs

V praxi: ABCMeta, ORMMeta (Django Model), ...
Většinou stačí __init_subclass__ nebo class dekorátory – méně magie.
"""

# ══════════════════════════════════════════════════════════════
# ČÁST 1: type() – základ všeho
# ══════════════════════════════════════════════════════════════

print("=== type() je metaklasa ===\n")

print(f"type(42)        = {type(42)}")
print(f"type(int)       = {type(int)}")
print(f"type(type)      = {type(type)}")   # type je svou vlastní metaklasou

# Dynamické vytvoření třídy pomocí type()
# type(jmeno, baze, slovnik_atributu)
Bod = type("Bod", (), {
    "__init__": lambda self, x, y: setattr(self, "x", x) or setattr(self, "y", y),
    "__repr__": lambda self: f"Bod({self.x}, {self.y})",
    "vzdalenost": lambda self: (self.x**2 + self.y**2)**0.5,
})

b = Bod(3, 4)
print(f"\nDynamicky vytvořená třída: {b}, vzdálenost={b.vzdalenost()}")
print(f"type(Bod) = {type(Bod)}")


# ══════════════════════════════════════════════════════════════
# ČÁST 2: Vlastní metaklasa
# ══════════════════════════════════════════════════════════════

print("\n=== Vlastní metaklasa ===\n")

class ValidacniMeta(type):
    """Metaklasa, která při definici třídy ověří, že má povinné metody."""

    POVINNE = ()   # podtřídy mohou přepsat

    def __new__(mcs, jmeno, baze, slovnik):
        cls = super().__new__(mcs, jmeno, baze, slovnik)
        povinne = slovnik.get("_povinne_metody", ())
        for metoda in povinne:
            if metoda not in slovnik and not any(
                metoda in vars(b) for b in baze
            ):
                raise TypeError(
                    f"Třída {jmeno!r} musí implementovat metodu {metoda!r}"
                )
        return cls

    def __init__(cls, jmeno, baze, slovnik):
        super().__init__(jmeno, baze, slovnik)
        print(f"  [Meta] Třída {jmeno!r} byla vytvořena.")


class Tvar(metaclass=ValidacniMeta):
    _povinne_metody = ("obsah", "obvod")

    def popis(self):
        return f"{type(self).__name__}: obsah={self.obsah():.2f}, obvod={self.obvod():.2f}"


class Kruh(Tvar):
    def __init__(self, r):   self.r = r
    def obsah(self):          return 3.14159 * self.r ** 2
    def obvod(self):          return 2 * 3.14159 * self.r

class Obdelnik(Tvar):
    def __init__(self, a, b): self.a, self.b = a, b
    def obsah(self):           return self.a * self.b
    def obvod(self):           return 2 * (self.a + self.b)

print()
for t in [Kruh(5), Obdelnik(4, 6)]:
    print(" ", t.popis())

# Pokus o třídu bez povinné metody
print()
try:
    class SpatnyCTverec(Tvar):
        def obsah(self): return 0
        # chybí obvod!
except TypeError as e:
    print(f"Metaklasa odmítla třídu: {e}")


# ══════════════════════════════════════════════════════════════
# ČÁST 3: __init_subclass__ – moderní alternativa k metaclass
# ══════════════════════════════════════════════════════════════

print("\n=== __init_subclass__ (Python 3.6+) ===\n")

class Plugin:
    """Automatická registrace podtříd jako pluginů."""
    _registry: dict[str, type] = {}

    def __init_subclass__(cls, nazev: str | None = None, **kwargs):
        super().__init_subclass__(**kwargs)
        klic = nazev or cls.__name__.lower()
        Plugin._registry[klic] = cls
        print(f"  [Plugin] Registrováno: {klic!r} → {cls.__name__}")

    @classmethod
    def ziskej(cls, nazev: str) -> "Plugin":
        if nazev not in cls._registry:
            raise KeyError(f"Plugin {nazev!r} nenalezen")
        return cls._registry[nazev]()

class JsonPlugin(Plugin, nazev="json"):
    def zpracuj(self, data): return f"JSON: {data}"

class CsvPlugin(Plugin, nazev="csv"):
    def zpracuj(self, data): return f"CSV: {data}"

class XmlPlugin(Plugin):            # nazev = "xmlplugin" (defaultně)
    def zpracuj(self, data): return f"XML: {data}"

print(f"\nRegistr: {list(Plugin._registry.keys())}")
for nazev in ["json", "csv", "xmlplugin"]:
    p = Plugin.ziskej(nazev)
    print(f"  {nazev}: {p.zpracuj({'klic': 'hodnota'})}")


# ══════════════════════════════════════════════════════════════
# ČÁST 4: Singleton přes metaklasu
# ══════════════════════════════════════════════════════════════

print("\n=== Singleton metaclass ===\n")

class SingletonMeta(type):
    _instance: dict = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instance:
            cls._instance[cls] = super().__call__(*args, **kwargs)
        return cls._instance[cls]

class Konfigurace(metaclass=SingletonMeta):
    def __init__(self):
        self.debug   = False
        self.verze   = "1.0"
        self.databaze = "sqlite:///db.sqlite3"

k1 = Konfigurace()
k2 = Konfigurace()
k1.debug = True

print(f"k1 is k2: {k1 is k2}")          # True – stejný objekt
print(f"k2.debug: {k2.debug}")           # True – sdílí stav

# ══════════════════════════════════════════════════════════════
# ČÁST 5: ABCMeta – abstraktní třídy (z abc modulu)
# ══════════════════════════════════════════════════════════════

print("\n=== ABCMeta (abc modul) ===\n")

from abc import ABC, abstractmethod

class Zvire(ABC):
    @abstractmethod
    def zvuk(self) -> str: ...

    @abstractmethod
    def pohyb(self) -> str: ...

    def popis(self):   # konkrétní metoda může existovat
        return f"{type(self).__name__}: {self.zvuk()}, {self.pohyb()}"

class Pes(Zvire):
    def zvuk(self):  return "Haf!"
    def pohyb(self): return "běhá"

class Ryba(Zvire):
    def zvuk(self):  return "(ticho)"
    def pohyb(self): return "plave"

for z in [Pes(), Ryba()]:
    print(" ", z.popis())

try:
    Zvire()   # nelze instantiovat abstraktní třídu
except TypeError as e:
    print(f"\nABC: {e}")

print(f"\ntype(Zvire) = {type(Zvire)}")   # ABCMeta

# ── Přehled: kdy co ──────────────────────────────────────────
print("""
=== Kdy co použít ===

  type()              → dynamické vytvoření třídy (zřídka)
  Vlastní metaclass   → framework-level magie (ORM, validace)
  __init_subclass__   → registrace podtříd, plugin systém ✓ (preferováno)
  @dataclass          → automatická generace __init__ atd.  ✓ (preferováno)
  ABC + @abstractmethod → vynucení rozhraní                 ✓ (preferováno)
  Protocol            → duck typing bez dědičnosti          ✓ (preferováno)
""")

# TVOJE ÚLOHA:
# 1. Přidej do Plugin._registry výpis všech pluginů s metodou Plugin.seznam().
# 2. Napiš metaklasu LogMeta, která obalí každou metodu logováním volání.
# 3. Napiš ABC Serizovatelny s abstraktními metodami uloz() a nacti()
#    a implementuj ho pro JsonSerizovatelny a BinarySerizovatelny.
