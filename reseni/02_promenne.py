"""Řešení – Lekce 02: Proměnné"""

# 1. Vlastní hodnoty
jmeno = "Ondra"
vek = 12
oblibene_zvire = "kočka"

print(f"Ahoj! Jsem {jmeno} a je mi {vek} let.")

# 2. Přidání proměnné oblibene_jidlo
oblibene_jidlo = "pizza"
print(f"Moje oblíbené jídlo je {oblibene_jidlo}.")

# 3. Co se stane při print(Jmeno)?
# → NameError: name 'Jmeno' is not defined
# Python rozlišuje velká a malá písmena!
# Proměnná se jmenuje 'jmeno' (malé j), ne 'Jmeno'.
try:
    print(Jmeno)
except NameError as e:
    print(f"Chyba: {e}")
