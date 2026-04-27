"""
LEKCE 63: Redis – in-memory databáze
======================================
pip install redis

Redis = Remote Dictionary Server.
Ukládá data v RAM → extrémně rychlý (100k+ ops/sec).

Datové struktury:
  String    – základní klíč-hodnota, TTL, čítače
  List      – fronta, zásobník
  Hash      – slovník (jako Python dict)
  Set       – množina (unikátní hodnoty)
  Sorted Set– množina s skóre (leaderboard)
  Stream    – append-only log (jako Kafka-lite)
  Pub/Sub   – publish-subscribe messaging

Tato lekce simuluje Redis chování v Pythonu (bez nutnosti
instalace Redis serveru), plus ukazuje produkční kód s redis-py.
"""

import time
import json
import threading
import heapq
from collections import defaultdict, deque
from typing import Any

# ══════════════════════════════════════════════════════════════
# ČÁST 1: Redis simulátor (bez serveru)
# ══════════════════════════════════════════════════════════════

print("=== Redis simulátor ===\n")

class RedisSimulator:
    """Simuluje základní Redis API bez nutnosti serveru."""

    def __init__(self):
        self._store:   dict[str, Any]   = {}
        self._ttl:     dict[str, float] = {}  # key → expire timestamp
        self._zamek = threading.Lock()

    def _expiroval(self, key: str) -> bool:
        if key in self._ttl and time.time() > self._ttl[key]:
            del self._store[key]
            del self._ttl[key]
            return True
        return False

    def _ziskej(self, key: str) -> Any | None:
        if self._expiroval(key):
            return None
        return self._store.get(key)

    # ── String operace ────────────────────────────────────────
    def set(self, key: str, value: Any, ex: int | None = None) -> bool:
        with self._zamek:
            self._store[key] = str(value)
            if ex:
                self._ttl[key] = time.time() + ex
            return True

    def get(self, key: str) -> str | None:
        with self._zamek:
            return self._ziskej(key)

    def incr(self, key: str, amount: int = 1) -> int:
        with self._zamek:
            val = int(self._ziskej(key) or 0) + amount
            self._store[key] = str(val)
            return val

    def expire(self, key: str, seconds: int) -> bool:
        with self._zamek:
            if key in self._store:
                self._ttl[key] = time.time() + seconds
                return True
            return False

    def ttl(self, key: str) -> int:
        with self._zamek:
            if key not in self._store:
                return -2
            if key not in self._ttl:
                return -1
            remaining = self._ttl[key] - time.time()
            return max(0, int(remaining))

    def delete(self, *keys: str) -> int:
        with self._zamek:
            n = 0
            for k in keys:
                if k in self._store:
                    self._store.pop(k)
                    self._ttl.pop(k, None)
                    n += 1
            return n

    def exists(self, *keys: str) -> int:
        return sum(1 for k in keys if self._ziskej(k) is not None)

    def keys(self, pattern: str = "*") -> list[str]:
        import fnmatch
        with self._zamek:
            return [k for k in self._store if fnmatch.fnmatch(k, pattern)
                    and not self._expiroval(k)]

    # ── Hash operace ──────────────────────────────────────────
    def hset(self, key: str, mapping: dict) -> int:
        with self._zamek:
            if key not in self._store:
                self._store[key] = {}
            self._store[key].update({k: str(v) for k, v in mapping.items()})
            return len(mapping)

    def hget(self, key: str, field: str) -> str | None:
        with self._zamek:
            return (self._ziskej(key) or {}).get(field)

    def hgetall(self, key: str) -> dict:
        with self._zamek:
            return dict(self._ziskej(key) or {})

    def hincrby(self, key: str, field: str, amount: int = 1) -> int:
        with self._zamek:
            if key not in self._store:
                self._store[key] = {}
            val = int(self._store[key].get(field, 0)) + amount
            self._store[key][field] = str(val)
            return val

    # ── List operace ──────────────────────────────────────────
    def rpush(self, key: str, *values) -> int:
        with self._zamek:
            if key not in self._store:
                self._store[key] = deque()
            for v in values:
                self._store[key].append(str(v))
            return len(self._store[key])

    def lpop(self, key: str) -> str | None:
        with self._zamek:
            lst = self._ziskej(key)
            if lst:
                return lst.popleft()
            return None

    def lrange(self, key: str, start: int, stop: int) -> list[str]:
        with self._zamek:
            lst = list(self._ziskej(key) or [])
            if stop == -1:
                return lst[start:]
            return lst[start:stop+1]

    def llen(self, key: str) -> int:
        with self._zamek:
            return len(self._ziskej(key) or [])

    # ── Sorted Set ────────────────────────────────────────────
    def zadd(self, key: str, mapping: dict[str, float]) -> int:
        with self._zamek:
            if key not in self._store:
                self._store[key] = {}
            n = 0
            for member, score in mapping.items():
                if member not in self._store[key]:
                    n += 1
                self._store[key][member] = score
            return n

    def zrange(self, key: str, start: int, stop: int,
               withscores: bool = False, rev: bool = False) -> list:
        with self._zamek:
            data = self._ziskej(key) or {}
            serazeno = sorted(data.items(), key=lambda x: x[1], reverse=rev)
            if stop == -1:
                cast = serazeno[start:]
            else:
                cast = serazeno[start:stop+1]
            if withscores:
                return [(m, s) for m, s in cast]
            return [m for m, _ in cast]

    def zscore(self, key: str, member: str) -> float | None:
        with self._zamek:
            return (self._ziskej(key) or {}).get(member)

    # ── Set ───────────────────────────────────────────────────
    def sadd(self, key: str, *members) -> int:
        with self._zamek:
            if key not in self._store:
                self._store[key] = set()
            pred = len(self._store[key])
            self._store[key].update(str(m) for m in members)
            return len(self._store[key]) - pred

    def smembers(self, key: str) -> set:
        with self._zamek:
            return set(self._ziskej(key) or set())

    def sismember(self, key: str, member: str) -> bool:
        with self._zamek:
            return str(member) in (self._ziskej(key) or set())


