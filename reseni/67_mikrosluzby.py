"""Reseni – Lekce 67: Mikrosluzby"""

import time
import random
import threading
from dataclasses import dataclass, field
from typing import Callable, Any
from enum import Enum
from collections import deque
from datetime import datetime


# CircuitBreaker ze zdrojove lekce

class CircuitState(Enum):
    CLOSED   = "CLOSED"
    OPEN     = "OPEN"
    HALF_OPEN = "HALF_OPEN"


@dataclass
class CircuitBreaker:
    nazev:          str
    threshold:      int   = 3
    timeout:        float = 2.0
    _stav:          CircuitState = field(default=CircuitState.CLOSED, init=False)
    _chyby:         int          = field(default=0, init=False)
    _posledni_chyba: float       = field(default=0.0, init=False)
    _celkem_volani: int          = field(default=0, init=False)
    _celkem_chyb:   int          = field(default=0, init=False)
    _latence:       list[float]  = field(default_factory=list, init=False)

    def volej(self, fn: Callable, *args, **kwargs) -> Any:
        t0 = time.perf_counter()
        if self._stav == CircuitState.OPEN:
            if time.time() - self._posledni_chyba > self.timeout:
                self._stav = CircuitState.HALF_OPEN
            else:
                raise RuntimeError(f"CircuitBreaker {self.nazev} je OPEN")

        try:
            self._celkem_volani += 1
            vysledek = fn(*args, **kwargs)
            elapsed = (time.perf_counter() - t0) * 1000
            self._latence.append(elapsed)
            if self._stav == CircuitState.HALF_OPEN:
                self._stav  = CircuitState.CLOSED
                self._chyby = 0
            return vysledek
        except Exception as e:
            self._chyby += 1
            self._celkem_chyb += 1
            self._posledni_chyba = time.time()
            if self._chyby >= self.threshold:
                self._stav = CircuitState.OPEN
            raise


# Ukol 1: Metriky (pocet volani, % selhani, prumerna latence)

print("=== Ukol 1: CircuitBreaker s metrikami ===\n")


class CircuitBreakerSMetrikami(CircuitBreaker):
    """Rozsireni CircuitBreakeru o podrobne metriky."""

    def metriky(self) -> dict:
        """Vrati aktualni metriky."""
        pct_chyb = (
            (self._celkem_chyb / self._celkem_volani * 100)
            if self._celkem_volani > 0 else 0.0
        )
        avg_latence = (
            sum(self._latence) / len(self._latence)
            if self._latence else 0.0
        )
        return {
            "nazev":        self.nazev,
            "stav":         self._stav.value,
            "celkem_volani": self._celkem_volani,
            "celkem_chyb":  self._celkem_chyb,
            "pct_chyb":     round(pct_chyb, 1),
            "avg_latence_ms": round(avg_latence, 2),
            "p99_latence_ms": round(
                sorted(self._latence)[int(len(self._latence) * 0.99)]
                if len(self._latence) > 1 else 0.0, 2
            ),
        }

    def tiskni_metriky(self) -> None:
        m = self.metriky()
        print(f"  [{m['nazev']}] stav={m['stav']} "
              f"volani={m['celkem_volani']} "
              f"chyby={m['celkem_chyb']} ({m['pct_chyb']}%) "
              f"avg={m['avg_latence_ms']}ms")


def nestabilni_api(chyba_pct: int = 30):
    """Simulace nestabilniho API."""
    time.sleep(random.uniform(0.005, 0.02))
    if random.randint(1, 100) <= chyba_pct:
        raise ConnectionError("API timeout")
    return {"stav": "ok"}


cb = CircuitBreakerSMetrikami("platebni-api", threshold=4)

print("  Testuji 20 volani (30% chybovost):")
uspech = 0
for i in range(20):
    try:
        cb.volej(nestabilni_api, chyba_pct=30)
        uspech += 1
    except (ConnectionError, RuntimeError) as e:
        pass

cb.tiskni_metriky()


# Ukol 2: Service Registry

print("\n=== Ukol 2: Service Registry ===\n")


@dataclass
class ServiceInstance:
    service: str
    host:    str
    port:    int
    zdravy:  bool = True
    _posledni_ping: float = field(default_factory=time.time, init=False)

    @property
    def adresa(self) -> str:
        return f"{self.host}:{self.port}"

    def healthcheck(self) -> bool:
        """Simulace health checku."""
        self._posledni_ping = time.time()
        # Simulace: 10% sance ze service padne
        self.zdravy = random.random() > 0.1
        return self.zdravy


