"""Reseni – Lekce 68: Security – bezpecnost Python aplikaci"""

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


# 1. TOTP (Time-based OTP) pro 2FA

print("=== Ukol 1: TOTP – Time-based OTP ===\n")

try:
    import pyotp   # pip install pyotp
    PYOTP_OK = True
except ImportError:
    PYOTP_OK = False

if PYOTP_OK:
    # Generovani tajneho klice pro uzivatele
    tajny_klic = pyotp.random_base32()
    print(f"  Tajny klic (sdilen pri registraci): {tajny_klic}")

    totp = pyotp.TOTP(tajny_klic)
    kod = totp.now()
    print(f"  Aktualni TOTP kod:  {kod}")
    print(f"  Overeni:            {totp.verify(kod)}")
    print(f"  Overeni spatny kod: {totp.verify('000000')}")

    # Provisioning URI pro QR kod
    uri = totp.provisioning_uri(name="student@example.com", issuer_name="PythonKurz")
    print(f"  QR URI: {uri[:80]}...")

else:
    print("  pyotp neni nainstalovan: pip install pyotp")
    print("  Ukazuji manual TOTP implementaci:\n")

    import struct
    import hmac as hmac_mod
    import hashlib
    import time

    def hotp(klic: bytes, counter: int) -> int:
        """HMAC-based One-Time Password (RFC 4226)."""
        msg = struct.pack(">Q", counter)
        h   = hmac_mod.new(klic, msg, hashlib.sha1).digest()
        offset = h[-1] & 0x0F
        code   = struct.unpack(">I", h[offset:offset+4])[0] & 0x7FFFFFFF
        return code % 10**6

    def totp_manual(klic_b32: str) -> str:
        """TOTP = HOTP s counter = current_time // 30."""
        import base64
        klic = base64.b32decode(klic_b32.upper())
        counter = int(time.time()) // 30
        kod = hotp(klic, counter)
        return f"{kod:06d}"

    # Generovani klice (v base32)
    tajny = base64.b32encode(secrets.token_bytes(20)).decode()
    print(f"  Tajny klic: {tajny}")
    kod = totp_manual(tajny)
    print(f"  TOTP kod:   {kod}")
    print(f"  (Platny 30 sekund)")


# 2. Middleware pro security headers (FastAPI)

print("\n=== Ukol 2: Security headers middleware (FastAPI) ===\n")

# vyžaduje: pip install fastapi

try:
    from fastapi import FastAPI, Request
    from fastapi.responses import Response
    from fastapi.testclient import TestClient

    SECURITY_HEADERS = {
        "X-Content-Type-Options":    "nosniff",
        "X-Frame-Options":           "SAMEORIGIN",
        "X-XSS-Protection":          "1; mode=block",
        "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
        "Content-Security-Policy":   "default-src 'self'; script-src 'self'",
        "Referrer-Policy":           "strict-origin-when-cross-origin",
        "Permissions-Policy":        "camera=(), microphone=(), geolocation=()",
    }

    app = FastAPI()

    @app.middleware("http")
    async def security_headers_middleware(request: Request, call_next):
        """Pridat security headers ke vsem odpovedi."""
        response = await call_next(request)
        for header, hodnota in SECURITY_HEADERS.items():
            response.headers[header] = hodnota
        return response

    @app.get("/")
    def index():
        return {"zprava": "Bezpecna aplikace"}

    with TestClient(app) as client:
        resp = client.get("/")
        print("  Security headers v odpovedi:")
        for header in SECURITY_HEADERS:
            val = resp.headers.get(header, "CHYBI!")
            stav = "OK" if val != "CHYBI!" else "X CHYBI"
            print(f"    [{stav}] {header}: {val[:50]}")

except ImportError:
    print("  FastAPI neni nainstalovan: pip install fastapi httpx")

    # Manualni demonstrace security headers
    SECURITY_HEADERS = {
        "X-Content-Type-Options":    "nosniff",
        "X-Frame-Options":           "SAMEORIGIN",
        "X-XSS-Protection":          "1; mode=block",
        "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
        "Content-Security-Policy":   "default-src 'self'",
        "Referrer-Policy":           "strict-origin-when-cross-origin",
    }
    print("  Security headers (bez spusteni):")
    for k, v in SECURITY_HEADERS.items():
        print(f"    {k}: {v}")


