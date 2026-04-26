"""
LEKCE 40: Databáze – sqlite3
==============================
SQLite = plnohodnotná SQL databáze v jednom souboru.
Je součástí Pythonu, žádná instalace.
Použití: mobilní aplikace, desktop tools, prototypy, testy.

SQL základy:
  CREATE TABLE  – vytvoř tabulku
  INSERT INTO   – vlož záznam
  SELECT        – načti záznamy
  UPDATE        – uprav záznam
  DELETE        – smaž záznam
  WHERE         – filtrování
  JOIN          – spojení tabulek
"""

import sqlite3
from dataclasses import dataclass, field
from pathlib import Path
from contextlib import contextmanager
from datetime import datetime

DB_SOUBOR = "kurz.db"

# ══════════════════════════════════════════════════════════════
# ČÁST 1: ZÁKLAD – přímá práce s sqlite3
# ══════════════════════════════════════════════════════════════

print("=== Základ sqlite3 ===\n")

# Připojení – vytvoří soubor pokud neexistuje
# ":memory:" = databáze pouze v RAM (pro testy)
conn = sqlite3.connect(":memory:")
conn.row_factory = sqlite3.Row   # řádky jako slovníky

cur = conn.cursor()

# DDL – definice struktury
cur.executescript("""
    CREATE TABLE IF NOT EXISTS studenti (
        id        INTEGER PRIMARY KEY AUTOINCREMENT,
        jmeno     TEXT    NOT NULL,
        email     TEXT    UNIQUE NOT NULL,
        vek       INTEGER CHECK(vek > 0),
        zapsano   TEXT    DEFAULT (date('now'))
    );

    CREATE TABLE IF NOT EXISTS kurzy (
        id    INTEGER PRIMARY KEY AUTOINCREMENT,
        nazev TEXT NOT NULL,
        lektor TEXT
    );

    CREATE TABLE IF NOT EXISTS zapis (
        student_id INTEGER REFERENCES studenti(id),
        kurz_id    INTEGER REFERENCES kurzy(id),
        datum      TEXT DEFAULT (date('now')),
        PRIMARY KEY (student_id, kurz_id)
    );
""")

# INSERT – parametrizované dotazy (!! nikdy f-string do SQL !!)
studenti = [
    ("Míša",   "misa@example.com",   15),
    ("Tomáš",  "tomas@example.com",  16),
    ("Bára",   "bara@example.com",   14),
    ("Ondra",  "ondra@example.com",  17),
    ("Klára",  "klara@example.com",  15),
]
cur.executemany(
    "INSERT INTO studenti (jmeno, email, vek) VALUES (?, ?, ?)",
    studenti
)

kurzy_data = [("Python základy", "Novák"), ("Algoritmy", "Dvořák"),
              ("Web", "Procházka")]
cur.executemany("INSERT INTO kurzy (nazev, lektor) VALUES (?,?)", kurzy_data)

# Zápisy do kurzů
cur.executemany("INSERT INTO zapis (student_id, kurz_id) VALUES (?,?)", [
    (1,1),(1,2),(2,1),(3,1),(3,3),(4,2),(4,3),(5,1),(5,2),(5,3)
])
conn.commit()

# SELECT
print("Všichni studenti:")
for row in cur.execute("SELECT * FROM studenti ORDER BY jmeno"):
    print(f"  {row['id']:2d}. {row['jmeno']:<10} {row['email']:<25} věk: {row['vek']}")

# WHERE + parametr
print("\nStudenti věku 15:")
for r in cur.execute("SELECT jmeno FROM studenti WHERE vek = ?", (15,)):
    print(f"  {r['jmeno']}")

# JOIN
print("\nKdo je zapsán do jakého kurzu:")
query = """
    SELECT s.jmeno, k.nazev, k.lektor
    FROM   zapis z
    JOIN   studenti s ON s.id = z.student_id
    JOIN   kurzy    k ON k.id = z.kurz_id
    ORDER  BY s.jmeno, k.nazev
"""
for r in cur.execute(query):
    print(f"  {r['jmeno']:<10} → {r['nazev']} (lektor: {r['lektor']})")

# Agregace
print("\nPočet studentů na kurz:")
for r in cur.execute("""
    SELECT k.nazev, COUNT(*) as pocet
    FROM   zapis z JOIN kurzy k ON k.id = z.kurz_id
    GROUP  BY k.id ORDER BY pocet DESC
"""):
    print(f"  {r['nazev']:<20} {r['pocet']} studentů")

conn.close()


# ══════════════════════════════════════════════════════════════
# ČÁST 2: REPOSITORY PATTERN – čistá architektura
# ══════════════════════════════════════════════════════════════

print("\n=== Repository pattern ===\n")

@dataclass
class Student:
    jmeno:  str
    email:  str
    vek:    int
    id:     int | None = None

@dataclass
class Kurz:
    nazev:  str
    lektor: str
    id:     int | None = None

