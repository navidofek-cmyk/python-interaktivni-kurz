"""Řešení – Lekce 40: Databáze – sqlite3"""

import sqlite3
import csv
import io
from dataclasses import dataclass
from contextlib import contextmanager


# ── Context manager pro DB spojení ───────────────────────────────────────────

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


# ── Datové třídy ─────────────────────────────────────────────────────────────

@dataclass
class Student:
    jmeno: str
    email: str
    vek: int
    id: int | None = None


@dataclass
class Kurz:
    nazev: str
    lektor: str
    id: int | None = None


# ── 1. StudentRepository s metodou pocet() ───────────────────────────────────

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
        hodnoty = tuple(kriteria.values())
        rows = self.conn.execute(
            f"SELECT * FROM studenti WHERE {podminky}", hodnoty
        ).fetchall()
        return [Student(**dict(r)) for r in rows]

    # 1. Metoda pocet() → int
    # Vrátí celkový počet studentů v databázi
    def pocet(self) -> int:
        """Vrátí počet studentů v tabulce."""
        row = self.conn.execute("SELECT COUNT(*) FROM studenti").fetchone()
        return row[0]


# ── 2. KurzRepository ─────────────────────────────────────────────────────────

class KurzRepository:
    """Repository pro kurzy s metodami vloz, vsichni, zapis_studenta."""

    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn
        self._init_schema()

    def _init_schema(self):
        self.conn.executescript("""
            CREATE TABLE IF NOT EXISTS kurzy (
                id     INTEGER PRIMARY KEY AUTOINCREMENT,
                nazev  TEXT NOT NULL,
                lektor TEXT
            );
            CREATE TABLE IF NOT EXISTS zapis (
                student_id INTEGER,
                kurz_id    INTEGER,
                datum      TEXT DEFAULT (date('now')),
                PRIMARY KEY (student_id, kurz_id)
            );
        """)

    def vloz(self, kurz: Kurz) -> Kurz:
        cur = self.conn.execute(
            "INSERT INTO kurzy (nazev, lektor) VALUES (?,?)",
            (kurz.nazev, kurz.lektor)
        )
        return Kurz(kurz.nazev, kurz.lektor, cur.lastrowid)

    def vsichni(self) -> list[Kurz]:
        return [Kurz(**dict(r))
                for r in self.conn.execute("SELECT * FROM kurzy ORDER BY nazev")]

    def zapis_studenta(self, student_id: int, kurz_id: int) -> bool:
        """Zapíše studenta do kurzu. Vrátí True pokud úspěšné, False pokud už zapsán."""
        try:
            self.conn.execute(
                "INSERT INTO zapis (student_id, kurz_id) VALUES (?,?)",
                (student_id, kurz_id)
            )
            return True
        except sqlite3.IntegrityError:
            return False  # already enrolled (PRIMARY KEY conflict)

    def studenti_kurzu(self, kurz_id: int) -> list[dict]:
        """Vrátí seznam studentů zapsaných do daného kurzu."""
        rows = self.conn.execute("""
            SELECT s.jmeno, s.email, z.datum
            FROM   zapis z JOIN studenti s ON s.id = z.student_id
            WHERE  z.kurz_id = ?
            ORDER  BY s.jmeno
        """, (kurz_id,)).fetchall()
        return [dict(r) for r in rows]


# ── 3. Migrace 4 a 5 ─────────────────────────────────────────────────────────

MIGRACE = [
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
    # 3. Migrace 4: přidání role uživatele
    (4, """
        ALTER TABLE uzivatele ADD COLUMN role TEXT DEFAULT 'user';
    """),
    # Migrace 5: tabulka pro session tokeny
    (5, """
        CREATE TABLE IF NOT EXISTS sessions (
            token      TEXT PRIMARY KEY,
            uzivatel_id INTEGER REFERENCES uzivatele(id),
            vyprseni   TEXT NOT NULL
        );
    """),
]


