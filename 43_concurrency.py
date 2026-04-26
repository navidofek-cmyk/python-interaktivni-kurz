"""
LEKCE 43: Concurrency – threading vs multiprocessing vs async
==============================================================
Tři způsoby jak dělat víc věcí "najednou" v Pythonu.
Každý vhodný pro jiný typ práce.

THREADING    – vlákna, sdílená paměť, GIL blokuje CPU-bound
MULTIPROCESSING – procesy, vlastní paměť, obchází GIL, CPU-bound
ASYNC        – korutiny, jeden thread, nejlepší pro I/O-bound

Pravidlo:
  I/O-bound (síť, soubory, DB) → async nebo threading
  CPU-bound (výpočty, komprese) → multiprocessing
"""

import threading
import multiprocessing
import asyncio
import time
import queue
import os
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed

# ══════════════════════════════════════════════════════════════
# ČÁST 1: THREADING
# ══════════════════════════════════════════════════════════════

print("=== THREADING ===\n")

# ── Základní thread ──────────────────────────────────────────

def stahni_simulace(url: str, vysledky: list, zamek: threading.Lock):
    """Simuluje stahování (I/O-bound)."""
    time.sleep(0.2)   # simulace latence sítě
    with zamek:        # Lock zabraňuje race condition
        vysledky.append(f"data z {url}")

urls = [f"https://api.example.com/item/{i}" for i in range(8)]
vysledky: list[str] = []
zamek = threading.Lock()

t0 = time.perf_counter()
thready = [threading.Thread(target=stahni_simulace, args=(u, vysledky, zamek))
           for u in urls]
for t in thready: t.start()
for t in thready: t.join()
print(f"Threading: {len(vysledky)} požadavků za {time.perf_counter()-t0:.2f}s")
print(f"  (sekvenčně by trvalo {0.2*len(urls):.1f}s)")

# ── Race condition demo ───────────────────────────────────────

print("\n--- Race condition ---")

class BezpecnyPocitadlo:
    def __init__(self):
        self._hodnota = 0
        self._zamek   = threading.Lock()

    def inkrementuj(self, n=1000):
        for _ in range(n):
            with self._zamek:
                self._hodnota += 1

    @property
    def hodnota(self): return self._hodnota

poc = BezpecnyPocitadlo()
thready = [threading.Thread(target=poc.inkrementuj) for _ in range(5)]
for t in thready: t.start()
for t in thready: t.join()
print(f"  Bezpečné počítadlo: {poc.hodnota} (očekáváno 5000)")

# ── Producer-Consumer s Queue ────────────────────────────────

print("\n--- Producer-Consumer ---")

def producent(q: queue.Queue, n: int):
    for i in range(n):
        q.put(f"úkol-{i}")
        time.sleep(0.01)
    q.put(None)   # sentinel – konec práce

def konzument(q: queue.Queue, id_: int, vysledky: list, zamek: threading.Lock):
    while True:
        ukol = q.get()
        if ukol is None:
            q.put(None)   # předej dál dalšímu konzumentovi
            break
        time.sleep(0.02)   # zpracování
        with zamek:
            vysledky.append(f"konzument-{id_} zpracoval {ukol}")
        q.task_done()

fronta:    queue.Queue = queue.Queue(maxsize=5)
zpracovano: list[str] = []
zamek2 = threading.Lock()

t0 = time.perf_counter()
prod   = threading.Thread(target=producent, args=(fronta, 10))
konzy  = [threading.Thread(target=konzument, args=(fronta, i, zpracovano, zamek2))
          for i in range(3)]

prod.start()
for k in konzy: k.start()
prod.join()
for k in konzy: k.join()

print(f"  Zpracováno {len(zpracovano)} úkolů za {time.perf_counter()-t0:.2f}s")

# ── Thread-local storage ─────────────────────────────────────

print("\n--- Thread-local ---")
lokalni = threading.local()

def nastav_a_tiskni(jmeno: str):
    lokalni.jmeno = jmeno
    time.sleep(0.05)
    print(f"  Thread {jmeno}: lokalni.jmeno = {lokalni.jmeno}")

