"""
LEKCE 93: Whisper – speech-to-text
=====================================
pip install openai-whisper
(nebo rychlejší varianta: pip install faster-whisper)

OpenAI Whisper = open-source model pro přepis řeči do textu.
Podporuje 99 jazyků včetně češtiny.
Běží lokálně – žádné API klíče, žádné poplatky.

Modely (velikost × přesnost × rychlost):
  tiny   –  39M params  → rychlý, méně přesný
  base   –  74M params  → dobrý kompromis
  small  – 244M params  → dobrá přesnost
  medium – 769M params  → vysoká přesnost
  large  –  ~3B params  → nejpřesnější, pomalý na CPU
"""

import os
import wave
import struct
import math
import tempfile
from pathlib import Path

print("=== Whisper – speech-to-text ===\n")

# ══════════════════════════════════════════════════════════════
# ČÁST 1: Základní použití
# ══════════════════════════════════════════════════════════════

try:
    import whisper
    WHISPER_OK = True
    print(f"  Whisper dostupný\n")
except ImportError:
    WHISPER_OK = False
    print("  Whisper není nainstalováno: pip install openai-whisper")
    print("  (alternativa: pip install faster-whisper)\n")

print(textwrap.dedent("""\
  import whisper

  # Načti model (stáhne se automaticky při prvním použití)
  model = whisper.load_model("base")   # ~74MB

  # Přepis souboru
  vysledek = model.transcribe("nahravka.wav")
  print(vysledek["text"])

  # S detailními informacemi
  vysledek = model.transcribe("nahravka.wav", verbose=True)
  for segment in vysledek["segments"]:
      print(f"[{segment['start']:.1f}s → {segment['end']:.1f}s] {segment['text']}")

  # Detekce jazyka
  audio  = whisper.load_audio("nahravka.wav")
  audio  = whisper.pad_or_trim(audio)
  mel    = whisper.log_mel_spectrogram(audio).to(model.device)
  _, probs = model.detect_language(mel)
  print(f"Jazyk: {max(probs, key=probs.get)}")

  # Přepis s přepisem do jiného jazyka
  vysledek = model.transcribe("czech_audio.wav",
                               language="cs",
                               task="translate")  # přelož do EN
  print(vysledek["text"])
""") if True else "")

import textwrap

print(textwrap.dedent("""\
  === Whisper API (OpenAI cloud) ===

  # Pokud nechceš lokálně:
  from openai import OpenAI
  client = OpenAI()

  with open("nahravka.wav", "rb") as f:
      transcript = client.audio.transcriptions.create(
          model="whisper-1",
          file=f,
          language="cs",
          response_format="verbose_json",
          timestamp_granularities=["segment"],
      )

  for segment in transcript.segments:
      print(f"[{segment.start:.1f}s] {segment.text}")
"""))


# ══════════════════════════════════════════════════════════════
# ČÁST 2: Generování testovací nahrávky + přepis
# ══════════════════════════════════════════════════════════════

print("=== Vytvoření testovací nahrávky ===\n")

SAMPLE_RATE = 16000   # Whisper preferuje 16kHz

def generuj_test_wav(soubor: str, delka_s: float = 1.0):
    """Generuje krátký syntetický zvuk pro test."""
    vzorky = int(SAMPLE_RATE * delka_s)
    data = []
    for i in range(vzorky):
        # Jednoduchý tón 440Hz
        hodnota = int(16000 * math.sin(2 * math.pi * 440 * i / SAMPLE_RATE))
        data.append(hodnota)
    with wave.open(soubor, "w") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(struct.pack(f"<{len(data)}h", *data))

with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
    tmp_wav = f.name

generuj_test_wav(tmp_wav)
print(f"  Testovací WAV: {tmp_wav} ({Path(tmp_wav).stat().st_size:,} B)")

if WHISPER_OK:
    print("\n  Načítám model tiny (nejrychlejší)...")
    model = whisper.load_model("tiny")
    print(f"  Model načten: {sum(p.numel() for p in model.parameters()):,} parametrů")

    vysledek = model.transcribe(tmp_wav)
    print(f"\n  Přepis tónového testu: {repr(vysledek['text'])}")
    print(f"  (Syntetický tón → pravděpodobně prázdný nebo šum)")
    print("\n  Pro reálný test: nahraj WAV se svým hlasem a spusť znovu.")

Path(tmp_wav).unlink(missing_ok=True)


# ══════════════════════════════════════════════════════════════
# ČÁST 3: Praktické pipeline
# ══════════════════════════════════════════════════════════════

print("\n=== Praktické pipeline ===\n")
print(textwrap.dedent("""\
  # Titulky pro video (SRT formát)
  import whisper

  model   = whisper.load_model("medium")
  vysl    = model.transcribe("video.mp4", verbose=False)

  with open("titulky.srt", "w", encoding="utf-8") as f:
      for i, seg in enumerate(vysl["segments"], 1):
          start = formát_cas(seg["start"])
          konec = formát_cas(seg["end"])
          f.write(f"{i}\\n{start} --> {konec}\\n{seg['text'].strip()}\\n\\n")

  def formát_cas(sekundy: float) -> str:
      h  = int(sekundy // 3600)
      m  = int((sekundy % 3600) // 60)
      s  = int(sekundy % 60)
      ms = int((sekundy % 1) * 1000)
      return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


  # Záznam z mikrofonu + přepis v reálném čase
  import sounddevice as sd    # pip install sounddevice
  import numpy as np

  def nahraj_a_prepis(delka_s: int = 5):
      print(f"Nahrávám {delka_s}s...")
      audio = sd.rec(delka_s * 16000, samplerate=16000, channels=1, dtype="float32")
      sd.wait()

      model  = whisper.load_model("base")
      vysl   = model.transcribe(audio.flatten(), language="cs")
      return vysl["text"]

  text = nahraj_a_prepis(5)
  print(f"Přepsáno: {text}")


  # Klasifikace sentimentu přepsaného textu (kombinace s lekcí 81)
  prepis  = model.transcribe("hovor.wav")["text"]
  from nltk.sentiment import SentimentIntensityAnalyzer
  sia     = SentimentIntensityAnalyzer()
  scores  = sia.polarity_scores(prepis)
  print(f"Sentiment: {scores}")
"""))

print("""
=== Faster Whisper (doporučeno pro produkci) ===

  pip install faster-whisper   # 2-4× rychlejší, méně RAM

  from faster_whisper import WhisperModel

  model = WhisperModel("base", device="cpu", compute_type="int8")
  segments, info = model.transcribe("audio.wav", beam_size=5)

  print(f"Jazyk: {info.language} ({info.language_probability:.0%})")
  for segment in segments:
      print(f"[{segment.start:.1f}s → {segment.end:.1f}s] {segment.text}")


=== Kdy Whisper ===

  ✓ Offline přepis (žádné API klíče)
  ✓ Čeština (model medium nebo large pro nejlepší výsledky)
  ✓ Titulky k videím
  ✓ Přepis schůzek, přednášek
  ✓ Voice commands v aplikaci
  ✗ Real-time streaming (latence) → použij Deepgram API nebo Vosk
""")

# TVOJE ÚLOHA:
# 1. Nahraj krátký hovor a přepiš ho Whisperem do SRT titulků.
# 2. Kombinuj s lekcí 74 (LLM API) – přepiš → shrň Claudem.
# 3. Napiš CLI nástroj: přijme WAV/MP4, vrátí .txt nebo .srt.
