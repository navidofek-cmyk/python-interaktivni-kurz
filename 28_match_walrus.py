"""
LEKCE 28: match / case  a  walrus operátor :=
===============================================
Dvě novinky z dokumentace (Python 3.10+).

MATCH = strukturální pattern matching.
        Jako if/elif, ale umí rozložit objekt na části
        a porovnat jeho tvar, nejen hodnotu.

WALRUS := = "mrož operátor" – přiřadí A zároveň vrátí hodnotu.
           Jméno proto, že := vypadá jako mrožovy oči a kly.
"""

# ══════════════════════════════════════════════════════════════
# ČÁST 1: WALRUS OPERÁTOR :=
# ══════════════════════════════════════════════════════════════

print("=== Walrus := ===\n")

# Starý způsob
data = [1, 5, 2, 8, 3, 9, 4]
filtr = []
for x in data:
    y = x * 2
    if y > 10:
        filtr.append(y)
print("Filtr (starý):", filtr)

# S walrusem – přiřazení uvnitř podmínky
filtr2 = [y for x in data if (y := x * 2) > 10]
print("Filtr (walrus):", filtr2)

# Typický use-case: čtení po kouscích
print("\n--- Walrus v while ---")
import io
stream = io.StringIO("ahoj\nsvetem\npython\n")

while radek := stream.readline():
    print(f"  přečteno: {radek!r}")

# Regex + walrus
import re
print("\n--- Walrus + regex ---")
texty = ["cena: 299 Kč", "bez ceny", "cena: 1499 Kč", "gratis"]
for t in texty:
    if m := re.search(r"(\d+)", t):
        print(f"  {t!r:25} → číslo: {m.group()}")
    else:
        print(f"  {t!r:25} → žádné číslo")


# ══════════════════════════════════════════════════════════════
# ČÁST 2: MATCH / CASE
# ══════════════════════════════════════════════════════════════

print("\n=== match / case ===\n")

# ── 1. Matching literálů (jako switch) ───────────────────────

def http_status(kod):
    match kod:
        case 200: return "OK"
        case 301: return "Moved Permanently"
        case 404: return "Not Found"
        case 418: return "I'm a teapot"   # RFC 2324, vážně existuje
        case 500: return "Internal Server Error"
        case _:   return f"Neznámý kód {kod}"   # _ = default

for kod in [200, 404, 418, 999]:
    print(f"  {kod}: {http_status(kod)}")

# ── 2. Matching sekvencí (rozkládání) ────────────────────────

print("\n--- Matching sekvencí ---")

def prikaz(cmd):
    match cmd.split():
        case ["jdi", smer]:
            return f"Jdeš {smer}."
        case ["vezmi", predmet]:
            return f"Bereš {predmet}."
        case ["jdi", smer, "rychle"]:
            return f"Rychle jdeš {smer}!"
        case ["konec"] | ["quit"] | ["q"]:
            return "Ukončuji hru."
        case []:
            return "Prázdný příkaz."
        case _:
            return f"Neznámý příkaz: {cmd!r}"

prikazy = ["jdi sever", "vezmi meč", "jdi jih rychle",
           "q", "letej", ""]
for p in prikazy:
    print(f"  {p!r:25} → {prikaz(p)}")

# ── 3. Matching slovníků ──────────────────────────────────────

print("\n--- Matching slovníků ---")

def zpracuj_udalost(event):
    match event:
        case {"typ": "klik", "x": x, "y": y}:
            return f"Klik na ({x}, {y})"
        case {"typ": "klavesa", "key": k} if k.startswith("F"):
            return f"Funkční klávesa: {k}"
        case {"typ": "klavesa", "key": k}:
            return f"Klávesa: {k!r}"
        case {"typ": typ, **zbytek}:
            return f"Neznámý typ {typ!r}, data: {zbytek}"

udalosti = [
    {"typ": "klik", "x": 100, "y": 200},
    {"typ": "klavesa", "key": "F5"},
    {"typ": "klavesa", "key": "Enter"},
    {"typ": "scroll", "delta": -3},
]
for u in udalosti:
    print(f"  {zpracuj_udalost(u)}")

# ── 4. Matching tříd (nejsilnější!) ──────────────────────────

print("\n--- Matching tříd ---")

class Bod:
    def __init__(self, x, y): self.x = x; self.y = y

class Kruh:
    def __init__(self, stred, polomer): self.stred = stred; self.polomer = polomer

class Obdelnik:
    def __init__(self, levy_horni, pravy_dolni):
        self.levy_horni = levy_horni
        self.pravy_dolni = pravy_dolni

def popis_tvaru(tvar):
    match tvar:
        case Bod(x=0, y=0):
            return "Bod v počátku"
        case Bod(x=x, y=0):
            return f"Bod na ose X: {x}"
        case Bod(x=x, y=y):
            return f"Bod ({x}, {y})"
        case Kruh(stred=Bod(x=0, y=0), polomer=r):
            return f"Kruh se středem v počátku, r={r}"
        case Kruh(stred=s, polomer=r):
            return f"Kruh se středem ({s.x},{s.y}), r={r}"
        case Obdelnik():
            return "Nějaký obdélník"

tvary = [
    Bod(0, 0), Bod(5, 0), Bod(3, 4),
    Kruh(Bod(0, 0), 10), Kruh(Bod(1, 2), 5),
    Obdelnik(Bod(0,0), Bod(10,10)),
]
for t in tvary:
    print(f"  {popis_tvaru(t)}")

# ── 5. Minihra s match ────────────────────────────────────────

print("\n=== Textová RPG s match ===")

stav = {"hp": 100, "mana": 50, "inventar": []}

while True:
    cmd = input("\n> ").strip().lower()
    match cmd.split():
        case ["konec"] | ["q"]:
            print("Nashledanou!")
            break
        case ["status"] | ["s"]:
            print(f"  HP: {stav['hp']}  Mana: {stav['mana']}  "
                  f"Inv: {stav['inventar'] or 'prázdný'}")
        case ["lec"] if stav["mana"] >= 20:
            stav["hp"] = min(100, stav["hp"] + 30)
            stav["mana"] -= 20
            print(f"  Vyléčil ses! HP: {stav['hp']}")
        case ["lec"]:
            print("  Nedostatek many!")
        case ["vezmi", predmet]:
            stav["inventar"].append(predmet)
            print(f"  Sebral jsi: {predmet}")
        case ["pouzij", predmet] if predmet in stav["inventar"]:
            stav["inventar"].remove(predmet)
            stav["hp"] = min(100, stav["hp"] + 50)
            print(f"  Použil jsi {predmet}. HP: {stav['hp']}")
        case ["pouzij", predmet]:
            print(f"  Nemáš {predmet}!")
        case _:
            print("  Příkazy: status, lec, vezmi <věc>, pouzij <věc>, konec")

# TVOJE ÚLOHA:
# 1. Přidej case ["utok", cil] do minihrý – odečti náhodný damage od HP.
# 2. Napiš funkci klasifikuj_cislo(n) s match: záporné/nula/malé/velké/obrovské.
# 3. Zkus walrus v: while chunk := file.read(1024) – simuluj čtení bloku.
