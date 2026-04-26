"""
LEKCE 21: Kdo snědl svačinu? – Detektivní logika
===================================================
Učíme se: logické operátory, podmínky, slovníky, funkce.
Inspirováno skutečnými událostmi. Jména jsou změněna.
"""

import random

print("=" * 54)
print("  DETEKTIVNÍ KANCELÁŘ: PŘÍPAD ZMIZELÉ SVAČINY")
print("=" * 54)
print("""
Situace: Dnes o přestávce zmizela svačina z batohu.
Oběť: ty.
Podezřelí: Tomáš, Bára, Ondra, učitelka Nováková.
Tvůj úkol: Vyslechnout podezřelé a najít pachatele.
""")

PODEZRELI = {
    "Tomáš": {
        "alibi": "Byl jsem na záchodě.",
        "stopy": {"drobky_na_rukou": True, "byl_u_batohu": False, "motiv": "má hlad"},
        "pravdivost": 0.6,
        "vinen": False,
    },
    "Bára": {
        "alibi": "Četla jsem knihu u okna.",
        "stopy": {"drobky_na_rukou": False, "byl_u_batohu": True, "motiv": "nemá svačinu"},
        "pravdivost": 0.9,
        "vinen": True,
    },
    "Ondra": {
        "alibi": "Hrál jsem fotbal na hřišti.",
        "stopy": {"drobky_na_rukou": False, "byl_u_batohu": False, "motiv": "žádný"},
        "pravdivost": 0.95,
        "vinen": False,
    },
    "učitelka Nováková": {
        "alibi": "Opravovala jsem písemky ve sborovně.",
        "stopy": {"drobky_na_rukou": False, "byl_u_batohu": False, "motiv": "záhadný"},
        "pravdivost": 1.0,
        "vinen": False,
    },
}

def proverit(jmeno, info):
    print(f"\n── Výslech: {jmeno} ──")
    print(f'  Alibi: "{info["alibi"]}"')
    print(f'  Motiv: {info["stopy"]["motiv"]}')

    podezrele = []
    if info["stopy"]["drobky_na_rukou"]:
        print("  ⚠ Drobky na rukou!")
        podezrele.append("drobky na rukou")
    if info["stopy"]["byl_u_batohu"]:
        print("  ⚠ Svědek ho/ji viděl u batohu!")
        podezrele.append("byl u batohu")

    if not podezrele:
        print("  Nic podezřelého nezjištěno.")

    # Alibi je spolehlivé?
    spolehlive = random.random() < info["pravdivost"]
    if spolehlive:
        print("  Alibi: POTVRZENO (svědci souhlasí)")
    else:
        print("  Alibi: NEPOTVRZENO (svědci si odporují)")
        podezrele.append("nepotrvzené alibi")

    return len(podezrele)

skore = {}
for jmeno, info in PODEZRELI.items():
    vstup = input(f"\nVyslechnout {jmeno}? (ano/ne): ").lower()
    if vstup == "ano":
        skore[jmeno] = proverit(jmeno, info)
    else:
        print(f"  {jmeno} přeskočen/a.")
        skore[jmeno] = 0

print("\n" + "=" * 54)
print("  SHRNUTÍ DŮKAZŮ")
print("=" * 54)

for jmeno, body in sorted(skore.items(), key=lambda x: x[1], reverse=True):
    print(f"  {jmeno:<25} podezření: {'█' * body} ({body})")

# Hráčovo obvinění
print()
obviněny = input("Kogo obviňuješ? ").strip()

# Vyhodnocení
skutecny_pachatel = [j for j, i in PODEZRELI.items() if i["vinen"]][0]

print("\n── VERDIKT ──")
if obviněny.lower() in skutecny_pachatel.lower():
    print(f"SPRÁVNĚ! {skutecny_pachatel} to byl/a.")
    print("Svačina bohužel neexistuje. Ale spravedlnost ano.")
else:
    print(f"Špatně. Byl/a to {skutecny_pachatel}.")
    print(f"  Doznání: \"No dobře. Měla jsem velký hlad.")
    print(f"            Příště si přinesu vlastní.\"")
    print("Falešně obviněný/á má právo na omluvu a sušenku.")

print("\nPřípad uzavřen. Detektivní kancelář děkuje za spolupráci.")
print("Svačinám přejeme lepší příště.")

# TVOJE ÚLOHA:
# 1. Přidej pátého podezřelého (sebe) s alibi "Spával jsem".
# 2. Přidej systém "stopy jako body" – čím víc stop, tím vyšší podezření %.
# 3. Udělej z toho hru pro 2 hráče: jeden nastaví pachatele, druhý hádá.
