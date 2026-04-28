"""Reseni – Lekce 66: gRPC"""

# Produkční gRPC vyžaduje: pip install grpcio grpcio-tools
# Tato lekce rozsiruje simulator z originalu

import time
import json
import struct
import threading
from dataclasses import dataclass, field
from typing import Any, Iterator


# Zakladni simulace ProtoBuf a gRPC kanalu (ze zdrojove lekce)

class ProtoBuf:
    """Jednoduchy binarni serializer (simulace protobuf)."""

    def serialize(self, data: dict) -> bytes:
        raw = json.dumps(data, ensure_ascii=False).encode("utf-8")
        return struct.pack(">H", len(raw)) + raw

    def deserialize(self, data: bytes) -> dict:
        delka = struct.unpack_from(">H", data, 0)[0]
        return json.loads(data[2:2+delka])


pb = ProtoBuf()


@dataclass
class StudentRequest:
    id:    int = 0
    jmeno: str = ""
    vek:   int = 0
    body:  float = 0.0


@dataclass
class StudentResponse:
    id:    int = 0
    jmeno: str = ""
    vek:   int = 0
    body:  float = 0.0


@dataclass
class ListRequest:
    min_body: float = 0.0
    limit:    int = 10


@dataclass
class ChatMessage:
    user: str = ""
    text: str = ""


STUDENTI_GRPC: dict[int, dict] = {
    1: {"id": 1, "jmeno": "Misa",  "vek": 15, "body": 87.5},
    2: {"id": 2, "jmeno": "Tomas", "vek": 16, "body": 92.0},
    3: {"id": 3, "jmeno": "Bara",  "vek": 14, "body": 78.3},
    4: {"id": 4, "jmeno": "Ondra", "vek": 17, "body": 95.1},
}
_next_id = 5


class StudentServiceServicer:
    def GetStudent(self, request: StudentRequest) -> StudentResponse:
        data = STUDENTI_GRPC.get(request.id)
        if not data:
            raise ValueError(f"NOT_FOUND: Student {request.id}")
        return StudentResponse(**data)

    def ListStudents(self, request: ListRequest) -> Iterator[StudentResponse]:
        count = 0
        for s in STUDENTI_GRPC.values():
            if s["body"] >= request.min_body and count < request.limit:
                yield StudentResponse(**s)
                count += 1

    def AddStudent(self, request: StudentRequest) -> StudentResponse:
        global _next_id
        novy = {"id": _next_id, "jmeno": request.jmeno, "vek": request.vek, "body": request.body}
        STUDENTI_GRPC[_next_id] = novy
        _next_id += 1
        return StudentResponse(**novy)

    def Chat(self, zpravy: list[ChatMessage]) -> Iterator[ChatMessage]:
        for z in zpravy:
            yield ChatMessage(user="Server", text=f"Echo od serveru: {z.text}")

    # Ukol 1: DeleteStudent
    def DeleteStudent(self, request: StudentRequest) -> StudentResponse:
        if request.id not in STUDENTI_GRPC:
            raise ValueError(f"NOT_FOUND: Student {request.id} nenalezen")
        smazany = STUDENTI_GRPC.pop(request.id)
        return StudentResponse(**smazany)


class GrpcChannel:
    """Simulovany gRPC kanal."""

    def __init__(self, servicer: StudentServiceServicer):
        self._servicer = servicer
        self._latence_log: list[float] = []   # pro Ukol 2

    def _zmer_latenci(self, fn_name: str, fn, *args):
        """Ukol 2: Mereni latence kazdeho volani."""
        t0 = time.perf_counter()
        vysledek = fn(*args)
        elapsed = (time.perf_counter() - t0) * 1000
        self._latence_log.append(elapsed)
        return vysledek

    def unary_unary(self, metoda: str, request: Any) -> Any:
        fn = getattr(self._servicer, metoda)
        return self._zmer_latenci(metoda, fn, request)

    def unary_stream(self, metoda: str, request: Any) -> Iterator[Any]:
        fn = getattr(self._servicer, metoda)
        t0 = time.perf_counter()
        vysledky = list(fn(request))
        elapsed = (time.perf_counter() - t0) * 1000
        self._latence_log.append(elapsed)
        return iter(vysledky)

    def stream_stream(self, metoda: str, zpravy: list) -> Iterator[Any]:
        fn = getattr(self._servicer, metoda)
        t0 = time.perf_counter()
        vysledky = list(fn(zpravy))
        elapsed = (time.perf_counter() - t0) * 1000
        self._latence_log.append(elapsed)
        return iter(vysledky)

    def latence_report(self) -> dict:
        if not self._latence_log:
            return {}
        return {
            "volani":  len(self._latence_log),
            "min_ms":  round(min(self._latence_log), 3),
            "max_ms":  round(max(self._latence_log), 3),
            "avg_ms":  round(sum(self._latence_log) / len(self._latence_log), 3),
        }


