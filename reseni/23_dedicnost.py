"""Řešení – Lekce 23: Dědičnost – třídy ze tříd"""

import random


# ── Rodičovská třída ─────────────────────────────────────────────────────────

class Postava:
    def __init__(self, jmeno, hp, utok):
        self.jmeno = jmeno
        self.hp = hp
        self.utok = utok

    def __str__(self):
        return f"{self.__class__.__name__} {self.jmeno}  HP:{self.hp}  Útok:{self.utok}"

    # 3. __repr__ vrací technický popis – vhodný pro debugování
    # Rozdíl: __str__ pro uživatele (print), __repr__ pro vývojáře (repr(), konzole)
    def __repr__(self):
        return (f"{self.__class__.__name__}("
                f"jmeno={self.jmeno!r}, hp={self.hp}, utok={self.utok})")

    def je_nazivu(self):
        return self.hp > 0

    def utoc(self, cil):
        cil.hp -= self.utok
        print(f"  {self.jmeno} → {cil.jmeno}: -{self.utok} HP")


# ── Bojovnik, Mag, Zlodej (z originální lekce) ───────────────────────────────

class Bojovnik(Postava):
    def __init__(self, jmeno):
        super().__init__(jmeno, hp=120, utok=20)
        self.stit = 10

    def blok(self):
        print(f"  {self.jmeno} blokuje štítem!")

    def utoc(self, cil):
        poskozeni = self.utok + 5
        cil.hp -= poskozeni
        print(f"  {self.jmeno} sekne mečem → {cil.jmeno}: -{poskozeni} HP")


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
            print(f"  {self.jmeno} sesílá blesk → {cil.jmeno}: -{poskozeni} HP")
        else:
            print(f"  {self.jmeno} nemá dost many!")
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
            poskozeni = self.utok * 3
            self.skryty = False
            cil.hp -= poskozeni
            print(f"  {self.jmeno} vyskočí ze stínu → {cil.jmeno}: -{poskozeni} HP (záloha!)")
        else:
            super().utoc(cil)


# 1. Paladin dědí z Bojovnik, přidá metodu lec()
# Super() volá Bojovnik.__init__, takže Paladin dostane stit + silný útok
class Paladin(Bojovnik):
    def __init__(self, jmeno):
        super().__init__(jmeno)  # zdědí hp=120, utok=20, stit=10
        self.hp = 130            # Paladin je odolnější
        self.svata_mana = 60

    def lec(self, cil=None, mnozstvi=30):
        """Paladin léčí sebe nebo spojence."""
        cil = cil or self
        cil.hp += mnozstvi
        print(f"  {self.jmeno} léčí {cil.jmeno} o {mnozstvi} HP → {cil.hp} HP")


# 2. Goblin – jednoduchý nepřítel
class Goblin(Postava):
    def __init__(self, jmeno="Goblin"):
        super().__init__(jmeno, hp=30, utok=8)

    def krikni(self):
        print(f"  {self.jmeno}: Grrrr!")


# ── Demo ─────────────────────────────────────────────────────────────────────

print("=== Rozšířený tým hrdinů ===\n")

paladin = Paladin("Světlonoš")
goblin = Goblin("Zlý goblin")

print(paladin)
print(goblin)

print("\n=== isinstance kontrola ===")
print(f"Paladin je Bojovnik? {isinstance(paladin, Bojovnik)}")
print(f"Paladin je Postava?  {isinstance(paladin, Postava)}")
print(f"Goblin je Postava?   {isinstance(goblin, Postava)}")

print("\n=== __repr__ vs __str__ ===")
b = Bojovnik("Radek")
print(f"str(b)  = {str(b)}")   # volá __str__ – pro uživatele
print(f"repr(b) = {repr(b)}")  # volá __repr__ – pro vývojáře/debugování

print("\n=== Paladin léčí po souboji ===")
mag = Mag("Alžběta")
goblin.utoc(mag)
print(f"  {mag.jmeno} má {mag.hp} HP po útoku goblina")
paladin.lec(mag, 25)

print("\n=== Boj Paladina s Goblinem ===")
print(paladin)
print(goblin)
while paladin.je_nazivu() and goblin.je_nazivu():
    paladin.utoc(goblin)
    if goblin.je_nazivu():
        goblin.utoc(paladin)

if paladin.je_nazivu():
    print(f"\n{paladin.jmeno} zvítězil! HP: {paladin.hp}")
else:
    print(f"\n{goblin.jmeno} zvítězil. Nepravděpodobné, ale stalo se.")
