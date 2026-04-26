"""
LEKCE 27: Generátory a iterátory
==================================
Generátor = funkce, která vrací hodnoty postupně (lazy), ne všechny najednou.
Klíčové slovo: yield

Proč?
  - Šetří paměť: range(1_000_000_000) nezabere 8 GB RAM
  - Umožňuje nekonečné sekvence
  - Zpracování dat za pochodu (pipeline)

Iterator protocol:
  Objekt je iterovatelný, pokud má __iter__() a __next__().
  for x in obj:  Python volá iter(obj) pak opakovaně next(obj).
"""

import itertools
import sys

# ══════════════════════════════════════════════════════════════
# ČÁST 1: GENERÁTORY
# ══════════════════════════════════════════════════════════════

# ── yield vs. return ─────────────────────────────────────────

def normalni_seznam(n):
    vysledek = []
    for i in range(n):
        vysledek.append(i * i)
    return vysledek          # vrátí CELÝ seznam najednou

def generator_ctvercu(n):
    for i in range(n):
        yield i * i          # vrátí jednu hodnotu, pak se POZASTAVÍ

print("=== yield vs. return ===")
print(type(normalni_seznam(5)))       # <class 'list'>
print(type(generator_ctvercu(5)))    # <class 'generator'>

print("\nHodnoty z generátoru:")
for x in generator_ctvercu(6):
    print(x, end="  ")

# Paměťový rozdíl
velke_n = 10_000_000
seznam_bytes = sys.getsizeof(list(range(velke_n)))
gen_bytes    = sys.getsizeof(range(velke_n))
print(f"\n\nlist(range({velke_n:_})): {seznam_bytes:_} B")
print(f"range({velke_n:_}):       {gen_bytes} B  ← generátor!")

# ── Nekonečný generátor ───────────────────────────────────────

def fibonacci():
    a, b = 0, 1
    while True:             # nekonečná smyčka – generátor ji zvládne
        yield a
        a, b = b, a + b

print("\n=== Nekonečný Fibonacci ===")
fib = fibonacci()
prvnich_10 = [next(fib) for _ in range(10)]
print(prvnich_10)

# Vezmi první Fibonacciho čísla větší než 1000
fib2 = fibonacci()
print(next(x for x in fib2 if x > 1000))

# ── Generator expression (jako list comprehension, ale líná) ──

velky_gen = (x**2 for x in range(1_000_000_000))   # 0 paměti navíc!
print(f"\nPrvní 5 z miliardového generátoru: "
      f"{[next(velky_gen) for _ in range(5)]}")

# ── yield from – delegace na podgenerátor ─────────────────────

def plosne_spoj(*iterovatelne):
    for it in iterovatelne:
        yield from it        # deleguje yield na vnořený iterátor

print("\n=== yield from ===")
print(list(plosne_spoj([1, 2], "abc", range(3, 6))))

# ── Generátor jako pipeline ────────────────────────────────────

def nacti_radky(text):
    for radek in text.splitlines():
        yield radek

def filtruj_prazdne(radky):
    for r in radky:
        if r.strip():
            yield r

def upper_pipe(radky):
    for r in radky:
        yield r.upper()

data = """
  ahoj světe

  python je skvělý

  generátory jsou cool
"""

print("\n=== Generátorový pipeline ===")
pipeline = upper_pipe(filtruj_prazdne(nacti_radky(data)))
for radek in pipeline:
    print(" ", radek)


# ══════════════════════════════════════════════════════════════
# ČÁST 2: VLASTNÍ ITERÁTOR (třída)
# ══════════════════════════════════════════════════════════════

class Rozsah:
    """Vlastní obdoba range() – jen pro pochopení protokolu."""
    def __init__(self, start, stop, krok=1):
        self.aktualni = start
        self.stop     = stop
        self.krok     = krok

    def __iter__(self):
        return self    # iterátor jsme my sami

    def __next__(self):
        if self.aktualni >= self.stop:
            raise StopIteration   # signál: konec iterace
        hodnota       = self.aktualni
        self.aktualni += self.krok
        return hodnota

print("\n=== Vlastní iterátor ===")
for x in Rozsah(0, 10, 2):
    print(x, end="  ")
print()

# ══════════════════════════════════════════════════════════════
# ČÁST 3: itertools – baterie jsou přiloženy
# ══════════════════════════════════════════════════════════════

print("\n=== itertools ===")

# count – nekonečné čítání
print("count od 5 po 0.5:", list(itertools.islice(itertools.count(5, 0.5), 6)))

# cycle – opakování dookola
barvy = itertools.cycle(["červená", "zelená", "modrá"])
print("cycle:", [next(barvy) for _ in range(7)])

# chain – spojení iterátorů
print("chain:", list(itertools.chain([1, 2], "ab", range(3))))

# combinations a permutations
karty = ["A", "K", "Q"]
print("combinations(2):", list(itertools.combinations(karty, 2)))
print("permutations(2):", list(itertools.permutations(karty, 2)))

# groupby – seskupení
data2 = [("ovoce","jablko"), ("zelenina","mrkev"),
          ("ovoce","hruška"), ("zelenina","hrách")]
data2.sort(key=lambda x: x[0])   # groupby vyžaduje setříděný vstup
for kategorie, skupina in itertools.groupby(data2, key=lambda x: x[0]):
    print(f"  {kategorie}: {[s[1] for s in skupina]}")

# TVOJE ÚLOHA:
# 1. Napište generátor prvocisla() který donekonečna yield-uje prvočísla.
# 2. Napište generátor pohyb_hada(sirka, vyska) pro spirálový pohyb.
# 3. Pomocí itertools.product vygenerujte všechny kombinace hodů 2 kostkami.
