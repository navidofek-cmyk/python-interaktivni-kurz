"""
LEKCE 92: Alembic – databázové migrace
========================================
pip install alembic sqlalchemy

Alembic = verzování schématu databáze (jako git pro DB).
Navazuje na SQLAlchemy z lekce 58.

Bez Alembic: ruční ALTER TABLE, ztráta dat, chaos v týmu.
S Alembic:   verze schématu, automatické migrace, rollback.

Workflow:
  1. Změň SQLAlchemy modely
  2. alembic revision --autogenerate -m "přidej sloupec"
  3. alembic upgrade head
  4. (případně: alembic downgrade -1)
"""

import textwrap
import subprocess
import shutil
from pathlib import Path
from datetime import datetime

# ══════════════════════════════════════════════════════════════
# ČÁST 1: Alembic bez CLI – programaticky
# ══════════════════════════════════════════════════════════════

print("=== Alembic – databázové migrace ===\n")

try:
    import sqlalchemy as sa
    from sqlalchemy import create_engine, text, inspect
    from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
    SA_OK = True
except ImportError:
    SA_OK = False
    print("SQLAlchemy není nainstalováno: pip install sqlalchemy alembic")

try:
    import alembic
    from alembic.config import Config
    from alembic.runtime.migration import MigrationContext
    from alembic.operations import Operations
    ALEMBIC_OK = True
except ImportError:
    ALEMBIC_OK = False
    print("Alembic není nainstalováno: pip install alembic")

if SA_OK and ALEMBIC_OK:
    # Vytvoř databázi v paměti
    engine = create_engine("sqlite:///:memory:", echo=False)

    print("--- Programatické migrace (bez CLI) ---\n")

    with engine.begin() as conn:
        ctx = MigrationContext.configure(conn)
        op  = Operations(ctx)

        # MIGRACE v0 → v1: vytvoření tabulky
        print("Migrace v0 → v1: vytvoření tabulky studenti")
        op.create_table("studenti",
            sa.Column("id",    sa.Integer, primary_key=True),
            sa.Column("jmeno", sa.String(100), nullable=False),
            sa.Column("email", sa.String(200), unique=True),
        )
        print("  ✓ CREATE TABLE studenti")

        # MIGRACE v1 → v2: přidání sloupce
        print("\nMigrace v1 → v2: přidání sloupce body + vytvoreno")
        op.add_column("studenti",
            sa.Column("body", sa.Float, server_default="0.0"))
        op.add_column("studenti",
            sa.Column("vytvoreno", sa.DateTime,
                       server_default=sa.func.now()))
        print("  ✓ ALTER TABLE studenti ADD COLUMN body")
        print("  ✓ ALTER TABLE studenti ADD COLUMN vytvoreno")

        # MIGRACE v2 → v3: index + cizí klíč
        print("\nMigrace v2 → v3: nová tabulka + index")
        op.create_table("kurzy",
            sa.Column("id",    sa.Integer, primary_key=True),
            sa.Column("nazev", sa.String(100), nullable=False),
        )
        op.create_table("zapisy",
            sa.Column("student_id", sa.Integer,
                       sa.ForeignKey("studenti.id"), nullable=False),
            sa.Column("kurz_id",    sa.Integer,
                       sa.ForeignKey("kurzy.id"),    nullable=False),
            sa.Column("body",       sa.Float),
        )
        op.create_index("idx_zapisy_student", "zapisy", ["student_id"])
        print("  ✓ CREATE TABLE kurzy")
        print("  ✓ CREATE TABLE zapisy")
        print("  ✓ CREATE INDEX idx_zapisy_student")

        # Vložení dat
        conn.execute(text("INSERT INTO studenti (jmeno, email, body) VALUES "
                          "('Míša', 'misa@k.cz', 87.5), "
                          "('Tomáš', 'tomas@k.cz', 92.0)"))

        # Zobraz stav
        insp = inspect(engine)
        print(f"\nTabulky: {insp.get_table_names()}")
        print("\nSloupce studenti:")
        for col in insp.get_columns("studenti"):
            print(f"  {col['name']:<15} {str(col['type']):<15} "
                  f"nullable={col['nullable']}")

        # ROLLBACK migrace – odeber sloupec
        print("\nRollback: odebrání sloupce vytvoreno")
        op.drop_column("studenti", "vytvoreno")
        print("  ✓ DROP COLUMN vytvoreno")


# ══════════════════════════════════════════════════════════════
# ČÁST 2: Alembic CLI projekt – kompletní workflow
# ══════════════════════════════════════════════════════════════

