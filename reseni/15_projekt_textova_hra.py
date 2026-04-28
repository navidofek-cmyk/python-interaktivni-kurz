"""Řešení – Lekce 15: Textová dobrodružná hra

Hra je plně interaktivní – input() je záměrně zachováno.
Rozšíření: nová místnost, lektvar léčení, uložení nejlepšího skóre.
Spust: python3 reseni/15_projekt_textova_hra.py
"""

import random
import os

SOUBOR_SKORE = "reseni_nejlepsi_kroky.txt"

# ── Mapa místností (rozšíření 1: přidána "studna") ───────────────────────────
MISTNOSTI = {
    "start": {
        "popis": "Stojis pred starym hradem. Brana je pootevřena.",
        "volby": {"vejdi": "vstupni_sal", "odejdi": "les"},
    },
    "vstupni_sal": {
        "popis": "Jsi v obrovskem sali. Vides schody nahoru a dvere doleva.",
        "volby": {"schody": "vez", "dvere": "kuchyn", "zpet": "start"},
    },
    "les": {
        "popis": "Temny les. Slysis zvuky. Vides cestu zpet a stezku do tmy.",
        "volby": {"zpet": "start", "stezka": "jeskyne"},
    },
    "vez": {
        "popis": "Vrchol veze. Je tu truhla s pokladem a drak spi v rohu!",
        "volby": {"poklad": "VYHRA", "utek": "vstupni_sal"},
        "nebezpeci": 0.4,
    },
    "kuchyn": {
        "popis": "Stara kuchyn. Najdes mec na stole, lektvar na police a dvere do sklepa.",
        "volby": {"vezmi_mec": "mec", "vezmi_lektvar": "lektvar",
                  "sklep": "sklep", "zpet": "vstupni_sal"},
        "predmet": "mec",
    },
    "sklep": {
        "popis": "Temny sklep. Je tu netvor!",
        "volby": {"bojuj": "boj", "utek": "kuchyn"},
    },
    "jeskyne": {
        "popis": "Skryta jeskyne se zlatem! Nasel/a jsi tajny poklad!",
        "volby": {"vezmi_zlato": "VYHRA", "zpet": "les"},
    },
    # Rozšíření 1: nová místnost studna propojená z lesa
    "studna": {
        "popis": "Stara studna. Voda je cista a obnovuje sily.",
        "volby": {"napij_se": "leceni", "zpet": "les"},
    },
}

# Propojíme les se studnou
MISTNOSTI["les"]["volby"]["studna"] = "studna"


def nacti_rekord():
    """Vrátí nejlepší (nejmenší) počet kroků z minulých her."""
    try:
        with open(SOUBOR_SKORE, "r", encoding="utf-8") as f:
            return int(f.read().strip())
    except (FileNotFoundError, ValueError):
        return None


def uloz_rekord(kroky):
    """Uloží nový rekord pokud je lepší než dosavadní."""
    rekord = nacti_rekord()
    if rekord is None or kroky < rekord:
        with open(SOUBOR_SKORE, "w", encoding="utf-8") as f:
            f.write(str(kroky))
        return True
    return False


def vykresli_hp(hp, max_hp=10):
    plne = int(hp / max_hp * 10)
    prazdne = 10 - plne
    return "[" + "=" * plne + "." * prazdne + f"] {hp}/{max_hp}"


