"""Reseni – Lekce 62: WebSockets"""

# vyžaduje: pip install websockets

import asyncio
import json
import time
import random
from datetime import datetime
from collections import defaultdict


# Simulace WebSocket bez externi knihovny (pro spusteni bez depsů)
# Produkčni kod pouziva 'websockets' nebo FastAPI WebSocket

print("=== Simulace WebSocket chat serveru ===\n")


class SimWsKlient:
    """Simulace WebSocket klienta."""

    def __init__(self, jmeno: str):
        self.jmeno = jmeno
        self._inbox: asyncio.Queue[str] = asyncio.Queue()
        self._outbox: asyncio.Queue[str] = asyncio.Queue()
        self.odpojeno = False

    async def send(self, zprava: str) -> None:
        await self._inbox.put(zprava)

    async def recv(self) -> str:
        return await asyncio.wait_for(self._outbox.get(), timeout=2.0)

    async def posli_serveru(self, zprava: str) -> None:
        await self._outbox.put(zprava)

    async def nacti_z_serveru(self) -> str | None:
        try:
            return await asyncio.wait_for(self._inbox.get(), timeout=0.5)
        except asyncio.TimeoutError:
            return None


class ChatServer:
    """Simulace chat serveru s podporou soukromych zprav."""

    def __init__(self):
        self._klienti: dict[str, SimWsKlient] = {}

    def pripoj(self, klient: SimWsKlient) -> None:
        self._klienti[klient.jmeno] = klient
        print(f"  [Server] {klient.jmeno} se pripojil")

    def odpoj(self, klient: SimWsKlient) -> None:
        self._klienti.pop(klient.jmeno, None)
        print(f"  [Server] {klient.jmeno} se odpojil")

    async def zpracuj_zpravu(self, odesilatel: SimWsKlient, raw: str) -> None:
        """Zpracuje zpravu – detekuje soukrome zpravy /msg."""
        try:
            zprava = json.loads(raw)
        except json.JSONDecodeError:
            zprava = {"type": "chat", "text": raw}

        typ  = zprava.get("type", "chat")
        text = zprava.get("text", "")

        # Ukol 1: Soukrome zpravy /msg <jmeno> <text>
        if text.startswith("/msg "):
            casti = text[5:].split(" ", 1)
            if len(casti) == 2:
                prijemce_jmeno, soukroma_zprava = casti
                await self._soukroma_zprava(odesilatel.jmeno, prijemce_jmeno, soukroma_zprava)
            else:
                await odesilatel.send(json.dumps({
                    "typ": "chyba", "text": "Format: /msg <jmeno> <zprava>"
                }))

        elif typ == "chat":
            # Broadcast vsem
            zprava_json = json.dumps({
                "typ":   "chat",
                "od":    odesilatel.jmeno,
                "text":  text,
                "cas":   datetime.now().strftime("%H:%M:%S"),
            })
            await self._broadcast(zprava_json, vyjma=None)

    async def _soukroma_zprava(self, od: str, komu: str, text: str) -> None:
        """Posle soukromou zpravu pouze jednomu klientovi."""
        prijemce = self._klienti.get(komu)
        odesilatel = self._klienti.get(od)
        zprava = json.dumps({"typ": "soukroma", "od": od, "text": text})

        if prijemce:
            await prijemce.send(zprava)
            # Potvrzeni odesilateli
            if odesilatel:
                await odesilatel.send(json.dumps({
                    "typ": "soukroma_sent", "komu": komu, "text": text
                }))
        else:
            if odesilatel:
                await odesilatel.send(json.dumps({
                    "typ": "chyba", "text": f"Uzivatel '{komu}' nenalezen"
                }))

    async def _broadcast(self, zprava_json: str, vyjma: str | None = None) -> None:
        """Rozesle zpravu vsem klientum (volitelne vyjma jednoho)."""
        for jmeno, klient in self._klienti.items():
            if jmeno != vyjma:
                await klient.send(zprava_json)


