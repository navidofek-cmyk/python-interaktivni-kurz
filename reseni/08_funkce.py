"""Řešení – Lekce 08: Funkce"""

# 1. Funkce pozdrav_cs s plným pozdravem
def pozdrav_cs(jmeno: str, vek: int) -> None:
    print(f"Ahoj, {jmeno}! Je ti {vek} let. Vítej v Pythonu!")

pozdrav_cs("Míša", 10)
pozdrav_cs("Tomáš", 16)

# 2. Funkce max_ze_dvou
def max_ze_dvou(a, b):
    return a if a >= b else b
    # nebo jednoduše: return max(a, b)

print(max_ze_dvou(5, 3))    # 5
print(max_ze_dvou(2, 8))    # 8
print(max_ze_dvou(4, 4))    # 4

# 3. Trojúhelník ze hvězdiček
def trojuhelnik(vyska: int) -> None:
    for i in range(1, vyska + 1):
        print("*" * i)

trojuhelnik(5)

# Bonus: trojúhelník na střed
def trojuhelnik_stred(vyska: int) -> None:
    for i in range(1, vyska + 1):
        mezera = " " * (vyska - i)
        print(mezera + "*" * i)

print()
trojuhelnik_stred(5)
