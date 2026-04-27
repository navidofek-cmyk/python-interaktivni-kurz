"""
LEKCE 74: LLM API – Claude a OpenAI z Pythonu
================================================
pip install anthropic openai

Volání velkých jazykových modelů (LLM) z Pythonu.
Claude (Anthropic) a GPT (OpenAI) mají podobné API.

Koncepty:
  Completion  – model dokončí text / odpoví na otázku
  Chat        – konverzace s historií zpráv
  Streaming   – odpověď přichází postupně (token po tokenu)
  Tool use    – model může volat funkce (Function Calling)
  Vision      – model vidí obrázky
  Embeddings  – převod textu na číselný vektor

Tato lekce:
  - Ukazuje jak API volat (s i bez klíče)
  - Implementuje vzory: retry, cache, rate limit, structured output
  - Simuluje odpovědi pokud klíč není dostupný
"""

import os
import time
import json
import hashlib
import re
from pathlib import Path
from functools import lru_cache
from dataclasses import dataclass
from typing import Iterator

# ══════════════════════════════════════════════════════════════
# ČÁST 1: Základní volání API
# ══════════════════════════════════════════════════════════════

print("=== LLM API – Claude (Anthropic) ===\n")

ANTHROPIC_KEY = os.getenv("ANTHROPIC_API_KEY", "")
OPENAI_KEY    = os.getenv("OPENAI_API_KEY", "")

# ── Simulátor pro demo bez API klíče ─────────────────────────
class LLMSimulator:
    """Simuluje LLM odpovědi pro demo bez API klíče."""
    ODPOVEDI = {
        "haiku": "Kód šumí tiše,\nPython tančí s daty,\nsvět se točí dál.",
        "default": "Jsem simulovaná odpověď LLM. Pro reálné volání nastav ANTHROPIC_API_KEY.",
    }

    def zprava(self, obsah: str, **kwargs) -> str:
        if "haiku" in obsah.lower() or "báseň" in obsah.lower():
            time.sleep(0.1)
            return self.ODPOVEDI["haiku"]
        time.sleep(0.2)
        return f"[Simulace] Odpověď na: {obsah[:50]}..."

    def stream(self, obsah: str, **kwargs) -> Iterator[str]:
        odpoved = self.zprava(obsah)
        for slovo in odpoved.split():
            yield slovo + " "
            time.sleep(0.02)


def vytvor_klienta():
    """Vytvoří reálný nebo simulovaný LLM klient."""
    if ANTHROPIC_KEY:
        try:
            import anthropic
            klient = anthropic.Anthropic(api_key=ANTHROPIC_KEY)
            print("  ✓ Anthropic klient inicializován")
            return "anthropic", klient
        except ImportError:
            print("  pip install anthropic")

    if OPENAI_KEY:
        try:
            import openai
            klient = openai.OpenAI(api_key=OPENAI_KEY)
            print("  ✓ OpenAI klient inicializován")
            return "openai", klient
        except ImportError:
            print("  pip install openai")

    print("  ℹ Žádný API klíč nenalezen – používám simulátor")
    print("  Nastav ANTHROPIC_API_KEY nebo OPENAI_API_KEY pro reálná volání\n")
    return "sim", LLMSimulator()

typ, klient = vytvor_klienta()


def chat(zprava: str, system: str = "", model: str = None) -> str:
    """Jednotné rozhraní pro Claude i OpenAI."""
    if typ == "anthropic":
        kwargs = {
            "model": model or "claude-opus-4-5",
            "max_tokens": 1024,
            "messages": [{"role": "user", "content": zprava}],
        }
        if system:
            kwargs["system"] = system
        resp = klient.messages.create(**kwargs)
        return resp.content[0].text

    elif typ == "openai":
        zpravy = []
        if system:
            zpravy.append({"role": "system", "content": system})
        zpravy.append({"role": "user", "content": zprava})
        resp = klient.chat.completions.create(
            model=model or "gpt-4o-mini",
            messages=zpravy,
            max_tokens=1024,
        )
        return resp.choices[0].message.content

    else:
        return klient.zprava(zprava, system=system)


# Základní volání
print("Základní dotaz:")
odpoved = chat("Napiš haiku o Pythonu.")
print(f"  {odpoved}\n")


# ══════════════════════════════════════════════════════════════
# ČÁST 2: Konverzace s historií
# ══════════════════════════════════════════════════════════════

print("=== Konverzace s historií ===\n")

@dataclass
class Zprava:
    role:    str   # "user" nebo "assistant"
    obsah:   str

