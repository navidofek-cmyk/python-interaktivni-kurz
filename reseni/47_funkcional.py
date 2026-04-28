"""Reseni – Lekce 47: Funkcionalni programovani"""

from functools import reduce
from typing import Callable, TypeVar, Any

T = TypeVar("T")


# 1. Memoize dekorator jako pure funkce (bez trid)

print("=== Ukol 1: memoize dekorator ===\n")


def memoize(fn: Callable) -> Callable:
    """Pure-function memoize dekorator (bez trid, bez import functools)."""
    cache: dict[tuple, Any] = {}

    def wrapper(*args):
        if args not in cache:
            cache[args] = fn(*args)
        return cache[args]

    wrapper.cache = cache           # pro introspekci
    wrapper.__name__ = fn.__name__
    return wrapper


@memoize
def fib(n: int) -> int:
    if n < 2:
        return n
    return fib(n - 1) + fib(n - 2)


import time

t0 = time.perf_counter()
vysledek = fib(35)
elapsed_prvni = time.perf_counter() - t0

t0 = time.perf_counter()
vysledek2 = fib(35)
elapsed_druhy = time.perf_counter() - t0

print(f"fib(35) = {vysledek}")
print(f"  1. volani: {elapsed_prvni*1000:.3f}ms")
print(f"  2. volani (z cache): {elapsed_druhy*1000:.3f}ms")
print(f"  Velikost cache: {len(fib.cache)} zaznamu")


# 2. Pipeline pro cisteni CSV: strip → split(',') → konverze typu

print("\n=== Ukol 2: CSV pipeline ===\n")


def pipe(*fns: Callable) -> Callable:
    def piped(x: Any) -> Any:
        result = x
        for fn in fns:
            result = fn(result)
        return result
    return piped


def konvertuj_typy(hodnoty: list[str]) -> list[Any]:
    """Pokusi se prevest kazde pole na int/float, jinak necha string."""
    vysledek = []
    for h in hodnoty:
        try:
            vysledek.append(int(h))
        except ValueError:
            try:
                vysledek.append(float(h))
            except ValueError:
                vysledek.append(h)
    return vysledek


csv_pipeline = pipe(
    str.strip,                         # odstran okrajove mezery
    lambda s: s.split(","),            # rozdel dle carky
    lambda lst: [h.strip() for h in lst],  # strip kazde hodnoty
    konvertuj_typy,                    # konverze int/float/str
)

csv_radky = [
    "  Jan, 25, 87.5  ",
    "Tomas,16,92",
    "  Bara ,  14  , 78.3  ",
]

for radek in csv_radky:
    sloupce = csv_pipeline(radek)
    print(f"  {radek!r}")
    print(f"    -> {sloupce}  (typy: {[type(x).__name__ for x in sloupce]})")


# 3. Flatten (zplosteni vnoreneho seznamu) pomoci reduce

print("\n=== Ukol 3: flatten pomoci reduce ===\n")


def flatten(nested: list) -> list:
    """Zplosti libovolne hluboko vnoreny seznam pomoci reduce."""
    def rozbal(acc: list, x: Any) -> list:
        if isinstance(x, list):
            return acc + flatten(x)
        return acc + [x]
    return reduce(rozbal, nested, [])


priklady = [
    [1, 2, 3],
    [1, [2, 3], 4],
    [1, [2, [3, [4, [5]]]]],
    [[1, 2], [3, [4, 5]], 6],
    [],
]

for vnoreny in priklady:
    print(f"  {str(vnoreny):<35} -> {flatten(vnoreny)}")
