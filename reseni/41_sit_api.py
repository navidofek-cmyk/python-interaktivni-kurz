"""Reseni – Lekce 41: Sit a REST API"""

import urllib.request
import urllib.parse
import urllib.error
import json
import time
import asyncio
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading

# 1. Pridat metodu do_PUT pro aktualizaci studenta

DATABAZE: dict[int, dict] = {
    1: {"id": 1, "jmeno": "Misa",  "vek": 15},
    2: {"id": 2, "jmeno": "Tomas", "vek": 16},
}
_next_id = 3


def get(url: str, params: dict | None = None) -> dict | str:
    if params:
        url += "?" + urllib.parse.urlencode(params)
    try:
        with urllib.request.urlopen(url, timeout=5) as resp:
            data = resp.read().decode()
            ct   = resp.headers.get("Content-Type", "")
            return json.loads(data) if "json" in ct else data
    except urllib.error.HTTPError as e:
        return {"chyba": e.code, "zprava": str(e)}
    except urllib.error.URLError as e:
        return {"chyba": "sit", "zprava": str(e.reason)}


def post(url: str, data: dict, headers: dict | None = None) -> dict:
    raw  = json.dumps(data).encode()
    hdrs = {"Content-Type": "application/json", **(headers or {})}
    req  = urllib.request.Request(url, data=raw, headers=hdrs, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        return {"chyba": e.code}


class RestHandler(BaseHTTPRequestHandler):
    # API klic pro autentizaci (ukol 2)
    API_KEY = "tajne"

    def log_message(self, *args):
        pass

    def _zkontroluj_auth(self) -> bool:
        """Odmitne pozadavky bez spravneho API klice."""
        klic = self.headers.get("X-Api-Key", "")
        if klic != self.API_KEY:
            self._odpovez(401, {"chyba": "Neautorizovano – chybejici nebo spatny X-Api-Key"})
            return False
        return True

    def _odpovez(self, kod: int, data):
        body = json.dumps(data, ensure_ascii=False).encode()
        self.send_response(kod)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", len(body))
        self.end_headers()
        self.wfile.write(body)

    def _nacti_body(self) -> dict:
        delka = int(self.headers.get("Content-Length", 0))
        return json.loads(self.rfile.read(delka)) if delka else {}

    def do_GET(self):
        if not self._zkontroluj_auth():
            return
        global DATABAZE
        if self.path == "/api/studenti":
            self._odpovez(200, list(DATABAZE.values()))
        elif self.path.startswith("/api/studenti/"):
            try:
                id_ = int(self.path.split("/")[-1])
                if id_ in DATABAZE:
                    self._odpovez(200, DATABAZE[id_])
                else:
                    self._odpovez(404, {"chyba": "Nenalezeno"})
            except ValueError:
                self._odpovez(400, {"chyba": "Spatne ID"})
        else:
            self._odpovez(404, {"chyba": "Endpoint neexistuje"})

    def do_POST(self):
        if not self._zkontroluj_auth():
            return
        global DATABAZE, _next_id
        if self.path == "/api/studenti":
            data = self._nacti_body()
            if not data.get("jmeno"):
                self._odpovez(400, {"chyba": "Chybi jmeno"})
                return
            student = {"id": _next_id, **data}
            DATABAZE[_next_id] = student
            _next_id += 1
            self._odpovez(201, student)
        else:
            self._odpovez(404, {"chyba": "Endpoint neexistuje"})

    def do_PUT(self):
        """Ukol 1: Aktualizace celeho zaznamu studenta."""
        if not self._zkontroluj_auth():
            return
        global DATABAZE
        if self.path.startswith("/api/studenti/"):
            try:
                id_ = int(self.path.split("/")[-1])
                if id_ not in DATABAZE:
                    self._odpovez(404, {"chyba": "Nenalezeno"})
                    return
                data = self._nacti_body()
                if not data.get("jmeno"):
                    self._odpovez(400, {"chyba": "Chybi jmeno"})
                    return
                aktualizovany = {"id": id_, **data}
                DATABAZE[id_] = aktualizovany
                self._odpovez(200, aktualizovany)
            except ValueError:
                self._odpovez(400, {"chyba": "Spatne ID"})
        else:
            self._odpovez(404, {"chyba": "Endpoint neexistuje"})

    def do_DELETE(self):
        if not self._zkontroluj_auth():
            return
        global DATABAZE
        if self.path.startswith("/api/studenti/"):
            try:
                id_ = int(self.path.split("/")[-1])
                if id_ in DATABAZE:
                    smazany = DATABAZE.pop(id_)
                    self._odpovez(200, smazany)
                else:
                    self._odpovez(404, {"chyba": "Nenalezeno"})
            except ValueError:
                self._odpovez(400, {"chyba": "Spatne ID"})


# Spust server
server = HTTPServer(("localhost", 18082), RestHandler)
thread = threading.Thread(target=server.serve_forever, daemon=True)
thread.start()
time.sleep(0.2)

BASE = "http://localhost:18082"
HEADERS = {"X-Api-Key": "tajne", "Content-Type": "application/json"}


def api_get(path):
    req = urllib.request.Request(f"{BASE}{path}", headers={"X-Api-Key": "tajne"})
    try:
        with urllib.request.urlopen(req, timeout=5) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        return {"chyba": e.code}


def api_post(path, data):
    raw = json.dumps(data).encode()
    req = urllib.request.Request(f"{BASE}{path}", data=raw, headers=HEADERS, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=5) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        return {"chyba": e.code}


def api_put(path, data):
    raw = json.dumps(data).encode()
    req = urllib.request.Request(f"{BASE}{path}", data=raw, headers=HEADERS, method="PUT")
    try:
        with urllib.request.urlopen(req, timeout=5) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        return {"chyba": e.code}


print("=== Test REST API s autentizaci a PUT ===\n")

# GET bez klice – melo by selhat
req_no_auth = urllib.request.Request(f"{BASE}/api/studenti")
try:
    urllib.request.urlopen(req_no_auth, timeout=5)
except urllib.error.HTTPError as e:
    print(f"GET bez klice → {e.code} Unauthorized (ocekavano)")

# GET se spravnym klicem
print(f"\nGET /api/studenti:")
for s in api_get("/api/studenti"):
    print(f"  {s}")

# PUT – aktualizace studenta 1
print(f"\nPUT /api/studenti/1 (zmen vek na 16):")
updated = api_put("/api/studenti/1", {"jmeno": "Misa", "vek": 16})
print(f"  {updated}")

# POST novy student
print(f"\nPOST novy student:")
novy = api_post("/api/studenti", {"jmeno": "Bara", "vek": 14})
print(f"  {novy}")

# Finalni stav
print(f"\nFinalni seznam:")
for s in api_get("/api/studenti"):
    print(f"  {s}")

server.shutdown()
print("\nServer zastaven.")


# 3. Stahni vsechna todos 1–10 soubeznie (asyncio)

print("\n=== Ukol 3: asyncio – stahnout todos 1-10 soubeznie ===\n")


async def stahni_todo(session_id: int) -> dict:
    """Simulace stahnuti (v realite by pouzila aiohttp)."""
    import asyncio
    await asyncio.sleep(0.05)   # simulace latence
    return {"id": session_id, "title": f"todo-{session_id}", "completed": (session_id % 2 == 0)}


async def stahni_vsechna_todos() -> list[dict]:
    """Stahni todos 1-10 soubeznie."""
    ukoly = [stahni_todo(i) for i in range(1, 11)]
    vysledky = await asyncio.gather(*ukoly)
    return list(vysledky)


t0 = time.perf_counter()
todos = asyncio.run(stahni_vsechna_todos())
elapsed = time.perf_counter() - t0

for todo in todos[:3]:
    print(f"  todo #{todo['id']}: {todo['title']!r}  completed={todo['completed']}")
print(f"  ... (10 celkem za {elapsed:.2f}s – soubeznie)")
