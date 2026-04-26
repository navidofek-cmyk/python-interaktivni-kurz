"""
LEKCE 36: Třídící algoritmy
=============================
Jak dostat čísla do pořadí? Existuje překvapivě mnoho způsobů –
každý s jiným přístupem a výkonem.

Složitost: kolik operací algoritmus potřebuje pro N prvků?
  O(N²)       – pomalé (bubble, selection, insertion)
  O(N log N)  – rychlé (merge, quick, heap)
  O(N)        – speciální případy (counting, radix)
"""

import random
import time

# ── Pomocná funkce pro vizualizaci ───────────────────────────

def vizualizuj(seznam, oznacene=(), titulek=""):
    radek = ""
    for i, x in enumerate(seznam):
        if i in oznacene:
            radek += f"\033[33m{x:3d}\033[0m"   # žlutá = porovnávané
        else:
            radek += f"{x:3d}"
    print(f"  {titulek:<20} {radek}")

def animuj(algoritmus, data, nazev):
    """Spustí algoritmus, počítá operace, vrátí setříděná data."""
    seznam = data.copy()
    kroky = [0]

    def swap(lst, i, j):
        kroky[0] += 1
        lst[i], lst[j] = lst[j], lst[i]

    def compare(a, b):
        kroky[0] += 1
        return a > b

    algoritmus(seznam, swap, compare)
    return seznam, kroky[0]


# ══════════════════════════════════════════════════════════════
# BUBBLE SORT – O(N²)
# ══════════════════════════════════════════════════════════════

def bubble_sort_viz(data):
    """Vizuální verze – ukazuje každé porovnání."""
    s = data.copy()
    n = len(s)
    print(f"\n{'─'*50}")
    print("BUBBLE SORT (bublinkové třídění)")
    print("Větší čísla 'bublají' doprava v každém průchodu.")
    print(f"{'─'*50}")
    vizualizuj(s, titulek="Start:")
    for pruchod in range(n - 1):
        for j in range(n - 1 - pruchod):
            if s[j] > s[j+1]:
                s[j], s[j+1] = s[j+1], s[j]
        vizualizuj(s, oznacene=(n-1-pruchod,), titulek=f"Po průchodu {pruchod+1}:")
    return s

bubble_sort_viz([5, 3, 8, 1, 9, 2, 7, 4, 6])


# ══════════════════════════════════════════════════════════════
# SELECTION SORT – O(N²)
# ══════════════════════════════════════════════════════════════

def selection_sort_viz(data):
    s = data.copy()
    n = len(s)
    print(f"\n{'─'*50}")
    print("SELECTION SORT (výběrové třídění)")
    print("Najde minimum, přesune na začátek, opakuje.")
    print(f"{'─'*50}")
    for i in range(n):
        min_idx = i
        for j in range(i+1, n):
            if s[j] < s[min_idx]:
                min_idx = j
        s[i], s[min_idx] = s[min_idx], s[i]
        vizualizuj(s, oznacene=(i,), titulek=f"Krok {i+1} – min→[{i}]:")
    return s

selection_sort_viz([5, 3, 8, 1, 9, 2, 7, 4, 6])


# ══════════════════════════════════════════════════════════════
# INSERTION SORT – O(N²) ale rychlý pro malá/skoro setříděná data
# ══════════════════════════════════════════════════════════════

def insertion_sort_viz(data):
    s = data.copy()
    print(f"\n{'─'*50}")
    print("INSERTION SORT (vkládací třídění)")
    print("Jako třídění karet v ruce: vezmeš kartu, vsunuješ na místo.")
    print(f"{'─'*50}")
    for i in range(1, len(s)):
        klic = s[i]
        j = i - 1
        while j >= 0 and s[j] > klic:
            s[j+1] = s[j]
            j -= 1
        s[j+1] = klic
        vizualizuj(s, oznacene=(j+1,), titulek=f"Vložen {klic}:")
    return s

