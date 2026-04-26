"""
LEKCE 22: Třídy – vlastní datové typy
=======================================
Třída je šablona pro výrobu objektů.
Objekt = věc, která má VLASTNOSTI (atributy) a SCHOPNOSTI (metody).

Dosud jsme používali hotové typy: int, str, list...
Teď si uděláme vlastní!
"""

# ── Bez třídy – chaotické ────────────────────────────────────────────────────
# hrac_jmeno = "Míša"
# hrac_hp    = 100
# hrac_utok  = 15
# To se rychle zamotá u více hráčů...

# ── Se třídou – čisté ────────────────────────────────────────────────────────

class Hrac:
    # __init__ se zavolá automaticky při vytvoření objektu
    def __init__(self, jmeno, hp, utok):
        self.jmeno = jmeno   # self = tento konkrétní objekt
        self.hp    = hp
        self.utok  = utok
        self.level = 1
        self.inventar = []

    # __str__ určuje, co se zobrazí při print(hrac)
    def __str__(self):
        return (f"[{self.jmeno}] HP:{self.hp}  "
                f"Útok:{self.utok}  Level:{self.level}")

    def je_nazivu(self):
        return self.hp > 0

    def utoc(self, cil):
        cil.hp -= self.utok
        print(f"  {self.jmeno} útočí na {cil.jmeno} za {self.utok} poškození."
              f"  ({cil.jmeno} má {max(cil.hp, 0)} HP)")

    def lec(self, mnozstvi=20):
        self.hp += mnozstvi
        print(f"  {self.jmeno} se vyléčil o {mnozstvi} HP. Má teď {self.hp} HP.")

    def sebrat(self, predmet):
        self.inventar.append(predmet)
        print(f"  {self.jmeno} sebral: {predmet}")

    def zkusenosti(self):
        self.level += 1
        self.utok  += 5
        print(f"  {self.jmeno} přešel na level {self.level}! Útok: {self.utok}")


# ── Vytvoření objektů ze třídy ───────────────────────────────────────────────
print("=== Vytváříme hráče ===\n")

hrac1 = Hrac("Míša", hp=100, utok=15)
hrac2 = Hrac("Tomáš", hp=80, utok=20)

print(hrac1)   # volá __str__
print(hrac2)

print("\n=== Souboj ===\n")

hrac1.utoc(hrac2)
hrac2.utoc(hrac1)
hrac1.lec(30)
hrac1.sebrat("meč +5")
hrac1.zkusenosti()

print(f"\nPodle zkušenosti stav:")
print(hrac1)
print(hrac2)


# ── Třída pro nepřítele ───────────────────────────────────────────────────────
class Nepritel:
    def __init__(self, jmeno, hp, utok, odmena):
        self.jmeno  = jmeno
        self.hp     = hp
        self.utok   = utok
        self.odmena = odmena  # zlaté mince po porážce

    def __str__(self):
        return f"[NEPŘÍTEL: {self.jmeno}] HP:{self.hp} Útok:{self.utok}"

    def je_nazivu(self):
        return self.hp > 0

    def utoc(self, hrac):
        hrac.hp -= self.utok
        print(f"  {self.jmeno} útočí na {hrac.jmeno} za {self.utok}! "
              f"({hrac.jmeno}: {max(hrac.hp,0)} HP)")


# ── Malá automatická hra ──────────────────────────────────────────────────────
print("\n" + "="*50)
print("=== MINIHRA: SOUBOJ ===")
print("="*50)

bojovnik = Hrac(input("\nJméno tvého hráče: "), hp=100, utok=18)
boss = Nepritel("Drak", hp=60, utok=12, odmena=100)

print(f"\n{bojovnik}")
print(boss)
print()

kolo = 1
while bojovnik.je_nazivu() and boss.je_nazivu():
    print(f"── Kolo {kolo} ──")
    bojovnik.utoc(boss)
    if boss.je_nazivu():
        boss.utoc(bojovnik)
    kolo += 1
    print()

if bojovnik.je_nazivu():
    print(f"VÝHRA! {bojovnik.jmeno} porazil {boss.jmeno}!")
    print(f"Získal {boss.odmena} zlatých.")
    bojovnik.zkusenosti()
else:
    print(f"{bojovnik.jmeno} prohrál. Drak slaví.")

print(f"\nFinální stav: {bojovnik}")

# TVOJE ÚLOHA:
# 1. Přidej atribut `mana` do Hrac a metodu `kouzlo(cil)` (stojí 20 many, útok *2).
# 2. Přidej do Nepritel metodu `loot()`, která vrátí náhodný předmět ze seznamu.
# 3. Udělej souboj interaktivní: každé kolo se ptej "útok / léčení / útěk".
