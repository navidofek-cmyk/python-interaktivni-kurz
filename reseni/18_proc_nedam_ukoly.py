"""Řešení – Lekce 18: Analýza důvodů, proč nejsou hotové domácí úkoly"""

import random
import statistics

# Úloha 1: vlastní 3 důvody přidané do seznamu
DUVODY = [
    "Snedl to pes.",
    "Foukal vitr a odnesl ho z okna.",
    "Byl jsem nemocny. (Zitra.)",
    "Myslel jsem, ze dnes neni skola.",
    "Udelal jsem ho, ale zapomnel doma.",
    "Netusil jsem, ze ho mame.",
    "Muj mladsi sourozenec ho znicil.",
    "Prisel vypadek proudu prave kdyz jsem zacal.",
    "Myslel jsem, ze to bylo dobrovolne.",
    "Udelam ho o prestavce. (Rekl jsem si v nedeli.)",
    # 3 vlastní důvody:
    "Wifi nefungovala a ukol byl online.",
    "Cetl jsem knihu o produktivite misto samotne prace.",
    "Nastavil jsem si budik na 5:00, ale byl to PM.",
]

print("=" * 55)
print("  VEDECKA ANALYZA: DOMACI UKOLY A JEJICH NEPRITOMNOST")
print("=" * 55)

jmeno   = "Jan"       # input() nahrazeno: "Jméno studenta"
predmet = "fyzika"    # input() nahrazeno: "Předmět"

print(f"\nDekujeme, {jmeno}. Zpracovavame data...\n")

# random.choice() vybere náhodný prvek ze seznamu v O(1) – jednoduché a rychlé
duvod = random.choice(DUVODY)
print(f'Doporuceny duvod pro {predmet}:\n  "{duvod}"\n')
print("Pravdepodobnost, ze to ucitel uveri:", f"{random.randint(2, 15)} %")
print("Pravdepodobnost poznamky do zakovske:", f"{random.randint(70, 99)} %\n")

# ── Úloha 2: pravděpodobnost přežití různých předmětů ────────────────────────
print("─" * 55)
print("PRAVDEPODOBNOST PREZITI BEZ UKOLU (predmet → %)")
predmety = ["matematika", "cestina", "fyzika", "dejepis", "telocvik"]
for p in predmety:
    # humor: tělocvik má vždy vysokou šanci přežití
    if p == "telocvik":
        sance = random.randint(70, 95)
    else:
        sance = random.randint(5, 40)
    print(f"  {p:<15} {sance} %")

# ── Statistická část s hardcoded daty ────────────────────────────────────────
print("\n─" * 55)
# input() nahrazeno: předem zadané časy v minutách
casy = [45, 10, 90, 5, 30, 15, 60]
print(f"Zadane casy (v minutach): {casy}")

if casy:
    print(f"\nZadal/a jsi {len(casy)} zaznamu.")
    print(f"Prumer:  {statistics.mean(casy):.1f} min")
    print(f"Median:  {statistics.median(casy):.1f} min")
    print(f"Minimum: {min(casy)} min  |  Maximum: {max(casy)} min")
    celkem = sum(casy)
    print(f"Celkem:  {celkem} min = {celkem/60:.1f} hodin")

    print("\nGraf (kazda blok = 5 minut):")
    for i, c in enumerate(casy, 1):
        sloupec = "=" * (c // 5) + ("+" if c % 5 >= 3 else "")
        print(f"  Zaznam {i:2d}: {sloupec} ({c} min)")

    # ── Úloha 3: kolik dní by trvalo ukol udělat tempem 10 min/den ───────────
    # jednoduchý podíl – celkem minut / minut za den = počet dní
    dni = celkem / 10
    print(f"\nPri tempu 10 min/den by to trvalo {dni:.1f} dni.")

    if celkem > 120:
        print("\nZaver: Tolik casu na ukol? Gratulujeme k odhodlani.")
    else:
        print("\nZaver: Stravil/a jsi vice casu nad timto programem nez nad ukolem.")

print("\n" + "─" * 55)
print("VEDECKY ZAVER:")
print("Domaci ukoly jsou korelovane s vyskytem nahle ospalosti,")
print("neodolatelnych zprav od kamaradu a urgentni potreby")
print("reorganizovat cely pokoj.")
print("\nTato studie byla financovana: nikem. Proto je zadarmo.")
