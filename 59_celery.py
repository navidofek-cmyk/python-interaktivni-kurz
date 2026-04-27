"""
LEKCE 59: Celery – background tasky a fronty
=============================================
pip install celery redis
(nebo: pip install celery[redis])

Celery = distribuovaná fronta úkolů.
Broker = prostředník (Redis, RabbitMQ) – ukládá frontu tasků.
Worker = proces který tasky zpracovává.

Kdy použít:
  - Posílání emailů (nečekej na uživatele)
  - Generování reportů, PDF
  - Zpracování obrázků / videí
  - Periodické úkoly (cron)
  - Dlouhé výpočty (ML, simulace)

Architektura:
  Web app → [task.delay()] → Broker (Redis) → Worker → výsledek

Tato lekce simuluje Celery bez nutnosti Redis/broker,
ukazuje koncepty a připravený produkční kód.
"""

import time
import threading
import queue
import uuid
import json
import functools
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import Any, Callable
from enum import Enum
from pathlib import Path

# ══════════════════════════════════════════════════════════════
# ČÁST 1: Simulace Celery bez brokeru
# ══════════════════════════════════════════════════════════════

print("=== Simulace task fronty ===\n")

class TaskStatus(Enum):
    PENDING  = "pending"
    RUNNING  = "running"
    SUCCESS  = "success"
    FAILURE  = "failure"
    RETRY    = "retry"

@dataclass
class TaskResult:
    task_id:   str
    status:    TaskStatus
    result:    Any = None
    error:     str | None = None
    started:   datetime | None = None
    finished:  datetime | None = None
    retries:   int = 0

    @property
    def trvani(self) -> float | None:
        if self.started and self.finished:
            return (self.finished - self.started).total_seconds()
        return None

class TaskRegistry:
    """Registr výsledků (v prod = Redis/backend)."""
    def __init__(self):
        self._store: dict[str, TaskResult] = {}
        self._zamek = threading.Lock()

    def uloz(self, vysledek: TaskResult):
        with self._zamek:
            self._store[vysledek.task_id] = vysledek

    def ziskej(self, task_id: str) -> TaskResult | None:
        return self._store.get(task_id)

    def vsechny(self) -> list[TaskResult]:
        return list(self._store.values())

registry = TaskRegistry()

def task(max_retries: int = 3, retry_delay: float = 1.0):
    """Dekorátor simulující @app.task z Celery."""
    def dekorator(fn: Callable) -> Callable:
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            return fn(*args, **kwargs)

        def delay(*args, **kwargs) -> str:
            """Zařadí task do fronty, vrátí task_id."""
            task_id = str(uuid.uuid4())[:8]
            vysledek = TaskResult(task_id=task_id, status=TaskStatus.PENDING)
            registry.uloz(vysledek)

            def run():
                vysledek.status  = TaskStatus.RUNNING
                vysledek.started = datetime.now()
                registry.uloz(vysledek)

                for pokus in range(max_retries + 1):
                    try:
                        result = fn(*args, **kwargs)
                        vysledek.status   = TaskStatus.SUCCESS
                        vysledek.result   = result
                        vysledek.finished = datetime.now()
                        registry.uloz(vysledek)
                        return
                    except Exception as e:
                        if pokus < max_retries:
                            vysledek.status  = TaskStatus.RETRY
                            vysledek.retries = pokus + 1
                            registry.uloz(vysledek)
                            time.sleep(retry_delay * (2 ** pokus))  # exp. backoff
                        else:
                            vysledek.status   = TaskStatus.FAILURE
                            vysledek.error    = str(e)
                            vysledek.finished = datetime.now()
                            registry.uloz(vysledek)

            t = threading.Thread(target=run, daemon=True)
            t.start()
            return task_id

        wrapper.delay = delay
        wrapper.max_retries = max_retries
        return wrapper
    return dekorator


# ── Definice tasků ────────────────────────────────────────────

@task(max_retries=2)
def posli_email(komu: str, predmet: str, text: str) -> dict:
    """Simuluje odesílání emailu."""
    time.sleep(0.3)
    print(f"    📧 Email → {komu}: {predmet!r}")
    return {"stav": "odesláno", "komu": komu, "cas": datetime.now().isoformat()}

@task(max_retries=3, retry_delay=0.2)
def generuj_report(uzivatel_id: int, format: str = "pdf") -> str:
    """Simuluje generování reportu (občas selže)."""
    import random
    time.sleep(0.5)
    if random.random() < 0.3:   # 30% šance selhání
        raise ConnectionError("Databáze nedostupná")
    print(f"    📄 Report vygenerován pro user={uzivatel_id}")
    return f"/reports/{uzivatel_id}_{format}_{int(time.time())}.{format}"

@task()
def zpracuj_obrazek(cesta: str, sirka: int, vyska: int) -> dict:
    """Simuluje resize obrázku."""
    time.sleep(0.4)
    print(f"    🖼️  Resize {cesta} → {sirka}×{vyska}")
    return {"vstup": cesta, "sirka": sirka, "vyska": vyska, "stav": "hotovo"}

