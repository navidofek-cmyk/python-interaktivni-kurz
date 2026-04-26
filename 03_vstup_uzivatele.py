"""
LEKCE 3: Python se ptá tebe!
==============================
Pomocí input() můžeš dát uživateli otázku a uložit odpověď.
"""

jmeno = input("Jak se jmenuješ? ")
print(f"Ahoj, {jmeno}! Vítej v Pythonu!")

oblibena_barva = input("Jaká je tvoje oblíbená barva? ")
print(f"Oooh, {oblibena_barva} je super barva!")

# Čísla z input() jsou vždy text – musíme je převést!
vek = int(input("Kolik ti je let? "))
pristi_rok = vek + 1
print(f"Příští rok ti bude {pristi_rok} let.")

# TVOJE ÚLOHA:
# 1. Přidej otázku na oblíbené jídlo.
# 2. Zkus zadat písmeno místo čísla věku – co se stane?
# 3. Vytvoř "dotazník o kamarádovi" se 3 otázkami a výpisem na konci.
