"""
LEKCE 19: Vědecký průzkum ledničky
=====================================
Učíme se: slovníky, třídění, procenta, textové grafy.
Data jsou anonymizována. (Nejsou.)
"""

print("=" * 52)
print("  ÚSTAV PRO VÝZKUM DOMÁCÍCH LEDNIČEK")
print("  Výzkumná zpráva č. 1 – Obsah a alarmující trendy")
print("=" * 52)

LEDNICKA = {
    "jogurt (prošlý)":      3,
    "kečup (skoro prázdný)": 1,
    "zelenina (záměr)":     2,
    "limonáda":             8,
    "zbytky od pondělí":    1,
    "sýr":                  4,
    "vajíčka":              6,
    "máslo":                1,
    "záhadná nádoba":       1,
    "zelenina (skutečnost)": 0,
}

celkem = sum(LEDNICKA.values())

print(f"\nCelkový počet položek: {celkem}")
print(f"Z toho zelenina (záměr vs. skutečnost): 2 vs. 0")
print(f"Efektivita zdravého stravování: 0 %\n")

print("OBSAH LEDNIČKY (sloupcový graf):")
print("─" * 52)

serazeno = sorted(LEDNICKA.items(), key=lambda x: x[1], reverse=True)

for polozka, pocet in serazeno:
    procent = pocet / celkem * 100 if celkem > 0 else 0
    sloupec = "█" * pocet
    print(f"  {polozka:<28} {sloupec:<10} {pocet} ks ({procent:.0f}%)")

print("─" * 52)
print(f"  {'CELKEM':<28} {'':10} {celkem} ks")

print("\nALARMUJÍCÍ ZJIŠTĚNÍ:")
if LEDNICKA.get("zbytky od pondělí", 0) > 0:
    print("  ⚠ Zbytky od pondělí detekováno. Doporučujeme akci.")
if LEDNICKA.get("záhadná nádoba", 0) > 0:
    print("  ⚠ Záhadná nádoba: neotevírat bez vědeckého dohledu.")
if LEDNICKA.get("zelenina (skutečnost)", 0) == 0:
    print("  ⚠ Zelenina: záměr přetrvává, realizace odložena.")

print("\n─" * 52)
print("\nPROVEĎ VLASTNÍ PRŮZKUM:")
print("Projdi svou ledničku a zadej obsah.")
print("(Nebo si to vymysli. Věda to nerozezná.)\n")

vlastni = {}
while True:
    polozka = input("Polozka (Enter = konec): ").strip()
    if not polozka:
        break
    try:
        pocet = int(input(f"  Kolik kusů '{polozka}'? "))
        vlastni[polozka] = pocet
    except ValueError:
        print("  Číslo prosím.")

if vlastni:
    celkem2 = sum(vlastni.values())
    print(f"\nTvoje lednicka má {celkem2} položek.")

    nejvetsi = max(vlastni, key=vlastni.get)
    print(f"Dominuje: {nejvetsi} ({vlastni[nejvetsi]} ks)")

    if "zelenina" in " ".join(vlastni.keys()).lower():
        print("Zelenina detekována. Gratulujeme rodičům.")
    else:
        print("Zelenina nenalezena. Výsledky jsou v souladu s průměrem.")
else:
    print("Žádná data. Lednicka zůstává záhadou.")

print("\nZpráva vygenerována automaticky. Vědci nenese zodpovědnost")
print("za záhadné nádoby ani za pocity viny ze zeleniny.")

# TVOJE ÚLOHA:
# 1. Přidej položky ze své skutečné ledničky.
# 2. Spočítej, kolik % tvoří sladké věci vs. zdravé.
# 3. Přidej funkci `doporuceni(lednicka)`, která navrhne,
#    co koupit – pokud chybí mléko, vejce nebo ovoce.
