"""Reseni – Lekce 55: Matplotlib"""

try:
    import matplotlib
    matplotlib.use("Agg")  # bez GUI – ukládáme do souboru
    import matplotlib.pyplot as plt
    import matplotlib.colors as mcolors
    import numpy as np
    MPL_OK = True
except ImportError:
    print("Matplotlib neni nainstalovano: pip install matplotlib numpy")
    MPL_OK = False

import math
from pathlib import Path

if not MPL_OK:
    exit()

np.random.seed(42)
VYSTUP = Path("grafy_reseni")
VYSTUP.mkdir(exist_ok=True)


def uloz(nazev: str) -> None:
    cesta = VYSTUP / nazev
    plt.savefig(cesta, dpi=100, bbox_inches="tight")
    plt.close()
    print(f"  Ulozen: {cesta}")


# 1. Histogram – paty graf k dashboardu

print("=== Ukol 1: Histogram ===\n")

data_body = np.concatenate([
    np.random.normal(75, 12, 60),   # vetsinova skupina
    np.random.normal(45, 8, 20),    # slabsi skupina
])
data_body = np.clip(data_body, 0, 100)

fig, ax = plt.subplots(figsize=(8, 5))
n, bins, patches = ax.hist(data_body, bins=15, edgecolor="white", linewidth=0.5)

# Obarvi sloupce dle hodnoty (zelena = uspech, cervena = neuspech)
for patch, left_edge in zip(patches, bins[:-1]):
    if left_edge >= 50:
        patch.set_facecolor("#3fb950")
    else:
        patch.set_facecolor("#f85149")

ax.axvline(x=50, color="yellow", linestyle="--", linewidth=2, label="Min. hranice (50)")
ax.axvline(x=data_body.mean(), color="cyan", linestyle=":", linewidth=2,
           label=f"Prumer ({data_body.mean():.1f})")

ax.set_title("Rozdeleni bodu studentu", fontsize=13, fontweight="bold", color="white")
ax.set_xlabel("Body", color="white")
ax.set_ylabel("Pocet studentu", color="white")
ax.legend(facecolor="#1c2128", labelcolor="white")
ax.set_facecolor("#0d1117")
fig.patch.set_facecolor("#161b22")
ax.tick_params(colors="#8b949e")
for s in ax.spines.values():
    s.set_color("#30363d")

uloz("05_histogram.png")


# 2. Mandelbrotova mnozina jako heatmapa

print("\n=== Ukol 2: Mandelbrotova mnozina ===\n")


def mandelbrot(c: complex, max_iter: int = 100) -> int:
    """Pocet iteraci pred divergenci – jadro Mandelbrotovy mnoziny."""
    z = 0
    for i in range(max_iter):
        if abs(z) > 2:
            return i
        z = z * z + c
    return max_iter


def generuj_mandelbrot(
    sirka: int = 400,
    vyska: int = 300,
    x_min: float = -2.5, x_max: float = 1.0,
    y_min: float = -1.2, y_max: float = 1.2,
    max_iter: int = 80,
) -> np.ndarray:
    """Generuje 2D pole s hodnotami iteraci."""
    x = np.linspace(x_min, x_max, sirka)
    y = np.linspace(y_min, y_max, vyska)
    X, Y = np.meshgrid(x, y)
    C = X + 1j * Y

    Z = np.zeros_like(C)
    vysledek = np.zeros(C.shape, dtype=int)
    maska = np.ones(C.shape, dtype=bool)

    for i in range(max_iter):
        Z[maska] = Z[maska] ** 2 + C[maska]
        diverguje = maska & (np.abs(Z) > 2)
        vysledek[diverguje] = i
        maska[diverguje] = False

    return vysledek


print("  Generuji Mandelbrotovu mnozinu...")
mandel = generuj_mandelbrot(sirka=500, vyska=380, max_iter=80)

fig, ax = plt.subplots(figsize=(10, 7))
im = ax.imshow(
    mandel,
    extent=[-2.5, 1.0, -1.2, 1.2],
    origin="lower",
    cmap="inferno",
    interpolation="bilinear",
)
plt.colorbar(im, ax=ax, label="Pocet iteraci")
ax.set_title("Mandelbrotova mnozina", fontsize=14, fontweight="bold", color="white")
ax.set_xlabel("Re(c)", color="white")
ax.set_ylabel("Im(c)", color="white")
ax.set_facecolor("black")
fig.patch.set_facecolor("#0d1117")
ax.tick_params(colors="#8b949e")
for s in ax.spines.values():
    s.set_color("#30363d")

uloz("06_mandelbrot.png")
print("  Hotovo!")


# 3. Animace sin vlny (ulozena jako GIF)

print("\n=== Ukol 3: Animace sin vlny (GIF) ===\n")

try:
    from matplotlib.animation import FuncAnimation, PillowWriter
    ANIM_OK = True
except ImportError:
    ANIM_OK = False

if ANIM_OK:
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.set_facecolor("#0d1117")
    fig.patch.set_facecolor("#161b22")
    ax.set_xlim(0, 2 * math.pi)
    ax.set_ylim(-1.5, 1.5)
    ax.set_title("Animovana sin vlna", color="white")
    ax.tick_params(colors="#8b949e")
    for s in ax.spines.values():
        s.set_color("#30363d")
    ax.axhline(0, color="#30363d", linewidth=0.8)

    x = np.linspace(0, 2 * math.pi, 300)
    linie, = ax.plot(x, np.sin(x), color="#58a6ff", linewidth=2)
    cas_text = ax.text(0.02, 0.92, "", transform=ax.transAxes,
                       color="white", fontsize=10)

    SNIMKU = 24

    def aktualizuj(snimek: int):
        faze = snimek * (2 * math.pi / SNIMKU)
        linie.set_ydata(np.sin(x + faze))
        cas_text.set_text(f"Faze: {math.degrees(faze):.0f}°")
        return linie, cas_text

    anim = FuncAnimation(fig, aktualizuj, frames=SNIMKU, interval=80, blit=True)

    gif_cesta = VYSTUP / "07_sin_animace.gif"
    writer = PillowWriter(fps=12)
    anim.save(str(gif_cesta), writer=writer)
    plt.close()
    print(f"  Animace ulozena: {gif_cesta}")
else:
    print("  PillowWriter nedostupny (pip install pillow)")
    # Uloz staticky obrazek misto GIFu
    fig, ax = plt.subplots(figsize=(8, 4))
    x = np.linspace(0, 2 * math.pi, 300)
    for i, faze in enumerate(np.linspace(0, 2*math.pi, 5)):
        ax.plot(x, np.sin(x + faze), alpha=0.7, label=f"faze={math.degrees(faze):.0f}°")
    ax.set_title("Sin vlna – vicenasobne faze")
    ax.legend(fontsize=8)
    uloz("07_sin_faze_staticky.png")
    print("  Ulozen staticky nahradni obrazek")

print(f"\nVsechny grafy ulozeny do {VYSTUP}/")
