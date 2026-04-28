"""Řešení – Lekce 97: difflib – porovnání textu

Toto je vzorové řešení úloh z lekce 97.
"""

import difflib
import keyword
import tempfile
from pathlib import Path

# ── Úloha 1 ────────────────────────────────────────────────
# Spell checker pro Python klíčová slova.
# Funkce oprav_kod(radek) navrhne opravy přes get_close_matches.

PYTHON_KLICOVA_SLOVA = keyword.kwlist + list(keyword.__builtins__) if hasattr(keyword, "__builtins__") else keyword.kwlist

# Pro jistotu přidáme i základní built-ins
import builtins
SLOVNIK = sorted(set(keyword.kwlist) | set(dir(builtins)))


def oprav_kod(radek: str) -> str:
    """
    Projde tokeny řádku, najde neznámá slova a navrhne opravy.
    Vrátí řádek s komentářem # OPRAVA: ... pro každé podezřelé slovo.
    """
    # Jednoduchá tokenizace – rozdělit na "slova" (identifikátory)
    import re
    tokeny = re.findall(r"[a-zA-Z_][a-zA-Z0-9_]*", radek)
    opravy = {}
    for token in tokeny:
        if token in SLOVNIK:
            continue   # správné slovo
        navrhy = difflib.get_close_matches(token, SLOVNIK, n=2, cutoff=0.7)
        if navrhy:
            opravy[token] = navrhy

    if not opravy:
        return radek + "  # vše OK"
    komentare = ", ".join(f"{k} → {v}" for k, v in opravy.items())
    return radek + f"  # OPRAVA: {komentare}"


print("Úloha 1 – spell checker pro Python kód:")
testovaci_radky = [
    "def moja_fnkce(lst: lits) -> Non:",
    "for i inn rang(10):",
    "if x == True and y != Fasle:",
    "print('ahoj')",
]
for r in testovaci_radky:
    print(f"  Vstup:  {r}")
    print(f"  Výstup: {oprav_kod(r)}")
    print()


# ── Úloha 2 ────────────────────────────────────────────────
# diff_souboru(soubor1, soubor2) – barevný unified_diff + statistika.

def diff_souboru(soubor1: str, soubor2: str) -> None:
    """Načte dva soubory a vypíše barevný unified_diff se statistikou."""
    radky1 = Path(soubor1).read_text(encoding="utf-8").splitlines(keepends=True)
    radky2 = Path(soubor2).read_text(encoding="utf-8").splitlines(keepends=True)

    diff = list(difflib.unified_diff(
        radky1, radky2,
        fromfile=soubor1,
        tofile=soubor2,
        lineterm="",
    ))

    pridano = sum(1 for r in diff if r.startswith("+") and not r.startswith("+++"))
    odebrano = sum(1 for r in diff if r.startswith("-") and not r.startswith("---"))

    for radek in diff:
        r = radek.rstrip()
        if r.startswith("+++") or r.startswith("---"):
            print(f"\033[1m{r}\033[0m")
        elif r.startswith("+"):
            print(f"\033[32m{r}\033[0m")
        elif r.startswith("-"):
            print(f"\033[31m{r}\033[0m")
        elif r.startswith("@@"):
            print(f"\033[36m{r}\033[0m")
        else:
            print(r)

    print(f"\n  Statistika: +{pridano} přidáno, -{odebrano} odebráno")


# Vytvoříme dva dočasné soubory pro ukázku
soubor_a = Path(tempfile.gettempdir()) / "verze_a.txt"
soubor_b = Path(tempfile.gettempdir()) / "verze_b.txt"
soubor_a.write_text("řádek jedna\nřádek dva\nřádek tři\n", encoding="utf-8")
soubor_b.write_text("řádek jedna\nřádek DVA (změněno)\nřádek tři\nřádek čtyři (nový)\n", encoding="utf-8")

print("Úloha 2 – diff_souboru():")
diff_souboru(str(soubor_a), str(soubor_b))
soubor_a.unlink()
soubor_b.unlink()
print()


# ── Úloha 3 ────────────────────────────────────────────────
# nejpodobnejsi_otazka(dotaz, faq) – najde nejpodobnější FAQ otázku.

