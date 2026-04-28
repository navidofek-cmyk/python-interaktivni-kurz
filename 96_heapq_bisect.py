"""
LEKCE 96: heapq a bisect – efektivní datové struktury
=======================================================
Naučíš se používat haldu (heap) a binární vyhledávání
pro efektivní prioritní fronty a práci s tříděnými daty.

heapq – min-heap v Pythonu:
  – přidání:  O(log n)
  – odebrání min: O(log n)
  – nahlédnutí na min: O(1)
  – ideální pro: priority queues, N největších/nejmenších

bisect – binární vyhledávání:
  – vyhledávání v setříděném listu: O(log n)
  – vkládání se zachováním pořadí: O(log n) hledání + O(n) vložení
  – ideální pro: udržování setříděných dat, intervalové mapování
"""

import heapq
import bisect
import time
import random
from dataclasses import dataclass, field

print("=== LEKCE 96: heapq a bisect ===\n")

# ══════════════════════════════════════════════════════════════
# ČÁST 1: heapq – základy min-heap
# ══════════════════════════════════════════════════════════════

print("── Část 1: heapq základy ──\n")

halda = []
heapq.heappush(halda, 5)
heapq.heappush(halda, 1)
heapq.heappush(halda, 8)
heapq.heappush(halda, 3)
heapq.heappush(halda, 2)

print(f"  Halda (list):   {halda}  ← halda, NE setříděný list!")
print(f"  Minimum (O(1)): {halda[0]}")

print("  Výběry ze haldy (vždy minimum):", end="")
kopia = list(halda)
while kopia:
    print(f" {heapq.heappop(kopia)}", end="")
print()
print()

# heapq.heapify – O(n) převod listu na haldu
data = [15, 3, 7, 1, 9, 4, 12, 6]
heapq.heapify(data)
print(f"  heapify({[15,3,7,1,9,4,12,6]}):")
print(f"    → {data}  (halda, halda[0]={data[0]} je min)")
print()

# nlargest / nsmallest – efektivnější než sort pro malé N
cisla = [random.randint(1, 1000) for _ in range(20)]
print(f"  Náhodných 20 čísel: {cisla}")
print(f"  5 největších:  {heapq.nlargest(5, cisla)}")
print(f"  5 nejmenších:  {heapq.nsmallest(5, cisla)}")
print()

# ══════════════════════════════════════════════════════════════
# ČÁST 2: Priority queue pro plánování úkolů
# ══════════════════════════════════════════════════════════════

print("── Část 2: Priority queue – plánování úkolů ──\n")

@dataclass(order=True)
class Ukol:
    priorita: int           # 1 = nejvyšší
    poradi: int = field(compare=True)   # tiebreaker
    nazev: str = field(compare=False)
    cas_pridani: float = field(compare=False, default_factory=time.time)

class PlannerUkolu:
    def __init__(self):
        self._halda: list = []
        self._pocitadlo = 0   # tiebreaker pro stejnou prioritu

    def pridej(self, nazev: str, priorita: int = 5):
        ukol = Ukol(priorita=priorita, poradi=self._pocitadlo, nazev=nazev)
        self._pocitadlo += 1
        heapq.heappush(self._halda, ukol)
        print(f"  [+] Přidán: {nazev!r} (priorita={priorita})")

    def dalsi(self) -> Ukol | None:
        if self._halda:
            return heapq.heappop(self._halda)
        return None

    def nahled(self) -> Ukol | None:
        return self._halda[0] if self._halda else None

    def __len__(self):
        return len(self._halda)

planner = PlannerUkolu()
planner.pridej("Napsat report", priorita=3)
planner.pridej("Odpovědět na email", priorita=2)
planner.pridej("KRITICKÁ CHYBA v produkci", priorita=1)
planner.pridej("Oběd", priorita=5)
planner.pridej("Code review", priorita=3)
planner.pridej("Deploy na staging", priorita=2)

