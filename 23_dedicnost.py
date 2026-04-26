"""
LEKCE 23: Dědičnost – třídy ze tříd
======================================
Dědičnost = nová třída převezme vše od rodičovské třídy
            a může přidat nebo změnit vlastnosti a metody.

Analogie: Živočich → Savec → Pes → Pudl
          Postava  → Bojovník / Mág / Zloděj
"""

# ── Rodičovská třída ─────────────────────────────────────────────────────────

class Postava:
    def __init__(self, jmeno, hp, utok):
        self.jmeno = jmeno
        self.hp    = hp
        self.utok  = utok

    def __str__(self):
        return f"{self.__class__.__name__} {self.jmeno}  HP:{self.hp}  Útok:{self.utok}"

    def je_nazivu(self):
        return self.hp > 0

    def utoc(self, cil):
        cil.hp -= self.utok
        print(f"  {self.jmeno} → {cil.jmeno}: -{self.utok} HP")


# ── Podtřídy – dědí z Postava ────────────────────────────────────────────────

class Bojovnik(Postava):
    def __init__(self, jmeno):
        super().__init__(jmeno, hp=120, utok=20)  # super() = rodič
        self.stit = 10   # vlastní atribut navíc

    def blok(self):
        print(f"  {self.jmeno} blokuje štítem! Další útok způsobí o {self.stit} méně.")

    # Přepíšeme metodu rodiče (override)
    def utoc(self, cil):
        poskozeni = self.utok + 5   # bojovník dá vždy +5
        cil.hp -= poskozeni
        print(f"  {self.jmeno} sekne mečem → {cil.jmeno}: -{poskozeni} HP  (silný úder!)")


class Mag(Postava):
    def __init__(self, jmeno):
        super().__init__(jmeno, hp=70, utok=35)
        self.mana = 100

    def __str__(self):
        return super().__str__() + f"  Mana:{self.mana}"

    def kouzlo(self, cil):
        if self.mana >= 30:
            self.mana -= 30
            poskozeni = self.utok * 2
            cil.hp -= poskozeni
            print(f"  {self.jmeno} sesílá blesk → {cil.jmeno}: -{poskozeni} HP  ⚡")
        else:
            print(f"  {self.jmeno} nemá dost many! Útočí pěstí.")
            super().utoc(cil)


class Zlodej(Postava):
    def __init__(self, jmeno):
        super().__init__(jmeno, hp=90, utok=25)
        self.skryty = False

    def skryj_se(self):
        self.skryty = True
        print(f"  {self.jmeno} se skryl do stínu...")

    def utoc(self, cil):
        if self.skryty:
            poskozeni = self.utok * 3   # útok ze zálohy
            self.skryty = False
            cil.hp -= poskozeni
            print(f"  {self.jmeno} vyskočí ze stínu → {cil.jmeno}: -{poskozeni} HP  🗡 (záloha!)")
        else:
            super().utoc(cil)


# ── Ukázka ───────────────────────────────────────────────────────────────────
print("=== Tým hrdinů ===\n")

tym = [
    Bojovnik("Radek"),
    Mag("Alžběta"),
    Zlodej("Šedý"),
]

for postava in tym:
    print(postava)

print("\n=== Speciální schopnosti ===\n")
tym[0].blok()
tym[1].kouzlo(tym[0])     # Alžběta kouzlí na Radka (test)
tym[2].skryj_se()
tym[2].utoc(tym[0])

print("\n=== isinstance – zjisti typ objektu ===\n")
for p in tym:
    print(f"{p.jmeno}: Postava? {isinstance(p, Postava)}   "
          f"Mág? {isinstance(p, Mag)}")


# ── Souboj party vs. boss ─────────────────────────────────────────────────────
print("\n" + "="*52)
print("SOUBOJ: Tým vs. Boss")
print("="*52)

class Boss(Postava):
    def __init__(self):
        super().__init__("Temný pán", hp=300, utok=30)
        self.faze = 1

    def utoc(self, cil):
        if self.hp < 100 and self.faze == 1:
            self.faze = 2
            self.utok = 50
            print(f"  !! {self.jmeno} zuří! Útok vzrostl na {self.utok}!")
        super().utoc(cil)

boss = Boss()
hrdinove = [Bojovnik("Radek"), Mag("Alžběta"), Zlodej("Šedý")]

print(f"\n{boss}")
for h in hrdinove:
    print(h)

kolo = 1
import random

while boss.je_nazivu() and any(h.je_nazivu() for h in hrdinove):
    print(f"\n── Kolo {kolo} ──")

    zivi = [h for h in hrdinove if h.je_nazivu()]

    for hrdina in zivi:
        if isinstance(hrdina, Mag):
            hrdina.kouzlo(boss)
        elif isinstance(hrdina, Zlodej) and kolo % 2 == 0:
            hrdina.skryj_se()
        else:
            hrdina.utoc(boss)

    if boss.je_nazivu():
        cil = random.choice(zivi)
        boss.utoc(cil)

    kolo += 1

if boss.je_nazivu():
    print("\nTemný pán vyhrál. Svět je v temnotě.")
else:
    print(f"\nTemný pán poražen po {kolo-1} kolech! Hrdinové slaví!")

# TVOJE ÚLOHA:
# 1. Přidej třídu Paladin(Bojovnik) – dědí z Bojovnik, přidá metodu lec().
# 2. Přidej třídu Goblin(Postava) jako nepřítele s hp=30, utok=8.
# 3. Přidej metodu __repr__ do Postava a zjisti, jak se liší od __str__.
