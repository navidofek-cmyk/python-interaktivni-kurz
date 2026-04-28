"""Řešení – Lekce 05: Rozhodování – if / elif / else"""

# 1. Podmínka: pokud věk == 10, vypiš "Přesně deset!"
vek = 10    # input() nahrazeno: "Kolik ti je let?"

if vek < 6:
    print("Jsi miminko!")
elif vek == 10:
    # přesná rovnost se testuje dvěma rovnítky ==, ne jedním
    print("Přesně deset!")
elif vek < 10:
    print("Jsi malé dítě.")
elif vek < 13:
    print("Jsi školák!")
elif vek < 18:
    print("Jsi teenager.")
else:
    print("Jsi dospělý!")

# 2. Je číslo sudé nebo liché?
cislo = 7   # input() nahrazeno: "Zadej číslo"
# operátor % vrátí zbytek po dělení; sudé číslo má zbytek 0
if cislo % 2 == 0:
    print(f"{cislo} je sudé.")
else:
    print(f"{cislo} je liché.")

# 3. Jaké počasí? – teplota doporučuje oblečení
teplota = 5   # input() nahrazeno: "Jaká je teplota ve stupních?"
# řetězec elif větví pokrývá celou škálu teplot přehledně
if teplota < 0:
    print("Je mrzák! Vlož si teplo oblečení, čepici a rukavice.")
elif teplota < 10:
    print("Je zima. Vezmi si kabát a šálu.")
elif teplota < 18:
    print("Je svěže. Mikina se hodí.")
elif teplota < 25:
    print("Pěkné počasí! Tričko bohatě stačí.")
else:
    print("Vedro! Kraťasy a hodně vody.")