r = RedisSimulator()


# ══════════════════════════════════════════════════════════════
# ČÁST 2: Ukázky použití
# ══════════════════════════════════════════════════════════════

print("--- Strings a TTL ---")
r.set("uzivatel:1:jmeno", "Míša")
r.set("session:abc123", "uzivatel:1", ex=2)   # vyprší za 2s

print(f"  jmeno:    {r.get('uzivatel:1:jmeno')}")
print(f"  session:  {r.get('session:abc123')}  TTL={r.ttl('session:abc123')}s")
time.sleep(2.1)
print(f"  session po 2s: {r.get('session:abc123')}  (vypršelo)")

print("\n--- Čítač (rate limiting) ---")
def je_povolen(uzivatel_id: str, limit: int = 5, okno: int = 1) -> bool:
    klic = f"rate:{uzivatel_id}"
    pocet = r.incr(klic)
    if pocet == 1:
        r.expire(klic, okno)
    return pocet <= limit

uzivatel = "user_42"
for i in range(8):
    povolen = je_povolen(uzivatel, limit=5)
    print(f"  Požadavek {i+1}: {'✓ OK' if povolen else '✗ Rate limit!'}")

print("\n--- Hash (uživatelský profil) ---")
r.hset("profil:1", {"jmeno": "Míša", "email": "misa@k.cz", "vek": "15", "body": "0"})
r.hincrby("profil:1", "body", 10)
r.hincrby("profil:1", "body", 5)
print(f"  Profil: {r.hgetall('profil:1')}")

print("\n--- List (fronta úkolů) ---")
for ukol in ["email", "report", "backup", "cleanup"]:
    r.rpush("fronta:ukoly", ukol)
print(f"  Fronta: {r.lrange('fronta:ukoly', 0, -1)}")
while r.llen("fronta:ukoly") > 0:
    ukol = r.lpop("fronta:ukoly")
    print(f"  Zpracovávám: {ukol}")

print("\n--- Sorted Set (leaderboard) ---")
r.zadd("skore:tyden", {
    "Míša": 1250, "Tomáš": 980, "Bára": 1100,
    "Ondra": 1450, "Klára": 750,
})
r.zadd("skore:tyden", {"Míša": 1350})   # update skóre

print("  Top 3:")
for i, (jmeno, skore) in enumerate(r.zrange("skore:tyden", 0, 2,
                                              withscores=True, rev=True), 1):
    print(f"    {i}. {jmeno}: {skore:.0f} bodů")

print("\n--- Set (unikátní návštěvníci) ---")
for uzivatel in ["u1","u2","u3","u1","u2","u4","u1"]:
    r.sadd("navstevnici:2024-01", uzivatel)
print(f"  Unikátní návštěvníci: {len(r.smembers('navstevnici:2024-01'))}")


# ══════════════════════════════════════════════════════════════
# ČÁST 3: Produkční vzory
# ══════════════════════════════════════════════════════════════

print("\n=== Produkční vzory ===\n")

print("--- Cache-aside pattern ---")

def ziskej_data_z_db(id: int) -> dict:
    print(f"    [DB] Načítám user {id} z databáze...")
    time.sleep(0.1)   # simulace DB dotazu
    return {"id": id, "jmeno": f"User_{id}", "email": f"user{id}@k.cz"}

def ziskej_uzivatele(id: int, ttl: int = 60) -> dict:
    klic = f"cache:user:{id}"
    cached = r.get(klic)
    if cached:
        print(f"    [cache] HIT pro user {id}")
        return json.loads(cached)
    data = ziskej_data_z_db(id)
    r.set(klic, json.dumps(data), ex=ttl)
    print(f"    [cache] MISS → uloženo do cache")
    return data

for _ in range(3):
    ziskej_uzivatele(42)

print("\n--- Distribuovaný lock ---")

class DistributedLock:
    def __init__(self, redis, nazev: str, ttl: int = 10):
        self.r   = redis
        self.key = f"lock:{nazev}"
        self.ttl = ttl

    def __enter__(self):
        while True:
            if not self.r.exists(self.key):
                self.r.set(self.key, "1", ex=self.ttl)
                return self
            time.sleep(0.01)

    def __exit__(self, *args):
        self.r.delete(self.key)

with DistributedLock(r, "platba"):
    print("  Kritická sekce – zpracovávám platbu...")
    time.sleep(0.1)
print("  Lock uvolněn.")


print("""
=== Produkční redis-py kód ===

import redis

# Připojení (s connection poolem)
r = redis.Redis(
    host="localhost", port=6379, db=0,
    decode_responses=True,
    max_connections=20,
)

# Cluster
r = redis.RedisCluster(host="localhost", port=7000)

# Asyncio
import redis.asyncio as aioredis
r = await aioredis.from_url("redis://localhost")

# Pub/Sub
pubsub = r.pubsub()
pubsub.subscribe("kanal")
for zprava in pubsub.listen():
    print(zprava)

# Pipeline (batch operace)
pipe = r.pipeline()
pipe.set("a", 1)
pipe.set("b", 2)
pipe.incr("a")
results = pipe.execute()   # odešle vše najednou → rychlejší
""")

# TVOJE ÚLOHA:
# 1. Implementuj LRU cache (Least Recently Used) pomocí Redis Sorted Set.
# 2. Napiš session store – ukládej Flask/FastAPI sessions do Redis.
# 3. Přidej Pub/Sub: jeden thread publishuje zprávy, druhý je přijímá.
