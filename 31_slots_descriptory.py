"""
LEKCE 31: __slots__ a Descriptory
====================================
Dvě věci z dokumentace (Data Model), které jsou "za oponou"
každé třídy v Pythonu.

__SLOTS__
  Normálně každý objekt nese slovník __dict__ pro atributy.
  __slots__ ho nahradí pevným polem → méně paměti, rychlejší přístup.

DESCRIPTOR
  Objekt, který řídí přístup k atributu jiného objektu.
  Implementuje __get__, __set__, __delete__.
  Takto fungují property, classmethod, staticmethod uvnitř.
"""

import sys
import time

# ══════════════════════════════════════════════════════════════
# ČÁST 1: __slots__
# ══════════════════════════════════════════════════════════════

print("=== __slots__ – paměťová optimalizace ===\n")

class BezSlots:
    def __init__(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z

class SeSlots:
    __slots__ = ("x", "y", "z")   # ← žádný __dict__, jen tato pole

    def __init__(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z

a = BezSlots(1, 2, 3)
b = SeSlots(1, 2, 3)

print(f"BezSlots.__dict__: {a.__dict__}")
print(f"SeSlots – žádný __dict__:", hasattr(b, "__dict__"))
print(f"SeSlots.__slots__: {b.__slots__}")

# Paměť
print(f"\nPaměť jedné instance:")
print(f"  BezSlots: {sys.getsizeof(a)} B + {sys.getsizeof(a.__dict__)} B (dict)")
print(f"  SeSlots:  {sys.getsizeof(b)} B  (žádný dict)")

# Velká kolekce – viditelný rozdíl
N = 500_000
t0 = time.perf_counter()
bez = [BezSlots(i, i*2, i*3) for i in range(N)]
t1 = time.perf_counter()
se  = [SeSlots(i, i*2, i*3)  for i in range(N)]
t2 = time.perf_counter()

print(f"\n{N:_} instancí:")
print(f"  BezSlots: {t1-t0:.3f}s")
print(f"  SeSlots:  {t2-t1:.3f}s")

# Co __slots__ neumožňuje
try:
    b.novy_atribut = 42   # AttributeError – mimo __slots__
except AttributeError as e:
    print(f"\nNelze přidat atribut mimo __slots__: {e}")

# __slots__ + dědičnost – pozor!
class Zaklad:
    __slots__ = ("x",)

class Potomek(Zaklad):
    __slots__ = ("y",)   # přidá jen 'y'; 'x' zdědí

p = Potomek()
p.x = 1
p.y = 2
print(f"\nDědičnost: p.x={p.x}, p.y={p.y}, má __dict__: {hasattr(p,'__dict__')}")

class PotomekBezSlots(Zaklad):
    pass   # zapomněl definovat __slots__ → dostane __dict__ zpět!

pb = PotomekBezSlots()
pb.x = 1
pb.cokoliv = "oops"   # funguje, protože pb má __dict__
print(f"PotomekBezSlots – má __dict__: {hasattr(pb,'__dict__')}")


# ══════════════════════════════════════════════════════════════
# ČÁST 2: DESCRIPTORY
# ══════════════════════════════════════════════════════════════

print("\n=== Descriptory ===\n")

# ── Non-data descriptor (jen __get__) ────────────────────────
# Typický příklad: metody – jsou non-data descriptory!

class LazyVypocet:
    """Vypočítá hodnotu jen jednou, pak ji uloží do instance."""
    def __init__(self, funkce):
        self.funkce = funkce
        self.nazev  = None

    def __set_name__(self, owner, name):   # zavolá se při definici třídy
        self.nazev = name

    def __get__(self, obj, objtype=None):
        if obj is None:            # přístup přes třídu, ne instanci
            return self
        hodnota = self.funkce(obj)
        setattr(obj, self.nazev, hodnota)  # přepíše descriptor v __dict__
        return hodnota

class Dokument:
    def __init__(self, text):
        self.text = text

    @LazyVypocet
    def slova(self):
        print("  (počítám slova...)")
        return self.text.split()

    @LazyVypocet
    def pocet_znaku(self):
        print("  (počítám znaky...)")
        return len(self.text)

print("--- Lazy descriptor ---")
d = Dokument("Ahoj krásný Pythone jak se máš")
print("První přístup k slova:")
print(d.slova)      # spočítá
print("Druhý přístup k slova:")
print(d.slova)      # z cache, bez výpisu


# ── Data descriptor (__get__ + __set__) ──────────────────────
# Typický příklad: property, validované atributy

class Rozsah:
    """Atribut, který vždy zůstane v rozsahu [min, max]."""
    def __init__(self, min_val, max_val):
        self.min_val = min_val
        self.max_val = max_val
        self._name   = None

    def __set_name__(self, owner, name):
        self._name = f"_{name}"

    def __get__(self, obj, objtype=None):
        if obj is None:
            return self
        return getattr(obj, self._name, self.min_val)

    def __set__(self, obj, value):
        if not (self.min_val <= value <= self.max_val):
            raise ValueError(
                f"{self._name[1:]} musí být mezi "
                f"{self.min_val} a {self.max_val}, dostali jsme {value}"
            )
        setattr(obj, self._name, value)

class Hrac:
    hp    = Rozsah(0, 100)
    mana  = Rozsah(0, 200)
    level = Rozsah(1, 99)

    def __init__(self, jmeno):
        self.jmeno = jmeno
        self.hp    = 100
        self.mana  = 150
        self.level = 1

    def __repr__(self):
        return f"Hrac({self.jmeno!r}, hp={self.hp}, mana={self.mana}, lv={self.level})"

print("\n--- Data descriptor (Rozsah) ---")
h = Hrac("Míša")
print(h)
h.hp = 50
print(h)

try:
    h.hp = 200   # mimo rozsah
except ValueError as e:
    print(f"Validace: {e}")

try:
    h.level = 0
except ValueError as e:
    print(f"Validace: {e}")


# ── Typový descriptor (reálný use-case) ──────────────────────

class Typed:
    """Descriptor, který vynucuje typ atributu."""
    def __init__(self, typ, nullable=False):
        self.typ      = typ
        self.nullable = nullable
        self._name    = None

    def __set_name__(self, owner, name):
        self._name = f"_{name}"

    def __get__(self, obj, objtype=None):
        if obj is None: return self
        return getattr(obj, self._name, None)

    def __set__(self, obj, value):
        if value is None and self.nullable:
            setattr(obj, self._name, None)
            return
        if not isinstance(value, self.typ):
            raise TypeError(
                f"Očekáváno {self.typ.__name__}, "
                f"dostali jsme {type(value).__name__}: {value!r}"
            )
        setattr(obj, self._name, value)

class Produkt:
    nazev  = Typed(str)
    cena   = Typed((int, float))
    popis  = Typed(str, nullable=True)

    def __init__(self, nazev, cena, popis=None):
        self.nazev = nazev
        self.cena  = cena
        self.popis = popis

    def __repr__(self):
        return f"Produkt({self.nazev!r}, {self.cena} Kč)"

print("\n--- Typed descriptor ---")
p = Produkt("Boty", 599.0)
print(p)
p.popis = None   # nullable=True → OK
p.cena = 649

try:
    p.nazev = 123
except TypeError as e:
    print(f"Typová chyba: {e}")


# ── property je descriptor ────────────────────────────────────
print("\n--- property = syntaktický cukr pro descriptor ---")

class Teplota:
    def __init__(self, celsius=0):
        self._celsius = celsius

    @property
    def celsius(self):
        return self._celsius

    @celsius.setter
    def celsius(self, hodnota):
        if hodnota < -273.15:
            raise ValueError("Pod absolutní nulou nelze!")
        self._celsius = hodnota

    @property
    def fahrenheit(self):
        return self._celsius * 9/5 + 32

    @property
    def kelvin(self):
        return self._celsius + 273.15

t = Teplota(100)
print(f"100°C = {t.fahrenheit}°F = {t.kelvin} K")
t.celsius = -10
print(f"-10°C = {t.fahrenheit}°F")

try:
    t.celsius = -300
except ValueError as e:
    print(f"Fyzika říká ne: {e}")

# TVOJE ÚLOHA:
# 1. Přidej descriptor Nezaporny, který odmítne záporná čísla.
# 2. Napiš LazyVypocet2 pomocí functools.cached_property (vestavěný ekvivalent).
# 3. Napiš třídu Matrix2x2 se __slots__ = ("_data",) a metodami
#    pro sčítání a násobení matic.
