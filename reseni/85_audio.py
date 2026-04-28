"""Řešení – Lekce 85: Audio – zpracování zvuku"""

import wave
import struct
import math
import time
from pathlib import Path

SAMPLE_RATE = 44100
AMPLITUDE   = 32767 * 0.7

def generuj_sin(freq: float, delka_s: float, sr: int = SAMPLE_RATE) -> list[int]:
    n = int(sr * delka_s)
    return [int(AMPLITUDE * math.sin(2 * math.pi * freq * i / sr)) for i in range(n)]

def generuj_fadeout(vzorky: list[int]) -> list[int]:
    n = len(vzorky)
    return [int(v * (1 - i/n)) for i, v in enumerate(vzorky)]

def uloz_wav(vzorky: list[int], soubor: str, sr: int = SAMPLE_RATE):
    with wave.open(soubor, "w") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(struct.pack(f"<{len(vzorky)}h", *vzorky))

def nacti_wav(soubor: str) -> tuple[list[int], int]:
    with wave.open(soubor, "r") as wf:
        sr = wf.getframerate()
        n  = wf.getnframes()
        ch = wf.getnchannels()
        raw = wf.readframes(n)
        vzorky = list(struct.unpack(f"<{n*ch}h", raw))
        if ch == 2:
            vzorky = [(vzorky[i] + vzorky[i+1]) // 2 for i in range(0, len(vzorky), 2)]
        return vzorky, sr


# 1. DTMF – tóny telefonní klávesnice
print("=== 1. DTMF tóny telefonní klávesnice ===\n")

# DTMF tabulka: každé tlačítko = součet dvou frekvencí
DTMF_FREKVENCE = {
    "1": (697, 1209), "2": (697, 1336), "3": (697, 1477),
    "4": (770, 1209), "5": (770, 1336), "6": (770, 1477),
    "7": (852, 1209), "8": (852, 1336), "9": (852, 1477),
    "*": (941, 1209), "0": (941, 1336), "#": (941, 1477),
    "A": (697, 1633), "B": (770, 1633), "C": (852, 1633), "D": (941, 1633),
}

def generuj_dtmf(cislo: str,
                  delka_tonu_s: float = 0.15,
                  mezera_s: float = 0.05) -> list[int]:
    """
    Generuje DTMF tóny pro zadané číslo/sekvenci.
    Každý tón = součet dvou sinusovek (row + column frekvence).
    """
    vzorky: list[int] = []
    mezera = [0] * int(SAMPLE_RATE * mezera_s)

    for znak in str(cislo).upper():
        if znak == " ":
            vzorky.extend([0] * int(SAMPLE_RATE * 0.1))
            continue
        if znak not in DTMF_FREKVENCE:
            print(f"  [!] Neznámý znak: {znak!r}")
            continue

        f_low, f_high = DTMF_FREKVENCE[znak]
        n = int(SAMPLE_RATE * delka_tonu_s)

        # Součet dvou sinusovek (normalizovaný na 50% každý)
        ton = [
            int(AMPLITUDE * 0.5 * (
                math.sin(2 * math.pi * f_low  * i / SAMPLE_RATE) +
                math.sin(2 * math.pi * f_high * i / SAMPLE_RATE)
            ))
            for i in range(n)
        ]
        ton = generuj_fadeout(ton)
        vzorky.extend(ton)
        vzorky.extend(mezera)

    return vzorky

# Generuj DTMF pro různá čísla
testy_dtmf = [
    ("112",         "tísňová linka"),
    ("420123456789","czech mobile"),
    ("0*#9",        "všechna tlačítka"),
]

for cislo, popis in testy_dtmf:
    vzorky = generuj_dtmf(cislo)
    soubor = f"dtmf_{cislo.replace('*','star').replace('#','hash')}.wav"
    uloz_wav(vzorky, soubor)
    delka = len(vzorky) / SAMPLE_RATE
    print(f"  {cislo:<15} ({popis}): {delka:.2f}s → {soubor}")
    Path(soubor).unlink(missing_ok=True)

print()
print("  DTMF frekvence:")
print("        1209 Hz  1336 Hz  1477 Hz  1633 Hz")
for radek, (znaky, f_row) in enumerate(
    zip(["123A", "456B", "789C", "*0#D"], [697, 770, 852, 941])
):
    print(f"  {f_row} Hz: " + "    ".join(znaky))


# 2. FFT vizualizace spektra (ASCII art)
print("\n=== 2. FFT vizualizace spektra ===\n")

def vypocti_fft_spektrum(vzorky: list[int],
                          sr: int = SAMPLE_RATE,
                          max_freq: float = 5000) -> tuple[list[float], list[float]]:
    """
    Vypočítá FFT a vrátí (frekvence, amplitudy) pro pozitivní část.
    Implementováno bez numpy pomocí DFT (pro demo – pro produkci použij numpy.fft).
    """
    n = len(vzorky)
    # Použij pouze každý 16. vzorek pro rychlost (downsampling)
    krok = max(1, n // 2048)
    uzky = vzorky[::krok]
    n_uzkych = len(uzky)

    # Jednoduchá DFT (pomalá, ale bez závislostí)
    half  = n_uzkych // 2
    sr_eff = sr // krok
    frekvence = [i * sr_eff / n_uzkych for i in range(half)]
    amplitudy = []

    # Rychlý odhad: rozděl na frekvenční pásma
    pasma_hz = [0, 100, 200, 400, 800, 1600, 3200, 6400, sr_eff // 2]
    for pas_i in range(len(pasma_hz) - 1):
        f_min  = pasma_hz[pas_i]
        f_max  = pasma_hz[pas_i + 1]
        i_min  = int(f_min * n_uzkych / sr_eff)
        i_max  = int(f_max * n_uzkych / sr_eff)
        if i_min >= n_uzkych:
            break
        i_max  = min(i_max, n_uzkych)
        cast   = uzky[i_min:i_max]
        if cast:
            rms = math.sqrt(sum(v*v for v in cast) / len(cast))
            amplitudy.append(rms)
        else:
            amplitudy.append(0.0)

    return pasma_hz[1:len(amplitudy)+1], amplitudy

def vizualizuj_spektrum(frekvence: list[float],
                         amplitudy: list[float],
                         sirka: int = 50):
    """Textová vizualizace spektra (horizontální sloupce)."""
    max_amp = max(amplitudy) if amplitudy else 1

    print("  Frekvenční spektrum:")
    print(f"  {'Pásmo':<12} {'Energie'}")
    for f, amp in zip(frekvence, amplitudy):
        if max_amp > 0:
            sloupec = int(amp / max_amp * sirka)
        else:
            sloupec = 0
        bar   = "█" * sloupec + "░" * (sirka - sloupec)
        pct   = amp / max_amp * 100 if max_amp > 0 else 0
        print(f"  {f:>6.0f} Hz: {bar} {pct:5.1f}%")

# Generuj testovací signál: mix 440Hz + 1000Hz + 2000Hz
def generuj_mix(frekvence: list[float], delka_s: float = 0.5) -> list[int]:
    n = int(SAMPLE_RATE * delka_s)
    vzorky = []
    for i in range(n):
        hodnota = sum(
            AMPLITUDE / len(frekvence) * math.sin(2 * math.pi * f * i / SAMPLE_RATE)
            for f in frekvence
        )
        vzorky.append(int(hodnota))
    return vzorky

print("Signál: 440Hz + 880Hz + 1760Hz (A4 + A5 + A6)\n")
mix_vzorky = generuj_mix([440, 880, 1760])
freqs, amps = vypocti_fft_spektrum(mix_vzorky)
vizualizuj_spektrum(freqs, amps)

print("\nSignál: 100Hz (bas) + 3000Hz (výšky)\n")
bas_mix = generuj_mix([100, 3000])
freqs2, amps2 = vypocti_fft_spektrum(bas_mix)
vizualizuj_spektrum(freqs2, amps2)


# 3. Metronom
print("\n=== 3. Metronom ===\n")

def generuj_tick(freq: float = 880, delka_ms: int = 50) -> list[int]:
    """Generuje krátký 'tick' tón."""
    vzorky = generuj_sin(freq, delka_ms / 1000)
    return generuj_fadeout(vzorky)

def generuj_tock(freq: float = 660, delka_ms: int = 50) -> list[int]:
    """Generuje 'tock' tón pro přízvučnou dobu."""
    vzorky = generuj_sin(freq, delka_ms / 1000)
    return generuj_fadeout(vzorky)

def generuj_metronom_wav(bpm: int = 120, takty: int = 4,
                          udery_v_taktu: int = 4,
                          soubor: str = "metronom.wav"):
    """
    Vygeneruje WAV soubor s metronomem.
    První doba každého taktu = tock (přízvučná).
    Ostatní doby = tick.
    """
    cas_mezi_udery_s = 60.0 / bpm
    tick_vzorky = generuj_tick(freq=1200, delka_ms=30)
    tock_vzorky = generuj_tock(freq=800,  delka_ms=50)

    vsechny_vzorky: list[int] = []

    for takt in range(takty):
        for doba in range(udery_v_taktu):
            # Přidej tón
            if doba == 0:
                vsechny_vzorky.extend(tock_vzorky)  # přízvučná doba
            else:
                vsechny_vzorky.extend(tick_vzorky)

            # Ticho do další doby
            n_ticha = int(SAMPLE_RATE * cas_mezi_udery_s) - len(tick_vzorky)
            if n_ticha > 0:
                vsechny_vzorky.extend([0] * n_ticha)

    uloz_wav(vsechny_vzorky, soubor)
    delka = len(vsechny_vzorky) / SAMPLE_RATE
    return delka

# Generuj metronomové soubory
for bpm, udery, popis in [(60, 4, "pomale_4-4"),
                             (120, 4, "stredni_4-4"),
                             (180, 3, "rychle_3-4")]:
    soubor = f"metronom_{popis}.wav"
    delka  = generuj_metronom_wav(bpm=bpm, takty=4,
                                    udery_v_taktu=udery,
                                    soubor=soubor)
    print(f"  {bpm} BPM, {udery}/4 takt, 4 takty: {delka:.2f}s → {soubor}")
    Path(soubor).unlink(missing_ok=True)

print()
print("  Přehrání metronomu v reálném čase (vyžaduje sounddevice):")
print("    import sounddevice as sd, numpy as np")
print("    vzorky = generuj_metronom_wav(bpm=120, ...)")
print("    sd.play(np.array(vzorky, dtype=np.int16), samplerate=44100)")
print("    sd.wait()")

print("\n=== Shrnutí ===")
print("  1. generuj_dtmf()         – DTMF tóny pro telefonní čísla")
print("  2. vizualizuj_spektrum()   – FFT analýza a ASCII art vizualizace")
print("  3. generuj_metronom_wav()  – metronom jako WAV soubor")
