"""
LEKCE 56: FastAPI – moderní REST API
======================================
pip install fastapi uvicorn

FastAPI = moderní web framework:
  - Automatická dokumentace (Swagger UI na /docs)
  - Validace přes Pydantic
  - Async od základu
  - Typová bezpečnost

Tato lekce vytvoří funkční API a spustí ho na pozadí.
Pak ho otestujeme přes urllib.

Reálné spuštění:
  uvicorn 56_fastapi:app --reload
  # Otevři: http://localhost:8000/docs
"""

try:
    import fastapi
    from fastapi import FastAPI, HTTPException, Depends, Query, Path as FPath
    from fastapi.testclient import TestClient
    from pydantic import BaseModel, Field
    FASTAPI_OK = True
except ImportError:
    print("FastAPI není nainstalováno: pip install fastapi uvicorn httpx")
    FASTAPI_OK = False

from datetime import datetime
from typing import Annotated
import json

# ══════════════════════════════════════════════════════════════
# MODELY
# ══════════════════════════════════════════════════════════════

if FASTAPI_OK:
    class StudentCreate(BaseModel):
        jmeno: str = Field(min_length=2, max_length=50)
        email: str = Field(pattern=r"^[^@]+@[^@]+\.[^@]+$")
        vek:   int = Field(ge=10, le=100)
        body:  float = Field(default=0.0, ge=0, le=100)

    class Student(StudentCreate):
        id:        int
        zapsano:   datetime = Field(default_factory=datetime.now)

        class Config:
            from_attributes = True

    class StudentUpdate(BaseModel):
        jmeno: str | None = None
        body:  float | None = Field(default=None, ge=0, le=100)
        vek:   int | None = None

    # ── In-memory databáze ────────────────────────────────────
    DB: dict[int, Student] = {}
    _next_id = 1

    def dalsi_id() -> int:
        global _next_id
        id_ = _next_id
        _next_id += 1
        return id_

    # Seed data
    for data in [
        {"jmeno": "Míša",  "email": "misa@k.cz",  "vek": 15, "body": 87.5},
        {"jmeno": "Tomáš", "email": "tomas@k.cz", "vek": 16, "body": 92.0},
        {"jmeno": "Bára",  "email": "bara@k.cz",  "vek": 14, "body": 78.3},
    ]:
        id_ = dalsi_id()
        DB[id_] = Student(id=id_, **data)


# ══════════════════════════════════════════════════════════════
# APLIKACE
# ══════════════════════════════════════════════════════════════

if FASTAPI_OK:
    app = FastAPI(
        title="Python Kurz API",
        description="REST API pro správu studentů – ukázkový kurz",
        version="1.0.0",
    )

    # ── Dependency injection ──────────────────────────────────
    def ziskej_studenta(student_id: int) -> Student:
        if student_id not in DB:
            raise HTTPException(status_code=404, detail=f"Student {student_id} nenalezen")
        return DB[student_id]

    # ── Endpointy ────────────────────────────────────────────

    @app.get("/", tags=["root"])
    async def root():
        return {"zprava": "Python Kurz API", "verze": "1.0.0", "studenti": len(DB)}

    @app.get("/studenti", response_model=list[Student], tags=["studenti"])
    async def seznam_studentu(
        min_body:  Annotated[float, Query(ge=0, le=100)] = 0,
        max_vek:   Annotated[int,   Query(ge=0)]         = 200,
        razeni:    str = "jmeno",
    ):
        """Vrátí seznam studentů s volitelným filtrováním a řazením."""
        vysledky = [
            s for s in DB.values()
            if s.body >= min_body and s.vek <= max_vek
        ]
        return sorted(vysledky, key=lambda s: getattr(s, razeni, s.jmeno))

    @app.get("/studenti/{student_id}", response_model=Student, tags=["studenti"])
    async def ziskej(student: Annotated[Student, Depends(ziskej_studenta)]):
        """Vrátí jednoho studenta podle ID."""
        return student

    @app.post("/studenti", response_model=Student, status_code=201, tags=["studenti"])
    async def vytvor_studenta(data: StudentCreate):
        """Vytvoří nového studenta."""
        # Unikátnost emailu
        if any(s.email == data.email for s in DB.values()):
            raise HTTPException(status_code=409, detail=f"Email {data.email} již existuje")
        id_ = dalsi_id()
        student = Student(id=id_, **data.model_dump())
        DB[id_] = student
        return student

    @app.patch("/studenti/{student_id}", response_model=Student, tags=["studenti"])
    async def aktualizuj(
        student: Annotated[Student, Depends(ziskej_studenta)],
        aktualizace: StudentUpdate,
    ):
        """Částečná aktualizace studenta (PATCH)."""
        data = aktualizace.model_dump(exclude_none=True)
        updated = student.model_copy(update=data)
        DB[student.id] = updated
        return updated

    @app.delete("/studenti/{student_id}", status_code=204, tags=["studenti"])
    async def smaz(student: Annotated[Student, Depends(ziskej_studenta)]):
        """Smaže studenta."""
        del DB[student.id]

    @app.get("/studenti/statistiky/body", tags=["statistiky"])
    async def statistiky():
        """Statistiky bodů všech studentů."""
        if not DB:
            return {"chyba": "Žádní studenti"}
        body = [s.body for s in DB.values()]
        return {
            "pocet":   len(body),
            "prumer":  round(sum(body) / len(body), 2),
            "min":     min(body),
            "max":     max(body),
            "nad_80":  sum(1 for b in body if b >= 80),
        }


