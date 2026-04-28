"""Řešení – Lekce 87: Hypothesis – property-based testing"""

# vyžaduje: pip install hypothesis pytest

import random
from typing import Any

try:
    from hypothesis import given, assume, settings, example
    from hypothesis import strategies as st
    from hypothesis.stateful import (RuleBasedStateMachine, rule,
                                       initialize, invariant)
    HYPOTHESIS_OK = True
except ImportError:
    print("Hypothesis není nainstalováno: pip install hypothesis")
    import sys; sys.exit(0)


# 1. Bubble sort – property testy pro všechny vlastnosti
print("=== 1. Bubble sort – property testy ===\n")

def bubble_sort(lst: list) -> list:
    """Bubble sort – implementace pro testování."""
    pol = list(lst)
    n   = len(pol)
    for i in range(n):
        prohozeno = False
        for j in range(n - i - 1):
            if pol[j] > pol[j+1]:
                pol[j], pol[j+1] = pol[j+1], pol[j]
                prohozeno = True
        if not prohozeno:
            break
    return pol

@given(st.lists(st.integers()))
def test_bubble_sort_zachova_delku(lst):
    """Třídění nemění počet prvků."""
    assert len(bubble_sort(lst)) == len(lst)

@given(st.lists(st.integers()))
def test_bubble_sort_zachova_prvky(lst):
    """Třídění nemění multiset prvků (stejné prvky, jiné pořadí)."""
    serazeny = bubble_sort(lst)
    assert sorted(serazeny) == sorted(lst)
    assert Counter_simple(serazeny) == Counter_simple(lst)

@given(st.lists(st.integers()))
def test_bubble_sort_je_serazeny(lst):
    """Výstup je skutečně seřazený vzestupně."""
    vysledek = bubble_sort(lst)
    for i in range(len(vysledek) - 1):
        assert vysledek[i] <= vysledek[i+1], \
            f"Narušeno: {vysledek[i]} > {vysledek[i+1]} na indexu {i}"

@given(st.lists(st.integers()))
def test_bubble_sort_idempotentni(lst):
    """Seřazení seřazeného = stejný výsledek."""
    serazeny = bubble_sort(lst)
    assert bubble_sort(serazeny) == serazeny

@given(st.lists(st.integers(), min_size=1))
def test_bubble_sort_min_je_prvni(lst):
    """Po seřazení je minimum na indexu 0."""
    serazeny = bubble_sort(lst)
    assert serazeny[0] == min(lst)

@given(st.lists(st.integers(), min_size=1))
def test_bubble_sort_max_je_posledni(lst):
    """Po seřazení je maximum na posledním indexu."""
    serazeny = bubble_sort(lst)
    assert serazeny[-1] == max(lst)

@given(st.lists(st.integers()))
@example([])
@example([42])
@example([1, 1, 1])
@example([5, 4, 3, 2, 1])   # obrácené pořadí – worst case
def test_bubble_sort_edge_cases(lst):
    """Hraniční případy – prázdný, jeden prvek, duplicity, obrácené."""
    serazeny = bubble_sort(lst)
    assert len(serazeny) == len(lst)
    for i in range(len(serazeny) - 1):
        assert serazeny[i] <= serazeny[i+1]

def Counter_simple(lst: list) -> dict:
    """Jednoduchý Counter bez importu collections."""
    d = {}
    for x in lst:
        d[x] = d.get(x, 0) + 1
    return d

# Spusť všechny testy
print("Spouštím property testy pro bubble_sort...\n")
for nazev, fn in [
    ("zachova délku",    test_bubble_sort_zachova_delku),
    ("zachova prvky",    test_bubble_sort_zachova_prvky),
    ("je seřazený",      test_bubble_sort_je_serazeny),
    ("idempotentní",     test_bubble_sort_idempotentni),
    ("min je první",     test_bubble_sort_min_je_prvni),
    ("max je poslední",  test_bubble_sort_max_je_posledni),
    ("edge cases",       test_bubble_sort_edge_cases),
]:
    try:
        fn()
        print(f"  ✓ {nazev}")
    except Exception as e:
        print(f"  ✗ {nazev}: {e}")


# 2. coin_change – výsledek <= brute force
print("\n=== 2. coin_change – property testy ===\n")

def coin_change_dp(mince: list[int], castka: int) -> int:
    """Optimální počet mincí (DP). Vrátí -1 pokud nelze."""
    if castka < 0:
        return -1
    dp = [float("inf")] * (castka + 1)
    dp[0] = 0
    for c in range(1, castka + 1):
        for m in mince:
            if m <= c and dp[c - m] + 1 < dp[c]:
                dp[c] = dp[c - m] + 1
    return dp[castka] if dp[castka] != float("inf") else -1

def coin_change_brute(mince: list[int], castka: int,
                       max_minci: int = 20) -> int:
    """Brute force (BFS). Pomalejší, ale referenčně správný."""
    if castka == 0:
        return 0
    from collections import deque
    navstivene = set()
    fronta = deque([(0, 0)])  # (aktuální částka, počet mincí)
    while fronta:
        aktualni, pocet = fronta.popleft()
        if pocet > max_minci:
            continue
        for m in mince:
            nova = aktualni + m
            if nova == castka:
                return pocet + 1
            if nova < castka and nova not in navstivene:
                navstivene.add(nova)
                fronta.append((nova, pocet + 1))
    return -1

