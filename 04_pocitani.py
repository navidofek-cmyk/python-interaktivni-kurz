"""
LEKCE 4: Python jako kalkulačka
=================================
Python umí počítat lépe než kalkulačka!
"""

print("=== Základní počítání ===")
print(5 + 3)    # sčítání
print(10 - 4)   # odčítání
print(6 * 7)    # násobení
print(15 / 4)   # dělení (výsledek je desetinné číslo)
print(15 // 4)  # dělení celé (zaokrouhlí dolů)
print(15 % 4)   # zbytek po dělení
print(2 ** 10)  # mocnina (2 na 10)

print("\n=== Kalkulačka ===")
cislo1 = float(input("Zadej první číslo: "))
cislo2 = float(input("Zadej druhé číslo: "))

print(f"{cislo1} + {cislo2} = {cislo1 + cislo2}")
print(f"{cislo1} - {cislo2} = {cislo1 - cislo2}")
print(f"{cislo1} * {cislo2} = {cislo1 * cislo2}")

if cislo2 != 0:
    print(f"{cislo1} / {cislo2} = {cislo1 / cislo2}")
else:
    print("Dělení nulou nejde!")

# TVOJE ÚLOHA:
# 1. Spočítej: kolik hodin je v týdnu? (7 * 24)
# 2. Spočítej: kolik sekund je v hodině? (60 * 60)
# 3. Přidej do kalkulačky mocninu (**)
