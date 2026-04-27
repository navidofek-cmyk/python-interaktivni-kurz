"""
LEKCE 60: Docker – kontejnerizace Python aplikací
===================================================
Docker = zabalení aplikace + závislostí + prostředí do jednoho kontejneru.
Funguje stejně na tvém počítači, CI serveru i v produkci.

Tato lekce:
  1. Generuje reálné Docker soubory pro Python projekty
  2. Ukazuje best practices (multi-stage, non-root user, .dockerignore)
  3. Spustí docker příkazy pokud je Docker k dispozici

Proč Docker:
  "U mě to funguje" → "Funguje to všude"
  Izolace závislostí, verzí Pythonu
  Snadné škálování a deployment
"""

import subprocess
import sys
import textwrap
from pathlib import Path

def docker_dostupny() -> bool:
    try:
        r = subprocess.run(["docker", "version", "--format", "{{.Server.Version}}"],
                          capture_output=True, text=True, timeout=5)
        return r.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False

DOCKER_OK = docker_dostupny()

# ══════════════════════════════════════════════════════════════
# ČÁST 1: Dockerfile pro různé typy aplikací
# ══════════════════════════════════════════════════════════════

print("=== Generuji Docker soubory ===\n")

demo_dir = Path("docker_demo")
demo_dir.mkdir(exist_ok=True)

# ── 1. Základní Python skript ─────────────────────────────────
(demo_dir / "app.py").write_text(textwrap.dedent('''
    from flask import Flask, jsonify
    import os

    app = Flask(__name__)

    @app.get("/")
    def index():
        return jsonify({
            "zprava": "Python v Dockeru!",
            "prostredi": os.getenv("ENV", "development"),
        })

    @app.get("/health")
    def health():
        return jsonify({"status": "ok"})

    if __name__ == "__main__":
        app.run(host="0.0.0.0", port=8000)
''').lstrip())

(demo_dir / "requirements.txt").write_text("flask==3.0.0\ngunicorn==21.2.0\n")

# ── 2. Produkční Dockerfile (multi-stage) ────────────────────
DOCKERFILE_PROD = '''\
# ── Stage 1: Builder ──────────────────────────────────────────
FROM python:3.12-slim AS builder

WORKDIR /app

# Zkopíruj jen requirements – vrstva se cachuje pokud se nezmění
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt


# ── Stage 2: Runtime ──────────────────────────────────────────
FROM python:3.12-slim AS runtime

# Non-root uživatel (bezpečnost!)
RUN groupadd -r appuser && useradd -r -g appuser appuser

WORKDIR /app

# Zkopíruj nainstalované závislosti z builderu
COPY --from=builder /install /usr/local

# Zkopíruj zdrojový kód
COPY --chown=appuser:appuser . .

# Přepni na non-root uživatele
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s \\
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"

EXPOSE 8000

# Produkční server (gunicorn místo flask dev serveru)
CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:8000", "--workers", "4"]
'''

(demo_dir / "Dockerfile").write_text(DOCKERFILE_PROD)
print("  ✓ Dockerfile (multi-stage, non-root)")

# ── 3. .dockerignore ─────────────────────────────────────────
(demo_dir / ".dockerignore").write_text(textwrap.dedent('''\
    __pycache__/
    *.pyc
    *.pyo
    .venv/
    venv/
    .git/
    .env
    *.log
    tests/
    docs/
    .pytest_cache/
    .mypy_cache/
    dist/
    build/
'''))
print("  ✓ .dockerignore")

# ── 4. docker-compose.yml ────────────────────────────────────
COMPOSE = '''\
version: "3.9"

services:
  web:
    build: .
    ports:
      - "8000:8000"
    environment:
      - ENV=production
      - DATABASE_URL=postgresql://user:pass@db:5432/kurz
    depends_on:
      db:
        condition: service_healthy
    restart: unless-stopped
    volumes:
      - ./logs:/app/logs    # persisted logs

  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: user
      POSTGRES_PASSWORD: pass
      POSTGRES_DB: kurz
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD", "pg_isready", "-U", "user"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data

  worker:
    build: .
    command: celery -A celery_app worker --loglevel=info
    environment:
      - CELERY_BROKER_URL=redis://redis:6379/0
    depends_on:
      - redis
      - db

volumes:
  postgres_data:
  redis_data:
'''

(demo_dir / "docker-compose.yml").write_text(COMPOSE)
print("  ✓ docker-compose.yml (web + db + redis + worker)")

# ── 5. Makefile pro Docker příkazy ───────────────────────────
MAKEFILE = '''\
.PHONY: build run stop logs shell test

build:
\tdocker build -t python-kurz .

run:
\tdocker run -p 8000:8000 --env-file .env python-kurz

stop:
\tdocker stop $(docker ps -q --filter ancestor=python-kurz)

logs:
\tdocker logs -f $(docker ps -q --filter ancestor=python-kurz)

shell:
\tdocker exec -it $(docker ps -q --filter ancestor=python-kurz) /bin/bash

compose-up:
\tdocker-compose up -d

compose-down:
\tdocker-compose down

compose-logs:
\tdocker-compose logs -f

test:
\tdocker build --target builder -t python-kurz-test .
\tdocker run --rm python-kurz-test pytest tests/
'''

