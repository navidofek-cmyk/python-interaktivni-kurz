"""Řešení – Lekce 03: Python se ptá tebe!"""

# 1. Přidej otázku na oblíbené jídlo
jmeno = "Míša"            # input() nahrazeno: "Jak se jmenuješ?"
print(f"Ahoj, {jmeno}! Vítej v Pythonu!")

oblibena_barva = "modrá"  # input() nahrazeno: "Jaká je tvoje oblíbená barva?"
print(f"Oooh, {oblibena_barva} je super barva!")

oblibene_jidlo = "pizza"  # input() nahrazeno: "Jaké je tvoje oblíbené jídlo?"
# input() vrací text – proto stačí přiřadit do proměnné a vypsat
print(f"Pizza nebo zelenina? Ty si vybral/a {oblibene_jidlo}, skvělý vkus!")

# 2. Ukázka chyby při zadání písmene místo čísla věku
vek_text = "deset"        # input() nahrazeno: "Kolik ti je let?"
try:
    vek = int(vek_text)
except ValueError as e:
    # int() vyhodí ValueError, pokud dostane text místo číslice
    print(f"Chyba: '{vek_text}' není číslo – Python hlásí: {e}")

# 3. Dotazník o kamarádovi – 3 otázky a výpis na konci
kamarad_jmeno    = "Tomáš"   # input() nahrazeno: "Jak se jmenuje tvůj kamarád?"
kamarad_obliba   = "fotbal"  # input() nahrazeno: "Co ho baví?"
kamarad_mesto    = "Brno"    # input() nahrazeno: "Odkud pochází?"

# f-string spojí všechny hodnoty do přehledné zprávy najednou
print(f"\n--- Dotazník o kamarádovi ---")
print(f"Jméno:   {kamarad_jmeno}")
print(f"Záliby:  {kamarad_obliba}")
print(f"Město:   {kamarad_mesto}")
