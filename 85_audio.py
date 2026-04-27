"""
LEKCE 85: Audio – zpracování zvuku
=====================================
Vestavěné: wave, struct, math
Volitelné: pip install pydub sounddevice numpy

Zvuk = tlaková vlna → čísla (samples) → soubor (WAV, MP3)

Vzorkovací frekvence (sample rate):
  8 000 Hz  – telefon
  44 100 Hz – CD kvalita
  48 000 Hz – profesionální audio

Bit depth: 16 bit = -32768 … 32767 na vzorek
"""

import wave
import struct
import math
import os
import time
from pathlib import Path

# ══════════════════════════════════════════════════════════════
# ČÁST 1: Generování tónů (čistá matematika)
# ══════════════════════════════════════════════════════════════

print("=== Generování tónů ===\n")

SAMPLE_RATE = 44100
AMPLITUDE   = 32767 * 0.7   # 70% max hlasitosti

def generuj_sin(freq: float, delka_s: float, sr: int = SAMPLE_RATE) -> list[int]:
    """Sinusový tón na zadané frekvenci."""
    n_vzorku = int(sr * delka_s)
    return [
        int(AMPLITUDE * math.sin(2 * math.pi * freq * i / sr))
        for i in range(n_vzorku)
    ]

def generuj_fadeout(vzorky: list[int]) -> list[int]:
    """Plynulé ztišení na konci."""
    n = len(vzorky)
    return [int(v * (1 - i/n)) for i, v in enumerate(vzorky)]

def generuj_chord(freqs: list[float], delka_s: float) -> list[int]:
    """Akord = součet více sinusovek."""
    n_vzorku = int(SAMPLE_RATE * delka_s)
    vzorky = []
    for i in range(n_vzorku):
        hodnota = sum(
            AMPLITUDE / len(freqs) * math.sin(2 * math.pi * f * i / SAMPLE_RATE)
            for f in freqs
        )
        vzorky.append(int(hodnota))
    return vzorky

def uloz_wav(vzorky: list[int], soubor: str, sr: int = SAMPLE_RATE):
    """Uloží vzorky jako WAV soubor."""
    with wave.open(soubor, "w") as wf:
        wf.setnchannels(1)      # mono
        wf.setsampwidth(2)      # 16 bit = 2 bajty
        wf.setframerate(sr)
        wf.writeframes(struct.pack(f"<{len(vzorky)}h", *vzorky))

# Nota → frekvence (MIDI systém)
NOTY = {
    "C4": 261.63, "D4": 293.66, "E4": 329.63,
    "F4": 349.23, "G4": 392.00, "A4": 440.00,
    "B4": 493.88, "C5": 523.25,
}

# Jednoduchá melodie – Twinkle Twinkle (prvních 8 not)
MELODIE = [
    ("C4", 0.5), ("C4", 0.5), ("G4", 0.5), ("G4", 0.5),
    ("A4", 0.5), ("A4", 0.5), ("G4", 1.0),
    ("F4", 0.5), ("F4", 0.5), ("E4", 0.5), ("E4", 0.5),
]

vsechny_vzorky: list[int] = []
for nota, delka in MELODIE:
    vzorky = generuj_sin(NOTY[nota], delka)
    vzorky = generuj_fadeout(vzorky)
    vsechny_vzorky.extend(vzorky)
    vsechny_vzorky.extend([0] * int(SAMPLE_RATE * 0.05))  # mezera

uloz_wav(vsechny_vzorky, "melodie.wav")
print(f"  ✓ melodie.wav  ({len(vsechny_vzorky)/SAMPLE_RATE:.1f}s, {Path('melodie.wav').stat().st_size:,} B)")

# Akord C dur
akord = generuj_chord([261.63, 329.63, 392.00], 2.0)   # C-E-G
akord = generuj_fadeout(akord)
uloz_wav(akord, "akord_c_dur.wav")
print(f"  ✓ akord_c_dur.wav  (C-E-G, 2s)")


# ══════════════════════════════════════════════════════════════
# ČÁST 2: Čtení a analýza WAV
# ══════════════════════════════════════════════════════════════

print("\n=== Čtení a analýza WAV ===\n")