print(f"\n  Fronta má {len(planner)} úkolů. Zpracovávám:\n")
while len(planner):
    ukol = planner.dalsi()
    print(f"  [✓] p={ukol.priorita} – {ukol.nazev}")
print()

# ══════════════════════════════════════════════════════════════
# ČÁST 3: bisect – binární vyhledávání
# ══════════════════════════════════════════════════════════════

print("── Část 3: bisect – binární vyhledávání ──\n")

setrideny = [10, 20, 30, 40, 50, 60, 70, 80]
hodnota = 45

# bisect_left  → pozice před prvním výskytem >= hodnota
# bisect_right → pozice za posledním výskytem == hodnota
pos_left  = bisect.bisect_left(setrideny, hodnota)
pos_right = bisect.bisect_right(setrideny, hodnota)

print(f"  Seznam: {setrideny}")
print(f"  Hledám: {hodnota}")
print(f"  bisect_left({hodnota})  = {pos_left}  → vložit PŘED index {pos_left}")
print(f"  bisect_right({hodnota}) = {pos_right}  → vložit ZA  index {pos_right}")
print()

# Příklad s duplicitami
dup = [10, 20, 20, 20, 30]
print(f"  S duplicitami: {dup}, hledám 20")
print(f"  bisect_left(20)  = {bisect.bisect_left(dup, 20)}  → první výskyt")
print(f"  bisect_right(20) = {bisect.bisect_right(dup, 20)}  → za posledním")
print()

# bisect.insort – vloží a zachová seřazení
setrideny2 = [1, 3, 5, 7, 9]
print(f"  Počáteční seznam: {setrideny2}")
for val in [4, 0, 6, 8]:
    bisect.insort(setrideny2, val)
    print(f"  Po insort({val}):    {setrideny2}")
print()

# ══════════════════════════════════════════════════════════════
# ČÁST 4: Praktické použití bisect – klasifikace, intervalové mapování
# ══════════════════════════════════════════════════════════════

print("── Část 4: Intervalové mapování (bisect) ──\n")

# Školní hodnocení
body_hranice = [50, 60, 70, 80, 90]     # setříděné
znamky       = ["F", "E", "D", "C", "B", "A"]

def znamka(body: int) -> str:
    index = bisect.bisect_left(body_hranice, body)
    # pokud je přesně na hranici → patří do vyšší kategorie
    index = bisect.bisect_right(body_hranice, body - 1)
    return znamky[index]

testovaci_body = [45, 50, 63, 70, 82, 90, 100]
print("  Body → Hodnocení:")
for b in testovaci_body:
    print(f"    {b:3d} bodů → {znamka(b)}")
print()

# Rychlé vyhledávání "je prvek v setříděném listu?"
def je_v_liste(setrideny_list: list, prvek) -> bool:
    """Binární hledání – O(log n) místo 'in' O(n)."""
    i = bisect.bisect_left(setrideny_list, prvek)
    return i < len(setrideny_list) and setrideny_list[i] == prvek

velky_setrideny = sorted(range(0, 1_000_000, 2))  # sudá čísla
print(f"  Seznam: 0, 2, 4, ... 999998 ({len(velky_setrideny)} prvků)")
print(f"  je_v_liste(500000) = {je_v_liste(velky_setrideny, 500000)}")
print(f"  je_v_liste(500001) = {je_v_liste(velky_setrideny, 500001)}")
print()

# ══════════════════════════════════════════════════════════════
# ČÁST 5: Výkon – bisect vs lineární hledání
# ══════════════════════════════════════════════════════════════

print("── Část 5: Srovnání výkonu bisect vs lineární hledání ──\n")

N = 100_000
data_sorted = sorted(random.sample(range(0, 10_000_000), N))
hledane = [random.randint(0, 10_000_000) for _ in range(1000)]

# Lineární hledání (in operator)
start = time.perf_counter()
for h in hledane:
    _ = h in data_sorted
cas_linear = time.perf_counter() - start

# Bisect hledání
start = time.perf_counter()
for h in hledane:
    _ = je_v_liste(data_sorted, h)
cas_bisect = time.perf_counter() - start

