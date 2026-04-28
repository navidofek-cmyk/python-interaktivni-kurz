"""Reseni – Lekce 65: Kafka – distribuovane streamovani"""

# Produkční Kafka vyžaduje: pip install kafka-python
# Tato lekce rozsiruje simulator z originalu

import threading
import time
import json
import random
import uuid
from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import Callable


@dataclass
class Message:
    topic:     str
    partition: int
    offset:    int
    key:       str | None
    value:     bytes
    timestamp: float = field(default_factory=time.time)


class Partition:
    def __init__(self):
        self._log:  list[Message] = []
        self._lock = threading.Lock()

    def append(self, msg: Message) -> int:
        with self._lock:
            msg.offset = len(self._log)
            self._log.append(msg)
            return msg.offset

    def read_from(self, offset: int) -> list[Message]:
        with self._lock:
            return self._log[offset:]

    def size(self) -> int:
        return len(self._log)


class KafkaSim:
    def __init__(self, num_partitions: int = 3):
        self._topics:     dict[str, list[Partition]] = {}
        self._num_parts   = num_partitions
        self._lock        = threading.Lock()
        self._skupiny:    dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))

    def _get_or_create_topic(self, topic: str) -> list[Partition]:
        with self._lock:
            if topic not in self._topics:
                self._topics[topic] = [Partition() for _ in range(self._num_parts)]
            return self._topics[topic]

    def produce(self, topic: str, value: bytes, key: str | None = None) -> int:
        partitions = self._get_or_create_topic(topic)
        part_idx   = hash(key or str(random.random())) % self._num_parts
        msg = Message(topic=topic, partition=part_idx, offset=0, key=key, value=value)
        return partitions[part_idx].append(msg)

    def consume(self, topic: str, group: str, max_zprav: int = 10) -> list[Message]:
        partitions = self._get_or_create_topic(topic)
        zpravy: list[Message] = []
        for i, partition in enumerate(partitions):
            klic_offset = f"{topic}:{i}"
            offset = self._skupiny[group][klic_offset]
            nove   = partition.read_from(offset)[:max_zprav - len(zpravy)]
            zpravy.extend(nove)
            self._skupiny[group][klic_offset] = offset + len(nove)
            if len(zpravy) >= max_zprav:
                break
        return zpravy

    def topic_info(self, topic: str) -> dict:
        partitions = self._topics.get(topic, [])
        return {
            "topic":      topic,
            "partitions": len(partitions),
            "zprav":      sum(p.size() for p in partitions),
        }


broker = KafkaSim(num_partitions=3)


# 1. Consumer Group rebalancing – novy consumer redistribuuje partitions

print("=== Ukol 1: Consumer Group rebalancing ===\n")


class ConsumerGroupManager:
    """Spravuje consumer group s dynamickym rebalancingem."""

    def __init__(self, topic: str, kafka: KafkaSim):
        self.topic    = topic
        self.kafka    = kafka
        self.group_id = f"group-{uuid.uuid4().hex[:6]}"
        self._members: dict[str, list[int]] = {}  # consumer_id → [assigned partitions]
        self._lock    = threading.Lock()

    def join(self, consumer_id: str) -> list[int]:
        """Pripoji noveho consumera a provede rebalancing."""
        with self._lock:
            vsichni  = list(self._members.keys()) + [consumer_id]
            parts    = list(range(self.kafka._num_parts))
            # Round-robin distribuce partitions
            priruzeni: dict[str, list[int]] = defaultdict(list)
            for i, part in enumerate(parts):
                priruzeni[vsichni[i % len(vsichni)]].append(part)
            self._members = dict(priruzeni)
            self._members.setdefault(consumer_id, [])
            print(f"  [Rebalance] +{consumer_id}: distribuce = {dict(self._members)}")
            return self._members[consumer_id]

    def leave(self, consumer_id: str) -> None:
        """Odpoji consumera a provede rebalancing."""
        with self._lock:
            self._members.pop(consumer_id, None)
            vsichni = list(self._members.keys())
            if vsichni:
                parts = list(range(self.kafka._num_parts))
                priruzeni: dict[str, list[int]] = defaultdict(list)
                for i, part in enumerate(parts):
                    priruzeni[vsichni[i % len(vsichni)]].append(part)
                self._members = dict(priruzeni)
            print(f"  [Rebalance] -{consumer_id}: distribuce = {dict(self._members)}")

    def assigned(self, consumer_id: str) -> list[int]:
        return self._members.get(consumer_id, [])


# Demo rebalancingu
topic_name = "udalosti"
for i in range(5):
    broker.produce(topic_name, json.dumps({"id": i}).encode())

manager = ConsumerGroupManager(topic_name, broker)
c1 = manager.join("consumer-1")
print(f"  consumer-1 dostalo: partitions {c1}")
c2 = manager.join("consumer-2")
print(f"  consumer-2 dostalo: partitions {c2}")
c3 = manager.join("consumer-3")
print(f"  consumer-3 dostalo: partitions {c3}")
manager.leave("consumer-2")
print(f"  Po odchodu consumer-2: {dict(manager._members)}")


# 2. Dead Letter Queue – zpravy ktere selzou 3x jdou do DLQ topicu

