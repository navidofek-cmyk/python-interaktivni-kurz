"""Řešení – Lekce 80: OpenCV – počítačové vidění"""

# vyžaduje: pip install opencv-python numpy

import sys
import numpy as np
from pathlib import Path

try:
    import cv2
    CV_OK = True
    print(f"OpenCV {cv2.__version__} dostupné\n")
except ImportError:
    print("OpenCV není nainstalováno: pip install opencv-python numpy\n")
    CV_OK = False

if not CV_OK:
    sys.exit(0)


# 1. Načti vlastní fotku a detekuj tváře
print("=== 1. Detekce tváří v obrázku ===\n")

def detekuj_tvare(img: np.ndarray,
                   scaleFactor: float = 1.1,
                   minNeighbors: int = 5,
                   minSize: tuple = (30, 30)) -> list[tuple]:
    """
    Detekuje tváře v obrázku pomocí Haar Cascade.
    Vrátí seznam (x, y, w, h) detekovaných tváří.
    """
    cascade_cesta = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    if not Path(cascade_cesta).exists():
        print(f"  Cascade soubor nenalezen: {cascade_cesta}")
        return []

    detektor = cv2.CascadeClassifier(cascade_cesta)
    sedy     = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    sedy     = cv2.equalizeHist(sedy)   # zlepšení kontrastu

    tvare = detektor.detectMultiScale(
        sedy,
        scaleFactor=scaleFactor,
        minNeighbors=minNeighbors,
        minSize=minSize,
        flags=cv2.CASCADE_SCALE_IMAGE,
    )
    return list(tvare) if len(tvare) > 0 else []

