"""
LEKCE 80: OpenCV – počítačové vidění
======================================
pip install opencv-python numpy

OpenCV = Open Source Computer Vision Library.
Zpracování obrazu, detekce objektů, analýza videa.

Použití:
  - Detekce obličejů, QR kódů, pohybu
  - Filtry a transformace obrázků
  - Čtení textu z obrazu (OCR)
  - Analýza videa z kamery
"""

import sys
import numpy as np
from pathlib import Path

try:
    import cv2
    CV_OK = True
except ImportError:
    print("OpenCV není nainstalováno: pip install opencv-python numpy")
    CV_OK = False

# ══════════════════════════════════════════════════════════════
# ČÁST 1: Základy – načtení, zobrazení, uložení
# ══════════════════════════════════════════════════════════════

print("=== OpenCV základy ===\n")

if CV_OK:
    # Vytvoř testovací obrázek místo načtení souboru
    img = np.zeros((400, 600, 3), dtype=np.uint8)

    # BGR (ne RGB!) – OpenCV používá Blue-Green-Red pořadí
    MODRA   = (255, 0,   0)    # BGR
    ZELENA  = (0,   255, 0)
    CERVENA = (0,   0,   255)
    BILA    = (255, 255, 255)
    ZLUTA   = (0,   255, 255)

    # Kreslení tvarů
    cv2.rectangle(img, (50, 50),   (200, 150), MODRA,   3)
    cv2.circle   (img, (350, 200), 80,         ZELENA,  -1)    # -1 = vyplněný
    cv2.line     (img, (0, 0),     (600, 400), CERVENA, 2)
    cv2.ellipse  (img, (300, 300), (100, 50), 45, 0, 360, ZLUTA, 2)
    cv2.putText  (img, "OpenCV kurz", (50, 380),
                   cv2.FONT_HERSHEY_SIMPLEX, 1.0, BILA, 2)

    cv2.imwrite("test_obrazek.png", img)
    print(f"  Obrázek: {img.shape}  (výška={img.shape[0]}, šířka={img.shape[1]}, kanály={img.shape[2]})")
    print(f"  Dtype: {img.dtype}  (uint8 = 0–255 na pixel)")

    # Základní operace
    sedy = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    print(f"  Šedotónový: {sedy.shape}  (2D – jen 1 kanál)")

    # Resize
    maly = cv2.resize(img, (300, 200))
    print(f"  Resize 50%: {maly.shape}")

    # Crop (řezání = NumPy slicing)
    crop = img[50:200, 50:300]
    print(f"  Crop: {crop.shape}")


# ══════════════════════════════════════════════════════════════
# ČÁST 2: Filtry a transformace
# ══════════════════════════════════════════════════════════════

print("\n=== Filtry ===\n")

if CV_OK:
    img = cv2.imread("test_obrazek.png")

    # Rozmazání (blur)
    blur_gaussian = cv2.GaussianBlur(img, (15, 15), 0)
    blur_median   = cv2.medianBlur(img, 9)

    # Ostření
    kernel_ostreni = np.array([[-1,-1,-1],
                                 [-1, 9,-1],
                                 [-1,-1,-1]])
    ostry = cv2.filter2D(img, -1, kernel_ostreni)

    # Detekce hran (Canny)
    sedy   = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    hrany  = cv2.Canny(sedy, 50, 150)

    # Práhování (thresholding)
    _, prahovany = cv2.threshold(sedy, 127, 255, cv2.THRESH_BINARY)
    adaptivni    = cv2.adaptiveThreshold(sedy, 255,
                    cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)

    # Morfologické operace
    kernel = np.ones((5,5), np.uint8)
    dilatace  = cv2.dilate(hrany,  kernel, iterations=1)
    eroze     = cv2.erode(hrany,   kernel, iterations=1)
    otevreni  = cv2.morphologyEx(hrany, cv2.MORPH_OPEN, kernel)

    print("  Filtry aplikovány:")
    print("  GaussianBlur  – vyhlazení šumu")
    print("  Canny          – detekce hran")
    print("  threshold      – binární maska")
    print("  dilate/erode   – morfologie")

    # Uložení výsledků
    cv2.imwrite("hrany.png", hrany)
    cv2.imwrite("prahovany.png", prahovany)
    print("  ✓ hrany.png, prahovany.png")


# ══════════════════════════════════════════════════════════════
# ČÁST 3: Detekce kontur a tvarů
# ══════════════════════════════════════════════════════════════

print("\n=== Detekce kontur ===\n")

