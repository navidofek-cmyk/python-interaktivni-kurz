"""
LEKCE 66: gRPC – vysokovýkonné RPC
=====================================
pip install grpcio grpcio-tools

gRPC = Google Remote Procedure Call.
Volej funkci na vzdáleném serveru jako by byla lokální.

REST vs gRPC:
  REST  → JSON přes HTTP/1.1, lidsky čitelné, cacheable
  gRPC  → Protocol Buffers přes HTTP/2, binární, 5–10× rychlejší

Protocol Buffers (protobuf):
  - Silně typovaný binární formát
  - Generuje kód pro 10+ jazyků
  - Zpětná kompatibilita (číslovaná pole)

Typy gRPC volání:
  Unary          – klasické req/resp
  Server stream  – server posílá proud dat
  Client stream  – klient posílá proud dat
  Bidirectional  – obousměrný stream

Tato lekce simuluje gRPC bez protoc kompilátoru.
"""

import time
import json
import struct
import threading
import random
import io
from dataclasses import dataclass, field, asdict
from typing import Iterator, Generator, Any
from datetime import datetime
from collections import defaultdict

# ══════════════════════════════════════════════════════════════
# ČÁST 1: Protobuf simulátor
# ══════════════════════════════════════════════════════════════

print("=== Protocol Buffers – binární serializace ===\n")

# Ukázka .proto souboru (pro referenci)
PROTO_DEF = """\
syntax = "proto3";

package kurz;

service StudentService {
    rpc GetStudent (StudentRequest) returns (StudentResponse);
    rpc ListStudents (ListRequest) returns (stream StudentResponse);
    rpc AddStudent (StudentRequest) returns (StudentResponse);
    rpc Chat (stream ChatMessage) returns (stream ChatMessage);
}

message StudentRequest {
    int32 id    = 1;
    string jmeno = 2;
    int32 vek   = 3;
    float body  = 4;
}

message StudentResponse {
    int32 id     = 1;
    string jmeno = 2;
    int32 vek    = 3;
    float body   = 4;
    string status = 5;
}

message ListRequest {
    int32 min_body = 1;
    int32 limit    = 2;
}

message ChatMessage {
    string user = 1;
    string text = 2;
    int64  ts   = 3;
}
"""

class ProtobufSimulator:
    """Simuluje binární protobuf kódování (zjednodušeně)."""

    WIRE_VARINT = 0
    WIRE_64BIT  = 1
    WIRE_LEN    = 2
    WIRE_32BIT  = 5

    @classmethod
    def encode_varint(cls, n: int) -> bytes:
        parts = []
        while n > 0x7F:
            parts.append((n & 0x7F) | 0x80)
            n >>= 7
        parts.append(n)
        return bytes(parts)

    @classmethod
    def encode_field(cls, field_num: int, wire: int, data: bytes) -> bytes:
        tag = (field_num << 3) | wire
        return cls.encode_varint(tag) + data

    @classmethod
    def serialize(cls, zprava: dict) -> bytes:
        """Zjednodušená protobuf serializace."""
        buf = b""
        for i, (klic, hodnota) in enumerate(zprava.items(), 1):
            if isinstance(hodnota, int):
                buf += cls.encode_field(i, cls.WIRE_VARINT,
                                         cls.encode_varint(abs(hodnota)))
            elif isinstance(hodnota, float):
                buf += cls.encode_field(i, cls.WIRE_32BIT,
                                         struct.pack("<f", hodnota))
            elif isinstance(hodnota, str):
                enc = hodnota.encode("utf-8")
                buf += cls.encode_field(i, cls.WIRE_LEN,
                                         cls.encode_varint(len(enc)) + enc)
        return buf

pb = ProtobufSimulator()
zprava = {"id": 1, "jmeno": "Míša", "vek": 15, "body": 87.5}
binarni = pb.serialize(zprava)
json_verze = json.dumps(zprava, ensure_ascii=False).encode()

print(f"Zpráva:      {zprava}")
print(f"JSON:        {json_verze} ({len(json_verze)} B)")
print(f"Protobuf:    {binarni.hex()} ({len(binarni)} B)")
print(f"Komprese:    {(1 - len(binarni)/len(json_verze))*100:.0f}% menší než JSON")


