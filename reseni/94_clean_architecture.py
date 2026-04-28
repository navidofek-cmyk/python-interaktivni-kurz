"""Řešení – Lekce 94: Clean Architecture a Event Sourcing"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable, Any
from abc import ABC, abstractmethod
from datetime import datetime
from uuid import uuid4, UUID
import json
import time


# ── Sdílené entity a use cases z originální lekce ────────────────
@dataclass
class StudentId:
    hodnota: UUID = field(default_factory=uuid4)
    def __str__(self): return str(self.hodnota)[:8]

@dataclass
class Student:
    id:    StudentId
    jmeno: str
    email: str
    body:  float = 0.0

    def __post_init__(self):
        if not self.jmeno.strip():
            raise ValueError("Jméno nesmí být prázdné")
        if "@" not in self.email:
            raise ValueError(f"Neplatný email: {self.email}")
        if not (0 <= self.body <= 100):
            raise ValueError(f"Body mimo rozsah: {self.body}")

    @property
    def prospiva(self) -> bool:
        return self.body >= 75

    def aktualizuj_body(self, nove_body: float):
        if not (0 <= nove_body <= 100):
            raise ValueError(f"Body mimo rozsah: {nove_body}")
        self.body = nove_body

@runtime_checkable
class StudentRepository(Protocol):
    def uloz(self, student: Student) -> None: ...
    def najdi(self, id: StudentId) -> Student | None: ...
    def vsichni(self) -> list[Student]: ...
    def smaz(self, id: StudentId) -> bool: ...

class InMemoryStudentRepo:
    def __init__(self):
        self._data: dict[str, Student] = {}
    def uloz(self, student: Student) -> None:
        self._data[str(student.id)] = student
    def najdi(self, id: StudentId) -> Student | None:
        return self._data.get(str(id))
    def vsichni(self) -> list[Student]:
        return list(self._data.values())
    def smaz(self, id: StudentId) -> bool:
        return self._data.pop(str(id), None) is not None

@dataclass
class VytvorStudenta:
    repo: StudentRepository
    def execute(self, jmeno: str, email: str) -> Student:
        if any(s.email == email for s in self.repo.vsichni()):
            raise ValueError(f"Email {email!r} je již obsazen")
        s = Student(id=StudentId(), jmeno=jmeno, email=email)
        self.repo.uloz(s)
        return s

@dataclass
class AktualizujBody:
    repo: StudentRepository
    def execute(self, student_id: StudentId, body: float) -> Student:
        s = self.repo.najdi(student_id)
        if s is None:
            raise LookupError(f"Student {student_id} nenalezen")
        s.aktualizuj_body(body)
        self.repo.uloz(s)
        return s


# ── Event types ────────────────────────────────────────────────
@dataclass(frozen=True)
class Udalost:
    id:  UUID     = field(default_factory=uuid4)
    cas: datetime = field(default_factory=datetime.now)

@dataclass(frozen=True)
class StudentZapsan(Udalost):
    student_id: UUID = field(default_factory=uuid4)
    jmeno:      str  = ""
    email:      str  = ""

@dataclass(frozen=True)
class BodyAktualizovany(Udalost):
    student_id: UUID  = field(default_factory=uuid4)
    stare_body: float = 0.0
    nove_body:  float = 0.0

@dataclass(frozen=True)
class StudentOdhlasil(Udalost):
    student_id: UUID = field(default_factory=uuid4)
    duvod:      str  = ""


# 1. Snapshot mechanismus v EventStore
print("=== 1. Snapshot mechanismus ===\n")

@dataclass
class Snapshot:
    """Uložený stav agregátu v daném bodě."""
    entity_id:      UUID
    verze:          int
    stav:           dict
    cas:            datetime = field(default_factory=datetime.now)


class EventStoreSeSnapshoty:
    """
    EventStore s automatickým snapshotem každých N událostí.
    Při rekonstrukci načte nejbližší snapshot a přehraje jen delta události.
    """
    SNAPSHOT_INTERVAL = 10   # snapshot každých 10 událostí

    def __init__(self):
        self._udalosti:  list[Udalost] = []
        self._snapshoty: dict[str, Snapshot] = {}   # entity_id → Snapshot

    def uloz(self, udalost: Udalost) -> None:
        self._udalosti.append(udalost)

        # Auto-snapshot každých N událostí pro tuto entitu
        eid = str(getattr(udalost, "student_id", None))
        if eid == "None":
            return
        pocet = sum(1 for u in self._udalosti
                    if str(getattr(u, "student_id", None)) == eid)
        if pocet % self.SNAPSHOT_INTERVAL == 0:
            self._uloz_snapshot(eid, pocet)

    def _uloz_snapshot(self, entity_id: str, verze: int):
        """Rekonstruuje aktuální stav a uloží jako snapshot."""
        from uuid import UUID as _UUID
        eid = _UUID(entity_id) if isinstance(entity_id, str) else entity_id
        agregat = self._rekonstruuj_bez_snapshotu(eid)
        snap = Snapshot(
            entity_id=eid,
            verze=verze,
            stav={
                "jmeno":   agregat.jmeno,
                "email":   agregat.email,
                "body":    agregat.body,
                "aktivni": agregat.aktivni,
            },
        )
        self._snapshoty[entity_id] = snap
        print(f"  [Snapshot] entity={entity_id[:8]} verze={verze} "
              f"stav=body:{agregat.body}")

    def pro_entitu(self, entity_id: UUID) -> list[Udalost]:
        return [u for u in self._udalosti
                if getattr(u, "student_id", None) == entity_id]

    def _rekonstruuj_bez_snapshotu(self, entity_id: UUID):
        """Plná rekonstrukce z událostí (bez snapshotu)."""
        agregat = StudentAggregate(entity_id)
        for u in self.pro_entitu(entity_id):
            agregat._aplikuj(u)
        return agregat

    def rekonstruuj(self, entity_id: UUID):
        """
        Rekonstrukce s využitím snapshotu:
        1. Načti nejbližší snapshot
        2. Přehraj pouze události po snapshotu
        """
        snap = self._snapshoty.get(str(entity_id))

        if snap is None:
            return self._rekonstruuj_bez_snapshotu(entity_id)

        # Obnov ze snapshotu
        agregat = StudentAggregate(entity_id)
        agregat.jmeno   = snap.stav["jmeno"]
        agregat.email   = snap.stav["email"]
        agregat.body    = snap.stav["body"]
        agregat.aktivni = snap.stav["aktivni"]

        # Přehraj pouze události PO snapshotu
        vsechny = self.pro_entitu(entity_id)
        po_snapshotu = vsechny[snap.verze:]  # události za snapshot verzi
        nacitano = len(po_snapshotu)
        for u in po_snapshotu:
            agregat._aplikuj(u)

        print(f"  [Rekonstrukce] snapshot verze={snap.verze}, "
              f"delta={nacitano} události")
        return agregat


class StudentAggregate:
    def __init__(self, student_id: UUID):
        self.id      = student_id
        self.jmeno   = ""
        self.email   = ""
        self.body    = 0.0
        self.aktivni = False
        self._cekajici: list[Udalost] = []

    @classmethod
    def z_udalosti(cls, student_id: UUID, udalosti: list[Udalost]):
        a = cls(student_id)
        for u in udalosti:
            a._aplikuj(u)
        return a

    def _aplikuj(self, udalost: Udalost):
        match udalost:
            case StudentZapsan(jmeno=j, email=e):
                self.jmeno   = j
                self.email   = e
                self.aktivni = True
            case BodyAktualizovany(nove_body=b):
                self.body = b
            case StudentOdhlasil():
                self.aktivni = False

    def zapsat(self, jmeno: str, email: str) -> StudentAggregate:
        u = StudentZapsan(student_id=self.id, jmeno=jmeno, email=email)
        self._aplikuj(u)
        self._cekajici.append(u)
        return self

    def aktualizuj_body(self, body: float) -> StudentAggregate:
        u = BodyAktualizovany(student_id=self.id,
                               stare_body=self.body, nove_body=body)
        self._aplikuj(u)
        self._cekajici.append(u)
        return self

    def vycerpej_udalosti(self) -> list[Udalost]:
        e = list(self._cekajici)
        self._cekajici.clear()
        return e

# Demo snapshots
store = EventStoreSeSnapshoty()
sid = uuid4()
agregat = StudentAggregate(sid).zapsat("Snapshot Test", "snap@k.cz")
for u in agregat.vycerpej_udalosti():
    store.uloz(u)

# Simuluj 15 aktualizací body → automatický snapshot po 10
for body in range(1, 16):
    a2 = StudentAggregate(sid)
    a2.body = body - 1
    u2 = BodyAktualizovany(student_id=sid, stare_body=float(body-1), nove_body=float(body))
    store.uloz(u2)

print(f"\nCelkem událostí: {len(store._udalosti)}")
print(f"Snapshoty:       {len(store._snapshoty)}")
obnoven = store.rekonstruuj(sid)
print(f"Obnovený stav: body={obnoven.body}, aktivni={obnoven.aktivni}")


# 2. Projekce: studenti aktivní v čase T
print("\n=== 2. Projekce – aktivní studenti v čase T ===\n")

class ProjekceAktivnichStudentu:
    """
    Projekce z event logu: kolik studentů bylo aktivních v čase T.
    Projde všechny události a rekonstruuje historický stav.
    """

    def __init__(self, udalosti: list[Udalost]):
        self.udalosti = sorted(udalosti, key=lambda u: u.cas)

    def aktivni_v_case(self, t: datetime) -> set[UUID]:
        """Vrátí set UUID aktivních studentů v čase T."""
        aktivni: set[UUID] = set()

        for u in self.udalosti:
            if u.cas > t:
                break  # přes časový limit
            match u:
                case StudentZapsan(student_id=sid):
                    aktivni.add(sid)
                case StudentOdhlasil(student_id=sid):
                    aktivni.discard(sid)

        return aktivni

    def history_aktivnich(self, kroky: int = 5) -> list[dict]:
        """
        Vrátí historický přehled počtu aktivních studentů
        v rovnoměrně rozložených časových bodech.
        """
        if not self.udalosti:
            return []

        t_min = self.udalosti[0].cas
        t_max = self.udalosti[-1].cas
        delta = (t_max - t_min).total_seconds() / max(kroky, 1)

        zaznamy = []
        for i in range(kroky + 1):
            t = datetime.fromtimestamp(t_min.timestamp() + i * delta)
            aktivni = self.aktivni_v_case(t)
            zaznamy.append({
                "cas":    t.strftime("%H:%M:%S"),
                "pocet":  len(aktivni),
                "udalosti_do_ted": sum(1 for u in self.udalosti if u.cas <= t),
            })

        return zaznamy

# Demo projekce
from time import sleep

vsechny_udalosti = []
sids = [uuid4() for _ in range(5)]

# Postupné přidávání a odhlašování studentů
for i, sid in enumerate(sids):
    a = StudentAggregate(sid).zapsat(f"Student_{i+1}", f"s{i+1}@k.cz")
    vsechny_udalosti.extend(a.vycerpej_udalosti())
    time.sleep(0.01)

# Odhlášení dvou studentů
for sid in sids[:2]:
    u = StudentOdhlasil(student_id=sid, duvod="Přestoupil")
    vsechny_udalosti.append(u)
    time.sleep(0.01)

# Zápis dalšího studenta
a_novy = StudentAggregate(uuid4()).zapsat("Student_6", "s6@k.cz")
vsechny_udalosti.extend(a_novy.vycerpej_udalosti())

projekce = ProjekceAktivnichStudentu(vsechny_udalosti)
print("  Historický přehled aktivních studentů:\n")
print(f"  {'Čas':>12}  {'Aktivní':>8}  {'Událostí celkem':>16}")
print(f"  {'─'*12}  {'─'*8}  {'─'*16}")
for zaznam in projekce.history_aktivnich(kroky=4):
    print(f"  {zaznam['cas']:>12}  {zaznam['pocet']:>8}  {zaznam['udalosti_do_ted']:>16}")

# Aktuální stav
ted = datetime.now()
aktivni_ted = projekce.aktivni_v_case(ted)
print(f"\n  Aktuálně aktivní: {len(aktivni_ted)} studentů")


# 3. Clean Arch + FastAPI – Use Cases jako handlery
print("\n=== 3. Clean Arch + FastAPI ===\n")

FASTAPI_USECASE_KOD = '''\
# main.py – FastAPI s Clean Architecture Use Cases

from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel, EmailStr
from typing import Annotated
from uuid import UUID

# ── DTOs (Pydantic pro FastAPI validaci) ──────────────────────
class VytvorStudentaRequest(BaseModel):
    jmeno: str
    email: str

class AktualizujBodyRequest(BaseModel):
    body: float

class StudentResponse(BaseModel):
    id:       str
    jmeno:    str
    email:    str
    body:     float
    prospiva: bool

    @classmethod
    def z_entity(cls, student: Student) -> "StudentResponse":
        return cls(
            id=str(student.id), jmeno=student.jmeno,
            email=student.email, body=student.body,
            prospiva=student.prospiva,
        )

# ── Dependency Injection ───────────────────────────────────────
def ziskej_repo() -> StudentRepository:
    """Factory pro repository – zde InMemory, v produkci SQLite/Postgres."""
    return InMemoryStudentRepo()   # vyměň za SQLiteStudentRepo() nebo ORM repo

def ziskej_vytvor_uc(repo = Depends(ziskej_repo)):
    return VytvorStudenta(repo)

def ziskej_update_uc(repo = Depends(ziskej_repo)):
    return AktualizujBody(repo)

# ── FastAPI aplikace ───────────────────────────────────────────
app = FastAPI(title="Student API", version="1.0.0")

@app.post("/studenti", response_model=StudentResponse, status_code=201)
def vytvor_studenta(
    data: VytvorStudentaRequest,
    uc:   Annotated[VytvorStudenta, Depends(ziskej_vytvor_uc)],
):
    """Use Case: VytvorStudenta – žádná databázová logika zde."""
    try:
        student = uc.execute(jmeno=data.jmeno, email=data.email)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    return StudentResponse.z_entity(student)

@app.put("/studenti/{student_id}/body", response_model=StudentResponse)
def aktualizuj_body(
    student_id: UUID,
    data:       AktualizujBodyRequest,
    uc:         Annotated[AktualizujBody, Depends(ziskej_update_uc)],
):
    """Use Case: AktualizujBody – business logika v use case, ne v controlleru."""
    try:
        sid     = StudentId(student_id)
        student = uc.execute(sid, data.body)
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    return StudentResponse.z_entity(student)

@app.get("/studenti", response_model=list[StudentResponse])
def seznam_studentu(repo: Annotated[StudentRepository, Depends(ziskej_repo)]):
    return [StudentResponse.z_entity(s) for s in repo.vsichni()]

@app.get("/studenti/{student_id}", response_model=StudentResponse)
def detail_studenta(student_id: UUID,
                     repo: Annotated[StudentRepository, Depends(ziskej_repo)]):
    sid = StudentId(student_id)
    s   = repo.najdi(sid)
    if s is None:
        raise HTTPException(status_code=404, detail=f"Student {student_id} nenalezen")
    return StudentResponse.z_entity(s)

# Spuštění:
#   uvicorn main:app --reload
# Testy:
#   curl -X POST /studenti -d \'{"jmeno":"Míša","email":"misa@k.cz"}\'
#   curl /studenti
'''
print(FASTAPI_USECASE_KOD)

# Demonstrace bez skutečného FastAPI
print("  Demo Use Cases (bez HTTP serveru):\n")

repo   = InMemoryStudentRepo()
vytvor = VytvorStudenta(repo)
update = AktualizujBody(repo)

for jmeno, email in [("Míša", "misa@k.cz"), ("Tomáš", "tomas@k.cz"),
                      ("Bára", "bara@k.cz")]:
    s = vytvor.execute(jmeno, email)
    update.execute(s.id, round(70 + hash(jmeno) % 30, 1))

print("  GET /studenti:")
for s in sorted(repo.vsichni(), key=lambda x: x.body, reverse=True):
    print(f"    {s.jmeno:<12} {s.body:5.1f}b  "
          f"{'✓' if s.prospiva else '✗'}")

# Test zaměnitelnosti repository
print("\n  Zaměnitelnost – SQLite backend:")
import sqlite3

class SQLiteStudentRepo:
    def __init__(self, db: str = ":memory:"):
        self.conn = sqlite3.connect(db)
        self.conn.execute(
            "CREATE TABLE IF NOT EXISTS studenti "
            "(id TEXT PRIMARY KEY, jmeno TEXT, email TEXT UNIQUE, body REAL)"
        )
    def uloz(self, student: Student):
        self.conn.execute(
            "INSERT OR REPLACE INTO studenti VALUES (?,?,?,?)",
            (str(student.id), student.jmeno, student.email, student.body)
        )
        self.conn.commit()
    def najdi(self, id: StudentId) -> Student | None:
        row = self.conn.execute(
            "SELECT * FROM studenti WHERE id=?", (str(id),)).fetchone()
        if row:
            return Student(StudentId(UUID(row[0])), row[1], row[2], row[3])
        return None
    def vsichni(self) -> list[Student]:
        return [Student(StudentId(UUID(r[0])), r[1], r[2], r[3])
                for r in self.conn.execute("SELECT * FROM studenti").fetchall()]
    def smaz(self, id: StudentId) -> bool:
        cur = self.conn.execute("DELETE FROM studenti WHERE id=?", (str(id),))
        self.conn.commit()
        return cur.rowcount > 0

repo_sql = SQLiteStudentRepo()
vytvor2  = VytvorStudenta(repo_sql)
update2  = AktualizujBody(repo_sql)

for jmeno, email in [("Míša", "misa@k.cz"), ("Tomáš", "tomas@k.cz")]:
    s = vytvor2.execute(jmeno, email)
    update2.execute(s.id, 80.0)

print(f"  SQLite backend: {len(repo_sql.vsichni())} studentů uloženo")
print("  Use cases identické – repository zaměněno transparentně")

print("\n=== Shrnutí ===")
print("  1. EventStore + Snapshot  – auto-snapshot po N událostech, delta replay")
print("  2. Projekce               – aktivni_v_case(t), historický přehled")
print("  3. FastAPI Use Cases      – DI, zaměnitelné repo, HTTP handler = tenká vrstva")
