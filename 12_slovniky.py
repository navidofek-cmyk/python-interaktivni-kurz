"""
LEKCE 12: Slovníky – věci s popiskem
======================================
Slovník je jako kartotéka: každá věc má svůj popisek (klíč).
seznam:   [hodnota, hodnota, ...]
slovník:  {klíč: hodnota, klíč: hodnota, ...}
"""

hrac = {
    "jmeno": "Míša",
    "vek": 10,
    "oblibena_hra": "Minecraft",
    "body": 350,
}

print(hrac["jmeno"])           # přístup přes klíč
print(hrac["body"])

hrac["body"] += 50             # změna hodnoty
hrac["mesto"] = "Praha"        # přidání nového klíče
print(hrac)

print("\n--- Procházení slovníku ---")
for klic, hodnota in hrac.items():
    print(f"  {klic}: {hodnota}")

print("\n--- Slovník ve slovníku ---")
trida = {
    "Míša":  {"vek": 10, "oblibeny_predmet": "matematika"},
    "Tomáš": {"vek": 11, "oblibeny_predmet": "tělocvik"},
    "Bara":  {"vek": 10, "oblibeny_predmet": "výtvarná"},
}

for jmeno, info in trida.items():
    print(f"{jmeno} ({info['vek']} let) má rád/a {info['oblibeny_predmet']}")

print("\n=== Překladač češtiny a angličtiny ===")
slovnik = {
    "pes": "dog",
    "kočka": "cat",
    "dům": "house",
    "strom": "tree",
    "auto": "car",
    "škola": "school",
}

print("Slova ve slovníku:", ", ".join(slovnik.keys()))

while True:
    slovo = input("\nZadej české slovo (nebo 'konec'): ").lower()
    if slovo == "konec":
        break
    if slovo in slovnik:
        print(f"  {slovo} = {slovnik[slovo]}")
    else:
        print(f"  Slovo '{slovo}' ve slovníku není.")
        pridej = input("  Chceš ho přidat? (ano/ne): ")
        if pridej == "ano":
            anglicky = input("  Jak se řekne anglicky? ")
            slovnik[slovo] = anglicky
            print("  Přidáno!")

# TVOJE ÚLOHA:
# 1. Přidej do překladače 5 nových slov přímo v kódu.
# 2. Vytvoř slovník svého oblíbeného hrdiny (jméno, síla, rychlost, schopnost).
# 3. Vytvoř "telefonní seznam" – slovník {jmeno: cislo} a umožni hledání.