@task()
def vypocti_statistiky(data: list[float]) -> dict:
    """CPU-bound výpočet na pozadí."""
    n = len(data)
    prumer = sum(data) / n
    variance = sum((x - prumer)**2 for x in data) / n
    return {
        "n": n,
        "prumer": round(prumer, 3),
        "std": round(variance**0.5, 3),
        "min": min(data),
        "max": max(data),
    }


# ── Spuštění tasků ────────────────────────────────────────────

print("Spouštím tasky na pozadí...\n")

task_ids = [
    posli_email.delay("misa@k.cz",  "Vítej!", "Ahoj Míšo!"),
    posli_email.delay("tomas@k.cz", "Report", "Tvůj report je hotov."),
    generuj_report.delay(42, "pdf"),
    generuj_report.delay(99, "xlsx"),
    zpracuj_obrazek.delay("foto.jpg", 800, 600),
    vypocti_statistiky.delay([3.14, 2.71, 1.41, 1.73, 2.23, 0.57, 1.62]),
]

# Čekej na dokončení
time.sleep(2.5)

print("\nVýsledky:")
print(f"{'Task ID':<10} {'Status':<12} {'Trvání':<10} {'Výsledek/Chyba'}")
print("─" * 70)
for tid in task_ids:
    r = registry.ziskej(tid)
    if r:
        trvani = f"{r.trvani:.2f}s" if r.trvani else "…"
        info = str(r.result)[:30] if r.result else (r.error or "")
        retry = f" (retry {r.retries}×)" if r.retries else ""
        print(f"{r.task_id:<10} {r.status.value:<12} {trvani:<10} {info}{retry}")


# ══════════════════════════════════════════════════════════════
# ČÁST 2: Periodické tasky (Beat scheduler)
# ══════════════════════════════════════════════════════════════

print("\n=== Periodické tasky ===\n")

@dataclass
class PeriodicTask:
    nazev:    str
    fn:       Callable
    interval: float        # sekundy
    _posledni: float = field(default_factory=time.time)

    def je_cas(self) -> bool:
        return time.time() - self._posledni >= self.interval

    def spust(self):
        self._posledni = time.time()
        self.fn()

def cisteni_db():
    print(f"  🗄️  [{datetime.now().strftime('%H:%M:%S')}] Čistím staré záznamy...")

def kontrola_zdravi():
    print(f"  💚 [{datetime.now().strftime('%H:%M:%S')}] Health check OK")

def backup():
    print(f"  💾 [{datetime.now().strftime('%H:%M:%S')}] Záloha dokončena")

periodicke = [
    PeriodicTask("cisteni_db",     cisteni_db,     interval=0.3),
    PeriodicTask("kontrola_zdravi", kontrola_zdravi, interval=0.5),
    PeriodicTask("backup",         backup,          interval=0.8),
]

print("Beat scheduler běží 2 sekundy:")
konec = time.time() + 2.0
while time.time() < konec:
    for pt in periodicke:
        if pt.je_cas():
            pt.spust()
    time.sleep(0.05)


# ══════════════════════════════════════════════════════════════
# ČÁST 3: Reálný Celery kód (pro referenci)
# ══════════════════════════════════════════════════════════════

CELERY_KOD = '''
# celery_app.py
from celery import Celery
from celery.schedules import crontab

app = Celery(
    "moje_app",
    broker="redis://localhost:6379/0",     # Redis jako broker
    backend="redis://localhost:6379/1",    # Redis pro výsledky
)

app.conf.update(
    task_serializer="json",
    result_expires=3600,    # výsledky expirují po 1h
    timezone="Europe/Prague",
    beat_schedule={
        # Spusť každý den v 8:00
        "denni-report": {
            "task": "tasks.generuj_report",
            "schedule": crontab(hour=8, minute=0),
            "args": (0, "pdf"),
        },
        # Každých 5 minut
        "health-check": {
            "task": "tasks.kontrola_zdravi",
            "schedule": 300,
        },
    },
)

# tasks.py
@app.task(bind=True, max_retries=3)
def posli_email(self, komu, predmet, text):
    try:
        # smtp_send(komu, predmet, text)
        return {"stav": "odesláno"}
    except Exception as exc:
        raise self.retry(exc=exc, countdown=60)

# Použití v Django/FastAPI:
# posli_email.delay("user@example.com", "Vítej", "...")
# posli_email.apply_async(args=[...], countdown=300)  # za 5 minut

# Spuštění:
# celery -A celery_app worker --loglevel=info
# celery -A celery_app beat --loglevel=info    # pro periodicke tasky
# celery -A celery_app flower                  # monitoring UI
'''

print("\n=== Produkční Celery kód ===")
print(textwrap.indent(CELERY_KOD, "  "))

import textwrap

# TVOJE ÚLOHA:
# 1. Přidej task chain: posli_email.delay() po dokončení generuj_report.
# 2. Přidej task group: zpracuj 10 obrázků paralelně a počkej na všechny.
# 3. Nainstaluj Redis + Celery a spusť skutečné tasky.
