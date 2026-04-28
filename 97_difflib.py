"""
LEKCE 97: difflib – porovnání textu
=====================================
Naučíš se porovnávat texty, hledat rozdíly a
implementovat spell checker / detekci plagiarismu.

difflib je součástí standardní knihovny – žádná instalace.

Hlavní nástroje:
  SequenceMatcher  – obecné porovnání sekvencí (text, listy, ...)
  unified_diff     – git-like diff výstup
  context_diff     – context diff (starší formát)
  get_close_matches – fuzzy hledání podobných slov
  HtmlDiff         – HTML diff pro code review
  Differ           – řádkový diff se znaky +/-/?
"""

import difflib
import textwrap
from pathlib import Path
import tempfile

print("=== LEKCE 97: difflib – porovnání textu ===\n")

# ══════════════════════════════════════════════════════════════
# ČÁST 1: SequenceMatcher – podobnost dvou stringů
# ══════════════════════════════════════════════════════════════

print("── Část 1: SequenceMatcher.ratio() ──\n")

def podobnost(a: str, b: str) -> float:
    """Vrátí 0.0–1.0, kde 1.0 = identické."""
    return difflib.SequenceMatcher(None, a, b).ratio()

pary = [
    ("python",        "python"),
    ("python",        "Python"),
    ("python",        "pythoon"),
    ("python",        "pythen"),
    ("python",        "java"),
    ("hello world",   "hello Word"),
    ("Brno",          "Bnro"),          # přehozená písmena
    ("2024-01-15",    "2024-01-25"),    # jedno číslo jinak
]

print("  Porovnání podobnosti (0.0 = různé, 1.0 = stejné):")
for a, b in pary:
    skore = podobnost(a, b)
    barometr = "█" * int(skore * 20)
    print(f"  {a!r:<20} ↔ {b!r:<20} {skore:.2f} {barometr}")
print()

# quick_ratio() – rychlejší, nepřesná horní mez
a, b = "Toto je testovací věta.", "Toto je testovaci veta."
sm = difflib.SequenceMatcher(None, a, b)
print(f"  Přesný ratio():       {sm.ratio():.4f}")
print(f"  Rychlý quick_ratio(): {sm.quick_ratio():.4f}  (horní mez, rychlejší)")
print(f"  real_quick_ratio():   {sm.real_quick_ratio():.4f}  (ještě hrubší odhad)")
print()

# Matching blocks – kde jsou shody
print("  Matching blocks (kde se texty shodují):")
for blok in sm.get_matching_blocks():
    if blok.size > 0:
        ukázka = a[blok.a:blok.a + blok.size]
        print(f"    a[{blok.a}:{blok.a+blok.size}] = b[{blok.b}:{blok.b+blok.size}] : {ukázka!r}")
print()

# ══════════════════════════════════════════════════════════════
# ČÁST 2: unified_diff – git-like diff
# ══════════════════════════════════════════════════════════════

print("── Část 2: unified_diff – git-like výstup ──\n")

stary_kod = """\
def secti(a, b):
    return a + b

def odecti(a, b):
    return a - b

def vynasob(a, b):
    return a * b
""".splitlines(keepends=True)

novy_kod = """\
def secti(a: int, b: int) -> int:
    \"\"\"Sečte dvě čísla.\"\"\"
    return a + b

def odecti(a: int, b: int) -> int:
    return a - b

def vydel(a: float, b: float) -> float:
    if b == 0:
        raise ValueError("Dělení nulou!")
    return a / b
""".splitlines(keepends=True)

diff = difflib.unified_diff(
    stary_kod, novy_kod,
    fromfile="matika.py (původní)",
    tofile="matika.py (nová verze)",
    lineterm=""
)