def oznac_tvare(img: np.ndarray, tvare: list) -> np.ndarray:
    """Nakreslí zelený obdélník kolem každé nalezené tváře."""
    vysledek = img.copy()
    for (x, y, w, h) in tvare:
        cv2.rectangle(vysledek, (x, y), (x+w, y+h), (0, 255, 0), 2)
        cv2.putText(vysledek, f"tvar {w}x{h}",
                    (x, y-5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
    return vysledek

# Vytvoř syntetický testovací obrázek (náhrada za reálnou fotku)
def vytvor_synteticky_portret(sirka: int = 300, vyska: int = 350) -> np.ndarray:
    """Syntetický portrét pro demo."""
    img = np.full((vyska, sirka, 3), 220, dtype=np.uint8)
    # Pozadí
    img[:] = (200, 210, 225)
    # Hlava (elipsa)
    cv2.ellipse(img, (sirka//2, vyska//3), (80, 95), 0, 0, 360, (220, 180, 140), -1)
    # Oči
    cv2.ellipse(img, (sirka//2 - 25, vyska//3 - 10), (12, 8), 0, 0, 360, (255, 255, 255), -1)
    cv2.ellipse(img, (sirka//2 + 25, vyska//3 - 10), (12, 8), 0, 0, 360, (255, 255, 255), -1)
    cv2.circle(img, (sirka//2 - 25, vyska//3 - 10), 5, (50, 40, 30), -1)
    cv2.circle(img, (sirka//2 + 25, vyska//3 - 10), 5, (50, 40, 30), -1)
    # Nos
    cv2.ellipse(img, (sirka//2, vyska//3 + 15), (8, 5), 0, 0, 360, (190, 150, 110), -1)
    # Ústa
    cv2.ellipse(img, (sirka//2, vyska//3 + 35), (20, 10), 0, 0, 180, (160, 80, 80), 2)
    return img

portret = vytvor_synteticky_portret()
tvare   = detekuj_tvare(portret)
print(f"  Syntetický portret: {portret.shape}")
print(f"  Nalezeno tváří: {len(tvare)}")
print(f"  (Haar Cascade je trénovaný na reálné fotky – syntetické tváře obvykle nedetekuje)")
print(f"  Pro reálnou fotku: cv2.imread('foto.jpg')")

if tvare:
    oznaceny = oznac_tvare(portret, tvare)
    cv2.imwrite("portret_detekce.png", oznaceny)
    print(f"  ✓ portret_detekce.png uložen")
    Path("portret_detekce.png").unlink(missing_ok=True)


# 2. Funkce anonymizuj(img) – rozmaže každou nalezenou tvář
print("\n=== 2. Anonymizace tváří ===\n")

def anonymizuj(img: np.ndarray, intenzita: int = 30) -> np.ndarray:
    """
    Rozmaže každou nalezenou tvář v obrázku.
    intenzita: čím vyšší, tím silnější mozaika (1-50)
    """
    vysledek = img.copy()
    tvare    = detekuj_tvare(img)

    if not tvare:
        print("  Žádné tváře nenalezeny – zkus reálnou fotku")
        return vysledek

    for (x, y, w, h) in tvare:
        oblast = vysledek[y:y+h, x:x+w]

        # Metoda 1: Gaussovo rozmazání (soft blur)
        rozmazana = cv2.GaussianBlur(oblast, (99, 99), 30)

        # Metoda 2: Pixelizace (mozaika) – výraznější anonymizace
        maly_w    = max(1, w // intenzita)
        maly_h    = max(1, h // intenzita)
        pixelovana = cv2.resize(oblast, (maly_w, maly_h),
                                  interpolation=cv2.INTER_LINEAR)
        pixelovana = cv2.resize(pixelovana, (w, h),
                                  interpolation=cv2.INTER_NEAREST)

        vysledek[y:y+h, x:x+w] = pixelovana

    print(f"  Anonymizováno {len(tvare)} tváří pomocí pixelizace")
    return vysledek

# Demo na syntetickém obrázku
anonymizovany = anonymizuj(portret)
cv2.imwrite("portret_anonymni.png", anonymizovany)
print(f"  ✓ portret_anonymni.png uložen")

# Ukázka s reálnou fotkou
print("""
  Použití s reálnou fotkou:
    img = cv2.imread("skupina_foto.jpg")
    anonymni = anonymizuj(img, intenzita=20)
    cv2.imwrite("anonymni_foto.jpg", anonymni)
""")


# 3. Detekce pohybu – porovnání dvou snímků (cv2.absdiff)
print("=== 3. Detekce pohybu ===\n")

def detekuj_pohyb(snimek1: np.ndarray,
                   snimek2: np.ndarray,
                   prah: int = 25,
                   min_plocha: int = 500) -> tuple[np.ndarray, list[tuple], float]:
    """
    Detekuje pohyb mezi dvěma snímky.

    Vrátí:
        maska:    binární maska pohybu
        oblasti:  seznam bounding boxů (x, y, w, h)
        procent:  procento plochy s pohybem
    """
    # Převod na šedotón
    sedy1 = cv2.cvtColor(snimek1, cv2.COLOR_BGR2GRAY)
    sedy2 = cv2.cvtColor(snimek2, cv2.COLOR_BGR2GRAY)

    # Rozmaž pro redukci šumu
    sedy1 = cv2.GaussianBlur(sedy1, (21, 21), 0)
    sedy2 = cv2.GaussianBlur(sedy2, (21, 21), 0)

    # Absolutní rozdíl
    diff = cv2.absdiff(sedy1, sedy2)

    # Prahování
    _, maska = cv2.threshold(diff, prah, 255, cv2.THRESH_BINARY)

    # Morfologie – zaplní mezery
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    maska  = cv2.dilate(maska, kernel, iterations=3)

    # Najdi kontury pohybu
    kontury, _ = cv2.findContours(maska, cv2.RETR_EXTERNAL,
                                    cv2.CHAIN_APPROX_SIMPLE)
    oblasti = []
    for k in kontury:
        if cv2.contourArea(k) > min_plocha:
            oblasti.append(cv2.boundingRect(k))

    procent = np.count_nonzero(maska) / maska.size * 100
    return maska, oblasti, procent

# Vytvoř dva testovací snímky s pohybem
def vytvor_snimky_pohybu() -> tuple[np.ndarray, np.ndarray]:
    """Simuluje statickou kameru s pohybujícím se objektem."""
    pozadi = np.full((300, 400, 3), 200, dtype=np.uint8)
    # Snímek 1: červený kruh vlevo
    s1 = pozadi.copy()
    cv2.circle(s1, (100, 150), 40, (0, 0, 200), -1)
    # Snímek 2: červený kruh vpravo (pohyb)
    s2 = pozadi.copy()
    cv2.circle(s2, (300, 150), 40, (0, 0, 200), -1)
    # Přidej šum
    s1 = cv2.add(s1, np.random.randint(0, 5, s1.shape, dtype=np.uint8))
    s2 = cv2.add(s2, np.random.randint(0, 5, s2.shape, dtype=np.uint8))
    return s1, s2

s1, s2 = vytvor_snimky_pohybu()
maska, oblasti, procent = detekuj_pohyb(s1, s2)

print(f"  Snímek 1 vs Snímek 2:")
print(f"  Pohyb: {procent:.1f}% plochy")
print(f"  Oblasti pohybu: {len(oblasti)}")
for i, (x, y, w, h) in enumerate(oblasti[:3], 1):
    print(f"    Oblast {i}: ({x},{y}) {w}×{h}px")

# Vizualizace
pohyb_vizualizace = s2.copy()
for (x, y, w, h) in oblasti:
    cv2.rectangle(pohyb_vizualizace, (x, y), (x+w, y+h), (0, 255, 0), 2)
    cv2.putText(pohyb_vizualizace, "POHYB",
                (x, y-5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)

cv2.imwrite("pohyb_detekce.png", pohyb_vizualizace)
cv2.imwrite("pohyb_maska.png", maska)
print(f"\n  ✓ pohyb_detekce.png  (obdélníky kolem pohybu)")
print(f"  ✓ pohyb_maska.png   (binární maska)")

# Úklid
for f in ["portret_anonymni.png", "pohyb_detekce.png", "pohyb_maska.png"]:
    Path(f).unlink(missing_ok=True)

print("\n=== Shrnutí ===")
print("  1. detekuj_tvare() / oznac_tvare() – Haar Cascade detekce")
print("  2. anonymizuj()                    – pixelizace obličejů")
print("  3. detekuj_pohyb()                 – absdiff + threshold + kontury")
