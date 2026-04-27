"""
LEKCE 82: Síťové sokety – TCP/UDP server od nuly
==================================================
Vestavěné: socket, asyncio
Nemusíš instalovat nic.

Soket = endpoint síťového spojení.
Každé HTTP, WebSocket, SSH spojení je uvnitř TCP soket.

TCP vs UDP:
  TCP – spolehlivý, spojení (HTTP, SSH, databáze)
  UDP – rychlý, bez záruky doručení (DNS, hry, streaming)
"""

import socket
import threading
import asyncio
import json
import struct
import time
import os
from datetime import datetime

# ══════════════════════════════════════════════════════════════
# ČÁST 1: TCP echo server + klient
# ══════════════════════════════════════════════════════════════

print("=== TCP echo server + klient ===\n")

def tcp_server(port: int, max_spojeni: int = 3):
    """Jednoduchý TCP echo server."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as srv:
        srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        srv.bind(("localhost", port))
        srv.listen(5)
        srv.settimeout(2.0)   # timeout pro accept (aby se server dal vypnout)

        prijato = 0
        while prijato < max_spojeni:
            try:
                conn, addr = srv.accept()
            except socket.timeout:
                break
            with conn:
                data = conn.recv(1024)
                if data:
                    conn.sendall(b"Echo: " + data)
                    prijato += 1

PORT = 19876

# Spusť server v threadu
server_thread = threading.Thread(target=tcp_server, args=(PORT,), daemon=True)
server_thread.start()
time.sleep(0.1)

# Klient
def tcp_klient(zprava: str, port: int) -> str:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect(("localhost", port))
        s.sendall(zprava.encode("utf-8"))
        return s.recv(1024).decode("utf-8")

for zprava in ["Ahoj!", "Python sokety", "třetí zpráva"]:
    odpoved = tcp_klient(zprava, PORT)
    print(f"  → {zprava!r:25}  ←  {odpoved!r}")

server_thread.join(timeout=3)


# ══════════════════════════════════════════════════════════════
# ČÁST 2: Multi-client chat server
# ══════════════════════════════════════════════════════════════

print("\n=== Multi-client chat server ===\n")

class ChatServer:
    def __init__(self, port: int):
        self.port     = port
        self.klienti: dict[socket.socket, str] = {}
        self.zamek    = threading.Lock()

    def broadcast(self, zprava: str, vyjimka=None):
        with self.zamek:
            for klient in list(self.klienti):
                if klient != vyjimka:
                    try:
                        klient.sendall(zprava.encode("utf-8"))
                    except Exception:
                        self.klienti.pop(klient, None)

    def obsluha_klienta(self, conn: socket.socket, addr):
        jmeno = f"User_{addr[1]}"
        with self.zamek:
            self.klienti[conn] = jmeno
        self.broadcast(f"[{jmeno} se připojil]\n", conn)

        try:
            while True:
                data = conn.recv(1024)
                if not data:
                    break
                zprava = data.decode("utf-8").strip()
                if zprava.startswith("/jmeno "):
                    stare = jmeno
                    jmeno = zprava.split(" ", 1)[1]
                    with self.zamek:
                        self.klienti[conn] = jmeno
                    self.broadcast(f"[{stare} → {jmeno}]\n")
                else:
                    cas = datetime.now().strftime("%H:%M")
                    self.broadcast(f"[{cas}] {jmeno}: {zprava}\n")
        except Exception:
            pass
        finally:
            with self.zamek:
                self.klienti.pop(conn, None)
            conn.close()
            self.broadcast(f"[{jmeno} se odpojil]\n")

    def spust(self, max_klientu: int = 3):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as srv:
            srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            srv.bind(("localhost", self.port))
            srv.listen(10)
            srv.settimeout(2.0)
            prijato = 0
            while prijato < max_klientu:
                try:
                    conn, addr = srv.accept()
                    t = threading.Thread(
                        target=self.obsluha_klienta,
                        args=(conn, addr), daemon=True)
                    t.start()
                    prijato += 1
                except socket.timeout:
                    if prijato > 0:
                        break

CHAT_PORT = 19877
chat = ChatServer(CHAT_PORT)
ct   = threading.Thread(target=chat.spust, daemon=True)
ct.start()
time.sleep(0.1)

# Simulace klientů
def chat_klient(jmeno: str, zpravy: list[str]):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect(("localhost", CHAT_PORT))
        s.settimeout(0.5)
        s.sendall(f"/jmeno {jmeno}\n".encode())
        for z in zpravy:
            time.sleep(0.05)
            s.sendall(f"{z}\n".encode())
        time.sleep(0.1)

t1 = threading.Thread(target=chat_klient,
                       args=("Míša", ["Ahoj všichni!", "Jak se máte?"]))
t2 = threading.Thread(target=chat_klient,
                       args=("Tomáš", ["Ahoj Míšo!", "Super!"]))

t1.start(); t2.start()
t1.join();  t2.join()
time.sleep(0.3)

print("  Chat server demo dokončen")
print(f"  Připojeno klientů: {len(chat.klienti)}")


# ══════════════════════════════════════════════════════════════
# ČÁST 3: UDP server (DNS-like dotazy)
# ══════════════════════════════════════════════════════════════

print("\n=== UDP server ===\n")

UDP_PORT = 19878

def udp_server(port: int, max_zprav: int = 4):
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.bind(("localhost", port))
        s.settimeout(1.0)
        for _ in range(max_zprav):
            try:
                data, addr = s.recvfrom(1024)
                otazka = data.decode()
                odpoved = json.dumps({
                    "dotaz": otazka,
                    "ip": "192.168.1." + str(hash(otazka) % 254 + 1),
                    "ttl": 300,
                })
                s.sendto(odpoved.encode(), addr)
            except socket.timeout:
                break

def udp_klient(dotaz: str, port: int) -> dict:
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.settimeout(1.0)
        s.sendto(dotaz.encode(), ("localhost", port))
        data, _ = s.recvfrom(4096)
        return json.loads(data)

ut = threading.Thread(target=udp_server, args=(UDP_PORT,), daemon=True)
ut.start()
time.sleep(0.1)

for domena in ["python.org", "github.com", "example.cz"]:
    try:
        vysl = udp_klient(domena, UDP_PORT)
        print(f"  {domena:<20} → {vysl['ip']}")
    except socket.timeout:
        print(f"  {domena:<20} → timeout")


# ══════════════════════════════════════════════════════════════
# ČÁST 4: Async soket server (asyncio)
# ══════════════════════════════════════════════════════════════

print("\n=== Async TCP server (asyncio) ===\n")

ASYNC_PORT = 19879
prijate_async = []

async def async_obsluha(reader: asyncio.StreamReader,
                         writer: asyncio.StreamWriter):
    addr = writer.get_extra_info("peername")
    data = await reader.read(1024)
    if data:
        zprava = data.decode().strip()
        prijate_async.append(zprava)
        writer.write(f"OK: {zprava}\n".encode())
        await writer.drain()
    writer.close()

async def async_demo():
    # Server
    server = await asyncio.start_server(
        async_obsluha, "localhost", ASYNC_PORT)

    # Klienti
    async def klient(zprava: str):
        r, w = await asyncio.open_connection("localhost", ASYNC_PORT)
        w.write(zprava.encode())
        await w.drain()
        odpoved = await r.read(1024)
        w.close()
        return odpoved.decode().strip()

    async with server:
        # Spusť 3 klienty souběžně
        vysledky = await asyncio.gather(
            klient("první"),
            klient("druhý"),
            klient("třetí"),
        )
        for v in vysledky:
            print(f"  {v}")

asyncio.run(async_demo())


# ══════════════════════════════════════════════════════════════
# ČÁST 5: Binární protokol s struct
# ══════════════════════════════════════════════════════════════

print("\n=== Binární protokol ===\n")

# Vlastní protokol: [4B magic][2B verze][4B délka][N bajtů dat]
MAGIC   = b"PYTP"
VERZE   = 1

def zabal_zpravu(data: bytes) -> bytes:
    """Zabalí data do binárního rámce."""
    hlavicka = struct.pack(">4sHI", MAGIC, VERZE, len(data))
    return hlavicka + data

def rozbal_zpravu(raw: bytes) -> tuple[int, bytes]:
    """Rozbalí binární rámec."""
    hlavicka_vel = struct.calcsize(">4sHI")
    magic, verze, delka = struct.unpack(">4sHI", raw[:hlavicka_vel])
    assert magic == MAGIC, "Neplatné magic bytes"
    return verze, raw[hlavicka_vel:hlavicka_vel + delka]

# Demo
zprava = json.dumps({"cmd": "ping", "ts": time.time()}).encode()
ramec  = zabal_zpravu(zprava)
verze, rozbalena = rozbal_zpravu(ramec)

print(f"  Zpráva:    {len(zprava)} B")
print(f"  Rámec:     {len(ramec)} B  (+ {len(ramec)-len(zprava)}B hlavička)")
print(f"  Hex:       {ramec[:12].hex()} ...")
print(f"  Rozbaleno: {rozbalena.decode()[:60]}")

print("""
=== Přehled soketů ===

  TCP    socket.SOCK_STREAM    spolehlivý, spojení
  UDP    socket.SOCK_DGRAM     rychlý, bez záruky
  Unix   socket.AF_UNIX        lokální IPC (stejný počítač)

  asyncio.start_server()  → async TCP server (doporučeno pro produkci)
  socket (raw)            → maximální kontrola
  http.server             → HTTP server 1 řádkem: python -m http.server
  uvicorn + FastAPI       → produkční HTTP server (lekce 56)
""")

# TVOJE ÚLOHA:
# 1. Přidaj do chat serveru seznam příkazů: /seznam (vypíše připojené) /opust (odpojení).
# 2. Přidej šifrování: zprávy zašifruj AES klíčem (lekce 68 – cryptography).
# 3. Napiš load balancer: přijímá spojení a distribuuje je na 3 backend servery round-robin.
