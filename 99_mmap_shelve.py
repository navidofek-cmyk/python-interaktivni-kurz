"""
LEKCE 99: mmap a shelve – velké soubory a persistence
=======================================================
Naučíš se číst obrovské soubory bez načítání do RAM
a ukládat Python objekty přímo na disk.

mmap (memory-mapped files):
  – soubor je mapován do virtuální paměti procesu
  – OS načítá jen stránky, které skutečně čteš
  – random access: přeskočíš na pozici 500 MB v O(1)
  – ideální: binární soubory, logy, databázové stránky

shelve (persistent dictionary):
  – shelve.open("db") → dict-like objekt
  – klíče: string, hodnoty: libovolný pickle-ovaný objekt
  – automaticky ukládá na disk
  – kdy shelve vs SQLite vs pickle?
    shelve   → rychlé prototypy, malé projekty
    SQLite   → dotazy, transakce, sdílení
    pickle   → jednorázový dump/load, ne inkrementální
"""

import mmap
import shelve
import os
import time
import struct
import tempfile
import random
import pickle
from pathlib import Path

print("=== LEKCE 99: mmap a shelve ===\n")

TMPDIR = Path(tempfile.gettempdir())

# ══════════════════════════════════════════════════════════════
# ČÁST 1: mmap – základy
# ══════════════════════════════════════════════════════════════

print("── Část 1: mmap – základy ──\n")

# Vytvoříme testovací binární soubor
BINARNI_SOUBOR = TMPDIR / "testdata.bin"
POCET_ZAZNAMU = 10_000
ZAZNAM_VELIKOST = 16  # 4× int32 = 16 bajtů

print(f"  Vytváříme binární soubor: {POCET_ZAZNAMU} záznamů × {ZAZNAM_VELIKOST} B")
with open(BINARNI_SOUBOR, "wb") as f:
    for i in range(POCET_ZAZNAMU):
        # Každý záznam: id(int32), hodnota(int32), x(float32), y(float32)
        zaznam = struct.pack("iiff", i, i * 3, i * 0.1, i * 0.2)
        f.write(zaznam)

velikost_mb = BINARNI_SOUBOR.stat().st_size / 1024 / 1024
print(f"  Soubor vytvořen: {BINARNI_SOUBOR.stat().st_size:,} B ({velikost_mb:.2f} MB)\n")

# Čtení přes mmap – random access
with open(BINARNI_SOUBOR, "rb") as f:
    mm = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)

    # Přeskok na libovolný záznam v O(1) – bez čtení celého souboru!
    def cti_zaznam(mm: mmap.mmap, index: int) -> tuple:
        offset = index * ZAZNAM_VELIKOST
        mm.seek(offset)
        data = mm.read(ZAZNAM_VELIKOST)
        return struct.unpack("iiff", data)

    print("  Random access do souboru (žádné načítání celého souboru):")
    for idx in [0, 999, 4999, 9999]:
        id_, val, x, y = cti_zaznam(mm, idx)
        print(f"    Záznam #{idx:5d}: id={id_}, val={val}, x={x:.1f}, y={y:.1f}")

    # Prohledání přes mmap.find() – jako bytes
    hledany = struct.pack("i", 500)   # hledáme id=500
    pozice = mm.find(hledany)
    print(f"\n  mmap.find(id=500) → bajt offset {pozice} (záznam #{pozice // ZAZNAM_VELIKOST})")

    velikost = mm.size()
    print(f"  mmap.size() = {velikost:,} bajtů")
    mm.close()

print()

# ══════════════════════════════════════════════════════════════
# ČÁST 2: mmap – zápis (read/write)
# ══════════════════════════════════════════════════════════════

print("── Část 2: mmap – čtení i zápis ──\n")

MMAP_RW_SOUBOR = TMPDIR / "rw_test.bin"

# Připravíme soubor s nulami (mmap potřebuje existující soubor)
MMAP_RW_SOUBOR.write_bytes(b"\x00" * 1024)

with open(MMAP_RW_SOUBOR, "r+b") as f:
    mm = mmap.mmap(f.fileno(), 0)

    # Zapisujeme přímo do mapované paměti
    mm.seek(0)
    mm.write(b"Ahoj, mmape! ")
    mm.write(struct.pack("i", 42))
    mm.write(b" - konec")

    # Čteme zpět
    mm.seek(0)
    text = mm.read(13).decode("utf-8")
    cislo = struct.unpack("i", mm.read(4))[0]
    zbytek = mm.read(8).decode("utf-8")

    print(f"  Zapsáno a přečteno přes mmap:")
    print(f"    text:   {text!r}")
    print(f"    číslo:  {cislo}")
    print(f"    zbytek: {zbytek!r}")
    mm.close()

