"""Řešení – Lekce 74: LLM API – Claude a OpenAI z Pythonu"""

# vyžaduje: pip install anthropic openai

import os
import json
import hashlib
import time
from pathlib import Path

ANTHROPIC_KEY = os.getenv("ANTHROPIC_API_KEY", "")
OPENAI_KEY    = os.getenv("OPENAI_API_KEY", "")

# 1. Funkce sumarizuj(text) – shrne libovolný text na 3 věty
print("=== 1. Funkce sumarizuj(text) ===\n")

def sumarizuj(text: str) -> str:
    """Shrne libovolný text na 3 věty pomocí Claude nebo OpenAI."""
    if ANTHROPIC_KEY:
        import anthropic
        client = anthropic.Anthropic()
        zprava = client.messages.create(
            model="claude-opus-4-7",
            max_tokens=256,
            system="Jsi asistent pro sumarizaci. Shrň zadaný text přesně na 3 věty česky. Nic víc, nic míň.",
            messages=[{"role": "user", "content": f"Shrň tento text na 3 věty:\n\n{text}"}],
        )
        return zprava.content[0].text

    elif OPENAI_KEY:
        from openai import OpenAI
        client = OpenAI()
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            max_tokens=256,
            messages=[
                {"role": "system", "content": "Shrň zadaný text přesně na 3 věty česky."},
                {"role": "user",   "content": f"Shrň tento text na 3 věty:\n\n{text}"},
            ],
        )
        return resp.choices[0].message.content

    else:
        # Simulace bez API klíče
        vety = [v.strip() for v in text.replace("\n", " ").split(".") if v.strip()]
        vety = [v + "." for v in vety if len(v) > 20][:3]
        return " ".join(vety) or "[Nastav ANTHROPIC_API_KEY nebo OPENAI_API_KEY]"

TESTOVACI_TEXT = """
Python je interpretovaný programovací jazyk vysoké úrovně, který klade důraz
na čitelnost kódu. Byl navržen Guidem van Rossumem a poprvé vydán v roce 1991.
Python se dnes používá v datové vědě, strojovém učení, webovém vývoji,
automatizaci a mnoha dalších oblastech. Má obrovskou komunitu a rozsáhlou
sbírku knihoven na PyPI. Velcí hráči jako Google, Netflix nebo NASA Python
aktivně využívají.
"""

print(f"Vstup: {TESTOVACI_TEXT[:80].strip()}...\n")
print(f"Sumarizace: {sumarizuj(TESTOVACI_TEXT)}")


# 2. Chatbot s pamětí – ukládá historii do SQLite
print("\n=== 2. Chatbot s pamětí (SQLite) ===\n")

import sqlite3
from datetime import datetime

