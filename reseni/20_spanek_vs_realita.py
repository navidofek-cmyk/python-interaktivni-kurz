"""Řešení – Lekce 20: Optimální čas na spaní vs. realita"""

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

# Spánkové tipy pro úlohu 3
TIPY = [
    "Vyhni se obrazovkam 30 minut pred spanim.",
    "Choď spat a vstavaj ve stejny cas i o vikendu.",
    "Drž loznici chladnou (~18 °C je ideal).",
    "Vyhni se kafein po 14:00.",
    "Kratka procházka ráno zlepší biorytmus.",
    "Tmave zavesy nebo maska na oci pomohou s kvalitou spanku.",
]

print("=" * 54)
print("  SPANKOVY INSTITUT REPUBLIKY")
print("  Analyza spankoveho deficitu – individualni zprava")
print("=" * 54)

# input() nahrazeny hardcoded hodnotami
jmeno    = "Adam"    # input() nahrazeno: "Jméno pacienta"
vek      = 14        # input() nahrazeno: "Věk"
vstavaní = "06:30"   # input() nahrazeno: "V kolik vstáváš?"
ulehani  = "23:15"   # input() nahrazeno: "V kolik reálně chodíš spát?"
zamysene = "22:00"   # input() nahrazeno: "V kolik bys chtěl/a chodit spát?"

# Určíme doporučení podle věku
doporuceny_cas = "22:00"
doporucena_delka = 9
for rozsah, (cas, delka) in DOPORUCENI.items():
    if rozsah[0] <= vek <= rozsah[1]:
        doporuceny_cas = cas
        doporucena_delka = delka
        break

fmt = "%H:%M"
t_vstani  = datetime.strptime(vstavaní, fmt)
t_ulehani = datetime.strptime(ulehani, fmt)
t_zamysl  = datetime.strptime(zamysene, fmt)
t_doporuc = datetime.strptime(doporuceny_cas, fmt)


def delka_spanku(usp, vst):
    """Vypočítá délku spánku v hodinách, správně zvládne přesah přes půlnoc."""
    delta = vst - usp
    if delta.total_seconds() < 0:
        delta += timedelta(days=1)
    return delta.total_seconds() / 3600


skutecny   = delka_spanku(t_ulehani, t_vstani)
zamysleny  = delka_spanku(t_zamysl,  t_vstani)
doporuceny = delka_spanku(t_doporuc, t_vstani)

deficit_den = doporucena_delka - skutecny
deficit_rok = deficit_den * 365

print(f"\n{'─'*54}")
print(f"  ZPRAVA PRO: {jmeno.upper()}, {vek} let")
print(f"{'─'*54}")
print(f"  Vstávani:             {vstavaní}")
print(f"  Realne ulehani:       {ulehani}  -> {skutecny:.1f} h spanku")
print(f"  Zamyslene ulehani:    {zamysene}  -> {zamysleny:.1f} h spanku")
print(f"  Doporucene ulehani:   {doporuceny_cas}  -> {doporuceny:.1f} h spanku")
print(f"  Denni deficit:        {deficit_den:+.1f} h")
print(f"\n  Za rok ztracis priblizne {abs(deficit_rok):.0f} hodin spanku.")
print(f"  To jsou {abs(deficit_rok)/24:.1f} dni. Celych dni. Ze zivota.")

# ── Diagnóza ──────────────────────────────────────────────────────────────────
print(f"\n{'─'*54}")
print("  DIAGNOZA:")
if skutecny >= doporucena_delka:
    print("  Spis dostatecne. Blahopreji. Jsi vzacny ukaz.")
elif deficit_den < 1:
    print("  Mirny deficit. Zvladnutelne, pokud nezacnes sledovat serialy.")
elif deficit_den < 2:
    print("  Stredne zavazny stav. Kava nepomuze. Ale pijeme ji dal.")
else:
    print("  Vazny spankovy dluh. Presto ctes tento program.")
    print("  Ocenujeme oddanost. Jdi spat.")

# ── Graf ─────────────────────────────────────────────────────────────────────
print(f"\n{'─'*54}")
print("  VIZUALIZACE (kazda = = 30 minut):")


def graf(nazev, hodiny):
    bloky = int(hodiny * 2)
    print(f"  {nazev:<14} {'='*bloky} {hodiny:.1f}h")


graf("Skutecnost", skutecny)
graf("Zamer", zamysleny)
graf("Doporuceni", doporucena_delka)

# ── Úloha 1: za kolik let se deficit nasčítá na celý měsíc ───────────────────
if deficit_den > 0:
    # 30 dní × 24 hodin = 720 hodin = jeden měsíc
    let_na_mesic = (30 * 24) / (deficit_den * 365)
    print(f"\n  Za {let_na_mesic:.1f} let se deficit nasčítá na cely mesic.")
else:
    print("\n  Zadny deficit – mesicni ztratu nemusis resit.")

# ── Úloha 2: spánek o víkendu zvlášť ─────────────────────────────────────────
ulehani_vikend  = "00:30"   # input() nahrazeno: "V kolik chodíš spát o víkendu?"
vstavaní_vikend = "09:00"   # input() nahrazeno: "V kolik vstáváš o víkendu?"

t_uleh_v = datetime.strptime(ulehani_vikend, fmt)
t_vst_v  = datetime.strptime(vstavaní_vikend, fmt)
vikend_hodin = delka_spanku(t_uleh_v, t_vst_v)

print(f"\n  Srovnani spanku:")
print(f"  Pracovni dny: {skutecny:.1f} h  |  Vikend: {vikend_hodin:.1f} h")
# timedelta zobrazí rozdíl – kladný = víkend je delší, záporný = kratší
rozdil = vikend_hodin - skutecny
print(f"  Rozdil: {rozdil:+.1f} h (vikend vs. pracovni dny)")

# ── Úloha 3: náhodný spánkový tip ─────────────────────────────────────────────
# random.choice() = rovnoměrný výběr z libovolného seznamu
tip = random.choice(TIPY)
print(f"\n  SPANKOVY TIP DNE:")
print(f"  {tip}")

scroly = int(deficit_rok * 60 / 1.5)
print(f"\n  Za rok ušetris {scroly:,} scrollu socialnich siti.")
print("  Volba je na tobe. (Scrollujes dal.)")
print(f"\n  Zprava vystavena: {datetime.now().strftime('%d.%m.%Y %H:%M')}")
