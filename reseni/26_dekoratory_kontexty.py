"""Řešení – Lekce 26: Dekorátory a context managery"""

import time
import functools
import contextlib
import os
from functools import lru_cache


# 1. Dekorátor @retry(n) – při výjimce zkusí funkci znovu n-krát
# Čeká vždy o trochu déle (backoff) – aby nepřehlcoval server
def retry(n: int, delay: float = 0.1):
    """Při výjimce opakuje funkci až n-krát s krátkým čekáním."""
    def dekorator(funkce):
        @functools.wraps(funkce)
        def obal(*args, **kwargs):
            for pokus in range(1, n + 2):  # n+1 celkových pokusů
                try:
                    return funkce(*args, **kwargs)
                except Exception as e:
                    if pokus > n:
                        print(f"  [retry] {funkce.__name__} selhalo po {n+1} pokusech: {e}")
                        raise
                    print(f"  [retry] Pokus {pokus}/{n+1} selhal: {e}, zkouším znovu...")
                    time.sleep(delay)
        return obal
    return dekorator


print("=== @retry ===")
import random

pokusy = [0]

@retry(3, delay=0.05)
def nespolehlivy_server():
    pokusy[0] += 1
    if pokusy[0] < 3:
        raise ConnectionError("Server nedostupný")
    return "OK"

vysledek = nespolehlivy_server()
print(f"  Výsledek: {vysledek} (trvalo {pokusy[0]} pokusů)")


# 2. Context manager otevri_bezpecne – při chybě vytvoří soubor s výchozím obsahem
# try/yield/except vzor: yield předá řízení bloku with, except chytí chyby

@contextlib.contextmanager
def otevri_bezpecne(soubor: str, vychozi: str = "# výchozí obsah\n"):
    """Otevře soubor pro čtení; pokud neexistuje, vytvoří ho s výchozím obsahem."""
    if not os.path.exists(soubor):
        print(f"  [ctx] {soubor!r} nenalezen – vytvářím s výchozím obsahem")
        with open(soubor, "w", encoding="utf-8") as f:
            f.write(vychozi)
    try:
        with open(soubor, "r", encoding="utf-8") as f:
            yield f
    except IOError as e:
        print(f"  [ctx] Chyba čtení: {e}")
        yield None
    finally:
        # úklid: pro demo smažeme soubor pokud jsme ho vytvořili
        if os.path.exists(soubor) and vychozi in open(soubor).read():
            os.remove(soubor)


print("\n=== otevri_bezpecne ===")
with otevri_bezpecne("/tmp/test_config.txt", "debug=True\n") as f:
    if f:
        obsah = f.read()
        print(f"  Obsah souboru: {obsah!r}")


# 3. Kombinace @stopky + @lru_cache na prvočísla
# Cache si pamatuje výsledky – druhé volání je skoro okamžité

def stopky(funkce):
    @functools.wraps(funkce)
    def obal(*args, **kwargs):
        zacatek = time.perf_counter()
        vysledek = funkce(*args, **kwargs)
        konec = time.perf_counter()
        print(f"  stopky: {funkce.__name__}({args[0] if args else ''}) "
              f"→ {(konec-zacatek)*1000:.3f} ms")
        return vysledek
    return obal


# Pořadí dekorátorů záleží: @lru_cache zapamatuje výsledky,
# @stopky měří jen první (nezkešovaná) volání
@stopky
@lru_cache(maxsize=None)
def je_prvocislo(n: int) -> bool:
    """Kontrola prvočísla Eratosthenovým sítem (naivní)."""
    if n < 2:
        return False
    for i in range(2, int(n**0.5) + 1):
        if n % i == 0:
            return False
    return True


def prvocisla_do(limit: int) -> list[int]:
    return [n for n in range(2, limit + 1) if je_prvocislo(n)]


print("\n=== @stopky + @lru_cache na prvočísla ===")
print("  První volání (výpočet):")
prvni = prvocisla_do(100)
print(f"  Prvočísla do 100: {prvni[:10]}... ({len(prvni)} celkem)")

print("\n  Druhé volání (z cache):")
druhe = prvocisla_do(100)
print(f"  Výsledek stejný: {prvni == druhe}")
print(f"  Cache info: {je_prvocislo.cache_info()}")
