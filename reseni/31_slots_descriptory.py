"""Řešení – Lekce 31: __slots__ a Descriptory"""

import sys
import functools


# 1. Descriptor Nezaporny – odmítne záporná čísla
# Data descriptor (má __get__ i __set__) – kontroluje při každém přiřazení

class Nezaporny:
    """Descriptor: atribut nemůže být záporný."""

    def __set_name__(self, owner, name):
        self._name = f"_{name}"

    def __get__(self, obj, objtype=None):
        if obj is None:
            return self
        return getattr(obj, self._name, 0)

    def __set__(self, obj, value):
        # Odmítáme záporná čísla – vynucujeme invariant třídy
        if value < 0:
            raise ValueError(
                f"{self._name[1:]!r} nemůže být záporné: {value}"
            )
        setattr(obj, self._name, value)


class Zbozi:
    cena = Nezaporny()
    mnozstvi = Nezaporny()

    def __init__(self, nazev, cena, mnozstvi):
        self.nazev = nazev
        self.cena = cena
        self.mnozstvi = mnozstvi

    def __repr__(self):
        return f"Zbozi({self.nazev!r}, cena={self.cena}, ks={self.mnozstvi})"


print("=== Descriptor Nezaporny ===")
z = Zbozi("Jablko", 9.90, 100)
print(z)

z.cena = 12.50
print(f"Po zdražení: {z}")

try:
    z.cena = -5
except ValueError as e:
    print(f"Validace: {e}")

try:
    z.mnozstvi = -10
except ValueError as e:
    print(f"Validace: {e}")


# 2. functools.cached_property – vestavěný ekvivalent LazyVypocet
# cached_property uloží výsledek do __dict__ instance při prvním přístupu
# Výhoda: jednodušší než vlastní descriptor, funguje pro read-only lazy atributy

class Analyza:
    def __init__(self, text: str):
        self.text = text

    @functools.cached_property
    def slova(self):
        print("  (computing slova...)")
        return self.text.lower().split()

    @functools.cached_property
    def unikatni(self):
        print("  (computing unikatni...)")
        return set(self.slova)

    @functools.cached_property
    def cetnosti(self):
        print("  (computing cetnosti...)")
        from collections import Counter
        return Counter(self.slova)


print("\n=== functools.cached_property ===")
a = Analyza("Python je skvělý a Python je rychlý")
print("První přístup (výpočet):")
print(f"  slova: {a.slova}")
print("Druhý přístup (z cache – žádný výpis 'computing'):")
print(f"  slova: {a.slova}")
print(f"  unikátní: {a.unikatni}")
print(f"  top 3: {a.cetnosti.most_common(3)}")


# 3. Matrix2x2 se __slots__ a operacemi
# __slots__ = ("_data",) → jedna ntice 4 čísel, žádný __dict__
# Sloučíme paměťovou efektivitu s matematickou funkcionalitou

class Matrix2x2:
    """2×2 matice s __slots__ pro paměťovou efektivitu."""
    __slots__ = ("_data",)

    def __init__(self, a, b, c, d):
        # Uložíme jako ntici: [[a, b], [c, d]]
        self._data = (a, b, c, d)

    @property
    def a(self): return self._data[0]
    @property
    def b(self): return self._data[1]
    @property
    def c(self): return self._data[2]
    @property
    def d(self): return self._data[3]

    def __repr__(self):
        return (f"Matrix2x2([{self.a}, {self.b}]\n"
                f"          [{self.c}, {self.d}])")

    def __str__(self):
        return f"[[{self.a}, {self.b}], [{self.c}, {self.d}]]"

    def __add__(self, other: "Matrix2x2") -> "Matrix2x2":
        """Sčítání matic: prvek po prvku."""
        return Matrix2x2(
            self.a + other.a, self.b + other.b,
            self.c + other.c, self.d + other.d,
        )

    def __mul__(self, other: "Matrix2x2") -> "Matrix2x2":
        """
        Násobení matic 2×2:
        [[a,b],[c,d]] × [[e,f],[g,h]] = [[ae+bg, af+bh],[ce+dg, cf+dh]]
        """
        return Matrix2x2(
            self.a * other.a + self.b * other.c,
            self.a * other.b + self.b * other.d,
            self.c * other.a + self.d * other.c,
            self.c * other.b + self.d * other.d,
        )

    def det(self) -> float:
        """Determinant matice 2×2: ad - bc."""
        return self.a * self.d - self.b * self.c

    @classmethod
    def jednotkova(cls) -> "Matrix2x2":
        """Vrátí identitní matici (neutrální prvek pro násobení)."""
        return cls(1, 0, 0, 1)


print("\n=== Matrix2x2 se __slots__ ===")
m1 = Matrix2x2(1, 2, 3, 4)
m2 = Matrix2x2(5, 6, 7, 8)
I = Matrix2x2.jednotkova()

print(f"m1 = {m1}")
print(f"m2 = {m2}")
print(f"m1 + m2 = {m1 + m2}")
print(f"m1 × m2 = {m1 * m2}")
print(f"m1 × I  = {m1 * I}  (násobení identitou vrátí původní matici)")
print(f"det(m1) = {m1.det()}")

print(f"\nMá __dict__: {hasattr(m1, '__dict__')}")  # False – díky __slots__
print(f"__slots__: {Matrix2x2.__slots__}")
print(f"Paměť instance: {sys.getsizeof(m1)} B (bez __dict__ slovníku)")

try:
    m1.novy_atribut = 42
except AttributeError as e:
    print(f"Nelze přidat atribut: {e}")
