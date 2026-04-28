"""Řešení – Lekce 27: Generátory a iterátory"""

import itertools


# 1. Generátor prvočísel – nekonečný, yield-uje prvočíslo za prvočíslem
# Používáme trial division: číslo n je prvočíslo, pokud ho nevydělí žádné
# dosud nalezené prvočíslo ≤ √n (optimalizace oproti naivní verzi)

def prvocisla():
    """Nekonečný generátor prvočísel."""
    nalezena = []
    kandidat = 2
    while True:
        # Je kandidát prvočíslo?
        je_prvocislo = all(
            kandidat % p != 0
            for p in nalezena
            if p * p <= kandidat
        )
        if je_prvocislo:
            nalezena.append(kandidat)
            yield kandidat
        kandidat += 1


print("=== Generátor prvočísel ===")
gen = prvocisla()
prvnich_20 = [next(gen) for _ in range(20)]
print(f"Prvních 20 prvočísel: {prvnich_20}")

# První prvočíslo větší než 1000
gen2 = prvocisla()
print(f"První prvočíslo > 1000: {next(p for p in gen2 if p > 1000)}")


# 2. Generátor pohyb_hada – spirálový pohyb (snaking/boustrophedon)
# Pohybuje se řádek po řádku, lichý řádek zprava doleva = had v hadím vzoru
# Používá se např. pro rastrové skenování nebo tisk z matrix tiskáren

def pohyb_hada(sirka: int, vyska: int):
    """
    Generuje souřadnice (x, y) pro pohyb hada po mřížce.
    Lichý řádek: zleva doprava, sudý řádek: zprava doleva.
    """
    for y in range(vyska):
        if y % 2 == 0:  # sudý řádek – zleva doprava
            for x in range(sirka):
                yield (x, y)
        else:           # lichý řádek – zprava doleva
            for x in range(sirka - 1, -1, -1):
                yield (x, y)


print("\n=== Pohyb hada (3×3 mřížka) ===")
trasa = list(pohyb_hada(4, 3))
print(f"Souřadnice: {trasa}")

# Vizualizace
print("Vizualizace (číslo = pořadí navštívení):")
grid = [[" . "] * 4 for _ in range(3)]
for i, (x, y) in enumerate(trasa):
    grid[y][x] = f"{i:2d} "
for radek in grid:
    print("  " + "".join(radek))


# 3. itertools.product – všechny kombinace hodů 2 kostkami
# product je kartézský součin: každá hodnota první kostky s každou druhé

print("\n=== Hody 2 kostkami (itertools.product) ===")
kostka = range(1, 7)  # 1–6

vsechny_hody = list(itertools.product(kostka, kostka))
print(f"Celkový počet kombinací: {len(vsechny_hody)}")

# Distribuce součtů
from collections import Counter
soucty = Counter(a + b for a, b in vsechny_hody)

print("\nDistribuce součtů:")
for soucet in sorted(soucty):
    pocet = soucty[soucet]
    bar = "█" * pocet
    pravdepodobnost = pocet / len(vsechny_hody) * 100
    print(f"  {soucet:2d}: {bar:<12} {pocet}× ({pravdepodobnost:.1f}%)")

print(f"\nNejpravděpodobnější součet: {soucty.most_common(1)[0][0]}")
print(f"(7 má 6/36 = 16.7% šanci – proto je 7 tak důležitá v kostkových hrách)")
