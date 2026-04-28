"""Řešení – Lekce 12: Slovníky – věci s popiskem"""

# 1. Překladač s 5 novými slovy přidanými přímo v kódu
slovnik = {
    "pes":    "dog",
    "kocka":  "cat",
    "dum":    "house",
    "strom":  "tree",
    "auto":   "car",
    "skola":  "school",
    # 5 nových slov přidaných v kódu:
    "pocitac": "computer",
    "kniha":   "book",
    "jidlo":   "food",
    "voda":    "water",
    "mesic":   "month",
}
# slovník poskytuje O(1) vyhledávání podle klíče díky hašování
print("Slova ve slovníku:", ", ".join(slovnik.keys()))

# Ukázka vyhledávání bez smyčky input()
hledana = ["pes", "kniha", "hora"]   # input() nahrazeno: hardcoded slova
for slovo in hledana:
    if slovo in slovnik:
        print(f"  {slovo} = {slovnik[slovo]}")
    else:
        print(f"  Slovo '{slovo}' ve slovníku není.")

# 2. Slovník oblíbeného hrdiny
hrdina = {
    "jmeno":     "Spider-Man",
    "sila":      75,
    "rychlost":  80,
    "schopnost": "pavoučí smysly a pavučina",
}
# slovník uchovává heterogenní typy hodnot (str i int) pod jednou strukturou
print("\n--- Můj oblíbený hrdina ---")
for klic, hodnota in hrdina.items():
    print(f"  {klic}: {hodnota}")

# 3. Telefonní seznam s vyhledáváním
telefony = {
    "Míša":  "777 123 456",
    "Tomáš": "608 987 654",
    "Bára":  "731 555 000",
}
print("\n--- Telefonní seznam ---")
hledej = "Tomáš"   # input() nahrazeno: "Koho hledáš?"
# dict.get() vrátí None místo KeyError pokud klíč neexistuje
vysledek = telefony.get(hledej)
if vysledek:
    print(f"  {hledej}: {vysledek}")
else:
    print(f"  Kontakt '{hledej}' nenalezen.")
