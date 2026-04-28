"""Reseni – Lekce 63: Redis"""

# Produkčni Redis vyžaduje: pip install redis
# Tato lekce simuluje Redis bez serveru

import time
import json
import threading
import heapq
from collections import defaultdict, deque, OrderedDict
from typing import Any


# Zakladni Redis simulátor (zkopirovan z originalu pro spusteni)

class RedisSim:
    def __init__(self):
        self._data:   dict[str, Any]  = {}
        self._expiry: dict[str, float] = {}
        self._lists:  dict[str, deque] = defaultdict(deque)
        self._hashes: dict[str, dict]  = defaultdict(dict)
        self._sets:   dict[str, set]   = defaultdict(set)
        self._zsets:  dict[str, dict]  = defaultdict(dict)
        self._lock = threading.Lock()

    def _je_expirovan(self, klic: str) -> bool:
        if klic in self._expiry:
            if time.time() > self._expiry[klic]:
                self.delete(klic)
                return True
        return False

    def set(self, klic: str, hodnota: Any, ex: int | None = None) -> None:
        with self._lock:
            self._data[klic] = str(hodnota)
            if ex:
                self._expiry[klic] = time.time() + ex

    def get(self, klic: str) -> str | None:
        with self._lock:
            if self._je_expirovan(klic):
                return None
            return self._data.get(klic)

    def exists(self, klic: str) -> bool:
        with self._lock:
            return not self._je_expirovan(klic) and klic in self._data

    def delete(self, *klice: str) -> int:
        n = 0
        for k in klice:
            if k in self._data:
                del self._data[k]
                n += 1
            self._expiry.pop(k, None)
        return n

    def incr(self, klic: str) -> int:
        with self._lock:
            val = int(self._data.get(klic, 0)) + 1
            self._data[klic] = str(val)
            return val

    def zadd(self, klic: str, mapping: dict) -> None:
        with self._lock:
            self._zsets[klic].update(mapping)

    def zrange(self, klic: str, start: int, stop: int, withscores: bool = False):
        with self._lock:
            serazene = sorted(self._zsets[klic].items(), key=lambda x: x[1])
            cast = serazene[start:stop+1 if stop != -1 else None]
            if withscores:
                return cast
            return [k for k, _ in cast]

    def zrevrange(self, klic: str, start: int, stop: int, withscores: bool = False):
        with self._lock:
            serazene = sorted(self._zsets[klic].items(), key=lambda x: -x[1])
            cast = serazene[start:stop+1 if stop != -1 else None]
            if withscores:
                return cast
            return [k for k, _ in cast]

    def hset(self, klic: str, field: str, value: Any) -> None:
        with self._lock:
            self._hashes[klic][field] = str(value)

    def hget(self, klic: str, field: str) -> str | None:
        with self._lock:
            return self._hashes[klic].get(field)

    def hgetall(self, klic: str) -> dict:
        with self._lock:
            return dict(self._hashes[klic])


r = RedisSim()


# 1. LRU Cache pomoci Sorted Set (cas pristupu = score)

print("=== Ukol 1: LRU Cache pomoci Sorted Set ===\n")


class RedisLRUCache:
    """LRU (Least Recently Used) cache implementovana pres Redis Sorted Set.
    - Sorted Set ukla (klic → score=cas_pristupu)
    - Hash ukla (klic → hodnota)
    - Kdyz je cache plna, smaze klic s nejnizsim score (nejstarsi pristup)
    """

    def __init__(self, redis_sim: RedisSim, nazev: str, max_velikost: int = 5):
        self.r         = redis_sim
        self.klic_hash = f"lru:data:{nazev}"
        self.klic_zset = f"lru:order:{nazev}"
        self.max_vel   = max_velikost

    def get(self, klic: str) -> Any | None:
        """Ziska hodnotu a aktualizuje cas pristupu (posune na 'novejsi' konec)."""
        hodnota = self.r.hget(self.klic_hash, klic)
        if hodnota is None:
            return None
        # Aktualizuj cas pristupu
        self.r.zadd(self.klic_zset, {klic: time.time()})
        return json.loads(hodnota)

    def set(self, klic: str, hodnota: Any) -> None:
        """Ulozi do cache. Kdyz je plna, smaže nejstarsi polozku."""
        # Zkontroluj kapacitu (pocet klicu v zset)
        cas_poradi = self.r._zsets[self.klic_zset]
        if len(cas_poradi) >= self.max_vel and klic not in cas_poradi:
            nejstarsi = min(cas_poradi, key=cas_poradi.get)
            self.r.delete(f"{self.klic_hash}:{nejstarsi}")
            self.r.hset(self.klic_hash, nejstarsi, "")
            del self.r._hashes[self.klic_hash][nejstarsi]
            del self.r._zsets[self.klic_zset][nejstarsi]

        self.r.hset(self.klic_hash, klic, json.dumps(hodnota))
        self.r.zadd(self.klic_zset, {klic: time.time()})

    def vypis(self) -> None:
        serazene = self.r.zrevrange(self.klic_zset, 0, -1)
        print(f"  Cache (nejnovejsi → nejstarsi):")
        for k in serazene:
            v = self.r.hget(self.klic_hash, k)
            print(f"    {k}: {v}")