class ChatbotSPameti:
    """Chatbot který si pamatuje historii konverzace v SQLite."""

    def __init__(self, db_cesta: str = ":memory:", session_id: str = "demo"):
        self.db_cesta   = db_cesta
        self.session_id = session_id
        self.conn       = sqlite3.connect(db_cesta)
        self._inicializuj_db()

    def _inicializuj_db(self):
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS zpravy (
                id       INTEGER PRIMARY KEY AUTOINCREMENT,
                session  TEXT NOT NULL,
                role     TEXT NOT NULL,
                obsah    TEXT NOT NULL,
                cas      TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        self.conn.commit()

    def _uloz(self, role: str, obsah: str):
        self.conn.execute(
            "INSERT INTO zpravy (session, role, obsah) VALUES (?,?,?)",
            (self.session_id, role, obsah)
        )
        self.conn.commit()

    def _ziskej_historii(self) -> list[dict]:
        rows = self.conn.execute(
            "SELECT role, obsah FROM zpravy WHERE session=? ORDER BY id",
            (self.session_id,)
        ).fetchall()
        return [{"role": r, "content": o} for r, o in rows]

    def posli(self, zprava: str) -> str:
        self._uloz("user", zprava)
        historie = self._ziskej_historii()

        if ANTHROPIC_KEY:
            import anthropic
            client = anthropic.Anthropic()
            resp = client.messages.create(
                model="claude-opus-4-7",
                max_tokens=512,
                system="Jsi přátelský Python lektor. Pamatuješ si celou konverzaci.",
                messages=historie,
            )
            odpoved = resp.content[0].text
        elif OPENAI_KEY:
            from openai import OpenAI
            client = OpenAI()
            resp = client.chat.completions.create(
                model="gpt-4o-mini",
                max_tokens=512,
                messages=[
                    {"role": "system", "content": "Jsi přátelský Python lektor."},
                    *historie,
                ],
            )
            odpoved = resp.choices[0].message.content
        else:
            odpoved = f"[Simulace] Přijal jsem: '{zprava}'. Nastav API klíč pro reálné odpovědi."

        self._uloz("assistant", odpoved)
        return odpoved

    def vypis_historii(self):
        print(f"  Historie session '{self.session_id}':")
        for zprava in self._ziskej_historii():
            prefix = "  Uživatel" if zprava["role"] == "user" else "  Asistent"
            print(f"  {prefix}: {zprava['content'][:60]}...")

    def pocet_zprav(self) -> int:
        r = self.conn.execute(
            "SELECT COUNT(*) FROM zpravy WHERE session=?", (self.session_id,)
        ).fetchone()
        return r[0]


bot = ChatbotSPameti(session_id="test")
odpovedi = [
    bot.posli("Co je dekorátor v Pythonu?"),
    bot.posli("Dej mi konkrétní příklad."),
    bot.posli("Jak ho použiji v praxi?"),
]

for i, odp in enumerate(odpovedi, 1):
    print(f"  Otázka {i}: {odp[:80]}...")

print(f"\n  Celkem zpráv v paměti: {bot.pocet_zprav()}")
bot.vypis_historii()


# 3. File cache – šetří kredity při vývoji
print("\n=== 3. LLM cache (file backend) ===\n")

CACHE_DIR = Path(f"/tmp/llm_cache_demo_{os.getpid()}")
CACHE_DIR.mkdir(exist_ok=True)

def llm_s_cache(prompt: str, ttl_hod: int = 24) -> str:
    """Volá LLM s cachováním odpovědí do souborů."""
    klic   = hashlib.md5(prompt.encode()).hexdigest()
    soubor = CACHE_DIR / f"{klic}.json"

    # Zkus cache
    if soubor.exists():
        data = json.loads(soubor.read_text())
        if time.time() - data["ts"] < ttl_hod * 3600:
            print(f"  [CACHE HIT]  {prompt[:40]}")
            return data["odpoved"]

    # Volej API
    print(f"  [CACHE MISS] {prompt[:40]}")
    odpoved = sumarizuj(prompt) if len(prompt) > 50 else f"Odpověď na: {prompt}"

    # Ulož do cache
    soubor.write_text(json.dumps({"ts": time.time(), "odpoved": odpoved}))
    return odpoved

# Test cache
r1 = llm_s_cache("Vysvětli co je asyncio v Pythonu a jak funguje event loop.")
r2 = llm_s_cache("Vysvětli co je asyncio v Pythonu a jak funguje event loop.")  # HIT
r3 = llm_s_cache("Jaký je rozdíl mezi list a tuple v Pythonu?")

print(f"\n  1. volání: {r1[:60]}...")
print(f"  2. volání (cache): {r2[:60]}...")
print(f"  3. volání: {r3[:60]}...")

# Úklid
import shutil
shutil.rmtree(CACHE_DIR, ignore_errors=True)

print("\n=== Shrnutí ===")
print("  1. sumarizuj(text) – shrnutí na 3 věty")
print("  2. ChatbotSPameti   – ukládá historii do SQLite")
print("  3. llm_s_cache()    – file cache pro úsporu API kreditů")
print(f"\n  API klíče: ANTHROPIC={'nastaven' if ANTHROPIC_KEY else 'CHYBÍ'}, "
      f"OPENAI={'nastaven' if OPENAI_KEY else 'CHYBÍ'}")