MMAP_RW_SOUBOR.unlink()
print()

# ══════════════════════════════════════════════════════════════
# ČÁST 3: Výkon – mmap vs klasické read()
# ══════════════════════════════════════════════════════════════

print("── Část 3: Výkon mmap vs read() ──\n")

# Vytvoříme větší soubor pro test
PERF_SOUBOR = TMPDIR / "perf_test.bin"
N_ZAZNAMU = 50_000

with open(PERF_SOUBOR, "wb") as f:
    for i in range(N_ZAZNAMU):
        f.write(struct.pack("i", i))

nahodne_indexy = [random.randint(0, N_ZAZNAMU - 1) for _ in range(500)]

# Test 1: klasické read() – seek + read pro každý záznam
start = time.perf_counter()
with open(PERF_SOUBOR, "rb") as f:
    for idx in nahodne_indexy:
        f.seek(idx * 4)
        _ = struct.unpack("i", f.read(4))[0]
cas_read = time.perf_counter() - start

# Test 2: mmap random access
start = time.perf_counter()
with open(PERF_SOUBOR, "rb") as f:
    mm = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)
    for idx in nahodne_indexy:
        mm.seek(idx * 4)
        _ = struct.unpack("i", mm.read(4))[0]
    mm.close()
cas_mmap = time.perf_counter() - start

# Test 3: mmap přes slice (nejrychlejší)
start = time.perf_counter()
with open(PERF_SOUBOR, "rb") as f:
    mm = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)
    for idx in nahodne_indexy:
        _ = struct.unpack_from("i", mm, idx * 4)[0]
    mm.close()
cas_mmap_slice = time.perf_counter() - start

print(f"  {N_ZAZNAMU:,} záznamů, 500 náhodných přístupů:")
print(f"  Klasické read():    {cas_read*1000:.2f} ms")
print(f"  mmap seek+read:     {cas_mmap*1000:.2f} ms")
print(f"  mmap unpack_from:   {cas_mmap_slice*1000:.2f} ms  (nejrychlejší)")
print()

PERF_SOUBOR.unlink()
BINARNI_SOUBOR.unlink()

# ══════════════════════════════════════════════════════════════
# ČÁST 4: shelve – persistent dictionary
# ══════════════════════════════════════════════════════════════

print("── Část 4: shelve – persistent dictionary ──\n")

SHELVE_SOUBOR = str(TMPDIR / "muj_shelve")

# Zápis
with shelve.open(SHELVE_SOUBOR) as db:
    db["uzivatel"] = {"jmeno": "Alice", "vek": 30, "role": "admin"}
    db["kurz_postup"] = {"dokoncene_lekce": list(range(1, 96)), "skore": 4250}
    db["nastaveni"] = {"tema": "dark", "jazyk": "cs", "notifikace": True}
    db["cisla"] = [1, 2, 3, 4, 5]
    print(f"  Uloženo {len(db)} záznamů do shelve")
    print(f"  Klíče: {list(db.keys())}")

# Čtení (jiná session – simulujeme restart programu)
print("\n  Po 'restartu' programu – čtení ze shelve:")
with shelve.open(SHELVE_SOUBOR) as db:
    uzivatel = db["uzivatel"]
    print(f"  Uživatel:     {uzivatel['jmeno']} (vek={uzivatel['vek']}, role={uzivatel['role']})")

    postup = db["kurz_postup"]
    print(f"  Postup:       {len(postup['dokoncene_lekce'])} lekcí, skóre={postup['skore']}")

    # Pozor: mutace in-place nefunguje bez writeback=True!
    db["cisla"].append(6)     # TOTO SE NEULOŽÍ bez writeback!

print()
with shelve.open(SHELVE_SOUBOR) as db:
    print(f"  Cisla bez writeback: {db['cisla']}  ← 6 chybí!")

# Správný způsob: writeback=True nebo přiřazení
with shelve.open(SHELVE_SOUBOR, writeback=True) as db:
    db["cisla"].append(6)     # writeback=True → uloží se

with shelve.open(SHELVE_SOUBOR) as db:
    print(f"  Cisla s writeback:   {db['cisla']}  ← 6 je tam")
print()

# ══════════════════════════════════════════════════════════════
# ČÁST 5: Porovnání shelve vs pickle vs sqlite
# ══════════════════════════════════════════════════════════════

print("── Část 5: Kdy co použít ──\n")