print("\n=== Ukol 2: Dead Letter Queue (DLQ) ===\n")


class DLQConsumer:
    """Consumer s Dead Letter Queue pro selhave zpravy."""
    DLQ_SUFFIX = ".dlq"
    MAX_RETRIES = 3

    def __init__(self, topic: str, kafka: KafkaSim, handler: Callable):
        self.topic   = topic
        self.dlq     = topic + self.DLQ_SUFFIX
        self.kafka   = kafka
        self.handler = handler
        self._retries: dict[int, int] = defaultdict(int)  # offset → pocet pokusu

    def zpracuj(self, group_id: str = "dlq-group") -> None:
        zpravy = self.kafka.consume(self.topic, group_id)
        for msg in zpravy:
            klic = msg.offset
            try:
                self.handler(msg)
                self._retries.pop(klic, None)
                print(f"  [OK] partition={msg.partition} offset={msg.offset}")
            except Exception as e:
                self._retries[klic] += 1
                pokusy = self._retries[klic]
                if pokusy >= self.MAX_RETRIES:
                    # Odesli do DLQ
                    dlq_value = json.dumps({
                        "puvodni_topic":     self.topic,
                        "puvodni_offset":    msg.offset,
                        "puvodni_partition": msg.partition,
                        "chyba":             str(e),
                        "pokusy":            pokusy,
                        "data":              msg.value.decode(errors="replace"),
                    }).encode()
                    self.kafka.produce(self.dlq, dlq_value)
                    self._retries.pop(klic, None)
                    print(f"  [DLQ] partition={msg.partition} offset={msg.offset} → DLQ po {pokusy} pokusech: {e}")
                else:
                    print(f"  [RETRY {pokusy}/{self.MAX_RETRIES}] {e}")


# Pridat testovaci zpravy
for i in range(6):
    broker.produce("platby", json.dumps({"id": i, "castka": 100 * i}).encode())

cnt = {"n": 0}

def platba_handler(msg: Message) -> None:
    """Simulace: kazda treti platba selze."""
    data = json.loads(msg.value)
    cnt["n"] += 1
    if data["id"] % 3 == 0 and data["id"] > 0:
        raise ValueError(f"Platba {data['id']} zamítnuta bankou")
    print(f"  [Zpracovano] platba id={data['id']} castka={data['castka']}")


dlq_consumer = DLQConsumer("platby", broker, platba_handler)
for _ in range(DLQConsumer.MAX_RETRIES + 1):
    dlq_consumer.zpracuj()

print(f"\n  DLQ zpravy:")
dlq_zpravy = broker.consume("platby" + DLQConsumer.DLQ_SUFFIX, "dlq-reader")
for z in dlq_zpravy:
    d = json.loads(z.value)
    print(f"    {d['puvodni_topic']} offset={d['puvodni_offset']}: {d['chyba']}")


# 3. Kafka Streams – agregace po 10s oknech

print("\n=== Ukol 3: Kafka Streams simulace – 10s okna ===\n")


class TumblingWindowAggregator:
    """Agreguje zpravy do neprekreslujicich se casovych oken."""

    def __init__(self, sirka_okna_s: float = 10.0):
        self.sirka = sirka_okna_s
        self._okna: dict[float, list[dict]] = defaultdict(list)

    def _klic_okna(self, timestamp: float) -> float:
        """Vrati zacatek okna pro dany timestamp."""
        return (timestamp // self.sirka) * self.sirka

    def pridat(self, msg: Message) -> None:
        try:
            data = json.loads(msg.value)
        except Exception:
            return
        klic = self._klic_okna(msg.timestamp)
        self._okna[klic].append(data)

    def agreguj(self) -> list[dict]:
        """Vrati agregace vsech uzavrenych oken."""
        nyni = time.time()
        vysledky = []
        for klic_okna, zaznamy in sorted(self._okna.items()):
            if klic_okna + self.sirka <= nyni:   # okno je uzavrene
                vysledky.append({
                    "okno_od":   klic_okna,
                    "okno_do":   klic_okna + self.sirka,
                    "pocet":     len(zaznamy),
                    "sum_castka": sum(z.get("castka", 0) for z in zaznamy),
                    "avg_castka": (
                        sum(z.get("castka", 0) for z in zaznamy) / len(zaznamy)
                        if zaznamy else 0
                    ),
                })
        return vysledky


# Simulace zprav z minulosti
okno_sim = TumblingWindowAggregator(sirka_okna_s=10.0)

t_base = time.time() - 35   # 35 sekund zpet

for i in range(15):
    msg = Message(
        topic="transakce",
        partition=0,
        offset=i,
        key=None,
        value=json.dumps({"id": i, "castka": random.randint(100, 1000)}).encode(),
        timestamp=t_base + i * 2.5,
    )
    okno_sim.pridat(msg)

print("  Agregace po 10s oknech:")
for okno in okno_sim.agreguj():
    import datetime
    od = datetime.datetime.fromtimestamp(okno["okno_od"]).strftime("%H:%M:%S")
    do = datetime.datetime.fromtimestamp(okno["okno_do"]).strftime("%H:%M:%S")
    print(f"  [{od}–{do}] {okno['pocet']} transakci, sum={okno['sum_castka']}, avg={okno['avg_castka']:.0f}")