if CV_OK:
    # Vytvoř obrázek s geometrickými tvary
    canvas = np.zeros((400, 600, 3), dtype=np.uint8)
    cv2.rectangle(canvas, (50, 50),   (150, 150), (255,255,255), -1)
    cv2.circle   (canvas, (300, 200), 80,         (255,255,255), -1)
    cv2.rectangle(canvas, (400, 100), (550, 300), (255,255,255), -1)

    sedy   = cv2.cvtColor(canvas, cv2.COLOR_BGR2GRAY)
    kontury, _ = cv2.findContours(sedy, cv2.RETR_EXTERNAL,
                                    cv2.CHAIN_APPROX_SIMPLE)

    print(f"  Nalezeno {len(kontury)} kontur")

    for i, kontura in enumerate(kontury):
        plocha = cv2.contourArea(kontura)
        obvod  = cv2.arcLength(kontura, True)

        # Aproximace tvaru
        epsilon = 0.04 * obvod
        approx  = cv2.approxPolyDP(kontura, epsilon, True)
        rohy    = len(approx)

        # Ohraničující obdélník
        x, y, w, h = cv2.boundingRect(kontura)

        tvar = {3: "trojúhelník", 4: "obdélník/čtverec"}.get(rohy, "kruh/jiný")
        print(f"  Kontura {i}: {tvar} ({rohy} rohů), "
              f"plocha={plocha:.0f}, bbox=({x},{y},{w},{h})")

        # Nakresli konturou a popis
        cv2.drawContours(canvas, [kontura], -1, (0,255,0), 2)
        cv2.putText(canvas, tvar, (x, y-5),
                     cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,255,255), 1)

    cv2.imwrite("kontury.png", canvas)
    print("  ✓ kontury.png")


# ══════════════════════════════════════════════════════════════
# ČÁST 4: Detekce tváří (Haar Cascade)
# ══════════════════════════════════════════════════════════════

print("\n=== Detekce tváří ===\n")

if CV_OK:
    import os
    # Cesta ke Haar cascade klasifikátoru (součást OpenCV)
    cascade_cesta = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"

    if Path(cascade_cesta).exists():
        detektor = cv2.CascadeClassifier(cascade_cesta)

        # Simulace – vytvoř syntetický "obličej" (demo bez reálné fotky)
        test_img = np.full((200, 200, 3), 200, dtype=np.uint8)  # šedé pozadí
        # Kruh pro hlavu
        cv2.circle(test_img, (100, 100), 70, (220, 180, 150), -1)
        # Oči
        cv2.circle(test_img, (75,  85), 10, (50, 50, 50), -1)
        cv2.circle(test_img, (125, 85), 10, (50, 50, 50), -1)

        sedy_img = cv2.cvtColor(test_img, cv2.COLOR_BGR2GRAY)
        tvare = detektor.detectMultiScale(sedy_img, scaleFactor=1.1,
                                           minNeighbors=5, minSize=(30, 30))
        print(f"  Nalezeno {len(tvare)} tváří v testovacím obrázku")
        print(f"  (Pro reálné fotky: cv2.imread('foto.jpg'))")

    print("""
  Reálný kód pro detekci tváří:
    img  = cv2.imread("skupina.jpg")
    sedy = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    tvare = detektor.detectMultiScale(sedy, 1.1, 5)
    for (x, y, w, h) in tvare:
        cv2.rectangle(img, (x,y), (x+w, y+h), (0,255,0), 2)
    cv2.imwrite("vysledek.jpg", img)
""")


# ══════════════════════════════════════════════════════════════
# ČÁST 5: Analýza barev a histogram
# ══════════════════════════════════════════════════════════════

print("=== Analýza barev ===\n")

if CV_OK:
    img = cv2.imread("test_obrazek.png")

    # Histogram – distribuce jasu
    for i, kanal in enumerate(['B', 'G', 'R']):
        hist = cv2.calcHist([img], [i], None, [256], [0, 256])
        prumer = np.average(np.arange(256), weights=hist.flatten())
        print(f"  Kanál {kanal}: průměr jasu = {prumer:.1f}")

    # Dominantní barvy (K-Means)
    pixely = img.reshape(-1, 3).astype(np.float32)
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0)
    _, labels, centroidy = cv2.kmeans(pixely, 3, None, criteria, 10,
                                        cv2.KMEANS_RANDOM_CENTERS)
    centroidy = centroidy.astype(int)
    unikatni, pocty = np.unique(labels, return_counts=True)

    print("\n  Dominantní barvy (K-Means, k=3):")
    for idx, pocet in sorted(zip(unikatni, pocty), key=lambda x: -x[1]):
        b, g, r = centroidy[idx]
        pct = pocet / len(labels) * 100
        print(f"    BGR({b:3d},{g:3d},{r:3d}) = #{r:02x}{g:02x}{b:02x}  {pct:.1f}%")

    # Úklid
    for f in ["test_obrazek.png", "hrany.png", "prahovany.png", "kontury.png"]:
        Path(f).unlink(missing_ok=True)

print("""
=== OpenCV vs PIL/Pillow ===

  OpenCV   → rychlé zpracování, počítačové vidění, video, kamera
  Pillow   → jednodušší API, web/email thumbnaily, základní úpravy
  scikit-image → vědecké zpracování, více algoritmů, čistší API

=== Kdy OpenCV ===
  ✓ Detekce objektů, obličejů, pohybu
  ✓ Zpracování videa v reálném čase
  ✓ Průmyslová inspekce, robotika
  ✗ Jednoduchý resize/crop → Pillow je pohodlnější
""")

# TVOJE ÚLOHA:
# 1. Načti vlastní fotku a detekuj v ní tváře.
# 2. Napiš funkci anonymizuj(img) která rozmaže každou nalezenou tvář.
# 3. Přidej detekci pohybu: porovnej dva snímky (cv2.absdiff).