def aplikuj_migrace(conn: sqlite3.Connection):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS schema_version (verze INTEGER PRIMARY KEY)
    """)
    aktualni = (conn.execute(
        "SELECT MAX(verze) FROM schema_version"
    ).fetchone()[0] or 0)

    print(f"  Aktuální verze: v{aktualni}")
    for verze, sql in MIGRACE:
        if verze > aktualni:
            conn.executescript(sql)
            conn.execute("INSERT INTO schema_version VALUES (?)", (verze,))
            print(f"  Aplikována migrace v{verze}")
    conn.commit()


# ── 4. export_csv ─────────────────────────────────────────────────────────────

def export_csv(conn: sqlite3.Connection, tabulka: str, soubor: str) -> int:
    """
    Uloží tabulku do CSV souboru.
    Vrátí počet exportovaných řádků.
    Bezpečné: tabulka se ověří proti seznamu existujících tabulek.
    """
    # Ověříme, že tabulka existuje (ochrana proti SQL injection v názvu)
    existujici = {r[0] for r in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    ).fetchall()}
    if tabulka not in existujici:
        raise ValueError(f"Tabulka {tabulka!r} neexistuje. "
                         f"Dostupné: {sorted(existujici)}")

    rows = conn.execute(f"SELECT * FROM {tabulka}").fetchall()
    if not rows:
        print(f"  Tabulka {tabulka!r} je prázdná.")
        return 0

    with open(soubor, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(rows[0].keys())  # hlavička
        for row in rows:
            writer.writerow(list(row))

    print(f"  Exportováno {len(rows)} řádků do {soubor!r}")
    return len(rows)


# ── Demo ──────────────────────────────────────────────────────────────────────

print("=== StudentRepository + KurzRepository ===\n")

with get_db() as conn:
    s_repo = StudentRepository(conn)
    k_repo = KurzRepository(conn)

    # Vložení studentů
    m = s_repo.vloz(Student("Míša", "misa@x.cz", 15))
    t = s_repo.vloz(Student("Tomáš", "tomas@x.cz", 16))
    b = s_repo.vloz(Student("Bára", "bara@x.cz", 14))

    # 1. pocet()
    print(f"Počet studentů: {s_repo.pocet()}")

    # 2. KurzRepository
    py = k_repo.vloz(Kurz("Python základy", "Novák"))
    alg = k_repo.vloz(Kurz("Algoritmy", "Dvořák"))

    k_repo.zapis_studenta(m.id, py.id)
    k_repo.zapis_studenta(t.id, py.id)
    k_repo.zapis_studenta(m.id, alg.id)

    print(f"\nVšechny kurzy: {[k.nazev for k in k_repo.vsichni()]}")
    print(f"Studenti v Python základy: {[s['jmeno'] for s in k_repo.studenti_kurzu(py.id)]}")

    # Duplicitní zápis
    result = k_repo.zapis_studenta(m.id, py.id)
    print(f"Dvojitý zápis Míši do Pythonu: {result} (False = již zapsán)")

    # 4. export_csv
    print()
    export_csv(conn, "studenti", "/tmp/studenti_export.csv")
    export_csv(conn, "kurzy", "/tmp/kurzy_export.csv")

print("\n=== Migrace 4 a 5 ===\n")
with get_db() as conn:
    aplikuj_migrace(conn)
    print("\n  Druhé spuštění (nic neprovede):")
    aplikuj_migrace(conn)

    # Ověřit, že migrace 4 (sloupec role) existuje
    row = conn.execute("PRAGMA table_info(uzivatele)").fetchall()
    sloupce = [r["name"] for r in row]
    print(f"\n  Sloupce uzivatele: {sloupce}")

    # Ověřit, že migrace 5 (tabulka sessions) existuje
    existuje = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='sessions'"
    ).fetchone()
    print(f"  Tabulka sessions existuje: {existuje is not None}")
