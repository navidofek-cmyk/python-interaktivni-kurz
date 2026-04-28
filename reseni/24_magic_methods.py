"""Řešení – Lekce 24: Magic methods (dunder metody)"""


# ── Vektor s __truediv__ ──────────────────────────────────────────────────────

class Vektor:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __str__(self):
        return f"Vektor({self.x}, {self.y})"

    def __repr__(self):
        return f"Vektor(x={self.x!r}, y={self.y!r})"

    def __add__(self, other):
        return Vektor(self.x + other.x, self.y + other.y)

    def __sub__(self, other):
        return Vektor(self.x - other.x, self.y - other.y)

    def __mul__(self, skalar):
        return Vektor(self.x * skalar, self.y * skalar)

    # 1. __truediv__ pro dělení vektoru skalárem
    # Dělíme každou složku – hodí se pro normalizaci (v / abs(v))
    def __truediv__(self, skalar):
        if skalar == 0:
            raise ZeroDivisionError("Nelze dělit vektorem nulou")
        return Vektor(self.x / skalar, self.y / skalar)

    def __eq__(self, other):
        return self.x == other.x and self.y == other.y

    def __abs__(self):
        return (self.x**2 + self.y**2) ** 0.5

    def __neg__(self):
        return Vektor(-self.x, -self.y)


print("=== Vektor s __truediv__ ===")
v = Vektor(6, 4)
print(f"v = {v}")
print(f"v / 2 = {v / 2}")           # __truediv__
print(f"Normalizovaný: {v / abs(v)}")  # délka = 1

try:
    v / 0
except ZeroDivisionError as e:
    print(f"Dělení nulou: {e}")


# ── Inventář s __add__ pro sloučení ──────────────────────────────────────────

class Inventar:
    def __init__(self, kapacita=10):
        self._predmety = []
        self.kapacita = kapacita

    def __str__(self):
        return f"Inventář ({len(self)}/{self.kapacita}): {self._predmety}"

    def __len__(self):
        return len(self._predmety)

    def __contains__(self, item):
        return item in self._predmety

    def __getitem__(self, index):
        return self._predmety[index]

    def __iter__(self):
        return iter(self._predmety)

    def __bool__(self):
        return len(self._predmety) > 0

    # 2. __add__ pro sloučení dvou inventářů
    # Nový inventář dostane kapacitu součtu obou, předměty se spojí
    # Pokud součet přesahuje kapacitu, vezmeme jen tolik, co se vejde
    def __add__(self, other):
        nova_kapacita = self.kapacita + other.kapacita
        novy = Inventar(kapacita=nova_kapacita)
        for p in self._predmety + other._predmety:
            novy.pridej(p)
        return novy

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


print("\n=== Inventář s __add__ ===")
inv1 = Inventar(kapacita=3)
inv1.pridej("meč")
inv1.pridej("štít")

inv2 = Inventar(kapacita=3)
inv2.pridej("lektvar")
inv2.pridej("mapa")
inv2.pridej("brnění")

print(f"Inv1: {inv1}")
print(f"Inv2: {inv2}")

slouceny = inv1 + inv2  # __add__
print(f"Sloučený: {slouceny}")


# ── Karta s __mul__ pro bodovou hodnotu ──────────────────────────────────────

class Karta:
    HODNOTY = ["2","3","4","5","6","7","8","9","10","J","Q","K","A"]
    BARVY = ["♣","♦","♥","♠"]
    # Bodové hodnoty pro blackjack
    BODY = {"2":2,"3":3,"4":4,"5":5,"6":6,"7":7,"8":8,"9":9,
            "10":10,"J":10,"Q":10,"K":10,"A":11}

    def __init__(self, hodnota, barva):
        self.hodnota = hodnota
        self.barva = barva
        self._rank = self.HODNOTY.index(hodnota)

    def __str__(self):
        return f"{self.hodnota}{self.barva}"

    def __repr__(self):
        return f"Karta({self.hodnota!r}, {self.barva!r})"

    def __eq__(self, other): return self._rank == other._rank
    def __lt__(self, other): return self._rank < other._rank
    def __le__(self, other): return self._rank <= other._rank

    # 3. __mul__ vrátí bodovou hodnotu karty * koeficient
    # Např. Karta("A","♠") * 3 → 33 (ace je 11 bodů × 3)
    # Použití: výpočet skóre v blackjacku nebo jiných hrách
    def __mul__(self, koeficient):
        return self.BODY[self.hodnota] * koeficient

    def __rmul__(self, koeficient):
        return self.__mul__(koeficient)


print("\n=== Karta s __mul__ ===")
eso = Karta("A", "♠")
kral = Karta("K", "♥")
desitka = Karta("10", "♣")

print(f"{eso} × 1 = {eso * 1} bodů")
print(f"{kral} × 1 = {kral * 1} bodů")
print(f"{desitka} × 2 = {desitka * 2} bodů (dvojnásobná sázka)")
print(f"3 × {eso} = {3 * eso} bodů (rmul)")

# Blackjack ruka
ruka = [Karta("A","♠"), Karta("K","♥"), Karta("3","♦")]
skore = sum(k * 1 for k in ruka)
print(f"\nRuka: {[str(k) for k in ruka]}")
print(f"Blackjack skóre: {skore}")