# ══════════════════════════════════════════════════════════════
# ČÁST 2: gRPC server simulátor
# ══════════════════════════════════════════════════════════════

print("\n=== gRPC server + klient simulace ===\n")

@dataclass
class StudentRequest:
    id:    int = 0
    jmeno: str = ""
    vek:   int = 0
    body:  float = 0.0

@dataclass
class StudentResponse:
    id:     int = 0
    jmeno:  str = ""
    vek:    int = 0
    body:   float = 0.0
    status: str = "OK"

@dataclass
class ListRequest:
    min_body: float = 0.0
    limit:    int = 10

@dataclass
class ChatMessage:
    user: str = ""
    text: str = ""
    ts:   int = field(default_factory=lambda: int(time.time() * 1000))


# DB
STUDENTI_DB = {
    1: StudentResponse(1, "Míša",  15, 87.5),
    2: StudentResponse(2, "Tomáš", 16, 92.0),
    3: StudentResponse(3, "Bára",  14, 78.3),
    4: StudentResponse(4, "Ondra", 17, 95.1),
    5: StudentResponse(5, "Klára", 15, 65.0),
}

class StudentServiceServicer:
    """Implementace gRPC service (odpovídá kódu generovanému z .proto)."""

    # ── Unary RPC ────────────────────────────────────────────
    def GetStudent(self, request: StudentRequest) -> StudentResponse:
        """Vrátí jednoho studenta podle ID."""
        student = STUDENTI_DB.get(request.id)
        if not student:
            raise ValueError(f"NOT_FOUND: student {request.id}")
        return student

    def AddStudent(self, request: StudentRequest) -> StudentResponse:
        """Přidá nového studenta."""
        novy_id = max(STUDENTI_DB.keys()) + 1
        student = StudentResponse(novy_id, request.jmeno, request.vek, request.body)
        STUDENTI_DB[novy_id] = student
        return student

    # ── Server streaming RPC ──────────────────────────────────
    def ListStudents(self, request: ListRequest) -> Iterator[StudentResponse]:
        """Streamuje studenty klientovi."""
        pocet = 0
        for student in STUDENTI_DB.values():
            if student.body >= request.min_body:
                if pocet >= request.limit:
                    break
                yield student
                pocet += 1
                time.sleep(0.02)   # simulace síťové latence

    # ── Bidirectional streaming RPC ───────────────────────────
    def Chat(self, requests: Iterator[ChatMessage]) -> Iterator[ChatMessage]:
        """Obousměrný chat stream."""
        for zprava in requests:
            echo = ChatMessage(
                user="Server",
                text=f"Echo: {zprava.text}",
            )
            yield echo


class GrpcChannel:
    """Simuluje gRPC channel (TCP spojení)."""

    def __init__(self, servicer):
        self._servicer = servicer
        self._latence = 0.005   # 5ms RTT

    def unary_unary(self, method: str, request):
        time.sleep(self._latence)
        fn = getattr(self._servicer, method)
        return fn(request)

    def unary_stream(self, method: str, request):
        time.sleep(self._latence)
        fn = getattr(self._servicer, method)
        yield from fn(request)

    def stream_stream(self, method: str, requests):
        time.sleep(self._latence)
        fn = getattr(self._servicer, method)
        yield from fn(iter(requests))


# Klient
servicer = StudentServiceServicer()
channel  = GrpcChannel(servicer)

print("--- Unary RPC: GetStudent ---")
for id_ in [1, 3, 99]:
    try:
        resp = channel.unary_unary("GetStudent", StudentRequest(id=id_))
        print(f"  GetStudent({id_}) → {resp.jmeno}, {resp.vek}let, {resp.body}b")
    except ValueError as e:
        print(f"  GetStudent({id_}) → gRPC Status: {e}")

print("\n--- Server streaming: ListStudents ---")
stream = channel.unary_stream("ListStudents", ListRequest(min_body=85.0, limit=3))
for student in stream:
    print(f"  stream → {student.jmeno}: {student.body}b")

print("\n--- Unary: AddStudent ---")
novy = channel.unary_unary("AddStudent", StudentRequest(jmeno="Pavel", vek=18, body=88.0))
print(f"  Přidán: id={novy.id}, {novy.jmeno}")

