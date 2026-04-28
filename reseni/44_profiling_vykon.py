"""Reseni – Lekce 44: Profiling a vykon"""

import timeit
import cProfile
import pstats
import io
import sys


# 1. Porovnej rychlost dict.get() vs try/except pro chybejici klic

print("=== Ukol 1: dict.get() vs try/except pro chybejici klic ===\n")

velky_dict = {str(i): i for i in range(10_000)}
CHYBEJICI = "99999"
EXISTUJICI = "5000"
OPAK = 500_000


cas_get_chybi = timeit.timeit(
    lambda: velky_dict.get(CHYBEJICI, None),
    number=OPAK,
)
cas_try_chybi = timeit.timeit(
    stmt="""
try:
    _ = d[k]
except KeyError:
    pass
""",
    globals={"d": velky_dict, "k": CHYBEJICI},
    number=OPAK,
)
cas_get_ok = timeit.timeit(
    lambda: velky_dict.get(EXISTUJICI, None),
    number=OPAK,
)
cas_try_ok = timeit.timeit(
    stmt="""
try:
    _ = d[k]
except KeyError:
    pass
""",
    globals={"d": velky_dict, "k": EXISTUJICI},
    number=OPAK,
)

print(f"  Chybejici klic ({OPAK:,} opakovani):")
print(f"    dict.get():    {cas_get_chybi*1000:.2f} ms")
print(f"    try/except:    {cas_try_chybi*1000:.2f} ms")
print(f"    Vyhoda get():  {cas_try_chybi/cas_get_chybi:.2f}x rychlejsi")

print(f"\n  Existujici klic ({OPAK:,} opakovani):")
print(f"    dict.get():    {cas_get_ok*1000:.2f} ms")
print(f"    try/except:    {cas_try_ok*1000:.2f} ms")
print(f"  Zaver: try/except je rychlejsi kdyz klic EXISTUJE (zero overhead)")
print(f"         dict.get() je rychlejsi kdyz klic CHYBI (vyhnuti se vyjimce)")


# 2. Dekorator @timeit_dec(n) pro mereni prumerneho casu

print("\n=== Ukol 2: @timeit_dec(n) dekorator ===\n")


def timeit_dec(n: int = 100):
    """Dekorator ktery zmeri prumerny cas n volani funkce."""
    def dekorator(fn):
        import functools

        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            start = timeit.default_timer()
            for _ in range(n - 1):
                fn(*args, **kwargs)
            vysledek = fn(*args, **kwargs)
            elapsed = timeit.default_timer() - start
            prumer_us = (elapsed / n) * 1_000_000
            print(f"  [{fn.__name__}] {n} volani: "
                  f"celkem={elapsed*1000:.3f}ms  "
                  f"prumer={prumer_us:.2f}µs/volani")
            return vysledek
        return wrapper
    return dekorator


@timeit_dec(n=1000)
def spoj_join(slova: list[str]) -> str:
    return "".join(slova)


@timeit_dec(n=1000)
def spoj_plus(slova: list[str]) -> str:
    result = ""
    for s in slova:
        result += s
    return result


test_slova = ["python"] * 100
r1 = spoj_join(test_slova)
r2 = spoj_plus(test_slova)
print(f"  Vysledky shodne: {r1 == r2}")


# 3. Profiluj funkci z lekce 38 (DP) – nejpomalejsi funkce

print("\n=== Ukol 3: cProfile na DP funkce ===\n")


def fib_dp(n: int) -> int:
    """Fibonacci pomoci tabulky (DP)."""
    if n <= 1:
        return n
    dp = [0] * (n + 1)
    dp[1] = 1
    for i in range(2, n + 1):
        dp[i] = dp[i - 1] + dp[i - 2]
    return dp[n]


def mincoin_dp(hodnoty: list[int], cil: int) -> int:
    """Min pocet minci pro danou castku (DP)."""
    dp = [float("inf")] * (cil + 1)
    dp[0] = 0
    for castka in range(1, cil + 1):
        for mince in hodnoty:
            if mince <= castka:
                dp[castka] = min(dp[castka], dp[castka - mince] + 1)
    return dp[cil] if dp[cil] != float("inf") else -1


def lis(arr: list[int]) -> int:
    """Nejdelsi rostouci podposloupnost (DP O(n^2))."""
    if not arr:
        return 0
    dp = [1] * len(arr)
    for i in range(1, len(arr)):
        for j in range(i):
            if arr[j] < arr[i]:
                dp[i] = max(dp[i], dp[j] + 1)
    return max(dp)


def spust_dp_ukoly():
    fib_dp(500)
    mincoin_dp([1, 5, 10, 25], 1000)
    lis(list(range(200, 0, -1)) + list(range(100)))


pr = cProfile.Profile()
pr.enable()
spust_dp_ukoly()
pr.disable()

stream = io.StringIO()
stats = pstats.Stats(pr, stream=stream)
stats.sort_stats("cumulative")
stats.print_stats(8)

print("Top funkce podle kumulativniho casu:")
for radek in stream.getvalue().split("\n")[4:12]:
    if radek.strip():
        print(f"  {radek}")