print("\n=== Alembic CLI workflow ===\n")
print(textwrap.dedent("""\
  # 1. Inicializace (jednou)
  alembic init alembic

  # Vznikne:
  alembic/
  ├── env.py          ← konfigurace (sem přidej sqlalchemy_url)
  ├── script.py.mako  ← šablona pro migrace
  └── versions/       ← migrace jako soubory

  # 2. Nastav databázi v alembic.ini nebo env.py:
  sqlalchemy.url = sqlite:///kurz.db
  # nebo v env.py:
  config.set_main_option("sqlalchemy.url", os.environ["DATABASE_URL"])

  # 3. Vytvoř první migraci ručně nebo autogenerací:
  alembic revision --autogenerate -m "initial schema"
  # nebo ručně:
  alembic revision -m "add body column"

  # 4. Spusť migrace:
  alembic upgrade head        # na nejnovější verzi
  alembic upgrade +2          # o 2 kroky vpřed
  alembic downgrade -1        # o 1 krok zpět
  alembic downgrade base      # zpět na začátek

  # 5. Informace:
  alembic current             # aktuální verze
  alembic history --verbose   # seznam migrací
  alembic show <revision>     # detail migrace
"""))


# ══════════════════════════════════════════════════════════════
# ČÁST 3: Generovaný migrační soubor
# ══════════════════════════════════════════════════════════════

print("=== Příklad migračního souboru ===\n")
print(textwrap.dedent("""\
  # alembic/versions/abc123_add_body_column.py
  \"\"\"Přidá sloupec body do studenti.

  Revision ID: abc123def456
  Revises: previous_revision
  Create Date: 2024-01-15 10:30:00
  \"\"\"

  from alembic import op
  import sqlalchemy as sa

  revision  = "abc123def456"
  down_revision = "previous_revision"
  branch_labels = None
  depends_on = None

  def upgrade() -> None:
      # Přidej sloupec body
      op.add_column("studenti",
          sa.Column("body", sa.Float, nullable=True, server_default="0.0"))

      # Přidej index na email
      op.create_index("ix_studenti_email", "studenti", ["email"], unique=True)

      # Proveď datovou migraci (naplň sloupec)
      op.execute(
          "UPDATE studenti SET body = 0.0 WHERE body IS NULL"
      )

      # Změň NULL na NOT NULL teprve po naplnění
      op.alter_column("studenti", "body", nullable=False)

  def downgrade() -> None:
      # Vždy implementuj rollback!
      op.drop_index("ix_studenti_email")
      op.drop_column("studenti", "body")
"""))


# ══════════════════════════════════════════════════════════════
# ČÁST 4: Integrace s SQLAlchemy modely
# ══════════════════════════════════════════════════════════════

print("\n=== env.py konfigurace s modely ===\n")
print(textwrap.dedent("""\
  # alembic/env.py – klíčové části

  from logging.config import fileConfig
  from sqlalchemy import engine_from_config, pool
  from alembic import context
  import os

  # Importuj VŠECHNY modely aby Alembic je viděl
  from myapp.models import Base   # DeclarativeBase
  target_metadata = Base.metadata

  def run_migrations_online():
      # Připoj k DB a spusť migrace
      url = os.environ.get("DATABASE_URL", config.get_main_option("sqlalchemy.url"))
      connectable = create_engine(url, poolclass=pool.NullPool)

      with connectable.connect() as connection:
          context.configure(
              connection=connection,
              target_metadata=target_metadata,
              compare_type=True,        # detekuj změny typů
              compare_server_default=True,
              render_as_batch=True,     # NUTNÉ pro SQLite ALTER!
          )
          with context.begin_transaction():
              context.run_migrations()
"""))

print("""
=== Best practices ===

  ✓ Vždy implementuj downgrade() – rollback je záchrana
  ✓ Datové migrace odděl od schématu (2 soubory)
  ✓ Testuj migrace na kopii produkční DB
  ✓ render_as_batch=True pro SQLite (neumí ALTER nativně)
  ✓ Commituj migrační soubory do gitu
  ✓ Nikdy neupravuj existující migraci – vytvoř novou
  ✓ CI/CD: alembic upgrade head před spuštěním aplikace
""")

# TVOJE ÚLOHA:
# 1. Inicializuj Alembic v projektu z lekce 58 a vytvoř první migraci.
# 2. Napiš migraci která přidá sloupec updated_at s auto-update triggerem.
# 3. Napiš test který ověří upgrade + downgrade každé migrace.
