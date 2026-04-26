"""
LEKCE 8: Funkce – vlastní příkazy
===================================
Funkce je jako recept – napíšeš ho jednou a používáš ho pořád.
"""

def pozdrav(jmeno):
    print(f"Ahoj, {jmeno}! Vítej!")

pozdrav("Míša")
pozdrav("Tomáš")
pozdrav("Barunka")

def secti(a, b):
    return a + b

vysledek = secti(3, 5)
print(f"3 + 5 = {vysledek}")
print(f"10 + 7 = {secti(10, 7)}")

def je_suche(cislo):
    if cislo % 2 == 0:
        return "sudé"
    else:
        return "liché"

for n in range(1, 11):
    print(f"{n} je {je_suche(n)}")

def hvezdicky(pocet):
    print("*" * pocet)

def obdelnik(sirka, vyska):
    for _ in range(vyska):
        hvezdicky(sirka)

print("\n=== Obdélník ===")
obdelnik(10, 4)

# TVOJE ÚLOHA:
# 1. Vytvoř funkci `pozdrav_cs(jmeno, vek)` která vypíše plný pozdrav.
# 2. Vytvoř funkci `max_ze_dvou(a, b)` která vrátí větší číslo.
# 3. Vytvoř funkci `trojuhelnik(vyska)` která nakreslí trojúhelník ze *.
#    Příklad pro vysku=4:
#    *
#    **
#    ***
#    ****
