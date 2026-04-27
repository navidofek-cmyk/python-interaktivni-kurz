"""
LEKCE 62: WebSockets – real-time komunikace
=============================================
pip install websockets

HTTP = požádej → odpověď → konec spojení.
WebSocket = trvalé obousměrné spojení.

Kdy WebSocket:
  - Chat aplikace
  - Live notifikace (ceny akcií, skóre)
  - Kolaborativní editace (Google Docs)
  - Online hry
  - Monitoring dashboardy

Tato lekce spustí WS server + klient ve stejném procesu
pomocí asyncio – žádný browser potřeba.
"""

import asyncio
import json
import time
import random
from datetime import datetime
from collections import defaultdict

try:
    import websockets
    from websockets.server import WebSocketServerProtocol
    WS_OK = True
except ImportError:
    print("websockets není nainstalováno: pip install websockets")
    WS_OK = False

if not WS_OK:
    exit()

# ══════════════════════════════════════════════════════════════
# ČÁST 1: Echo server
# ══════════════════════════════════════════════════════════════

print("=== Echo WebSocket server ===\n")

async def echo_handler(ws: WebSocketServerProtocol):
    print(f"  [server] Připojeno: {ws.remote_address}")
    async for zprava in ws:
        print(f"  [server] Přijato: {zprava!r}")
        odpoved = f"Echo: {zprava}"
        await ws.send(odpoved)
    print(f"  [server] Odpojeno")

async def echo_klient(uri: str):
    async with websockets.connect(uri) as ws:
        for text in ["Ahoj!", "Python", "WebSocket"]:
            await ws.send(text)
            odpoved = await ws.recv()
            print(f"  [klient] {text!r} → {odpoved!r}")

async def demo_echo():
    async with websockets.serve(echo_handler, "localhost", 8765):
        await echo_klient("ws://localhost:8765")

asyncio.run(demo_echo())


# ══════════════════════════════════════════════════════════════
# ČÁST 2: Chat server s místnostmi
# ══════════════════════════════════════════════════════════════

print("\n=== Chat server s místnostmi ===\n")

class ChatServer:
    def __init__(self):
        # místnost → množina klientů
        self.mistnosti: dict[str, set] = defaultdict(set)
        self.uzivatelska_jmena: dict = {}

    async def pripoj(self, ws: WebSocketServerProtocol, mistnost: str, jmeno: str):
        self.mistnosti[mistnost].add(ws)
        self.uzivatelska_jmena[ws] = jmeno
        await self.broadcast(mistnost, f"🟢 {jmeno} vstoupil/a do místnosti", ws)
        print(f"  [chat] {jmeno} → #{mistnost} ({len(self.mistnosti[mistnost])} uživatelů)")

    async def odpoj(self, ws: WebSocketServerProtocol, mistnost: str):
        jmeno = self.uzivatelska_jmena.pop(ws, "?")
        self.mistnosti[mistnost].discard(ws)
        await self.broadcast(mistnost, f"🔴 {jmeno} opustil/a místnost")
        print(f"  [chat] {jmeno} ← #{mistnost}")

    async def broadcast(self, mistnost: str, text: str, vyjimka=None):
        """Rozešle zprávu všem v místnosti."""
        msg = json.dumps({"cas": datetime.now().strftime("%H:%M:%S"), "text": text})
        klienti = self.mistnosti[mistnost] - ({vyjimka} if vyjimka else set())
        if klienti:
            await asyncio.gather(*[k.send(msg) for k in klienti],
                                  return_exceptions=True)

    async def handler(self, ws: WebSocketServerProtocol):
        # První zpráva = přihlášení {mistnost, jmeno}
        raw = await ws.recv()
        info = json.loads(raw)
        mistnost = info.get("mistnost", "general")
        jmeno    = info.get("jmeno", f"user_{id(ws) % 1000}")

        await self.pripoj(ws, mistnost, jmeno)
        try:
            async for raw in ws:
                data = json.loads(raw)
                text = f"{jmeno}: {data['text']}"
                await self.broadcast(mistnost, text)
        finally:
            await self.odpoj(ws, mistnost)

