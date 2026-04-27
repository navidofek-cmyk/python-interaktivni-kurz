"""
LEKCE 58: SQLAlchemy – ORM
============================
pip install sqlalchemy

ORM = Object-Relational Mapping.
Místo SQL dotazů pracuješ s Python objekty.
SQLAlchemy = nejpopulárnější ORM pro Python.

Core  – nízkoúrovňový SQL builder
ORM   – Python třídy ↔ databázové tabulky

SQLAlchemy 2.0 (moderní API):
  mapped_column() + Mapped[] místo Column()
  Session jako context manager
  select() místo query()
"""

try:
    import sqlalchemy as sa
    from sqlalchemy import create_engine, select, func, and_, or_
    from sqlalchemy.orm import (
        DeclarativeBase, Mapped, mapped_column,
        relationship, Session, selectinload,
    )
    SA_OK = True
except ImportError:
    print("SQLAlchemy není nainstalováno: pip install sqlalchemy")
    SA_OK = False

from datetime import datetime, date
from typing import Optional
import textwrap

if not SA_OK:
    exit()

# ══════════════════════════════════════════════════════════════
# ČÁST 1: MODELY (deklarativní styl)
# ══════════════════════════════════════════════════════════════

print("=== Definice modelů ===\n")

class Base(DeclarativeBase):
    pass