async def demo_chat():
    server = ChatServer()

    # Vytvor klienty
    misa  = SimWsKlient("Misa")
    tomas = SimWsKlient("Tomas")
    bara  = SimWsKlient("Bara")

    for k in [misa, tomas, bara]:
        server.pripoj(k)

    print("\n--- Verejne zpravy ---")

    # Misa posle verejnou zpravu
    await server.zpracuj_zpravu(misa, json.dumps({"type": "chat", "text": "Ahoj vsichni!"}))

    # Precti zpravy pro vsechny
    for klient in [misa, tomas, bara]:
        z = await klient.nacti_z_serveru()
        if z:
            data = json.loads(z)
            print(f"  [{klient.jmeno}] obdrzel: {data.get('od','?')}: {data.get('text','')}")

    print("\n--- Soukrome zpravy (/msg) ---")

    # Tomas posle soukromou zpravu Mise
    await server.zpracuj_zpravu(tomas, json.dumps({"type": "chat", "text": "/msg Misa Ahoj Miso!"}))

    # Precti zpravy
    misa_z = await misa.nacti_z_serveru()
    tomas_z = await tomas.nacti_z_serveru()
    bara_z = await bara.nacti_z_serveru()   # nema dostat nic

    if misa_z:
        d = json.loads(misa_z)
        print(f"  [Misa] soukroma od {d.get('od','?')}: {d.get('text','')}")
    if tomas_z:
        d = json.loads(tomas_z)
        print(f"  [Tomas] potvrzeni: → {d.get('komu','?')}: {d.get('text','')}")
    if bara_z:
        print(f"  [CHYBA] Bara dostala soukromou zpravu: {bara_z}")
    else:
        print(f"  [Bara] zadna zprava (spravne – soukroma)")

    print("\n--- Neexistujici prijemce ---")
    await server.zpracuj_zpravu(misa, json.dumps({"type": "chat", "text": "/msg Neexistujici Ahoj!"}))
    err = await misa.nacti_z_serveru()
    if err:
        d = json.loads(err)
        print(f"  [Misa] {d.get('typ','?')}: {d.get('text','')}")


asyncio.run(demo_chat())


# 2. Reconnect logika na strane klienta (exponential backoff)

print("\n=== Ukol 2: Reconnect s exponential backoff ===\n")


class ReconnectClient:
    """Klient s automatickym reconnectem a exponential backoff."""

    def __init__(self, url: str, max_retries: int = 5, base_delay: float = 0.1):
        self.url = url
        self.max_retries = max_retries
        self.base_delay  = base_delay

    async def connect_s_retry(self) -> bool:
        """Pokusi se pripojit s exponentialnim backoffem."""
        for pokus in range(1, self.max_retries + 1):
            try:
                print(f"  Pokus {pokus}/{self.max_retries}: pripojuji na {self.url}")
                # Simulace: prvni 2 pokusy selzou
                if pokus < 3:
                    raise ConnectionError("Server nedostupny (simulace)")
                # Uspech
                print(f"  Pripojeno! (po {pokus} pokusech)")
                return True
            except ConnectionError as e:
                zpozdeni = self.base_delay * (2 ** (pokus - 1)) + random.uniform(0, 0.05)
                print(f"  Selhal ({e}) – cekam {zpozdeni:.2f}s")
                if pokus < self.max_retries:
                    await asyncio.sleep(zpozdeni)
        print(f"  Vzdavam to po {self.max_retries} pokusech")
        return False


async def demo_reconnect():
    klient = ReconnectClient("ws://localhost:8765", max_retries=5)
    ok = await klient.connect_s_retry()
    print(f"  Vysledek: {'pripojeno' if ok else 'selhalo'}")


asyncio.run(demo_reconnect())


# 3. WebSocket proxy – produkční kód

print("\n=== Ukol 3: WebSocket proxy (produkční kod) ===\n")

# vyžaduje: pip install websockets

PROXY_KOD = """\
# vyžaduje: pip install websockets

import asyncio
import websockets

async def ws_proxy(ws_klient, cil_url: str):
    \"\"\"Presmeruje zpravy mezi klientem a cilovym serverem.\"\"\"
    async with websockets.connect(cil_url) as ws_cil:
        async def klient_na_cil():
            async for zprava in ws_klient:
                await ws_cil.send(zprava)

        async def cil_na_klient():
            async for zprava in ws_cil:
                await ws_klient.send(zprava)

        await asyncio.gather(klient_na_cil(), cil_na_klient())


async def proxy_server(port: int = 8766, cil: str = "ws://backend:8765"):
    async with websockets.serve(
        lambda ws: ws_proxy(ws, cil),
        "0.0.0.0", port
    ):
        print(f"WS Proxy bezi na :{port}, presmeruje na {cil}")
        await asyncio.Future()   # bezi navzdy


asyncio.run(proxy_server())
"""

print(PROXY_KOD)
