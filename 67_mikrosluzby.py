"""
LEKCE 67: Mikroslužby – patterns a architektura
=================================================
Mikroslužby = aplikace rozdělená na malé nezávislé služby.
Každá má vlastní proces, databázi, deployment.

Monolith vs Mikroslužby:
  Monolith     → vše v jednom procesu, jednoduché, ale těžko škálovatelné
  Mikroslužby  → nezávislé služby, složitější, ale škálovatelné

Klíčové patterns:
  API Gateway        – jediný vstupní bod
  Circuit Breaker    – ochrana před kaskádovými selháními
  Service Discovery  – jak služby najdou ostatní
  Saga               – distribuované transakce
  Event Sourcing     – stav = log událostí
  CQRS               – oddělené čtení a zápis
"""

import time
import random
import threading
import json
from dataclasses import dataclass, field
from typing import Callable, Any
from enum import Enum
from collections import deque, defaultdict
from datetime import datetime, timedelta

# ══════════════════════════════════════════════════════════════
# ČÁST 1: Circuit Breaker
# ══════════════════════════════════════════════════════════════

print("=== Circuit Breaker ===\n")
print("Chrání systém před kaskádovými selháními.")
print("Stavy: CLOSED (normál) → OPEN (blokuje) → HALF_OPEN (zkouší)\n")

class CircuitState(Enum):
    CLOSED    = "CLOSED"     # normální provoz
    OPEN      = "OPEN"       # blokuje volání
    HALF_OPEN = "HALF_OPEN"  # zkouší jestli se služba zotavila

@dataclass
class CircuitBreaker:
    nazev:           str
    selhani_limit:   int   = 5
    timeout_s:       float = 10.0
    uspech_limit:    int   = 2   # kolik úspěchů v HALF_OPEN → CLOSED

    _stav:           CircuitState = field(default=CircuitState.CLOSED, init=False)
    _selhani:        int = field(default=0, init=False)
    _uspechy:        int = field(default=0, init=False)
    _posledni_selh:  float = field(default=0.0, init=False)

    def __call__(self, fn: Callable) -> Callable:
        def wrapper(*args, **kwargs):
            return self.zavolej(fn, *args, **kwargs)
        wrapper.__name__ = fn.__name__
        return wrapper

    def zavolej(self, fn: Callable, *args, **kwargs) -> Any:
        if self._stav == CircuitState.OPEN:
            if time.time() - self._posledni_selh > self.timeout_s:
                self._stav = CircuitState.HALF_OPEN
                print(f"  [{self.nazev}] → HALF_OPEN (zkouším...)")
            else:
                raise RuntimeError(f"Circuit OPEN: {self.nazev} nedostupný")

        try:
            result = fn(*args, **kwargs)
            self._on_uspech()
            return result
        except Exception as e:
            self._on_selhani()
            raise

    def _on_uspech(self):
        if self._stav == CircuitState.HALF_OPEN:
            self._uspechy += 1
            if self._uspechy >= self.uspech_limit:
                self._stav    = CircuitState.CLOSED
                self._selhani = 0
                self._uspechy = 0
                print(f"  [{self.nazev}] → CLOSED (zotaven!)")
        else:
            self._selhani = max(0, self._selhani - 1)

    def _on_selhani(self):
        self._selhani      += 1
        self._posledni_selh = time.time()
        if self._selhani >= self.selhani_limit:
            self._stav = CircuitState.OPEN
            print(f"  [{self.nazev}] → OPEN (příliš mnoho selhání!)")

    @property
    def stav(self) -> str:
        return self._stav.value

# Demo
cb = CircuitBreaker("platebni-sluzba", selhani_limit=3, timeout_s=0.5)
platebni_chyba = True   # simuluj vadnou službu

def platba(castka: float) -> dict:
    if platebni_chyba:
        raise ConnectionError("Platební brána nedostupná")
    return {"status": "OK", "castka": castka}

print("Série volání (služba selhává):")
for i in range(7):
    try:
        result = cb.zavolej(platba, 100 * (i+1))
        print(f"  Volání {i+1}: OK → {result}")
    except Exception as e:
        print(f"  Volání {i+1}: ✗ {e}")

