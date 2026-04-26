"""
LEKCE 37: Grafy – BFS a DFS
=============================
Graf = uzly (vrcholy) propojené hranami.
Použití: mapy, sociální sítě, závislosti balíčků, GPS navigace...

BFS (Breadth-First Search) – prohledávání do šířky
  → nejprve všichni sousedé, pak jejich sousedé...
  → najde NEJKRATŠÍ cestu (počet hran)
  → používá FRONTU (queue)

DFS (Depth-First Search) – prohledávání do hloubky
  → jde co nejdál jednou cestou, pak se vrátí
  → používá ZÁSOBNÍK (stack) nebo rekurzi
  → vhodný pro detekci cyklů, topologické řazení
"""

from collections import deque

# ══════════════════════════════════════════════════════════════
# REPREZENTACE GRAFU
# ══════════════════════════════════════════════════════════════

# Seznam sousedů (adjacency list) – nejběžnější
METRO = {
    "Můstek":      ["Muzeum", "Náměstí Republiky", "Staroměstská"],
    "Muzeum":      ["Můstek", "Hlavní nádraží", "Náměstí Míru"],
    "Staroměstská":["Můstek", "Malostranská"],
    "Malostranská":["Staroměstská", "Hradčanská"],
    "Hradčanská":  ["Malostranská", "Dejvická"],
    "Dejvická":    ["Hradčanská"],
    "Hlavní nádraží": ["Muzeum", "Florenc"],
    "Florenc":     ["Hlavní nádraží", "Náměstí Republiky", "Invalidovna"],
    "Náměstí Republiky": ["Můstek", "Florenc"],
    "Invalidovna": ["Florenc"],
    "Náměstí Míru": ["Muzeum", "Jiřího z Poděbrad"],
    "Jiřího z Poděbrad": ["Náměstí Míru", "Flora"],
    "Flora":       ["Jiřího z Poděbrad"],
}

def tiskni_graf(graf, max_uzlu=6):
    print("Graf (seznam sousedů):")
    for uzel, sousede in list(graf.items())[:max_uzlu]:
        print(f"  {uzel:<25} → {sousede}")
    print(f"  ... ({len(graf)} uzlů celkem)")


# ══════════════════════════════════════════════════════════════
# BFS – nejkratší cesta
# ══════════════════════════════════════════════════════════════

def bfs(graf, start, cil=None):
    """Vrátí: (vzdalenosti od start, predchudci pro rekonstrukci cesty)."""
    navstiveno = {start}
    fronta     = deque([start])
    vzdalenost = {start: 0}
    predchudce = {start: None}

    while fronta:
        uzel = fronta.popleft()

        if uzel == cil:
            break

        for soused in graf.get(uzel, []):
            if soused not in navstiveno:
                navstiveno.add(soused)
                fronta.append(soused)
                vzdalenost[soused] = vzdalenost[uzel] + 1
                predchudce[soused] = uzel

    return vzdalenost, predchudce

def rekonstruuj_cestu(predchudce, cil):
    cesta = []
    uzel  = cil
    while uzel is not None:
        cesta.append(uzel)
        uzel = predchudce.get(uzel)
    return list(reversed(cesta))

print("=== BFS – nejkratší cesta v metru ===\n")
tiskni_graf(METRO)

start, cil = "Dejvická", "Flora"
vzdalenosti, predchudci = bfs(METRO, start, cil)

if cil in predchudci:
    cesta = rekonstruuj_cestu(predchudci, cil)
    print(f"\nNejkratší cesta: {start} → {cil}")
    print(f"  {' → '.join(cesta)}")
    print(f"  Počet přestávek: {len(cesta)-1}")
else:
    print(f"Cesta z {start} do {cil} neexistuje.")

print(f"\nVzdálenosti z {start}:")
for stanice, d in sorted(vzdalenosti.items(), key=lambda x: x[1]):
    print(f"  {d} přestávek: {stanice}")


# ══════════════════════════════════════════════════════════════
# DFS – průchod do hloubky
# ══════════════════════════════════════════════════════════════

def dfs_rekurzivni(graf, uzel, navstiveno=None, poradi=None):
    if navstiveno is None:
        navstiveno = set()
        poradi     = []
    navstiveno.add(uzel)
    poradi.append(uzel)
    for soused in graf.get(uzel, []):
        if soused not in navstiveno:
            dfs_rekurzivni(graf, soused, navstiveno, poradi)
    return poradi

def dfs_iterativni(graf, start):
    navstiveno = set()
    zasobnik   = [start]
    poradi     = []
    while zasobnik:
        uzel = zasobnik.pop()
        if uzel not in navstiveno:
            navstiveno.add(uzel)
            poradi.append(uzel)
            for soused in reversed(graf.get(uzel, [])):
                if soused not in navstiveno:
                    zasobnik.append(soused)
    return poradi

