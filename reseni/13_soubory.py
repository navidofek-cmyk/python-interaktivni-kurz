"""Řešení – Lekce 13: Soubory – Python si pamatuje!"""

import os

SOUBOR_DENIK = "reseni_denik.txt"
SOUBOR_NAKUP = "reseni_nakup.txt"

# ── Základní operace se soubory ───────────────────────────────────────────────

# Zápis souboru
with open("reseni_poznamky.txt", "w", encoding="utf-8") as f:
    f.write("Toto je moje prvni poznamka.\n")
    f.write("Python umi ukladat texty!\n")
    f.write("Skvele, ze?\n")
print("Soubor reseni_poznamky.txt byl vytvoreny.")

# Čtení souboru
with open("reseni_poznamky.txt", "r", encoding="utf-8") as f:
    obsah = f.read()
# with-blok automaticky zavře soubor i při výjimce – bezpečnější než f.close()
print(obsah)

# ── Úloha 1: Možnost "Smazat všechno" ────────────────────────────────────────

def pridej_zaznam(text):
    """Přidá řádek do deníku (append = nepřepíše existující obsah)."""
    with open(SOUBOR_DENIK, "a", encoding="utf-8") as f:
        f.write(text + "\n")

def zobraz_denik():
    """Vypíše všechny záznamy z deníku s číslem řádku."""
    try:
        with open(SOUBOR_DENIK, "r", encoding="utf-8") as f:
            zaznamy = f.readlines()
        if zaznamy:
            print("\n--- Tvuj denik ---")
            for i, z in enumerate(zaznamy, 1):
                print(f"  {i}. {z}", end="")
        else:
            print("Denik je prazdny.")
    except FileNotFoundError:
        print("Denik jeste neexistuje.")

def smaz_vse():
    """Smaže veškerý obsah deníku otevřením souboru v režimu 'w'."""
    # Otevření v módu "w" přepíše soubor prázdným obsahem – rychlé smazání
    with open(SOUBOR_DENIK, "w", encoding="utf-8") as f:
        pass
    print("Denik byl smazan.")

# Simulace deníku bez input()
pridej_zaznam("Prvni zaznam – dnes bylo dobre pocasi.")  # input() nahrazeno
pridej_zaznam("Druhy zaznam – ucil jsem se Python.")     # input() nahrazeno
zobraz_denik()
smaz_vse()
zobraz_denik()

# ── Úloha 2: Uložení nákupního seznamu do souboru ────────────────────────────

nakup = ["mléko", "chleb", "maslo", "jablka", "syr"]   # seznam z lekce 7
with open(SOUBOR_NAKUP, "w", encoding="utf-8") as f:
    for polozka in nakup:
        f.write(polozka + "\n")
print(f"\nNakupni seznam ulozen do '{SOUBOR_NAKUP}'.")

# ── Úloha 3: Průměrná délka slov v souboru ───────────────────────────────────

with open(SOUBOR_NAKUP, "r", encoding="utf-8") as f:
    slova = [radek.strip() for radek in f if radek.strip()]

if slova:
    delky = [len(s) for s in slova]
    # sum() / len() je přímočarý způsob průměru bez importu statistics
    prumer = sum(delky) / len(delky)
    print(f"Prumerna delka slov v nakupnim seznamu: {prumer:.1f} znaku")

# Úklid dočasných souborů
for soubor in ["reseni_poznamky.txt", SOUBOR_DENIK, SOUBOR_NAKUP]:
    if os.path.exists(soubor):
        os.remove(soubor)