# Zotavení
platebni_chyba = False
time.sleep(0.6)
print("\nPo zotavení:")
for i in range(4):
    try:
        result = cb.zavolej(platba, 500)
        print(f"  Volání {i+1}: OK  [stav={cb.stav}]")
    except Exception as e:
        print(f"  Volání {i+1}: ✗ {e}  [stav={cb.stav}]")


# ══════════════════════════════════════════════════════════════
# ČÁST 2: API Gateway
# ══════════════════════════════════════════════════════════════

print("\n=== API Gateway ===\n")
print("Jediný vstupní bod. Routing, auth, rate limiting, logging.\n")

@dataclass
class Request:
    metoda: str
    cesta:  str
    headers: dict = field(default_factory=dict)
    body:    dict = field(default_factory=dict)
    user_id: int | None = None

@dataclass
class Response:
    status: int
    body:   Any

class Middleware:
    def __init__(self, nazev: str):
        self.nazev = nazev

    def __call__(self, req: Request, dalsi: Callable) -> Response:
        return dalsi(req)

class AuthMiddleware(Middleware):
    TOKENY = {"bearer-123": 1, "bearer-456": 2}

    def __call__(self, req: Request, dalsi: Callable) -> Response:
        token = req.headers.get("Authorization", "")
        user_id = self.TOKENY.get(token)
        if not user_id:
            return Response(401, {"chyba": "Neautorizováno"})
        req.user_id = user_id
        print(f"    [Auth] user_id={user_id}")
        return dalsi(req)

class RateLimitMiddleware(Middleware):
    def __init__(self, limit: int = 5, okno: int = 10):
        super().__init__("RateLimit")
        self.limit = limit
        self._pocitadla: dict[int, list] = defaultdict(list)

    def __call__(self, req: Request, dalsi: Callable) -> Response:
        ted = time.time()
        klic = req.user_id or "anon"
        # Smaž staré záznamy
        self._pocitadla[klic] = [t for t in self._pocitadla[klic]
                                   if ted - t < 10]
        if len(self._pocitadla[klic]) >= self.limit:
            return Response(429, {"chyba": "Příliš mnoho požadavků"})
        self._pocitadla[klic].append(ted)
        return dalsi(req)

class LogMiddleware(Middleware):
    def __call__(self, req: Request, dalsi: Callable) -> Response:
        t0 = time.perf_counter()
        resp = dalsi(req)
        ms = (time.perf_counter() - t0) * 1000
        print(f"    [Log] {req.metoda} {req.cesta} → {resp.status} ({ms:.1f}ms)")
        return resp

class ApiGateway:
    def __init__(self):
        self._routes:  dict[str, dict[str, Callable]] = defaultdict(dict)
        self._middlewares: list[Middleware] = []

    def use(self, middleware: Middleware):
        self._middlewares.append(middleware)

    def route(self, metoda: str, cesta: str):
        def dec(fn):
            self._routes[metoda][cesta] = fn
            return fn
        return dec

    def handle(self, req: Request) -> Response:
        handler = self._routes.get(req.metoda, {}).get(req.cesta)
        if not handler:
            return Response(404, {"chyba": f"{req.cesta} nenalezena"})

        # Middleware chain
        def build_chain(idx: int) -> Callable:
            if idx >= len(self._middlewares):
                return handler
            mw = self._middlewares[idx]
            dalsi = build_chain(idx + 1)
            return lambda r: mw(r, dalsi)

        return build_chain(0)(req)

# Mikroslužby (simulace)
def student_service(student_id: int) -> dict:
    time.sleep(0.01)
    return {"id": student_id, "jmeno": "Míša", "vek": 15}

def platba_service(user_id: int, castka: float) -> dict:
    time.sleep(0.02)
    return {"user_id": user_id, "castka": castka, "stav": "OK"}

# Gateway setup
gw = ApiGateway()
gw.use(LogMiddleware("Log"))
gw.use(AuthMiddleware("Auth"))
gw.use(RateLimitMiddleware(limit=3))

@gw.route("GET", "/studenti/1")
def get_student(req: Request) -> Response:
    data = student_service(1)
    return Response(200, data)

@gw.route("POST", "/platby")
def vytvor_platbu(req: Request) -> Response:
    data = platba_service(req.user_id, req.body.get("castka", 0))
    return Response(201, data)

