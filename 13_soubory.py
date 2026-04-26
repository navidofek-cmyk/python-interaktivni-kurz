"""
LEKCE 13: Soubory – Python si pamatuje!
=========================================
Program si může ukládat věci na disk a načíst je příště znovu.
"""

print("=== Zápis do souboru ===")
with open("poznamky.txt", "w", encoding="utf-8") as f:
    f.write("Toto je moje první poznámka.\n")
    f.write("Python umí ukládat texty!\n")
    f.write("Skvělé, že?\n")

print("Soubor poznamky.txt byl vytvořen.")

print("\n=== Čtení ze souboru ===")
with open("poznamky.txt", "r", encoding="utf-8") as f:
    obsah = f.read()
print(obsah)

print("=== Přidání řádku (append) ===")
with open("poznamky.txt", "a", encoding="utf-8") as f:
    f.write("Tento řádek byl přidán později.\n")

print("\n=== Čtení řádek po řádku ===")
with open("poznamky.txt", "r", encoding="utf-8") as f:
    for cislo, radek in enumerate(f, 1):
        print(f"  {cislo}: {radek}", end="")

print("\n\n=== Deník ===")
SOUBOR = "denik.txt"

while True:
    print("\n1) Přidat záznam")
    print("2) Zobrazit deník")
    print("3) Konec")
    volba = input("Co chceš dělat? ")

    if volba == "1":
        text = input("Napiš svůj záznam: ")
        with open(SOUBOR, "a", encoding="utf-8") as f:
            f.write(text + "\n")
        print("Uloženo!")

    elif volba == "2":
        try:
            with open(SOUBOR, "r", encoding="utf-8") as f:
                zaznamy = f.readlines()
            if zaznamy:
                print("\n--- Tvůj deník ---")
                for i, z in enumerate(zaznamy, 1):
                    print(f"  {i}. {z}", end="")
            else:
                print("Deník je prázdný.")
        except FileNotFoundError:
            print("Deník ještě neexistuje.")

    elif volba == "3":
        print("Ahoj!")
        break

# TVOJE ÚLOHA:
# 1. Přidej do deníku možnost "4) Smazat všechno" (otevři soubor s "w").
# 2. Ulož nákupní seznam z lekce 7 do souboru.
# 3. Načti soubor a vypočítej průměrnou délku slov.
