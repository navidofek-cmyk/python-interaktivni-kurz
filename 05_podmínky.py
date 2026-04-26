"""
LEKCE 5: Rozhodování – if / elif / else
=========================================
Python se umí rozhodovat podle toho, co je pravda.
"""

vek = int(input("Kolik ti je let? "))

if vek < 6:
    print("Jsi miminko!")
elif vek < 10:
    print("Jsi malé dítě.")
elif vek < 13:
    print("Jsi školák!")
elif vek < 18:
    print("Jsi teenager.")
else:
    print("Jsi dospělý!")

print("\n=== Hádání čísla ===")
tajne = 7
hadani = int(input("Hádej číslo od 1 do 10: "))

if hadani == tajne:
    print("SPRÁVNĚ! Jsi skvělý!")
elif hadani < tajne:
    print("Moc málo! Zkus větší číslo.")
else:
    print("Moc velké! Zkus menší číslo.")

# TVOJE ÚLOHA:
# 1. Přidej podmínku: pokud věk == 10, vypiš "Přesně deset!"
# 2. Udělej program "Je číslo sudé nebo liché?" (nápověda: % 2)
# 3. Udělej program "Jaké počasí?" – ptá se na teplotu a radí oblečení.
