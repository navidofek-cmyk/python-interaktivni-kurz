"""Řešení – Lekce 96: heapq a bisect – efektivní datové struktury

Toto je vzorové řešení úloh z lekce 96.
"""

import heapq
import bisect
import os
import time
import random

# ── Úloha 1 ────────────────────────────────────────────────
# MedianFinder pomocí dvou hald: max-heap pro dolní polovinu
# a min-heap pro horní polovinu. median() v O(1).

class MedianFinder:
    """
    Udržuje running median pomocí dvou hald:
      dolni  – max-heap (negovaná čísla) pro menší polovinu
      horni  – min-heap pro větší polovinu
    Invariant: len(horni) == len(dolni) nebo len(horni) == len(dolni)+1
    """

    def __init__(self):
        self.dolni: list = []   # max-heap (uloženo negovaně)
        self.horni: list = []   # min-heap

    def pridej(self, cislo: float):
        # Vložíme do horní haldy
        heapq.heappush(self.horni, cislo)
        # Přesuň minimum horní do dolní (zajistí správné rozdělení)
        heapq.heappush(self.dolni, -heapq.heappop(self.horni))
        # Vyrovnání: horní může mít nejvýše o 1 prvek méně než dolní
        if len(self.dolni) > len(self.horni):
            heapq.heappush(self.horni, -heapq.heappop(self.dolni))

    def median(self) -> float:
        if len(self.horni) > len(self.dolni):
            return float(self.horni[0])
        return (self.horni[0] + (-self.dolni[0])) / 2.0


print("Úloha 1 – MedianFinder:")
mf = MedianFinder()
posloupnost = [5, 3, 8, 1, 9, 2, 7]
for cislo in posloupnost:
    mf.pridej(cislo)
    print(f"  pridej({cislo})  → median = {mf.median()}")
print()


# ── Úloha 2 ────────────────────────────────────────────────
# top_n_souboru(adresare, n) – N největších souborů přes heapq.nlargest().

def top_n_souboru(adresare: list[str], n: int) -> list[tuple[int, str]]:
    """
    Vrátí n největších souborů jako seznam (velikost_bajtu, cesta),
    seřazených od největšího.
    """
    vsechny = []
    for adresar in adresare:
        try:
            for jmeno in os.listdir(adresar):
                cesta = os.path.join(adresar, jmeno)
                if os.path.isfile(cesta):
                    try:
                        vsechny.append((os.path.getsize(cesta), cesta))
                    except OSError:
                        pass
        except OSError:
            pass
    return heapq.nlargest(n, vsechny, key=lambda x: x[0])


print("Úloha 2 – top_n_souboru():")
top = top_n_souboru(["/usr/lib/python3", "/tmp"], n=5)
if top:
    for velikost, cesta in top:
        print(f"  {velikost:>12,} B  {cesta}")
else:
    # Fallback – prohledáme aktuální adresář
    import sys
    adresar = os.path.dirname(os.path.abspath(__file__))
    top = top_n_souboru([adresar], n=5)
    for velikost, cesta in top:
        print(f"  {velikost:>12,} B  {os.path.basename(cesta)}")
print()


# ── Úloha 3 ────────────────────────────────────────────────
# interpolacni_hledani pomocí bisect + porovnání výkonu.

def interpolacni_hledani(setrideny: list, hledana_hodnota) -> int:
    """
    Vyhledá hledana_hodnota v setříděném listu.
    Vrátí index nebo -1.
    Využívá bisect_left pro O(log n) nalezení pozice.
    """
    i = bisect.bisect_left(setrideny, hledana_hodnota)
    if i < len(setrideny) and setrideny[i] == hledana_hodnota:
        return i
    return -1


# Test správnosti
setrideny = list(range(0, 1_000_000, 2))  # sudá čísla
assert interpolacni_hledani(setrideny, 500000) == 250000
assert interpolacni_hledani(setrideny, 500001) == -1

