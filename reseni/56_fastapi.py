"""Reseni – Lekce 56: FastAPI"""

# vyžaduje: pip install fastapi uvicorn httpx

try:
    from fastapi import FastAPI, HTTPException, Depends, Header
    from fastapi.testclient import TestClient
    from pydantic import BaseModel, Field
    FASTAPI_OK = True
except ImportError:
    print("FastAPI neni nainstalovano: pip install fastapi uvicorn httpx")
    FASTAPI_OK = False

import json
from pathlib import Path
from typing import Annotated

if not FASTAPI_OK:
    print("""
# Ukazka kodu (pro spusteni: pip install fastapi uvicorn httpx)

from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel, Field

app = FastAPI()
DB = {}

class Student(BaseModel):
    jmeno: str
    vek: int = Field(ge=0, le=150)
    body: float = Field(ge=0, le=100)

API_KEY = "tajne"

@app.get("/studenti/top/{n}")
def top_studenti(n: int):
    serazeni = sorted(DB.values(), key=lambda s: s["body"], reverse=True)
    return serazeni[:n]

@app.get("/studenti")
def seznam(x_api_key: str = Header(None)):
    if x_api_key != API_KEY:
        raise HTTPException(401, "Neautorizovano")
    return list(DB.values())
""")
    exit()


# Databaze v pameti
DB: dict[int, dict] = {
    1: {"id": 1, "jmeno": "Misa",  "vek": 15, "body": 87.5},
    2: {"id": 2, "jmeno": "Tomas", "vek": 16, "body": 92.0},
    3: {"id": 3, "jmeno": "Bara",  "vek": 14, "body": 78.3},
    4: {"id": 4, "jmeno": "Ondra", "vek": 17, "body": 95.1},
    5: {"id": 5, "jmeno": "Klara", "vek": 15, "body": 65.0},
}
_next_id = 6

# Soubor pro persistenci (ukol 3)
DB_SOUBOR = Path("studenti_db.json")

API_KEY = "tajne"


class StudentVstup(BaseModel):
    jmeno: str = Field(min_length=2)
    vek:   int = Field(ge=0, le=150)
    body:  float = Field(ge=0, le=100)


class StudentOdpoved(StudentVstup):
    id: int


# Ukol 2: Zavislostnni funkce pro overeni API klice
def overit_api_klic(x_api_key: Annotated[str | None, Header()] = None) -> None:
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Neautorizovano – spatny nebo chybejici X-API-Key")


app = FastAPI(title="Python Kurz API", version="2.0")


# Ukol 3: Pomocna funkce pro persistenci
def uloz_db() -> None:
    """Ulozi databazi do JSON souboru."""
    DB_SOUBOR.write_text(
        json.dumps(list(DB.values()), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


# Endpointy bez autentizace
@app.get("/studenti", response_model=list[StudentOdpoved])
def seznam_studentu():
    return list(DB.values())


@app.get("/studenti/{student_id}", response_model=StudentOdpoved)
def get_student(student_id: int):
    if student_id not in DB:
        raise HTTPException(status_code=404, detail=f"Student {student_id} nenalezen")
    return DB[student_id]


# Ukol 1: GET /studenti/top/{n} – n studentu s nejvyssimi body
@app.get("/studenti/top/{n}", response_model=list[StudentOdpoved])
def top_studenti(n: int):
    """Vrati n studentu s nejvyssimi body."""
    if n < 1:
        raise HTTPException(status_code=400, detail="n musi byt alespon 1")
    serazeni = sorted(DB.values(), key=lambda s: s["body"], reverse=True)
    return serazeni[:n]


# Endpointy s autentizaci (ukol 2)
@app.post(
    "/studenti",
    response_model=StudentOdpoved,
    status_code=201,
    dependencies=[Depends(overit_api_klic)],
)
def vytvor_studenta(vstup: StudentVstup):
    global _next_id
    student = {"id": _next_id, **vstup.model_dump()}
    DB[_next_id] = student
    _next_id += 1
    uloz_db()  # ukol 3: persistuj
    return student


@app.put(
    "/studenti/{student_id}",
    response_model=StudentOdpoved,
    dependencies=[Depends(overit_api_klic)],
)
def aktualizuj_studenta(student_id: int, vstup: StudentVstup):
    if student_id not in DB:
        raise HTTPException(status_code=404, detail="Student nenalezen")
    student = {"id": student_id, **vstup.model_dump()}
    DB[student_id] = student
    uloz_db()
    return student


@app.delete(
    "/studenti/{student_id}",
    dependencies=[Depends(overit_api_klic)],
)
def smaz_studenta(student_id: int):
    if student_id not in DB:
        raise HTTPException(status_code=404, detail="Student nenalezen")
    smazany = DB.pop(student_id)
    uloz_db()
    return {"smazano": smazany}


# Testovani pres TestClient
def tiskni(popis: str, resp) -> None:
    print(f"\n{popis}")
    print(f"  Status: {resp.status_code}")
    try:
        data = resp.json()
        if isinstance(data, list):
            print(f"  Data: {len(data)} zaznamu")
            for item in data[:2]:
                print(f"    {item}")
        else:
            print(f"  Data: {data}")
    except Exception:
        print(f"  Telo: {resp.text[:100]}")


print("=== Test FastAPI endpointu ===")

with TestClient(app) as client:

    # Ukol 1: top N studentu
    tiskni("GET /studenti/top/3", client.get("/studenti/top/3"))

    # Ukol 2: Autentizace – bez klice
    tiskni("POST /studenti bez klice (401 ocekavano)",
           client.post("/studenti", json={"jmeno": "Test", "vek": 15, "body": 80.0}))

    # Ukol 2: Autentizace – se spravnym klicem
    tiskni("POST /studenti se spravnym X-API-Key",
           client.post("/studenti",
                       json={"jmeno": "Novy", "vek": 15, "body": 80.0},
                       headers={"X-API-Key": "tajne"}))

    # Ukol 3: Persistovana databaze
    tiskni("GET /studenti (po pridani)", client.get("/studenti"))

    # Smazat testovaci zaznam
    tiskni("DELETE /studenti/6 (se klicem)",
           client.delete("/studenti/6", headers={"X-API-Key": "tajne"}))

# Ukol 3: Zkontroluj soubor
if DB_SOUBOR.exists():
    print(f"\nPersistence: {DB_SOUBOR} obsahuje {len(json.loads(DB_SOUBOR.read_text()))} zaznamu")
    DB_SOUBOR.unlink()

print("""
Spusteni jako realny server:
  uvicorn 56_fastapi:app --reload --port 8000
  http://localhost:8000/docs

Websocket endpoint by bylo mozne pridat takto:
  from fastapi import WebSocket

  @app.websocket("/ws/live")
  async def ws_live(websocket: WebSocket):
      await websocket.accept()
      while True:
          data = await websocket.receive_text()
          await websocket.send_text(f"Echo: {data}")
""")
