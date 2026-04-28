"""Řešení – Lekce 33: Metaklasy – třídy tříd"""

import functools
import json
import pickle
from abc import ABC, abstractmethod


# ── Systém pluginů z originálu ────────────────────────────────────────────────

class Plugin:
    """Automatická registrace podtříd jako pluginů."""
    _registry: dict[str, type] = {}

    def __init_subclass__(cls, nazev: str | None = None, **kwargs):
        super().__init_subclass__(**kwargs)
        klic = nazev or cls.__name__.lower()
        Plugin._registry[klic] = cls

    @classmethod
    def ziskej(cls, nazev: str) -> "Plugin":
        if nazev not in cls._registry:
            raise KeyError(f"Plugin {nazev!r} nenalezen")
        return cls._registry[nazev]()

    # 1. Metoda seznam() – vypíše všechny dostupné pluginy
    # Centrální registr umožňuje dynamické discovery bez importování
    @classmethod
    def seznam(cls) -> list[str]:
        """Vrátí seznam názvů všech registrovaných pluginů."""
        return sorted(cls._registry.keys())


class JsonPlugin(Plugin, nazev="json"):
    def zpracuj(self, data): return f"JSON: {json.dumps(data)}"

class CsvPlugin(Plugin, nazev="csv"):
    def zpracuj(self, data): return f"CSV: {','.join(str(v) for v in data.values())}"

class XmlPlugin(Plugin):
    def zpracuj(self, data):
        tags = "".join(f"<{k}>{v}</{k}>" for k, v in data.items())
        return f"XML: <root>{tags}</root>"


print("=== Plugin.seznam() ===")
print(f"Dostupné pluginy: {Plugin.seznam()}")
for nazev in Plugin.seznam():
    p = Plugin.ziskej(nazev)
    print(f"  {nazev}: {p.zpracuj({'klic': 'hodnota', 'cislo': 42})}")


# ── 2. Metaklasa LogMeta – logování volání metod ─────────────────────────────
# LogMeta obalí všechny metody (ne dunder) logovacím wrapperem
# Výhoda: nemusíme ručně dekorovat každou metodu – metaklasa to udělá za nás

class LogMeta(type):
    """Metaklasa, která automaticky loguje každé volání veřejné metody."""

    def __new__(mcs, jmeno, baze, slovnik):
        nove = {}
        for attr, hodnota in slovnik.items():
            # Logujeme jen callable veřejné metody (ne __dunder__ a ne _private)
            if callable(hodnota) and not attr.startswith("_"):
                nove[attr] = mcs._obal_logem(hodnota)
            else:
                nove[attr] = hodnota
        return super().__new__(mcs, jmeno, baze, nove)

    @staticmethod
    def _obal_logem(metoda):
        @functools.wraps(metoda)
        def obal(self, *args, **kwargs):
            print(f"  [LOG] {type(self).__name__}.{metoda.__name__}"
                  f"({', '.join(map(repr, args))})")
            vysledek = metoda(self, *args, **kwargs)
            print(f"  [LOG] → {vysledek!r}")
            return vysledek
        return obal


class Kalkulacka(metaclass=LogMeta):
    def secti(self, a, b):
        return a + b

    def odecti(self, a, b):
        return a - b

    def vydel(self, a, b):
        if b == 0:
            raise ZeroDivisionError("Dělení nulou!")
        return a / b


print("\n=== LogMeta – automatické logování ===")
k = Kalkulacka()
k.secti(3, 4)
k.odecti(10, 3)
k.vydel(15, 3)


# ── 3. ABC Serizovatelny s JsonSerizovatelny a BinarySerizovatelny ────────────
# ABC s @abstractmethod vynucuje implementaci rozhraní u podtříd
# Výhoda oproti Protocol: dědičnost zaručí, že třída MUSÍ implementovat metody

class Serizovatelny(ABC):
    """Abstraktní třída pro serializaci objektů."""

    @abstractmethod
    def uloz(self) -> bytes:
        """Serializuje objekt do bytes."""
        ...

    @classmethod
    @abstractmethod
    def nacti(cls, data: bytes) -> "Serizovatelny":
        """Deserializuje objekt z bytes."""
        ...

    def __repr__(self):
        return f"{type(self).__name__}({vars(self)})"


class JsonSerizovatelny(Serizovatelny):
    """JSON serializace – čitelná, ale pomalejší."""

    def __init__(self, payload: dict):
        self.payload = payload

    def uloz(self) -> bytes:
        return json.dumps(self.payload, ensure_ascii=False).encode("utf-8")

    @classmethod
    def nacti(cls, data: bytes) -> "JsonSerizovatelny":
        return cls(json.loads(data.decode("utf-8")))


class BinarySerizovatelny(Serizovatelny):
    """Pickle serializace – rychlá, binární, Pythoní."""

    def __init__(self, hodnota):
        self.hodnota = hodnota

    def uloz(self) -> bytes:
        return pickle.dumps(self.hodnota)

    @classmethod
    def nacti(cls, data: bytes) -> "BinarySerizovatelny":
        return cls(pickle.loads(data))


print("\n=== ABC Serizovatelny ===")

# Nelze instantiovat abstraktní třídu
try:
    Serizovatelny()
except TypeError as e:
    print(f"ABC vynucuje implementaci: {e}")

# Fungující implementace
jobj = JsonSerizovatelny({"python": "skvělý", "verze": 3.12})
bobj = BinarySerizovatelny([1, "dva", 3.0, {"čtyři": 4}])

for obj in [jobj, bobj]:
    bajty = obj.uloz()
    obnoveny = type(obj).nacti(bajty)
    print(f"\n{type(obj).__name__}:")
    print(f"  Velikost: {len(bajty)} bajtů")
    print(f"  Obnoveno: {obnoveny}")
