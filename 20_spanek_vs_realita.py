"""
LEKCE 20: Optimální čas na spaní vs. realita
==============================================
Učíme se: datetime, časové výpočty, grafy v textu.
Výsledky jsou klinicky přesné. (Nejsou.)
"""

from datetime import datetime, timedelta
import random

DOPORUCENI = {
    (5, 7):   ("19:30", 11),
    (8, 9):   ("20:30", 10),
    (10, 12): ("21:00", 9),
    (13, 17): ("22:00", 8),
    (18, 25): ("23:00", 8),
    (26, 64): ("23:30", 7),
    (65, 99): ("22:00", 8),
}

print("=" * 54)
print("  SPÁNKOVÝ INSTITUT REPUBLIKY")
print("  Analýza spánkového deficitu – individuální zpráva")
print("=" * 54)

jmeno = input("\nJméno pacienta: ")
vek = int(input("Věk: "))
vstavaní = input("V kolik obvykle vstáváš? (HH:MM, např. 06:30): ")
ulehani = input("V kolik reálně chodíš spát? (HH:MM, např. 23:15): ")
zamysene = input("V kolik by ses chtěl/a chodit spát? (HH:MM): ")

# Zjistíme doporučení
doporuceny_cas = "22:00"
doporucena_delka = 9

for rozsah, (cas, delka) in DOPORUCENI.items():
    if rozsah[0] <= vek <= rozsah[1]:
        doporuceny_cas = cas
        doporucena_delka = delka
        break

# Výpočty
fmt = "%H:%M"
t_vstani   = datetime.strptime(vstavaní, fmt)
t_ulehani  = datetime.strptime(ulehani, fmt)
t_zamysl   = datetime.strptime(zamysene, fmt)
t_doporuc  = datetime.strptime(doporuceny_cas, fmt)

# Spánek přes půlnoc
def delka_spanku(usp, vst):
    delta = vst - usp
    if delta.total_seconds() < 0:
        delta += timedelta(days=1)
    return delta.total_seconds() / 3600

skutecny    = delka_spanku(t_ulehani, t_vstani)
zamysleny   = delka_spanku(t_zamysl, t_vstani)
doporuceny  = delka_spanku(t_doporuc, t_vstani)

deficit_den = doporucena_delka - skutecny
deficit_rok = deficit_den * 365

print(f"\n{'─'*54}")
print(f"  ZPRÁVA PRO: {jmeno.upper()}, {vek} let")
print(f"{'─'*54}")
print(f"  Vstávání:             {vstavaní}")
print(f"  Reálné ulehání:       {ulehani}  → {skutecny:.1f} h spánku")
print(f"  Zamýšlené ulehání:    {zamysene}  → {zamysleny:.1f} h spánku")
print(f"  Doporučené ulehání:   {doporuceny_cas}  → {doporuceny:.1f} h spánku")
print(f"  Denní deficit:        {deficit_den:+.1f} h")

print(f"\n  Za rok ztrácíš přibližně {abs(deficit_rok):.0f} hodin spánku.")
print(f"  To jsou {abs(deficit_rok)/24:.1f} dní. Celých dní. Ze života.")

# Humorné zhodnocení
print(f"\n{'─'*54}")
print("  DIAGNÓZA:")
if skutecny >= doporucena_delka:
    print("  Spíš dostatečně. Blahopřejeme. Jsi vzácný úkaz.")
elif deficit_den < 1:
    print("  Mírný deficit. Zvládnutelné, pokud nezačneš sledovat")
    print("  seriály. (Začneš sledovat seriály.)")
elif deficit_den < 2:
    print("  Středně závažný stav. Káva nepomůže. Ale pijeme ji dál.")
else:
    print("  Vážný spánkový dluh. Přesto čteš tento program.")
    print("  Oceňujeme oddanost. Jdi spát.")

# Graf porovnání
print(f"\n{'─'*54}")
print("  VIZUALIZACE (každá █ = 30 minut):")

def graf(nazev, hodiny, max_h=12):
    bloky = int(hodiny * 2)
    print(f"  {nazev:<14} {'█'*bloky} {hodiny:.1f}h")

graf("Skutečnost", skutecny)
graf("Záměr", zamysleny)
graf("Doporučení", doporucena_delka)

# Kolik scrollování by nahradilo spánek
scroly = int(deficit_rok * 60 / 1.5)  # průměr 1.5s na scroll
print(f"\n  Za rok ušetříš {scroly:,} scrollů sociálních sítí.")
print("  Nebo jeden výborný román týdně.")
print("  Volba je na tobě. (Scrolluješ dál.)")

print(f"\n  Zpráva vystavena: {datetime.now().strftime('%d.%m.%Y %H:%M')}")
print("  Spánkový institut nenese odpovědnost za ospalost")
print("  vzniklou čtením této zprávy.")

# TVOJE ÚLOHA:
# 1. Přidej výpočet: za kolik let se deficit "nasčítá" na celý měsíc?
# 2. Přidej možnost zadat spánek o víkendu zvlášť a porovnat.
# 3. Přidej "spánkové tipy" – vypiš náhodný tip z připraveného seznamu.
