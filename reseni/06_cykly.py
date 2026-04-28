"""Řešení – Lekce 06: Cykly"""

# 1. Násobilka čísla 7
print("Násobilka 7:")
for i in range(1, 11):
    print(f"  7 × {i:2d} = {7*i}")

# 2. Odpočítávání od čísla zadaného uživatelem
cislo = int(input("Od kolika odpočítat? "))
for i in range(cislo, 0, -1):
    print(i, "...")
print("ŠTART! 🚀")

# 3. Součet čísel od 1 do 100
soucet = 0
for i in range(1, 101):
    soucet += i
print(f"\nSoučet 1–100 = {soucet}")
# Gaussův vzorec pro ověření: n*(n+1)/2
print(f"Ověření vzorcem: {100*101//2}")