FAQ = {
    "Jak nainstaluji Python?": "Stáhni instalátor z python.org a spusť ho.",
    "Co je to virtuální prostředí?": "Izolovaná instalace Pythonu pro projekt. Vytvoříš ho přes `python -m venv .venv`.",
    "Jak spustím Python skript?": "V terminálu zadej `python3 skript.py`.",
    "Co je pip?": "Správce balíčků pro Python. Instalace: `pip install nazev_balicku`.",
    "Jak debugovat Python kód?": "Použij `breakpoint()` v kódu nebo spusť `python -m pdb skript.py`.",
    "Co je list comprehension?": "Zkrácený zápis pro vytvoření listu: `[x*2 for x in range(10)]`.",
    "Jak načíst soubor v Pythonu?": "Použij `with open('soubor.txt') as f: obsah = f.read()`.",
    "Co jsou dekorátory?": "Funkce obalující jinou funkci. Zapisují se jako `@dekorator` nad definicí funkce.",
    "Jak funguje GIL?": "Global Interpreter Lock blokuje paralelní spouštění Python bytekódu ve více vláknech.",
    "Co je asyncio?": "Knihovna pro asynchronní I/O programování pomocí klíčových slov async/await.",
}


def nejpodobnejsi_otazka(dotaz: str, faq: dict[str, str]) -> tuple[str, str]:
    """Najde nejpodobnější otázku ve FAQ a vrátí (otázka, odpověď)."""
    otazky = list(faq.keys())
    nejlepsi_otazka = max(
        otazky,
        key=lambda o: difflib.SequenceMatcher(None, dotaz.lower(), o.lower()).ratio()
    )
    return nejlepsi_otazka, faq[nejlepsi_otazka]


print("Úloha 3 – nejpodobnejsi_otazka():")
testy = [
    "jak nainstalovat python",
    "co je venv",
    "jak spustit skript",
    "co delá pip install",
    "jak ladim kod",
    "co je list comprehension",
]
for t in testy:
    otazka, odpoved = nejpodobnejsi_otazka(t, FAQ)
    shoda = difflib.SequenceMatcher(None, t.lower(), otazka.lower()).ratio()
    print(f"  Dotaz:   '{t}'")
    print(f"  FAQ:     '{otazka}'  (shoda={shoda:.2f})")
    print(f"  Odpověď: {odpoved[:60]}...")
    print()


# ── Úloha 4 ────────────────────────────────────────────────
# Verzovací systém pro textové soubory.

class VerzovaniTextu:
    """Jednoduchý verzovací systém – ukládá historii textů."""

    def __init__(self):
        self._verze: list[str] = []

    def uloz_verzi(self, text: str) -> int:
        """Uloží verzi, vrátí číslo verze (1-based)."""
        self._verze.append(text)
        return len(self._verze)

    def zobraz_diff(self, verze1: int, verze2: int) -> None:
        """Zobrazí unified_diff mezi dvěma verzemi (1-based indexy)."""
        t1 = self._verze[verze1 - 1].splitlines(keepends=True)
        t2 = self._verze[verze2 - 1].splitlines(keepends=True)
        diff = difflib.unified_diff(
            t1, t2,
            fromfile=f"verze {verze1}",
            tofile=f"verze {verze2}",
            lineterm="",
        )
        for radek in diff:
            r = radek.rstrip()
            if r.startswith("+") and not r.startswith("+++"):
                print(f"\033[32m  {r}\033[0m")
            elif r.startswith("-") and not r.startswith("---"):
                print(f"\033[31m  {r}\033[0m")
            elif r.startswith("@@"):
                print(f"\033[36m  {r}\033[0m")
            else:
                print(f"  {r}")

    def vrat_verzi(self, cislo: int) -> str:
        """Vrátí text dané verze (1-based)."""
        return self._verze[cislo - 1]

    def pocet_verzi(self) -> int:
        return len(self._verze)


vcs = VerzovaniTextu()

v1 = """Funkce v Pythonu se definují klíčovým slovem def.
Funkce mohou přijímat argumenty a vracet hodnoty.
Každá funkce by měla dělat jednu věc."""

v2 = """Funkce v Pythonu se definují klíčovým slovem def.
Funkce mohou přijímat argumenty a vracet hodnoty.
Každá funkce by měla dělat jednu věc.
Doporučuje se psát docstringy."""

v3 = """Funkce v Pythonu se definují klíčovým slovem def.
Mohou přijímat libovolný počet argumentů.
Každá funkce by měla dělat jednu věc.
Doporučuje se psát docstringy."""

v4 = """Funkce v Pythonu se definují pomocí def.
Mohou přijímat libovolný počet argumentů (*args, **kwargs).
Každá funkce by měla mít jednu odpovědnost (SRP).
Doporučuje se psát docstringy pro dokumentaci."""

for text in [v1, v2, v3, v4]:
    vcs.uloz_verzi(text)

print("Úloha 4 – verzovací systém:")
print(f"  Celkem verzí: {vcs.pocet_verzi()}")
print()
print("  Diff verze 1 → verze 4:")
vcs.zobraz_diff(1, 4)
print()
print(f"  Verze 2 (první 2 řádky): {vcs.vrat_verzi(2).splitlines()[0][:50]}...")
