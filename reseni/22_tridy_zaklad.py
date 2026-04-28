"""Řešení – Lekce 22: Třídy – vlastní datové typy"""

import random

# ── Základní třída Hrac s mana a kouzlem ────────────────────────────────────

class Hrac:
    def __init__(self, jmeno, hp=100, utok=15):
        self.jmeno = jmeno
        self.hp = hp
        self.utok = utok
        self.level = 1
        self.inventar = []
        # 1. Nový atribut mana
        self.mana = 100

    def __str__(self):
        return (f"[{self.jmeno}] HP:{self.hp}  Útok:{self.utok}"
                f"  Mana:{self.mana}  Level:{self.level}")

    def je_nazivu(self):
        return self.hp > 0

    def utoc(self, cil):
        cil.hp -= self.utok
        print(f"  {self.jmeno} útočí na {cil.jmeno} za {self.utok} poškození. "
              f"({cil.jmeno} má {max(cil.hp, 0)} HP)")

    # 1. Metoda kouzlo: stojí 20 many, útok * 2
    # Kdybychom kouzlili bez many, útok selže – vynucujeme pravidla hry
    def kouzlo(self, cil):
        if self.mana < 20:
            print(f"  {self.jmeno} nemá dost many! (má {self.mana})")
            return
        self.mana -= 20
        poskozeni = self.utok * 2
        cil.hp -= poskozeni
        print(f"  {self.jmeno} sesílá kouzlo na {cil.jmeno}"
              f" za {poskozeni} poškození! (mana: {self.mana})")

    def lec(self, mnozstvi=20):
        self.hp += mnozstvi
        print(f"  {self.jmeno} se vyléčil o {mnozstvi} HP. Má teď {self.hp} HP.")

    def sebrat(self, predmet):
        self.inventar.append(predmet)
        print(f"  {self.jmeno} sebral: {predmet}")

    def zkusenosti(self):
        self.level += 1
        self.utok += 5
        print(f"  {self.jmeno} přešel na level {self.level}! Útok: {self.utok}")


# ── Třída Nepritel s loot() ──────────────────────────────────────────────────

class Nepritel:
    LOOT_TABULKA = ["zlaté mince", "lektvar léčení", "starý meč",
                    "amulet ochrany", "prach", "nic"]

    def __init__(self, jmeno, hp, utok, odmena):
        self.jmeno = jmeno
        self.hp = hp
        self.utok = utok
        self.odmena = odmena

    def __str__(self):
        return f"[NEPŘÍTEL: {self.jmeno}] HP:{self.hp} Útok:{self.utok}"

    def je_nazivu(self):
        return self.hp > 0

    def utoc(self, hrac):
        hrac.hp -= self.utok
        print(f"  {self.jmeno} útočí na {hrac.jmeno} za {self.utok}! "
              f"({hrac.jmeno}: {max(hrac.hp, 0)} HP)")

    # 2. Metoda loot – vrátí náhodný předmět ze seznamu
    # random.choice vybere nepředvídatelně – každé kolo může padnout jiný loot
    def loot(self):
        predmet = random.choice(self.LOOT_TABULKA)
        print(f"  {self.jmeno} upustil: {predmet}")
        return predmet


# ── 3. Interaktivní souboj (simulovaný) ─────────────────────────────────────

print("=== INTERAKTIVNÍ SOUBOJ (simulace vstupů) ===\n")

# simulace vstupu: jméno hráče
jmeno_hrace = "Hrdina"  # simulace vstupu: "Hrdina"
bojovnik = Hrac(jmeno_hrace, hp=100, utok=18)
boss = Nepritel("Drak", hp=60, utok=12, odmena=100)

print(bojovnik)
print(boss)
print()

# Každé kolo se ptáme: útok / léčení / kouzlo / útěk
# Simulujeme sekvenci akcí jako by hráč zadával příkazy
akce_sekvence = ["utok", "leceni", "kouzlo", "utok", "utok", "utok"]
kolo = 1

while bojovnik.je_nazivu() and boss.je_nazivu():
    print(f"── Kolo {kolo} ──")
    print(f"  {bojovnik.jmeno}: HP={bojovnik.hp} Mana={bojovnik.mana}"
          f" | {boss.jmeno}: HP={boss.hp}")

    # simulace vstupu: výběr akce
    if kolo <= len(akce_sekvence):
        akce = akce_sekvence[kolo - 1]
    else:
        akce = "utok"
    print(f"  Akce (útok/léčení/kouzlo/útěk) → simulace: '{akce}'")

    if akce == "utok":
        bojovnik.utoc(boss)
    elif akce == "leceni":
        bojovnik.lec(30)
    elif akce == "kouzlo":
        bojovnik.kouzlo(boss)
    elif akce == "utek":
        print(f"  {bojovnik.jmeno} utekl! Zbabělec...")
        break

    if boss.je_nazivu():
        boss.utoc(bojovnik)

    kolo += 1
    print()

if bojovnik.je_nazivu() and boss.hp <= 0:
    print(f"VÝHRA! {bojovnik.jmeno} porazil {boss.jmeno}!")
    predmet = boss.loot()
    bojovnik.sebrat(predmet)
    bojovnik.zkusenosti()
elif not bojovnik.je_nazivu():
    print(f"{bojovnik.jmeno} byl poražen. Drak slaví.")

print(f"\nFinální stav: {bojovnik}")
