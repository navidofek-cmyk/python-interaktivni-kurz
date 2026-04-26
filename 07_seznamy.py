"""
LEKCE 7: Seznamy – více věcí najednou
=======================================
Seznam je jako tašku, do které dáš víc věcí.
"""

ovoce = ["jablko", "banán", "jahoda", "meloun", "hrozno"]

print("Moje ovoce:", ovoce)
print("První ovoce:", ovoce[0])       # indexy začínají od 0!
print("Poslední ovoce:", ovoce[-1])   # -1 = poslední
print("Počet druhů:", len(ovoce))

print("\n--- Procházení seznamu ---")
for o in ovoce:
    print(f"Mám ráda {o}!")

print("\n--- Přidávání a odebírání ---")
ovoce.append("pomeranč")         # přidej na konec
print("Po přidání:", ovoce)

ovoce.remove("banán")            # odeber konkrétní
print("Po odebrání banánu:", ovoce)

print("\n--- Třídění ---")
ovoce.sort()
print("Abecedně:", ovoce)

print("\n=== Nákupní seznam ===")
nakup = []
print("Přidej věci do nákupu (prázdný vstup = konec):")

while True:
    vec = input("Přidej věc: ")
    if vec == "":
        break
    nakup.append(vec)

print("\nTvůj nákupní seznam:")
for i, vec in enumerate(nakup, 1):
    print(f"  {i}. {vec}")

# TVOJE ÚLOHA:
# 1. Vytvoř seznam svých 5 oblíbených filmů.
# 2. Přidej film na konec a vytiskni celý seznam.
# 3. Zjisti, jestli je "Minecraft" v tvém seznamu her (pomocí `in`).
