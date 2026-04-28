"""Řešení – Lekce 86: tkinter – desktop GUI"""

# Vestavěné – žádná instalace (Linux: sudo apt install python3-tk)
# GUI část vyžaduje X display – logika je spustitelná vždy

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import sys

print("=== tkinter řešení – logická část ===\n")
print("GUI demo vyžaduje X display.")
print("Pro spuštění: python3 86_tkinter.py\n")


# 1. Funkce "Najít a nahradit" pro textový editor
print("=== 1. Logika Najít a nahradit ===\n")

def najdi_a_nahrad_logika(text: str, hledat: str, nahradit: str,
                            rozlisovat: bool = True) -> tuple[str, int]:
    """
    Najde a nahradí všechny výskyty v textu.
    Vrátí (nový_text, počet_nahrazení).
    """
    if not hledat:
        return text, 0
    if not rozlisovat:
        import re
        novy, pocet = re.subn(re.escape(hledat), nahradit, text, flags=re.IGNORECASE)
    else:
        pocet  = text.count(hledat)
        novy   = text.replace(hledat, nahradit)
    return novy, pocet

# Testy logiky
TESTOVACI_TEXT = """def hello():
    print("Hello World")
    print("Hello Python")
    return "Hello!"

hello()
"""

print("Testovací text:")
print(TESTOVACI_TEXT)

# Nahrazení bez ohledu na velikost
for hledat, nahradit, rozlisovat in [
    ("Hello", "Ahoj",   True),
    ("hello", "ahoj",   False),
    ("print", "console.log", True),
]:
    novy, pocet = najdi_a_nahrad_logika(TESTOVACI_TEXT, hledat, nahradit, rozlisovat)
    print(f"  '{hledat}' → '{nahradit}' (rozlišovat={rozlisovat}): "
          f"{pocet} nahrazení")
    if pocet > 0:
        print(f"  Výsledek (první 2 řádky):")
        for radek in novy.splitlines()[:2]:
            if radek.strip():
                print(f"    {radek}")
        print()


# 2. Kalkulačka – logika
print("=== 2. Kalkulačka – logika ===\n")

class Kalkulator:
    """Logika kalkulačky bez GUI."""

    def __init__(self):
        self.displej    = "0"
        self.akumulátor = None
        self.operátor   = None
        self.novy_vstup = True

    def stiskni_cislo(self, cifra: str):
        if self.novy_vstup:
            self.displej  = cifra
            self.novy_vstup = False
        else:
            if self.displej == "0" and cifra != ".":
                self.displej = cifra
            elif "." in self.displej and cifra == ".":
                pass  # nepovolíme dvě desetinné tečky
            else:
                self.displej += cifra

    def stiskni_operator(self, op: str):
        try:
            hodnota = float(self.displej)
        except ValueError:
            return
        if self.akumulátor is not None and not self.novy_vstup:
            self.vypocti()
        self.akumulátor  = float(self.displej)
        self.operátor    = op
        self.novy_vstup  = True

    def vypocti(self):
        if self.akumulátor is None or self.operátor is None:
            return
        try:
            a = self.akumulátor
            b = float(self.displej)
            vysledek = {
                "+": a + b,
                "-": a - b,
                "*": a * b,
                "/": a / b if b != 0 else None,
                "%": a % b if b != 0 else None,
            }.get(self.operátor)

            if vysledek is None:
                self.displej = "Chyba"
            else:
                # Odstraň zbytečnou desetinnou část
                if vysledek == int(vysledek):
                    self.displej = str(int(vysledek))
                else:
                    self.displej = f"{vysledek:.10g}"
        except Exception:
            self.displej = "Chyba"

        self.akumulátor  = None
        self.operátor    = None
        self.novy_vstup  = True

    def smaz(self):
        self.displej    = "0"
        self.akumulátor = None
        self.operátor   = None
        self.novy_vstup = True

    def procento(self):
        try:
            self.displej = str(float(self.displej) / 100)
            self.novy_vstup = True
        except ValueError:
            pass

    def zmena_znamenka(self):
        try:
            val = float(self.displej)
            self.displej = str(-val) if val != 0 else "0"
        except ValueError:
            pass

# Test kalkulačky
calc = Kalkulator()
print("Simulace stisku tlačítek:")
operace = [
    ("cifry", ["1", "2", "3"], "123"),
    ("+", None, "123 +"),
    ("cifry", ["4", "5"], "123 + 45"),
    ("=", None, "168"),
    ("cifry", ["8"], "8"),
    ("*", None, "8 *"),
    ("cifry", ["7"], "8 * 7"),
    ("=", None, "56"),
    ("cifry", ["1", "0"], "10"),
    ("/", None, "10 /"),
    ("cifry", ["0"], "10 / 0"),
    ("=", None, "Chyba: dělení nulou"),
]

