"""
LEKCE 39: Testování – unittest a TDD
======================================
Testy = kód, který ověřuje že tvůj kód funguje správně.
Bez testů zjistíš chybu až v produkci. Špatně.

unittest – vestavěný testovací framework (styl JUnit)
pytest   – populárnější, jednodušší syntaxe (lekce 40)

TDD (Test-Driven Development):
  1. Napiš test (selže – RED)
  2. Napiš minimální kód aby prošel (GREEN)
  3. Refaktoruj (REFACTOR)
  Opakuj.
"""

import unittest
from dataclasses import dataclass

# ══════════════════════════════════════════════════════════════
# KÓD KTERÝ BUDEME TESTOVAT
# ══════════════════════════════════════════════════════════════

def faktorial(n: int) -> int:
    if not isinstance(n, int):
        raise TypeError(f"Očekáváno int, dostali jsme {type(n).__name__}")
    if n < 0:
        raise ValueError(f"Faktoriál záporného čísla neexistuje: {n}")
    if n == 0:
        return 1
    return n * faktorial(n - 1)

def je_palindrom(s: str) -> bool:
    cistý = s.lower().replace(" ", "")
    return cistý == cistý[::-1]

def binarni_hledani(seznam: list, cil) -> int:
    """Vrátí index nebo -1."""
    levo, pravo = 0, len(seznam) - 1
    while levo <= pravo:
        stred = (levo + pravo) // 2
        if seznam[stred] == cil:
            return stred
        elif seznam[stred] < cil:
            levo = stred + 1
        else:
            pravo = stred - 1
    return -1

@dataclass
class BankovniUcet:
    vlastnik: str
    zustatek: float = 0.0

    def vklad(self, castka: float) -> None:
        if castka <= 0:
            raise ValueError("Vklad musí být kladný")
        self.zustatek += castka

    def vyber(self, castka: float) -> None:
        if castka <= 0:
            raise ValueError("Výběr musí být kladný")
        if castka > self.zustatek:
            raise ValueError(f"Nedostatek prostředků: máš {self.zustatek}, chceš {castka}")
        self.zustatek -= castka

    def prevod(self, cil: "BankovniUcet", castka: float) -> None:
        self.vyber(castka)
        cil.vklad(castka)


# ══════════════════════════════════════════════════════════════
# UNITTEST TESTY
# ══════════════════════════════════════════════════════════════

class TestFaktorial(unittest.TestCase):

    # Každá metoda začínající test_ je test
    def test_zakladni_pripady(self):
        self.assertEqual(faktorial(0), 1)
        self.assertEqual(faktorial(1), 1)
        self.assertEqual(faktorial(5), 120)
        self.assertEqual(faktorial(10), 3628800)

    def test_velke_cislo(self):
        self.assertEqual(faktorial(20), 2432902008176640000)

    def test_zaporny_vstup(self):
        with self.assertRaises(ValueError):
            faktorial(-1)
        with self.assertRaises(ValueError):
            faktorial(-100)

    def test_spatny_typ(self):
        with self.assertRaises(TypeError):
            faktorial(3.14)
        with self.assertRaises(TypeError):
            faktorial("5")

    def test_chybova_zprava(self):
        with self.assertRaises(ValueError) as ctx:
            faktorial(-5)
        self.assertIn("-5", str(ctx.exception))


class TestPalindrom(unittest.TestCase):

    def test_palindromy(self):
        palindromy = ["racecar", "level", "noon", "Radar",
                      "A man a plan a canal Panama",
                      "Was it a car or a cat I saw"]
        for s in palindromy:
            with self.subTest(s=s):   # subTest → zobrazí která hodnota selhala
                self.assertTrue(je_palindrom(s), f"{s!r} by měl být palindrom")

    def test_nepalindromy(self):
        for s in ["hello", "python", "world"]:
            with self.subTest(s=s):
                self.assertFalse(je_palindrom(s))

    def test_prazdny_retezec(self):
        self.assertTrue(je_palindrom(""))
        self.assertTrue(je_palindrom("a"))


