"""Reseni – Lekce 53: NumPy"""

try:
    import numpy as np
    NUMPY_OK = True
except ImportError:
    print("NumPy neni nainstalovano: pip install numpy")
    NUMPY_OK = False

if not NUMPY_OK:
    exit()


# 1. Sachovnice 8x8 pomoci np.zeros a indexovani

print("=== Ukol 1: Sachovnice 8x8 ===\n")

sachovnice = np.zeros((8, 8), dtype=int)
sachovnice[1::2, ::2] = 1    # licha radka, sude sloupce
sachovnice[::2, 1::2] = 1    # suda radka, liche sloupce

print("Sachovnice 8x8 (1=bily, 0=cerny):")
for radek in sachovnice:
    print("  " + " ".join(str(c) for c in radek))

print(f"\nPocet bilych polí: {sachovnice.sum()} (ocekavano 32)")
print(f"Pocet cernych poli: {(sachovnice == 0).sum()} (ocekavano 32)")


# 2. Korelaciní koeficient dvou nahodnych poli

print("\n=== Ukol 2: Korelace nahodnych poli ===\n")

np.random.seed(42)
a = np.random.randn(1000)

# Kladna korelace
b_kladna = a + np.random.randn(1000) * 0.5

# Zaporna korelace
b_zaporna = -a + np.random.randn(1000) * 0.3

# Zadna korelace
b_nahodna = np.random.randn(1000)

for popis, b in [
    ("Kladna korelace", b_kladna),
    ("Zaporna korelace", b_zaporna),
    ("Nahodna (zadna)", b_nahodna),
]:
    korelace = np.corrcoef(a, b)[0, 1]
    print(f"  {popis:<25} r = {korelace:+.4f}")


# 3. Funkce normalize(arr) → pole s hodnotami 0–1

print("\n=== Ukol 3: normalize() funkce ===\n")


def normalize(arr: np.ndarray) -> np.ndarray:
    """Normalizuje pole do rozsahu [0, 1].
    Pouziva min-max normalizaci: (x - min) / (max - min)
    """
    mn = arr.min()
    mx = arr.max()
    if mx == mn:
        return np.zeros_like(arr, dtype=float)
    return (arr - mn) / (mx - mn)


priklady = [
    np.array([1.0, 2.0, 3.0, 4.0, 5.0]),
    np.array([0, 10, 50, 100]),
    np.array([-5.0, 0.0, 5.0]),
    np.random.randint(0, 100, 5).astype(float),
]

for pole in priklady:
    norm = normalize(pole)
    print(f"  Vstup: {pole}")
    print(f"  Norma: {norm.round(3)}")
    print(f"  Min={norm.min():.0f} Max={norm.max():.0f}\n")


# 4. Konvoluce 3x3 blur filtrem (prumerovani sousedu)

print("=== Ukol 4: Konvoluce 3x3 blur filtrem ===\n")


def blur_3x3(obraz: np.ndarray) -> np.ndarray:
    """Aplikuje 3x3 prumernovy blur filtr (box blur).
    Pro kazdy pixel vypocita prumer 3x3 okoli.
    Okrajove pixely zachova nezmenene.
    """
    vysledek = obraz.copy().astype(float)
    jadro = np.ones((3, 3)) / 9.0   # prumerovaci jadro

    radky, sloupce = obraz.shape
    # Prochazej vnitrni pixely (bez okraju)
    for r in range(1, radky - 1):
        for s in range(1, sloupce - 1):
            okoli = obraz[r-1:r+2, s-1:s+2]
            vysledek[r, s] = (okoli * jadro).sum()

    return vysledek


# Numpy vektorizovana verze (rychlejsi)
def blur_3x3_vekt(obraz: np.ndarray) -> np.ndarray:
    """Vektorizovana verze blur filtru bez smyckek."""
    padded = np.pad(obraz.astype(float), 1, mode="edge")
    vysledek = np.zeros_like(obraz, dtype=float)
    for dr in range(3):
        for ds in range(3):
            vysledek += padded[dr:dr+obraz.shape[0], ds:ds+obraz.shape[1]]
    return vysledek / 9.0


# Testovaci obrazek 6x6
np.random.seed(7)
obrazek = np.random.randint(0, 256, (6, 6))

print("Puvodni 'obraz' (6x6):")
print(obrazek)

zamazany = blur_3x3(obrazek)
print("\nPo blur filtru (zaokrouhleno):")
print(zamazany.round(1))

zamazany_v = blur_3x3_vekt(obrazek)
print(f"\nVysledky shodne (obe metody): {np.allclose(zamazany, zamazany_v)}")
print(f"Prumerna zmena pixelu: {np.abs(obrazek - zamazany).mean():.2f}")
