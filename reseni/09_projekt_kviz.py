"""Řešení – Lekce 09: Projekt Kvíz"""

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
    # Rozšíření 1: vlastní přidané otázky
    {
        "otazka": "Kolik kontinentů má Země?",
        "odpovedi": ["A) 5", "B) 6", "C) 7", "D) 8"],
        "spravna": "C"
    },
    {
        "otazka": "Jaký je nejrychlejší suchozemský živočich?",
        "odpovedi": ["A) Lev", "B) Gepard", "C) Kůň", "D) Pštros"],
        "spravna": "B"
    },
    {
        "otazka": "Z jakého ovoce se vyrábí víno?",
        "odpovedi": ["A) Jablka", "B) Švestky", "C) Hroznové víno", "D) Třešně"],
        "spravna": "C"
    },
]

SOUBOR_SKORE = "nejlepsi_skore.txt"


def nacti_nejlepsi():
    """Načte nejlepší skóre ze souboru; vrátí 0 pokud soubor neexistuje."""
    try:
        with open(SOUBOR_SKORE, "r", encoding="utf-8") as f:
            return int(f.read().strip())
    except (FileNotFoundError, ValueError):
        return 0


def uloz_skore(skore):
    """Uloží skóre do souboru pokud je lepší než dosavadní rekord."""
    nejlepsi = nacti_nejlepsi()
    if skore > nejlepsi:
        with open(SOUBOR_SKORE, "w", encoding="utf-8") as f:
            f.write(str(skore))
        return True
    return False


def spust_kviz():
    print("=" * 40)
    print("      VITEJ V SUPER KVIZU!")
    print("=" * 40)

    nejlepsi = nacti_nejlepsi()
    if nejlepsi > 0:
        print(f"Nejlepsi skore: {nejlepsi} bodu")

    # Rozšíření 3 + input() nahrazeno: jméno je hardcoded
    jmeno = "Míša"   # input() nahrazeno: "Jak se jmenuješ?"
    print(f"\nAhoj, {jmeno}! Priprav se na {len(otazky)} otazek!\n")

    skore = 0
    # random.shuffle() promíchá otázky náhodně při každém spuštění
    random.shuffle(otazky)

    for cislo, q in enumerate(otazky, 1):
        print(f"--- Otazka {cislo}/{len(otazky)} ---")
        print(q["otazka"])
        for odpoved in q["odpovedi"]:
            print(" ", odpoved)

        # Rozšíření 2: simulujeme náhodnou odpověď místo input()
        # (skutečný input() by čekal na klávesnici)
        volba = random.choice(["A", "B", "C", "D"])   # input() nahrazeno: náhodná volba
        print(f"Tvoje odpoved: {volba}")

        if volba == q["spravna"]:
            print("SPRAVNE!\n")
            skore += 1
        else:
            print(f"Spatne. Spravna odpoved byla: {q['spravna']}\n")

    print("=" * 40)
    print(f"VYSLEDEK: {skore} / {len(otazky)}")

    # Rozšíření 3: uložení skóre do souboru
    if uloz_skore(skore):
        print(f"Novy rekord! Ulozeno do {SOUBOR_SKORE}")

    if skore == len(otazky):
        print(f"Perfektni skore, {jmeno}! Jsi genius!")
    elif skore >= len(otazky) * 0.8:
        print(f"Skvela prace, {jmeno}!")
    elif skore >= len(otazky) * 0.5:
        print(f"Dobra prace, {jmeno}. Priste to pojde lepe!")
    else:
        print(f"Nevadi, {jmeno}. Trochu procvic a zkus to znovu!")

    print("=" * 40)


spust_kviz()
