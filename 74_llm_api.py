"""
LEKCE 74: LLM API – Claude a OpenAI z Pythonu
================================================
pip install anthropic openai

Volání velkých jazykových modelů z Pythonu.

CLAUDE (Anthropic)          OPENAI
──────────────────          ──────
claude-opus-4-7   ←→        gpt-4o
claude-sonnet-4-6 ←→        gpt-4o-mini
claude-haiku-4-5  ←→        gpt-4o-mini (rychlý)

Kdy co:
  Claude  → delší kontext (1M tokenů), lepší instrukce, tool use
  OpenAI  → velký ekosystém, fine-tuning, embeddings, DALL-E

Oba mají:
  Completion   – jednorázová odpověď
  Chat         – konverzace s historií
  Streaming    – odpověď token po tokenu
  Tool use     – model volá tvoje funkce
  Vision       – model vidí obrázky
  JSON output  – strukturovaná odpověď
"""

import os, json, time
from typing import Iterator

# ── Instalace ─────────────────────────────────────────────────
# pip install anthropic openai

ANTHROPIC_KEY = os.getenv("ANTHROPIC_API_KEY", "")
OPENAI_KEY    = os.getenv("OPENAI_API_KEY", "")

# ══════════════════════════════════════════════════════════════
# ČÁST 1: CLAUDE – Anthropic SDK
# ══════════════════════════════════════════════════════════════

print("=" * 55)
print("CLAUDE – Anthropic SDK")
print("=" * 55)

if not ANTHROPIC_KEY:
    print("\nℹ  ANTHROPIC_API_KEY není nastaven.")
    print("   export ANTHROPIC_API_KEY='sk-ant-...'")
    print("   Lekce zobrazuje kód – nastav klíč a spusť znovu.\n")
