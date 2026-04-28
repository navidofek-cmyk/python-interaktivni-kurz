"""Řešení – Lekce 39: Testování – unittest a TDD"""

import unittest
from dataclasses import dataclass
from unittest.mock import patch, MagicMock


# ── Funkce z originální lekce (musíme je mít zde) ────────────────────────────

def faktorial(n: int) -> int:
    if not isinstance(n, int):
        raise TypeError(f"Očekáváno int, dostali jsme {type(n).__name__}")
    if n < 0:
        raise ValueError(f"Faktoriál záporného čísla neexistuje: {n}")
    if n == 0:
        return 1
    return n * faktorial(n - 1)


def je_palindrom(s: str) -> bool:
    cisty = s.lower().replace(" ", "")
    return cisty == cisty[::-1]


# ── 1. Test faktorial(0) == faktorial(1) == 1 pomocí subTest ─────────────────

class TestFaktorialSubTest(unittest.TestCase):

    def test_zakladni_pripady_subtest(self):
        """Testuje faktoriál 0 a 1 pomocí subTest – zobrazí která hodnota selhala."""
        # subTest vrátí kontext, který při selhání zobrazí aktuální hodnotu n
        # Výhoda: všechny iterace se otestují, ne jen první selhání
        ocekavana = {0: 1, 1: 1, 5: 120, 10: 3628800}
        for n, expected in ocekavana.items():
            with self.subTest(n=n):
                self.assertEqual(faktorial(n), expected,
                                 f"faktorial({n}) by mělo být {expected}")

    def test_faktorial_nuly_a_jednicka_jsou_stejne(self):
        """0! == 1! == 1 – oba jsou definovány jako 1."""
        with self.subTest(n=0):
            self.assertEqual(faktorial(0), 1)
        with self.subTest(n=1):
            self.assertEqual(faktorial(1), 1)
        # Explicitně ověříme rovnost
        self.assertEqual(faktorial(0), faktorial(1))


# ── 2. Třída Fronta a kompletní sada testů ────────────────────────────────────

class Fronta:
    """FIFO fronta – testovací třída."""

    def __init__(self):
        self._prvky = []

    def push(self, prvek) -> None:
        self._prvky.append(prvek)

    def pop(self):
        if self.is_empty():
            raise IndexError("Fronta je prázdná")
        return self._prvky.pop(0)

    def peek(self):
        if self.is_empty():
            raise IndexError("Fronta je prázdná")
        return self._prvky[0]

    def is_empty(self) -> bool:
        return len(self._prvky) == 0

    def __len__(self) -> int:
        return len(self._prvky)


class TestFronta(unittest.TestCase):

    def setUp(self):
        """Před každým testem vytvoří čistou prázdnou frontu."""
        self.f = Fronta()

    def test_nova_fronta_je_prazdna(self):
        """Nová fronta musí být prázdná."""
        self.assertTrue(self.f.is_empty())
        self.assertEqual(len(self.f), 0)

    def test_push_prvek(self):
        """Po push() fronta není prázdná."""
        self.f.push(42)
        self.assertFalse(self.f.is_empty())
        self.assertEqual(len(self.f), 1)

    def test_push_vice_prvku(self):
        """Vložíme více prvků a ověříme délku."""
        for i in range(5):
            self.f.push(i)
        self.assertEqual(len(self.f), 5)

    def test_pop_fifo_poradi(self):
        """FIFO: první vložený je první odebraný."""
        for x in [10, 20, 30]:
            self.f.push(x)
        self.assertEqual(self.f.pop(), 10)
        self.assertEqual(self.f.pop(), 20)
        self.assertEqual(self.f.pop(), 30)

    def test_pop_snizi_delku(self):
        """Pop sníží délku fronty o 1."""
        self.f.push("a")
        self.f.push("b")
        self.f.pop()
        self.assertEqual(len(self.f), 1)

    def test_pop_prazdna_vyhodi_vyjimku(self):
        """Pop z prázdné fronty vyhodí IndexError."""
        with self.assertRaises(IndexError):
            self.f.pop()

    def test_peek_vraci_prvni_bez_odebrání(self):
        """peek() vrátí první prvek, ale neodebere ho."""
        self.f.push("první")
        self.f.push("druhý")
        self.assertEqual(self.f.peek(), "první")
        self.assertEqual(len(self.f), 2)  # délka se nezměnila

    def test_peek_prazdna_vyhodi_vyjimku(self):
        """peek() z prázdné fronty vyhodí IndexError."""
        with self.assertRaises(IndexError):
            self.f.peek()

    def test_is_empty_po_pop_all(self):
        """Fronta je prázdná po odebrání všech prvků."""
        self.f.push(1)
        self.f.pop()
        self.assertTrue(self.f.is_empty())

    def test_ruzne_typy(self):
        """Fronta funguje s libovolnými typy."""
        self.f.push("text")
        self.f.push(42)
        self.f.push([1, 2, 3])
        with self.subTest("pop string"):
            self.assertEqual(self.f.pop(), "text")
        with self.subTest("pop int"):
            self.assertEqual(self.f.pop(), 42)
        with self.subTest("pop list"):
            self.assertEqual(self.f.pop(), [1, 2, 3])