insertion_sort_viz([5, 3, 8, 1, 9, 2, 7, 4, 6])


# ══════════════════════════════════════════════════════════════
# MERGE SORT – O(N log N)
# ══════════════════════════════════════════════════════════════

def merge_sort(s):
    """Rozděl a panuj: rozsekej na půlky, setřiď, spoj."""
    if len(s) <= 1:
        return s
    stred = len(s) // 2
    levy  = merge_sort(s[:stred])
    pravy = merge_sort(s[stred:])
    return merge(levy, pravy)

def merge(levy, pravy):
    vysledek = []
    i = j = 0
    while i < len(levy) and j < len(pravy):
        if levy[i] <= pravy[j]:
            vysledek.append(levy[i]); i += 1
        else:
            vysledek.append(pravy[j]); j += 1
    return vysledek + levy[i:] + pravy[j:]

print(f"\n{'─'*50}")
print("MERGE SORT (třídění slučováním)")
print("Rozdělí seznam na půl, každou půl setřídí rekurzivně, pak spojí.")
print(f"{'─'*50}")
data = [5, 3, 8, 1, 9, 2, 7, 4, 6]
print(f"  Vstup:  {data}")
print(f"  Výstup: {merge_sort(data)}")


# ══════════════════════════════════════════════════════════════
# QUICKSORT – O(N log N) průměrně, O(N²) nejhorší případ
# ══════════════════════════════════════════════════════════════

def quicksort(s):
    """Pivot: vše menší vlevo, vše větší vpravo, rekurze."""
    if len(s) <= 1:
        return s
    pivot = s[len(s) // 2]
    levy  = [x for x in s if x < pivot]
    stred = [x for x in s if x == pivot]
    pravy = [x for x in s if x > pivot]
    return quicksort(levy) + stred + quicksort(pravy)

print(f"\n{'─'*50}")
print("QUICKSORT (rychlé třídění)")
print("Zvolí pivot, rozdělí na menší/větší, rekurzivně setřídí části.")
print(f"{'─'*50}")
data = [5, 3, 8, 1, 9, 2, 7, 4, 6]
print(f"  Vstup:  {data}")
print(f"  Výstup: {quicksort(data)}")


# ══════════════════════════════════════════════════════════════
# SROVNÁNÍ RYCHLOSTI
# ══════════════════════════════════════════════════════════════

def bubble(s):
    s = s.copy()
    for i in range(len(s)):
        for j in range(len(s)-1-i):
            if s[j] > s[j+1]: s[j], s[j+1] = s[j+1], s[j]
    return s

print(f"\n{'─'*50}")
print("SROVNÁNÍ RYCHLOSTI")
print(f"{'─'*50}")
print(f"{'Algoritmus':<20} {'N=500':>8} {'N=2000':>8} {'N=8000':>8}")
print("─" * 50)

algoritmy = [
    ("Bubble sort",    bubble),
    ("Insertion sort", lambda s: sorted(s)),          # vestavěný pro referenci
    ("Merge sort",     merge_sort),
    ("Quicksort",      quicksort),
    ("Python sorted",  sorted),
]

for nazev, fn in algoritmy:
    casy = []
    for n in [500, 2000, 8000]:
        data = random.sample(range(n*10), n)
        t0 = time.perf_counter()
        fn(data)
        casy.append((time.perf_counter() - t0) * 1000)
    print(f"  {nazev:<18} {casy[0]:>6.1f}ms {casy[1]:>6.1f}ms {casy[2]:>6.1f}ms")

print(f"\nPoznámka: Python sorted() je Timsort – hybridní merge+insertion.")

# TVOJE ÚLOHA:
# 1. Napiš counting_sort(seznam) pro čísla 0–100 – O(N) složitost.
# 2. Přidej do bubble_sort_viz počítadlo swap operací.
# 3. Otestuj quicksort na již setříděném seznamu – proč je pomalý?
#    Jak pomůže náhodný výběr pivotu?
