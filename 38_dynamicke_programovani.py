"""
LEKCE 38: Dynamické programování
==================================
DP = "zapamatuj si podvýsledky, nepočítej je dvakrát"

Kdy použít:
  1. Problém má PŘEKRÝVAJÍCÍ SE podproblémy (Fibonacci, mince)
  2. Problém má OPTIMÁLNÍ SUBSTRUKTURA (optimum celku = optima částí)

Dva přístupy:
  TOP-DOWN (memoizace) – rekurze + cache, počítáš co potřebuješ
  BOTTOM-UP (tabulace) – iterace od základu nahoru, počítáš vše

Klasické DP problémy:
  Fibonacci, problém s mincemi (coin change), batoh (knapsack),
  nejdelší společná podsekvence (LCS), editační vzdálenost
"""

from functools import lru_cache
import time

# ══════════════════════════════════════════════════════════════
# FIBONACCI – motivační příklad
# ══════════════════════════════════════════════════════════════

def fib_naivni(n):
    if n < 2: return n
    return fib_naivni(n-1) + fib_naivni(n-2)   # exponenciální!

@lru_cache(maxsize=None)
def fib_memo(n):
    if n < 2: return n
    return fib_memo(n-1) + fib_memo(n-2)         # O(N) díky cache

def fib_dp(n):
    if n < 2: return n
    dp = [0] * (n+1)
    dp[1] = 1
    for i in range(2, n+1):
        dp[i] = dp[i-1] + dp[i-2]
    return dp[n]                                   # O(N) čas, O(N) paměť

def fib_optimalni(n):
    a, b = 0, 1
    for _ in range(n): a, b = b, a+b
    return a                                        # O(N) čas, O(1) paměť!

print("=== Fibonacci – srovnání přístupů ===\n")
for fn, nazev in [(fib_memo, "Memoizace"), (fib_dp, "Bottom-up DP"),
                   (fib_optimalni, "Optimální O(1)")]:
    t0 = time.perf_counter()
    vysledek = fn(35)
    ms = (time.perf_counter()-t0)*1000
    print(f"  {nazev:<20} fib(35)={vysledek}  {ms:.3f}ms")

print("\n  Naivní rekurze pro n=35 by trvala ~sekundy (2^35 volání).")


# ══════════════════════════════════════════════════════════════
# COIN CHANGE – problém s mincemi
# ══════════════════════════════════════════════════════════════

def coin_change(mince: list[int], castka: int) -> int:
    """Minimální počet mincí pro danou částku. -1 pokud nelze."""
    dp = [float("inf")] * (castka + 1)
    dp[0] = 0

    for c in range(1, castka + 1):
        for mince_hodnota in mince:
            if mince_hodnota <= c:
                dp[c] = min(dp[c], dp[c - mince_hodnota] + 1)

    return dp[castka] if dp[castka] != float("inf") else -1

def coin_change_cesta(mince, castka):
    """Vrátí také konkrétní kombinaci mincí."""
    dp      = [float("inf")] * (castka + 1)
    pouzita = [0] * (castka + 1)
    dp[0]   = 0

    for c in range(1, castka + 1):
        for m in mince:
            if m <= c and dp[c - m] + 1 < dp[c]:
                dp[c]      = dp[c - m] + 1
                pouzita[c] = m

    if dp[castka] == float("inf"):
        return -1, []

    kombinace = []
    c = castka
    while c > 0:
        kombinace.append(pouzita[c])
        c -= pouzita[c]
    return dp[castka], kombinace

print("\n=== Coin Change – problém s mincemi ===\n")
mince = [1, 5, 10, 25]   # CZK: halíř, 5h, 10h, 25h
for castka in [11, 30, 41, 99, 0]:
    pocet, kombinace = coin_change_cesta(mince, castka)
    print(f"  {castka:3d} Kč: {pocet} mincí  {sorted(kombinace, reverse=True)}")

# Proč greedy (hladový) algoritmus nefunguje vždy:
print("\n  Mince [1, 3, 4], částka 6:")
print(f"  Greedy:  4+1+1 = 3 mince  ← ŠPATNĚ")
print(f"  DP:      3+3   = {coin_change([1,3,4], 6)} mince  ← SPRÁVNĚ")


# ══════════════════════════════════════════════════════════════
# 0/1 KNAPSACK – problém batohu
# ══════════════════════════════════════════════════════════════