class TestBinarniHledani(unittest.TestCase):

    def setUp(self):
        """Volá se před KAŽDÝM testem."""
        self.data = list(range(0, 20, 2))   # [0,2,4,...,18]

    def test_nalezeni_prvku(self):
        self.assertEqual(binarni_hledani(self.data, 10), 5)
        self.assertEqual(binarni_hledani(self.data, 0),  0)
        self.assertEqual(binarni_hledani(self.data, 18), 9)

    def test_nenalezeni(self):
        self.assertEqual(binarni_hledani(self.data, 7),  -1)
        self.assertEqual(binarni_hledani(self.data, -1), -1)
        self.assertEqual(binarni_hledani(self.data, 99), -1)

    def test_prazdny_seznam(self):
        self.assertEqual(binarni_hledani([], 5), -1)

    def test_jeden_prvek(self):
        self.assertEqual(binarni_hledani([42], 42),  0)
        self.assertEqual(binarni_hledani([42], 99), -1)


class TestBankovniUcet(unittest.TestCase):

    def setUp(self):
        self.ucet  = BankovniUcet("Míša", 1000.0)
        self.ucet2 = BankovniUcet("Tomáš", 500.0)

    def test_pocatecni_stav(self):
        self.assertEqual(self.ucet.vlastnik, "Míša")
        self.assertAlmostEqual(self.ucet.zustatek, 1000.0)

    def test_vklad(self):
        self.ucet.vklad(500)
        self.assertAlmostEqual(self.ucet.zustatek, 1500.0)

    def test_vklad_zaporny(self):
        with self.assertRaises(ValueError):
            self.ucet.vklad(-100)
        with self.assertRaises(ValueError):
            self.ucet.vklad(0)

    def test_vyber(self):
        self.ucet.vyber(300)
        self.assertAlmostEqual(self.ucet.zustatek, 700.0)

    def test_vyber_vice_nez_zustatek(self):
        with self.assertRaises(ValueError) as ctx:
            self.ucet.vyber(9999)
        self.assertIn("Nedostatek", str(ctx.exception))

    def test_prevod(self):
        self.ucet.prevod(self.ucet2, 200)
        self.assertAlmostEqual(self.ucet.zustatek,  800.0)
        self.assertAlmostEqual(self.ucet2.zustatek, 700.0)

    def test_prevod_nedostatek(self):
        with self.assertRaises(ValueError):
            self.ucet.prevod(self.ucet2, 9999)
        # Zůstatky se NESMÍ změnit při selhání
        self.assertAlmostEqual(self.ucet.zustatek,  1000.0)
        self.assertAlmostEqual(self.ucet2.zustatek,  500.0)

    def tearDown(self):
        """Volá se po KAŽDÉM testu (úklid)."""
        pass   # zde bychom např. zavřeli DB spojení


# ══════════════════════════════════════════════════════════════
# MOCK – nahrazení závislostí
# ══════════════════════════════════════════════════════════════

from unittest.mock import patch, MagicMock, call
import datetime

def pozdrav_uzivatele(jmeno: str) -> str:
    hodina = datetime.datetime.now().hour
    if hodina < 12:
        cas = "ráno"
    elif hodina < 18:
        cas = "odpoledne"
    else:
        cas = "večer"
    return f"Dobré {cas}, {jmeno}!"

class TestPozdrav(unittest.TestCase):

    def test_rano(self):
        # Zmrazíme čas na 8:00
        with patch("datetime.datetime") as mock_dt:
            mock_dt.now.return_value.hour = 8
            self.assertIn("ráno", pozdrav_uzivatele("Míša"))

    def test_odpoledne(self):
        with patch("datetime.datetime") as mock_dt:
            mock_dt.now.return_value.hour = 15
            self.assertIn("odpoledne", pozdrav_uzivatele("Míša"))

    def test_vecer(self):
        with patch("datetime.datetime") as mock_dt:
            mock_dt.now.return_value.hour = 21
            self.assertIn("večer", pozdrav_uzivatele("Míša"))


# ── Spuštění testů ────────────────────────────────────────────
if __name__ == "__main__":
    # Verbose: zobrazí každý test
    unittest.main(verbosity=2)

# Spuštění z terminálu:
#   python3 39_testovani.py
#   python3 -m pytest 39_testovani.py -v   (pokud máš pytest)

# TVOJE ÚLOHA:
# 1. Přidej test pro faktorial(0) == faktorial(1) == 1 pomocí subTest.
# 2. Napiš třídu Fronta a kompletní sadu testů pro push/pop/peek/is_empty.
# 3. Použij mock na patch("builtins.input") a otestuj funkci z lekce 3.