print("  --- git diff výstup ---")
for radek in diff:
    if radek.startswith("+++") or radek.startswith("---"):
        print(f"  \033[1m{radek}\033[0m")
    elif radek.startswith("+"):
        print(f"  \033[32m{radek}\033[0m")   # zelená
    elif radek.startswith("-"):
        print(f"  \033[31m{radek}\033[0m")   # červená
    elif radek.startswith("@@"):
        print(f"  \033[36m{radek}\033[0m")   # cyan
    else:
        print(f"  {radek}")
print()

# ══════════════════════════════════════════════════════════════
# ČÁST 3: get_close_matches – spell checker / fuzzy hledání
# ══════════════════════════════════════════════════════════════

print("── Část 3: get_close_matches – spell checker ──\n")

SLOVNIK_CZ = [
    "python", "program", "funkce", "třída", "objekt", "metoda",
    "seznam", "slovník", "tuple", "string", "integer", "float",
    "boolean", "import", "modul", "balíček", "knihovna",
    "algoritmus", "rekurze", "iterace", "generátor", "dekorátor",
    "výjimka", "chyba", "testování", "ladění", "refaktoring",
    "databáze", "server", "klient", "api", "endpoint",
]

def spell_check(slovo: str, slovnik: list[str], n: int = 3) -> list[str]:
    """Vrátí až n nejpodobnějších slov ze slovníku."""
    return difflib.get_close_matches(slovo, slovnik, n=n, cutoff=0.6)

chybne_slovo = [
    "pyton",       # python
    "fnkce",       # funkce
    "algorytmus",  # algoritmus
    "generetor",   # generátor
    "databaze",    # databáze
    "rekursia",    # rekurze
    "xyxyxy",      # nic nenajde
]

print("  Spell checker (cutoff=0.6):")
for slovo in chybne_slovo:
    navrhy = spell_check(slovo, SLOVNIK_CZ)
    if navrhy:
        print(f"  {slovo!r:<15} → návrhy: {navrhy}")
    else:
        print(f"  {slovo!r:<15} → žádný návrh nenalezen")
print()

# Fuzzy hledání v příkazech (jako zsh / fish)
PRIKAZY = ["git status", "git commit", "git push", "git pull", "git log",
           "git diff", "git merge", "git rebase", "git stash", "git clone"]

def fuzzy_prikaz(vstup: str) -> list[str]:
    return difflib.get_close_matches(vstup, PRIKAZY, n=3, cutoff=0.4)

print("  Fuzzy hledání příkazů:")
testy = ["gt status", "git comit", "gut push", "git lgo"]
for t in testy:
    print(f"  '{t}' → {fuzzy_prikaz(t)}")
print()

# ══════════════════════════════════════════════════════════════
# ČÁST 4: Detekce plagiarismu
# ══════════════════════════════════════════════════════════════

print("── Část 4: Detekce plagiarismu ──\n")

PRACE = {
    "Original": """
        Rekurze je technika, kdy funkce volá sama sebe.
        Každé rekurzivní volání musí mít základní případ,
        jinak dojde k nekonečné smyčce a přetečení zásobníku.
        Klasický příklad je výpočet faktoriálu nebo Fibonacciho posloupnosti.
    """,
    "Pavel (mírná úprava)": """
        Rekurze je metoda, kdy funkce volá samu sebe.
        Každé rekurzivní volání musí mít základní podmínku,
        jinak nastane nekonečná smyčka a přetečení zásobníku.
        Typický příklad je výpočet faktoriálu nebo Fibonacciho řady.
    """,
    "Jana (vlastní práce)": """
        Rekurzivní funkce se odkazuje sama na sebe ve svém těle.
        Důležité je definovat ukončovací podmínku – bázový případ.
        Bez něj by program skončil chybou RecursionError.
        Rekurzi lze vždy nahradit iterací, ale někdy je elegantnější.
    """,
    "Tomáš (zkopírováno)": """
        Rekurze je technika, kdy funkce volá sama sebe.
        Každé rekurzivní volání musí mít základní případ,
        jinak dojde k nekonečné smyčce a přetečení zásobníku.
        Klasický příklad je výpočet faktoriálu nebo Fibonacciho posloupnosti.
    """,
}

