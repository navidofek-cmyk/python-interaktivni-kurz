"""Řešení – Lekce 07: Seznamy – více věcí najednou"""

# 1. Seznam 5 oblíbených filmů
filmy = ["Avengers", "Inception", "Interstellar", "The Matrix", "Toy Story"]
# seznam je indexovaný od 0, uchovává pořadí a umožňuje duplicity
print("Oblíbené filmy:", filmy)

# 2. Přidej film na konec a vytiskni celý seznam
# append() přidá prvek na konec bez nutnosti znát délku seznamu
filmy.append("Spider-Man")
print("Po přidání Spider-Mana:", filmy)

# 3. Zjisti, jestli je "Minecraft" v seznamu her
hry = ["Minecraft", "Roblox", "Fortnite", "FIFA"]
# operátor `in` projde seznam a vrátí True/False v O(n)
if "Minecraft" in hry:
    print("Minecraft je v tvém seznamu her!")
else:
    print("Minecraft v seznamu her není.")

# Bonusová ukázka: nákupní seznam s hardcoded hodnotami (místo smyčky input())
print("\n=== Nákupní seznam ===")
nakup = ["mléko", "chléb", "máslo"]   # input() nahrazeno: předdefinované položky
print("Tvůj nákupní seznam:")
for i, vec in enumerate(nakup, 1):
    print(f"  {i}. {vec}")
