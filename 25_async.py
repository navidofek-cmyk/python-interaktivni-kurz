"""
LEKCE 25: Async / Await – souběžnost
=======================================
Normální Python: dělá jednu věc, čeká, pak pokračuje.
Async Python:    spustí víc věcí, zatímco čeká → rychlejší!

Analogie:
  Bez async: Objednám pizzu → stojím u dveří a čekám → pizza přijde → jím.
  S async:   Objednám pizzu → jdu hrát hry → zvonek → jím.

Kdy async POMÁHÁ:
  - Stahování souborů, volání API, čtení ze sítě (I/O-bound úkoly)
  - Ovládání více věcí najednou (chat, server, hry)

Kdy async NEPOMÁHÁ:
  - Těžké výpočty (to je paralelismus – jiné téma)

Klíčová slova:
  async def  → definice async funkce (korutiny)
  await      → "čekej zde, ale pusť ostatní dál"
  asyncio.run()        → spustí async svět
  asyncio.gather()     → spusť více věcí souběžně
  asyncio.sleep()      → async čekání (neblokuje)
"""

import asyncio
import time
import random

# ── 1. Základní async funkce ─────────────────────────────────────────────────

async def pozdrav(jmeno, zpozdeni):
    print(f"  Čekám na {jmeno}... ({zpozdeni}s)")
    await asyncio.sleep(zpozdeni)    # NEBLOKUJE – ostatní běží dál
    print(f"  Ahoj, {jmeno}!")

async def demo_zaklad():
    print("=== Souběžné pozdravy ===")
    zacatek = time.time()

    # gather = spusť oboje ZÁROVEŇ, počkej než oboje skončí
    await asyncio.gather(
        pozdrav("Míša", 2),
        pozdrav("Tomáš", 1),
        pozdrav("Bara", 3),
    )

    print(f"  Celkem trvalo: {time.time()-zacatek:.1f}s  "
          f"(bez async by to bylo ~6s)\n")

asyncio.run(demo_zaklad())


# ── 2. Async generátor – streamování dat ─────────────────────────────────────

async def nacti_zpravy(kanal):
    zpravy = [
        "Server: spojení navázáno",
        "Server: data přijata",
        "Server: zpracování...",
        "Server: hotovo!",
    ]
    for z in zpravy:
        await asyncio.sleep(random.uniform(0.3, 0.8))
        yield f"[{kanal}] {z}"

async def demo_stream():
    print("=== Streaming ze dvou kanálů souběžně ===")

    async def tiskni_kanal(kanal):
        async for zprava in nacti_zpravy(kanal):
            print(f"  {zprava}")

    await asyncio.gather(
        tiskni_kanal("A"),
        tiskni_kanal("B"),
    )
    print()

asyncio.run(demo_stream())


# ── 3. Async timeout – co když to trvá moc dlouho ───────────────────────────

async def pomal_server():
    await asyncio.sleep(5)
    return "výsledek"

async def demo_timeout():
    print("=== Timeout ===")
    try:
        vysledek = await asyncio.wait_for(pomal_server(), timeout=2.0)
        print(f"  Odpověď: {vysledek}")
    except asyncio.TimeoutError:
        print("  Server neodpověděl do 2s – timeout!")
    print()

asyncio.run(demo_timeout())


# ── 4. Praktická ukázka – "stahování" souborů ────────────────────────────────

async def stahni(soubor, velikost_mb):
    print(f"  ↓ Začínám stahovat {soubor} ({velikost_mb} MB)...")
    await asyncio.sleep(velikost_mb * 0.3)   # simulace rychlosti sítě
    print(f"  ✓ {soubor} staženo!")
    return velikost_mb

async def demo_stahování():
    print("=== Stahování souborů ===")
    soubory = [
        ("hra.zip",    80),
        ("video.mp4",  50),
        ("hudba.mp3",   5),
        ("dokument.pdf", 2),
    ]

    zacatek = time.time()

    # Bez async: 80+50+5+2 = 137 * 0.3 = ~41s (simulace)
    # S async:   max(80,50,5,2) * 0.3 = ~24s
    stazeno = await asyncio.gather(*[stahni(s, v) for s, v in soubory])

    celkem = sum(stazeno)
    trvalo = time.time() - zacatek
    print(f"\n  Celkem staženo: {celkem} MB za {trvalo:.1f}s")
    print(f"  (Sekvenčně by to trvalo ~{celkem*0.3:.0f}s)\n")

asyncio.run(demo_stahování())


# ── 5. async with – async kontext manager ────────────────────────────────────

class AsyncSpojeni:
    async def __aenter__(self):
        print("  Navazuji spojení...")
        await asyncio.sleep(0.5)
        print("  Spojení navázáno.")
        return self

    async def __aexit__(self, *args):
        await asyncio.sleep(0.2)
        print("  Spojení uzavřeno.")

    async def dotaz(self, sql):
        await asyncio.sleep(0.3)
        return f"výsledek({sql!r})"

async def demo_context():
    print("=== Async context manager ===")
    async with AsyncSpojeni() as db:
        r1 = await db.dotaz("SELECT * FROM uzivatele")
        r2 = await db.dotaz("SELECT * FROM produkty")
        print(f"  {r1}")
        print(f"  {r2}")
    print()

asyncio.run(demo_context())


# ── Přehled vzorů ─────────────────────────────────────────────────────────────
print("=== Cheat sheet ===")
print("""
  async def foo():          # async funkce (korutina)
      await asyncio.sleep(1)

  asyncio.run(foo())        # spusť z normálního kódu

  await asyncio.gather(     # spusť souběžně
      foo(), bar()
  )

  await asyncio.wait_for(   # s timeoutem
      foo(), timeout=3.0
  )

  async for x in gen():     # async generátor
      ...

  async with res() as r:    # async context manager
      ...
""")

# TVOJE ÚLOHA:
# 1. Napiš async funkci `pocasi(mesto)`, která "stáhne" počasí (sleep 1s)
#    a vrátí náhodnou teplotu. Spusť pro 5 měst souběžně.
# 2. Přidej asyncio.Queue: jeden "producent" přidává čísla, dva "konzumenti" je zpracovávají.
# 3. Změř, o kolik je gather() rychlejší než sekvenční await await await.