else:
    import anthropic
    claude = anthropic.Anthropic()   # klíč z ANTHROPIC_API_KEY

    # ── 1a. Základní volání ───────────────────────────────────
    print("\n--- Základní volání ---")

    zprava = claude.messages.create(
        model="claude-opus-4-7",          # vždy nejnovější Opus
        max_tokens=256,
        messages=[{
            "role": "user",
            "content": "Napiš haiku o Pythonu. Jen haiku, nic jiného.",
        }],
    )
    print(zprava.content[0].text)
    print(f"  [tokeny: in={zprava.usage.input_tokens} out={zprava.usage.output_tokens}]")

    # ── 1b. System prompt + konverzace ───────────────────────
    print("\n--- System prompt ---")

    odpoved = claude.messages.create(
        model="claude-opus-4-7",
        max_tokens=512,
        system="Jsi přátelský Python lektor. Odpovídej stručně česky.",
        messages=[
            {"role": "user",      "content": "Co je dekorátor?"},
            {"role": "assistant", "content": "Dekorátor je funkce, která obalí jinou funkci a přidá jí chování."},
            {"role": "user",      "content": "Dej mi příklad."},
        ],
    )
    print(odpoved.content[0].text[:200])

    # ── 1c. Streaming ─────────────────────────────────────────
    print("\n--- Streaming ---")
    print("Odpověď: ", end="", flush=True)

    with claude.messages.stream(
        model="claude-opus-4-7",
        max_tokens=128,
        messages=[{"role": "user", "content": "Tři věci které musíš vědět o Pythonu. Krátce."}],
    ) as stream:
        for text in stream.text_stream:
            print(text, end="", flush=True)

    final = stream.get_final_message()
    print(f"\n  [tokeny: {final.usage.output_tokens}]")

    # ── 1d. Tool use (function calling) ──────────────────────
    print("\n--- Tool use ---")

    NASTROJE_CLAUDE = [
        {
            "name": "vypocti",
            "description": "Vypočítá matematický výraz",
            "input_schema": {
                "type": "object",
                "properties": {
                    "vyraz": {"type": "string", "description": "Python výraz, např. '2**10'"},
                },
                "required": ["vyraz"],
            },
        },
        {
            "name": "pocasi",
            "description": "Vrátí počasí pro město",
            "input_schema": {
                "type": "object",
                "properties": {
                    "mesto": {"type": "string"},
                },
                "required": ["mesto"],
            },
        },
    ]

    def spust_nastroj(jmeno: str, vstup: dict) -> str:
        if jmeno == "vypocti":
            try:
                return str(eval(vstup["vyraz"]))   # jen pro demo!
            except Exception as e:
                return f"Chyba: {e}"
        if jmeno == "pocasi":
            return f"V {vstup['mesto']}: 22 °C, slunečno"
        return "Neznámý nástroj"

    zpravy = [{"role": "user", "content": "Kolik je 2 na 10 a jaké je počasí v Praze?"}]

    while True:
        odpoved = claude.messages.create(
            model="claude-opus-4-7",
            max_tokens=512,
            tools=NASTROJE_CLAUDE,
            messages=zpravy,
        )

        if odpoved.stop_reason == "end_turn":
            for blok in odpoved.content:
                if blok.type == "text":
                    print(f"  Claude: {blok.text}")
            break

        # Zpracuj tool_use bloky
        zpravy.append({"role": "assistant", "content": odpoved.content})
        vysledky = []
        for blok in odpoved.content:
            if blok.type == "tool_use":
                vysledek = spust_nastroj(blok.name, blok.input)
                print(f"  nástroj {blok.name}({blok.input}) → {vysledek}")
                vysledky.append({
                    "type": "tool_result",
                    "tool_use_id": blok.id,
                    "content": vysledek,
                })
        zpravy.append({"role": "user", "content": vysledky})

    # ── 1e. Structured output (JSON schema) ───────────────────
    print("\n--- Structured output ---")

    from pydantic import BaseModel

    class Analyza(BaseModel):
        jazyk: str
        obtiznost: str          # "snadné" / "střední" / "těžké"
        klicova_temata: list[str]
        doporucene_lekce: list[int]

    odpoved = claude.messages.parse(
        model="claude-opus-4-7",
        max_tokens=512,
        messages=[{
            "role": "user",
            "content": "Analyzuj toto téma: asyncio, Futures, Task, event loop",
        }],
        output_format=Analyza,
    )
    analyza: Analyza = odpoved.parsed_output
    print(f"  Jazyk: {analyza.jazyk}")
    print(f"  Obtížnost: {analyza.obtiznost}")
    print(f"  Témata: {analyza.klicova_temata}")

    # ── 1f. Prompt caching ────────────────────────────────────
    print("\n--- Prompt caching (velký kontext) ---")

    VELKY_KONTEXT = "Obsah Pythonské dokumentace... " * 500   # ~10 000 tokenů

    def dotaz_s_cache(otazka: str) -> tuple[str, bool]:
        resp = claude.messages.create(
            model="claude-opus-4-7",
            max_tokens=256,
            system=[{
                "type": "text",
                "text": VELKY_KONTEXT,
                "cache_control": {"type": "ephemeral"},  # cachuj toto
            }],
            messages=[{"role": "user", "content": otazka}],
        )
        z_cache = resp.usage.cache_read_input_tokens > 0
        return resp.content[0].text, z_cache

    t1 = time.perf_counter()
    _, hit1 = dotaz_s_cache("Co je Python?")
    t2 = time.perf_counter()
    _, hit2 = dotaz_s_cache("Co je asyncio?")
    t3 = time.perf_counter()

    print(f"  Dotaz 1: {(t2-t1)*1000:.0f}ms  cache={'HIT' if hit1 else 'MISS (zapsáno)'}")
    print(f"  Dotaz 2: {(t3-t2)*1000:.0f}ms  cache={'HIT' if hit2 else 'MISS'}")
    print(f"  Druhý dotaz byl {'rychlejší ✓' if t3-t2 < t2-t1 else 'podobně rychlý'}")

    # ── 1g. Error handling ────────────────────────────────────
    print("\n--- Error handling ---")

    try:
        claude.messages.create(
            model="claude-neexistujici-model",
            max_tokens=10,
            messages=[{"role": "user", "content": "Ahoj"}],
        )
    except anthropic.NotFoundError as e:
        print(f"  NotFoundError: {e.message[:60]}")
    except anthropic.AuthenticationError:
        print("  AuthenticationError: neplatný API klíč")
    except anthropic.RateLimitError as e:
        retry = e.response.headers.get("retry-after", "?")
        print(f"  RateLimitError: retry after {retry}s")
    except anthropic.APIStatusError as e:
        print(f"  APIStatusError {e.status_code}: {e.message[:60]}")