@contextmanager
def get_db(cesta: str = ":memory:"):
    conn = sqlite3.connect(cesta)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

class StudentRepository:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn
        self._init_schema()

    def _init_schema(self):
        self.conn.executescript("""
            CREATE TABLE IF NOT EXISTS studenti (
                id    INTEGER PRIMARY KEY AUTOINCREMENT,
                jmeno TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                vek   INTEGER
            );
        """)

    def vloz(self, student: Student) -> Student:
        cur = self.conn.execute(
            "INSERT INTO studenti (jmeno, email, vek) VALUES (?,?,?)",
            (student.jmeno, student.email, student.vek)
        )
        return Student(student.jmeno, student.email, student.vek, cur.lastrowid)

    def ziskej(self, id: int) -> Student | None:
        row = self.conn.execute(
            "SELECT * FROM studenti WHERE id=?", (id,)
        ).fetchone()
        return Student(**dict(row)) if row else None

    def vsichni(self) -> list[Student]:
        return [Student(**dict(r))
                for r in self.conn.execute("SELECT * FROM studenti ORDER BY jmeno")]

    def aktualizuj(self, student: Student) -> None:
        self.conn.execute(
            "UPDATE studenti SET jmeno=?, email=?, vek=? WHERE id=?",
            (student.jmeno, student.email, student.vek, student.id)
        )

    def smaz(self, id: int) -> bool:
        cur = self.conn.execute("DELETE FROM studenti WHERE id=?", (id,))
        return cur.rowcount > 0

    def hledej(self, **kriteria) -> list[Student]:
        podminky = " AND ".join(f"{k}=?" for k in kriteria)
        hodnoty  = tuple(kriteria.values())
        rows = self.conn.execute(
            f"SELECT * FROM studenti WHERE {podminky}", hodnoty
        ).fetchall()
        return [Student(**dict(r)) for r in rows]

# Použití
with get_db() as conn:
    repo = StudentRepository(conn)

    # CREATE
    m = repo.vloz(Student("Míša",  "misa@x.cz",  15))
    t = repo.vloz(Student("Tomáš", "tomas@x.cz", 16))
    b = repo.vloz(Student("Bára",  "bara@x.cz",  15))
    print(f"Vloženi: {m.jmeno}(id={m.id}), {t.jmeno}(id={t.id}), {b.jmeno}(id={b.id})")

    # READ
    print(f"\nVšichni: {[s.jmeno for s in repo.vsichni()]}")
    print(f"Student 2: {repo.ziskej(2)}")

    # UPDATE
    t.vek = 17
    repo.aktualizuj(t)
    print(f"\nPo aktualizaci: {repo.ziskej(2)}")

    # hledej
    print(f"\n15letí: {[s.jmeno for s in repo.hledej(vek=15)]}")

    # DELETE
    repo.smaz(m.id)
    print(f"\nPo smazání Míši: {[s.jmeno for s in repo.vsichni()]}")


# ══════════════════════════════════════════════════════════════
# ČÁST 3: MIGRACE & SCHEMA VERSIONING
# ══════════════════════════════════════════════════════════════

print("\n=== Schema migrace ===\n")

MIGRACE = [
    # (verze, sql)
    (1, """
        CREATE TABLE IF NOT EXISTS uzivatele (
            id    INTEGER PRIMARY KEY,
            email TEXT UNIQUE NOT NULL
        );
    """),
    (2, """
        ALTER TABLE uzivatele ADD COLUMN jmeno TEXT;
        ALTER TABLE uzivatele ADD COLUMN vytvoreno TEXT DEFAULT (datetime('now'));
    """),
    (3, """
        CREATE INDEX IF NOT EXISTS idx_email ON uzivatele(email);
    """),
]

def aplikuj_migrace(conn: sqlite3.Connection):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS schema_version (verze INTEGER PRIMARY KEY)
    """)
    aktualni = (conn.execute(
        "SELECT MAX(verze) FROM schema_version"
    ).fetchone()[0] or 0)

    print(f"  Aktuální verze schématu: {aktualni}")
    for verze, sql in MIGRACE:
        if verze > aktualni:
            conn.executescript(sql)
            conn.execute("INSERT INTO schema_version VALUES (?)", (verze,))
            print(f"  Aplikována migrace v{verze}")

    conn.commit()

with get_db() as conn:
    aplikuj_migrace(conn)
    aplikuj_migrace(conn)   # druhé spuštění – nic neprovede

# TVOJE ÚLOHA:
# 1. Přidej do StudentRepository metodu pocet() → int.
# 2. Napiš KurzRepository s metodami vloz, vsichni, a zapis_studenta(student_id, kurz_id).
# 3. Přidej migrace 4 a 5 do seznamu MIGRACE a ověř že se aplikují správně.
# 4. Napiš export_csv(conn, tabulka, soubor) který uloží tabulku do CSV.