# Testování
print("Testování API Gateway:")
pozadavky = [
    Request("GET",  "/studenti/1", {"Authorization": "bearer-123"}),
    Request("POST", "/platby",     {"Authorization": "bearer-456"}, {"castka": 999}),
    Request("GET",  "/studenti/1", {}),    # bez auth
    Request("GET",  "/neexistuje", {"Authorization": "bearer-123"}),
]

for req in pozadavky:
    print(f"\n  {req.metoda} {req.cesta}:")
    resp = gw.handle(req)
    print(f"    → {resp.status}: {resp.body}")


# ══════════════════════════════════════════════════════════════
# ČÁST 3: Saga pattern – distribuovaná transakce
# ══════════════════════════════════════════════════════════════

print("\n=== Saga pattern ===\n")
print("Distribuovaná transakce přes více mikroslužeb.")
print("Každý krok má kompenzační akci (rollback).\n")

@dataclass
class SagaKrok:
    nazev:      str
    akce:       Callable
    kompenzace: Callable

class Saga:
    def __init__(self, nazev: str):
        self.nazev  = nazev
        self.kroky:  list[SagaKrok] = []
        self._hotove: list[SagaKrok] = []

    def pridej(self, krok: SagaKrok) -> "Saga":
        self.kroky.append(krok)
        return self

    def spust(self, kontext: dict) -> bool:
        print(f"  Saga [{self.nazev}] START")
        for krok in self.kroky:
            try:
                krok.akce(kontext)
                self._hotove.append(krok)
                print(f"    ✓ {krok.nazev}")
            except Exception as e:
                print(f"    ✗ {krok.nazev}: {e} → kompenzace")
                self._kompenzuj(kontext)
                return False
        print(f"  Saga [{self.nazev}] COMMIT")
        return True

    def _kompenzuj(self, kontext: dict):
        for krok in reversed(self._hotove):
            try:
                krok.kompenzace(kontext)
                print(f"    ↩ {krok.nazev} (kompenzace)")
            except Exception as e:
                print(f"    ✗ Kompenzace {krok.nazev} selhala: {e}")
        print(f"  Saga [{self.nazev}] ROLLBACK")

# Objednávka e-shopu
def overit_zasoby(k: dict):
    if k.get("produkt") == "VYPRODANO":
        raise ValueError("Produkt není skladem")
    k["zasoby_rezervovany"] = True

def zpracovat_platbu(k: dict):
    if random.random() < 0.3:    # 30% šance selhání platby
        raise ConnectionError("Platební brána nedostupná")
    k["platba_zpracovana"] = True

def odeslat_zasilku(k: dict):
    k["zasilka_odeslana"] = True

saga_objednavka = Saga("vytvoreni-objednavky")
saga_objednavka.pridej(SagaKrok(
    "Rezervuj zásoby", overit_zasoby,
    lambda k: k.pop("zasoby_rezervovany", None)
))
saga_objednavka.pridej(SagaKrok(
    "Zpracuj platbu", zpracovat_platbu,
    lambda k: k.update({"platba_stornovana": True})
))
saga_objednavka.pridej(SagaKrok(
    "Odešli zásilku", odeslat_zasilku,
    lambda k: k.update({"zasilka_zrusena": True})
))

# Zkus 3× (platba může selhat)
for pokus in range(3):
    print(f"\nPokus {pokus+1}:")
    kontext = {"produkt": "Python kurz", "cena": 999}
    uspech = saga_objednavka.spust(kontext)
    saga_objednavka._hotove.clear()  # reset pro další pokus
    if uspech:
        print(f"  Výsledek: {kontext}")
        break


print("""
=== Kdy mikroslužby ===

  Mikroslužby JSOU správné když:
    ✓ Různé části potřebují různé technologie
    ✓ Různé části škálují různě (platby × notifikace)
    ✓ Velký tým – každý vlastní svoji službu
    ✓ Různé deployment cykly

  Mikroslužby NEJSOU správné když:
    ✗ Malý tým (< 5 lidí)
    ✗ Nová aplikace (začni monolitem!)
    ✗ Těsně provázaná doménová logika
    ✗ Nemáš DevOps kapacitu

  "Monolith first, microservices later" – Martin Fowler
""")

# TVOJE ÚLOHA:
# 1. Přidej do CircuitBreaker metriky (počet volání, % selhání, průměrná latence).
# 2. Implementuj Service Registry – služby se registrují a Gateway je hledá.
# 3. Přidej do Saga pattern retry s exponential backoff před kompenzací.