for akce, cifry, ocekavany in operace:
    if akce == "cifry" and cifry:
        for c in cifry:
            calc.stiskni_cislo(c)
    elif acka := {"+": "+", "-": "-", "*": "*", "/": "/"}.get(akce):
        calc.stiskni_operator(acka)
    elif akce == "=":
        calc.vypocti()
    print(f"  [{ocekavany}] displej = {calc.displej}")

calc.smaz()
# Procenta
calc.stiskni_cislo("5")
calc.stiskni_cislo("0")
calc.procento()
print(f"\n  50% = {calc.displej}")


# 3. Canvas – kruh a obdélník + výběr nástroje
print("\n=== 3. Canvas nástroje – logická část ===\n")

class CanvasLogika:
    """Logika kreslení – nezávislá na GUI."""

    def __init__(self):
        self.tvar   = "tuzka"    # tuzka / obdelnik / kruh / cara
        self.barva  = "#2E86AB"
        self.tloustka = 3
        self.objekty: list[dict] = []
        self._zacatek = None

    def zac_kreslit(self, x: int, y: int):
        self._zacatek = (x, y)

    def konec_kresleni(self, x: int, y: int) -> dict | None:
        """Ukončí kreslení, vrátí přidaný objekt."""
        if self._zacatek is None:
            return None
        x0, y0 = self._zacatek
        obj = {
            "tvar":     self.tvar,
            "barva":    self.barva,
            "tloustka": self.tloustka,
            "x0": x0, "y0": y0, "x1": x, "y1": y,
        }
        if self.tvar == "kruh":
            # Poloměr = polovina vzdálenosti středů
            obj["cx"]  = (x0 + x) // 2
            obj["cy"]  = (y0 + y) // 2
            obj["r"]   = int(math.hypot(x - x0, y - y0) / 2)

        self.objekty.append(obj)
        self._zacatek = None
        return obj

    def smaz_vse(self):
        self.objekty.clear()

    def exportuj_svg(self) -> str:
        """Exportuje nakreslenou scénu jako SVG."""
        radky = ['<svg xmlns="http://www.w3.org/2000/svg" width="600" height="500">']
        radky.append(f'  <rect width="600" height="500" fill="white"/>')

        for obj in self.objekty:
            b = obj["barva"]
            w = obj["tloustka"]
            if obj["tvar"] == "obdelnik":
                radky.append(
                    f'  <rect x="{min(obj["x0"],obj["x1"])}" y="{min(obj["y0"],obj["y1"])}" '
                    f'width="{abs(obj["x1"]-obj["x0"])}" height="{abs(obj["y1"]-obj["y0"])}" '
                    f'stroke="{b}" stroke-width="{w}" fill="none"/>'
                )
            elif obj["tvar"] == "kruh":
                radky.append(
                    f'  <circle cx="{obj["cx"]}" cy="{obj["cy"]}" r="{obj["r"]}" '
                    f'stroke="{b}" stroke-width="{w}" fill="none"/>'
                )
            elif obj["tvar"] in ("cara", "tuzka"):
                radky.append(
                    f'  <line x1="{obj["x0"]}" y1="{obj["y0"]}" '
                    f'x2="{obj["x1"]}" y2="{obj["y1"]}" '
                    f'stroke="{b}" stroke-width="{w}"/>'
                )

        radky.append("</svg>")
        return "\n".join(radky)

import math

canvas = CanvasLogika()

# Simulace kreslení
canvas.tvar = "obdelnik"
canvas.barva = "#FF5733"
canvas.zac_kreslit(50, 50)
obj1 = canvas.konec_kresleni(200, 150)

canvas.tvar = "kruh"
canvas.barva = "#2E86AB"
canvas.zac_kreslit(300, 100)
obj2 = canvas.konec_kresleni(400, 200)

canvas.tvar = "cara"
canvas.barva = "#27AE60"
canvas.zac_kreslit(10, 400)
obj3 = canvas.konec_kresleni(590, 400)

print(f"  Nakresleno objektů: {len(canvas.objekty)}")
for o in canvas.objekty:
    print(f"    {o['tvar']:12} barva={o['barva']}  "
          f"({o['x0']},{o['y0']}) → ({o['x1']},{o['y1']})")

svg = canvas.exportuj_svg()
print(f"\n  SVG export ({len(svg)} B):")
print(f"  {svg[:200]}...")

print("\n=== Shrnutí ===")
print("  1. najdi_a_nahrad_logika() – str.replace + regex, s/bez rozlišení")
print("  2. Kalkulator              – stavy, operátory, chyby (dělení nulou)")
print("  3. CanvasLogika            – tvary, barvy, SVG export")
print()
print("  GUI demo spustit:")
print("  python3 -c \"import tkinter; root = tkinter.Tk(); root.mainloop()\"")
