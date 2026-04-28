"""Reseni – Lekce 60: Docker – kontejnerizace"""

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
DEMO_DIR  = Path("docker_reseni_demo")
DEMO_DIR.mkdir(exist_ok=True)


# 1. Dockerizace FastAPI aplikace (Dockerfile + docker-compose.yml)

print("=== Ukol 1: Dockerizace FastAPI (lekce 56) ===\n")

DOCKERFILE_FASTAPI = """\
# Multi-stage build pro FastAPI
FROM python:3.12-slim AS builder

WORKDIR /app

# Instalace zavislosti (cachujeme oddelene)
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# ─────────────────────────────────────────────────────────
FROM python:3.12-slim AS runtime

# Non-root uzivatel pro bezpecnost
RUN groupadd -r appgroup && useradd -r -g appgroup appuser

WORKDIR /app

# Preneseni instalovanych balicku z builderu
COPY --from=builder /root/.local /home/appuser/.local

# Kopirovani aplikace
COPY main.py .
COPY studenti_api/ ./studenti_api/

# Spravna vlastnicleni souboru
RUN chown -R appuser:appgroup /app

USER appuser

ENV PATH=/home/appuser/.local/bin:$PATH
ENV PYTHONPATH=/app

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \\
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
"""

REQUIREMENTS_TXT = """\
fastapi==0.115.0
uvicorn[standard]==0.32.0
pydantic==2.10.0
"""

DOCKER_COMPOSE_FASTAPI = """\
version: "3.9"

services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=sqlite:///data/studenti.db
      - SECRET_KEY=${SECRET_KEY}
      - DEBUG=false
    volumes:
      - api_data:/app/data
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 5s
      retries: 3
    restart: unless-stopped

volumes:
  api_data:
"""

for nazev, obsah in [
    ("Dockerfile",          DOCKERFILE_FASTAPI),
    ("requirements.txt",    REQUIREMENTS_TXT),
    ("docker-compose.yml",  DOCKER_COMPOSE_FASTAPI),
]:
    (DEMO_DIR / nazev).write_text(obsah, encoding="utf-8")
    print(f"  Vytvoren: {DEMO_DIR}/{nazev}")


# 2. Docker Compose s Nginx reverse proxy

print("\n=== Ukol 2: docker-compose s Nginx reverse proxy ===\n")

DOCKER_COMPOSE_NGINX = """\
version: "3.9"

services:
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/conf.d/default.conf:ro
      - ./certs:/etc/nginx/certs:ro
    depends_on:
      - api
    restart: unless-stopped

  api:
    build: .
    # Bez exportovani portu – Nginx pristupuje internou siti
    expose:
      - "8000"
    environment:
      - DATABASE_URL=sqlite:///data/studenti.db
      - SECRET_KEY=${SECRET_KEY:-nahrad-v-produkci}
    volumes:
      - api_data:/app/data
    restart: unless-stopped

volumes:
  api_data:
"""

NGINX_CONF = """\
# nginx.conf pro Python FastAPI
upstream api_backend {
    server api:8000;
    # Pro vice repliky:
    # server api_1:8000;
    # server api_2:8000;
}

server {
    listen 80;
    server_name kurz.example.com;

    # HTTP → HTTPS redirect
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl;
    server_name kurz.example.com;

    ssl_certificate     /etc/nginx/certs/cert.pem;
    ssl_certificate_key /etc/nginx/certs/key.pem;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN";
    add_header X-Content-Type-Options "nosniff";
    add_header X-XSS-Protection "1; mode=block";

    # Proxy nastaveni
    location / {
        proxy_pass         http://api_backend;
        proxy_set_header   Host             $host;
        proxy_set_header   X-Real-IP        $remote_addr;
        proxy_set_header   X-Forwarded-For  $proxy_add_x_forwarded_for;
        proxy_set_header   X-Forwarded-Proto https;
        proxy_read_timeout 60s;
    }

    # Staticke soubory prime pres Nginx (rychlejsi)
    location /static/ {
        alias /app/static/;
        expires 7d;
        add_header Cache-Control "public, immutable";
    }
}
"""

for nazev, obsah in [
    ("docker-compose-nginx.yml", DOCKER_COMPOSE_NGINX),
    ("nginx.conf",               NGINX_CONF),
]:
    (DEMO_DIR / nazev).write_text(obsah, encoding="utf-8")
    print(f"  Vytvoren: {DEMO_DIR}/{nazev}")

print("""
  Nginx jako reverse proxy:
    - SSL terminace (HTTP → HTTPS)
    - Load balancing mezi replikami API
    - Staticke soubory bez Python
    - Security headers
    - Logovani pristupovych logu
""")


# 3. GitHub Actions + DOCKERHUB_TOKEN

print("=== Ukol 3: GitHub Actions CI/CD + Docker Hub ===\n")

GH_ACTIONS_DOCKER = """\
# .github/workflows/docker.yml
# Nastaveni secrets v GitHub: Settings → Secrets → Actions
#   DOCKERHUB_USERNAME = tvoje-dockerhub-jmeno
#   DOCKERHUB_TOKEN    = osobni pristupovy token (Settings → Security → PAT)

name: Build & Push Docker image

on:
  push:
    branches: [main]
    tags: ["v*.*.*"]
  pull_request:
    branches: [main]

env:
  IMAGE_NAME: tvoje-jmeno/python-kurz

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install -r requirements.txt
      - run: pytest tests/ -v

  build-push:
    needs: test
    runs-on: ubuntu-latest
    if: github.event_name != 'pull_request'
    steps:
      - uses: actions/checkout@v4

      - name: Login to Docker Hub
        uses: docker/login-action@v3
        with:
          username: ${{ secrets.DOCKERHUB_USERNAME }}
          password: ${{ secrets.DOCKERHUB_TOKEN }}

      - name: Docker meta (tagy)
        id: meta
        uses: docker/metadata-action@v5
        with:
          images: ${{ env.IMAGE_NAME }}
          tags: |
            type=ref,event=branch
            type=semver,pattern={{version}}
            type=sha,prefix=sha-

      - name: Build and push
        uses: docker/build-push-action@v5
        with:
          context: .
          push: true
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
          cache-from: type=gha
          cache-to: type=gha,mode=max
"""

(DEMO_DIR / ".github" / "workflows").mkdir(parents=True, exist_ok=True)
(DEMO_DIR / ".github" / "workflows" / "docker.yml").write_text(GH_ACTIONS_DOCKER, encoding="utf-8")
print(f"  Vytvoren: {DEMO_DIR}/.github/workflows/docker.yml")

if DOCKER_OK:
    print("\n  Docker je dostupny – spust build:")
    print(f"    cd {DEMO_DIR} && docker build -t python-kurz-reseni .")
else:
    print("\n  Docker neni dostupny – soubory vygenerovany pro referenci")

import shutil
shutil.rmtree(DEMO_DIR, ignore_errors=True)
print("\nDemo slozka uklizena.")
