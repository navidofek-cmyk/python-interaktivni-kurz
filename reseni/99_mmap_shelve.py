"""Řešení – Lekce 99: mmap a shelve – velké soubory a persistence

Toto je vzorové řešení úloh z lekce 99.
"""

import mmap
import shelve
import struct
import tempfile
import time
import random
from datetime import datetime, date
from pathlib import Path

TMPDIR = Path(tempfile.gettempdir())

# ── Úloha 1 ────────────────────────────────────────────────
# grep_mmap(soubor, hledany) – najde všechny výskyty bajtového
# řetězce v souboru přes mmap a vrátí jejich offsety.

def grep_mmap(soubor: str, hledany: bytes) -> list[int]:
    """
    Najde všechny výskyty `hledany` v souboru pomocí mmap.
    Vrátí seznam bajtových offsetů (pozic).
    """
    offsety = []
    with open(soubor, "rb") as f:
        mm = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)
        pos = 0
        while True:
            found = mm.find(hledany, pos)
            if found == -1:
                break
            offsety.append(found)
            pos = found + 1
        mm.close()
    return offsety


# Vytvoříme testovací Python soubor
testovaci_py = TMPDIR / "test_grep.py"
testovaci_py.write_text("""\
def secti(a, b):
    return a + b

def odecti(a, b):
    return a - b

def vypocitej():
    def vnitrni():
        pass
    return vnitrni

class Kalkulator:
    def __init__(self):
        pass
    def spocitej(self):
        def pomocna():
            pass
""", encoding="utf-8")

print("Úloha 1 – grep_mmap():")
offsety = grep_mmap(str(testovaci_py), b"def ")
print(f"  Soubor: {testovaci_py.name}")
print(f"  Hledané: b'def '")
print(f"  Nalezeno {len(offsety)} výskytů na offsetech: {offsety}")

# Ověříme – načteme řádky s def
obsah = testovaci_py.read_bytes()
for offset in offsety:
    konec = obsah.find(b"\n", offset)
    radek = obsah[offset:konec].decode("utf-8")
    print(f"    offset {offset:4d}: {radek!r}")

testovaci_py.unlink()
print()


# ── Úloha 2 ────────────────────────────────────────────────
# TtlCache – shelve-based cache s TTL (Time To Live).

class TtlCache:
    """Persistentní cache s TTL pomocí shelve."""

    def __init__(self, cesta: str):
        self._cesta = cesta

    def set(self, klic: str, hodnota, ttl_sekund: int = 60) -> None:
        """Uloží hodnotu s časem expirace."""
        expiry = time.time() + ttl_sekund
        with shelve.open(self._cesta) as db:
            db[klic] = (hodnota, expiry)

    def get(self, klic: str):
        """Vrátí hodnotu nebo None (pokud expirovala nebo neexistuje)."""
        with shelve.open(self._cesta) as db:
            zaznam = db.get(klic)
            if zaznam is None:
                return None
            hodnota, expiry = zaznam
            if time.time() > expiry:
                del db[klic]
                return None
            return hodnota

    def delete(self, klic: str) -> None:
        with shelve.open(self._cesta) as db:
            if klic in db:
                del db[klic]

    def cleanup(self) -> int:
        """Smaže expirované záznamy. Vrátí počet smazaných."""
        smazano = 0
        now = time.time()
        with shelve.open(self._cesta) as db:
            expirove = [k for k, (_, exp) in db.items() if now > exp]
            for k in expirove:
                del db[k]
                smazano += 1
        return smazano


cache_soubor = str(TMPDIR / "ttl_cache_test")
cache = TtlCache(cache_soubor)

print("Úloha 2 – TtlCache:")
cache.set("uzivatel_1", {"jmeno": "Alice", "vek": 30}, ttl_sekund=10)
cache.set("konfig",     {"debug": True}, ttl_sekund=1)    # expiruje rychle
cache.set("token",      "abc123xyz",     ttl_sekund=3600)

print(f"  get('uzivatel_1') = {cache.get('uzivatel_1')}")
print(f"  get('token')      = {cache.get('token')}")

time.sleep(1.1)   # Počkáme na expiraci "konfig"
print(f"  get('konfig') po 1s = {cache.get('konfig')}  (None = expirováno)")

cache.delete("token")
print(f"  get('token') po delete = {cache.get('token')}")

smazano = cache.cleanup()
print(f"  cleanup() smazal {smazano} expirovaných záznamů")

# Úklid shelve souborů
for suffix in ["", ".db", ".dir", ".bak", ".dat"]:
    Path(cache_soubor + suffix).unlink(missing_ok=True)
print()


# ── Úloha 3 ────────────────────────────────────────────────
# Binární soubor 100 000 záznamů struct "Ihf", čtení po stránkách přes mmap.

ZAZNAM_FMT = "Ihf"
ZAZNAM_VEL = struct.calcsize(ZAZNAM_FMT)   # = 12 bajtů
POCET = 100_000
STRANKA = 4096  # 4 KB stránka

bin_soubor = TMPDIR / "zaznamy100k.bin"

