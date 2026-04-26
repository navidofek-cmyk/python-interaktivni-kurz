"""
LEKCE 35: Rekurze
==================
Funkce, která volá sama sebe.

Každá rekurzivní funkce musí mít:
  1. BASE CASE  – podmínka kdy PŘESTANE volat sebe (jinak → StackOverflow)
  2. RECURSIVE CASE – zmenší problém a zavolá sebe

Analogie: Matryoshka – otevřeš panenku, uvnitř je menší, otevřeš ji,
          uvnitř je ještě menší... až přijdeš na nejmenší (base case).
"""

import sys
sys.setrecursionlimit(10_000)

# ── Faktoriál ────────────────────────────────────────────────

def faktorial_iterativni(n):
    vysledek = 1
    for i in range(2, n + 1):
        vysledek *= i
    return vysledek

def faktorial(n):
    if n <= 1:          # BASE CASE
        return 1
    return n * faktorial(n - 1)   # RECURSIVE CASE

print("=== Faktoriál ===")
for i in range(8):
    print(f"  {i}! = {faktorial(i)}")

# Vizualizace zásobníku volání
print("\nZásobník volání faktorial(4):")
print("  faktorial(4)")
print("  → 4 * faktorial(3)")
print("       → 3 * faktorial(2)")
print("            → 2 * faktorial(1)")
print("                 → 1          ← BASE CASE")
print("            ← 2 * 1 = 2")
print("       ← 3 * 2 = 6")
print("  ← 4 * 6 = 24")


# ── Fibonacci ────────────────────────────────────────────────

from functools import lru_cache

def fib_pomaly(n):
    """Exponenciální složitost – katastrofa pro n > 35."""
    if n < 2:
        return n
    return fib_pomaly(n-1) + fib_pomaly(n-2)

@lru_cache(maxsize=None)
def fib(n):
    """S cache: lineární složitost O(n)."""
    if n < 2:
        return n
    return fib(n-1) + fib(n-2)

print("\n=== Fibonacci ===")
print("Prvních 15:", [fib(i) for i in range(15)])
print(f"fib(50) = {fib(50)}")

# Zobraz jako sloupcový graf
print("\nFibonacciho spirála (prvních 12):")
maxval = fib(11)
for i in range(12):
    sloupec = int(fib(i) / maxval * 30)
    print(f"  fib({i:2d}) = {fib(i):4d} {'█' * sloupec}")


# ── Binární vyhledávání (rekurzivně) ─────────────────────────

def binarni_hledani(seznam, cil, levo=0, pravo=None, hloubka=0):
    if pravo is None:
        pravo = len(seznam) - 1

    odsazeni = "  " * hloubka
    print(f"{odsazeni}[{levo}..{pravo}] hledám {cil} v {seznam[levo:pravo+1]}")

    if levo > pravo:
        return -1

    stred = (levo + pravo) // 2
    if seznam[stred] == cil:
        print(f"{odsazeni}Nalezeno na indexu {stred}!")
        return stred
    elif seznam[stred] < cil:
        return binarni_hledani(seznam, cil, stred + 1, pravo, hloubka + 1)
    else:
        return binarni_hledani(seznam, cil, levo, stred - 1, hloubka + 1)

print("\n=== Binární vyhledávání ===")
data = list(range(0, 32, 2))
print(f"Data: {data}")
binarni_hledani(data, 18)


# ── Hanojské věže ────────────────────────────────────────────

def hanoi(n, zdroj, cil, pomocny, tahy=None):
    if tahy is None:
        tahy = []
    if n == 0:
        return tahy
    hanoi(n-1, zdroj, pomocny, cil, tahy)
    tahy.append((zdroj, cil))
    hanoi(n-1, pomocny, cil, zdroj, tahy)
    return tahy

print("\n=== Hanojské věže ===")
for disky in range(1, 5):
    tahy = hanoi(disky, "A", "C", "B")
    print(f"  {disky} disk(y): {len(tahy)} tahů  (2^{disky}-1 = {2**disky-1})")

print("\nPostup pro 3 disky:")
for i, (z, c) in enumerate(hanoi(3, "A", "C", "B"), 1):
    print(f"  Tah {i:2d}: {z} → {c}")


# ── Průchod stromem ──────────────────────────────────────────

class Uzel:
    def __init__(self, hodnota, levy=None, pravy=None):
        self.hodnota = hodnota
        self.levy    = levy
        self.pravy   = pravy

def inorder(uzel):
    """Levý → Kořen → Pravý (dá setříděný výstup pro BST)."""
    if uzel is None:
        return []
    return inorder(uzel.levy) + [uzel.hodnota] + inorder(uzel.pravy)

def tiskni_strom(uzel, prefix="", je_levy=True):
    if uzel is None:
        return
    print(prefix + ("├── " if je_levy else "└── ") + str(uzel.hodnota))
    if uzel.levy or uzel.pravy:
        tiskni_strom(uzel.levy,  prefix + ("│   " if je_levy else "    "), True)
        tiskni_strom(uzel.pravy, prefix + ("│   " if je_levy else "    "), False)

strom = Uzel(5,
    levy  = Uzel(3, Uzel(1), Uzel(4)),
    pravy = Uzel(8, Uzel(7), Uzel(9))
)

print("\n=== Binární vyhledávací strom ===")
tiskni_strom(strom, "", False)
print(f"\nInorder (setříděně): {inorder(strom)}")


# ── Flatten – zploštění vnořeného seznamu ────────────────────

def flatten(lst):
    vysledek = []
    for item in lst:
        if isinstance(item, list):
            vysledek.extend(flatten(item))   # rekurze pro podseznam
        else:
            vysledek.append(item)
    return vysledek

print("\n=== Flatten ===")
vnoreny = [1, [2, 3, [4, 5]], [6, [7, [8, 9]]], 10]
print(f"Vstup:  {vnoreny}")
print(f"Výstup: {flatten(vnoreny)}")

# TVOJE ÚLOHA:
# 1. Napiš rekurzivní funkci mocnina(zaklad, exp) bez operátoru **.
# 2. Napiš rekurzivní funkci palindrom(s) → True/False bez [::-1].
# 3. Napiš rekurzivní součet číslic: suma_cislic(1234) → 10.
# 4. Kolik tahů potřebuje Hanoi pro 10 disků? Pro 64? (legendární mniši)