original = PRACE["Original"]
print("  Podobnost s originálem (práh plagiarismu: 0.80):")
for jmeno, text in PRACE.items():
    skore = difflib.SequenceMatcher(None,
                                     original.split(), text.split()).ratio()
    status = "PLAGIÁT!" if skore >= 0.80 and jmeno != "Original" else "OK"
    if jmeno == "Original":
        status = "originál"
    print(f"  {jmeno:<25} podobnost={skore:.2f}  [{status}]")
print()

# ══════════════════════════════════════════════════════════════
# ČÁST 5: Differ – detailní řádkový diff
# ══════════════════════════════════════════════════════════════

print("── Část 5: Differ – detailní diff s ? markery ──\n")

text1 = ["Dobrý den\n", "Jak se máte?\n", "Nashledanou\n"]
text2 = ["Dobrý den\n", "Jak se daří?\n", "Na shledanou\n"]

d = difflib.Differ()
vysledek = list(d.compare(text1, text2))

print("  Differ výstup (? = pozice změny):")
for radek in vysledek:
    radek_strip = radek.rstrip()
    if radek.startswith("+ "):
        print(f"  \033[32m{radek_strip}\033[0m")
    elif radek.startswith("- "):
        print(f"  \033[31m{radek_strip}\033[0m")
    elif radek.startswith("? "):
        print(f"  \033[33m{radek_strip}\033[0m")
    else:
        print(f"  {radek_strip}")
print()

# ══════════════════════════════════════════════════════════════
# ČÁST 6: HtmlDiff – HTML výstup pro code review
# ══════════════════════════════════════════════════════════════

print("── Část 6: HtmlDiff – export do HTML ──\n")

html_soubor = Path(tempfile.gettempdir()) / "diff.html"

hd = difflib.HtmlDiff(wrapcolumn=60)
html = hd.make_file(
    stary_kod, novy_kod,
    fromdesc="matika.py (původní)",
    todesc="matika.py (nová verze)"
)

html_soubor.write_text(html, encoding="utf-8")
print(f"  HTML diff uložen: {html_soubor}")
print(f"  Velikost souboru: {html_soubor.stat().st_size:,} bajtů")
print(f"  Otevři v prohlížeči: firefox {html_soubor}")

html_soubor.unlink()
print(f"  (soubor pro ukázku smazán)\n")

# ══════════════════════════════════════════════════════════════
# TVOJE ÚLOHA:
# ══════════════════════════════════════════════════════════════
print("=" * 55)
print("TVOJE ÚLOHA:")
print("=" * 55)
print("""
1. Napiš spell checker pro Python klíčová slova. Vytvoř
   seznam všech Python klíčových slov (keyword.kwlist),
   pak napiš funkci oprav_kod(radek: str) -> str, která
   najde neznámá slova a navrhne opravy přes get_close_matches.
   Otestuj na: "def moja_fnkce(lst: lits) -> Non:"

2. Implementuj funkci `diff_souboru(soubor1, soubor2)`,
   která načte dva textové soubory a vypíše barevný
   unified_diff (+ zelená, - červená, @@ cyan) do terminálu.
   Přidej statistiku: počet přidaných / odebraných řádků.

3. Napiš funkci `nejpodobnejsi_otazka(dotaz: str,
   faq: dict[str, str]) -> tuple[str, str]`, která
   dostane otázku uživatele a slovník FAQ {otázka: odpověď}
   a vrátí nejpodobnější otázku a odpověď. Použij
   SequenceMatcher. Vytvoř aspoň 8 FAQ otázek a otestuj.

4. Implementuj verzovací systém pro textové soubory:
   - uloz_verzi(text: str) → uloží do listu verzí
   - zobraz_diff(verze1: int, verze2: int) → unified_diff
   - vrat_verzi(cislo: int) → vrátí text dané verze
   Simuluj editaci dokumentu ve 4 krocích a zobraz diff
   mezi verzí 1 a 4.
""")
