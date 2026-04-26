"""
LEKCE 17: Věda a vesmír (a výpočet černé díry)
================================================
Python umí počítat vesmírné věci!
Modul `math` obsahuje matematické funkce a konstanty.
"""

import math

print("=== Modul math ===")
print(f"π (pí)         = {math.pi}")
print(f"e (Eulerovo)   = {math.e}")
print(f"√2             = {math.sqrt(2)}")
print(f"sin(90°)       = {math.sin(math.radians(90))}")
print(f"log10(1000)    = {math.log10(1000)}")

print("\n=== Výpočet černé díry ===")
print("(Tohle se OPRAVDU počítá takhle!)")
print()

# Schwarzschildův poloměr: r = 2 * G * M / c²
G = 6.674e-11    # gravitační konstanta (m³ kg⁻¹ s⁻²)
c = 3e8          # rychlost světla (m/s)

def schwarzschild(hmotnost_kg):
    return 2 * G * hmotnost_kg / c**2

# Příklady
objekty = {
    "Slunce":       1.989e30,
    "Země":         5.972e24,
    "Měsíc":        7.342e22,
    "slon":         5000,
    "10leté dítě":  35,
    "mravenec":     0.001,
}

for nazev, kg in objekty.items():
    r = schwarzschild(kg)
    if r < 1e-15:
        popis = f"{r:.2e} m  (menší než proton, takže klid)"
    elif r < 0.001:
        popis = f"{r:.2e} m  (mikroskopické)"
    elif r < 1:
        popis = f"{r*100:.4f} cm"
    elif r < 1000:
        popis = f"{r:.2f} m"
    else:
        popis = f"{r/1000:.2f} km"
    print(f"  {nazev:<20} → černá díra o poloměru {popis}")

print()
print("Závěr: Mravenec jako černá díra by byl menší než atomové jádro.")
print("       Fyzici to nazývají 'bezpečné'. My to nazýváme 'vtipné'.")

print("\n=== Tvoje vlastní černá díra ===")
hmotnost = float(input("Zadej svoji hmotnost v kg: "))
r = schwarzschild(hmotnost)
print(f"\nKdybys byl/a černá díra, tvůj poloměr by byl: {r:.2e} metrů")
print(f"To je {r / 1e-15:.1f}× větší než proton.")
print("Závěr: Jsi v bezpečí. Prozatím.")

print("\n=== Další vesmírná čísla ===")
vek_vesmiru_s = 13.8e9 * 365.25 * 24 * 3600
print(f"Věk vesmíru v sekundách: {vek_vesmiru_s:.2e}")

vzdalenost_proxima = 4.243 * 9.461e15   # světelné roky na metry
print(f"Proxima Centauri:        {vzdalenost_proxima:.2e} metrů")

print(f"Rychlostí 100 km/h bys tam dojel za: "
      f"{vzdalenost_proxima / (100000/3.6) / 3600 / 24 / 365:.0f} let")
print("Doporučujeme vzít si svačinu.")

# TVOJE ÚLOHA:
# 1. Spočítej, kolik sekund ti je (vek_roky * 365.25 * 24 * 3600).
# 2. Spočítej obvod Země (poloměr = 6 371 km, vzorec: 2 * π * r).
# 3. Přidej do tabulky "meteorit (500 kg)" a "černá díra v centru Galaxie (4e6 sluncí)".