# 3. Brute-force ochrana: po 5 neuspesnych loginech zablokuj IP na 15 min

print("\n=== Ukol 3: Brute-force ochrana ===\n")


class BruteForceOchrana:
    """Po MAX_POKUSU neuspesnych loginech zablokuje IP na BLOK_CASEM sekund."""

    MAX_POKUSU:  int   = 5
    BLOK_CAS_S:  float = 15 * 60   # 15 minut (zkraceno na 0.5s pro demo)

    def __init__(self, blok_cas: float | None = None):
        self._pokusy:   dict[str, int]   = {}
        self._blok:     dict[str, float] = {}
        self._blok_cas = blok_cas or self.BLOK_CAS_S

    def je_blokovana(self, ip: str) -> bool:
        """Zkontroluje jestli je IP stale blokovana."""
        if ip in self._blok:
            if time.time() < self._blok[ip]:
                return True
            else:
                # Blokace expirovala – reset
                del self._blok[ip]
                self._pokusy.pop(ip, None)
        return False

    def zaznamenej_neuspech(self, ip: str) -> dict:
        """Zaznamena neuspesny pokus a potencialne zablokuje IP."""
        if self.je_blokovana(ip):
            return {"blokovana": True, "zbyvajici_s": self._blok[ip] - time.time()}

        self._pokusy[ip] = self._pokusy.get(ip, 0) + 1
        pokusy = self._pokusy[ip]

        if pokusy >= self.MAX_POKUSU:
            self._blok[ip] = time.time() + self._blok_cas
            self._pokusy.pop(ip, None)
            return {
                "blokovana":   True,
                "zbyvajici_s": self._blok_cas,
                "zprava":      f"IP {ip} zablokovana po {self.MAX_POKUSU} pokusech na {self._blok_cas:.0f}s",
            }

        return {
            "blokovana":    False,
            "pokusy":       pokusy,
            "zbyvajici":    self.MAX_POKUSU - pokusy,
        }

    def zaznamenej_uspech(self, ip: str) -> None:
        """Uspesny login – reset pocitadla."""
        self._pokusy.pop(ip, None)
        self._blok.pop(ip, None)

    def reset(self, ip: str) -> None:
        """Manualni odblokovani (admin)."""
        self._pokusy.pop(ip, None)
        self._blok.pop(ip, None)


def falovy_login(uzivatel: str, heslo: str) -> bool:
    """Demo: spravne heslo je 'tajne123'."""
    return heslo == "tajne123"


ochrana = BruteForceOchrana(blok_cas=0.5)   # 0.5s pro demo

ip_utocnik = "192.168.1.100"
ip_normalni = "10.0.0.1"

# Utocnik zkusi 7x spatne heslo
print(f"Simulace brute-force z {ip_utocnik}:")
for i in range(7):
    if ochrana.je_blokovana(ip_utocnik):
        vysl = ochrana.zaznamenej_neuspech(ip_utocnik)
        print(f"  Pokus {i+1}: BLOKOVANA ({vysl.get('zprava','')[:60]})")
        break
    ok = falovy_login("misa", f"spatne{i}")
    if not ok:
        info = ochrana.zaznamenej_neuspech(ip_utocnik)
        if info.get("blokovana"):
            stav = "BLOKOVANA!"
        else:
            stav = f"zbyvajici pokusy: {info.get('zbyvajici', 0)}"
        print(f"  Pokus {i+1}: Login selhal – {stav}")

# Normalni uzivatel
print(f"\nNormalni uzivatel z {ip_normalni}:")
ok = falovy_login("bara", "tajne123")
ochrana.zaznamenej_uspech(ip_normalni)
print(f"  Login OK: {ok}")
print(f"  Blokovana: {ochrana.je_blokovana(ip_normalni)}")

# Cekej az uplyne blokace
print(f"\nCekam na expiraci blokace ({ochrana._blok_cas}s)...")
time.sleep(ochrana._blok_cas + 0.1)
print(f"  IP {ip_utocnik} blokovana: {ochrana.je_blokovana(ip_utocnik)}")