class Konverzace:
    def __init__(self, system: str = ""):
        self.system  = system
        self.historie: list[Zprava] = []

    def posli(self, zprava: str) -> str:
        self.historie.append(Zprava("user", zprava))

        if typ == "anthropic":
            resp = klient.messages.create(
                model="claude-opus-4-5",
                max_tokens=1024,
                system=self.system,
                messages=[{"role": z.role, "content": z.obsah}
                           for z in self.historie],
            ) if ANTHROPIC_KEY else None
            odpoved = resp.content[0].text if resp else klient.zprava(zprava)
        elif typ == "openai":
            zpravy = ([{"role": "system", "content": self.system}]
                       if self.system else [])
            zpravy += [{"role": z.role, "content": z.obsah}
                        for z in self.historie]
            resp = klient.chat.completions.create(
                model="gpt-4o-mini", messages=zpravy, max_tokens=1024
            )
            odpoved = resp.choices[0].message.content
        else:
            odpoved = klient.zprava(zprava)

        self.historie.append(Zprava("assistant", odpoved))
        return odpoved

    def tiskni_historii(self):
        for z in self.historie:
            ikona = "👤" if z.role == "user" else "🤖"
            print(f"  {ikona} {z.obsah[:80]}")

konv = Konverzace(system="Jsi přátelský Python lektor. Odpovídej stručně česky.")
otazky = [
    "Co je dekorátor v Pythonu?",
    "Dej mi jednoduchý příklad.",
]
for otazka in otazky:
    odpoved = konv.posli(otazka)
    print(f"  Otázka: {otazka}")
    print(f"  Odpověď: {odpoved[:100]}...\n")


# ══════════════════════════════════════════════════════════════
# ČÁST 3: Structured output – JSON odpovědi
# ══════════════════════════════════════════════════════════════

print("=== Structured Output – JSON ===\n")

def extrahuj_json(text: str) -> dict:
    """Vytáhni JSON z odpovědi modelu."""
    m = re.search(r"\{.*\}", text, re.DOTALL)
    if m:
        try:
            return json.loads(m.group())
        except json.JSONDecodeError:
            pass
    return {}

SCHEMA_PROMPT = """\
Analyzuj tento Python kód a vrať JSON s těmito klíči:
- "funkce": seznam názvů funkcí
- "tridy": seznam názvů tříd
- "importy": seznam importovaných modulů
- "slozitost": "nízká" / "střední" / "vysoká"

Kód:
{kod}

Vrať POUZE validní JSON, nic jiného."""

ukazka_kodu = """\
import asyncio
from dataclasses import dataclass

@dataclass
class Student:
    jmeno: str
    body: float

async def nacti_studenty(db_url: str) -> list[Student]:
    await asyncio.sleep(0.1)
    return [Student("Míša", 87.5)]

def vypocti_prumer(studenti: list[Student]) -> float:
    return sum(s.body for s in studenti) / len(studenti)
"""

prompt = SCHEMA_PROMPT.format(kod=ukazka_kodu)
if typ == "sim":
    # Simulovaná odpověď
    analyza = {
        "funkce": ["nacti_studenty", "vypocti_prumer"],
        "tridy": ["Student"],
        "importy": ["asyncio", "dataclasses"],
        "slozitost": "nízká",
    }
else:
    odpoved = chat(prompt)
    analyza = extrahuj_json(odpoved)

print(f"  Analýza kódu: {json.dumps(analyza, ensure_ascii=False, indent=2)}")


# ══════════════════════════════════════════════════════════════
# ČÁST 4: Cache a retry
# ══════════════════════════════════════════════════════════════

print("\n=== Cache a retry ===\n")

CACHE_DIR = Path(".llm_cache")
CACHE_DIR.mkdir(exist_ok=True)

def klic_cache(zprava: str, system: str = "") -> str:
    return hashlib.md5(f"{system}:{zprava}".encode()).hexdigest()

def chat_s_cache(zprava: str, system: str = "", ttl_hod: int = 24) -> str:
    """LLM volání s file-based cache."""
    klic = klic_cache(zprava, system)
    soubor = CACHE_DIR / f"{klic}.json"

    if soubor.exists():
        data = json.loads(soubor.read_text())
        vek = time.time() - data["ts"]
        if vek < ttl_hod * 3600:
            print(f"  [cache HIT] {vek:.0f}s starý")
            return data["odpoved"]

    print(f"  [cache MISS] volám API...")
    odpoved = chat(zprava, system=system)
    soubor.write_text(json.dumps({"ts": time.time(), "odpoved": odpoved}))
    return odpoved

