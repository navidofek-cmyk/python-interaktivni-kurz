"""
LEKCE 65: Kafka – distribuované streamování
============================================
pip install kafka-python

Apache Kafka = distribuovaný messaging systém.
Designovaný pro miliony zpráv za sekundu.

Koncepty:
  Topic      – pojmenovaný kanál pro zprávy
  Partition  – topic je rozdělen na partitions (paralelismus)
  Producer   – posílá zprávy do topicu
  Consumer   – čte zprávy z topicu
  Consumer Group – víc consumerů sdílí práci
  Offset     – pozice v partition (Kafka nemazí zprávy!)
  Broker     – Kafka server (obvykle cluster)

Redis PubSub vs Kafka:
  Redis  → rychlý, ztrácí zprávy po restartu, max throughput ~1M/s
  Kafka  → perzistentní, přehrávání zpráv, petabajty, Netflix/LinkedIn

Tato lekce simuluje Kafka bez serveru + produkční kód.
"""

import threading
import time
import json
import random
import uuid
from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import Callable, Any
from datetime import datetime
from enum import Enum

# ══════════════════════════════════════════════════════════════
# ČÁST 1: Kafka simulátor
# ══════════════════════════════════════════════════════════════

print("=== Kafka simulátor ===\n")

@dataclass
class KafkaMessage:
    topic:     str
    partition: int
    offset:    int
    key:       str | None
    value:     Any
    timestamp: float = field(default_factory=time.time)
    headers:   dict  = field(default_factory=dict)

    def __repr__(self):
        return (f"KafkaMsg(topic={self.topic!r}, partition={self.partition}, "
                f"offset={self.offset}, key={self.key!r})")

class KafkaSimulator:
    """In-process Kafka simulátor pro demonstraci."""

    def __init__(self):
        # topic → partition → [zpravy]
        self._topics:  dict[str, dict[int, list[KafkaMessage]]] = defaultdict(
            lambda: defaultdict(list)
        )
        self._offsets: dict[str, dict[int, int]] = defaultdict(
            lambda: defaultdict(int)
        )
        # consumer_group → topic → partition → committed_offset
        self._committed: dict[str, dict[str, dict[int, int]]] = defaultdict(
            lambda: defaultdict(lambda: defaultdict(int))
        )
        self._zamek = threading.Lock()

    def create_topic(self, nazev: str, partitions: int = 3):
        with self._zamek:
            for p in range(partitions):
                self._topics[nazev][p]  # inicializuj
        print(f"  [Kafka] Topic {nazev!r} vytvořen ({partitions} partitions)")

    def _partition_for_key(self, key: str | None, num_partitions: int) -> int:
        if key is None:
            return random.randint(0, num_partitions - 1)
        return hash(key) % num_partitions

    def produce(self, topic: str, value: Any, key: str | None = None,
                headers: dict | None = None) -> KafkaMessage:
        with self._zamek:
            parts = self._topics[topic]
            num_parts = len(parts) or 1
            partition = self._partition_for_key(key, num_parts)
            offset = len(parts[partition])
            msg = KafkaMessage(
                topic=topic, partition=partition, offset=offset,
                key=key, value=value, headers=headers or {},
            )
            parts[partition].append(msg)
            return msg

    def consume(self, topic: str, group: str, partition: int | None = None,
                batch_size: int = 10) -> list[KafkaMessage]:
        """Vrátí nové zprávy od posledního commitu."""
        with self._zamek:
            zpravy = []
            parts = self._topics.get(topic, {})
            cil_partitions = [partition] if partition is not None else list(parts.keys())
            for p in cil_partitions:
                committed = self._committed[group][topic][p]
                nove = parts[p][committed:committed + batch_size]
                zpravy.extend(nove)
            return zpravy

    def commit(self, group: str, zpravy: list[KafkaMessage]):
        with self._zamek:
            for msg in zpravy:
                self._committed[group][msg.topic][msg.partition] = msg.offset + 1

    def lag(self, topic: str, group: str) -> int:
        """Počet nezpracovaných zpráv."""
        with self._zamek:
            total_lag = 0
            for p, msgs in self._topics.get(topic, {}).items():
                committed = self._committed[group][topic][p]
                total_lag += len(msgs) - committed
            return total_lag

kafka = KafkaSimulator()


# ══════════════════════════════════════════════════════════════
# ČÁST 2: Producer / Consumer
# ══════════════════════════════════════════════════════════════

print("--- Producer: uživatelské události ---")

kafka.create_topic("udalosti-uzivatelu", partitions=3)
kafka.create_topic("platby",             partitions=2)
kafka.create_topic("notifikace",         partitions=1)

# Producer – generuje události
udalosti = [
    ("prihlaseni",  "user:1", {"user_id": 1, "ip": "192.168.1.1"}),
    ("nakup",       "user:2", {"user_id": 2, "produkt": "Python kurz", "cena": 999}),
    ("prihlaseni",  "user:3", {"user_id": 3, "ip": "10.0.0.1"}),
    ("nakup",       "user:1", {"user_id": 1, "produkt": "NumPy kniha", "cena": 499}),
    ("odhlaseni",   "user:2", {"user_id": 2}),
    ("platba",      "user:2", {"user_id": 2, "castka": 999, "status": "OK"}),
    ("prihlaseni",  "user:4", {"user_id": 4, "ip": "172.16.0.5"}),
    ("nakup",       "user:3", {"user_id": 3, "produkt": "Pandas kurz", "cena": 799}),
]

for typ, klic, data in udalosti:
    msg = kafka.produce("udalosti-uzivatelu",
                        value={"typ": typ, "data": data, "ts": datetime.now().isoformat()},
                        key=klic)
    print(f"  → {msg}")

