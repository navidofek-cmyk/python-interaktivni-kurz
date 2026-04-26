"""
LEKCE 24: Magic methods (dunder metody)
========================================
Metody se dvěma podtržítky na každé straně: __tohle__.
Python je volá automaticky – jsou "za oponou" každé operace.

__init__    → volá se při obj = Trida()
__str__     → volá se při print(obj)
__repr__    → volá se v konzoli / pro debugování
__len__     → volá se při len(obj)
__add__     → volá se při obj1 + obj2
__eq__      → volá se při obj1 == obj2
__lt__      → volá se při obj1 < obj2
__contains__→ volá se při x in obj
__iter__    → volá se při for x in obj
__getitem__ → volá se při obj[index]
"""

# ── Vektor – matematický příklad ──────────────────────────────────────────────

class Vektor:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __str__(self):            # pro uživatele
        return f"Vektor({self.x}, {self.y})"

    def __repr__(self):           # pro vývojáře / debugování
        return f"Vektor(x={self.x!r}, y={self.y!r})"

    def __add__(self, other):     # v1 + v2
        return Vektor(self.x + other.x, self.y + other.y)

    def __sub__(self, other):     # v1 - v2
        return Vektor(self.x - other.x, self.y - other.y)

    def __mul__(self, skalar):    # v * 3
        return Vektor(self.x * skalar, self.y * skalar)

    def __eq__(self, other):      # v1 == v2
        return self.x == other.x and self.y == other.y

    def __abs__(self):            # abs(v) = délka vektoru
        return (self.x**2 + self.y**2) ** 0.5

    def __neg__(self):            # -v
        return Vektor(-self.x, -self.y)

print("=== Vektor ===")
a = Vektor(3, 4)
b = Vektor(1, 2)
print(a)            # __str__
print(repr(a))      # __repr__
print(a + b)        # __add__
print(a - b)        # __sub__
print(a * 3)        # __mul__
print(a == b)       # __eq__
print(abs(a))       # __abs__ → délka = 5.0
print(-a)           # __neg__


# ── Inventář – kontejnerový příklad ──────────────────────────────────────────

class Inventar:
    def __init__(self, kapacita=10):
        self._predmety = []
        self.kapacita  = kapacita

    def __str__(self):
        return f"Inventář ({len(self)}/{self.kapacita}): {self._predmety}"

    def __len__(self):            # len(inv)
        return len(self._predmety)

    def __contains__(self, item): # "meč" in inv
        return item in self._predmety

    def __getitem__(self, index): # inv[0]
        return self._predmety[index]

    def __iter__(self):           # for predmet in inv
        return iter(self._predmety)

    def __bool__(self):           # if inv:
        return len(self._predmety) > 0

    def pridej(self, predmet):
        if len(self) >= self.kapacita:
            print(f"  Inventář plný! Nelze přidat '{predmet}'.")
        else:
            self._predmety.append(predmet)

    def odeber(self, predmet):
        if predmet in self:
            self._predmety.remove(predmet)
        else:
            print(f"  '{predmet}' v inventáři není.")

print("\n=== Inventář ===")
inv = Inventar(kapacita=5)
inv.pridej("meč")
inv.pridej("štít")
inv.pridej("lektvar")
inv.pridej("mapa")

print(inv)                      # __str__
print(f"Počet: {len(inv)}")     # __len__
print(f"Má meč? {'meč' in inv}")     # __contains__
print(f"První: {inv[0]}")       # __getitem__

print("\nVšechny předměty:")
for p in inv:                   # __iter__
    print(f"  - {p}")

if inv:                         # __bool__
    print("Inventář není prázdný.")

inv.odeber("štít")
print(inv)


# ── Karta – porovnávání ───────────────────────────────────────────────────────

class Karta:
    HODNOTY = ["2","3","4","5","6","7","8","9","10","J","Q","K","A"]
    BARVY   = ["♣","♦","♥","♠"]

    def __init__(self, hodnota, barva):
        self.hodnota = hodnota
        self.barva   = barva
        self._rank   = self.HODNOTY.index(hodnota)

    def __str__(self):
        return f"{self.hodnota}{self.barva}"

    def __repr__(self):
        return f"Karta({self.hodnota!r}, {self.barva!r})"

    def __eq__(self, other): return self._rank == other._rank
    def __lt__(self, other): return self._rank <  other._rank
    def __le__(self, other): return self._rank <= other._rank

print("\n=== Karty ===")
k1 = Karta("A", "♠")
k2 = Karta("7", "♥")
k3 = Karta("K", "♣")

print(f"{k1} vs {k2}: A > 7 ? {k1 > k2}")   # __gt__ z __lt__
print(f"{k2} vs {k3}: 7 < K ? {k2 < k3}")

ruka = [k3, k1, k2]
print(f"Ruka před tříděním: {[str(k) for k in ruka]}")
ruka.sort()   # funguje protože máme __lt__
print(f"Ruka po třídění:    {[str(k) for k in ruka]}")

# TVOJE ÚLOHA:
# 1. Přidej do Vektor __truediv__(self, skalar) pro dělení: v / 2.
# 2. Přidej do Inventar __add__(self, other) pro sloučení dvou inventářů.
# 3. Přidej do Karta __mul__ tak aby Karta("A","♠") * 3 vrátilo bodovou hodnotu.