def chat_s_retry(zprava: str, max_pokusy: int = 3) -> str:
    """Retry s exponential backoff pro rate limits."""
    for pokus in range(max_pokusy):
        try:
            return chat(zprava)
        except Exception as e:
            if "rate_limit" in str(e).lower() and pokus < max_pokusy - 1:
                zpozdeni = 2 ** pokus
                print(f"  Rate limit – čekám {zpozdeni}s...")
                time.sleep(zpozdeni)
            else:
                raise
    raise RuntimeError("Všechny pokusy selhaly")

# Demo
o1 = chat_s_cache("Co je Python?")
o2 = chat_s_cache("Co je Python?")   # z cache
print(f"  Odpověď: {o1[:60]}...")

import shutil
shutil.rmtree(CACHE_DIR, ignore_errors=True)


# ══════════════════════════════════════════════════════════════
# ČÁST 5: Tool Use (Function Calling)
# ══════════════════════════════════════════════════════════════

print("\n=== Tool Use (Function Calling) ===\n")
print("  Model může volat tvoje Python funkce!\n")

# Definice nástrojů
def ziskej_pocasi(mesto: str) -> dict:
    """Simuluje počasí API."""
    return {"mesto": mesto, "teplota": 22, "popis": "slunečno"}

def vypocti(vyrazu: str) -> float:
    """Bezpečně vyhodnotí matematický výraz."""
    povolene = set("0123456789+-*/()., ")
    if all(c in povolene for c in vyrazu):
        return eval(vyrazu)
    raise ValueError("Nepovolen výraz")

NASTROJE = {
    "ziskej_pocasi": {
        "popis": "Vrátí počasí pro zadané město",
        "parametry": {"mesto": "string"},
        "funkce": ziskej_pocasi,
    },
    "vypocti": {
        "popis": "Vypočítá matematický výraz",
        "parametry": {"vyrazu": "string"},
        "funkce": vypocti,
    },
}

def agent_s_nastroji(dotaz: str) -> str:
    """Jednoduchý agent který může volat nástroje."""
    # Prompt instrukuje model k volání nástrojů přes JSON
    system = f"""Jsi asistent s přístupem k nástrojům.
Pokud potřebuješ nástroj, odpověz JSON: {{"nastroj": "jmeno", "parametry": {{...}}}}
Dostupné nástroje: {list(NASTROJE.keys())}"""

    odpoved = chat(dotaz, system=system)

    # Zkontroluj jestli model chce volat nástroj
    data = extrahuj_json(odpoved)
    if "nastroj" in data:
        nastroj = NASTROJE.get(data["nastroj"])
        if nastroj:
            vysledek = nastroj["funkce"](**data.get("parametry", {}))
            print(f"  [agent] Volám nástroj: {data['nastroj']}({data.get('parametry',{})})")
            print(f"  [agent] Výsledek: {vysledek}")
            # Zavolej model znovu s výsledkem nástroje
            return chat(f"Výsledek nástroje: {vysledek}. Teď odpověz na: {dotaz}")

    return odpoved

print("  Dotaz: Jaké je počasí v Praze?")
odpoved = agent_s_nastroji("Jaké je počasí v Praze?")
print(f"  Odpověď: {odpoved[:100]}")


# ══════════════════════════════════════════════════════════════
# ČÁST 6: Přehled modelů a ceny
# ══════════════════════════════════════════════════════════════

print("""
=== Modely a kdy co použít ===

  Claude (Anthropic):
    claude-opus-4-5      → nejchytřejší, komplexní úkoly, dražší
    claude-sonnet-4-5    → rovnováha výkon/cena, doporučený
    claude-haiku-4-5     → rychlý a levný, jednoduché úkoly

  GPT (OpenAI):
    gpt-4o               → nejchytřejší, vize, dražší
    gpt-4o-mini          → levný, rychlý, většina úkolů
    o1-mini              → reasoning, matematika, kód

  Volně dostupné (self-hosted):
    Llama 3.1 (Meta)     → via Ollama
    Mistral              → via Ollama nebo API
    Gemma 2 (Google)     → via Ollama

  Doporučení:
    Prototyp/vývoj  → claude-haiku nebo gpt-4o-mini (levné)
    Produkce        → claude-sonnet nebo gpt-4o
    Privacy/offline → Ollama s Llama 3.1
""")

# TVOJE ÚLOHA:
# 1. Nastav ANTHROPIC_API_KEY a spusť skutečné volání API.
# 2. Napiš funkci summarize(text, max_vety=3) která shrne libovolný text.
# 3. Vytvoř chatbota s pamětí – ukládej historii do SQLite (lekce 40).
# 4. Přidej streaming výstup – model odpovídá token po tokenu.
