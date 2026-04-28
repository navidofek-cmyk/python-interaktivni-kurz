"""Řešení – Lekce 37: Grafy – BFS a DFS"""

from collections import deque
import heapq


# Originální MAPA z lekce
MAPA = {
    "Praha":   [("Brno", 210), ("Plzeň", 90),  ("Liberec", 110)],
    "Brno":    [("Praha", 210), ("Ostrava", 170), ("Olomouc", 75)],
    "Plzeň":   [("Praha", 90),  ("České Budějovice", 100)],
    "Liberec": [("Praha", 110), ("Hradec Králové", 100)],
    "Ostrava": [("Brno", 170),  ("Olomouc", 90)],
    "Olomouc": [("Brno", 75),   ("Ostrava", 90), ("Hradec Králové", 160)],
    "Hradec Králové": [("Liberec", 100), ("Olomouc", 160)],
    "České Budějovice": [("Plzeň", 100)],
}


def dijkstra(graf, start):
    dist = {uzel: float("inf") for uzel in graf}
    dist[start] = 0
    predchudce = {start: None}
    fronta = [(0, start)]

    while fronta:
        d, uzel = heapq.heappop(fronta)
        if d > dist[uzel]:
            continue
        for soused, vaha in graf.get(uzel, []):
            nova_d = d + vaha
            if nova_d < dist[soused]:
                dist[soused] = nova_d
                predchudce[soused] = uzel
                heapq.heappush(fronta, (nova_d, soused))

    return dist, predchudce


def rekonstruuj_cestu(predchudce, cil):
    cesta = []
    uzel = cil
    while uzel is not None:
        cesta.append(uzel)
        uzel = predchudce.get(uzel)
    return list(reversed(cesta))


# 1. Přidej Zlín a znovu spusť Dijkstru
# Zlín: Brno 80km, Ostrava 110km – přidáme symetricky do obou stran

MAPA_SE_ZLINEM = dict(MAPA)
MAPA_SE_ZLINEM["Zlín"] = [("Brno", 80), ("Ostrava", 110)]
MAPA_SE_ZLINEM["Brno"] = list(MAPA["Brno"]) + [("Zlín", 80)]
MAPA_SE_ZLINEM["Ostrava"] = list(MAPA["Ostrava"]) + [("Zlín", 110)]

print("=== 1. Dijkstra s přidaným Zlínem ===\n")
vzdal, pred = dijkstra(MAPA_SE_ZLINEM, "Praha")

print("Nejkratší vzdálenosti z Prahy (s Zlínem):")
for mesto, d in sorted(vzdal.items(), key=lambda x: x[1]):
    cesta = rekonstruuj_cestu(pred, mesto)
    print(f"  {d:4d} km  {' → '.join(cesta)}")


# 2. Je graf bipartitní? – lze obarvit 2 barvami bez sousedních stejných barev
# Algoritmus: BFS, střídavě přiřazujeme barvy 0 a 1
# Pokud narazíme na soused se stejnou barvou → není bipartitní

def je_bipartitni(graf: dict) -> tuple[bool, dict]:
    """
    BFS barvení grafu.
    Vrátí (True/False, slovník {uzel: barva}).
    Bipartitní = lze rozdělit uzly na dvě skupiny bez vnitřních hran.
    """
    barva = {}  # {uzel: 0 nebo 1}

    for start in graf:
        if start in barva:
            continue
        # BFS z každé nenavštívené komponenty
        fronta = deque([start])
        barva[start] = 0

        while fronta:
            uzel = fronta.popleft()
            for soused in graf.get(uzel, []):
                if soused not in barva:
                    barva[soused] = 1 - barva[uzel]  # opačná barva
                    fronta.append(soused)
                elif barva[soused] == barva[uzel]:
                    return False, barva  # lichý cyklus → není bipartitní

    return True, barva


print("\n=== 2. Je graf bipartitní? ===\n")

# Bipartitní: tah šachovnice (každý uzel jen do "opačné barvy")
bipartitni = {
    "A": ["B", "D"],
    "B": ["A", "C"],
    "C": ["B", "D"],
    "D": ["A", "C"],
}
# Sociální síť (trojúhelník) – není bipartitní
neni_bipartitni = {
    "X": ["Y", "Z"],
    "Y": ["X", "Z"],
    "Z": ["X", "Y"],
}
# Dvě skupiny: studenti ↔ kurzy
studenti_kurzy = {
    "Míša": ["Python", "Matematika"],
    "Tomáš": ["Python"],
    "Python": ["Míša", "Tomáš"],
    "Matematika": ["Míša"],
}

for nazev, graf in [("Čtverec (bipartitní)", bipartitni),
                     ("Trojúhelník (není bipartitní)", neni_bipartitni),
                     ("Studenti–Kurzy (bipartitní)", studenti_kurzy)]:
    bipart, barvy = je_bipartitni(graf)
    skupiny = {0: [], 1: []}
    for uzel, b in barvy.items():
        skupiny[b].append(uzel)
    print(f"  {nazev}: {'ANO' if bipart else 'NE'}")
    if bipart:
        print(f"    Skupina 0: {skupiny[0]}")
        print(f"    Skupina 1: {skupiny[1]}")


# 3. Počet komponent grafu pomocí BFS
# Komponenta = skupina uzlů, které jsou vzájemně dosažitelné
# Algoritmus: BFS z každého nenavštíveného uzlu → každý start = nová komponenta

def pocet_komponent(graf: dict) -> tuple[int, list[set]]:
    """
    Vrátí (počet komponent, seznam množin uzlů v každé komponentě).
    Izolovaný uzel = vlastní komponenta.
    """
    navstiveno = set()
    komponenty = []

    def bfs_komponenta(start):
        komponenta = set()
        fronta = deque([start])
        navstiveno.add(start)
        while fronta:
            uzel = fronta.popleft()
            komponenta.add(uzel)
            for soused in graf.get(uzel, []):
                if soused not in navstiveno:
                    navstiveno.add(soused)
                    fronta.append(soused)
        return komponenta

    for uzel in graf:
        if uzel not in navstiveno:
            komponenty.append(bfs_komponenta(uzel))

    return len(komponenty), komponenty


print("\n=== 3. Počet komponent grafu ===\n")

# Propojený graf (1 komponenta)
propojeny = {"A": ["B"], "B": ["A", "C"], "C": ["B"], "D": ["E"], "E": ["D"]}

# Izolované uzly + skupiny (více komponent)
fragmentovany = {
    "A": ["B"],  "B": ["A"],   # komponenta 1
    "C": ["D"],  "D": ["C"],   # komponenta 2
    "E": [],                   # izolovaný uzel
    "F": ["G", "H"], "G": ["F"], "H": ["F"],  # komponenta 3
}

for nazev, graf in [("Fragmentovaný", propojeny), ("Více skupin", fragmentovany)]:
    pocet, komp = pocet_komponent(graf)
    print(f"  {nazev}: {pocet} komponenta/y")
    for i, k in enumerate(komp, 1):
        print(f"    Komponenta {i}: {sorted(k)}")