servicer = StudentServiceServicer()
channel  = GrpcChannel(servicer)


# Standardni operace
print("=== gRPC simulace – rozsirence ===\n")

print("--- GetStudent ---")
for id_ in [1, 2, 99]:
    try:
        resp = channel.unary_unary("GetStudent", StudentRequest(id=id_))
        print(f"  GetStudent({id_}) → {resp.jmeno}, {resp.vek}let, {resp.body}b")
    except ValueError as e:
        print(f"  GetStudent({id_}) → {e}")

print("\n--- ListStudents ---")
for s in channel.unary_stream("ListStudents", ListRequest(min_body=85.0, limit=3)):
    print(f"  stream → {s.jmeno}: {s.body}b")


# Ukol 1: DeleteStudent s NOT_FOUND

print("\n=== Ukol 1: DeleteStudent ===\n")

print("--- Delete existujiciho ---")
try:
    resp = channel.unary_unary("DeleteStudent", StudentRequest(id=3))
    print(f"  Smazan: {resp.jmeno} (id={resp.id})")
except ValueError as e:
    print(f"  Chyba: {e}")

print("--- Delete neexistujiciho ---")
try:
    channel.unary_unary("DeleteStudent", StudentRequest(id=99))
except ValueError as e:
    print(f"  Spravne NOT_FOUND: {e}")

print("--- Seznam po smazani ---")
for s in channel.unary_stream("ListStudents", ListRequest(min_body=0)):
    print(f"  {s.id}: {s.jmeno}")


# Ukol 2: Interceptor pro mereni latence (zabudovan do GrpcChannel)

print("\n=== Ukol 2: Latence report (interceptor) ===\n")

# Provedeme par dalsich volani
channel.unary_unary("GetStudent",  StudentRequest(id=1))
channel.unary_unary("AddStudent",  StudentRequest(jmeno="Novy", vek=16, body=80.0))
channel.unary_stream("ListStudents", ListRequest(min_body=80.0))
channel.stream_stream("Chat", [ChatMessage("Klient", "Hi")])

report = channel.latence_report()
print(f"  Celkovy latence report:")
for k, v in report.items():
    print(f"    {k}: {v}")


# Ukol 3: Client-side load balancing

print("\n=== Ukol 3: Client-side load balancing ===\n")


class LoadBalancedChannel:
    """Distribuuje volani round-robin mezi vice kanaly."""

    def __init__(self, servicers: list[StudentServiceServicer]):
        self._kanaly = [GrpcChannel(s) for s in servicers]
        self._index  = 0
        self._lock   = threading.Lock()

    def _vybrat_kanal(self) -> GrpcChannel:
        with self._lock:
            kanal = self._kanaly[self._index]
            self._index = (self._index + 1) % len(self._kanaly)
            return kanal

    def unary_unary(self, metoda: str, request: Any) -> Any:
        kanal = self._vybrat_kanal()
        return kanal.unary_unary(metoda, request)

    def unary_stream(self, metoda: str, request: Any) -> Iterator[Any]:
        kanal = self._vybrat_kanal()
        return kanal.unary_stream(metoda, request)

    def latence_souhrn(self) -> dict:
        souhrn = {}
        for i, k in enumerate(self._kanaly):
            souhrn[f"kanal-{i}"] = k.latence_report()
        return souhrn


# Tri "servery" (sdili stejnou DB pro jednoduchost)
lb_channel = LoadBalancedChannel([
    StudentServiceServicer(),
    StudentServiceServicer(),
    StudentServiceServicer(),
])

print("  10 volani pres 3 kanaly (round-robin):")
for i in range(10):
    try:
        resp = lb_channel.unary_unary("GetStudent", StudentRequest(id=(i % 4) + 1))
        print(f"  [{i}] kanal={i%3}: {resp.jmeno}")
    except ValueError:
        print(f"  [{i}] kanal={i%3}: NOT_FOUND")

print("\n  Latence dle kanalu:")
for kanal_id, rep in lb_channel.latence_souhrn().items():
    if rep:
        print(f"    {kanal_id}: {rep.get('volani','?')} volani, avg={rep.get('avg_ms','?')}ms")
