"""Řešení – Lekce 04: Python jako kalkulačka"""

# 1. Kolik hodin je v týdnu?
hodiny_v_tydnu = 7 * 24
# násobení je základní aritmetická operace, Python ji provede okamžitě
print(f"Hodin v týdnu: {hodiny_v_tydnu}")

# 2. Kolik sekund je v hodině?
sekund_v_hodine = 60 * 60
# dvě minuty po 60 sekundách – prostý součin
print(f"Sekund v hodině: {sekund_v_hodine}")

# 3. Kalkulačka rozšířená o mocninu
cislo1 = 5.0    # input() nahrazeno: "Zadej první číslo"
cislo2 = 3.0    # input() nahrazeno: "Zadej druhé číslo"

print(f"\n=== Kalkulačka ===")
print(f"{cislo1} + {cislo2} = {cislo1 + cislo2}")
print(f"{cislo1} - {cislo2} = {cislo1 - cislo2}")
print(f"{cislo1} * {cislo2} = {cislo1 * cislo2}")

if cislo2 != 0:
    print(f"{cislo1} / {cislo2} = {cislo1 / cislo2}")
else:
    print("Dělení nulou nejde!")

# operátor ** provede umocnění: základ ^ exponent
print(f"{cislo1} ** {cislo2} = {cislo1 ** cislo2}")
