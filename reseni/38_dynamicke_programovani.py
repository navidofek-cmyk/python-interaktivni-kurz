"""Řešení – Lekce 38: Dynamické programování"""

from functools import lru_cache
import itertools
import time


# 1. Nejdelší rostoucí podsekvence (LIS – Longest Increasing Subsequence)
# dp[i] = délka nejdelší rostoucí podsekvence končící na indexu i
# Složitost: O(N²) – existuje i O(N log N) s patience sortem

def longest_increasing_subsequence(seznam: list) -> tuple[int, list]:
    """
    Vrátí (délka LIS, samotná podsekvence).
    DP přístup: pro každý prvek najdi nejdelší LIS končící před ním.
    """
    n = len(seznam)
    if n == 0:
        return 0, []

    dp = [1] * n          # dp[i] = délka LIS končící na i
    predchudce = [-1] * n  # pro rekonstrukci cesty

    for i in range(1, n):
        for j in range(i):
            if seznam[j] < seznam[i] and dp[j] + 1 > dp[i]:
                dp[i] = dp[j] + 1
                predchudce[i] = j

    # Najdi konec nejdelší LIS
    max_delka = max(dp)
    konec = dp.index(max_delka)

    # Rekonstrukce
    lis = []
    idx = konec
    while idx != -1:
        lis.append(seznam[idx])
        idx = predchudce[idx]
    lis.reverse()

    return max_delka, lis


print("=== 1. Nejdelší rostoucí podsekvence (LIS) ===\n")
testy = [
    [10, 9, 2, 5, 3, 7, 101, 18],
    [0, 1, 0, 3, 2, 3],
    [7, 7, 7, 7, 7],
    [1, 3, 6, 7, 9, 4, 10, 5, 6],
    [3, 1, 4, 1, 5, 9, 2, 6],
]
for s in testy:
    delka, lis = longest_increasing_subsequence(s)
    print(f"  {str(s):<35} → délka {delka}: {lis}")


# 2. Edit distance s operacemi
# Rekonstruujeme operace zpětným průchodem DP tabulky
# Každá buňka dp[i][j] říká: kolik operací stojí přeměna a[:i] na b[:j]

def edit_distance_s_operacemi(a: str, b: str) -> tuple[int, list[str]]:
    """
    Vrátí (editační vzdálenost, seznam operací).
    Operace: 'ponechat X', 'nahradit X→Y', 'smazat X', 'vložit Y'
    """
    m, n = len(a), len(b)
    dp = [[0] * (n + 1) for _ in range(m + 1)]

    for i in range(m + 1): dp[i][0] = i
    for j in range(n + 1): dp[0][j] = j

    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if a[i-1] == b[j-1]:
                dp[i][j] = dp[i-1][j-1]
            else:
                dp[i][j] = 1 + min(dp[i-1][j], dp[i][j-1], dp[i-1][j-1])

    # Zpětná rekonstrukce operací
    operace = []
    i, j = m, n
    while i > 0 or j > 0:
        if i > 0 and j > 0 and a[i-1] == b[j-1]:
            operace.append(f"ponechat '{a[i-1]}'")
            i -= 1; j -= 1
        elif i > 0 and j > 0 and dp[i][j] == dp[i-1][j-1] + 1:
            operace.append(f"nahradit '{a[i-1]}'→'{b[j-1]}'")
            i -= 1; j -= 1
        elif i > 0 and dp[i][j] == dp[i-1][j] + 1:
            operace.append(f"smazat '{a[i-1]}'")
            i -= 1
        else:
            operace.append(f"vložit '{b[j-1]}'")
            j -= 1

    operace.reverse()
    vzdalenost = dp[m][n]
    # Zobrazíme jen změny (ne "ponechat")
    zmeny = [op for op in operace if not op.startswith("ponechat")]
    return vzdalenost, zmeny


print("\n=== 2. Edit distance s operacemi ===\n")
pary = [
    ("kitten", "sitting"),
    ("python", "pyton"),
    ("ahoj",   "ahoj"),
    ("abc",    "xyz"),
]
for a, b in pary:
    d, ops = edit_distance_s_operacemi(a, b)
    print(f"  {a!r:12} → {b!r:12}  vzdálenost: {d}")
    if ops:
        for op in ops:
            print(f"    {op}")


