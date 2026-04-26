"""
LEKCE 47: Funkcionální programování
=====================================
FP = styl programování kde funkce jsou "první třídou" –
     předáváš je jako argumenty, vracíš jako hodnoty, skládáš je.

Klíčové myšlenky:
  Pure functions     – stejný vstup → vždy stejný výstup, žádné side effects
  Immutability       – neměnnost dat
  Function composition – skládání malých funkcí do větších
  Higher-order functions – funkce které berou/vracejí funkce

Python není čistě funkcionální, ale podporuje tento styl dobře.
"""

from functools import reduce, partial, wraps
from itertools import chain, starmap, takewhile, dropwhile, accumulate
import operator

# ══════════════════════════════════════════════════════════════
# ČÁST 1: MAP, FILTER, REDUCE
# ══════════════════════════════════════════════════════════════

print("=== map / filter / reduce ===\n")

cisla = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

# map – aplikuj funkci na každý prvek
ctverece = list(map(lambda x: x**2, cisla))
print(f"map (čtverce):   {ctverece}")

# ekvivalent list comprehension – preferovaný v Pythonu
ctverece2 = [x**2 for x in cisla]
print(f"list comp:       {ctverece2}")

# filter – vyber prvky splňující podmínku
suda = list(filter(lambda x: x % 2 == 0, cisla))
print(f"filter (sudá):   {suda}")

# reduce – sbal seznam na jednu hodnotu
soucin = reduce(operator.mul, cisla)
print(f"reduce (součin): {soucin}")

soucet = reduce(operator.add, cisla)
print(f"reduce (součet): {soucet}  (= sum: {sum(cisla)})")

# Komplex: průměr bez sum/len
prumer = reduce(lambda acc, x: acc + x, cisla) / reduce(lambda acc, _: acc + 1, cisla, 0)
print(f"reduce (průměr): {prumer}")

# Reálný příklad
data = [
    {"jmeno": "Míša",  "vek": 15, "body": 87},
    {"jmeno": "Tomáš", "vek": 16, "body": 92},
    {"jmeno": "Bára",  "vek": 14, "body": 78},
    {"jmeno": "Ondra", "vek": 17, "body": 95},
    {"jmeno": "Klára", "vek": 15, "body": 65},
]

top_body = list(map(
    lambda s: s["jmeno"],
    filter(lambda s: s["body"] >= 85, data)
))
print(f"\nStudenti s 85+ body: {top_body}")

# Totéž čitelněji:
top_body2 = [s["jmeno"] for s in data if s["body"] >= 85]
print(f"list comp:           {top_body2}")


# ══════════════════════════════════════════════════════════════
# ČÁST 2: PARTIAL – parciální aplikace
# ══════════════════════════════════════════════════════════════

print("\n=== partial – fixace argumentů ===\n")

def mocnina(zaklad, exponent):
    return zaklad ** exponent

druha = partial(mocnina, exponent=2)
treti = partial(mocnina, exponent=3)

print(f"druha(5)  = {druha(5)}")
print(f"treti(3)  = {treti(3)}")
print(f"[druha(i) for i in range(6)] = {[druha(i) for i in range(6)]}")

# Partial s print
tiskni_prefix = partial(print, "  [LOG]", sep=" | ")
tiskni_prefix("Server started")
tiskni_prefix("User connected")

# Reálný příklad: konfigurovatelný validátor
def validuj(hodnota, *, min_val, max_val, zprava):
    if not (min_val <= hodnota <= max_val):
        raise ValueError(f"{zprava}: {hodnota} mimo rozsah [{min_val}, {max_val}]")
    return hodnota

validuj_vek  = partial(validuj, min_val=0,   max_val=150, zprava="Věk")
validuj_body = partial(validuj, min_val=0,   max_val=100, zprava="Body")
validuj_hp   = partial(validuj, min_val=0,   max_val=999, zprava="HP")

print(f"\n  validuj_vek(25)   = {validuj_vek(25)}")
print(f"  validuj_body(87)  = {validuj_body(87)}")
try:
    validuj_vek(200)
except ValueError as e:
    print(f"  validuj_vek(200)  → {e}")