lru = RedisLRUCache(r, "user_cache", max_velikost=3)

print("Plneni cache (max 3 polozky):")
for i in range(1, 6):
    lru.set(f"user:{i}", {"id": i, "jmeno": f"User{i}"})
    time.sleep(0.01)

lru.vypis()

print("\nPristup k user:3 (presune na zacatek):")
val = lru.get("user:3")
print(f"  Hodnota: {val}")
lru.vypis()


# 2. Session store pro FastAPI sessions

print("\n=== Ukol 2: Session store (Redis-based) ===\n")

import secrets as secrets_mod
from datetime import timedelta


class SessionStore:
    """Uklada session data v Redis (nebo simulatoru)."""

    def __init__(self, redis_sim: RedisSim, ttl_sekundy: int = 3600):
        self.r   = redis_sim
        self.ttl = ttl_sekundy

    def vytvor_session(self, data: dict) -> str:
        """Vytvori novou session a vrati session_id."""
        session_id = secrets_mod.token_urlsafe(32)
        self.r.set(f"session:{session_id}", json.dumps(data), ex=self.ttl)
        return session_id

    def nacti_session(self, session_id: str) -> dict | None:
        """Nacte session data dle ID."""
        raw = self.r.get(f"session:{session_id}")
        if raw is None:
            return None
        return json.loads(raw)

    def aktualizuj_session(self, session_id: str, data: dict) -> bool:
        """Aktualizuje session data."""
        if not self.r.exists(f"session:{session_id}"):
            return False
        self.r.set(f"session:{session_id}", json.dumps(data), ex=self.ttl)
        return True

    def smaz_session(self, session_id: str) -> None:
        """Odhlasite – smaze session."""
        self.r.delete(f"session:{session_id}")


store = SessionStore(r, ttl_sekundy=3600)

# Simulace login
session_id = store.vytvor_session({"uzivatel": "Misa", "role": "student", "login_cas": "10:00"})
print(f"Login – session_id: {session_id[:20]}...")

nacten = store.nacti_session(session_id)
print(f"Nactena session: {nacten}")

store.aktualizuj_session(session_id, {"uzivatel": "Misa", "role": "admin"})
aktualizovan = store.nacti_session(session_id)
print(f"Po aktualizaci: {aktualizovan}")

store.smaz_session(session_id)
print(f"Po odhlaseni: {store.nacti_session(session_id)}")


# 3. Pub/Sub – publisher a subscriber ve dvou threadech

print("\n=== Ukol 3: Pub/Sub simulace ===\n")


class PubSubSim:
    """Simulace Redis Pub/Sub."""

    def __init__(self):
        self._kanaly: dict[str, list[Any]] = defaultdict(list)
        self._lock   = threading.Lock()

    def subscribe(self, kanal: str) -> "PubSubFronta":
        fronta: deque = deque()
        with self._lock:
            self._kanaly[kanal].append(fronta)
        return PubSubFronta(self, kanal, fronta)

    def publish(self, kanal: str, zprava: str) -> int:
        with self._lock:
            odberatelu = self._kanaly.get(kanal, [])
            for q in odberatelu:
                q.append(zprava)
            return len(odberatelu)


class PubSubFronta:
    def __init__(self, pubsub: PubSubSim, kanal: str, fronta: deque):
        self._pubsub = pubsub
        self.kanal   = kanal
        self._fronta = fronta

    def listen(self):
        while True:
            if self._fronta:
                zprava = self._fronta.popleft()
                yield {"type": "message", "channel": self.kanal, "data": zprava}
            else:
                time.sleep(0.01)


ps = PubSubSim()
zpravy_prijate: list[str] = []
stop_event = threading.Event()


def subscriber_thread():
    fronta = ps.subscribe("novinky")
    for zprava in fronta.listen():
        if zprava["data"] == "STOP":
            break
        zpravy_prijate.append(zprava["data"])
        print(f"  [Subscriber] Obdrzel: {zprava['data']}")


def publisher_thread():
    time.sleep(0.05)
    for i, text in enumerate(["Zprava 1", "Python 3.13 vydán", "Novy kurz dostupny"]):
        odberatelu = ps.publish("novinky", text)
        print(f"  [Publisher] Odeslal '{text}' ({odberatelu} odberatelu)")
        time.sleep(0.1)
    ps.publish("novinky", "STOP")


sub_t = threading.Thread(target=subscriber_thread)
pub_t = threading.Thread(target=publisher_thread)

sub_t.start()
pub_t.start()

pub_t.join()
sub_t.join(timeout=3.0)

print(f"\n  Celkem prijato zprav: {len(zpravy_prijate)}")