class ServiceRegistry:
    """Centralni registr sluzeb – sluzby se registruji a API Gateway je vyhledava."""

    def __init__(self):
        self._registry: dict[str, list[ServiceInstance]] = {}
        self._lock = threading.Lock()

    def zaregistruj(self, instance: ServiceInstance) -> None:
        with self._lock:
            self._registry.setdefault(instance.service, []).append(instance)
        print(f"  [Registry] Zaregistrovan {instance.service} na {instance.adresa}")

    def odregistruj(self, service: str, host: str, port: int) -> None:
        with self._lock:
            sluzby = self._registry.get(service, [])
            self._registry[service] = [
                s for s in sluzby
                if not (s.host == host and s.port == port)
            ]
        print(f"  [Registry] Odregistrovan {service} {host}:{port}")

    def ziskej_zdravou(self, service: str) -> ServiceInstance | None:
        """Vrati jednu zdravou instanci sluzby (round-robin)."""
        with self._lock:
            instance_all = self._registry.get(service, [])
            zdrave = [s for s in instance_all if s.zdravy]
            if not zdrave:
                return None
            # Jednoduchy round-robin pomoci rotace
            selected = zdrave[0]
            self._registry[service] = zdrave[1:] + [selected] + [
                s for s in instance_all if not s.zdravy
            ]
            return selected

    def vsechny_instance(self, service: str) -> list[ServiceInstance]:
        return self._registry.get(service, [])

    def health_check_vsech(self) -> None:
        """Otestuje zdravi vsech instanci."""
        with self._lock:
            for service, instance_list in self._registry.items():
                for inst in instance_list:
                    inst.healthcheck()


registry = ServiceRegistry()

# Zaregistruj sluzby
for i in range(3):
    registry.zaregistruj(ServiceInstance("uzivatelska-sluzba", "host-A", 8000 + i))
for i in range(2):
    registry.zaregistruj(ServiceInstance("platebni-sluzba", "host-B", 9000 + i))

print("\n  Vyhledani sluzby (round-robin):")
for _ in range(4):
    inst = registry.ziskej_zdravou("uzivatelska-sluzba")
    print(f"    → {inst.adresa if inst else 'zadna dostupna'}")

registry.health_check_vsech()
print("\n  Stav po health checku:")
for service in ["uzivatelska-sluzba", "platebni-sluzba"]:
    zdravych = sum(1 for s in registry.vsechny_instance(service) if s.zdravy)
    celkem   = len(registry.vsechny_instance(service))
    print(f"    {service}: {zdravych}/{celkem} zdravych")


# Ukol 3: Saga s retry + exponential backoff pred kompenzaci

print("\n=== Ukol 3: Saga s retry a exponential backoff ===\n")


@dataclass
class SagaKrok:
    nazev:      str
    akce:       Callable
    kompenzace: Callable
    max_retries: int = 2
    base_delay:  float = 0.05


@dataclass
class SagaRetry:
    nazev: str
    kroky: list[SagaKrok] = field(default_factory=list)
    _hotove: list[SagaKrok] = field(default_factory=list)

    def pridej(self, krok: SagaKrok) -> "SagaRetry":
        self.kroky.append(krok)
        return self

    def _zkus_s_backoff(self, krok: SagaKrok, kontext: dict) -> bool:
        """Zkusi akci s exponential backoff pred kompenzaci."""
        for pokus in range(krok.max_retries + 1):
            try:
                krok.akce(kontext)
                return True
            except Exception as e:
                if pokus < krok.max_retries:
                    zpozdeni = krok.base_delay * (2 ** pokus)
                    print(f"    [Retry {pokus+1}/{krok.max_retries}] {krok.nazev}: {e} → backoff {zpozdeni:.3f}s")
                    time.sleep(zpozdeni)
                else:
                    print(f"    [Selhalo po {krok.max_retries+1} pokusech] {krok.nazev}: {e}")
                    return False
        return False

    def spust(self, kontext: dict) -> bool:
        print(f"  Saga [{self.nazev}] START")
        for krok in self.kroky:
            if self._zkus_s_backoff(krok, kontext):
                self._hotove.append(krok)
                print(f"    V {krok.nazev}")
            else:
                self._kompenzuj(kontext)
                return False
        print(f"  Saga [{self.nazev}] COMMIT")
        return True

    def _kompenzuj(self, kontext: dict) -> None:
        for krok in reversed(self._hotove):
            try:
                krok.kompenzace(kontext)
                print(f"    ↩ {krok.nazev} (kompenzace)")
            except Exception as e:
                print(f"    X Kompenzace {krok.nazev} selhala: {e}")
        print(f"  Saga [{self.nazev}] ROLLBACK")


platba_pokusy = {"n": 0}

def objednavka_akce(k: dict):
    k["objednavka_id"] = 42

def platba_akce_nestabilni(k: dict):
    """Prvni 2 pokusy selzou, treti uspeje."""
    platba_pokusy["n"] += 1
    if platba_pokusy["n"] <= 2:
        raise ConnectionError("Platebni brana timeout")
    k["platba_ok"] = True

def doprava_akce(k: dict):
    k["doprava_ok"] = True

saga = SagaRetry("nakup-retry")
saga.pridej(SagaKrok("vytvor-objednavku", objednavka_akce, lambda k: k.pop("objednavka_id", None)))
saga.pridej(SagaKrok("zpracuj-platbu", platba_akce_nestabilni,
                     lambda k: k.update({"platba_storno": True}),
                     max_retries=3, base_delay=0.02))
saga.pridej(SagaKrok("rezervuj-dopravu", doprava_akce, lambda k: None))

kontext: dict = {}
ok = saga.spust(kontext)
print(f"\n  Vysledek: {'uspech' if ok else 'selhani'}")
print(f"  Kontext: {kontext}")
