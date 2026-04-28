"""Řešení – Lekce 10: Projekt Had v bludišti

Toto je konzolová hra Had. input() je zachováno pro interaktivní ovládání,
protože hra bez vstupů nedává smysl. Spusť: python3 reseni/10_projekt_had.py
"""

import random
import os

SIRKA = 20
VYSKA = 10


def vykresli(had, jidlo, skore):
    os.system("clear" if os.name == "posix" else "cls")
    print(f"  Skore: {skore}   |   Ovladani: W A S D   |   Konec: Q")
    print("+" + "-" * SIRKA + "+")

    for y in range(VYSKA):
        radek = "|"
        for x in range(SIRKA):
            if [x, y] == had[0]:
                radek += "O"       # hlava hada
            elif [x, y] in had[1:]:
                radek += "#"       # telo hada
            elif [x, y] == jidlo:
                radek += "*"       # jidlo
            else:
                radek += " "
        radek += "|"
        print(radek)

    print("+" + "-" * SIRKA + "+")


def novy_had():
    x = SIRKA // 2
    y = VYSKA // 2
    return [[x, y], [x - 1, y], [x - 2, y]]


def nove_jidlo(had):
    # smyčka zaručuje, že jídlo nevznikne na těle hada
    while True:
        jidlo = [random.randint(0, SIRKA - 1), random.randint(0, VYSKA - 1)]
        if jidlo not in had:
            return jidlo


def hraj():
    had = novy_had()
    jidlo = nove_jidlo(had)
    smer = [1, 0]
    skore = 0

    print("Stiskni Enter pro start...")
    input()

    while True:
        vykresli(had, jidlo, skore)

        tah = input("Tah (W/A/S/D/Q): ").lower().strip()

        if tah == "q":
            print("Konec hry. Ahoj!")
            break
        elif tah == "w" and smer != [0, 1]:
            smer = [0, -1]
        elif tah == "s" and smer != [0, -1]:
            smer = [0, 1]
        elif tah == "a" and smer != [1, 0]:
            smer = [-1, 0]
        elif tah == "d" and smer != [-1, 0]:
            smer = [1, 0]

        nova_hlava = [had[0][0] + smer[0], had[0][1] + smer[1]]

        # kontrola narazu do zdi
        if not (0 <= nova_hlava[0] < SIRKA and 0 <= nova_hlava[1] < VYSKA):
            vykresli(had, jidlo, skore)
            print(f"\nBUM! Narazil jsi do zdi. Konecne skore: {skore}")
            break

        # kontrola uštknutí sám sebe
        if nova_hlava in had:
            vykresli(had, jidlo, skore)
            print(f"\nBUM! Kousl jsi se. Konecne skore: {skore}")
            break

        # insert na začátek je O(n) – pro malé hady zcela dostačující
        had.insert(0, nova_hlava)

        if nova_hlava == jidlo:
            skore += 10
            jidlo = nove_jidlo(had)
            print("Nom nom! +10 bodu!")
            input("Enter pro pokracovani...")
        else:
            had.pop()


hraj()