# ── 3. Mock na patch("builtins.input") ───────────────────────────────────────
# Mockujeme input() tak, aby funkce nevyžadovala opravdový vstup od uživatele

def ziskej_jmeno_uzivatele() -> str:
    """Funkce z lekce 3 – ptá se na jméno."""
    jmeno = input("Jak se jmenuješ? ").strip()
    if not jmeno:
        return "Anonymní"
    return jmeno.capitalize()


def nacti_cislo(prompt: str, min_val: int = 0, max_val: int = 100) -> int:
    """Načte číslo v rozsahu."""
    while True:
        try:
            hodnota = int(input(prompt))
            if min_val <= hodnota <= max_val:
                return hodnota
            print(f"Zadej číslo mezi {min_val} a {max_val}.")
        except ValueError:
            print("Neplatný vstup!")


class TestInputMock(unittest.TestCase):

    def test_ziskej_jmeno_normalni(self):
        """Testuje normální vstup se jménem."""
        # patch nahradí builtins.input naším mock objektem
        with patch("builtins.input", return_value="míša"):
            vysledek = ziskej_jmeno_uzivatele()
        self.assertEqual(vysledek, "Míša")  # capitalize

    def test_ziskej_jmeno_prazdne(self):
        """Prázdný vstup → 'Anonymní'."""
        with patch("builtins.input", return_value="   "):
            vysledek = ziskej_jmeno_uzivatele()
        self.assertEqual(vysledek, "Anonymní")

    def test_ziskej_jmeno_s_mezerami(self):
        """Strip odstraní okolní mezery."""
        with patch("builtins.input", return_value="  tomáš  "):
            vysledek = ziskej_jmeno_uzivatele()
        self.assertEqual(vysledek, "Tomáš")

    def test_nacti_cislo_validni(self):
        """Platné číslo v rozsahu."""
        with patch("builtins.input", return_value="42"):
            vysledek = nacti_cislo("Zadej číslo: ", 0, 100)
        self.assertEqual(vysledek, 42)

    def test_nacti_cislo_retry(self):
        """První vstup neplatný, druhý OK → musí se zeptat znovu."""
        with patch("builtins.input", side_effect=["abc", "200", "50"]):
            # "abc" vyhodí ValueError → zkusí znovu
            # "200" je mimo rozsah → zkusí znovu
            # "50" je platné
            vysledek = nacti_cislo("Zadej číslo: ", 0, 100)
        self.assertEqual(vysledek, 50)


# ── Spuštění testů ────────────────────────────────────────────────────────────

if __name__ == "__main__":
    unittest.main(verbosity=2)
