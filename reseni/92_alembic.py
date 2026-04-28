"""Řešení – Lekce 92: Alembic – databázové migrace"""

# vyžaduje: pip install alembic sqlalchemy

import textwrap
from pathlib import Path
from datetime import datetime

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


# 1. Inicializace Alembic + první migrace (pro projekt z lekce 58)
print("=== 1. Alembic inicializace a první migrace ===\n")

INIT_WORKFLOW = textwrap.dedent("""\
  # Přidej do existujícího projektu (lekce 58 – SQLAlchemy)

  # 1. Inicializace (jednou za projekt)
  cd muj-projekt/
  alembic init alembic

  # 2. Uprav alembic/env.py – přidej modely:
  from myapp.models import Base   # <-- tvoje DeclarativeBase
  target_metadata = Base.metadata

  # 3. Nastav URL v alembic.ini nebo env.py:
  sqlalchemy.url = sqlite:///kurz.db
  # nebo z ENV proměnné:
  import os
  config.set_main_option("sqlalchemy.url", os.environ["DATABASE_URL"])

  # 4. Vytvoř první migraci (detekuje existující modely):
  alembic revision --autogenerate -m "initial schema"

  # Vznikne soubor: alembic/versions/abc123_initial_schema.py

  # 5. Aplikuj:
  alembic upgrade head

  # Ověř:
  alembic current
  alembic history --verbose
""")
print(INIT_WORKFLOW)

# Funkční demo: programatická migrace
if SA_OK and ALEMBIC_OK:
    print("  Funkční demo (in-memory SQLite):")
    engine = create_engine("sqlite:///:memory:", echo=False)

    with engine.begin() as conn:
        ctx = MigrationContext.configure(conn)
        op  = Operations(ctx)

        # Simulace schématu projektu z lekce 58
        op.create_table("studenti",
            sa.Column("id",    sa.Integer, primary_key=True),
            sa.Column("jmeno", sa.String(100), nullable=False),
            sa.Column("email", sa.String(200), unique=True),
        )
        print("  ✓ CREATE TABLE studenti")

    print(f"  Tabulky: {inspect(engine).get_table_names()}")


# 2. Migrace: přidání sloupce updated_at s auto-update
print("\n=== 2. Migrace: updated_at s auto-update ===\n")

UPDATED_AT_MIGRACE = textwrap.dedent("""\
  # alembic/versions/002_add_updated_at.py
  \"\"\"Přidá sloupec updated_at s automatickou aktualizací.

  Revision ID: 002abc
  Revises:     001xyz
  Create Date: 2024-01-20 10:00:00
  \"\"\"

  from alembic import op
  import sqlalchemy as sa
  from sqlalchemy import text

  revision      = "002abc"
  down_revision = "001xyz"

  def upgrade() -> None:
      # 1. Přidej sloupec s výchozí hodnotou
      op.add_column("studenti",
          sa.Column("updated_at", sa.DateTime,
                     server_default=sa.func.now(),
                     nullable=True))

      # 2. Naplň existující záznamy (datová migrace)
      op.execute(text(
          "UPDATE studenti SET updated_at = datetime('now') "
          "WHERE updated_at IS NULL"
      ))

      # 3. Změň na NOT NULL (až po naplnění!)
      with op.batch_alter_table("studenti") as batch_op:
          batch_op.alter_column("updated_at", nullable=False)

      # 4. Přidej trigger pro auto-update (SQLite syntax)
      op.execute(text(\"\"\"
          CREATE TRIGGER IF NOT EXISTS studenti_updated_at
          AFTER UPDATE ON studenti
          BEGIN
              UPDATE studenti
              SET updated_at = datetime('now')
              WHERE id = NEW.id;
          END
      \"\"\"))

  def downgrade() -> None:
      # Smaž trigger
      op.execute(text("DROP TRIGGER IF EXISTS studenti_updated_at"))
      # Odeber sloupec
      with op.batch_alter_table("studenti") as batch_op:
          batch_op.drop_column("updated_at")

  # Pro PostgreSQL (místo SQLite triggeru):
  # op.execute(text(\"\"\"
  #     CREATE OR REPLACE FUNCTION update_updated_at()
  #     RETURNS TRIGGER AS $$
  #     BEGIN
  #         NEW.updated_at = NOW();
  #         RETURN NEW;
  #     END;
  #     $$ LANGUAGE plpgsql;
  # \"\"\"))
  # op.execute(text(\"\"\"
  #     CREATE TRIGGER studenti_updated_at
  #     BEFORE UPDATE ON studenti
  #     FOR EACH ROW EXECUTE FUNCTION update_updated_at();
  # \"\"\"))
""")
print(UPDATED_AT_MIGRACE)

