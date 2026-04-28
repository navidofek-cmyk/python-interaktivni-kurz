"""Reseni – Lekce 58: SQLAlchemy ORM"""

# vyžaduje: pip install sqlalchemy

try:
    import sqlalchemy as sa
    from sqlalchemy import create_engine, select, func, and_
    from sqlalchemy.orm import (
        DeclarativeBase, Mapped, mapped_column,
        relationship, Session,
    )
    SA_OK = True
except ImportError:
    print("SQLAlchemy neni nainstalovano: pip install sqlalchemy")
    SA_OK = False

from datetime import date, datetime

if not SA_OK:
    print("""
# Ukazka kodu (pro spusteni: pip install sqlalchemy)

class Hodnoceni(Base):
    __tablename__ = "hodnoceni"
    id:         Mapped[int]  = mapped_column(primary_key=True)
    zapis_id:   Mapped[int]  = mapped_column(sa.ForeignKey("zapisy.id"))
    komentar:   Mapped[str]  = mapped_column(sa.Text)
    datum:      Mapped[date] = mapped_column(default=date.today)
    zapis:      Mapped["Zapis"] = relationship(back_populates="hodnoceni")
""")
    exit()


# Schema

class Base(DeclarativeBase):
    pass


class Kurz(Base):
    __tablename__ = "kurzy"
    id:     Mapped[int] = mapped_column(primary_key=True)
    nazev:  Mapped[str] = mapped_column(sa.String(100))
    lektor: Mapped[str] = mapped_column(sa.String(50))
    kredity: Mapped[int] = mapped_column(default=3)
    zapisy: Mapped[list["Zapis"]] = relationship(back_populates="kurz")


class Student(Base):
    __tablename__ = "studenti"
    id:    Mapped[int] = mapped_column(primary_key=True)
    jmeno: Mapped[str] = mapped_column(sa.String(50))
    vek:   Mapped[int]
    zapisy: Mapped[list["Zapis"]] = relationship(back_populates="student")


class Zapis(Base):
    __tablename__ = "zapisy"
    id:         Mapped[int]   = mapped_column(primary_key=True)
    student_id: Mapped[int]   = mapped_column(sa.ForeignKey("studenti.id"))
    kurz_id:    Mapped[int]   = mapped_column(sa.ForeignKey("kurzy.id"))
    body:       Mapped[float] = mapped_column(default=0.0)
    datum:      Mapped[date]  = mapped_column(default=date.today)
    student:    Mapped["Student"] = relationship(back_populates="zapisy")
    kurz:       Mapped["Kurz"]    = relationship(back_populates="zapisy")
    # Ukol 1: vazba na Hodnoceni
    hodnoceni:  Mapped[list["Hodnoceni"]] = relationship(back_populates="zapis")


# Ukol 1: Pridat tabulku Hodnoceni(zapis_id, komentar, datum) s FK na Zapis
class Hodnoceni(Base):
    __tablename__ = "hodnoceni"
    id:       Mapped[int]  = mapped_column(primary_key=True)
    zapis_id: Mapped[int]  = mapped_column(sa.ForeignKey("zapisy.id"))
    komentar: Mapped[str]  = mapped_column(sa.Text)
    datum:    Mapped[date] = mapped_column(default=date.today)
    zapis:    Mapped["Zapis"] = relationship(back_populates="hodnoceni")


engine = create_engine("sqlite:///:memory:", echo=False)
Base.metadata.create_all(engine)


def naplnit_db(session: Session) -> None:
    kurzy = [
        Kurz(nazev="Python",       lektor="Novak",   kredity=4),
        Kurz(nazev="Matematika",   lektor="Dvorak",  kredity=3),
        Kurz(nazev="Databaze",     lektor="Novak",   kredity=3),
    ]
    session.add_all(kurzy)

    studenti = [
        Student(jmeno="Misa",  vek=15),
        Student(jmeno="Tomas", vek=16),
        Student(jmeno="Bara",  vek=14),
        Student(jmeno="Ondra", vek=17),
    ]
    session.add_all(studenti)
    session.flush()

    zapisy = [
        Zapis(student=studenti[0], kurz=kurzy[0], body=87.5),
        Zapis(student=studenti[0], kurz=kurzy[1], body=92.0),
        Zapis(student=studenti[0], kurz=kurzy[2], body=78.0),
        Zapis(student=studenti[1], kurz=kurzy[0], body=75.0),
        Zapis(student=studenti[1], kurz=kurzy[1], body=88.0),
        Zapis(student=studenti[2], kurz=kurzy[0], body=65.0),
        Zapis(student=studenti[3], kurz=kurzy[0], body=95.0),
        Zapis(student=studenti[3], kurz=kurzy[1], body=91.0),
        Zapis(student=studenti[3], kurz=kurzy[2], body=89.0),
    ]
    session.add_all(zapisy)
    session.flush()

    # Ukol 1: Pridat hodnoceni k zapiNum
    hodnoceni_data = [
        Hodnoceni(zapis=zapisy[0], komentar="Vyborny vykon, aktivni student"),
        Hodnoceni(zapis=zapisy[1], komentar="Vzorne splneno"),
        Hodnoceni(zapis=zapisy[6], komentar="Skvele, nejlepsi v rocniku"),
    ]
    session.add_all(hodnoceni_data)
    session.commit()


with Session(engine) as session:
    naplnit_db(session)

    print("=== Ukol 1: Hodnoceni tabulka ===\n")

    dotaz = select(Hodnoceni).join(Hodnoceni.zapis).join(Zapis.student)
    for h in session.scalars(dotaz):
        print(f"  {h.datum} | {h.zapis.student.jmeno} | {h.komentar[:50]}")


    print("\n=== Ukol 2: Studenti zapsani na VSECHNY kurzy ===\n")

    pocet_kurzu = session.scalar(select(func.count()).select_from(Kurz))

    # Studenti s poctem distinct kurzu == celkovy pocet kurzu
    dotaz_vsechny = (
        select(Student.jmeno, func.count(func.distinct(Zapis.kurz_id)).label("n_kurzu"))
        .join(Student.zapisy)
        .group_by(Student.id)
        .having(func.count(func.distinct(Zapis.kurz_id)) == pocet_kurzu)
    )

    print(f"  Celkovy pocet kurzu: {pocet_kurzu}")
    print(f"  Studenti zapsani na vsechny kurzy:")
    for radek in session.execute(dotaz_vsechny):
        print(f"    {radek.jmeno} ({radek.n_kurzu} kurzu)")


    print("\n=== Ukol 3: Alembic migrace (pridat sloupec) ===\n")

    # Alembic vyžaduje: pip install alembic
    # Ukázka bez spusteni

    ALEMBIC_INIT = """\
# 1. Inicializace
#   alembic init migrations
#   → vytvoří migrations/ + alembic.ini

# 2. Uprav alembic.ini:
#   sqlalchemy.url = sqlite:///kurz.db

# 3. Vygeneruj migraci (Alembic porovná model vs DB):
#   alembic revision --autogenerate -m "pridat_poznamka_sloupec"

# 4. Generovana migrace (migrations/versions/xxx_pridat_poznamka.py):
from alembic import op
import sqlalchemy as sa

def upgrade():
    op.add_column("studenti", sa.Column("poznamka", sa.Text(), nullable=True))

def downgrade():
    op.drop_column("studenti", "poznamka")

# 5. Spust migraci:
#   alembic upgrade head

# 6. Rollback:
#   alembic downgrade -1
"""
    print(ALEMBIC_INIT)

print("SQLAlchemy reseni dokonceno.")
