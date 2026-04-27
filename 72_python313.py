"""
LEKCE 72: Python 3.13 – novinky
=================================
Python 3.13 (říjen 2024) přinesl dvě experimentální novinky
které mohou změnit jak Python funguje:

JIT KOMPILÁTOR (experimental)
  Python 3.13 má vestavěný JIT (Just-In-Time) kompilátor.
  Zatím ~přibližně 5% speedup, cíl je 2–5× v budoucnu.
  Spustíš: python3.13 --enable-gil --jit script.py

FREE-THREADED MODE (experimental, PEP 703)
  Python 3.13 lze zkompilovat BEZ GIL (Global Interpreter Lock).
  GIL = zámek který zabraňuje skutečnému paralelismu threadů.
  Bez GIL → skutečný paralelismus CPU-bound kódu přes threading.
  Spustíš: python3.13t (t = free-threaded build)

Ostatní novinky:
  Lepší chybové hlášky (červené šipky na přesné místo)
  copy.replace() – kopírování s nahrazením atributů
  Vylepšený REPL (interaktivní konzole)
  locals() je nyní definované chování
  random.Random.choices() je rychlejší
"""

import sys
import platform
import time
import threading
import dis
from concurrent.futures import ThreadPoolExecutor

print(f"Python verze: {sys.version}")
print(f"Platform:     {platform.python_implementation()}")
print()

# ══════════════════════════════════════════════════════════════
# ČÁST 1: Lepší chybové hlášky (dostupné od 3.10+, vylepšeny v 3.13)
# ══════════════════════════════════════════════════════════════

print("=== Lepší chybové hlášky ===\n")

# Python 3.13 přidal přesnější ukazatele chyb
chybove_priklady = [
    # Každý z těchto vyvolá chybu – ukáže jak Python hlásí chyby
    ('x = {"klic": "hodnota")\n# SyntaxError: Python ukáže přesně na ")"',
     "SyntaxError – závorka"),
    ('result = None\nresult.upper()\n# AttributeError: Python napíše "result is None"',
     "AttributeError s nápovědou"),
    ('import colections\n# ModuleNotFoundError: "Did you mean: collections?"',
     "ImportError s nápadem"),
]

for kod, popis in chybove_priklady:
    print(f"  Příklad: {popis}")
    print(f"  {kod.splitlines()[0]}")
    print()


# ══════════════════════════════════════════════════════════════
# ČÁST 2: copy.replace() – nový protokol
# ══════════════════════════════════════════════════════════════

print("=== copy.replace() ===\n")

import copy
from dataclasses import dataclass

@dataclass
class Bod:
    x: float
    y: float
    z: float = 0.0

    # Python 3.13: podpora __replace__ protokolu
    def __replace__(self, **zmeny):
        return Bod(
            x=zmeny.get("x", self.x),
            y=zmeny.get("y", self.y),
            z=zmeny.get("z", self.z),
        )

p1 = Bod(1.0, 2.0, 3.0)

if sys.version_info >= (3, 13):
    p2 = copy.replace(p1, x=10.0)
    print(f"  copy.replace(p1, x=10): {p2}")
else:
    # Ekvivalent pro starší verze
    from dataclasses import replace
    p2 = replace(p1, x=10.0)
    print(f"  dataclasses.replace(p1, x=10): {p2}")
    print(f"  (copy.replace() dostupné od Pythonu 3.13)")

print(f"  Původní: {p1}  Nový: {p2}")


# ══════════════════════════════════════════════════════════════
# ČÁST 3: GIL a free-threaded mode
# ══════════════════════════════════════════════════════════════

print("\n=== GIL – Global Interpreter Lock ===\n")

print("  GIL = mutex který chrání CPython interní struktury.")
print("  Důsledek: v jednom okamžiku běží vždy jen jeden Python thread.")
print("  Threading tedy NEPOMÁHÁ pro CPU-bound operace.\n")

# Demo: GIL v praxi
def cpu_bound(n: int) -> int:
    return sum(i * i for i in range(n))

N = 2_000_000

# Sekvenční
t0 = time.perf_counter()
cpu_bound(N)
cpu_bound(N)
t_seq = time.perf_counter() - t0

# Threading (stále blokovaný GILem pro CPU-bound)
t0 = time.perf_counter()
with ThreadPoolExecutor(max_workers=2) as ex:
    f1 = ex.submit(cpu_bound, N)
    f2 = ex.submit(cpu_bound, N)
    f1.result(); f2.result()
t_thread = time.perf_counter() - t0

print(f"  CPU-bound N={N:_} (2× sekvenčně vs. 2 thready):")
print(f"  Sekvenční: {t_seq:.3f}s")
print(f"  Threading: {t_thread:.3f}s")
print(f"  → threading {'byl rychlejší' if t_thread < t_seq * 0.9 else 'NEPOMOHL (GIL)'}\n")

# Zjisti jestli běžíme na free-threaded buildu
gil_aktivni = getattr(sys, "_is_gil_enabled", lambda: True)()
print(f"  GIL aktivní: {gil_aktivni}")
if not gil_aktivni:
    print("  🎉 Běžíš na free-threaded Pythonu 3.13t!")
    print("  Threading nyní pomáhá i pro CPU-bound operace.")
else:
    print("  Pro skutečný paralelismus použij multiprocessing nebo 3.13t build.")


# ══════════════════════════════════════════════════════════════
# ČÁST 4: Vylepšený REPL a locals()
# ══════════════════════════════════════════════════════════════

print("\n=== Vylepšený REPL (3.13) ===\n")
print("  Nový REPL v Pythonu 3.13 přidal:")
print("  - Víceřádkový vstup (šipka nahoru obnoví celý blok)")
print("  - Barevný výstup a syntax highlighting")
print("  - Zobrazení chyb s červenými šipkami")
print("  - Vychozí exit() bez nutnosti importu")
print()
print("  Spusť: python3.13")
print("  (vyžaduje Python 3.13+)\n")

# locals() – nové definované chování
print("=== locals() – definované chování (3.13) ===\n")
print("  Před 3.13: modifikace locals() slovníku neměla garantovaný efekt.")
print("  Od 3.13: locals() vrací vždy aktuální snapshot lokálních proměnných.\n")

x = 42
lokalni = locals()
print(f"  locals()['x'] = {lokalni.get('x')}")


# ══════════════════════════════════════════════════════════════
# ČÁST 5: Roadmapa – co přijde v budoucnu
# ══════════════════════════════════════════════════════════════

print("""
=== Python roadmapa ===

  3.13 (říjen 2024)
    ✓ Experimentální JIT kompilátor
    ✓ Free-threaded mode (bez GIL) – experimentální
    ✓ Lepší REPL
    ✓ copy.replace()

  3.14 (říjen 2025, plánováno)
    → Vylepšený JIT (větší speedup)
    → T-string literals (template strings jako f-strings)
    → Lepší diagnostiky

  Vzdálenější budoucnost
    → JIT zralý pro produkci (2–5× speedup)
    → Free-threaded jako výchozí
    → Potenciální odstranění GIL

  Aktuální rychlost vývoje:
    Python 3.11 byl ~25% rychlejší než 3.10
    Python 3.12 byl ~5% rychlejší než 3.11
    Python 3.13 JIT: ~5% zatím, cíl je výrazně více
""")

# TVOJE ÚLOHA:
# 1. Nainstaluj Python 3.13 a porovnej rychlost faktoriálu s 3.11.
# 2. Zkus python3.13t (free-threaded build) a porovnej threading vs multiprocessing.
# 3. Spusť python3.13 --jit a změř speedup na CPU-bound smyčce.
