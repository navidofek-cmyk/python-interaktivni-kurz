"""Řešení – Lekce 19: Vědecký průzkum ledničky"""

print("=" * 52)
print("  USTAV PRO VYZKUM DOMACICH LEDNICEK")
print("  Vyzkumna zprava c. 1 – Obsah a alarmujici trendy")
print("=" * 52)

# Úloha 1: skutečná (rozšířená) lednicka
LEDNICKA = {
    "jogurt (prosly)":       3,
    "kecup (skoro prazdny)": 1,
    "zelenina (zamer)":      2,
    "limonada":              8,
    "zbytky od pondeli":     1,
    "syr":                   4,
    "vajicka":               6,
    "maslo":                 1,
    "zahadna nadoba":        1,
    "zelenina (skutecnost)": 0,
    # vlastní položky:
    "cola":                  4,
    "cokolada":              2,
    "hummus":                1,
}

celkem = sum(LEDNICKA.values())

print(f"\nCelkovy pocet polozek: {celkem}")
print(f"Z toho zelenina (zamer vs. skutecnost): 2 vs. 0")
print(f"Efektivita zdraveho stravovani: 0 %\n")

print("OBSAH LEDNICKE (sloupcovy graf):")
print("─" * 52)

# sorted() + lambda vrátí nový seřazený seznam bez změny originálu
serazeno = sorted(LEDNICKA.items(), key=lambda x: x[1], reverse=True)

for polozka, pocet in serazeno:
    procent = pocet / celkem * 100 if celkem > 0 else 0
    sloupec = "=" * pocet
    print(f"  {polozka:<30} {sloupec:<10} {pocet} ks ({procent:.0f}%)")

print("─" * 52)
print(f"  {'CELKEM':<30} {'':10} {celkem} ks")

# ── Úloha 2: kolik % tvoří sladké věci vs. zdravé ────────────────────────────
sladke_klice  = {"limonada", "cola", "cokolada", "jogurt (prosly)"}
zdrave_klice  = {"zelenina (skutecnost)", "zelenina (zamer)", "vajicka", "hummus"}

pocet_sladke = sum(LEDNICKA.get(k, 0) for k in sladke_klice)
pocet_zdrave = sum(LEDNICKA.get(k, 0) for k in zdrave_klice)

# procenta z celku – zaokrouhlení na 1 desetinné místo
pct_sladke = pocet_sladke / celkem * 100 if celkem else 0
pct_zdrave = pocet_zdrave / celkem * 100 if celkem else 0

print(f"\nSladke veci: {pocet_sladke} ks = {pct_sladke:.1f} %")
print(f"Zdrave veci: {pocet_zdrave} ks = {pct_zdrave:.1f} %")

# ── Úloha 3: funkce doporuceni() ─────────────────────────────────────────────

def doporuceni(lednicka):
    """Navrhne co koupit, pokud chybí základní potraviny."""
    potreba = []
    # kontrola nezbytností – get() s výchozí hodnotou 0 zabrání KeyError
    if lednicka.get("mleko", 0) == 0:
        potreba.append("mleko")
    if lednicka.get("vajicka", 0) < 2:
        potreba.append("vajicka")
    if lednicka.get("ovoce", 0) == 0:
        potreba.append("ovoce")
    if potreba:
        print(f"\nDOPORUCUJEME KOUPIT: {', '.join(potreba)}")
    else:
        print("\nLednicka je zasobena. Gratuluji.")

doporuceni(LEDNICKA)

print("\nALARMUJICI ZJISTENI:")
if LEDNICKA.get("zbytky od pondeli", 0) > 0:
    print("  Zbytky od pondeli detekovany. Doporucujeme akci.")
if LEDNICKA.get("zahadna nadoba", 0) > 0:
    print("  Zahadna nadoba: neotvirat bez vedeckeho dohledu.")
if LEDNICKA.get("zelenina (skutecnost)", 0) == 0:
    print("  Zelenina: zamer pretrvava, realizace odlozena.")

print("\nZprava vygenerovana automaticky.")
