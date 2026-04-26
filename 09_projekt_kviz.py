"""
PROJEKT: Kvíz
==============
Tvůj první větší program – kvíz se skóre!
Zkombinuje vše co jsi se naučil.
"""

import random

otazky = [
    {
        "otazka": "Jaké je hlavní město České republiky?",
        "odpovedi": ["A) Brno", "B) Praha", "C) Ostrava", "D) Plzeň"],
        "spravna": "B"
    },
    {
        "otazka": "Kolik noh má pavouk?",
        "odpovedi": ["A) 6", "B) 4", "C) 10", "D) 8"],
        "spravna": "D"
    },
    {
        "otazka": "Kolik je 12 × 12?",
        "odpovedi": ["A) 124", "B) 144", "C) 132", "D) 148"],
        "spravna": "B"
    },
    {
        "otazka": "Která planeta je největší v naší sluneční soustavě?",
        "odpovedi": ["A) Saturn", "B) Mars", "C) Jupiter", "D) Neptun"],
        "spravna": "C"
    },
    {
        "otazka": "Jak se jmenuje autor Harryho Pottera?",
        "odpovedi": ["A) J.R.R. Tolkien", "B) J.K. Rowling", "C) Roald Dahl", "D) C.S. Lewis"],
        "spravna": "B"
    },
]

def spust_kviz():
    print("=" * 40)
    print("      VÍTEJ V SUPER KVÍZU!")
    print("=" * 40)

    jmeno = input("\nJak se jmenuješ? ")
    print(f"\nAhoj, {jmeno}! Připrav se na {len(otazky)} otázek!\n")

    skore = 0
    random.shuffle(otazky)

    for cislo, q in enumerate(otazky, 1):
        print(f"--- Otázka {cislo}/{len(otazky)} ---")
        print(q["otazka"])
        for odpoved in q["odpovedi"]:
            print(" ", odpoved)

        while True:
            volba = input("Tvoje odpověď (A/B/C/D): ").upper()
            if volba in ["A", "B", "C", "D"]:
                break
            print("Zadej A, B, C nebo D!")

        if volba == q["spravna"]:
            print("✓ SPRÁVNĚ!\n")
            skore += 1
        else:
            print(f"✗ Špatně. Správná odpověď byla: {q['spravna']}\n")

    print("=" * 40)
    print(f"VÝSLEDEK: {skore} / {len(otazky)}")

    if skore == len(otazky):
        print(f"Perfektní skóre, {jmeno}! Jsi génius!")
    elif skore >= len(otazky) * 0.8:
        print(f"Skvělá práce, {jmeno}!")
    elif skore >= len(otazky) * 0.5:
        print(f"Dobrá práce, {jmeno}. Příště to půjde lépe!")
    else:
        print(f"Nevadí, {jmeno}. Trochu procvič a zkus to znovu!")

    print("=" * 40)

spust_kviz()

# ROZŠÍŘENÍ (pro odvážné):
# 1. Přidej vlastní otázky do seznamu `otazky`.
# 2. Přidej časový limit na odpověď (nápověda: import time, time.time()).
# 3. Ulož nejlepší skóre do souboru a zobraz ho na začátku.
