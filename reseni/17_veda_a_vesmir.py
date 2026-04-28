"""Řešení – Lekce 17: Věda a vesmír (a výpočet černé díry)"""

import math

G = 6.674e-11    # gravitační konstanta (m³ kg⁻¹ s⁻²)
c = 3e8          # rychlost světla (m/s)


def schwarzschild(hmotnost_kg):
    """Schwarzschildův poloměr černé díry dané hmotnosti."""
    # vzorec r = 2GM/c² – základ obecné teorie relativity
    return 2 * G * hmotnost_kg / c**2


# ── Úloha 1: Kolik sekund mi je? ─────────────────────────────────────────────
vek_roky = 13   # input() nahrazeno: věk v letech
sekund = vek_roky * 365.25 * 24 * 3600
# 365.25 zohledňuje přestupné roky (průměr)
print(f"Je mi {vek_roky} let = přibližně {sekund:.2e} sekund")

# ── Úloha 2: Obvod Země ───────────────────────────────────────────────────────
polomer_zeme_km = 6371
# vzorec obvodu kružnice: 2 * π * r
obvod_zeme = 2 * math.pi * polomer_zeme_km
print(f"Obvod Země: {obvod_zeme:.2f} km  (~{obvod_zeme:.0f} km)")

# ── Úloha 3: Rozšíření tabulky o meteorit a supermasivní černou díru ─────────
objekty = {
    "Slunce":                          1.989e30,
    "Zeme":                            5.972e24,
    "Mesic":                           7.342e22,
    "slon":                            5000,
    "10lete dite":                     35,
    "mravenec":                        0.001,
    # nové položky:
    "meteorit (500 kg)":               500,
    "cerna dira v centru Galaxie":     4e6 * 1.989e30,   # 4 miliony hmotností Slunce
}

print("\n=== Tabulka Schwarzschildových poloměrů ===")
for nazev, kg in objekty.items():
    r = schwarzschild(kg)
    if r < 1e-15:
        popis = f"{r:.2e} m  (mensi nez proton)"
    elif r < 0.001:
        popis = f"{r:.2e} m  (mikroskopicke)"
    elif r < 1:
        popis = f"{r*100:.4f} cm"
    elif r < 1000:
        popis = f"{r:.2f} m"
    else:
        popis = f"{r/1000:.2f} km"
    print(f"  {nazev:<40} -> cerna dira o polomeru {popis}")

# ── Bonus: vlastní černá díra ─────────────────────────────────────────────────
hmotnost = 60.0   # input() nahrazeno: hmotnost v kg
r = schwarzschild(hmotnost)
print(f"\nKdybys vazil/a {hmotnost} kg jako cerna dira: {r:.2e} metru")
print(f"To je {r / 1e-15:.1f}x vetsi nez proton.")
print("Zaver: Jsi v bezpeci. Prozatim.")
