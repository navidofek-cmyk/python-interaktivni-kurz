"""
LEKCE 87: Hypothesis – property-based testing
===============================================
pip install hypothesis

Hypothesis = místo "testuj konkrétní příklady" testuje VLASTNOSTI.
Sám generuje stovky vstupů a hledá protipříklady.

Klasický test:    assert secti(2, 3) == 5
Property test:    pro libovolná a, b: secti(a, b) == secti(b, a)

Hypothesis najde edge cases které tě nikdy nenapadnou:
  0, -1, None, "", [], float("inf"), nan, MAX_INT...
"""

import pytest
from hypothesis import given, assume, settings, example
from hypothesis import strategies as st
from hypothesis.stateful import RuleBasedStateMachine, rule, initialize

# ══════════════════════════════════════════════════════════════
# ČÁST 1: Základní strategie
# ══════════════════════════════════════════════════════════════

print("=== Hypothesis strategie ===\n")

# Ukázka co Hypothesis generuje
from hypothesis import find

print("Integers(-10, 10):", [find(st.integers(-10, 10), lambda x: True) for _ in range(5)])
print("Text(max_size=5):", [find(st.text(max_size=5), lambda x: True) for _ in range(3)])
print("Lists(integers):", find(st.lists(st.integers(), min_size=3, max_size=5), lambda x: True))

# ══════════════════════════════════════════════════════════════
# ČÁST 2: Testování funkcí
# ══════════════════════════════════════════════════════════════

print("\n=== Property testy ===\n")

# Funkce které budeme testovat
def reverz(lst: list) -> list:
    return lst[::-1]

def setrid(lst: list) -> list:
    return sorted(lst)

def soucet_seznamu(lst: list[float]) -> float:
    return sum(lst)

def binarne_hledej(seznam: list[int], cil: int) -> int:
    """Vrátí index nebo -1. (Záměrně s chybou pro demo)"""
    lo, hi = 0, len(seznam) - 1
    while lo <= hi:
        mid = (lo + hi) // 2
        if seznam[mid] == cil:
            return mid
        elif seznam[mid] < cil:
            lo = mid + 1
        else:
            hi = mid - 1
    return -1


# Property testy
@given(st.lists(st.integers()))
def test_reverz_involutorni(lst):
    """Dvojitý reverz = originál."""
    assert reverz(reverz(lst)) == lst

@given(st.lists(st.integers()))
def test_setrid_zachova_prvky(lst):
    """Třídění nemění obsah, jen pořadí."""
    assert sorted(setrid(lst)) == sorted(lst)
    assert len(setrid(lst)) == len(lst)

@given(st.lists(st.integers()))
def test_setrid_je_serazeny(lst):
    """Výsledek je skutečně seřazený."""
    result = setrid(lst)
    for i in range(len(result) - 1):
        assert result[i] <= result[i + 1]

@given(st.lists(st.floats(allow_nan=False, allow_infinity=False)))
def test_soucet_komutativni(lst):
    """Pořadí prvků neovlivní součet."""
    import random
    shuffled = list(lst)
    random.shuffle(shuffled)
    assert abs(soucet_seznamu(lst) - soucet_seznamu(shuffled)) < 1e-9

@given(
    seznam=st.lists(st.integers(), min_size=1).map(sorted),
    cil=st.integers(),
)
def test_binarni_hledani(seznam, cil):
    """Binární hledání: pokud prvek je, najde ho; pokud není, vrátí -1."""
    idx = binarne_hledej(seznam, cil)
    if cil in seznam:
        assert idx >= 0, f"Prvek {cil} je v {seznam} ale nebyl nalezen"
        assert seznam[idx] == cil
    else:
        assert idx == -1, f"Prvek {cil} není v {seznam} ale vrátil idx={idx}"


# ══════════════════════════════════════════════════════════════
# ČÁST 3: Složitější strategie
# ══════════════════════════════════════════════════════════════

print("=== Složitější strategie ===\n")

from dataclasses import dataclass
from hypothesis import given
from hypothesis.strategies import builds, composite

@dataclass
class Student:
    jmeno: str
    vek:   int
    body:  float

# Strategie pro Student
student_strategy = builds(
    Student,
    jmeno=st.text(min_size=1, max_size=50, alphabet=st.characters(
        whitelist_categories=["L"])),   # jen písmena
    vek=st.integers(min_value=10, max_value=25),
    body=st.floats(min_value=0, max_value=100, allow_nan=False),
)