chat = ChatServer()

async def chat_klient(uri: str, jmeno: str, mistnost: str, zpravy: list[str]):
    async with websockets.connect(uri) as ws:
        await ws.send(json.dumps({"jmeno": jmeno, "mistnost": mistnost}))
        for zprava in zpravy:
            await asyncio.sleep(0.1)
            await ws.send(json.dumps({"text": zprava}))
        # Počkej na příchozí zprávy
        try:
            async with asyncio.timeout(0.5):
                async for raw in ws:
                    data = json.loads(raw)
                    print(f"  [{jmeno}] přijato: {data['text']!r}")
        except asyncio.TimeoutError:
            pass

async def demo_chat():
    async with websockets.serve(chat.handler, "localhost", 8766):
        await asyncio.gather(
            chat_klient("ws://localhost:8766", "Míša",  "python", ["Ahoj!", "Jak se máš?"]),
            chat_klient("ws://localhost:8766", "Tomáš", "python", ["Skvěle!", "Učíme se WS"]),
            chat_klient("ws://localhost:8766", "Bára",  "java",   ["Jdu jinam"]),
        )

asyncio.run(demo_chat())


# ══════════════════════════════════════════════════════════════
# ČÁST 3: Live data stream (akcie, senzory)
# ══════════════════════════════════════════════════════════════

print("\n=== Live data stream ===\n")

async def stream_server(ws: WebSocketServerProtocol):
    """Posílá simulovaná data akcií každých 100ms."""
    akcie = {"PYTH": 150.0, "RUST": 89.5, "GO": 42.3}
    try:
        for _ in range(20):  # 20 ticků
            for ticker, cena in akcie.items():
                zmena = random.gauss(0, 0.5)
                akcie[ticker] = max(1.0, cena + zmena)

            data = {
                "cas":  datetime.now().strftime("%H:%M:%S.%f")[:12],
                "akcie": {t: round(c, 2) for t, c in akcie.items()},
            }
            await ws.send(json.dumps(data))
            await asyncio.sleep(0.05)
    except websockets.exceptions.ConnectionClosed:
        pass

async def stream_klient(uri: str, pocet: int = 5):
    async with websockets.connect(uri) as ws:
        print(f"  {'Čas':<13} {'PYTH':>8} {'RUST':>8} {'GO':>8}")
        print(f"  {'─'*40}")
        i = 0
        async for raw in ws:
            if i >= pocet:
                break
            data = json.loads(raw)
            a = data["akcie"]
            print(f"  {data['cas']:<13} {a['PYTH']:>8.2f} {a['RUST']:>8.2f} {a['GO']:>8.2f}")
            i += 1

async def demo_stream():
    async with websockets.serve(stream_server, "localhost", 8767):
        await stream_klient("ws://localhost:8767")

asyncio.run(demo_stream())


# ══════════════════════════════════════════════════════════════
# ČÁST 4: WebSocket + FastAPI
# ══════════════════════════════════════════════════════════════

print("\n=== WebSocket v FastAPI (kód pro referenci) ===")
print("""
from fastapi import FastAPI, WebSocket
from fastapi.websockets import WebSocketDisconnect

app = FastAPI()
pripojeni: list[WebSocket] = []

@app.websocket("/ws")
async def ws_endpoint(ws: WebSocket):
    await ws.accept()
    pripojeni.append(ws)
    try:
        while True:
            data = await ws.receive_text()
            # Rozešli všem
            for klient in pripojeni:
                await klient.send_text(f"Broadcast: {data}")
    except WebSocketDisconnect:
        pripojeni.remove(ws)

# JavaScript klient:
# const ws = new WebSocket("ws://localhost:8000/ws");
# ws.onmessage = e => console.log(e.data);
# ws.send("Ahoj!");
""")

# TVOJE ÚLOHA:
# 1. Přidej do chat serveru soukromé zprávy: /msg <jmeno> <text>.
# 2. Přidej reconnect logiku na straně klienta (exponential backoff).
# 3. Napiš WebSocket proxy – přeposílá zprávy mezi dvěma servery.
