"""
LEKCE 44: Výkon a profiling
=============================
"Předčasná optimalizace je kořen všeho zla." – Donald Knuth

Postup:
  1. Napiš správný kód
  2. Změř (profiling) – kde je bottleneck?
  3. Optimalizuj POUZE to místo
  4. Změř znovu

Nástroje:
  timeit      – přesné měření malých úseků
  cProfile    – kde program tráví čas
  dis         – Python bytecode
  sys.getsizeof / tracemalloc – paměť
  line_profiler – řádek po řádku (pip install)
"""

import timeit
import cProfile
import pstats
import io
import dis
import sys
import tracemalloc
from functools import lru_cache

# ══════════════════════════════════════════════════════════════
# ČÁST 1: timeit – přesné měření
# ══════════════════════════════════════════════════════════════

print("=== timeit ===\n")

# Spojení řetězců – 4 způsoby
N = 1000

def spoj_plus(slova):
    result = ""
    for s in slova: result += s
    return result

def spoj_join(slova):
    return "".join(slova)

def spoj_list(slova):
    parts = []
    for s in slova: parts.append(s)
    return "".join(parts)

def spoj_fstring(slova):
    return "".join(f"{s}" for s in slova)

slova = ["python"] * N

def mer(fn, label, opak=1000):
    cas = timeit.timeit(lambda: fn(slova), number=opak)
    print(f"  {label:<25} {cas*1000/opak:.3f} µs/volání  ({cas:.3f}s celkem)")

print(f"Spojení {N} slov ({opak} opakování):", opak := 200)
mer(spoj_plus,    "string + string")
mer(spoj_join,    "''.join(list)")
mer(spoj_list,    "list + join")
mer(spoj_fstring, "fstring generator")

# Různé datové struktury pro hledání
print()
import random
data_list = list(range(10_000))
data_set  = set(data_list)
data_dict = dict.fromkeys(data_list, True)
hledej    = random.randint(0, 9999)

print(f"Hledání prvku v různých strukturách (10 000 prvků):")
for fn, label in [
    (lambda: hledej in data_list, "hledej in list  O(N)"),
    (lambda: hledej in data_set,  "hledej in set   O(1)"),
    (lambda: hledej in data_dict, "hledej in dict  O(1)"),
]:
    cas = timeit.timeit(fn, number=100_000)
    print(f"  {label:<30} {cas:.3f}s")


# ══════════════════════════════════════════════════════════════
# ČÁST 2: cProfile – kde program tráví čas
# ══════════════════════════════════════════════════════════════

print("\n=== cProfile ===\n")

def fib_pomaly(n):
    if n < 2: return n
    return fib_pomaly(n-1) + fib_pomaly(n-2)

@lru_cache(maxsize=None)
def fib_rychly(n):
    if n < 2: return n
    return fib_rychly(n-1) + fib_rychly(n-2)

def profiluj(fn, *args, radku=10):
    pr = cProfile.Profile()
    pr.enable()
    vysledek = fn(*args)
    pr.disable()

    vystup = io.StringIO()
    stats  = pstats.Stats(pr, stream=vystup)
    stats.sort_stats("cumulative")
    stats.print_stats(radku)
    return vysledek, vystup.getvalue()

print("Profil fib_pomaly(28):")
vysl, report = profiluj(fib_pomaly, 28)
print(f"  Výsledek: {vysl}")
# Zobraz jen první 3 řádky statistik
for radek in report.split("\n")[4:8]:
    if radek.strip():
        print(f"  {radek}")

fib_rychly.cache_clear()
print("\nProfil fib_rychly(100):")
vysl, report = profiluj(fib_rychly, 100)
print(f"  Výsledek: {vysl}")
for radek in report.split("\n")[4:8]:
    if radek.strip():
        print(f"  {radek}")


# ══════════════════════════════════════════════════════════════
# ČÁST 3: dis – bytecode
# ══════════════════════════════════════════════════════════════

print("\n=== dis – Python bytecode ===\n")

def jednoducha(x, y):
    return x + y * 2

def slozitejsi(x, y):
    vysledek = x + y * 2
    if vysledek > 10:
        return vysledek
    return 0

print("Bytecode jednoducha(x, y):")
dis.dis(jednoducha)

print("\nBytecode list comprehension vs for loop:")