print("\n--- Bidirectional streaming: Chat ---")
zpravy_klienta = [
    ChatMessage(user="Klient", text="Ahoj!"),
    ChatMessage(user="Klient", text="Jak se máš?"),
    ChatMessage(user="Klient", text="Nashledanou!"),
]
for odpoved in channel.stream_stream("Chat", zpravy_klienta):
    print(f"  ← {odpoved.user}: {odpoved.text}")


# ══════════════════════════════════════════════════════════════
# ČÁST 3: Výkon – gRPC vs REST srovnání
# ══════════════════════════════════════════════════════════════

print("\n=== Výkon: gRPC vs REST simulace ===\n")

import json

def simuluj_rest_request(data: dict) -> bytes:
    """JSON serializace + HTTP overhead."""
    headers = b"HTTP/1.1 200 OK\r\nContent-Type: application/json\r\n\r\n"
    body    = json.dumps(data).encode()
    return headers + body

def simuluj_grpc_request(data: dict) -> bytes:
    """Protobuf serializace + HTTP/2 framing."""
    payload = pb.serialize(data)
    # gRPC frame: 1B komprese + 4B délka + payload
    return bytes([0]) + struct.pack(">I", len(payload)) + payload

data = {"id": 1, "jmeno": "Míša Nováková", "vek": 15, "body": 87.5,
        "email": "misa@example.com", "predmet": "matematika"}

N = 100_000
t0 = time.perf_counter()
for _ in range(N):
    simuluj_rest_request(data)
t_rest = time.perf_counter() - t0

t0 = time.perf_counter()
for _ in range(N):
    simuluj_grpc_request(data)
t_grpc = time.perf_counter() - t0

rest_size = len(simuluj_rest_request(data))
grpc_size = len(simuluj_grpc_request(data))

print(f"  {N:,} serializací:")
print(f"  REST (JSON):   {t_rest*1000:.0f}ms  {rest_size}B na zprávu")
print(f"  gRPC (proto):  {t_grpc*1000:.0f}ms  {grpc_size}B na zprávu")
print(f"  Speedup:       {t_rest/t_grpc:.1f}×  Komprese: {(1-grpc_size/rest_size)*100:.0f}%")


# ══════════════════════════════════════════════════════════════
# ČÁST 4: Produkční kód
# ══════════════════════════════════════════════════════════════

print("""
=== Produkční gRPC s grpcio ===

# 1. Definuj .proto soubor (kurz.proto)
# 2. Zkompiluj: python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. kurz.proto
# 3. Implementuj servicer:

import grpc
import kurz_pb2
import kurz_pb2_grpc

class StudentServicer(kurz_pb2_grpc.StudentServiceServicer):
    def GetStudent(self, request, context):
        student = db.get(request.id)
        if not student:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details(f"Student {request.id} nenalezen")
            return kurz_pb2.StudentResponse()
        return kurz_pb2.StudentResponse(**student)

    def ListStudents(self, request, context):
        for student in db.values():
            if student["body"] >= request.min_body:
                yield kurz_pb2.StudentResponse(**student)

# 4. Spusť server:
def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    kurz_pb2_grpc.add_StudentServiceServicer_to_server(StudentServicer(), server)
    server.add_insecure_port("[::]:50051")
    server.start()
    server.wait_for_termination()

# 5. Klient:
with grpc.insecure_channel("localhost:50051") as channel:
    stub = kurz_pb2_grpc.StudentServiceStub(channel)
    student = stub.GetStudent(kurz_pb2.StudentRequest(id=1))
    print(student.jmeno)

# gRPC interceptory (middleware):
class LoggingInterceptor(grpc.ServerInterceptor):
    def intercept_service(self, continuation, handler_call_details):
        print(f"Call: {handler_call_details.method}")
        return continuation(handler_call_details)
""")

# TVOJE ÚLOHA:
# 1. Přidej do StudentServiceServicer metodu DeleteStudent s chybou NOT_FOUND.
# 2. Napiš gRPC interceptor pro měření latence každého volání.
# 3. Implementuj client-side load balancing přes více GrpcChannel instancí.