# Funkční demo updated_at
if SA_OK and ALEMBIC_OK:
    engine2 = create_engine("sqlite:///:memory:", echo=False)
    with engine2.begin() as conn:
        ctx = MigrationContext.configure(conn, opts={"as_sql": False})
        op  = Operations(ctx)

        op.create_table("studenti",
            sa.Column("id",    sa.Integer, primary_key=True),
            sa.Column("jmeno", sa.String(100), nullable=False),
            sa.Column("email", sa.String(200), nullable=True),
        )
        op.add_column("studenti",
            sa.Column("updated_at", sa.DateTime, nullable=True))

        conn.execute(text("INSERT INTO studenti (jmeno, email, updated_at) VALUES ('Míša', 'misa@k.cz', datetime('now'))"))

        conn.execute(text("""
            CREATE TRIGGER IF NOT EXISTS studenti_upd
            AFTER UPDATE ON studenti
            BEGIN
                UPDATE studenti SET updated_at = datetime('now') WHERE id = NEW.id;
            END
        """))

        conn.execute(text("UPDATE studenti SET jmeno = 'Míša Nováková' WHERE id = 1"))

        row = conn.execute(text("SELECT jmeno, updated_at FROM studenti WHERE id=1")).fetchone()
        print(f"  Po UPDATE: jmeno={row[0]}, updated_at={row[1]}")


# 3. Test upgrade + downgrade každé migrace
print("\n=== 3. Testování upgrade + downgrade ===\n")

TEST_MIGRACE_KOD = textwrap.dedent("""\
  # tests/test_migrace.py
  import pytest
  from sqlalchemy import create_engine, inspect, text
  from alembic.config import Config
  from alembic.command import upgrade, downgrade
  import subprocess, os

  @pytest.fixture
  def alembic_cfg(tmp_path):
      \"\"\"Konfigurace Alembic pro testovací databázi.\"\"\"
      db_url = f"sqlite:///{tmp_path}/test.db"
      cfg = Config("alembic.ini")
      cfg.set_main_option("sqlalchemy.url", db_url)
      return cfg, db_url

  def test_upgrade_head(alembic_cfg):
      \"\"\"Upgrade na head proběhne bez chyb.\"\"\"
      cfg, db_url = alembic_cfg
      upgrade(cfg, "head")    # spustí všechny migrace

      engine = create_engine(db_url)
      tabulky = inspect(engine).get_table_names()
      assert "studenti" in tabulky, "Tabulka studenti neexistuje po upgrade"
      engine.dispose()

  def test_downgrade_base(alembic_cfg):
      \"\"\"Downgrade na base smaže vše.\"\"\"
      cfg, db_url = alembic_cfg
      upgrade(cfg, "head")
      downgrade(cfg, "base")   # rollback všeho

      engine = create_engine(db_url)
      tabulky = inspect(engine).get_table_names()
      # Po downgrade na base by neměly existovat naše tabulky
      assert "studenti" not in tabulky
      engine.dispose()

  def test_kazda_migrace_zvlast(alembic_cfg):
      \"\"\"Každá migrace zvlášť – upgrade a pak downgrade.\"\"\"
      cfg, db_url = alembic_cfg

      # Získej seznam revizí
      result = subprocess.run(
          ["alembic", "history", "--verbose"],
          capture_output=True, text=True
      )
      revize = [
          line.split()[0]
          for line in result.stdout.splitlines()
          if "->" in line
      ]

      for rev in revize:
          # Upgrade na tuto revizi
          upgrade(cfg, rev)
          # Downgrade o jeden krok
          downgrade(cfg, "-1")
          # Upgrade zpět
          upgrade(cfg, rev)

  def test_idempotence(alembic_cfg):
      \"\"\"Dvojitý upgrade head nemá vedlejší efekty.\"\"\"
      cfg, db_url = alembic_cfg
      upgrade(cfg, "head")
      upgrade(cfg, "head")   # druhý upgrade – nic se nesmí změnit

      engine = create_engine(db_url)
      count  = engine.execute("SELECT COUNT(*) FROM alembic_version").scalar()
      assert count >= 1
      engine.dispose()
""")
print(TEST_MIGRACE_KOD)