class Student(Base):
    __tablename__ = "studenti"

    id:       Mapped[int]           = mapped_column(primary_key=True)
    jmeno:    Mapped[str]           = mapped_column(sa.String(50))
    email:    Mapped[str]           = mapped_column(sa.String(100), unique=True)
    vek:      Mapped[int]
    zapsano:  Mapped[datetime]      = mapped_column(default=datetime.now)

    # Vztah 1:N – student má mnoho zápisů
    zapisy:   Mapped[list["Zapis"]] = relationship(back_populates="student",
                                                    cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"Student(id={self.id}, jmeno={self.jmeno!r}, vek={self.vek})"

class Kurz(Base):
    __tablename__ = "kurzy"

    id:       Mapped[int] = mapped_column(primary_key=True)
    nazev:    Mapped[str] = mapped_column(sa.String(100))
    lektor:   Mapped[Optional[str]] = mapped_column(sa.String(50), nullable=True)
    kapacita: Mapped[int] = mapped_column(default=30)

    zapisy:   Mapped[list["Zapis"]] = relationship(back_populates="kurz")

    def __repr__(self) -> str:
        return f"Kurz(id={self.id}, nazev={self.nazev!r})"

class Zapis(Base):
    __tablename__ = "zapisy"

    id:         Mapped[int]       = mapped_column(primary_key=True)
    student_id: Mapped[int]       = mapped_column(sa.ForeignKey("studenti.id"))
    kurz_id:    Mapped[int]       = mapped_column(sa.ForeignKey("kurzy.id"))
    datum:      Mapped[date]      = mapped_column(default=date.today)
    body:       Mapped[Optional[float]] = mapped_column(nullable=True)

    student:    Mapped["Student"] = relationship(back_populates="zapisy")
    kurz:       Mapped["Kurz"]    = relationship(back_populates="zapisy")

# ── Vytvoření databáze ────────────────────────────────────────
engine = create_engine("sqlite:///:memory:", echo=False)
Base.metadata.create_all(engine)
print("Tabulky vytvořeny:", Base.metadata.tables.keys())


# ══════════════════════════════════════════════════════════════
# ČÁST 2: CRUD operace
# ══════════════════════════════════════════════════════════════

print("\n=== CRUD ===\n")

with Session(engine) as session:
    # CREATE
    studenti = [
        Student(jmeno="Míša",  email="misa@k.cz",  vek=15),
        Student(jmeno="Tomáš", email="tomas@k.cz", vek=16),
        Student(jmeno="Bára",  email="bara@k.cz",  vek=14),
        Student(jmeno="Ondra", email="ondra@k.cz", vek=17),
        Student(jmeno="Klára", email="klara@k.cz", vek=15),
    ]
    kurzy = [
        Kurz(nazev="Python základy", lektor="Novák",   kapacita=20),
        Kurz(nazev="Algoritmy",      lektor="Dvořák",  kapacita=15),
        Kurz(nazev="Web vývoj",      lektor="Procházka", kapacita=25),
    ]
    session.add_all(studenti + kurzy)
    session.flush()  # přiřadí ID bez commitu

    # Zápisy
    zapisy_data = [
        (1, 1, 87.5), (1, 2, 92.0),
        (2, 1, 78.3), (3, 1, 95.1), (3, 3, 88.0),
        (4, 2, 72.0), (5, 1, 65.5), (5, 3, 81.0),
    ]
    for sid, kid, body in zapisy_data:
        session.add(Zapis(student_id=sid, kurz_id=kid, body=body))

    session.commit()
    print("Data vložena.")

    # READ – select()
    vsichni = session.scalars(select(Student).order_by(Student.jmeno)).all()
    print(f"\nVšichni studenti ({len(vsichni)}):")
    for s in vsichni:
        print(f"  {s}")

    # Filtrování
    mladi = session.scalars(
        select(Student).where(Student.vek <= 15).order_by(Student.jmeno)
    ).all()
    print(f"\nStudenti ≤15 let: {[s.jmeno for s in mladi]}")

    # UPDATE
    misa = session.scalar(select(Student).where(Student.jmeno == "Míša"))
    misa.vek = 16
    session.commit()
    print(f"\nPo úpravě: {misa}")

    # DELETE
    klara = session.scalar(select(Student).where(Student.jmeno == "Klára"))
    session.delete(klara)
    session.commit()
    print(f"Klára smazána. Zbývá: {session.scalar(select(func.count()).select_from(Student))} studentů")


# ══════════════════════════════════════════════════════════════
# ČÁST 3: VZTAHY A EAGER LOADING
# ══════════════════════════════════════════════════════════════

print("\n=== Vztahy a loading ===\n")

with Session(engine) as session:
    # selectinload – načte vztahy jedním dotazem navíc (N+1 problem fix)
    studenti_se_zapisy = session.scalars(
        select(Student)
        .options(selectinload(Student.zapisy).selectinload(Zapis.kurz))
        .order_by(Student.jmeno)
    ).all()

    for student in studenti_se_zapisy:
        kurzy_jmena = [z.kurz.nazev for z in student.zapisy]
        print(f"  {student.jmeno:<10} → {kurzy_jmena}")


# ══════════════════════════════════════════════════════════════
# ČÁST 4: AGREGACE A SLOŽITÉ DOTAZY
# ══════════════════════════════════════════════════════════════

print("\n=== Agregace ===\n")

with Session(engine) as session:
    # Průměrné body na kurz
    vysledek = session.execute(
        select(Kurz.nazev, func.avg(Zapis.body).label("prumer"),
               func.count(Zapis.id).label("pocet"))
        .join(Zapis, Kurz.id == Zapis.kurz_id)
        .group_by(Kurz.id)
        .order_by(func.avg(Zapis.body).desc())
    ).all()

    print("Průměrné body na kurz:")
    for nazev, prumer, pocet in vysledek:
        print(f"  {nazev:<20} {prumer:.1f} bodů  ({pocet} studentů)")

    # Studenti s body nad průměrem
    prumer_subq = select(func.avg(Zapis.body)).scalar_subquery()
    nad_prumerem = session.scalars(
        select(Student)
        .join(Zapis)
        .where(Zapis.body > prumer_subq)
        .distinct()
    ).all()
    print(f"\nStudenti nad průměrem: {[s.jmeno for s in nad_prumerem]}")


# ══════════════════════════════════════════════════════════════
# ČÁST 5: REPOSITORY PATTERN + UNIT OF WORK
# ══════════════════════════════════════════════════════════════

print("\n=== Repository pattern ===\n")

class StudentRepo:
    def __init__(self, session: Session):
        self.session = session

    def vloz(self, jmeno: str, email: str, vek: int) -> Student:
        student = Student(jmeno=jmeno, email=email, vek=vek)
        self.session.add(student)
        return student

    def ziskej(self, id: int) -> Optional[Student]:
        return self.session.get(Student, id)

    def vsichni(self) -> list[Student]:
        return list(self.session.scalars(select(Student).order_by(Student.jmeno)))

    def hledej_email(self, email: str) -> Optional[Student]:
        return self.session.scalar(select(Student).where(Student.email == email))

    def smaz(self, student: Student) -> None:
        self.session.delete(student)

with Session(engine) as session:
    repo = StudentRepo(session)

    novy = repo.vloz("Pavel", "pavel@k.cz", 18)
    session.flush()
    print(f"Vložen: {novy}")
    print(f"Všichni: {[s.jmeno for s in repo.vsichni()]}")

    nalezen = repo.hledej_email("misa@k.cz")
    print(f"Hledám misa@k.cz: {nalezen}")

    session.commit()

print("""
=== SQLAlchemy vs raw SQL ===

  Raw SQL   → maximální kontrola, výkon, složité dotazy
  SQLAlchemy Core → SQL builder s Python API
  SQLAlchemy ORM  → Python objekty, vztahy, pohodlí

  Pro produkci: SQLAlchemy + Alembic (migrace schématu)
  pip install alembic
""")

# TVOJE ÚLOHA:
# 1. Přidej tabulku Hodnoceni(zapis_id, komentar, datum) s FK na Zapis.
# 2. Napiš dotaz: studenti kteří jsou zapsáni na VŠECHNY kurzy.
# 3. Přidej Alembic migrace – alembic init, vytvoř migraci pro přidání sloupce.
