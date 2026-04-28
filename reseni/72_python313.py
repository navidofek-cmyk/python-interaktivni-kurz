"""Řešení – Lekce 72: Python 3.13 – novinky"""

import sys
import time
import threading
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from dataclasses import dataclass, replace

print(f"Python verze: {sys.version}\n")

# 1. Benchmark faktoriálu – porovnání rychlosti verzí
print("=== 1. Benchmark faktoriálu ===\n")

import math

def faktorial_smycka(n: int) -> int:
    """Faktoriál přes smyčku."""
    vysledek = 1
    for i in range(2, n + 1):
        vysledek *= i
    return vysledek

def faktorial_math(n: int) -> int:
    """Faktoriál přes math.factorial (C implementace)."""
    return math.factorial(n)

def faktorial_rekurze(n: int) -> int:
    """Rekurzivní faktoriál."""
    if n <= 1:
        return 1
    return n * faktorial_rekurze(n - 1)

sys.setrecursionlimit(5000)

N = 1000
OPAKOVÁNÍ = 500

t0 = time.perf_counter()
for _ in range(OPAKOVÁNÍ):
    faktorial_smycka(N)
t_smycka = time.perf_counter() - t0

t0 = time.perf_counter()
for _ in range(OPAKOVÁNÍ):
    faktorial_math(N)
t_math = time.perf_counter() - t0

t0 = time.perf_counter()
for _ in range(OPAKOVÁNÍ):
    faktorial_rekurze(N)
t_rekurze = time.perf_counter() - t0

print(f"Faktoriál({N}), {OPAKOVÁNÍ}× opakování:")
print(f"  Smyčka:    {t_smycka*1000:.1f}ms")
print(f"  math:      {t_math*1000:.1f}ms  ({t_smycka/t_math:.1f}× rychlejší než smyčka)")
print(f"  Rekurze:   {t_rekurze*1000:.1f}ms")
print(f"\n  Python {sys.version_info.major}.{sys.version_info.minor} na {sys.platform}")
print(f"  (Na Python 3.13+ s --jit je CPU-bound kód ~5% rychlejší)")

# 2. Threading vs multiprocessing – porovnání pro CPU-bound operace
print("\n=== 2. Threading vs Multiprocessing ===\n")

def cpu_bound(n: int) -> int:
    """CPU-bound operace – součet čtverců."""
    return sum(i * i for i in range(n))

N_CPU = 500_000
POCET = 4

# Sekvenční
t0 = time.perf_counter()
for _ in range(POCET):
    cpu_bound(N_CPU)
t_seq = time.perf_counter() - t0

# Threading (GIL blokuje CPU-bound)
t0 = time.perf_counter()
with ThreadPoolExecutor(max_workers=POCET) as ex:
    futures = [ex.submit(cpu_bound, N_CPU) for _ in range(POCET)]
    [f.result() for f in futures]
t_thread = time.perf_counter() - t0

# Multiprocessing (obchází GIL)
t0 = time.perf_counter()
with ProcessPoolExecutor(max_workers=min(POCET, 4)) as ex:
    futures = [ex.submit(cpu_bound, N_CPU) for _ in range(POCET)]
    [f.result() for f in futures]
t_proc = time.perf_counter() - t0

print(f"CPU-bound N={N_CPU:_}, {POCET}× paralelně:")
print(f"  Sekvenční:        {t_seq:.3f}s")
print(f"  ThreadPool:       {t_thread:.3f}s  "
      f"({'lepší' if t_thread < t_seq * 0.9 else 'GIL blokuje – nepomáhá'})")
print(f"  ProcessPool:      {t_proc:.3f}s  "
      f"({'rychlejší' if t_proc < t_seq * 0.9 else 'overhead přesahuje zisk'})")

# Zjisti GIL status
gil_aktivni = getattr(sys, "_is_gil_enabled", lambda: True)()
print(f"\n  GIL aktivní: {gil_aktivni}")
if not gil_aktivni:
    print("  Běžíš na free-threaded Python 3.13t – threading pomáhá!")
else:
    print("  Pro CPU-bound paralelismus: multiprocessing nebo Python 3.13t")

# 3. CPU-bound smyčka s měřením potenciálního JIT speedup
print("\n=== 3. JIT benchmark – opakovaná smyčka ===\n")

def intenzivni_smycka(n: int) -> float:
    """Intenzivní numerická smyčka – kandidát pro JIT optimalizaci."""
    souct = 0.0
    for i in range(n):
        souct += (i % 7) * 0.001 + (i % 13) * 0.002
    return souct

# Zahřívání (JIT by zde začal kompilovat)
intenzivni_smycka(10_000)

t0 = time.perf_counter()
vysledek = intenzivni_smycka(1_000_000)
t1 = time.perf_counter()

print(f"Intenzivní smyčka 1M iterací: {(t1-t0)*1000:.1f}ms")
print(f"Výsledek: {vysledek:.2f}")
print()
print("Jak spustit s JIT (Python 3.13+):")
print("  python3.13 --jit 72_python313.py")
print("  (zatím ~5% speedup, v budoucnu 2-5×)")
print()
print("Jak spustit bez GIL (Python 3.13t):")
print("  python3.13t 72_python313.py")
print("  (free-threaded build – threading funguje pro CPU-bound)")

# copy.replace() demo
print("\n=== Bonus: copy.replace() / dataclasses.replace() ===\n")

@dataclass
class Konfigurace:
    host: str
    port: int
    debug: bool = False
    max_spojeni: int = 100

    def __replace__(self, **zmeny):
        return Konfigurace(
            host=zmeny.get("host", self.host),
            port=zmeny.get("port", self.port),
            debug=zmeny.get("debug", self.debug),
            max_spojeni=zmeny.get("max_spojeni", self.max_spojeni),
        )

prod_cfg  = Konfigurace(host="db.example.com", port=5432)
dev_cfg   = replace(prod_cfg, host="localhost", debug=True)
test_cfg  = replace(prod_cfg, host="localhost", port=5433, max_spojeni=10)

print(f"Produkce: {prod_cfg}")
print(f"Vývoj:    {dev_cfg}")
print(f"Test:     {test_cfg}")
