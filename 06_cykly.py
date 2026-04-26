"""
LEKCE 6: Cykly – opakování bez nudy
======================================
Místo abys psal print() stokrát, nechej Python to zopakovat!
"""

print("=== FOR cyklus ===")
for i in range(5):
    print(f"Kolo číslo {i + 1}")

print("\n=== Odpočítávání ===")
for i in range(10, 0, -1):
    print(i, "...")
print("ŠTART! 🚀")

print("\n=== While cyklus ===")
# while běží, DOKUD je podmínka pravdivá
pocet = 0
while pocet < 5:
    print(f"Dřep číslo {pocet + 1}")
    pocet = pocet + 1
print("Hotovo! Výborně!")

print("\n=== Hádací hra s nápovědou ===")
tajne = 42
pokusy = 0

while True:
    hadani = int(input("Hádej číslo (1-100): "))
    pokusy += 1

    if hadani == tajne:
        print(f"VÝHRA! Uhodl jsi za {pokusy} pokusů!")
        break
    elif hadani < tajne:
        print("Více!")
    else:
        print("Méně!")

# TVOJE ÚLOHA:
# 1. Vytiskni násobilku čísla 7 (7*1 až 7*10).
# 2. Udělej odpočítávání od čísla, které zadá uživatel.
# 3. Spočítej součet čísel od 1 do 100 pomocí cyklu.