# Výkonové srovnání na 1 000 náhodných hledání
hledane = [random.randint(0, 1_000_000) for _ in range(1000)]

start = time.perf_counter()
for h in hledane:
    interpolacni_hledani(setrideny, h)
cas_bisect = (time.perf_counter() - start) * 1000

start = time.perf_counter()
for h in hledane:
    _ = h in setrideny
cas_linear = (time.perf_counter() - start) * 1000

start = time.perf_counter()
for h in hledane:
    bisect.bisect_left(setrideny, h)
cas_bisect_raw = (time.perf_counter() - start) * 1000

print("Úloha 3 – interpolacni_hledani():")
print(f"  Seznam: {len(setrideny):,} prvků, 1 000 hledání")
print(f"  Lineární (in):        {cas_linear:.2f} ms")
print(f"  bisect_left (raw):    {cas_bisect_raw:.2f} ms")
print(f"  interpolacni_hledani: {cas_bisect:.2f} ms")
print()


# ── Úloha 4 ────────────────────────────────────────────────
# Dijkstrův algoritmus s rekonstrukcí cesty.

def dijkstra_s_cestou(graf: dict, start: str) -> tuple[dict, dict]:
    """
    Vrátí (vzdalenosti, predchudci).
    predchudci[vrchol] = vrchol, ze kterého jsme přišli.
    """
    vzdalenosti = {v: float("inf") for v in graf}
    predchudci: dict[str, str | None] = {v: None for v in graf}
    vzdalenosti[start] = 0
    halda = [(0, start)]

    while halda:
        aktualni_dist, aktualni = heapq.heappop(halda)
        if aktualni_dist > vzdalenosti[aktualni]:
            continue
        for soused, vaha in graf[aktualni]:
            nova_dist = aktualni_dist + vaha
            if nova_dist < vzdalenosti[soused]:
                vzdalenosti[soused] = nova_dist
                predchudci[soused] = aktualni
                heapq.heappush(halda, (nova_dist, soused))

    return vzdalenosti, predchudci


def cesta(predchudci: dict, start: str, cil: str) -> list[str]:
    """Sestaví cestu od start do cil ze slovníku předchůdců."""
    if predchudci.get(cil) is None and cil != start:
        return []   # cesta neexistuje
    trasa = []
    aktualni: str | None = cil
    while aktualni is not None:
        trasa.append(aktualni)
        aktualni = predchudci.get(aktualni)
    trasa.reverse()
    return trasa


mapa = {
    "Praha":    [("Brno", 210), ("Plzeň", 90), ("Liberec", 110)],
    "Brno":     [("Praha", 210), ("Ostrava", 170), ("Olomouc", 75)],
    "Plzeň":    [("Praha", 90), ("České Budějovice", 100)],
    "Liberec":  [("Praha", 110), ("Olomouc", 290)],
    "Ostrava":  [("Brno", 170), ("Olomouc", 90)],
    "Olomouc":  [("Brno", 75), ("Ostrava", 90), ("Liberec", 290)],
    "České Budějovice": [("Plzeň", 100), ("Brno", 245)],
}

vzdalenosti, predchudci = dijkstra_s_cestou(mapa, "Praha")
trasa = cesta(predchudci, "Praha", "Ostrava")

print("Úloha 4 – Dijkstra s rekonstrukcí cesty:")
print(f"  Nejkratší cesta Praha → Ostrava: {' → '.join(trasa)}")
print(f"  Vzdálenost: {vzdalenosti['Ostrava']} km")
print()
print("  Všechny vzdálenosti z Prahy:")
for mesto, dist in sorted(vzdalenosti.items(), key=lambda x: x[1]):
    znacka = "← start" if dist == 0 else f"{dist} km"
    trasa_m = cesta(predchudci, "Praha", mesto)
    print(f"  {mesto:<25} {znacka:>8}  {' → '.join(trasa_m)}")
