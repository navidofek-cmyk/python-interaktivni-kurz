"""
LEKCE 26: Dekorátory a context managery
=========================================
Dvě mocné pythonní zbraně.

DEKORÁTOR  = funkce, která obalí jinou funkci a přidá jí chování
             bez toho, abys musel měnit její kód.
             Syntaxe: @dekorator nad def.

CONTEXT MANAGER = objekt, který řídí "vstup" a "výstup" z bloku with.
             Používáš ho každý den: with open(...) as f
"""

import time
import functools
import contextlib

# ══════════════════════════════════════════════════════════════
# ČÁST 1: DEKORÁTORY
# ══════════════════════════════════════════════════════════════

# ── Nejjednodušší dekorátor ───────────────────────────────────

def krik(funkce):
    @functools.wraps(funkce)   # zachová jméno a docstring původní funkce
    def obal(*args, **kwargs):
        print(">>> ZAČÍNÁM <<<")
        vysledek = funkce(*args, **kwargs)
        print(">>> HOTOVO <<<")
        return vysledek
    return obal

@krik
def pozdrav(jmeno):
    print(f"Ahoj, {jmeno}!")

print("=== @krik ===")
pozdrav("Míša")

# ── Měření času ───────────────────────────────────────────────

def stopky(funkce):
    @functools.wraps(funkce)
    def obal(*args, **kwargs):
        zacatek = time.perf_counter()
        vysledek = funkce(*args, **kwargs)
        konec = time.perf_counter()
        print(f"  ⏱ {funkce.__name__}() trvalo {(konec-zacatek)*1000:.2f} ms")
        return vysledek
    return obal

@stopky
def secti_hodne(n):
    return sum(range(n))

print("\n=== @stopky ===")
print(secti_hodne(10_000_000))

# ── Dekorátor s parametrem ────────────────────────────────────

def opakuj(kolikrat):
    def dekorator(funkce):
        @functools.wraps(funkce)
        def obal(*args, **kwargs):
            for _ in range(kolikrat):
                funkce(*args, **kwargs)
        return obal
    return dekorator

@opakuj(3)
def bum():
    print("  BUM!")

print("\n=== @opakuj(3) ===")
bum()

# ── Cache (memoizace) – vestavěný dekorátor ──────────────────

from functools import lru_cache

@lru_cache(maxsize=None)   # zapamatuje si výsledky volání
@stopky
def fibonacci(n):
    if n < 2:
        return n
    return fibonacci(n - 1) + fibonacci(n - 2)

print("\n=== @lru_cache (Fibonacci) ===")
print(f"fib(35) = {fibonacci(35)}")
print(f"fib(35) = {fibonacci(35)}")   # druhé volání: z cache, skoro 0 ms

# ── Více dekorátorů najednou – pořadí záleží! ────────────────

def hvezdy(f):
    @functools.wraps(f)
    def obal(*a, **k):
        print("★★★★★")
        f(*a, **k)
        print("★★★★★")
    return obal

def ramecek(f):
    @functools.wraps(f)
    def obal(*a, **k):
        print("─" * 20)
        f(*a, **k)
        print("─" * 20)
    return obal

@hvezdy        # aplikuje se jako druhý (vnější)
@ramecek       # aplikuje se jako první (vnitřní)
def zprava():
    print("  Důležitá zpráva!")

print("\n=== Vrstvené dekorátory ===")
zprava()


# ══════════════════════════════════════════════════════════════
# ČÁST 2: CONTEXT MANAGERY
# ══════════════════════════════════════════════════════════════

# ── Vlastní context manager přes třídu ───────────────────────

class Transakce:
    def __init__(self, jmeno):
        self.jmeno = jmeno

    def __enter__(self):
        print(f"\n  [DB] BEGIN {self.jmeno}")
        return self          # to, co dostaneme jako `as x`

    def __exit__(self, typ, hodnota, tb):
        if typ is None:      # žádná výjimka
            print(f"  [DB] COMMIT {self.jmeno}")
        else:
            print(f"  [DB] ROLLBACK {self.jmeno} – chyba: {hodnota}")
        return True          # True = výjimku pohltíme (nepropadne dál)

    def uloz(self, data):
        print(f"  [DB] INSERT {data!r}")

print("=== Context manager (třída) ===")
with Transakce("platba") as t:
    t.uloz({"částka": 500, "příjemce": "Míša"})
    t.uloz({"částka": 200, "příjemce": "Tomáš"})

print()
with Transakce("chybná operace") as t:
    t.uloz({"data": "ok"})
    raise ValueError("Nedostatek peněz")   # simulace chyby

# ── Vlastní context manager přes @contextmanager ─────────────

@contextlib.contextmanager
def casovac(nazev):
    print(f"  ▶ Start: {nazev}")
    zacatek = time.perf_counter()
    try:
        yield          # sem přijde tělo bloku `with`
    finally:
        trvalo = time.perf_counter() - zacatek
        print(f"  ■ Konec: {nazev} ({trvalo*1000:.1f} ms)")

print("=== @contextmanager ===")
with casovac("výpočet"):
    vysledek = sum(i**2 for i in range(1_000_000))
    print(f"  výsledek = {vysledek}")

# ── Vnořené / více context managerů najednou ─────────────────

print("\n=== Více context managerů ===")
with (
    casovac("celá sekce"),
    contextlib.suppress(ZeroDivisionError),   # tiše ignoruj tuto výjimku
):
    print("  10 / 2 =", 10 / 2)
    print("  10 / 0 =", 10 / 0)   # chyba – suppress ji zahodí
    print("  Toto se nevytiskne.")

print("  Pokračujeme po bloku with – suppress fungovalo.")

# TVOJE ÚLOHA:
# 1. Napište dekorátor @retry(n), který při výjimce zkusí funkci znovu n-krát.
# 2. Napište context manager `otevri_bezpecne(soubor)`, který při chybě
#    vytvoří soubor s výchozím obsahem místo pádu programu.
# 3. Zkombinujte @stopky a @lru_cache na funkci počítající prvočísla
#    a změřte, jak moc cache pomáhá.
