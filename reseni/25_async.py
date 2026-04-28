"""Řešení – Lekce 25: Async / Await – souběžnost"""

import asyncio
import random
import time


# 1. Async funkce pocasi – stáhne počasí pro 5 měst souběžně
# gather() spustí všechny korutiny paralelně – čeká jen na nejpomalejší

async def pocasi(mesto: str) -> tuple[str, float]:
    """Simuluje stahování počasí (sleep 1s) a vrátí náhodnou teplotu."""
    await asyncio.sleep(1)  # simulace síťového volání
    teplota = round(random.uniform(-5, 35), 1)
    return mesto, teplota


async def demo_pocasi():
    print("=== Počasí pro 5 měst souběžně ===\n")
    mesta = ["Praha", "Brno", "Ostrava", "Plzeň", "Liberec"]

    zacatek = time.time()
    # gather spustí všech 5 najednou – trvá ~1s, ne 5s
    vysledky = await asyncio.gather(*[pocasi(m) for m in mesta])
    trvalo = time.time() - zacatek

    for mesto, teplota in vysledky:
        print(f"  {mesto:<12} {teplota:+.1f}°C")
    print(f"\n  Trvalo: {trvalo:.2f}s (sekvenčně by bylo ~5s)")

asyncio.run(demo_pocasi())


# 2. asyncio.Queue – producent přidává čísla, dva konzumenti je zpracovávají
# Queue umožňuje komunikaci mezi korutinami bez závodních podmínek

async def producent(fronta: asyncio.Queue, n: int):
    """Přidá čísla 0..n-1 do fronty."""
    for i in range(n):
        await asyncio.sleep(random.uniform(0.05, 0.15))
        await fronta.put(i)
        print(f"  [Producent] přidal: {i}")
    # Sentinel hodnoty – signál pro každého konzumenta
    await fronta.put(None)
    await fronta.put(None)


async def konzument(jmeno: str, fronta: asyncio.Queue, vysledky: list):
    """Zpracovává čísla z fronty dokud nedostane None."""
    while True:
        cislo = await fronta.get()
        if cislo is None:
            print(f"  [{jmeno}] konec práce")
            fronta.task_done()
            break
        # simulace zpracování
        await asyncio.sleep(0.1)
        vysledek = cislo ** 2
        vysledky.append((jmeno, cislo, vysledek))
        print(f"  [{jmeno}] zpracoval {cislo} → {vysledek}")
        fronta.task_done()


async def demo_queue():
    print("\n=== asyncio.Queue – producent & 2 konzumenti ===\n")
    fronta = asyncio.Queue(maxsize=5)
    vysledky = []

    await asyncio.gather(
        producent(fronta, 8),
        konzument("Konzument-A", fronta, vysledky),
        konzument("Konzument-B", fronta, vysledky),
    )
    print(f"\n  Celkem zpracováno: {len(vysledky)} položek")

asyncio.run(demo_queue())


# 3. Měření: gather() vs. sekvenční await
# Ukáže konkrétní číselný rozdíl v sekundách

async def pomala_uloha(n: float):
    await asyncio.sleep(n)
    return n


async def demo_mereni():
    print("\n=== Gather vs. sekvenční – měření ===\n")
    zpozdeni = [0.3, 0.5, 0.4, 0.6, 0.2]

    # Sekvenční – čeká na každou úlohu zvlášť
    t0 = time.perf_counter()
    for z in zpozdeni:
        await pomala_uloha(z)
    sekv_cas = time.perf_counter() - t0

    # Souběžné s gather – čeká jen na nejdelší
    t0 = time.perf_counter()
    await asyncio.gather(*[pomala_uloha(z) for z in zpozdeni])
    gather_cas = time.perf_counter() - t0

    print(f"  Sekvenční:  {sekv_cas:.2f}s  (suma: {sum(zpozdeni):.1f}s)")
    print(f"  gather():   {gather_cas:.2f}s  (max:  {max(zpozdeni):.1f}s)")
    print(f"  Zrychlení:  {sekv_cas / gather_cas:.1f}×")

asyncio.run(demo_mereni())