def list_comp(n):
    return [x*x for x in range(n)]

def for_loop(n):
    result = []
    for x in range(n): result.append(x*x)
    return result

print("\nlist comprehension:")
dis.dis(list_comp)
print("\nfor loop:")
dis.dis(for_loop)

t1 = timeit.timeit(lambda: list_comp(1000), number=5000)
t2 = timeit.timeit(lambda: for_loop(1000),  number=5000)
print(f"\nVýkon: list_comp={t1:.3f}s  for_loop={t2:.3f}s  "
      f"→ list_comp je {t2/t1:.1f}× rychlejší")


# ══════════════════════════════════════════════════════════════
# ČÁST 4: Paměť – tracemalloc
# ══════════════════════════════════════════════════════════════

print("\n=== tracemalloc – sledování paměti ===\n")

def pamet_list(n):
    return list(range(n))

def pamet_generator(n):
    return (x for x in range(n))   # neukládá do paměti!

def pamet_range(n):
    return range(n)                  # také líné

N = 100_000

for fn, label in [
    (pamet_list,      "list(range(N))"),
    (pamet_generator, "generator"),
    (pamet_range,     "range object"),
]:
    tracemalloc.start()
    obj = fn(N)
    snapshot = tracemalloc.take_snapshot()
    tracemalloc.stop()
    velikost = sys.getsizeof(obj)
    print(f"  {label:<25} {velikost:>10,} B  ({velikost/1024:.1f} KB)")

# ── Optimalizační techniky ───────────────────────────────────

print("\n=== Optimalizační techniky ===\n")

# 1. __slots__ vs __dict__
from dataclasses import dataclass

class BezSlots:
    def __init__(self, x, y): self.x = x; self.y = y

class SeSlots:
    __slots__ = ("x", "y")
    def __init__(self, x, y): self.x = x; self.y = y

N = 100_000
t1 = timeit.timeit(lambda: [BezSlots(i, i) for i in range(1000)], number=N//100)
t2 = timeit.timeit(lambda: [SeSlots(i, i)  for i in range(1000)], number=N//100)
print(f"  Vytvoření 1000 instancí: bez __slots__={t1:.3f}s  se __slots__={t2:.3f}s")
print(f"  Speedup: {t1/t2:.2f}×")

# 2. Local variable lookup je rychlejší než global
import math

def s_globalem(n):
    return [math.sqrt(i) for i in range(n)]

def s_lokalnim(n):
    sqrt = math.sqrt          # lokální reference = rychlejší lookup
    return [sqrt(i) for i in range(n)]

t1 = timeit.timeit(lambda: s_globalem(1000), number=5000)
t2 = timeit.timeit(lambda: s_lokalnim(1000), number=5000)
print(f"\n  math.sqrt přes global vs lokální:  {t1:.3f}s vs {t2:.3f}s  ({t1/t2:.2f}×)")

# 3. set pro membership test
velky_seznam = list(range(100_000))
velka_mnozina = set(velky_seznam)

t1 = timeit.timeit(lambda: 99_999 in velky_seznam,  number=10_000)
t2 = timeit.timeit(lambda: 99_999 in velka_mnozina, number=10_000)
print(f"\n  99_999 in list:  {t1:.4f}s")
print(f"  99_999 in set:   {t2:.4f}s  ({t1/t2:.0f}× rychlejší)")

print("""
=== Zlatá pravidla výkonu ===

1. Měř první, optimalizuj druhé.
2. Algoritmus > implementace (O(N log N) > O(N²) vždy).
3. Vestavěné funkce (sorted, sum, map) jsou v C → rychlé.
4. list comprehension > for + append.
5. set/dict lookup = O(1), list lookup = O(N).
6. __slots__ šetří paměť u mnoha instancí.
7. Lokální proměnné jsou rychlejší než globální/atributy.
8. lru_cache zachrání rekurzivní výpočty.
9. numpy/pandas pro numeriku (C engine).
""")

# TVOJE ÚLOHA:
# 1. Porovnej rychlost dict.get() vs try/except pro chybějící klíč.
# 2. Napiš dekorátor @timeit_dec(n) který změří průměrný čas n volání.
# 3. Profiluj lekci 38 (DP) a najdi nejpomalejší funkci.
