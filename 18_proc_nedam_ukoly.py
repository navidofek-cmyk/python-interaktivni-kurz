"""
LEKCE 18: Analýza důvodů, proč nejsou hotové domácí úkoly
============================================================
Učíme se: náhoda (random), statistiky, grafy v textu.
Vědecky podložená data. Rozhodně.
"""

import random
import statistics

DUVODY = [
    "Snědl to pes.",
    "Foukal vítr a odnesl ho z okna.",
    "Byl jsem nemocný. (Zítra.)",
    "Myslel jsem, že dnes není škola.",
    "Udělal jsem ho, ale zapomněl doma.",
    "Netušil jsem, že ho máme.",
    "Můj mladší sourozenec ho zničil.",
    "Přišel výpadek proudu přesně když jsem začal.",
    "Myslel jsem, že to bylo dobrovolné.",
    "Udělám ho o přestávce. (Řekl jsem si v neděli.)",
]

print("=" * 55)
print("  VĚDECKÁ ANALÝZA: DOMÁCÍ ÚKOLY A JEJICH NEPŘÍTOMNOST")
print("=" * 55)

jmeno = input("\nJméno studenta (pro vědecké účely): ")
predmet = input("Předmět: ")

print(f"\nDěkujeme, {jmeno}. Zpracováváme data...\n")

# Náhodný důvod
duvod = random.choice(DUVODY)
print(f'Doporučený důvod pro {predmet}:\n  "{duvod}"\n')
print("Pravděpodobnost, že to učitel uvěří:",
      f"{random.randint(2, 15)} %")
print("Pravděpodobnost poznámky do žákovské:",
      f"{random.randint(70, 99)} %\n")

print("─" * 55)
print("STATISTICKÁ ČÁST – zadej časy, kdy jsi měl/a úkol udělat")
print("(v minutách, zadávej dokud nenapíšeš 0)\n")

casy = []
while True:
    try:
        c = int(input(f"  Minuta číslo {len(casy)+1} (0 = hotovo): "))
        if c == 0:
            break
        casy.append(c)
    except ValueError:
        print("  Zadej číslo.")

if casy:
    print(f"\nZadal/a jsi {len(casy)} záznamů.")
    print(f"Průměr:  {statistics.mean(casy):.1f} min")
    print(f"Medián:  {statistics.median(casy):.1f} min")
    print(f"Minimum: {min(casy)} min  |  Maximum: {max(casy)} min")
    celkem = sum(casy)
    print(f"Celkem:  {celkem} min = {celkem/60:.1f} hodin")

    # Textový sloupcový graf
    print("\nGraf (každá █ = 5 minut):")
    for i, c in enumerate(casy, 1):
        sloupec = "█" * (c // 5) + ("▌" if c % 5 >= 3 else "")
        print(f"  Záznam {i:2d}: {sloupec} ({c} min)")

    if celkem > 120:
        print("\nZávěr: Tolik času na úkol? Gratuluji k odhodlání.")
        print("        (Nebo jsi zapomněl stisknout stop.)")
    else:
        print("\nZávěr: Strávil/a jsi více času nad tímto programem")
        print("        než nad samotným úkolem. Efektivita.")
else:
    print("\nŽádná data. Věda mlčí.")

print("\n" + "─" * 55)
print("VĚDECKÝ ZÁVĚR:")
print("Domácí úkoly jsou korelované s výskytem náhlé ospalosti,")
print("neodolatelných zpráv od kamarádů a urgentní potřeby")
print("reorganizovat celý pokoj.")
print("\nTato studie byla financována: nikým. Proto je zadarmo.")

# TVOJE ÚLOHA:
# 1. Přidej vlastní 3 důvody do seznamu DUVODY.
# 2. Přidej "pravděpodobnost přežití" (random.randint) různých předmětů.
# 3. Spočítej, kolik dní by trvalo úkol udělat tempem 10 min/den.