# ══════════════════════════════════════════════════════════════
# ČÁST 3: FUNCTION COMPOSITION
# ══════════════════════════════════════════════════════════════

print("\n=== Kompozice funkcí ===\n")

from typing import Callable, TypeVar
T = TypeVar("T")

def compose(*fns: Callable) -> Callable:
    """compose(f, g, h)(x) == f(g(h(x)))"""
    def composed(x):
        result = x
        for fn in reversed(fns):
            result = fn(result)
        return result
    return composed

def pipe(*fns: Callable) -> Callable:
    """pipe(f, g, h)(x) == h(g(f(x)))  – opačné pořadí než compose"""
    def piped(x):
        result = x
        for fn in fns:
            result = fn(result)
        return result
    return piped

# Zpracování textu jako pipeline
normalizuj = pipe(
    str.strip,
    str.lower,
    lambda s: s.replace("-", " "),
    lambda s: " ".join(s.split()),   # normalize whitespace
)

print("Normalizace textu:")
vstupy = ["  Python-kurz  ", "HELLO   WORLD", "  foo--bar  "]
for v in vstupy:
    print(f"  {v!r:25} → {normalizuj(v)!r}")

# Matematická pipeline
zpracuj = pipe(
    lambda lst: filter(lambda x: x > 0, lst),   # jen kladná
    lambda lst: map(lambda x: x**2, lst),         # kvadrát
    list,
    partial(sorted, reverse=True),                # seřaď sestupně
)

data2 = [-3, 5, -1, 2, 8, -4, 3]
print(f"\n  {data2} → {zpracuj(data2)}")


# ══════════════════════════════════════════════════════════════
# ČÁST 4: CURRYING
# ══════════════════════════════════════════════════════════════

print("\n=== Currying ===\n")

def curry(fn):
    """Transformuje f(a,b,c) na f(a)(b)(c)."""
    import inspect
    n = len(inspect.signature(fn).parameters)

    def curried(*args):
        if len(args) >= n:
            return fn(*args[:n])
        return lambda *more: curried(*(args + more))
    return curried

@curry
def secti(a, b, c):
    return a + b + c

print(f"secti(1)(2)(3) = {secti(1)(2)(3)}")
print(f"secti(1, 2)(3) = {secti(1, 2)(3)}")
print(f"secti(1)(2, 3) = {secti(1)(2, 3)}")

pricti_10 = secti(10)
print(f"pricti_10(5)(3) = {pricti_10(5)(3)}")


# ══════════════════════════════════════════════════════════════
# ČÁST 5: itertools pro FP
# ══════════════════════════════════════════════════════════════

print("\n=== itertools v FP stylu ===\n")

# accumulate – running totals
body_postupne = list(accumulate([10, 5, 20, 15, 8]))
print(f"Kumulativní body: {body_postupne}")

# starmap – map s rozbalením argumentů
body_pairy = [(3, 4), (5, 12), (8, 15)]
prepony = list(starmap(lambda a, b: (a**2 + b**2)**0.5, body_pairy))
print(f"Přepony:          {prepony}")

# takewhile / dropwhile
cisla2 = [2, 4, 6, 7, 8, 10, 11, 12]
print(f"takewhile(sudé):  {list(takewhile(lambda x: x%2==0, cisla2))}")
print(f"dropwhile(sudé):  {list(dropwhile(lambda x: x%2==0, cisla2))}")

# Funkcionální FizzBuzz
fizzbuzz = pipe(
    lambda n: range(1, n+1),
    partial(map, lambda i: "FizzBuzz" if i%15==0
                      else "Fizz" if i%3==0
                      else "Buzz" if i%5==0
                      else str(i)),
    list,
)
print(f"\nFizzBuzz 1–20:")
print(f"  {fizzbuzz(20)}")

# TVOJE ÚLOHA:
# 1. Napiš memoize dekorátor jako pure funkci (bez tříd).
# 2. Napiš pipeline pro čištění CSV: strip → split(',') → konverze typů.
# 3. Pomocí reduce implementuj flatten (zploštění vnořeného seznamu).