# 3. TSP (Travelling Salesman Problem) pro 5 měst
# Brute force: zkusíme všechny permutace (5! = 120 cest)
# DP (Held-Karp): O(N² × 2^N) – pro 5 měst: 5² × 32 = 800 operací vs. 120
# Pro malé N je brute force srozumitelnější

MESTA = ["Praha", "Brno", "Olomouc", "Ostrava", "Plzeň"]
VZDALENOSTI = {
    ("Praha",   "Brno"):     210,
    ("Praha",   "Olomouc"):  280,
    ("Praha",   "Ostrava"):  360,
    ("Praha",   "Plzeň"):     90,
    ("Brno",    "Olomouc"):   75,
    ("Brno",    "Ostrava"):  170,
    ("Brno",    "Plzeň"):    310,
    ("Olomouc", "Ostrava"):   90,
    ("Olomouc", "Plzeň"):    350,
    ("Ostrava", "Plzeň"):    440,
}

def vzdal(a, b):
    return VZDALENOSTI.get((a, b)) or VZDALENOSTI.get((b, a)) or 9999


def tsp_brute_force(mesta: list, start: str) -> tuple[int, list]:
    """Zkusí všechny permutace a vrátí nejkratší okruh."""
    ostatni = [m for m in mesta if m != start]
    nejlepsi_cena = float("inf")
    nejlepsi_trasa = []

    for perm in itertools.permutations(ostatni):
        trasa = [start] + list(perm) + [start]
        cena = sum(vzdal(trasa[i], trasa[i+1]) for i in range(len(trasa)-1))
        if cena < nejlepsi_cena:
            nejlepsi_cena = cena
            nejlepsi_trasa = trasa

    return nejlepsi_cena, nejlepsi_trasa


def tsp_dp(mesta: list, start_idx: int = 0) -> tuple[int, list]:
    """
    Held-Karp DP algoritmus pro TSP.
    dp[maska][i] = min cena dosažení uzlu i s navštívenými uzly v masce.
    """
    n = len(mesta)
    INF = float("inf")
    # dp[mask][i] = min cena trasy z start do i přes uzly v masce
    dp = [[INF] * n for _ in range(1 << n)]
    parent = [[-1] * n for _ in range(1 << n)]

    dp[1 << start_idx][start_idx] = 0

    for mask in range(1 << n):
        for u in range(n):
            if dp[mask][u] == INF:
                continue
            if not (mask >> u & 1):
                continue
            for v in range(n):
                if mask >> v & 1:
                    continue
                nova_maska = mask | (1 << v)
                nova_cena = dp[mask][u] + vzdal(mesta[u], mesta[v])
                if nova_cena < dp[nova_maska][v]:
                    dp[nova_maska][v] = nova_cena
                    parent[nova_maska][v] = u

    # Uzavřeme okruh (návrat do start)
    plna_maska = (1 << n) - 1
    min_cena = INF
    posledni = -1
    for u in range(n):
        if u == start_idx:
            continue
        cena = dp[plna_maska][u] + vzdal(mesta[u], mesta[start_idx])
        if cena < min_cena:
            min_cena = cena
            posledni = u

    # Rekonstrukce cesty
    trasa_idx = [start_idx]
    mask = plna_maska
    aktualni = posledni
    while aktualni != start_idx:
        trasa_idx.append(aktualni)
        predchozi = parent[mask][aktualni]
        mask ^= (1 << aktualni)
        aktualni = predchozi
    trasa_idx.reverse()
    trasa_idx.append(start_idx)
    trasa = [mesta[i] for i in trasa_idx]

    return min_cena, trasa


print("\n=== 3. TSP – 5 měst ===\n")
print(f"  Města: {MESTA}\n")

t0 = time.perf_counter()
bf_cena, bf_trasa = tsp_brute_force(MESTA, "Praha")
bf_cas = (time.perf_counter() - t0) * 1000

t0 = time.perf_counter()
dp_cena, dp_trasa = tsp_dp(MESTA, 0)
dp_cas = (time.perf_counter() - t0) * 1000

print(f"  Brute force:  {bf_cena} km  {' → '.join(bf_trasa)}  ({bf_cas:.2f}ms)")
print(f"  DP (Held-Karp): {dp_cena} km  {' → '.join(dp_trasa)}  ({dp_cas:.2f}ms)")
print(f"\n  Shoda výsledků: {bf_cena == dp_cena}")
print(f"  (Pro N=5: {len(list(itertools.permutations(MESTA[1:])))} permutací vs. {5**2 * 2**5} DP stavů)")