@composite
def sorted_nonempty_list(draw):
    """Composite strategie: neprázdný setříděný seznam."""
    lst = draw(st.lists(st.integers(), min_size=1, max_size=20))
    return sorted(lst)

@given(student_strategy)
def test_student_validni(student):
    assert len(student.jmeno) > 0
    assert 10 <= student.vek <= 25
    assert 0 <= student.body <= 100

@given(sorted_nonempty_list())
def test_maximum_je_posledni(lst):
    assert max(lst) == lst[-1]


# ══════════════════════════════════════════════════════════════
# ČÁST 4: Stateful testing (stavový automat)
# ══════════════════════════════════════════════════════════════

print("=== Stateful testing – zásobník ===\n")

class Zasobnik:
    """Implementace zásobníku – testujeme správnost."""
    def __init__(self):
        self._data: list = []

    def push(self, item) -> None:
        self._data.append(item)

    def pop(self):
        if not self._data:
            raise IndexError("Zásobník je prázdný")
        return self._data.pop()

    def peek(self):
        if not self._data:
            raise IndexError("Zásobník je prázdný")
        return self._data[-1]

    @property
    def prazdny(self) -> bool:
        return len(self._data) == 0

    def __len__(self) -> int:
        return len(self._data)


class TestZasobnik(RuleBasedStateMachine):
    """Hypothesis testuje zásobník jako stavový automat."""

    @initialize()
    def vytvor(self):
        self.zasobnik = Zasobnik()
        self.ocekavany = []   # referenční implementace

    @rule(item=st.integers())
    def push(self, item):
        self.zasobnik.push(item)
        self.ocekavany.append(item)
        assert len(self.zasobnik) == len(self.ocekavany)

    @rule()
    def pop(self):
        assume(not self.zasobnik.prazdny)
        item = self.zasobnik.pop()
        ocekavany_item = self.ocekavany.pop()
        assert item == ocekavany_item

    @rule()
    def peek(self):
        assume(not self.zasobnik.prazdny)
        assert self.zasobnik.peek() == self.ocekavany[-1]

    @rule()
    def zkontroluj_prazdny(self):
        assert self.zasobnik.prazdny == (len(self.ocekavany) == 0)


# ══════════════════════════════════════════════════════════════
# ČÁST 5: Spuštění všech testů
# ══════════════════════════════════════════════════════════════

print("Spouštím property testy...\n")

testy = [
    ("reverz je involutorní",   test_reverz_involutorni),
    ("třídění zachová prvky",   test_setrid_zachova_prvky),
    ("třídění je seřazené",     test_setrid_je_serazeny),
    ("součet komutativní",      test_soucet_komutativni),
    ("binární hledání",         test_binarni_hledani),
    ("student validní",         test_student_validni),
    ("maximum je poslední",     test_maximum_je_posledni),
]

prosel  = 0
selhal  = 0

for nazev, test_fn in testy:
    try:
        test_fn()
        print(f"  ✓ {nazev}")
        prosel += 1
    except Exception as e:
        print(f"  ✗ {nazev}: {e}")
        selhal += 1

# Stavový test
print("\n  Stavový test zásobníku...")
try:
    TestZasobnikTest = TestZasobnik.TestCase
    TestZasobnikTest().runTest()
    print("  ✓ zásobník (stavový automat)")
    prosel += 1
except Exception as e:
    print(f"  ✗ zásobník: {e}")
    selhal += 1

print(f"\nVýsledek: {prosel} prošlo, {selhal} selhalo")

print("""
=== Hypothesis vs klasické testy ===

  Klasický:   assert soucet([1, 2, 3]) == 6
  Property:   pro každý seznam l: soucet(l) == sum(l)

  Hypothesis navíc testuje:
    → prázdné seznamy []
    → záporná čísla [-1, -maxint]
    → float("inf"), float("nan")
    → velmi dlouhé řetězce
    → Unicode edge cases
    → kombinace které tě nenapadnou

  Shrinkage: když najde chybu, zmenší vstup na nejmenší
  možný protipříklad (např. z [5, -3, 7, 0] na [-1]).
""")

# TVOJE ÚLOHA:
# 1. Napiš property test pro lekci 36 (bubble sort) – ověř všechny vlastnosti.
# 2. Otestuj funkci coin_change z lekce 38 – výsledek <= brute force řešení.
# 3. Napiš stavový test pro BankovniUcet z lekce 39.