def knapsack(predmety: list[tuple], kapacita: int):
    """
    predmety = [(nazev, vaha, hodnota), ...]
    Vrátí max hodnotu a seznam vybraných předmětů.
    """
    n  = len(predmety)
    dp = [[0] * (kapacita + 1) for _ in range(n + 1)]

    for i in range(1, n + 1):
        _, vaha, hodnota = predmety[i-1]
        for w in range(kapacita + 1):
            dp[i][w] = dp[i-1][w]   # nevzít předmět
            if vaha <= w:
                dp[i][w] = max(dp[i][w], dp[i-1][w-vaha] + hodnota)

    # Zpětná rekonstrukce – co vzít?
    vybrane = []
    w = kapacita
    for i in range(n, 0, -1):
        if dp[i][w] != dp[i-1][w]:
            vybrane.append(predmety[i-1][0])
            w -= predmety[i-1][1]

    return dp[n][kapacita], list(reversed(vybrane))

print("\n=== 0/1 Knapsack – problém batohu ===\n")
predmety = [
    ("notebook",   3, 1500),
    ("kamera",     2,  800),
    ("knížka",     1,  200),
    ("jídlo",      2,  400),
    ("stan",       4,  600),
    ("spacák",     3,  500),
    ("lékárnička", 1,  900),
]
kapacita = 7

hodnota, vybrane = knapsack(predmety, kapacita)
print(f"  Batoh: max {kapacita} kg")
print(f"  Předměty: {[f'{n}({v}kg,{h}Kč)' for n,v,h in predmety]}")
print(f"\n  Optimální výběr: {vybrane}")
print(f"  Celková hodnota: {hodnota} Kč")
celkova_vaha = sum(v for n,v,h in predmety if n in vybrane)
print(f"  Celková váha:    {celkova_vaha} kg / {kapacita} kg")


# ══════════════════════════════════════════════════════════════
# LCS – nejdelší společná podsekvence
# ══════════════════════════════════════════════════════════════

def lcs(a: str, b: str) -> str:
    m, n = len(a), len(b)
    dp = [[""] * (n+1) for _ in range(m+1)]

    for i in range(1, m+1):
        for j in range(1, n+1):
            if a[i-1] == b[j-1]:
                dp[i][j] = dp[i-1][j-1] + a[i-1]
            else:
                dp[i][j] = max(dp[i-1][j], dp[i][j-1], key=len)

    return dp[m][n]

print("\n=== LCS – nejdelší společná podsekvence ===\n")
pary = [
    ("ABCBDAB", "BDCAB"),
    ("python",  "typhon"),
    ("algoritmus", "altruismus"),
]
for a, b in pary:
    spolecna = lcs(a, b)
    print(f"  LCS({a!r}, {b!r}) = {spolecna!r}  (délka {len(spolecna)})")


# ══════════════════════════════════════════════════════════════
# EDITAČNÍ VZDÁLENOST (Levenshtein)
# ══════════════════════════════════════════════════════════════

def edit_distance(a: str, b: str) -> tuple[int, list]:
    m, n = len(a), len(b)
    dp = [[0]*(n+1) for _ in range(m+1)]

    for i in range(m+1): dp[i][0] = i
    for j in range(n+1): dp[0][j] = j

    for i in range(1, m+1):
        for j in range(1, n+1):
            if a[i-1] == b[j-1]:
                dp[i][j] = dp[i-1][j-1]
            else:
                dp[i][j] = 1 + min(
                    dp[i-1][j],    # smazání
                    dp[i][j-1],    # vložení
                    dp[i-1][j-1],  # nahrazení
                )
    return dp[m][n]

print("\n=== Editační vzdálenost (překlepy) ===\n")
pary = [
    ("kitten",    "sitting"),
    ("python",    "pyton"),
    ("algoritmus","algritmus"),
    ("sobota",    "neděle"),
]
for a, b in pary:
    d = edit_distance(a, b)
    print(f"  {a!r:15} → {b!r:15}  vzdálenost: {d}")

print("\n  Použití: spell-check, diff, DNA sekvence, fuzzy vyhledávání")

# TVOJE ÚLOHA:
# 1. Napiš longest_increasing_subsequence(seznam) – nejdelší rostoucí podsekvenci.
# 2. Rozšiř edit_distance aby vrátila i seznam operací (smaž/vlož/nahraď X→Y).
# 3. Problém obchodního cestujícího (TSP) pro 5 měst – brute force vs. DP.