print(f"  Seznam: {N:,} prvků, 1 000 hledání")
print(f"  Lineární (in):  {cas_linear*1000:.2f} ms")
print(f"  Bisect (log n): {cas_bisect*1000:.2f} ms")
print(f"  Bisect je ~{cas_linear/cas_bisect:.0f}× rychlejší")
print()

# ══════════════════════════════════════════════════════════════
# ČÁST 6: Dijkstrův algoritmus s heapq
# ══════════════════════════════════════════════════════════════

print("── Část 6: Dijkstra s heapq ──\n")

def dijkstra(graf: dict, start: str) -> dict:
    """
    Nejkratší cesty z vrcholu 'start' do všech ostatních.
    graf = {vrchol: [(soused, váha), ...]}
    Vrátí {vrchol: nejkratsi_vzdalenost}
    """
    vzdalenosti = {v: float("inf") for v in graf}
    vzdalenosti[start] = 0
    # halda: (vzdalenost, vrchol)
    halda = [(0, start)]

    while halda:
        aktualni_dist, aktualni = heapq.heappop(halda)

        # Přeskočíme zastaralé záznamy
        if aktualni_dist > vzdalenosti[aktualni]:
            continue

        for soused, vaha in graf[aktualni]:
            nova_dist = aktualni_dist + vaha
            if nova_dist < vzdalenosti[soused]:
                vzdalenosti[soused] = nova_dist
                heapq.heappush(halda, (nova_dist, soused))

    return vzdalenosti

# Graf: mapa měst s vzdálenostmi (km)
mapa = {
    "Praha":    [("Brno", 210), ("Plzeň", 90), ("Liberec", 110)],
    "Brno":     [("Praha", 210), ("Ostrava", 170), ("Olomouc", 75)],
    "Plzeň":    [("Praha", 90), ("České Budějovice", 100)],
    "Liberec":  [("Praha", 110), ("Olomouc", 290)],
    "Ostrava":  [("Brno", 170), ("Olomouc", 90)],
    "Olomouc":  [("Brno", 75), ("Ostrava", 90), ("Liberec", 290)],
    "České Budějovice": [("Plzeň", 100), ("Brno", 245)],
}

vzdalenosti = dijkstra(mapa, "Praha")
print("  Nejkratší vzdálenosti z Prahy:")
for mesto, dist in sorted(vzdalenosti.items(), key=lambda x: x[1]):
    znacka = " ← start" if dist == 0 else f"{dist} km"
    print(f"    {mesto:<25} {znacka}")
print()

# ══════════════════════════════════════════════════════════════
# TVOJE ÚLOHA:
# ══════════════════════════════════════════════════════════════
print("=" * 55)
print("TVOJE ÚLOHA:")
print("=" * 55)
print("""
1. Implementuj MedianFinder třídu pomocí dvou hald:
   max-heap pro dolní polovinu čísel a min-heap pro
   horní polovinu. Metody: pridej(cislo), median().
   Median se musí vrátit v O(log n) a getMedian v O(1).
   Otestuj na sekvenci [5, 3, 8, 1, 9, 2, 7].

2. Napiš funkci `top_n_souboru(adresare: list[str], n: int)
   -> list[tuple]`, která projde zadané adresáře, najde
   N největších souborů (os.path.getsize) a vrátí je
   setříděné od největšího. Použij heapq.nlargest().

3. Implementuj funkci `interpolacni_hledani(setrideny: list,
   hledana_hodnota)` pomocí bisect, která vrátí index prvku
   nebo -1. Porovnej rychlost s bisect.bisect_left přímo
   a s lineárním hledáním na listu 1 000 000 prvků.

4. Rozšiř Dijkstrův algoritmus o rekonstrukci cesty:
   vrať nejen vzdálenosti, ale i slovník předchůdců
   {vrchol: predchudce}. Napiš funkci `cesta(predchudci,
   start, cil) -> list[str]`, která z něj sestaví cestu.
   Vypiš nejkratší cestu Praha → Ostrava.
""")
