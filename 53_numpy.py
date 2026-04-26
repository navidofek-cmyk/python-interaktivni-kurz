"""
LEKCE 53: NumPy – numerické výpočty
=====================================
pip install numpy

NumPy = Numerical Python. Základ datové vědy v Pythonu.
ndarray = N-dimenzionální pole – jako list, ale:
  - Operace probíhají v C → 10–100× rychlejší
  - Broadcast – operace na celém poli najednou
  - Velká matematická knihovna (linalg, fft, random...)

Kdy použít:
  - Matematické výpočty na velkých datech
  - Obrázky (3D pole: výška × šířka × kanály)
  - Strojové učení (vstupy do sklearn, torch, tensorflow)
"""

try:
    import numpy as np
    NUMPY_OK = True
except ImportError:
    print("NumPy není nainstalováno: pip install numpy")
    NUMPY_OK = False

import time

if not NUMPY_OK:
    exit()

# ══════════════════════════════════════════════════════════════
# ČÁST 1: VYTVÁŘENÍ POLÍ
# ══════════════════════════════════════════════════════════════

print("=== Vytváření polí ===\n")

a = np.array([1, 2, 3, 4, 5])
b = np.array([[1, 2, 3],
              [4, 5, 6],
              [7, 8, 9]])

print(f"1D pole: {a}  dtype={a.dtype}  shape={a.shape}")
print(f"2D pole:\n{b}  shape={b.shape}")

# Speciální pole
print(f"\nnp.zeros(5):   {np.zeros(5)}")
print(f"np.ones(4):    {np.ones(4)}")
print(f"np.eye(3):\n{np.eye(3)}")
print(f"np.arange(0,10,2): {np.arange(0,10,2)}")
print(f"np.linspace(0,1,5): {np.linspace(0,1,5)}")
print(f"np.random.randint(1,10,(2,3)):\n{np.random.randint(1,10,(2,3))}")


# ══════════════════════════════════════════════════════════════
# ČÁST 2: OPERACE – vektorizace
# ══════════════════════════════════════════════════════════════

print("\n=== Vektorizace ===\n")

x = np.array([1.0, 2.0, 3.0, 4.0, 5.0])

# Operace na celém poli najednou (broadcast)
print(f"x:        {x}")
print(f"x + 10:   {x + 10}")
print(f"x * 2:    {x * 2}")
print(f"x ** 2:   {x ** 2}")
print(f"np.sqrt(x): {np.sqrt(x)}")
print(f"np.sin(x):  {np.sin(x).round(3)}")

# Porovnání rychlosti: Python list vs NumPy
N = 1_000_000
lst = list(range(N))
arr = np.arange(N, dtype=float)

t0 = time.perf_counter()
vysledek_list = [x**2 for x in lst]
t_list = time.perf_counter() - t0

t0 = time.perf_counter()
vysledek_numpy = arr ** 2
t_numpy = time.perf_counter() - t0

print(f"\nN={N:_} prvků, operace x²:")
print(f"  Python list: {t_list*1000:.1f} ms")
print(f"  NumPy array: {t_numpy*1000:.1f} ms")
print(f"  Speedup:     {t_list/t_numpy:.0f}×")


# ══════════════════════════════════════════════════════════════
# ČÁST 3: INDEXOVÁNÍ A SLICING
# ══════════════════════════════════════════════════════════════

print("\n=== Indexování ===\n")

m = np.array([[1,2,3,4],
              [5,6,7,8],
              [9,10,11,12]])

print(f"m[1,2] = {m[1,2]}")          # řádek 1, sloupec 2
print(f"m[0] = {m[0]}")              # celý první řádek
print(f"m[:,2] = {m[:,2]}")          # celý třetí sloupec
print(f"m[0:2, 1:3] =\n{m[0:2,1:3]}")  # podmatice

# Boolean masking
data = np.array([3, -1, 7, -4, 2, 8, -2, 5])
print(f"\ndata:         {data}")
print(f"data > 0:     {data > 0}")
print(f"data[data>0]: {data[data > 0]}")    # filtrování
data[data < 0] = 0                           # nahrazení záporných
print(f"po nahrazení: {data}")