# ══════════════════════════════════════════════════════════════
# TESTOVÁNÍ S TestClient
# ══════════════════════════════════════════════════════════════

if FASTAPI_OK:
    print("=== FastAPI – testování s TestClient ===\n")
    client = TestClient(app)

    def tiskni_odpoved(popis: str, resp):
        ok = "✓" if resp.status_code < 400 else "✗"
        print(f"  {ok} {popis}: {resp.status_code}")
        try:
            data = resp.json()
            if isinstance(data, list):
                print(f"    → seznam {len(data)} položek")
                for item in data[:2]:
                    print(f"      {item}")
            elif isinstance(data, dict) and len(str(data)) < 150:
                print(f"    → {data}")
        except Exception:
            pass

    # GET /
    tiskni_odpoved("GET /", client.get("/"))

    # GET /studenti
    tiskni_odpoved("GET /studenti", client.get("/studenti"))

    # GET /studenti s filtrem
    tiskni_odpoved("GET /studenti?min_body=85", client.get("/studenti?min_body=85"))

    # GET /studenti/1
    tiskni_odpoved("GET /studenti/1", client.get("/studenti/1"))

    # POST vytvoření
    novy = {"jmeno": "Ondra", "email": "ondra@k.cz", "vek": 17, "body": 95.0}
    tiskni_odpoved("POST /studenti", client.post("/studenti", json=novy))

    # POST duplicitní email
    tiskni_odpoved("POST duplicitní email", client.post("/studenti", json=novy))

    # PATCH aktualizace
    tiskni_odpoved("PATCH /studenti/1", client.patch("/studenti/1", json={"body": 91.0}))

    # GET statistiky
    tiskni_odpoved("GET /statistiky/body", client.get("/studenti/statistiky/body"))

    # DELETE
    tiskni_odpoved("DELETE /studenti/2", client.delete("/studenti/2"))
    tiskni_odpoved("GET /studenti/2 (po smazání)", client.get("/studenti/2"))

    # GET /studenti znovu
    tiskni_odpoved("GET /studenti (finální seznam)", client.get("/studenti"))

    print("""
Spuštění jako reálný server:
  uvicorn 56_fastapi:app --reload --port 8000

Dokumentace (automatická!):
  http://localhost:8000/docs        ← Swagger UI
  http://localhost:8000/redoc       ← ReDoc
  http://localhost:8000/openapi.json ← JSON Schema
""")

# TVOJE ÚLOHA:
# 1. Přidej endpoint GET /studenti/top/{n} → n studentů s nejvyššími body.
# 2. Přidej autentizaci – API klíč v hlavičce X-API-Key.
# 3. Přidej perzistenci – ulož DB do JSON souboru při každé změně.
# 4. Přidej WebSocket endpoint /ws/live pro real-time notifikace.