print("\n=== DFS – průchod do hloubky ===")
print(f"\nDFS rekurzivní z Můstek:")
print(f"  {dfs_rekurzivni(METRO, 'Můstek')}")
print(f"\nDFS iterativní z Můstek:")
print(f"  {dfs_iterativni(METRO, 'Můstek')}")


# ══════════════════════════════════════════════════════════════
# DIJKSTRŮV ALGORITMUS – nejkratší cesta s váhami
# ══════════════════════════════════════════════════════════════

import heapq

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
    dist      = {uzel: float("inf") for uzel in graf}
    dist[start] = 0
    predchudce  = {start: None}
    fronta      = [(0, start)]   # (vzdálenost, uzel)

    while fronta:
        d, uzel = heapq.heappop(fronta)
        if d > dist[uzel]:
            continue
        for soused, vaha in graf.get(uzel, []):
            nova_d = d + vaha
            if nova_d < dist[soused]:
                dist[soused]      = nova_d
                predchudce[soused] = uzel
                heapq.heappush(fronta, (nova_d, soused))

    return dist, predchudce

print("\n=== Dijkstrův algoritmus – nejkratší cesty v ČR ===")
vzdal, pred = dijkstra(MAPA, "Praha")

print("\nNejkratší vzdálenosti z Prahy:")
for mesto, d in sorted(vzdal.items(), key=lambda x: x[1]):
    cesta = rekonstruuj_cestu(pred, mesto)
    print(f"  {d:4d} km  {' → '.join(cesta)}")


# ══════════════════════════════════════════════════════════════
# DETEKCE CYKLU
# ══════════════════════════════════════════════════════════════

def ma_cyklus(graf):
    """DFS detekce cyklu v neorientovaném grafu."""
    navstiveno = set()

    def dfs(uzel, rodic):
        navstiveno.add(uzel)
        for soused in graf.get(uzel, []):
            if soused not in navstiveno:
                if dfs(soused, uzel):
                    return True
            elif soused != rodic:
                return True   # nalezen cyklus!
        return False

    return any(dfs(u, None) for u in graf if u not in navstiveno)

STROM  = {"A": ["B","C"], "B": ["A","D"], "C": ["A"], "D": ["B"]}
CYKLUS = {"A": ["B","C"], "B": ["A","D"], "C": ["A","D"], "D": ["B","C"]}

print(f"\n=== Detekce cyklu ===")
print(f"  Strom (bez cyklu): {ma_cyklus(STROM)}")
print(f"  Graf s cyklem:     {ma_cyklus(CYKLUS)}")

# ══════════════════════════════════════════════════════════════
# TOPOLOGICKÉ ŘAZENÍ (DAG)
# ══════════════════════════════════════════════════════════════

def topologicke_razeni(zavislosti: dict[str, list[str]]) -> list[str]:
    """Kahn's algorithm – pořadí, ve kterém lze splnit úkoly."""
    from collections import Counter
    stupne = Counter()
    for uzel in zavislosti:
        stupne.setdefault(uzel, 0)
        for soused in zavislosti[uzel]:
            stupne[soused] += 1

    fronta  = deque(u for u, d in stupne.items() if d == 0)
    poradi  = []
    while fronta:
        uzel = fronta.popleft()
        poradi.append(uzel)
        for soused in zavislosti.get(uzel, []):
            stupne[soused] -= 1
            if stupne[soused] == 0:
                fronta.append(soused)

    if len(poradi) != len(stupne):
        raise ValueError("Graf obsahuje cyklus – topologické řazení nelze!")
    return poradi

KURZ = {
    "Python základy":   ["OOP", "Funkce"],
    "Funkce":           ["Dekorátory", "Rekurze"],
    "OOP":              ["Dědičnost", "Magic methods"],
    "Rekurze":          ["Algoritmy"],
    "Dědičnost":        ["Algoritmy"],
    "Magic methods":    [],
    "Dekorátory":       [],
    "Algoritmy":        [],
}

print(f"\n=== Topologické řazení – pořadí výuky ===")
print(f"  {' → '.join(topologicke_razeni(KURZ))}")

# TVOJE ÚLOHA:
# 1. Přidej do MAPA město "Zlín" (Brno 80km, Ostrava 110km) a znovu spusť Dijkstru.
# 2. Napiš je_bipartitni(graf) – lze Graf obarvit 2 barvami bez sousedních stejných?
# 3. Zjisti počet komponent grafu (izolovaných podgrafů) pomocí BFS.