# ══════════════════════════════════════════════════════════════
# ČÁST 2: OPENAI SDK
# ══════════════════════════════════════════════════════════════

print("\n" + "=" * 55)
print("OPENAI SDK")
print("=" * 55)

if not OPENAI_KEY:
    print("\nℹ  OPENAI_API_KEY není nastaven.")
    print("   export OPENAI_API_KEY='sk-...'")
    print("   Lekce zobrazuje kód – nastav klíč a spusť znovu.\n")
else:
    from openai import OpenAI
    oai = OpenAI()   # klíč z OPENAI_API_KEY

    # ── 2a. Základní volání ───────────────────────────────────
    print("\n--- Základní volání ---")

    zprava = oai.chat.completions.create(
        model="gpt-4o-mini",
        max_tokens=256,
        messages=[{
            "role": "user",
            "content": "Napiš haiku o Pythonu. Jen haiku, nic jiného.",
        }],
    )
    print(zprava.choices[0].message.content)
    print(f"  [tokeny: in={zprava.usage.prompt_tokens} out={zprava.usage.completion_tokens}]")

    # ── 2b. System prompt + konverzace ───────────────────────
    print("\n--- System prompt ---")

    odpoved = oai.chat.completions.create(
        model="gpt-4o-mini",
        max_tokens=512,
        messages=[
            {"role": "system",    "content": "Jsi přátelský Python lektor. Odpovídej stručně česky."},
            {"role": "user",      "content": "Co je dekorátor?"},
            {"role": "assistant", "content": "Dekorátor je funkce, která obalí jinou funkci a přidá jí chování."},
            {"role": "user",      "content": "Dej mi příklad."},
        ],
    )
    print(odpoved.choices[0].message.content[:200])

    # ── 2c. Streaming ─────────────────────────────────────────
    print("\n--- Streaming ---")
    print("Odpověď: ", end="", flush=True)

    stream = oai.chat.completions.create(
        model="gpt-4o-mini",
        max_tokens=128,
        stream=True,
        messages=[{"role": "user", "content": "Tři věci které musíš vědět o Pythonu. Krátce."}],
    )
    for chunk in stream:
        delta = chunk.choices[0].delta.content or ""
        print(delta, end="", flush=True)
    print()

    # ── 2d. Tool use ──────────────────────────────────────────
    print("\n--- Tool use ---")

    NASTROJE_OAI = [
        {
            "type": "function",
            "function": {
                "name": "vypocti",
                "description": "Vypočítá matematický výraz",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "vyraz": {"type": "string"},
                    },
                    "required": ["vyraz"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "pocasi",
                "description": "Vrátí počasí pro město",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "mesto": {"type": "string"},
                    },
                    "required": ["mesto"],
                },
            },
        },
    ]

    zpravy_oai = [{"role": "user", "content": "Kolik je 2 na 10 a jaké je počasí v Praze?"}]

    while True:
        odpoved = oai.chat.completions.create(
            model="gpt-4o-mini",
            tools=NASTROJE_OAI,
            messages=zpravy_oai,
        )
        zprava_asistenta = odpoved.choices[0].message
        zpravy_oai.append(zprava_asistenta)

        if not zprava_asistenta.tool_calls:
            print(f"  GPT: {zprava_asistenta.content}")
            break

        for volani in zprava_asistenta.tool_calls:
            vstup = json.loads(volani.function.arguments)
            vysledek = spust_nastroj(volani.function.name, vstup)
            print(f"  nástroj {volani.function.name}({vstup}) → {vysledek}")
            zpravy_oai.append({
                "role": "tool",
                "tool_call_id": volani.id,
                "content": vysledek,
            })

    # ── 2e. Structured output ─────────────────────────────────
    print("\n--- Structured output (response_format) ---")

    odpoved = oai.chat.completions.create(
        model="gpt-4o-mini",
        max_tokens=512,
        response_format={"type": "json_object"},
        messages=[{
            "role": "system", "content": "Vrať JSON s klíči: jazyk, obtiznost, klicova_temata.",
        }, {
            "role": "user", "content": "Analyzuj: asyncio, Futures, Task, event loop",
        }],
    )
    data = json.loads(odpoved.choices[0].message.content)
    print(f"  {data}")

    # ── 2f. Error handling ────────────────────────────────────
    print("\n--- Error handling ---")
    from openai import NotFoundError, RateLimitError, AuthenticationError

    try:
        oai.chat.completions.create(
            model="gpt-neexistujici",
            max_tokens=10,
            messages=[{"role": "user", "content": "Ahoj"}],
        )
    except NotFoundError as e:
        print(f"  NotFoundError: {str(e)[:60]}")
    except AuthenticationError:
        print("  AuthenticationError: neplatný API klíč")
    except RateLimitError:
        print("  RateLimitError: překročen limit")