print("Úloha 3 – sumarizuj_mmap():")
# Vytvoříme soubor
with open(bin_soubor, "wb") as f:
    for i in range(POCET):
        f.write(struct.pack(ZAZNAM_FMT, i, i % 1000, random.uniform(0.5, 999.5)))

print(f"  Soubor: {bin_soubor.stat().st_size:,} B ({POCET:,} záznamů × {ZAZNAM_VEL} B)")


def sumarizuj_mmap(soubor: Path) -> dict:
    """
    Spočítá průměr, min a max pole 'cena' (3. složka struct Ihf)
    přes mmap bez načtení celého souboru do paměti.
    Čte po stránkách 4096 B.
    """
    celkem = 0.0
    min_cena = float("inf")
    max_cena = float("-inf")
    pocet = 0

    velikost = soubor.stat().st_size
    zaznamu_na_stranku = STRANKA // ZAZNAM_VEL

    with open(soubor, "rb") as f:
        mm = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)
        offset = 0
        while offset + ZAZNAM_VEL <= velikost:
            # Přečteme co nejvíce celých záznamů do stránky
            konec = min(offset + zaznamu_na_stranku * ZAZNAM_VEL, velikost)
            while offset + ZAZNAM_VEL <= konec:
                _, _, cena = struct.unpack_from(ZAZNAM_FMT, mm, offset)
                celkem += cena
                if cena < min_cena:
                    min_cena = cena
                if cena > max_cena:
                    max_cena = cena
                pocet += 1
                offset += ZAZNAM_VEL
        mm.close()

    return {
        "pocet":  pocet,
        "prumer": celkem / pocet if pocet else 0.0,
        "min":    min_cena,
        "max":    max_cena,
    }


stats = sumarizuj_mmap(bin_soubor)
print(f"  Výsledky (pole 'cena'):")
print(f"    Počet:   {stats['pocet']:,}")
print(f"    Průměr:  {stats['prumer']:.2f}")
print(f"    Min:     {stats['min']:.2f}")
print(f"    Max:     {stats['max']:.2f}")

bin_soubor.unlink()
print()


# ── Úloha 4 ────────────────────────────────────────────────
# shelve-based deník: zapis, vypis_dnes, hledej, statistiky.

class Denik:
    """Jednoduchý persistentní deník na shelve."""

    def __init__(self, cesta: str):
        self._cesta = cesta

    def _klic(self) -> str:
        return datetime.now().strftime("%Y-%m-%d_%H:%M:%S.%f")

    def zapis(self, text: str) -> str:
        klic = self._klic()
        with shelve.open(self._cesta, writeback=True) as db:
            db[klic] = text
        return klic

    def vypis_dnes(self) -> list[tuple[str, str]]:
        dnes = date.today().strftime("%Y-%m-%d")
        zaznamy = []
        with shelve.open(self._cesta) as db:
            for k in sorted(db.keys()):
                if k.startswith(dnes):
                    zaznamy.append((k, db[k]))
        return zaznamy

    def hledej(self, klic: str) -> list[tuple[str, str]]:
        """Vrátí záznamy obsahující klíčové slovo."""
        nalezene = []
        klic_lower = klic.lower()
        with shelve.open(self._cesta) as db:
            for k in sorted(db.keys()):
                if klic_lower in db[k].lower():
                    nalezene.append((k, db[k]))
        return nalezene

    def statistiky(self) -> dict:
        """Vrátí statistiky: počet zápisů, nejaktivnější den."""
        pocty: dict[str, int] = {}
        celkem = 0
        with shelve.open(self._cesta) as db:
            celkem = len(db)
            for k in db.keys():
                den = k[:10]   # YYYY-MM-DD
                pocty[den] = pocty.get(den, 0) + 1
        nejaktivnejsi = max(pocty, key=lambda d: pocty[d]) if pocty else None
        return {
            "celkem":        celkem,
            "nejaktivnejsi": nejaktivnejsi,
            "pocty_dni":     pocty,
        }


denik_soubor = str(TMPDIR / "denik_test")
denik = Denik(denik_soubor)

# Přidáme testovací záznamy
denik.zapis("Dnes jsem se naučil používat shelve v Pythonu.")
denik.zapis("Shelve je skvělé pro rychlé prototypy a ukládání dat.")
denik.zapis("Procvičoval jsem mmap pro čtení velkých binárních souborů.")
denik.zapis("Python je opravdu výborný jazyk pro skriptování.")

print("Úloha 4 – Denik:")
dnesni = denik.vypis_dnes()
print(f"  Záznamy z dneška ({len(dnesni)}):")
for k, v in dnesni:
    print(f"    [{k}] {v[:60]}...")

nalezene = denik.hledej("shelve")
print(f"\n  Hledání 'shelve' – nalezeno {len(nalezene)} záznamů")
for k, v in nalezene:
    print(f"    [{k}] {v[:60]}")

stats = denik.statistiky()
print(f"\n  Statistiky:")
print(f"    Celkem zápisů:       {stats['celkem']}")
print(f"    Nejaktivnější den:   {stats['nejaktivnejsi']}")

# Úklid
for suffix in ["", ".db", ".dir", ".bak", ".dat"]:
    Path(denik_soubor + suffix).unlink(missing_ok=True)
