"""Reseni – Lekce 59: Celery – background tasky"""

# Produkční Celery vyžaduje: pip install celery redis
# Tato lekce simuluje Celery bez serveru

import time
import threading
import queue
import uuid
import json
import functools
import textwrap
from dataclasses import dataclass, field
from typing import Callable, Any
from datetime import datetime
from enum import Enum


# Kopie simulatoru z originalni lekce

class StavTasku(Enum):
    PENDING  = "PENDING"
    STARTED  = "STARTED"
    SUCCESS  = "SUCCESS"
    FAILURE  = "FAILURE"
    RETRY    = "RETRY"


@dataclass
class Task:
    id:        str
    fn:        Callable
    args:      tuple
    kwargs:    dict
    stav:      StavTasku = StavTasku.PENDING
    vysledek:  Any = None
    chyba:     str | None = None
    max_retries: int = 3
    retries:   int = 0


class SimpleQueue:
    def __init__(self, workers: int = 2):
        self._fronta:  queue.Queue = queue.Queue()
        self._vysledky: dict[str, Task] = {}
        self._zamek   = threading.Lock()
        self._workers = [
            threading.Thread(target=self._worker, daemon=True)
            for _ in range(workers)
        ]
        for w in self._workers:
            w.start()

    def _worker(self) -> None:
        while True:
            task: Task = self._fronta.get()
            with self._zamek:
                task.stav = StavTasku.STARTED
            try:
                task.vysledek = task.fn(*task.args, **task.kwargs)
                with self._zamek:
                    task.stav = StavTasku.SUCCESS
            except Exception as e:
                task.retries += 1
                if task.retries <= task.max_retries:
                    with self._zamek:
                        task.stav = StavTasku.RETRY
                    time.sleep(0.1)
                    self._fronta.put(task)
                else:
                    with self._zamek:
                        task.stav    = StavTasku.FAILURE
                        task.chyba   = str(e)
            self._fronta.task_done()

    def delay(self, fn: Callable, *args, **kwargs) -> str:
        task_id = str(uuid.uuid4())[:8]
        task    = Task(id=task_id, fn=fn, args=args, kwargs=kwargs)
        with self._zamek:
            self._vysledky[task_id] = task
        self._fronta.put(task)
        return task_id

    def stav(self, task_id: str) -> Task | None:
        return self._vysledky.get(task_id)

    def cekej(self, task_id: str, timeout: float = 5.0) -> Any:
        konec = time.time() + timeout
        while time.time() < konec:
            task = self.stav(task_id)
            if task and task.stav in (StavTasku.SUCCESS, StavTasku.FAILURE):
                return task.vysledek
            time.sleep(0.05)
        raise TimeoutError(f"Task {task_id} nesplneno v {timeout}s")


broker = SimpleQueue(workers=3)


# 1. Task chain: posli_email po dokonceni generuj_report

print("=== Ukol 1: Task chain – report → email ===\n")


def generuj_report(uzivatel_id: int, format_: str = "pdf") -> dict:
    """Generuje report pro uzivatele."""
    time.sleep(0.2)  # simulace generovani
    return {
        "uzivatel_id": uzivatel_id,
        "format": format_,
        "soubor": f"report_{uzivatel_id}.{format_}",
        "cas": datetime.now().strftime("%H:%M:%S"),
    }


def posli_email(komu: str, predmet: str, text: str) -> dict:
    """Posle email."""
    time.sleep(0.1)  # simulace SMTP
    return {"stav": "odeslano", "komu": komu, "predmet": predmet}


def chain(*fns_args: tuple[Callable, tuple]) -> Any:
    """Spusti tasky v retezci – vystup prvniho je vstup druheho.
    Kazdy tuple: (fn, extra_args_krome_predchoziho_vysledku)
    """
    vysledek = None
    for fn, extra_args in fns_args:
        if vysledek is None:
            vysledek = fn(*extra_args)
        else:
            vysledek = fn(vysledek, *extra_args)
    return vysledek


def report_a_email(uzivatel_id: int, email: str) -> dict:
    """Chain: vygeneruj report a posli email s potvrzenim."""
    report = generuj_report(uzivatel_id, "pdf")
    notifikace = posli_email(
        komu=email,
        predmet="Vas report je pripraven",
        text=f"Report byl vygenerovan: {report['soubor']}",
    )
    return {"report": report, "email": notifikace}


# Spust chain
id1 = broker.delay(report_a_email, 42, "student@example.com")
id2 = broker.delay(report_a_email, 43, "dalsi@example.com")

for task_id, uzivatel in [(id1, 42), (id2, 43)]:
    vysl = broker.cekej(task_id)
    print(f"  Uzivatel {uzivatel}: report={vysl['report']['soubor']}  email={vysl['email']['stav']}")


# 2. Task group: zpracuj 10 obrazku paralelne a pockej na vsechny

print("\n=== Ukol 2: Task group – 10 obrazku paralelne ===\n")


def zpracuj_obrazek(obrazek_id: int, operace: str = "resize") -> dict:
    """Simulace zpracovani obrazku."""
    import random
    time.sleep(random.uniform(0.05, 0.2))
    return {
        "id":      obrazek_id,
        "operace": operace,
        "vysledek": f"{operace}_{obrazek_id}.jpg",
    }


# Spust vsech 10 paralelne
task_ids = [
    broker.delay(zpracuj_obrazek, i, "resize")
    for i in range(10)
]

print(f"  Spusteno {len(task_ids)} tasku paralelne...")

# Cekej na vsechny
t0 = time.perf_counter()
vysledky = [broker.cekej(tid, timeout=5.0) for tid in task_ids]
elapsed = time.perf_counter() - t0

print(f"  Vsechny hotovy za {elapsed:.2f}s (paralelne, ne sekv.)")
print(f"  Vzorky: {[v['vysledek'] for v in vysledky[:3]]}")


# 3. Realna Celery instalace a spusteni

print("\n=== Ukol 3: Realna Celery konfigurace ===\n")

# vyžaduje: pip install celery redis
CELERY_CHAIN_GROUP = textwrap.dedent("""\
    # vyžaduje: pip install celery redis

    from celery import Celery, chain, group, chord

    app = Celery("moje_app", broker="redis://localhost:6379/0",
                 backend="redis://localhost:6379/1")

    @app.task
    def generuj_report(uzivatel_id: int, format_: str) -> dict:
        # ... logika generovani
        return {"soubor": f"report_{uzivatel_id}.{format_}"}

    @app.task
    def posli_email(report: dict, komu: str) -> dict:
        # smtp_send(komu, report['soubor'])
        return {"stav": "odeslano"}

    # Ukol 1: chain – posli_email po dokonceni generuj_report
    vysledek = chain(
        generuj_report.s(42, "pdf"),
        posli_email.s("student@example.com"),
    ).delay()

    # Ukol 2: group – 10 obrazku paralelne
    jobs = group(zpracuj_obrazek.s(i) for i in range(10))
    vysledek_group = jobs.apply_async()
    vsechny = vysledek_group.get(timeout=30)

    # Chord = group + callback po dokonceni vsech
    vysledky = chord(
        group(zpracuj_obrazek.s(i) for i in range(10)),
        callback=zaloguj_vsechny.s()
    ).delay()

    # Spusteni:
    # redis-server
    # celery -A tasks worker --loglevel=info -c 4
    # celery -A tasks beat --loglevel=info    # periodicke tasky
""")

print(CELERY_CHAIN_GROUP)