# ══════════════════════════════════════════════════════════════
# ČÁST 3: SROVNÁNÍ A PRODUKČNÍ VZORY
# ══════════════════════════════════════════════════════════════

print("\n" + "=" * 55)
print("PRODUKČNÍ VZORY")
print("=" * 55)

# ── Cache s file-backend ──────────────────────────────────────
import hashlib
from pathlib import Path

CACHE_DIR = Path(".llm_cache")
CACHE_DIR.mkdir(exist_ok=True)

def chat_s_cache(prompt: str, ttl_hod: int = 24) -> str | None:
    """Klíčovaná file cache – šetří API kredity při vývoji."""
    klic  = hashlib.md5(prompt.encode()).hexdigest()
    soubor = CACHE_DIR / f"{klic}.json"
    if soubor.exists():
        data = json.loads(soubor.read_text())
        if time.time() - data["ts"] < ttl_hod * 3600:
            return data["odpoved"]
    return None

def chat_uloz_cache(prompt: str, odpoved: str):
    klic = hashlib.md5(prompt.encode()).hexdigest()
    soubor = CACHE_DIR / f"{klic}.json"
    soubor.write_text(json.dumps({"ts": time.time(), "odpoved": odpoved}))

# ── Retry s exponential backoff ───────────────────────────────
def api_s_retry(fn, max_pokusy: int = 3):
    """Automatický retry pro rate limity a 5xx chyby."""
    for pokus in range(max_pokusy):
        try:
            return fn()
        except Exception as e:
            zprava = str(e).lower()
            je_retryable = "rate" in zprava or "429" in zprava or "500" in zprava
            if je_retryable and pokus < max_pokusy - 1:
                zpozdeni = 2 ** pokus
                print(f"  Retry {pokus+1}/{max_pokusy} za {zpozdeni}s... ({type(e).__name__})")
                time.sleep(zpozdeni)
            else:
                raise

import shutil
shutil.rmtree(CACHE_DIR, ignore_errors=True)

print("""
=== Srovnání Claude vs OpenAI ===

                      Claude          OpenAI
  Max kontext         1M tokenů       128K (gpt-4o)
  Tool use            ✓               ✓
  Vision              ✓               ✓ (gpt-4o)
  JSON output         ✓ output_config ✓ response_format
  Streaming           ✓               ✓
  Prompt caching      ✓ (vestavěné)   ✗ (jen přes API tier)
  Embeddings          ✗               ✓ text-embedding-3
  Fine-tuning         ✗               ✓
  Image generation    ✗               ✓ DALL-E 3
  Cena (input)        $5/1M (Opus 4.7)  $2.5/1M (gpt-4o)

=== Kdy co použít ===

  Claude:   delší dokumenty, složité instrukce, bezpečnost
  OpenAI:   ekosystém, embeddings, generování obrázků
  Oba:      prototypuj s gpt-4o-mini nebo haiku (levné)
            produkce s opus/gpt-4o dle požadavků

=== Minimální produkční checklist ===

  ✓ Klíče z env proměnných (NIKDY v kódu!)
  ✓ Retry s exponential backoff
  ✓ Cache pro opakující se dotazy
  ✓ Logging (co jde do API, co přijde zpět)
  ✓ Timeout (prevent hanging requests)
  ✓ Sanitizace vstupu (SQL/prompt injection)
""")

# TVOJE ÚLOHA:
# 1. Nastav ANTHROPIC_API_KEY a spusť reálné volání.
# 2. Napiš funkci sumarizuj(text) která shrne libovolný text na 3 věty.
# 3. Postav chatbota s pamětí – ukládej historii do SQLite (lekce 40).
# 4. Přidej streaming do webové aplikace z lekce 56 (FastAPI + Server-Sent Events).