print(f"\n  Lag (skupina 'analyzy'): {kafka.lag('udalosti-uzivatelu', 'analyzy')}")

print("\n--- Consumer: analýzy ---")

# Consumer group – zpracuj zprávy
davka = kafka.consume("udalosti-uzivatelu", group="analyzy", batch_size=5)
print(f"  Přijato {len(davka)} zpráv:")
for msg in davka:
    print(f"  [p={msg.partition} o={msg.offset}] key={msg.key} typ={msg.value['typ']}")

kafka.commit("analyzy", davka)
print(f"  Po commitu – lag: {kafka.lag('udalosti-uzivatelu', 'analyzy')}")

# Zpracuj zbytek
zbytek = kafka.consume("udalosti-uzivatelu", group="analyzy")
kafka.commit("analyzy", zbytek)
print(f"  Po druhém commitu – lag: {kafka.lag('udalosti-uzivatelu', 'analyzy')}")


# ══════════════════════════════════════════════════════════════
# ČÁST 3: Event-driven architektura
# ══════════════════════════════════════════════════════════════

print("\n=== Event-driven pipeline ===\n")

kafka.create_topic("objednavky", partitions=3)
kafka.create_topic("platby-vysledky", partitions=2)
kafka.create_topic("emaily-k-odeslani", partitions=1)

def objednavkovy_service():
    """Vytváří objednávky a posílá je do Kafky."""
    objednavky = [
        {"id": "ord-1", "user": "u1", "produkt": "Python kurz", "cena": 999},
        {"id": "ord-2", "user": "u2", "produkt": "Data Science",  "cena": 1499},
        {"id": "ord-3", "user": "u3", "produkt": "Docker kurz",   "cena": 799},
    ]
    for obj in objednavky:
        kafka.produce("objednavky", value=obj, key=obj["id"])
        print(f"  [Orders] Objednávka vytvořena: {obj['id']} ({obj['cena']} Kč)")

def platebni_service():
    """Zpracuje objednávky a posílá výsledky plateb."""
    zpravy = kafka.consume("objednavky", group="platby")
    kafka.commit("platby", zpravy)
    for msg in zpravy:
        obj = msg.value
        uspesna = random.random() > 0.2   # 80% úspěšnost
        vysledek = {
            "objednavka_id": obj["id"],
            "user": obj["user"],
            "cena": obj["cena"],
            "stav": "OK" if uspesna else "SELHALO",
        }
        kafka.produce("platby-vysledky", value=vysledek, key=obj["id"])
        print(f"  [Platby] {obj['id']}: {'✓ OK' if uspesna else '✗ SELHALO'}")

def notifikacni_service():
    """Posílá emaily na základě výsledků plateb."""
    zpravy = kafka.consume("platby-vysledky", group="notifikace")
    kafka.commit("notifikace", zpravy)
    for msg in zpravy:
        v = msg.value
        text = (f"Platba {v['cena']} Kč proběhla úspěšně."
                if v["stav"] == "OK"
                else f"Platba {v['cena']} Kč selhala. Zkuste znovu.")
        kafka.produce("emaily-k-odeslani",
                      value={"komu": f"{v['user']}@k.cz", "text": text})
        print(f"  [Email] → {v['user']}: {text[:50]}")

# Spusť pipeline
print("Pipeline:")
objednavkovy_service()
print()
platebni_service()
print()
notifikacni_service()


# ══════════════════════════════════════════════════════════════
# ČÁST 4: Produkční kafka-python kód
# ══════════════════════════════════════════════════════════════

print("""
=== Produkční kafka-python kód ===

from kafka import KafkaProducer, KafkaConsumer
import json

# Producer
producer = KafkaProducer(
    bootstrap_servers=["kafka1:9092", "kafka2:9092"],
    value_serializer=lambda v: json.dumps(v).encode(),
    key_serializer=lambda k: k.encode() if k else None,
    acks="all",           # všechny repliky potvrdí
    retries=3,
    compression_type="gzip",
)

producer.send("udalosti", key="user:1", value={"typ": "prihlaseni"})
producer.flush()

# Consumer
consumer = KafkaConsumer(
    "udalosti",
    bootstrap_servers=["kafka1:9092"],
    group_id="moje-skupina",
    value_deserializer=lambda v: json.loads(v.decode()),
    auto_offset_reset="earliest",   # začni od začátku pokud nový group
    enable_auto_commit=False,        # ruční commit pro at-least-once
)

for zprava in consumer:
    zpracuj(zprava.value)
    consumer.commit()   # commit po zpracování

# Aiokafka (asyncio)
# pip install aiokafka
from aiokafka import AIOKafkaProducer, AIOKafkaConsumer

async def async_producer():
    p = AIOKafkaProducer(bootstrap_servers="kafka:9092")
    await p.start()
    await p.send_and_wait("topic", b"zprava")
    await p.stop()
""")

print("""
=== Redis PubSub vs Kafka vs RabbitMQ ===

              Redis PubSub   Kafka          RabbitMQ
Perzistence   ✗ RAM only     ✓ disk          ✓ disk
Replay        ✗              ✓ (offsets)     ✗
Throughput    ~1M/s          ~10M/s          ~100k/s
Ordering      ✗              ✓ per partition  ✓ per queue
Use-case      Live notif.    Event sourcing  Task queue
""")

# TVOJE ÚLOHA:
# 1. Přidej do simulátoru Consumer Group rebalancing (nový consumer → redistribuce partitions).
# 2. Implementuj Dead Letter Queue – zprávy které selžou 3× jdou do DLQ topicu.
# 3. Napiš Kafka Streams simulaci – aggregate zprávy po 10s oknech.
