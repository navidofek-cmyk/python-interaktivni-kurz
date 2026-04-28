"""Reseni – Lekce 46: Regularni vyrazy"""

import re


# 1. Regex pro ceske PSC (5 cislic, ev. s mezerou: "110 00")

print("=== Ukol 1: Ceske PSC ===\n")

psc_vzor = re.compile(r"^\d{3}\s?\d{2}$")

psc_priklady = [
    ("110 00", True),
    ("60200",  True),
    ("602 00", True),
    ("1100",   False),   # kratke
    ("11000 ", False),   # mezera navic
    ("abc 00", False),   # ne-cisla
    ("110-00", False),   # spatny oddelovac
]

for psc, ocekavano in psc_priklady:
    ok = bool(psc_vzor.match(psc))
    stav = "OK" if ok == ocekavano else "FAIL"
    ikona = "V" if ok else "X"
    print(f"  [{stav}] {ikona} {psc!r:<12} (ocekavano: {ocekavano})")


# 2. Funkce maskuj_kartu(cislo) → "4111 **** **** 1111"

print("\n=== Ukol 2: maskuj_kartu() ===\n")


def maskuj_kartu(cislo: str) -> str:
    """Maskuje stredni skupiny cisel kreditni karty hvezdicky.
    Vstup: "4111111111111111" nebo "4111 1111 1111 1111"
    Vystup: "4111 **** **** 1111"
    """
    # Odstran mezery a pomlcky
    pouze_cisla = re.sub(r"[\s\-]", "", cislo)
    # Rozbij na skupiny po 4
    skupiny = re.findall(r"\d{4}", pouze_cisla)
    if len(skupiny) != 4:
        return re.sub(r"\d(?=\d{4})", "*", cislo)
    # Maskuj prostredni skupiny
    maskovaný = [skupiny[0]] + ["****"] * (len(skupiny) - 2) + [skupiny[-1]]
    return " ".join(maskovaný)


karty = [
    "4111111111111111",
    "4111 1111 1111 1111",
    "5500-0000-0000-0004",
    "378282246310005",     # 15 cislic (Amex) – fallback
]

for karta in karty:
    print(f"  {karta:<25} -> {maskuj_kartu(karta)}")


# 3. Parser CSV radku (zachova hodnoty v uvozovkach s carkou uvnitr)

print("\n=== Ukol 3: Parsovani CSV radku s uvozovkami ===\n")


def parsuj_csv_radek(radek: str) -> list[str]:
    """Spravne parsuje CSV radek.
    Zachova carky uvnitr uvozovek.
    Priklad: 'Jan,"Novak, Jr.",25' -> ['Jan', 'Novak, Jr.', '25']
    """
    vysledky = []
    # Regex: bud hodnota v uvozovkach, nebo bezna hodnota bez carka
    vzor = re.compile(r'"([^"]*(?:""[^"]*)*)"|([^,]*)')
    pozice = 0
    while pozice <= len(radek):
        m = vzor.match(radek, pozice)
        if not m:
            break
        if m.group(1) is not None:
            # Hodnota v uvozovkach – nahrad zdvojene uvozovky
            vysledky.append(m.group(1).replace('""', '"'))
        else:
            vysledky.append(m.group(2))
        pozice = m.end()
        if pozice < len(radek):
            if radek[pozice] == ',':
                pozice += 1   # preskoc carku
            else:
                break
    return vysledky


csv_radky = [
    'Jan,Novak,25',
    '"Novak, Jr.",Jan,25',
    '"Rosta ""Racek"" Kopriva",info@email.cz,"Praha, CZ"',
    'simple,hodnota,123',
    '"carky,uvnitr","a take ""uvozovky""",posledni',
]

for radek in csv_radky:
    sloupce = parsuj_csv_radek(radek)
    print(f"  Vstup:   {radek!r}")
    print(f"  Vystup:  {sloupce}")
    print()
