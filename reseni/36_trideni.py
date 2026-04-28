"""Řešení – Lekce 36: Třídící algoritmy"""

import random
import time


# 1. Counting sort – O(N) složitost pro čísla 0–100
# Princip: spočítáme kolikrát se každé číslo vyskytuje (counting array),
# pak z toho sestavíme setříděné pořadí.
# Funguje jen pro celá čísla v omezeném rozsahu – proto O(N) místo O(N log N).

def counting_sort(seznam: list[int], max_val: int = 100) -> list[int]:
    """Counting sort pro čísla 0 až max_val. Složitost O(N + max_val)."""
    if not seznam:
        return []

    pocty = [0] * (max_val + 1)
    for cislo in seznam:
        if 0 <= cislo <= max_val:
            pocty[cislo] += 1

    vysledek = []
    for hodnota, pocet in enumerate(pocty):
        vysledek.extend([hodnota] * pocet)

    return vysledek


print("=== 1. Counting sort ===")
data = [random.randint(0, 100) for _ in range(15)]
setrideno = counting_sort(data)
print(f"  Vstup:  {data}")
print(f"  Výstup: {setrideno}")
assert setrideno == sorted(data), "Counting sort selhalo!"
print("  Ověřeno: výsledek se shoduje se sorted() ✓")

# Rychlostní test
velka_data = [random.randint(0, 100) for _ in range(100_000)]
t0 = time.perf_counter()
counting_sort(velka_data)
cas = (time.perf_counter() - t0) * 1000
print(f"\n  100 000 čísel (0–100): {cas:.1f} ms  (counting sort)")


# 2. Bubble sort s počítadlem swap operací
# Počítadlo ukazuje, proč je bubble sort pomalý: O(N²) swapů v nejhorším případě

def bubble_sort_s_pocitadlem(data: list) -> tuple[list, int, int]:
    """
    Vrátí (setřízená data, počet porovnání, počet swapů).
    Čím více swapů, tím více je data neuspořádaná.
    """
    s = data.copy()
    n = len(s)
    pocet_porovnani = 0
    pocet_swapu = 0

    for pruchod in range(n - 1):
        vymeneno = False
        for j in range(n - 1 - pruchod):
            pocet_porovnani += 1
            if s[j] > s[j + 1]:
                s[j], s[j + 1] = s[j + 1], s[j]
                pocet_swapu += 1
                vymeneno = True
        if not vymeneno:
            break  # optimalizace: pokud žádný swap → je seřazeno

    return s, pocet_porovnani, pocet_swapu


print("\n=== 2. Bubble sort s počítadlem swapů ===")
prikl = [
    ("náhodný",      random.sample(range(10), 10)),
    ("skoro setříd.", [1, 2, 3, 4, 6, 5, 7, 8, 9, 10]),
    ("setříděný",     list(range(1, 11))),
    ("obrácený",      list(range(10, 0, -1))),
]
print(f"  {'Typ':<18} {'Vstup':<35} Porovn.  Swapy")
print("  " + "-" * 70)
for typ, data in prikl:
    _, porovn, swapy = bubble_sort_s_pocitadlem(data)
    print(f"  {typ:<18} {str(data):<35} {porovn:>6}   {swapy:>5}")


# 3. Quicksort na setříděném vstupu – problém + náhodný pivot jako řešení
# Standardní quicksort s pivotem uprostřed je O(N²) pro setřízené pole,
# protože vždy vybírá nejmenší/největší prvek jako pivot → nevyvážené dělení.
# Náhodný pivot tento worst-case průměrně eliminuje.

def quicksort_stredovy(s: list) -> list:
    """Pivot = prostřední prvek (špatný pro setříděná data)."""
    if len(s) <= 1:
        return s
    pivot = s[len(s) // 2]
    levy = [x for x in s if x < pivot]
    stred = [x for x in s if x == pivot]
    pravy = [x for x in s if x > pivot]
    return quicksort_stredovy(levy) + stred + quicksort_stredovy(pravy)


def quicksort_nahodny(s: list) -> list:
    """Pivot = náhodný prvek – eliminuje worst-case pro setříděná data."""
    if len(s) <= 1:
        return s
    pivot = random.choice(s)  # náhodný pivot
    levy = [x for x in s if x < pivot]
    stred = [x for x in s if x == pivot]
    pravy = [x for x in s if x > pivot]
    return quicksort_nahodny(levy) + stred + quicksort_nahodny(pravy)


print("\n=== 3. Quicksort: setříděný vstup ===")
n = 1000

data_nahodna = random.sample(range(n), n)
data_setridena = list(range(n))

print(f"  {'Algoritmus':<25} {'náhodná data':>12}  {'setříděná data':>14}")
print("  " + "-" * 55)

for nazev, fn in [("quicksort(střed. pivot)", quicksort_stredovy),
                   ("quicksort(náhodný pivot)", quicksort_nahodny)]:
    t0 = time.perf_counter()
    fn(data_nahodna.copy())
    t_nahodna = (time.perf_counter() - t0) * 1000

    t0 = time.perf_counter()
    fn(data_setridena.copy())
    t_setridena = (time.perf_counter() - t0) * 1000

    print(f"  {nazev:<25} {t_nahodna:>10.2f}ms  {t_setridena:>12.2f}ms")

print()
print("  Vysvětlení: středový pivot vybírá prvek uprostřed indexu.")
print("  Pro setříděná data → vždy minimální nebo maximální → O(N²).")
print("  Náhodný pivot rozbíjí vzor → průměrně O(N log N) i pro setříděná data.")