# ══════════════════════════════════════════════════════════════
# ČÁST 4: LINEÁRNÍ ALGEBRA
# ══════════════════════════════════════════════════════════════

print("\n=== Lineární algebra ===\n")

A = np.array([[2, 1],
              [5, 3]])
B = np.array([[1, 2],
              [3, 4]])

print(f"A @ B (maticové násobení):\n{A @ B}")
print(f"A.T (transponování):\n{A.T}")
print(f"np.linalg.det(A) = {np.linalg.det(A):.0f}")
print(f"np.linalg.inv(A):\n{np.linalg.inv(A)}")

# Řešení soustavy rovnic Ax = b
# 2x + y = 5
# 5x + 3y = 14
b_vec = np.array([5, 14])
x = np.linalg.solve(A, b_vec)
print(f"\nŘešení 2x+y=5, 5x+3y=14: x={x[0]:.0f}, y={x[1]:.0f}")

# Vlastní čísla a vektory
eigenvalues, eigenvectors = np.linalg.eig(A)
print(f"Vlastní čísla: {eigenvalues.round(3)}")


# ══════════════════════════════════════════════════════════════
# ČÁST 5: STATISTIKA A AGREGACE
# ══════════════════════════════════════════════════════════════

print("\n=== Statistika ===\n")

np.random.seed(42)
data = np.random.normal(loc=50, scale=15, size=1000)  # normální rozdělení

print(f"N = {len(data)}")
print(f"Průměr:     {data.mean():.2f}")
print(f"Medián:     {np.median(data):.2f}")
print(f"Rozptyl:    {data.var():.2f}")
print(f"Std. odch.: {data.std():.2f}")
print(f"Min / Max:  {data.min():.2f} / {data.max():.2f}")
print(f"Percentily: 25%={np.percentile(data,25):.1f}  75%={np.percentile(data,75):.1f}")

# Histogram v textu
hist, edges = np.histogram(data, bins=10)
print("\nHistogram:")
for i, (pocet, hrana) in enumerate(zip(hist, edges)):
    sloupec = "█" * (pocet // 10)
    print(f"  {hrana:5.0f}–{edges[i+1]:5.0f} |{sloupec} ({pocet})")


# ══════════════════════════════════════════════════════════════
# ČÁST 6: OBRÁZKY JAKO POLE
# ══════════════════════════════════════════════════════════════

print("\n=== Obrázky jako NumPy pole ===\n")

# Obrázek = 2D pole (šedotónový) nebo 3D pole (RGB)
# shape = (výška, šířka) nebo (výška, šířka, 3)

# Generuj syntetický "obrázek"
vyska, sirka = 8, 12
obrazek = np.zeros((vyska, sirka), dtype=np.uint8)

# Přidej bílý obdélník
obrazek[2:6, 3:9] = 255

# Přidej gradient
for y in range(vyska):
    for x in range(sirka):
        if obrazek[y, x] == 0:
            obrazek[y, x] = int(x / sirka * 128)

print("'Obrázek' 8×12 (ASCII art):")
znaky = " ░▒▓█"
for radek in obrazek:
    print("  " + "".join(znaky[v//52] for v in radek))

print(f"\nshape={obrazek.shape}, dtype={obrazek.dtype}")
print(f"Průměrná hodnota pixelu: {obrazek.mean():.1f}")
print(f"Inverze: min/max po 255-img = {(255-obrazek).min()}/{(255-obrazek).max()}")

# TVOJE ÚLOHA:
# 1. Vytvoř šachovnici 8×8 pomocí np.zeros a indexování.
# 2. Spočítej korelaci dvou náhodných polí (np.corrcoef).
# 3. Napiš funkci normalize(arr) → pole s hodnotami 0–1.
# 4. Implementuj konvoluci 3×3 blur filtrem (průměrování sousedů).
