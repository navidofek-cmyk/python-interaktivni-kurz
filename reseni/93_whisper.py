"""Řešení – Lekce 93: Whisper – speech-to-text"""

# vyžaduje: pip install openai-whisper
# alternativa: pip install faster-whisper

import wave
import struct
import math
import tempfile
import re
import sys
from pathlib import Path
from datetime import timedelta

SAMPLE_RATE = 16000   # Whisper preferuje 16kHz

def generuj_test_wav(soubor: str, freq: float = 440.0, delka_s: float = 1.0):
    """Generuje syntetický WAV pro testy."""
    vzorky = int(SAMPLE_RATE * delka_s)
    data   = [int(16000 * math.sin(2 * math.pi * freq * i / SAMPLE_RATE))
              for i in range(vzorky)]
    with wave.open(soubor, "w") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(struct.pack(f"<{len(data)}h", *data))

try:
    import whisper
    WHISPER_OK = True
    print("Whisper dostupný\n")
except ImportError:
    WHISPER_OK = False
    print("Whisper není nainstalováno: pip install openai-whisper\n")

import textwrap


# 1. Přepis hovorů + SRT titulky
print("=== 1. SRT titulky z nahrávky ===\n")

def format_cas_srt(sekundy: float) -> str:
    """Formátuje čas do SRT formátu: HH:MM:SS,mmm"""
    td   = timedelta(seconds=sekundy)
    hodiny = int(td.total_seconds() // 3600)
    minuty = int((td.total_seconds() % 3600) // 60)
    seky   = int(td.total_seconds() % 60)
    milisy = int((td.total_seconds() % 1) * 1000)
    return f"{hodiny:02d}:{minuty:02d}:{seky:02d},{milisy:03d}"

def prepis_na_srt(model, audio_soubor: str,
                   jazyk: str = "cs") -> str:
    """
    Přepíše audio soubor a vrátí obsah SRT souboru.
    """
    vysledek = model.transcribe(
        audio_soubor,
        language=jazyk,
        verbose=False,
    )

    radky = []
    for i, seg in enumerate(vysledek["segments"], 1):
        zacatek = format_cas_srt(seg["start"])
        konec   = format_cas_srt(seg["end"])
        text    = seg["text"].strip()
        radky.append(f"{i}\n{zacatek} --> {konec}\n{text}\n")

    return "\n".join(radky)

def prepis_na_txt(model, audio_soubor: str,
                   jazyk: str = "cs") -> str:
    """Přepíše audio soubor a vrátí čistý text."""
    vysledek = model.transcribe(audio_soubor, language=jazyk, verbose=False)
    return vysledek["text"]

# Ukázka kódu pro reálné použití
print(textwrap.dedent("""\
  Použití (s reálnou nahrávkou):
    import whisper
    model = whisper.load_model("medium")   # medium = lepší přesnost pro češtinu

    # SRT titulky
    srt = prepis_na_srt(model, "hovor.wav", jazyk="cs")
    Path("titulky.srt").write_text(srt, encoding="utf-8")
    print(srt[:300])

    # Čistý text
    txt = prepis_na_txt(model, "hovor.wav")
    Path("prepis.txt").write_text(txt, encoding="utf-8")
"""))

# Test s syntetickým WAV
if WHISPER_OK:
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        tmp_wav = f.name

    generuj_test_wav(tmp_wav, freq=440, delka_s=1.0)

    print("  Načítám tiny model...")
    model = whisper.load_model("tiny")

    # SRT test
    srt_obsah = prepis_na_srt(model, tmp_wav, jazyk="cs")
    print(f"  SRT výstup pro syntetický tón:")
    if srt_obsah.strip():
        print(textwrap.indent(srt_obsah[:200], "    "))
    else:
        print("    (prázdný – syntetický tón nezpůsobí rozpoznatelnou řeč)")

    Path(tmp_wav).unlink(missing_ok=True)


# 2. Kombinace Whisper + Claude: přepis → shrnutí
print("\n=== 2. Whisper + Claude – přepis → shrnutí ===\n")

def prepis_a_shrn(audio_soubor: str,
                   model_whisper=None,
                   anthropic_key: str = "") -> dict:
    """
    Pipeline: WAV → přepis (Whisper) → shrnutí (Claude).
    Vrátí {"prepis": str, "shrnuti": str, "jazyk": str}.
    """
    import os
    key = anthropic_key or os.getenv("ANTHROPIC_API_KEY", "")

    # Krok 1: Přepis
    if model_whisper is not None:
        vysledek = model_whisper.transcribe(audio_soubor, verbose=False)
        prepis   = vysledek["text"]
        jazyk    = vysledek.get("language", "unknown")
    else:
        prepis = "[Whisper není dostupný]"
        jazyk  = "cs"

    # Krok 2: Shrnutí přes Claude
    if key and prepis.strip() and prepis != "[Whisper není dostupný]":
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=key)
            resp   = client.messages.create(
                model="claude-opus-4-7",
                max_tokens=512,
                system="Jsi asistent pro shrnutí přepisů. Shrň přepis na 2-3 věty.",
                messages=[{"role": "user",
                            "content": f"Přepis:\n{prepis}\n\nShrnutí:"}],
            )
            shrnuti = resp.content[0].text
        except Exception as e:
            shrnuti = f"[Claude nedostupný: {e}]"
    else:
        shrnuti = "[Nastav ANTHROPIC_API_KEY pro shrnutí]"

    return {"prepis": prepis, "shrnuti": shrnuti, "jazyk": jazyk}

# Demo
import os
print("  Pipeline demo:")
if WHISPER_OK:
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        tmp2 = f.name
    generuj_test_wav(tmp2, freq=330, delka_s=0.5)
    vysledek = prepis_a_shrn(tmp2, model_whisper=model if WHISPER_OK else None)
    print(f"  Přepis:  {repr(vysledek['prepis'])}")
    print(f"  Shrnutí: {vysledek['shrnuti']}")
    print(f"  Jazyk:   {vysledek['jazyk']}")
    Path(tmp2).unlink(missing_ok=True)
else:
    print("  (Whisper nedostupný – viz instalace výše)")


# 3. CLI nástroj: WAV/MP4 → .txt nebo .srt
print("\n=== 3. CLI nástroj ===\n")

CLI_KOD = '''\
#!/usr/bin/env python3
"""
Whisper CLI – přepis audio/video na text nebo SRT titulky.
Použití: python whisper_cli.py <soubor> [--format txt|srt] [--lang cs] [--model base]

Příklady:
  python whisper_cli.py hovor.wav
  python whisper_cli.py video.mp4 --format srt --lang cs
  python whisper_cli.py meeting.wav --format txt --model medium
"""

import argparse
import sys
from pathlib import Path

def parse_args():
    parser = argparse.ArgumentParser(description="Whisper CLI – přepis řeči")
    parser.add_argument("soubor",           help="Vstupní audio/video soubor")
    parser.add_argument("--format",  "-f", default="txt",
                        choices=["txt", "srt"], help="Výstupní formát (default: txt)")
    parser.add_argument("--lang",    "-l", default="cs",  help="Jazyk (default: cs)")
    parser.add_argument("--model",   "-m", default="base",
                        choices=["tiny","base","small","medium","large"],
                        help="Whisper model (default: base)")
    parser.add_argument("--output",  "-o", default=None,  help="Výstupní soubor")
    return parser.parse_args()

def format_cas_srt(sekundy: float) -> str:
    td = __import__("datetime").timedelta(seconds=sekundy)
    h  = int(td.total_seconds() // 3600)
    m  = int((td.total_seconds() % 3600) // 60)
    s  = int(td.total_seconds() % 60)
    ms = int((td.total_seconds() % 1) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

def main():
    args = parse_args()

    vstup = Path(args.soubor)
    if not vstup.exists():
        print(f"Chyba: soubor {vstup} neexistuje", file=sys.stderr)
        sys.exit(1)

    # Výchozí výstupní soubor
    vystup = Path(args.output) if args.output else vstup.with_suffix(f".{args.format}")

    print(f"Přepisuji: {vstup}")
    print(f"Model:     {args.model}")
    print(f"Jazyk:     {args.lang}")
    print(f"Formát:    {args.format}")
    print(f"Výstup:    {vystup}")

    try:
        import whisper
    except ImportError:
        print("Instaluj: pip install openai-whisper", file=sys.stderr)
        sys.exit(1)

    print("Načítám model...")
    model = whisper.load_model(args.model)

    print("Přepisuji...")
    result = model.transcribe(str(vstup), language=args.lang, verbose=False)

    if args.format == "txt":
        obsah = result["text"].strip()
    else:
        radky = []
        for i, seg in enumerate(result["segments"], 1):
            zacatek = format_cas_srt(seg["start"])
            konec   = format_cas_srt(seg["end"])
            text    = seg["text"].strip()
            radky.append(f"{i}\\n{zacatek} --> {konec}\\n{text}\\n")
        obsah = "\\n".join(radky)

    vystup.write_text(obsah, encoding="utf-8")
    print(f"\\nHotovo! Uloženo: {vystup} ({len(obsah):,} znaků)")
    print(f"Detekovaný jazyk: {result.get('language', '?')}")

if __name__ == "__main__":
    main()
'''
print(CLI_KOD)

# Uložit CLI skript
Path("whisper_cli.py").write_text(CLI_KOD.strip(), encoding="utf-8")
print(f"  ✓ whisper_cli.py uložen ({Path('whisper_cli.py').stat().st_size:,} B)")
print()
print("  Použití:")
print("    python whisper_cli.py hovor.wav")
print("    python whisper_cli.py video.mp4 --format srt --lang cs")
print("    python whisper_cli.py meeting.wav --model medium --output prepis.txt")
Path("whisper_cli.py").unlink(missing_ok=True)

print("\n=== Shrnutí ===")
print("  1. prepis_na_srt()  – Whisper segmenty → SRT formát (HH:MM:SS,mmm)")
print("  2. prepis_a_shrn()  – pipeline Whisper + Claude API")
print("  3. whisper_cli.py   – argparse CLI, txt/srt výstup, volba modelu")
