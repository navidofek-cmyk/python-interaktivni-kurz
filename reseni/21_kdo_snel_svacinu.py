"""Řešení – Lekce 21: Kdo snědl svačinu? – Detektivní logika"""

import random

# Původní slovník podezřelých + nový 5. podezřelý (já)
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
    # 1. Pátý podezřelý – já sám
    # Přidán jako 5. hráč, aby hra měla více neočekávaných možností
    "Já": {
        "alibi": "Spával jsem.",
        "stopy": {"drobky_na_rukou": False, "byl_u_batohu": False, "motiv": "somnambulismus?"},
        "pravdivost": 0.5,
        "vinen": False,
    },
}


def proverit(jmeno, info):
    print(f"\n── Výslech: {jmeno} ──")
    print(f'  Alibi: "{info["alibi"]}"')
    print(f'  Motiv: {info["stopy"]["motiv"]}')

    podezrele = []
    if info["stopy"]["drobky_na_rukou"]:
        print("  !! Drobky na rukou!")
        podezrele.append("drobky na rukou")
    if info["stopy"]["byl_u_batohu"]:
        print("  !! Svědek ho/ji viděl u batohu!")
        podezrele.append("byl u batohu")

    if not podezrele:
        print("  Nic podezřelého nezjištěno.")

    # Alibi ověření
    spolehlive = random.random() < info["pravdivost"]
    if spolehlive:
        print("  Alibi: POTVRZENO")
    else:
        print("  Alibi: NEPOTVRZENO")
        podezrele.append("nepotvrzené alibi")

    # 2. Stopy jako procentuální podezření
    # Čím víc stop, tím vyšší podezření – vrátíme skóre a vypočítáme %
    max_stop = 3  # max možné: drobky + byl_u_batohu + nepotvrzené alibi
    procenta = round(len(podezrele) / max_stop * 100)
    print(f"  Podezření: {procenta}% ({len(podezrele)}/{max_stop} indicií)")

    return len(podezrele), procenta


# 3. Hra pro 2 hráče: hráč 1 nastaví pachatele, hráč 2 hádá
print("=" * 54)
print("  DETEKTIVNÍ KANCELÁŘ – HRA PRO 2 HRÁČE")
print("=" * 54)

# simulace vstupu: hráč 1 zvolí pachatele
pachatel_volba = "Bára"  # simulace vstupu: "Bára"
print(f"\n[Hráč 1] Zadej jméno pachatele (ostatní nekoukejte): {pachatel_volba}")

jmena = list(PODEZRELI.keys())
if pachatel_volba not in jmena:
    pachatel_volba = random.choice(jmena)
    print(f"  (Neplatné jméno, náhodně zvoleno: {pachatel_volba})")

# Nastav vinu – dočasně přepíšeme
pro_hru = {}
for j, info in PODEZRELI.items():
    pro_hru[j] = {**info, "vinen": (j == pachatel_volba)}

print("\n" + "=" * 54)
print("  [Hráč 2] Začíná výslech podezřelých")
print("=" * 54)

skore = {}
# simulace vstupu: všichni vyslechnuti
odpovedi = {"Tomáš": "ano", "Bára": "ano", "Ondra": "ano",
            "učitelka Nováková": "ano", "Já": "ano"}

for jmeno, info in pro_hru.items():
    vstup = odpovedi.get(jmeno, "ano")  # simulace vstupu: "ano"
    print(f"\nVyslechnout {jmeno}? (simulace: {vstup})")
    if vstup == "ano":
        body, pct = proverit(jmeno, info)
        skore[jmeno] = (body, pct)
    else:
        print(f"  {jmeno} přeskočen/a.")
        skore[jmeno] = (0, 0)

print("\n" + "=" * 54)
print("  SHRNUTÍ DŮKAZŮ (seřazeno dle podezření)")
print("=" * 54)

for jmeno, (body, pct) in sorted(skore.items(), key=lambda x: x[1][0], reverse=True):
    bar = "█" * body
    print(f"  {jmeno:<25} {bar} ({pct}%)")

# Hráč 2 obviní
obviněny = "Bára"  # simulace vstupu: "Bára"
print(f"\n[Hráč 2] Obviňuji: {obviněny}")

skutecny = [j for j, i in pro_hru.items() if i["vinen"]][0]
print("\n── VERDIKT ──")
if obviněny.lower() in skutecny.lower():
    print(f"SPRÁVNĚ! {skutecny} to byl/a. Hráč 2 vyhrál!")
else:
    print(f"Špatně. Byl/a to {skutecny}. Hráč 1 vyhrál!")

print("\nPřípad uzavřen.")
