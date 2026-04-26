"""
PROJEKT: Textová dobrodružná hra
==================================
Klasická "volba příběhu" hra! Kombinuje vše:
proměnné, podmínky, cykly, slovníky, funkce, soubory.
"""

import random
import os

# ── Příběh je mapa místností ─────────────────────────────────────────────────
MISTNOSTI = {
    "start": {
        "popis": "Stojíš před starým hradem. Brána je pootevřená.",
        "volby": {"vejdi": "vstupní_sál", "odejdi": "les"},
    },
    "vstupní_sál": {
        "popis": "Jsi v obrovském sále. Vidíš schody nahoru a dveře doleva.",
        "volby": {"schody": "věž", "dveře": "kuchyň", "zpět": "start"},
    },
    "les": {
        "popis": "Temný les. Slyšíš zvuky. Vidíš cestu zpět a stezku do tmy.",
        "volby": {"zpět": "start", "stezka": "jeskyně"},
    },
    "věž": {
        "popis": "Vrchol věže. Je tu truhla s pokladem a drak spí v rohu!",
        "volby": {"poklad": "VÝHRA", "útěk": "vstupní_sál"},
        "nebezpeci": 0.4,  # 40% šance na probuzení draka
    },
    "kuchyň": {
        "popis": "Stará kuchyň. Najdeš meč na stole a dveře do sklepa.",
        "volby": {"vezmi_meč": "meč", "sklep": "sklep", "zpět": "vstupní_sál"},
        "predmet": "meč",
    },
    "sklep": {
        "popis": "Temný sklep. Je tu netvor!",
        "volby": {"bojuj": "boj", "útěk": "kuchyň"},
    },
    "jeskyně": {
        "popis": "Skrytá jeskyně se zlatem! Našel jsi tajný poklad!",
        "volby": {"vezmi_zlato": "VÝHRA", "zpět": "les"},
    },
}

def vykresli_hp(hp, max_hp=10):
    plne = int(hp / max_hp * 10)
    prazdne = 10 - plne
    return "[" + "█" * plne + "░" * prazdne + f"] {hp}/{max_hp}"

def spust_hru():
    os.system("clear" if os.name == "posix" else "cls")
    print("=" * 50)
    print("   DOBRODRUŽSTVÍ V PROKLETÉM HRADĚ")
    print("=" * 50)

    jmeno = input("\nJak se jmenuješ, hrdino? ")
    hrac = {"jmeno": jmeno, "hp": 10, "inventar": [], "kroky": 0}

    print(f"\nVítej, {jmeno}! Odvahu a štěstí na cestě!\n")
    input("Stiskni Enter pro start...")

    aktualni = "start"

    while True:
        os.system("clear" if os.name == "posix" else "cls")
        mistnost = MISTNOSTI.get(aktualni)

        print(f"\n{'─'*50}")
        print(f"HP: {vykresli_hp(hrac['hp'])}   Kroky: {hrac['kroky']}")
        if hrac["inventar"]:
            print(f"Inventář: {', '.join(hrac['inventar'])}")
        print(f"{'─'*50}\n")
        print(f"📍 {mistnost['popis']}\n")

        # speciální místnosti
        if aktualni == "VÝHRA":
            print(f"🏆 GRATULUJI, {hrac['jmeno']}!")
            print(f"   Dokončil jsi dobrodružství za {hrac['kroky']} kroků!")
            break

        # nebezpečí v místnosti (drak)
        if "nebezpeci" in mistnost and "meč" not in hrac["inventar"]:
            if random.random() < mistnost["nebezpeci"]:
                print("🐉 DRAK SE PROBUDIL! Utíkáš, ale drak tě šlehne ohněm!")
                hrac["hp"] -= 3
                print(f"   Ztratil jsi 3 HP. Zbývá: {hrac['hp']}")
                if hrac["hp"] <= 0:
                    print(f"\n💀 Drak tě porazil. Konec hry, {hrac['jmeno']}.")
                    break
                input("Stiskni Enter...")
                aktualni = "vstupní_sál"
                continue

        # boj s netvotem
        if aktualni == "boj":
            if "meč" in hrac["inventar"]:
                print("⚔️  Bojuješ mečem. VYHRÁVÁŠ! Netvor utíká a za sebou nechá klíč.")
                hrac["inventar"].append("klíč")
                MISTNOSTI["sklep"]["volby"] = {"zpět": "kuchyň"}
            else:
                skoda = random.randint(1, 4)
                hrac["hp"] -= skoda
                print(f"👊 Biješ pěstí. Netvor tě praštil! -{skoda} HP.")
                if hrac["hp"] <= 0:
                    print(f"\n💀 Prohrál jsi. Konec hry, {hrac['jmeno']}.")
                    break
            aktualni = "kuchyň"
            input("Stiskni Enter...")
            continue

        # předmět v místnosti
        if "predmet" in mistnost and mistnost["predmet"] not in hrac["inventar"]:
            predmet = mistnost["predmet"]
            print(f"✨ Vidíš: {predmet}")

        # výběr akce
        volby = mistnost["volby"]
        print("Co uděláš?")
        for i, (akce, _) in enumerate(volby.items(), 1):
            print(f"  {i}) {akce}")

        volba = input("\nTvoje volba: ").lower().strip()

        # přijmout číslo nebo text
        if volba.isdigit():
            idx = int(volba) - 1
            klice = list(volby.keys())
            if 0 <= idx < len(klice):
                volba = klice[idx]

        if volba in volby:
            cil = volby[volba]
            # sbírání předmětu
            if cil == "meč":
                hrac["inventar"].append("meč")
                print("✅ Vzal jsi meč!")
                input("Stiskni Enter...")
            else:
                aktualni = cil
                hrac["kroky"] += 1
        else:
            print("To nejde. Zkus jinou možnost.")
            input("Stiskni Enter...")

spust_hru()

# ROZŠÍŘENÍ:
# 1. Přidej novou místnost do MISTNOSTI a propoj ji.
# 2. Přidej lektvar léčení (+3 HP) do kuchyně.
# 3. Ulož nejlepší skóre (nejméně kroků) do souboru.