def spust_hru():
    os.system("clear" if os.name == "posix" else "cls")
    print("=" * 50)
    print("   DOBRODRUZSTVI V PROKLETEM HRADE")
    print("=" * 50)

    rekord = nacti_rekord()
    if rekord:
        print(f"Nejlepsi skore: {rekord} kroku")

    jmeno = input("\nJak se jmenujes, hrdino? ")
    # slovník hráče uchovává veškerý stav na jednom místě
    hrac = {"jmeno": jmeno, "hp": 10, "inventar": [], "kroky": 0}

    print(f"\nVitej, {jmeno}! Odvahu a stesti na ceste!\n")
    input("Stiskni Enter pro start...")

    aktualni = "start"

    while True:
        os.system("clear" if os.name == "posix" else "cls")
        mistnost = MISTNOSTI.get(aktualni)

        print(f"\n{'─'*50}")
        print(f"HP: {vykresli_hp(hrac['hp'])}   Kroky: {hrac['kroky']}")
        if hrac["inventar"]:
            print(f"Inventar: {', '.join(hrac['inventar'])}")
        print(f"{'─'*50}\n")
        print(f">>> {mistnost['popis']}\n")

        # Výhra
        if aktualni == "VYHRA":
            print(f"GRATULACE, {hrac['jmeno']}!")
            print(f"Dokoncil/a jsi dobrodruzstvi za {hrac['kroky']} kroku!")
            if uloz_rekord(hrac["kroky"]):
                print(f"Novy rekord! Ulozeno do {SOUBOR_SKORE}")
            break

        # Rozšíření 2: pití léčivé vody ve studně
        if aktualni == "leceni":
            prirust = min(3, 10 - hrac["hp"])
            hrac["hp"] += prirust
            print(f"Napijes se studene vody. +{prirust} HP.")
            input("Stiskni Enter...")
            aktualni = "les"
            continue

        # Nebezpečí: drak
        if "nebezpeci" in mistnost and "mec" not in hrac["inventar"]:
            if random.random() < mistnost["nebezpeci"]:
                print("DRAK SE PROBUDIL! Utíkas, ale drak te slehne ohnem!")
                hrac["hp"] -= 3
                print(f"   Ztratil/a jsi 3 HP. Zbývá: {hrac['hp']}")
                if hrac["hp"] <= 0:
                    print(f"\nDrak te porazil. Konec hry, {hrac['jmeno']}.")
                    break
                input("Stiskni Enter...")
                aktualni = "vstupni_sal"
                continue

        # Boj s netvotem
        if aktualni == "boj":
            if "mec" in hrac["inventar"]:
                print("Bojes mecem. VYHRAVAS! Netvor utika.")
                hrac["inventar"].append("klic")
                MISTNOSTI["sklep"]["volby"] = {"zpet": "kuchyn"}
            else:
                skoda = random.randint(1, 4)
                hrac["hp"] -= skoda
                print(f"Bijes pesti. Netvor te praštil! -{skoda} HP.")
                if hrac["hp"] <= 0:
                    print(f"\nProhral/a jsi. Konec hry, {hrac['jmeno']}.")
                    break
            aktualni = "kuchyn"
            input("Stiskni Enter...")
            continue

        # Předmět v místnosti (meč)
        if "predmet" in mistnost and mistnost["predmet"] not in hrac["inventar"]:
            print(f"Vides: {mistnost['predmet']}")

        # Výběr akce
        volby = mistnost["volby"]
        print("Co udelaš?")
        for i, (akce, _) in enumerate(volby.items(), 1):
            print(f"  {i}) {akce}")

        volba = input("\nTvoje volba: ").lower().strip()

        if volba.isdigit():
            idx = int(volba) - 1
            klice = list(volby.keys())
            if 0 <= idx < len(klice):
                volba = klice[idx]

        if volba in volby:
            cil = volby[volba]
            if cil == "mec":
                hrac["inventar"].append("mec")
                print("Vzal/a jsi mec!")
                input("Stiskni Enter...")
            # Rozšíření 2: lektvar léčení (+3 HP)
            elif cil == "lektvar":
                if "lektvar" not in hrac["inventar"]:
                    hrac["inventar"].append("lektvar")
                    hrac["hp"] = min(10, hrac["hp"] + 3)
                    print(f"Vypil/a jsi lektvar leceni. +3 HP! Nyni: {hrac['hp']} HP")
                else:
                    print("Uz jsi lektvar pouzil/a.")
                input("Stiskni Enter...")
            else:
                aktualni = cil
                hrac["kroky"] += 1
        else:
            print("To nejde. Zkus jinou moznost.")
            input("Stiskni Enter...")


spust_hru()
