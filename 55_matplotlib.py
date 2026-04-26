"""
LEKCE 55: Matplotlib – vizualizace dat
========================================
pip install matplotlib

Matplotlib je základní vizualizační knihovna Pythonu.
Grafy ukládáme do souborů (PNG), nevyžaduje GUI.

Typy grafů:
  plot()    – čárový graf
  scatter() – bodový graf
  bar()     – sloupcový graf
  hist()    – histogram
  pie()     – koláčový
  imshow()  – obrázky / heatmapy
  subplot() – více grafů vedle sebe
"""

try:
    import matplotlib
    matplotlib.use("Agg")   # bez GUI – ukládáme do souborů
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    import numpy as np
    MPL_OK = True
except ImportError:
    print("Matplotlib není nainstalováno: pip install matplotlib numpy")
    MPL_OK = False

from pathlib import Path
import math

if not MPL_OK:
    exit()

np.random.seed(42)
VYSTUP = Path("grafy")
VYSTUP.mkdir(exist_ok=True)

def uloz(nazev: str):
    cesta = VYSTUP / nazev
    plt.savefig(cesta, dpi=100, bbox_inches="tight")
    plt.close()
    print(f"  ✓ {cesta}")


# ══════════════════════════════════════════════════════════════
# ČÁST 1: Čárový graf
# ══════════════════════════════════════════════════════════════

print("=== Grafy uloženy do grafy/ ===\n")

fig, ax = plt.subplots(figsize=(10, 5))

x = np.linspace(0, 4 * math.pi, 300)
ax.plot(x, np.sin(x),   label="sin(x)",   color="#58a6ff", linewidth=2)
ax.plot(x, np.cos(x),   label="cos(x)",   color="#ff7b72", linewidth=2)
ax.plot(x, np.sin(2*x), label="sin(2x)",  color="#3fb950", linewidth=1.5, linestyle="--")

ax.axhline(0, color="gray", linewidth=0.5)
ax.set_title("Trigonometrické funkce", fontsize=14, fontweight="bold")
ax.set_xlabel("x")
ax.set_ylabel("y")
ax.legend()
ax.grid(True, alpha=0.3)
ax.set_facecolor("#0d1117")
fig.patch.set_facecolor("#161b22")
ax.tick_params(colors="white"); ax.xaxis.label.set_color("white")
ax.yaxis.label.set_color("white"); ax.title.set_color("white")
[s.set_color("#30363d") for s in ax.spines.values()]
ax.tick_params(colors="#8b949e"); ax.legend(facecolor="#1c2128", labelcolor="white")
uloz("01_carovy_graf.png")


# ══════════════════════════════════════════════════════════════
# ČÁST 2: Bodový graf + regresní přímka
# ══════════════════════════════════════════════════════════════

uceni = np.array([1,2,3,4,5,6,7,8,9,10])
body  = uceni * 8 + np.random.randn(10) * 5

fig, ax = plt.subplots(figsize=(8, 5))
ax.scatter(uceni, body, color="#58a6ff", s=80, zorder=3, label="Studenti")

# Lineární regrese
koef = np.polyfit(uceni, body, 1)
reg_x = np.linspace(uceni.min(), uceni.max(), 100)
reg_y = np.polyval(koef, reg_x)
ax.plot(reg_x, reg_y, color="#ff7b72", linewidth=2, label=f"Regrese: y={koef[0]:.1f}x+{koef[1]:.1f}")

ax.set_title("Hodiny učení vs. body")
ax.set_xlabel("Hodiny učení za týden")
ax.set_ylabel("Body v testu")
ax.legend(); ax.grid(True, alpha=0.3)
uloz("02_scatter_regrese.png")


# ══════════════════════════════════════════════════════════════
# ČÁST 3: Sloupcový graf + chybové úsečky
# ══════════════════════════════════════════════════════════════

predmety = ["Matematika", "Fyzika", "Informatika", "Biologie", "Chemie"]
prumery  = [78.3, 82.1, 91.5, 69.8, 74.2]
odchylky = [8.2, 6.5, 5.1, 9.3, 7.8]
barvy    = ["#58a6ff","#3fb950","#d2a8ff","#ffa657","#ff7b72"]

fig, ax = plt.subplots(figsize=(10, 5))
bars = ax.bar(predmety, prumery, color=barvy, alpha=0.85,
               yerr=odchylky, capsize=5, error_kw={"ecolor": "white", "alpha": 0.7})

for bar, val in zip(bars, prumery):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1.5,
            f"{val:.1f}", ha="center", va="bottom", fontsize=10, fontweight="bold")

ax.axhline(80, color="yellow", linewidth=1, linestyle="--", alpha=0.7, label="Průměr 80")
ax.set_title("Průměrné body podle předmětu")
ax.set_ylabel("Body")
ax.set_ylim(0, 110)
ax.legend(); ax.grid(True, axis="y", alpha=0.3)
uloz("03_sloupce_chybove_usecky.png")