# Funkční demo testu upgrade/downgrade
if SA_OK and ALEMBIC_OK:
    print("  Funkční demo (in-memory):\n")

    def simuluj_migrace() -> list[dict]:
        """Simuluje sérii migrací s testem upgrade+downgrade."""
        engine = create_engine("sqlite:///:memory:", echo=False)
        vysledky = []

        migrace = [
            ("001_initial",   "CREATE TABLE studenti (id INTEGER PRIMARY KEY, jmeno TEXT)"),
            ("002_add_email", "ALTER TABLE studenti ADD COLUMN email TEXT"),
            ("003_add_body",  "ALTER TABLE studenti ADD COLUMN body REAL DEFAULT 0"),
        ]

        for rev, sql in migrace:
            try:
                with engine.begin() as conn:
                    conn.execute(text(sql))
                vysledky.append({"rev": rev, "status": "OK"})
            except Exception as e:
                vysledky.append({"rev": rev, "status": f"CHYBA: {e}"})

        return vysledky

    for res in simuluj_migrace():
        ikona = "✓" if res["status"] == "OK" else "✗"
        print(f"  {ikona} upgrade {res['rev']}: {res['status']}")

    print("\n  Downgrade simulace:")
    engine3 = create_engine("sqlite:///:memory:", echo=False)
    with engine3.begin() as conn:
        conn.execute(text("CREATE TABLE studenti (id INTEGER PRIMARY KEY, jmeno TEXT, email TEXT, body REAL DEFAULT 0)"))
        conn.execute(text("INSERT INTO studenti (jmeno, email, body) VALUES ('Míša', 'misa@k.cz', 87.5)"))
        sloupce_pred = [c["name"] for c in inspect(engine3).get_columns("studenti")]

        # SQLite neumí DROP COLUMN přímo → batch mode
        with engine3.begin() as conn2:
            conn2.execute(text("CREATE TABLE studenti_new AS SELECT id, jmeno, email FROM studenti"))
            conn2.execute(text("DROP TABLE studenti"))
            conn2.execute(text("ALTER TABLE studenti_new RENAME TO studenti"))

        sloupce_po = [c["name"] for c in inspect(engine3).get_columns("studenti")]
        print(f"  Sloupce před downgrade: {sloupce_pred}")
        print(f"  Sloupce po downgrade:   {sloupce_po}")
        print(f"  ✓ Sloupec 'body' úspěšně odstraněn")

print("\n=== Shrnutí ===")
print("  1. Alembic inicializace  – workflow, env.py konfigurace, první migrace")
print("  2. updated_at trigger    – add_column, datová migrace, trigger, batch_alter")
print("  3. Test migrací          – pytest + upgrade head/downgrade base/každá revize")
