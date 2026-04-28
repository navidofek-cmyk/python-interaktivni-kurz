"""Reseni – Lekce 43: Concurrency"""

import threading
import asyncio
import time
import math
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from typing import Callable, Any


# 1. Porovnej ThreadPoolExecutor vs ProcessPoolExecutor na faktorial(50_000)

print("=== Ukol 1: ThreadPool vs ProcessPool – faktorial(50_000) ===\n")


def faktorial_iterace(n: int) -> int:
    """CPU-bound: iterativni faktorial (bez rekurze kvuli limitu)."""
    vysledek = 1
    for i in range(2, n + 1):
        vysledek *= i
    return vysledek


N = 20_000   # snizeno kvuli rychlosti demo
POCET = 4


t0 = time.perf_counter()
with ThreadPoolExecutor(max_workers=POCET) as ex:
    vysledky_t = list(ex.map(faktorial_iterace, [N] * POCET))
cas_thread = time.perf_counter() - t0

t0 = time.perf_counter()
with ProcessPoolExecutor(max_workers=POCET) as ex:
    vysledky_p = list(ex.map(faktorial_iterace, [N] * POCET))
cas_process = time.perf_counter() - t0

print(f"faktorial({N}) x {POCET} opakování:")
print(f"  ThreadPool:   {cas_thread:.3f}s  (GIL blokuje → bez speedupu)")
print(f"  ProcessPool:  {cas_process:.3f}s  (vice CPU jader)")
if cas_thread > 0 and cas_process > 0:
    print(f"  Speedup ProcessPool: {cas_thread/cas_process:.2f}x")
print(f"  Vysledky shodne: {len(set(str(r) for r in vysledky_t)) == 1}")


# 2. Thread-safe cache jako dekorator @thread_safe_cache

print("\n=== Ukol 2: @thread_safe_cache dekorator ===\n")


def thread_safe_cache(fn: Callable) -> Callable:
    """Thread-safe memoize dekorator pouzivajici dict + Lock."""
    cache: dict[tuple, Any] = {}
    zamek = threading.Lock()

    def wrapper(*args, **kwargs):
        klic = (args, tuple(sorted(kwargs.items())))
        with zamek:
            if klic in cache:
                return cache[klic]
        # Vypocet mimo zamek (nechceme blokovat ostatni thready)
        vysledek = fn(*args, **kwargs)
        with zamek:
            cache[klic] = vysledek
        return vysledek

    wrapper.cache = cache           # pro introspekci
    wrapper.__name__ = fn.__name__
    return wrapper


@thread_safe_cache
def pomaly_vypocet(n: int) -> int:
    """Simulace pomalého výpočtu."""
    time.sleep(0.1)
    return n * n


# Paralelni volani – sdilena cache
volani_poradi = []
zamek_log = threading.Lock()


def testuj(n: int):
    vysl = pomaly_vypocet(n)
    with zamek_log:
        volani_poradi.append((n, vysl))


thready = [threading.Thread(target=testuj, args=(i % 3,)) for i in range(9)]
t0 = time.perf_counter()
for t in thready: t.start()
for t in thready: t.join()
elapsed = time.perf_counter() - t0

print(f"9 volani (hodnoty 0,1,2 opakujici se) za {elapsed:.2f}s")
print(f"  (bez cache by trvalo ~{0.1*9:.1f}s, s cache ~{0.1*3:.1f}s)")
print(f"  Cache obsahuje {len(pomaly_vypocet.cache)} zaznamu: {pomaly_vypocet.cache}")


# 3. asyncio.Queue pro producer-consumer bez threadu

print("\n=== Ukol 3: asyncio.Queue – producer-consumer ===\n")


async def producent(fronta: asyncio.Queue, n: int, id_: int):
    """Generuje n ukolu a da je do fronty."""
    for i in range(n):
        ukol = f"ukol-{id_}-{i}"
        await fronta.put(ukol)
        await asyncio.sleep(0.01)
    # Sentinel pro kazdeho konzumenta
    await fronta.put(None)


async def konzument(fronta: asyncio.Queue, id_: int, vysledky: list):
    """Zpracovava ukoly dokud nenajde sentinel."""
    while True:
        ukol = await fronta.get()
        if ukol is None:
            fronta.task_done()
            break
        await asyncio.sleep(0.02)   # simulace zpracovani
        vysledky.append(f"konzument-{id_} zpracoval {ukol}")
        fronta.task_done()


async def async_main():
    fronta: asyncio.Queue = asyncio.Queue(maxsize=5)
    vysledky: list[str] = []

    t0 = time.perf_counter()

    # 2 producenti, 3 konzumenti
    producenti = [
        asyncio.create_task(producent(fronta, 5, 1)),
        asyncio.create_task(producent(fronta, 5, 2)),
    ]
    # Kazdy konzument potrebuje vlastni sentinel – producenti posheji 2
    konzumenti = [
        asyncio.create_task(konzument(fronta, k, vysledky))
        for k in range(2)
    ]

    await asyncio.gather(*producenti)
    await asyncio.gather(*konzumenti)

    elapsed = time.perf_counter() - t0
    print(f"asyncio producer-consumer: {len(vysledky)} ukolu za {elapsed:.2f}s")
    for zaz in vysledky[:4]:
        print(f"  {zaz}")
    if len(vysledky) > 4:
        print(f"  ... (+{len(vysledky)-4} dalsi)")


asyncio.run(async_main())