(demo_dir / "Makefile").write_text(MAKEFILE)
print("  ✓ Makefile")


# ══════════════════════════════════════════════════════════════
# ČÁST 2: Best practices a patterny
# ══════════════════════════════════════════════════════════════

print(f"\n=== Best practices ===\n")

TIPY = [
    ("python:3.12-slim místo python:3.12",
     "Slim = bez dev nástrojů → 100+ MB menší image"),

    ("Multi-stage build",
     "Builder stage instaluje závislosti, runtime stage je čistá → menší finální image"),

    (".dockerignore vždy",
     "Bez něj se kopíruje .venv, .git, testy → zbytečně velký context"),

    ("Non-root user",
     "Pokud kontejner kompromitován, útočník nemá root → menší škoda"),

    ("COPY requirements.txt DŘÍVE než kód",
     "Docker cachuje vrstvy – pokud se requirements nezmění, pip install se přeskočí"),

    ("Gunicorn v produkci",
     "Flask dev server je single-threaded a nezabezpečený pro produkci"),

    ("HEALTHCHECK",
     "Docker/Kubernetes ví jestli aplikace opravdu běží, nejen jestli je proces živý"),

    ("Proměnné přes ENV/secrets",
     "Nikdy nehardcoduj hesla do Dockerfile – používej env variables nebo Docker secrets"),
]

for tip, vysvetleni in TIPY:
    print(f"  ✓ {tip}")
    print(f"    → {vysvetleni}\n")


# ══════════════════════════════════════════════════════════════
# ČÁST 3: Spuštění pokud Docker dostupný
# ══════════════════════════════════════════════════════════════

if DOCKER_OK:
    print("=== Docker je dostupný – zkusíme build ===\n")

    def spust_docker(cmd: list[str], popis: str):
        print(f"$ docker {' '.join(cmd[1:])}")
        r = subprocess.run(cmd, capture_output=True, text=True, cwd=str(demo_dir))
        if r.returncode == 0:
            print(f"  ✓ {popis}")
        else:
            print(f"  ✗ Chyba: {r.stderr[:200]}")
        return r.returncode == 0

    spust_docker(["docker", "build", "-t", "python-kurz-demo", "."], "Build")
    spust_docker(["docker", "image", "ls", "python-kurz-demo"], "Zobrazení image")
    spust_docker(["docker", "image", "rm", "python-kurz-demo"], "Cleanup")

else:
    print("=== Docker není dostupný – zobrazuji příkazy ===\n")
    prikazy = [
        ("Sestavení image",           "docker build -t moje-app ."),
        ("Spuštění kontejneru",       "docker run -p 8000:8000 moje-app"),
        ("Spuštění na pozadí",        "docker run -d -p 8000:8000 moje-app"),
        ("Zobrazení běžících",        "docker ps"),
        ("Logy kontejneru",           "docker logs <container_id>"),
        ("Shell v kontejneru",        "docker exec -it <container_id> bash"),
        ("Zastavení",                 "docker stop <container_id>"),
        ("Zobrazení images",          "docker images"),
        ("Smazání image",             "docker rmi moje-app"),
        ("Docker Compose up",         "docker-compose up -d"),
        ("Docker Compose down",       "docker-compose down"),
        ("Push na Docker Hub",        "docker push uzivatel/moje-app:latest"),
    ]
    for popis, cmd in prikazy:
        print(f"  {popis:<30} {cmd}")


# ══════════════════════════════════════════════════════════════
# ČÁST 4: GitHub Actions + Docker
# ══════════════════════════════════════════════════════════════

CI_PIPELINE = '''\
# .github/workflows/docker.yml
name: Build & Push Docker image

on:
  push:
    branches: [main]
    tags: ["v*"]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Login to Docker Hub
        uses: docker/login-action@v3
        with:
          username: ${{ secrets.DOCKERHUB_USERNAME }}
          password: ${{ secrets.DOCKERHUB_TOKEN }}

      - name: Build and push
        uses: docker/build-push-action@v5
        with:
          push: true
          tags: |
            uzivatel/python-kurz:latest
            uzivatel/python-kurz:${{ github.sha }}
          cache-from: type=gha
          cache-to: type=gha,mode=max
'''

print(f"\n=== GitHub Actions CI/CD pipeline ===")
print(textwrap.indent(CI_PIPELINE, "  "))

import shutil
shutil.rmtree(demo_dir, ignore_errors=True)

# TVOJE ÚLOHA:
# 1. Dockerizuj lekci 56 (FastAPI) – přidej Dockerfile a docker-compose.yml.
# 2. Přidej do docker-compose.yml Nginx jako reverse proxy před web service.
# 3. Nastav GitHub Actions secret DOCKERHUB_TOKEN a pushni image na Docker Hub.