def nacti_wav(soubor: str) -> tuple[list[int], int]:
    """Vrátí (vzorky, sample_rate)."""
    with wave.open(soubor, "r") as wf:
        n_channels = wf.getnchannels()
        sr         = wf.getframerate()
        n_frames   = wf.getnframes()
        raw        = wf.readframes(n_frames)
        vzorky     = list(struct.unpack(f"<{n_frames * n_channels}h", raw))
        if n_channels == 2:
            # Stereo → mono průměrem
            vzorky = [(vzorky[i] + vzorky[i+1]) // 2 for i in range(0, len(vzorky), 2)]
        return vzorky, sr

vzorky, sr = nacti_wav("melodie.wav")
print(f"  Sample rate:  {sr} Hz")
print(f"  Délka:        {len(vzorky)/sr:.2f}s")
print(f"  Vzorků:       {len(vzorky):,}")

# Statistiky
max_amp  = max(abs(v) for v in vzorky)
prumer   = sum(abs(v) for v in vzorky) / len(vzorky)
rms      = math.sqrt(sum(v*v for v in vzorky) / len(vzorky))
print(f"  Max amplituda:{max_amp}")
print(f"  Průměr abs:   {prumer:.1f}")
print(f"  RMS:          {rms:.1f}")


# ══════════════════════════════════════════════════════════════
# ČÁST 3: Textová vizualizace průběhu
# ══════════════════════════════════════════════════════════════

print("\n=== Průběh signálu (ASCII art) ===\n")

def vizualizuj_prubeh(vzorky: list[int], sirka: int = 60, vyska: int = 12):
    """Vizualizuje audio průběh v terminálu."""
    # Downsample na šířku
    chunk = len(vzorky) // sirka
    sloupce = []
    for i in range(sirka):
        cast = vzorky[i*chunk:(i+1)*chunk]
        sloupce.append(max(abs(v) for v in cast) if cast else 0)

    max_val = max(sloupce) or 1
    normalizovano = [v / max_val for v in sloupce]

    # Vykresli od shora dolů
    for radek in range(vyska, 0, -1):
        prah = radek / vyska
        line = ""
        for norm in normalizovano:
            if norm >= prah:
                line += "█"
            elif norm >= prah - 1/vyska:
                line += "▄"
            else:
                line += " "
        if radek == vyska // 2:
            print(f"  {line}  ← max={max_val}")
        else:
            print(f"  {line}")

# Vizualizuj prvních 0.5s melodie
prvni_pulka = vzorky[:SAMPLE_RATE // 2]
print("Průběh melodie (prvních 0.5s):")
vizualizuj_prubeh(prvni_pulka)


# ══════════════════════════════════════════════════════════════
# ČÁST 4: Efekty
# ══════════════════════════════════════════════════════════════

print("\n=== Zvukové efekty ===\n")

def echo(vzorky: list[int], zpozdeni_ms: int = 200,
          utlum: float = 0.5) -> list[int]:
    """Přidá echo."""
    zpozdeni_vzorku = int(SAMPLE_RATE * zpozdeni_ms / 1000)
    vystup = list(vzorky)
    for i in range(zpozdeni_vzorku, len(vzorky)):
        new_val = int(vzorky[i] + vzorky[i - zpozdeni_vzorku] * utlum)
        vystup[i] = max(-32768, min(32767, new_val))
    return vystup

def zmena_rychlosti(vzorky: list[int], faktor: float) -> list[int]:
    """Zrychlí/zpomalí (resampling)."""
    n_novy = int(len(vzorky) / faktor)
    return [vzorky[int(i * faktor)] for i in range(n_novy)]

def inverze_faze(vzorky: list[int]) -> list[int]:
    return [-v for v in vzorky]

# Aplikuj efekty
with_echo = echo(vsechny_vzorky, zpozdeni_ms=150, utlum=0.4)
uloz_wav(with_echo, "melodie_echo.wav")
print(f"  ✓ melodie_echo.wav  (echo 150ms)")

rychle = zmena_rychlosti(vsechny_vzorky, 1.5)
uloz_wav(rychle, "melodie_rychle.wav")
print(f"  ✓ melodie_rychle.wav  (1.5× rychlost)")


# ══════════════════════════════════════════════════════════════
# ČÁST 5: pydub (pokud dostupný)
# ══════════════════════════════════════════════════════════════

print("\n=== pydub (volitelné) ===\n")

try:
    from pydub import AudioSegment
    from pydub.generators import Sine

    # Generování tónu
    ton = Sine(440).to_audio_segment(duration=1000)   # 1 sec, 440Hz
    ton.export("ton_440hz.wav", format="wav")
    print(f"  ✓ ton_440hz.wav  ({len(ton)}ms)")

    # Mix dvou souborů
    melodie_seg = AudioSegment.from_wav("melodie.wav")
    echo_seg    = AudioSegment.from_wav("melodie_echo.wav")
    mix         = melodie_seg.overlay(echo_seg - 6)   # echo o 6dB tišší
    mix.export("melodie_mix.wav", format="wav")
    print(f"  ✓ melodie_mix.wav  (originál + echo mix)")

    # Konverze do MP3 (potřebuje ffmpeg)
    # mix.export("melodie.mp3", format="mp3")
    Path("ton_440hz.wav").unlink(missing_ok=True)
    Path("melodie_mix.wav").unlink(missing_ok=True)

except ImportError:
    print("  pydub není dostupné: pip install pydub")
    print("  (pro MP3 také potřebuješ ffmpeg)")

# Úklid
for f in ["melodie.wav", "akord_c_dur.wav", "melodie_echo.wav", "melodie_rychle.wav"]:
    Path(f).unlink(missing_ok=True)

print("""
=== Audio knihovny v Pythonu ===

  wave        → vestavěný, jen WAV
  pydub       → pohodlné API, MP3/OGG/FLAC (potřebuje ffmpeg)
  sounddevice → přehrávání a nahrávání v reálném čase
  librosa     → analýza hudby (tempo, spektrum, MFCC) – pip install librosa
  pyaudio     → low-level audio I/O
  scipy.signal→ filtry, FFT, spektrum

  Rychlý start pro nahrávání:
    import sounddevice as sd, numpy as np
    data = sd.rec(44100, samplerate=44100, channels=1)
    sd.wait()
""")

# TVOJE ÚLOHA:
# 1. Napiš funkci generuj_dtmf(cislo) – generuje tón telefonní klávesnice.
# 2. Implementuj FFT vizualizaci spektra (np.fft.rfft + matplotlib).
# 3. Napiš jednoduchý metronom: tick každých N sekund přes sounddevice.