# ══════════════════════════════════════════════════════════════
# ČÁST 4: Histogram + normální rozdělení
# ══════════════════════════════════════════════════════════════

data = np.concatenate([
    np.random.normal(60, 10, 300),
    np.random.normal(85, 8, 200),
])

fig, ax = plt.subplots(figsize=(9, 5))
n, bins, patches = ax.hist(data, bins=30, density=True, alpha=0.7,
                            color="#58a6ff", edgecolor="#30363d")

from scipy.stats import norm as scipy_norm  # noqa
try:
    mu, sigma = data.mean(), data.std()
    x_fit = np.linspace(data.min(), data.max(), 200)
    ax.plot(x_fit, scipy_norm.pdf(x_fit, mu, sigma),
            color="#ff7b72", linewidth=2, label=f"N({mu:.1f}, {sigma:.1f}²)")
    ax.legend()
except ImportError:
    ax.axvline(data.mean(), color="red", linewidth=2, label=f"Průměr {data.mean():.1f}")
    ax.legend()

ax.set_title("Distribuce bodů (bimodální)")
ax.set_xlabel("Body"); ax.set_ylabel("Hustota")
ax.grid(True, alpha=0.3)
uloz("04_histogram.png")


# ══════════════════════════════════════════════════════════════
# ČÁST 5: Heatmapa (korelační matice)
# ══════════════════════════════════════════════════════════════

matice = np.array([
    [1.00, 0.82, 0.45, -0.23],
    [0.82, 1.00, 0.31, -0.15],
    [0.45, 0.31, 1.00,  0.67],
    [-0.23, -0.15, 0.67, 1.00],
])
predmety4 = ["Mat", "Fyz", "Inf", "Bio"]

fig, ax = plt.subplots(figsize=(6, 5))
im = ax.imshow(matice, cmap="RdYlGn", vmin=-1, vmax=1, aspect="auto")
plt.colorbar(im, ax=ax, label="Korelace")

ax.set_xticks(range(4)); ax.set_yticks(range(4))
ax.set_xticklabels(predmety4); ax.set_yticklabels(predmety4)
for i in range(4):
    for j in range(4):
        ax.text(j, i, f"{matice[i,j]:.2f}", ha="center", va="center",
                fontsize=11, fontweight="bold",
                color="black" if abs(matice[i,j]) < 0.5 else "white")

ax.set_title("Korelační matice předmětů")
uloz("05_heatmapa.png")


# ══════════════════════════════════════════════════════════════
# ČÁST 6: Dashboard – více grafů
# ══════════════════════════════════════════════════════════════

fig = plt.figure(figsize=(14, 8))
fig.suptitle("Studijní přehled", fontsize=16, fontweight="bold")

# Levý nahoře: čárový vývoj
ax1 = fig.add_subplot(2, 2, 1)
mesice = ["Led", "Úno", "Bře", "Dub", "Kvě", "Čvn"]
ax1.plot(mesice, [70,73,78,82,87,91], marker="o", color="#58a6ff")
ax1.set_title("Vývoj bodů"); ax1.grid(True, alpha=0.3)

# Pravý nahoře: koláčový
ax2 = fig.add_subplot(2, 2, 2)
sektory = [35, 28, 22, 15]
popisky = ["Výborný\n(90+)", "Dobrý\n(75-90)", "Průměrný\n(60-75)", "Nedost.\n(<60)"]
barvy2 = ["#3fb950","#58a6ff","#d2a8ff","#ff7b72"]
ax2.pie(sektory, labels=popisky, colors=barvy2, autopct="%1.0f%%", startangle=90)
ax2.set_title("Rozdělení výsledků")

# Levý dole: sloupcový
ax3 = fig.add_subplot(2, 2, 3)
ax3.bar(predmety, prumery, color=barvy, alpha=0.8)
ax3.set_title("Body dle předmětu"); ax3.set_ylabel("Průměr")
ax3.grid(True, axis="y", alpha=0.3)

# Pravý dole: scatter
ax4 = fig.add_subplot(2, 2, 4)
ax4.scatter(uceni, body, color="#ffa657", alpha=0.8)
ax4.set_title("Učení vs. body")
ax4.set_xlabel("Hodiny/týden"); ax4.grid(True, alpha=0.3)

plt.tight_layout()
uloz("06_dashboard.png")

print(f"\nVšechny grafy jsou v: {VYSTUP.absolute()}")
print("Otevři libovolný PNG soubor pro zobrazení.")

# TVOJE ÚLOHA:
# 1. Přidej do dashboardu pátý graf (histogram).
# 2. Nakresli Mandelbrotovu množinu jako heatmapu (imshow).
# 3. Animuj sin vlnu – plt.FuncAnimation (ulož jako GIF).
