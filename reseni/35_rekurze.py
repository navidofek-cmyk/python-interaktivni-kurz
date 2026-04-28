"""Řešení – Lekce 35: Rekurze"""

import sys
sys.setrecursionlimit(10_000)


# 1. Rekurzivní mocnina bez operátoru **
# Base case: cokoli na 0 = 1
# Recursive case: zaklad^exp = zaklad × zaklad^(exp-1)
# Pro záporné exponenty: 1 / zaklad^(-exp)

def mocnina(zaklad: float, exp: int) -> float:
    """Rekurzivní umocňování bez operátoru **."""
    if exp == 0:
        return 1
    if exp < 0:
        return 1 / mocnina(zaklad, -exp)
    return zaklad * mocnina(zaklad, exp - 1)


print("=== 1. Rekurzivní mocnina ===")
testy = [(2, 10), (3, 5), (5, 0), (2, -3), (10, 4)]
for zaklad, exp in testy:
    vysledek = mocnina(zaklad, exp)
    ocekavany = zaklad ** exp
    shoda = "✓" if abs(vysledek - ocekavany) < 1e-9 else "✗"
    print(f"  {zaklad}^{exp:3d} = {vysledek:10.4f}  (vestavěný: {ocekavany}) {shoda}")


# 2. Rekurzivní palindrom bez [::-1]
# Porovnáváme první a poslední znak, pak rekurzivně zkrácený řetězec
# Base case: prázdný řetězec nebo jeden znak → palindrom

def palindrom(s: str) -> bool:
    """Rekurzivní kontrola palindromu bez obracení řetězce."""
    # Normalizace: malá písmena, bez mezer
    s = s.lower().replace(" ", "")

    if len(s) <= 1:        # base case
        return True
    if s[0] != s[-1]:
        return False
    return palindrom(s[1:-1])  # recursive: zkrátíme z obou stran


print("\n=== 2. Rekurzivní palindrom ===")
testy = [
    ("racecar", True), ("level", True), ("python", False),
    ("Was it a car or a cat I saw", True), ("hello", False), ("", True),
]
for s, ocekavany in testy:
    vysledek = palindrom(s)
    shoda = "✓" if vysledek == ocekavany else "✗"
    print(f"  {s!r:35} → {vysledek}  {shoda}")


# 3. Rekurzivní součet číslic
# suma_cislic(1234) → 1+2+3+4 = 10
# Base case: jednociferné číslo → samo sebe
# Recursive case: poslední cifra + suma_cislic(zbytek)

def suma_cislic(n: int) -> int:
    """Rekurzivní součet číslic nezáporného čísla."""
    n = abs(n)  # pracujeme s absolutní hodnotou
    if n < 10:
        return n
    return n % 10 + suma_cislic(n // 10)


print("\n=== 3. Rekurzivní suma číslic ===")
testy = [1234, 9999, 100, 0, 999999, -456]
for n in testy:
    s = suma_cislic(n)
    # Ověření: sum(int(c) for c in str(abs(n)))
    ocekavany = sum(int(c) for c in str(abs(n)))
    shoda = "✓" if s == ocekavany else "✗"
    print(f"  suma_cislic({n}) = {s}  {shoda}")


# 4. Hanojské věže – kolik tahů pro n disků?
# Vzorec: 2^n - 1 tahů
# Pro 64 disků: 2^64 - 1 = 18 446 744 073 709 551 615 tahů
# Pokud každý tah trvá 1 sekundu: cca 585 miliard let!

def hanoi_pocet_tahu(n: int) -> int:
    """Rekurzivně spočítá počet tahů pro n disků."""
    if n == 0:
        return 0
    return 2 * hanoi_pocet_tahu(n - 1) + 1  # = 2^n - 1


print("\n=== 4. Hanojské věže – počet tahů ===")
print(f"  {'Disků':>6}  {'Tahů':>25}  {'Vzorec':>15}  {'Čas při 1 tah/s'}")
print("  " + "-" * 75)

ROK = 365.25 * 24 * 3600  # sekundy v roce

for n in [1, 2, 3, 5, 10, 20, 32, 64]:
    tahy = hanoi_pocet_tahu(n)
    vzorec = 2**n - 1
    assert tahy == vzorec

    sekundy = tahy
    if sekundy < 60:
        cas = f"{sekundy:.0f}s"
    elif sekundy < 3600:
        cas = f"{sekundy/60:.1f} min"
    elif sekundy < ROK:
        cas = f"{sekundy/3600:.1f} hod"
    elif sekundy < ROK * 1e6:
        cas = f"{sekundy/ROK:.0f} let"
    else:
        cas = f"{sekundy/ROK:.2e} let"

    print(f"  {n:>6}  {tahy:>25,}  (2^{n}-1)  {cas}")

print()
print("  Legenda: mnichové v Hanoji přesouvají 64 zlatých disků.")
print("  Podle legendy: až skončí, nastane konec světa.")
print(f"  Ale teprve za ~{(2**64-1)/ROK:.2e} let :)")
