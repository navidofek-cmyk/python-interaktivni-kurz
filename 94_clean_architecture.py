"""
LEKCE 94: Clean Architecture a Event Sourcing
===============================================
Bez instalace – čistý Python.

CLEAN ARCHITECTURE (Robert C. Martin):
  Závislosti tečou jen dovnitř.
  Vnitřní vrstvy nevědí nic o vnějších.

  ┌─────────────────────────────────┐
  │  Frameworks & Drivers (FastAPI) │  ← vnější
  │  ┌─────────────────────────┐   │
  │  │  Interface Adapters      │   │
  │  │  ┌─────────────────┐    │   │
  │  │  │  Use Cases      │    │   │
  │  │  │  ┌──────────┐   │    │   │
  │  │  │  │ Entities │   │    │   │  ← vnitřní (žádné závislosti)
  │  │  │  └──────────┘   │    │   │
  │  │  └─────────────────┘    │   │
  │  └─────────────────────────┘   │
  └─────────────────────────────────┘

EVENT SOURCING:
  Stav = log událostí (ne aktuální hodnota).
  "Co se stalo" místo "jak to teď je".
  → audit log zdarma, time travel, replay
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable, Any
from abc import ABC, abstractmethod
from datetime import datetime
from uuid import uuid4, UUID
import json

# ══════════════════════════════════════════════════════════════
# ČÁST 1: CLEAN ARCHITECTURE – vrstvená aplikace
# ══════════════════════════════════════════════════════════════

print("=== Clean Architecture – vrstvy ===\n")

# ─── VRSTVA 1: Entities (čistá doménová logika) ───────────────

@dataclass
class StudentId:
    hodnota: UUID = field(default_factory=uuid4)
    def __str__(self): return str(self.hodnota)[:8]

@dataclass
class Student:
    """Domain entity – žádné závislosti na frameworku."""
    id:     StudentId
    jmeno:  str
    email:  str
    body:   float = 0.0

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

    def aktualizuj_body(self, nove_body: float) -> None:
        if not (0 <= nove_body <= 100):
            raise ValueError(f"Body mimo rozsah: {nove_body}")
        self.body = nove_body


# ─── VRSTVA 2: Use Cases (aplikační logika) ───────────────────

@runtime_checkable
class StudentRepository(Protocol):
    """Port – rozhraní pro persistenci. Implementace je venku."""
    def uloz(self, student: Student) -> None: ...
    def najdi(self, id: StudentId) -> Student | None: ...
    def vsichni(self) -> list[Student]: ...
    def smaz(self, id: StudentId) -> bool: ...

@dataclass
class VytvorStudenta:
    """Use case: vytvoří studenta."""
    repo: StudentRepository

    def execute(self, jmeno: str, email: str) -> Student:
        # Kontrola unikátnosti emailu
        existujici = [s for s in self.repo.vsichni() if s.email == email]
        if existujici:
            raise ValueError(f"Email {email!r} je již obsazen")
        student = Student(id=StudentId(), jmeno=jmeno, email=email)
        self.repo.uloz(student)
        return student

@dataclass
class AktualizujBody:
    """Use case: aktualizuje body studenta."""
    repo: StudentRepository

    def execute(self, student_id: StudentId, body: float) -> Student:
        student = self.repo.najdi(student_id)
        if student is None:
            raise LookupError(f"Student {student_id} nenalezen")
        student.aktualizuj_body(body)
        self.repo.uloz(student)
        return student

@dataclass
class ZiskejRebricek:
    """Use case: vrátí top N studentů."""
    repo: StudentRepository

    def execute(self, n: int = 5) -> list[Student]:
        return sorted(self.repo.vsichni(), key=lambda s: s.body, reverse=True)[:n]


# ─── VRSTVA 3: Interface Adapters (konverze dat) ──────────────

@dataclass
class StudentDTO:
    """Data Transfer Object – pro API / UI."""
    id:        str
    jmeno:     str
    email:     str
    body:      float
    prospiva:  bool

    @classmethod
    def z_entity(cls, student: Student) -> "StudentDTO":
        return cls(id=str(student.id), jmeno=student.jmeno,
                    email=student.email, body=student.body,
                    prospiva=student.prospiva)

    def jako_json(self) -> str:
        return json.dumps(self.__dict__, ensure_ascii=False)


# ─── VRSTVA 4: Frameworks (konkrétní implementace) ────────────

class InMemoryStudentRepo:
    """Adapter – in-memory implementace StudentRepository."""
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

class SQLiteStudentRepo:
    """Adapter – SQLite implementace StudentRepository."""
    def __init__(self, cesta: str = ":memory:"):
        import sqlite3
        self.conn = sqlite3.connect(cesta)
        self.conn.execute(
            "CREATE TABLE IF NOT EXISTS studenti "
            "(id TEXT PRIMARY KEY, jmeno TEXT, email TEXT UNIQUE, body REAL)"
        )

    def uloz(self, student: Student) -> None:
        self.conn.execute(
            "INSERT OR REPLACE INTO studenti VALUES (?,?,?,?)",
            (str(student.id), student.jmeno, student.email, student.body)
        )
        self.conn.commit()

    def najdi(self, id: StudentId) -> Student | None:
        row = self.conn.execute(
            "SELECT * FROM studenti WHERE id=?", (str(id),)).fetchone()
        if row:
            sid = StudentId(UUID(row[0]))
            return Student(id=sid, jmeno=row[1], email=row[2], body=row[3])
        return None

    def vsichni(self) -> list[Student]:
        rows = self.conn.execute("SELECT * FROM studenti").fetchall()
        return [Student(StudentId(UUID(r[0])), r[1], r[2], r[3]) for r in rows]

    def smaz(self, id: StudentId) -> bool:
        cur = self.conn.execute("DELETE FROM studenti WHERE id=?", (str(id),))
        self.conn.commit()
        return cur.rowcount > 0


# Demo
print("--- Demo: Use cases s In-Memory repo ---\n")
repo   = InMemoryStudentRepo()
vytvor = VytvorStudenta(repo)
update = AktualizujBody(repo)
rebrik = ZiskejRebricek(repo)

studenti_data = [("Míša", "misa@k.cz"), ("Tomáš", "tomas@k.cz"),
                  ("Bára", "bara@k.cz"), ("Ondra", "ondra@k.cz")]
ids = []
for jmeno, email in studenti_data:
    s = vytvor.execute(jmeno, email)
    ids.append(s.id)
    update.execute(s.id, round(60 + 35 * hash(jmeno) % 100 / 100, 1))

print("Žebříček:")
for i, s in enumerate(rebrik.execute(n=10), 1):
    dto = StudentDTO.z_entity(s)
    print(f"  {i}. {dto.jmeno:<10} {dto.body:5.1f}b  "
          f"{'✓' if dto.prospiva else '✗'}")

# Zaměnitelnost: přepni na SQLite bez změny use cases
print("\nSamiž use cases, SQLite backend:")
repo2 = SQLiteStudentRepo()
vytvor2 = VytvorStudenta(repo2)
update2 = AktualizujBody(repo2)
for jmeno, email in studenti_data:
    s = vytvor2.execute(jmeno, email)
    update2.execute(s.id, 80.0)
print(f"  SQLite: {len(repo2.vsichni())} studentů uloženo")


# ══════════════════════════════════════════════════════════════
# ČÁST 2: EVENT SOURCING
# ══════════════════════════════════════════════════════════════

print("\n=== Event Sourcing ===\n")

@dataclass(frozen=True)
class Udalost:
    """Základ všech doménových událostí."""
    id:         UUID      = field(default_factory=uuid4)
    cas:        datetime  = field(default_factory=datetime.now)
    verze:      int       = 1

@dataclass(frozen=True)
class StudentZapsan(Udalost):
    student_id: UUID  = field(default_factory=uuid4)
    jmeno:      str   = ""
    email:      str   = ""

@dataclass(frozen=True)
class BodyAktualizovany(Udalost):
    student_id:  UUID  = field(default_factory=uuid4)
    stare_body:  float = 0.0
    nove_body:   float = 0.0

@dataclass(frozen=True)
class StudentOdhlasil(Udalost):
    student_id: UUID  = field(default_factory=uuid4)
    duvod:      str   = ""

class EventStore:
    """Úložiště událostí – append-only log."""
    def __init__(self):
        self._udalosti: list[Udalost] = []

    def uloz(self, udalost: Udalost) -> None:
        self._udalosti.append(udalost)

    def pro_entitu(self, entity_id: UUID) -> list[Udalost]:
        return [u for u in self._udalosti
                if getattr(u, "student_id", None) == entity_id]

    def vsechny(self) -> list[Udalost]:
        return list(self._udalosti)

    def od(self, cas: datetime) -> list[Udalost]:
        return [u for u in self._udalosti if u.cas >= cas]

class StudentAggregate:
    """Agregát – rekonstruuje stav z událostí."""

    def __init__(self, student_id: UUID):
        self.id      = student_id
        self.jmeno   = ""
        self.email   = ""
        self.body    = 0.0
        self.aktivni = False
        self._cekajici: list[Udalost] = []

    @classmethod
    def z_udalosti(cls, student_id: UUID,
                    udalosti: list[Udalost]) -> "StudentAggregate":
        agregat = cls(student_id)
        for u in udalosti:
            agregat._aplikuj(u)
        return agregat

    def _aplikuj(self, udalost: Udalost) -> None:
        match udalost:
            case StudentZapsan(jmeno=j, email=e):
                self.jmeno   = j
                self.email   = e
                self.aktivni = True
            case BodyAktualizovany(nove_body=b):
                self.body = b
            case StudentOdhlasil():
                self.aktivni = False

    # Příkazy – generují události
    def zapsat(self, jmeno: str, email: str) -> "StudentAggregate":
        u = StudentZapsan(student_id=self.id, jmeno=jmeno, email=email)
        self._aplikuj(u)
        self._cekajici.append(u)
        return self

    def aktualizuj_body(self, body: float) -> "StudentAggregate":
        u = BodyAktualizovany(student_id=self.id,
                               stare_body=self.body, nove_body=body)
        self._aplikuj(u)
        self._cekajici.append(u)
        return self

    def odhlas(self, duvod: str = "") -> "StudentAggregate":
        u = StudentOdhlasil(student_id=self.id, duvod=duvod)
        self._aplikuj(u)
        self._cekajici.append(u)
        return self

    def vycerpej_udalosti(self) -> list[Udalost]:
        udalosti = list(self._cekajici)
        self._cekajici.clear()
        return udalosti


# Demo event sourcing
store = EventStore()

# Simuluj 3 studenty s historií
sid1 = uuid4()
s1   = (StudentAggregate(sid1)
         .zapsat("Míša", "misa@k.cz")
         .aktualizuj_body(75.0)
         .aktualizuj_body(87.5)
         .aktualizuj_body(91.0))

for u in s1.vycerpej_udalosti():
    store.uloz(u)

sid2 = uuid4()
s2   = (StudentAggregate(sid2)
         .zapsat("Tomáš", "tomas@k.cz")
         .aktualizuj_body(55.0)
         .odhlas("Přestoupil na jinou školu"))

for u in s2.vycerpej_udalosti():
    store.uloz(u)

# Rekonstruuj stav z událostí
print("Všechny události:")
for u in store.vsechny():
    cas = u.cas.strftime("%H:%M:%S")
    match u:
        case StudentZapsan(jmeno=j):
            print(f"  [{cas}] ✎ Zapsán:     {j}")
        case BodyAktualizovany(stare_body=s, nove_body=n):
            print(f"  [{cas}] ↑ Body:       {s} → {n}")
        case StudentOdhlasil(duvod=d):
            print(f"  [{cas}] ✗ Odhlásil:   {d or '(bez důvodu)'}")

print("\nRekonstruovaný stav Míši:")
s1_obnoven = StudentAggregate.z_udalosti(sid1, store.pro_entitu(sid1))
print(f"  Jméno: {s1_obnoven.jmeno}, Body: {s1_obnoven.body}, Aktivní: {s1_obnoven.aktivni}")

print("\nTime travel – jak vypadal stav po první změně body:")
udalosti_do_druhe = store.pro_entitu(sid1)[:2]   # jen prvních 2 události
s1_cas = StudentAggregate.z_udalosti(sid1, udalosti_do_druhe)
print(f"  Body po první aktualizaci: {s1_cas.body}")

print("""
=== Clean Arch vs Event Sourcing – kdy co ===

  Clean Architecture:
    ✓ Každý projekt – odděluje logiku od frameworku
    ✓ Testovatelnost – use cases testujeme bez DB/HTTP
    ✓ Zaměnitelnost – SQLite v devu, PostgreSQL v produkci

  Event Sourcing:
    ✓ Audit log je požadavek (banky, healthcare)
    ✓ Time travel / debug ("jak to vypadalo ve čtvrtek")
    ✓ Event-driven architektura (lekce 65 – Kafka)
    ✗ Jednoduché CRUD – zbytečná komplexita
""")

# TVOJE ÚLOHA:
# 1. Přidej snapshot mechanismus do EventStore (každých 10 událostí ulož snapshot).
# 2. Implementuj projektci: z event logu vygeneruj "kolik studentů bylo aktivních v čase T".
# 3. Kombinuj Clean Arch + FastAPI z lekce 56 – Use Cases jako FastAPI endpoint handlery.