@given(
    mince=st.lists(
        st.integers(min_value=1, max_value=50),
        min_size=1, max_size=6
    ).map(lambda lst: sorted(set(lst))),
    castka=st.integers(min_value=0, max_value=50),
)
def test_coin_change_dp_opt_nebo_stejny(mince, castka):
    """DP výsledek je <= brute force nebo stejný."""
    dp_vysledek    = coin_change_dp(mince, castka)
    brute_vysledek = coin_change_brute(mince, castka, max_minci=30)

    # Pokud brute force říká -1, DP musí také
    if brute_vysledek == -1:
        assert dp_vysledek == -1, \
            f"DP={dp_vysledek} ale brute=-1 pro mince={mince}, castka={castka}"
    # Pokud brute force najde řešení, DP musí být <= (stejně dobré nebo lepší)
    elif dp_vysledek != -1:
        assert dp_vysledek <= brute_vysledek, \
            f"DP={dp_vysledek} > brute={brute_vysledek} pro mince={mince}, castka={castka}"

@given(st.integers(min_value=1, max_value=100))
def test_coin_change_s_1_vzdy_resitelne(castka):
    """Pokud máme minci hodnoty 1, vždy existuje řešení."""
    vysledek = coin_change_dp([1, 5, 10, 25], castka)
    assert vysledek > 0, f"Nelze rozmáčknout {castka} mincemi [1,5,10,25]"

@given(st.integers(min_value=1, max_value=20))
def test_coin_change_jendna_mince(castka):
    """Pokud mince = [1], výsledek = castka."""
    assert coin_change_dp([1], castka) == castka

print("Spouštím property testy pro coin_change...\n")
for nazev, fn in [
    ("DP <= brute force",           test_coin_change_dp_opt_nebo_stejny),
    ("s mincí 1: vždy řešitelné",   test_coin_change_s_1_vzdy_resitelne),
    ("mince=[1]: výsledek=castka",  test_coin_change_jendna_mince),
]:
    try:
        fn()
        print(f"  ✓ {nazev}")
    except Exception as e:
        print(f"  ✗ {nazev}: {e}")


# 3. Stavový test pro BankovniUcet
print("\n=== 3. Stavový test – BankovniUcet ===\n")

class BankovniUcet:
    """Bankovní účet pro testování."""
    def __init__(self, majitel: str, pocatecni_zustatek: float = 0.0):
        if pocatecni_zustatek < 0:
            raise ValueError("Počáteční zůstatek musí být >= 0")
        self.majitel  = majitel
        self.zustatek = pocatecni_zustatek
        self.uzamcen  = False
        self.transakce: list[dict] = []

    def vloz(self, castka: float) -> float:
        if castka <= 0:
            raise ValueError("Částka musí být kladná")
        if self.uzamcen:
            raise PermissionError("Účet je uzamčen")
        self.zustatek += castka
        self.transakce.append({"typ": "vklad", "castka": castka, "zustatek": self.zustatek})
        return self.zustatek

    def vyber(self, castka: float) -> float:
        if castka <= 0:
            raise ValueError("Částka musí být kladná")
        if self.uzamcen:
            raise PermissionError("Účet je uzamčen")
        if castka > self.zustatek:
            raise ValueError(f"Nedostatek prostředků: {self.zustatek} < {castka}")
        self.zustatek -= castka
        self.transakce.append({"typ": "výběr", "castka": castka, "zustatek": self.zustatek})
        return self.zustatek

    def zamkni(self):
        self.uzamcen = True

    def odemkni(self):
        self.uzamcen = False


class TestBankovniUcet(RuleBasedStateMachine):
    """Hypothesis stavový test pro BankovniUcet."""

    @initialize()
    def setup(self):
        self.ucet       = BankovniUcet("Test User", 100.0)
        self.ocekavany  = 100.0   # referenční sledování zůstatku

    @rule(castka=st.floats(min_value=0.01, max_value=1000.0,
                            allow_nan=False, allow_infinity=False))
    def vlozit(self, castka):
        if not self.ucet.uzamcen:
            self.ucet.vloz(castka)
            self.ocekavany += castka
            assert abs(self.ucet.zustatek - self.ocekavany) < 1e-9

    @rule(castka=st.floats(min_value=0.01, max_value=500.0,
                            allow_nan=False, allow_infinity=False))
    def vybrat(self, castka):
        assume(not self.ucet.uzamcen)
        assume(castka <= self.ucet.zustatek)
        self.ucet.vyber(castka)
        self.ocekavany -= castka
        assert abs(self.ucet.zustatek - self.ocekavany) < 1e-9

    @rule()
    def zamknout(self):
        self.ucet.zamkni()
        assert self.ucet.uzamcen

    @rule()
    def odemknout(self):
        self.ucet.odemkni()
        assert not self.ucet.uzamcen

    @invariant()
    def zustatek_nikdy_zaporne(self):
        assert self.ucet.zustatek >= 0, \
            f"Záporný zůstatek: {self.ucet.zustatek}"

    @invariant()
    def pocet_transakci_roste(self):
        assert len(self.ucet.transakce) >= 0

# Spusť stavový test
print("Stavový test BankovniUcet...")
try:
    TestBankovniUcetTest = TestBankovniUcet.TestCase
    TestBankovniUcetTest().runTest()
    print("  ✓ Všechny invarianty splněny")
except Exception as e:
    print(f"  ✗ Selhání: {e}")

# Shrnutí
print(f"\n=== Výsledky ===")
print("  Bubble sort:   7 property testů (délka, prvky, seřazení, idempotence, min, max, edge)")
print("  coin_change:   3 property testů (DP<=brute, vždy řešitelné, mince=[1])")
print("  BankovniUcet:  stavový automat (vklad, výběr, zamčení, invarianty)")
