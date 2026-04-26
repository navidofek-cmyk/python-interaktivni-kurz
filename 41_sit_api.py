"""
LEKCE 41: Síť a REST API
==========================
HTTP = protokol webu. REST API = způsob jak si programy povídají přes HTTP.

urllib  – vestavěný, žádná instalace
requests – populárnější, čitelnější (pip install requests)

HTTP metody:
  GET    – načti data
  POST   – pošli/vytvoř data
  PUT    – nahraď celý záznam
  PATCH  – uprav část záznamu
  DELETE – smaž

Status kódy:
  2xx – OK   (200 OK, 201 Created, 204 No Content)
  4xx – Chyba klienta  (400 Bad Request, 404 Not Found, 401 Unauthorized)
  5xx – Chyba serveru  (500 Internal Server Error)
"""

import urllib.request
import urllib.parse
import urllib.error
import json
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading

# ══════════════════════════════════════════════════════════════
# ČÁST 1: urllib – bez závislostí
# ══════════════════════════════════════════════════════════════

print("=== urllib – vestavěný HTTP klient ===\n")

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
        return {"chyba": "síť", "zprava": str(e.reason)}

def post(url: str, data: dict, headers: dict | None = None) -> dict:
    raw     = json.dumps(data).encode()
    hdrs    = {"Content-Type": "application/json", **(headers or {})}
    req     = urllib.request.Request(url, data=raw, headers=hdrs, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        return {"chyba": e.code}

# Veřejné demo API
print("JSONPlaceholder – veřejné testovací API:")

todo = get("https://jsonplaceholder.typicode.com/todos/1")
print(f"  TODO #{todo.get('id')}: {todo.get('title')!r}  hotovo={todo.get('completed')}")

user = get("https://jsonplaceholder.typicode.com/users/1")
print(f"  User: {user.get('name')} z {user.get('address',{}).get('city')}")

posts = get("https://jsonplaceholder.typicode.com/posts", {"userId": 1, "_limit": 3})
if isinstance(posts, list):
    for p in posts:
        print(f"  Post: {p['title'][:50]}")

# POST
novy = post("https://jsonplaceholder.typicode.com/posts", {
    "title": "Moje první API volání",
    "body":  "Python to zvládl!",
    "userId": 1,
})
print(f"\n  POST → nový post id={novy.get('id')}: {novy.get('title')!r}")


# ══════════════════════════════════════════════════════════════
# ČÁST 2: VLASTNÍ HTTP SERVER
# ══════════════════════════════════════════════════════════════

print("\n=== Vlastní REST API server ===\n")

# In-memory databáze
DATABAZE: dict[int, dict] = {
    1: {"id": 1, "jmeno": "Míša",  "vek": 15},
    2: {"id": 2, "jmeno": "Tomáš", "vek": 16},
}
_next_id = 3

class RestHandler(BaseHTTPRequestHandler):
    """Jednoduchý REST handler pro /api/studenti"""

    def log_message(self, *args):
        pass   # potlač výchozí logování

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
                self._odpovez(400, {"chyba": "Špatné ID"})
        else:
            self._odpovez(404, {"chyba": "Endpoint neexistuje"})

    def do_POST(self):
        global DATABAZE, _next_id
        if self.path == "/api/studenti":
            data = self._nacti_body()
            if not data.get("jmeno"):
                self._odpovez(400, {"chyba": "Chybí jmeno"})
                return
            student = {"id": _next_id, **data}
            DATABAZE[_next_id] = student
            _next_id += 1
            self._odpovez(201, student)
        else:
            self._odpovez(404, {"chyba": "Endpoint neexistuje"})

    def do_DELETE(self):
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
                self._odpovez(400, {"chyba": "Špatné ID"})

# Spusť server v background threadu
server = HTTPServer(("localhost", 18080), RestHandler)
thread = threading.Thread(target=server.serve_forever, daemon=True)
thread.start()
time.sleep(0.2)
print("Server běží na http://localhost:18080\n")

# ── Klient který volá náš server ─────────────────────────────
BASE = "http://localhost:18080"

def api_get(path):
    return get(f"{BASE}{path}")

def api_post(path, data):
    return post(f"{BASE}{path}", data)

def api_delete(path):
    req = urllib.request.Request(f"{BASE}{path}", method="DELETE")
    try:
        with urllib.request.urlopen(req, timeout=5) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        return {"chyba": e.code}

# GET všichni
print("GET /api/studenti:")
for s in api_get("/api/studenti"):
    print(f"  {s}")

# GET jeden
print(f"\nGET /api/studenti/1:")
print(f"  {api_get('/api/studenti/1')}")

# POST nový
print(f"\nPOST nový student:")
novy = api_post("/api/studenti", {"jmeno": "Bára", "vek": 14})
print(f"  Vytvořen: {novy}")

# GET neexistující
print(f"\nGET /api/studenti/999:")
print(f"  {api_get('/api/studenti/999')}")

# DELETE
print(f"\nDELETE /api/studenti/2:")
print(f"  {api_delete('/api/studenti/2')}")

# Finální stav
print(f"\nFinální seznam:")
for s in api_get("/api/studenti"):
    print(f"  {s}")

server.shutdown()
print("\nServer zastaven.")

# ══════════════════════════════════════════════════════════════
# ČÁST 3: WEBSOCKET-LIKE – Server-Sent Events (ukázka konceptu)
# ══════════════════════════════════════════════════════════════

print("\n=== Retry a exponential backoff ===\n")

import random

def volej_s_retry(url: str, max_pokusy: int = 3, zakladni_zpozdeni: float = 0.5):
    """Zkusí volání max_pokusy-krát s exponenciálním zpožděním."""
    for pokus in range(1, max_pokusy + 1):
        try:
            vysledek = get(url)
            print(f"  Pokus {pokus}: OK")
            return vysledek
        except Exception as e:
            zpozdeni = zakladni_zpozdeni * (2 ** (pokus - 1)) + random.uniform(0, 0.1)
            print(f"  Pokus {pokus}: chyba – čekám {zpozdeni:.2f}s")
            if pokus < max_pokusy:
                time.sleep(zpozdeni)
    raise RuntimeError(f"Selhalo po {max_pokusy} pokusech")

data = volej_s_retry("https://jsonplaceholder.typicode.com/todos/1")
print(f"  Výsledek: {data.get('title')!r}")

# TVOJE ÚLOHA:
# 1. Přidaj do RestHandler metodu do_PUT pro aktualizaci studenta.
# 2. Přidej autentizaci: server odmítne požadavky bez hlavičky "X-Api-Key: tajne".
# 3. Napiš funkci stahni_vsechna_todos() která stáhne todos 1-10 souběžně (asyncio).