thready = [threading.Thread(target=nastav_a_tiskni, args=(n,))
           for n in ["Míša", "Tomáš", "Bára"]]
for t in thready: t.start()
for t in thready: t.join()


# ══════════════════════════════════════════════════════════════
# ČÁST 2: MULTIPROCESSING
# ══════════════════════════════════════════════════════════════

print("\n=== MULTIPROCESSING ===\n")

def cpu_narocna_prace(n: int) -> int:
    """CPU-bound: počítá sumu čtverců."""
    return sum(i * i for i in range(n))

N = 2_000_000

# Sekvenční
t0 = time.perf_counter()
vysledky_seq = [cpu_narocna_prace(N) for _ in range(4)]
cas_seq = time.perf_counter() - t0

# Paralelní (ProcessPoolExecutor)
t0 = time.perf_counter()
with ProcessPoolExecutor(max_workers=4) as ex:
    vysledky_par = list(ex.map(cpu_narocna_prace, [N]*4))
cas_par = time.perf_counter() - t0

print(f"CPU-bound výpočet (4× N={N:_}):")
print(f"  Sekvenční:  {cas_seq:.2f}s")
print(f"  Paralelní:  {cas_par:.2f}s  (speedup: {cas_seq/cas_par:.1f}×)")
print(f"  Výsledky shodné: {vysledky_seq == vysledky_par}")

# ── as_completed – výsledky jak přicházejí ───────────────────

print("\n--- as_completed ---")

def pomala_uloha(id_: int) -> dict:
    import random
    time.sleep(random.uniform(0.1, 0.5))
    return {"id": id_, "vysledek": id_ ** 2}

t0 = time.perf_counter()
with ProcessPoolExecutor(max_workers=4) as ex:
    futures = {ex.submit(pomala_uloha, i): i for i in range(6)}
    for fut in as_completed(futures):
        r = fut.result()
        print(f"  [{time.perf_counter()-t0:.2f}s] hotovo id={r['id']}: {r['vysledek']}")


# ══════════════════════════════════════════════════════════════
# ČÁST 3: ASYNC (srovnání)
# ══════════════════════════════════════════════════════════════

print("\n=== ASYNC – srovnání s threadingem pro I/O ===\n")

async def async_stahni(session_id: int) -> str:
    await asyncio.sleep(0.2)   # simulace I/O
    return f"data-{session_id}"

async def async_main():
    t0 = time.perf_counter()
    vysledky = await asyncio.gather(*[async_stahni(i) for i in range(8)])
    print(f"Async: {len(vysledky)} požadavků za {time.perf_counter()-t0:.2f}s")
    print(f"  (stejný výsledek jako threading, ale bez overhead vláken)")

asyncio.run(async_main())


# ══════════════════════════════════════════════════════════════
# ČÁST 4: PŘEHLEDOVÁ TABULKA
# ══════════════════════════════════════════════════════════════

print("""
=== Kdy co použít ===

┌─────────────────────┬────────────┬────────────┬────────────┐
│                     │ threading  │ multiproc. │   async    │
├─────────────────────┼────────────┼────────────┼────────────┤
│ I/O-bound (síť/DB)  │    ✓       │    ~       │    ✓✓      │
│ CPU-bound (výpočty) │    ✗ (GIL) │    ✓✓      │    ✗       │
│ Sdílená paměť       │    ✓       │    ✗       │    ✓       │
│ Overhead            │   střední  │   vysoký   │   nízký    │
│ Složitost kódu      │   střední  │   střední  │   střední  │
│ Race conditions     │    riziko  │    méně    │   bezpečné │
└─────────────────────┴────────────┴────────────┴────────────┘

GIL (Global Interpreter Lock) = CPython pouští vždy jen 1 thread
najednou pro Python kód → threading nepomáhá u CPU-bound.
""")

# TVOJE ÚLOHA:
# 1. Porovnej ThreadPoolExecutor vs ProcessPoolExecutor na faktoriálu(50_000).
# 2. Napiš thread-safe cache (dict + Lock) jako dekorátor @thread_safe_cache.
# 3. Použij asyncio.Queue pro producer-consumer bez threadů.
