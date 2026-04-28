"""Řešení – Lekce 28: match/case a walrus operátor :="""

import random
import io
import re


# 1. Přidání case ["utok", cil] do minihrové logiky
# match na split() seznamu umožňuje pattern matching na příkazy

print("=== Minihra s match + útok ===\n")

stav = {"hp": 100, "mana": 50, "inventar": [], "zlato": 0}
nepritel_hp = 80

# simulace vstupu: sekvence příkazů místo opravdového input()
prikazy_simulace = [
    "status",
    "vezmi lektvar",
    "utok drak",
    "lec",
    "utok drak",
    "utok drak",
    "utok drak",
    "status",
    "konec",
]

for cmd in prikazy_simulace:
    print(f"> {cmd}  # simulace vstupu")
    match cmd.split():
        case ["konec"] | ["q"]:
            print("Nashledanou!")
            break
        case ["status"] | ["s"]:
            print(f"  HP: {stav['hp']}  Mana: {stav['mana']}  "
                  f"Inv: {stav['inventar'] or 'prázdný'}  "
                  f"Nepřítel HP: {nepritel_hp}")
        case ["lec"] if stav["mana"] >= 20:
            stav["hp"] = min(100, stav["hp"] + 30)
            stav["mana"] -= 20
            print(f"  Vyléčil ses! HP: {stav['hp']}")
        case ["lec"]:
            print("  Nedostatek many!")
        case ["vezmi", predmet]:
            stav["inventar"].append(predmet)
            print(f"  Sebral jsi: {predmet}")
        case ["pouzij", predmet] if predmet in stav["inventar"]:
            stav["inventar"].remove(predmet)
            stav["hp"] = min(100, stav["hp"] + 50)
            print(f"  Použil jsi {predmet}. HP: {stav['hp']}")
        # 1. Útok na nepřítele – odečteme náhodný damage od HP nepřítele
        # Přidáme i protiútok: nepřítel vrátí menší zásah zpět
        case ["utok", cil]:
            if nepritel_hp <= 0:
                print(f"  {cil} je již poražen!")
            else:
                damage = random.randint(15, 30)
                nepritel_hp -= damage
                print(f"  Útočíš na {cil} za {damage} poškození! "
                      f"({cil} HP: {max(nepritel_hp, 0)})")
                if nepritel_hp <= 0:
                    odmena = random.randint(20, 50)
                    stav["zlato"] += odmena
                    print(f"  {cil} poražen! Získal jsi {odmena} zlatých.")
                else:
                    protiutok = random.randint(8, 18)
                    stav["hp"] = max(0, stav["hp"] - protiutok)
                    print(f"  {cil} vrátil {protiutok} poškození. HP: {stav['hp']}")
        case _:
            print("  Příkazy: status, lec, vezmi <věc>, pouzij <věc>, utok <cíl>, konec")
    print()


# 2. Klasifikace čísla pomocí match
# match porovnává podmínky pomocí guard (if klauzule)

def klasifikuj_cislo(n: int | float) -> str:
    match n:
        case _ if n < 0:
            return f"{n} je záporné"
        case 0:
            return "nula"
        case _ if n < 10:
            return f"{n} je malé (1-9)"
        case _ if n < 1000:
            return f"{n} je velké (10-999)"
        case _:
            return f"{n} je obrovské (≥1000)"


print("=== klasifikuj_cislo() ===")
for n in [-5, 0, 3, 42, 999, 1_000_000]:
    print(f"  {n:>10} → {klasifikuj_cislo(n)}")


# 3. Walrus při čtení bloku dat ze souboru
# while chunk := file.read(1024) opakuje dokud read() vrací neprázdný řetězec

print("\n=== Walrus + čtení bloku (simulace) ===")

# Simulujeme soubor pomocí io.StringIO s delším textem
obsah = "A" * 2500  # 2500 znaků
soubor = io.BytesIO(obsah.encode())

celkem = 0
pocet_bloku = 0
while chunk := soubor.read(1024):  # walrus: přiřadí a zároveň testuje
    pocet_bloku += 1
    celkem += len(chunk)
    print(f"  Blok {pocet_bloku}: přečteno {len(chunk)} bajtů (celkem {celkem})")

print(f"  Hotovo: {pocet_bloku} bloků, {celkem} bajtů celkem")