print("""  PICKLE:
    ✓ Jednoduchý dump celého objektu najednou
    ✓ Nejrychlejší pro serializaci/deserializaci
    ✗ Celý soubor = jeden objekt (ne inkrementální)
    ✗ Bezpečnostní riziko (nikdy nenačítej cizí pickle!)
    Použij: cache výsledků, uložení ML modelu

  SHELVE:
    ✓ Dict-like API, snadné použití
    ✓ Ukládá inkrementálně (jen změněné klíče)
    ✓ Hodnoty mohou být libovolné Python objekty
    ✗ Klíče musí být stringy
    ✗ Není thread-safe bez zámků
    ✗ Formát není přenositelný (OS/Python verze)
    Použij: osobní nástroje, rychlé prototypy

  SQLITE:
    ✓ Dotazy (SELECT, WHERE, JOIN)
    ✓ Transakce (ACID)
    ✓ Thread-safe, process-safe
    ✓ Přenositelný formát, čitelný nástroji
    ✗ Více kódu (ORM nebo raw SQL)
    Použij: produkce, sdílená data, dotazy
""")

# Výkonové srovnání shelve vs pickle pro 1000 objektů
DATA = {f"klic_{i}": {"id": i, "data": list(range(10))} for i in range(1000)}

# Pickle – uloží vše najednou
PICKLE_SOUBOR = TMPDIR / "test.pkl"
start = time.perf_counter()
with open(PICKLE_SOUBOR, "wb") as f:
    pickle.dump(DATA, f)
cas_pickle_zapis = time.perf_counter() - start

start = time.perf_counter()
with open(PICKLE_SOUBOR, "rb") as f:
    _ = pickle.load(f)
cas_pickle_cteni = time.perf_counter() - start

# Shelve – inkrementální
start = time.perf_counter()
with shelve.open(SHELVE_SOUBOR + "_perf") as db:
    for k, v in DATA.items():
        db[k] = v
cas_shelve_zapis = time.perf_counter() - start

start = time.perf_counter()
with shelve.open(SHELVE_SOUBOR + "_perf") as db:
    _ = {k: db[k] for k in db}
cas_shelve_cteni = time.perf_counter() - start

print(f"  1000 objektů – zápis a čtení:")
print(f"  {'':5} {'Zápis':>12} {'Čtení':>12}")
print(f"  Pickle  {cas_pickle_zapis*1000:>10.2f} ms {cas_pickle_cteni*1000:>10.2f} ms  (vše najednou)")
print(f"  Shelve  {cas_shelve_zapis*1000:>10.2f} ms {cas_shelve_cteni*1000:>10.2f} ms  (inkrementální)")
print()

# Úklid
for p in [PICKLE_SOUBOR]:
    p.unlink(missing_ok=True)
for suffix in ["", ".db", ".dir", ".bak", ".dat", "_perf", "_perf.db",
               "_perf.dir", "_perf.bak", "_perf.dat"]:
    Path(SHELVE_SOUBOR + suffix).unlink(missing_ok=True)
print("  Dočasné soubory smazány.\n")

# ══════════════════════════════════════════════════════════════
# TVOJE ÚLOHA:
# ══════════════════════════════════════════════════════════════
print("=" * 55)
print("TVOJE ÚLOHA:")
print("=" * 55)
print("""
1. Napiš funkci `grep_mmap(soubor: str, hledany: bytes)
   -> list[int]`, která pomocí mmap najde všechny výskyty
   hledaného bajtového řetězce v souboru a vrátí seznam
   jejich offsetů (pozic v souboru). Otestuj na textovém
   souboru (zakóduj do UTF-8) hledáním slova b"def ".

2. Implementuj jednoduchou shelve-based cache s TTL:
   class TtlCache:
       def set(self, klic, hodnota, ttl_sekund=60)
       def get(self, klic)  → hodnota nebo None (po expiraci)
       def delete(self, klic)
       def cleanup()  → smaže expirované záznamy
   Použij shelve pro persistenci, ukládej (hodnota, expiry_ts).

3. Vytvoř binární soubor s 100 000 záznamů ve formátu
   struct "Ihf" (unsigned int id, int hodnota, float cena).
   Napiš funkci `sumarizuj_mmap(soubor)`, která přes mmap
   spočítá průměr, min a max pole 'cena' bez načtení celého
   souboru do paměti najednou (čti po stránkách 4096 B).

4. Napiš shelve-based deník (journal):
   - zapis(text: str) → uloží záznam s časovou značkou
   - vypis_dnes() → všechny záznamy z dneška
   - hledej(klic: str) → záznamy obsahující klíčové slovo
   - statistiky() → počet zápisů, nejaktivnější den
   Záznamy ukládej pod klíčem ve formátu "YYYY-MM-DD_HH:MM:SS".
""")
