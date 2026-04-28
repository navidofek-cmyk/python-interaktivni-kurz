"""Řešení – Lekce 90: OpenTelemetry – observabilita"""

# vyžaduje: pip install opentelemetry-api opentelemetry-sdk

import time
import uuid
import json
import random
from functools import wraps
from contextlib import contextmanager
from datetime import datetime
from collections import defaultdict

# ── Vlastní span implementace (z originální lekce) ───────────────
class Span:
    def __init__(self, jmeno: str, parent_id: str | None = None,
                 trace_id: str | None = None):
        self.trace_id  = trace_id or uuid.uuid4().hex[:16]
        self.span_id   = uuid.uuid4().hex[:8]
        self.parent_id = parent_id
        self.jmeno     = jmeno
        self.zacatek   = time.perf_counter()
        self.konec     = None
        self.atributy: dict = {}
        self.udalosti: list = []
        self.status    = "OK"

    def set_attribute(self, klic: str, hodnota):
        self.atributy[klic] = hodnota

    def add_event(self, jmeno: str, **attrs):
        self.udalosti.append({"jmeno": jmeno, "cas": time.perf_counter(), **attrs})

    def end(self):
        self.konec = time.perf_counter()

    @property
    def trvani_ms(self) -> float:
        return ((self.konec or time.perf_counter()) - self.zacatek) * 1000

_aktivni_span: list[Span] = []
_dokoncene_spany: list[Span] = []

@contextmanager
def span(jmeno: str, **attrs):
    parent = _aktivni_span[-1] if _aktivni_span else None
    s = Span(jmeno,
              parent_id=parent.span_id if parent else None,
              trace_id=parent.trace_id if parent else None)
    for k, v in attrs.items():
        s.set_attribute(k, v)
    _aktivni_span.append(s)
    try:
        yield s
    except Exception as e:
        s.status = f"ERROR: {type(e).__name__}: {e}"
        raise
    finally:
        s.end()
        _aktivni_span.pop()
        _dokoncene_spany.append(s)


# 1. FastAPI auto-instrumentace (ukázka kódu)
print("=== 1. FastAPI auto-instrumentace ===\n")

FASTAPI_OTEL_KOD = '''\
# main.py s OpenTelemetry auto-instrumentací
from fastapi import FastAPI
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor

# 1. Nastav Jaeger exportér
jaeger_exporter = JaegerExporter(
    agent_host_name="localhost",
    agent_port=6831,
)
provider = TracerProvider()
provider.add_span_processor(BatchSpanProcessor(jaeger_exporter))
trace.set_tracer_provider(provider)

# 2. Vytvoř FastAPI app
app = FastAPI()

# 3. Auto-instrumentace – přidá trace pro KAŽDÝ request automaticky
FastAPIInstrumentor.instrument_app(app)         # HTTP requesty
SQLAlchemyInstrumentor().instrument()            # DB dotazy
HTTPXClientInstrumentor().instrument()           # outgoing HTTP

# 4. Ruční trace pro business logiku
tracer = trace.get_tracer("moje-aplikace")

@app.get("/studenti/{id}")
async def get_student(id: int):
    with tracer.start_as_current_span("business.get_student") as s:
        s.set_attribute("student.id", id)
        # ... logika ...
        return {"id": id}

# Spuštění:
#   pip install opentelemetry-instrumentation-fastapi \\
#               opentelemetry-instrumentation-sqlalchemy \\
#               opentelemetry-exporter-jaeger
#   uvicorn main:app
# Jaeger UI: http://localhost:16686
'''
print(FASTAPI_OTEL_KOD)


# 2. Decorator @traced(jmeno) – obalí funkci do spanu
print("=== 2. Decorator @traced(jmeno) ===\n")

def traced(jmeno: str | None = None, **extra_attrs):
    """
    Dekorátor který obalí funkci do trace spanu.
    Automaticky zachytí argumenty, výjimky a návratovou hodnotu.
    """
    def dekorator(fn):
        span_jmeno = jmeno or f"{fn.__module__}.{fn.__qualname__}"

        @wraps(fn)
        def wrapper(*args, **kwargs):
            with span(span_jmeno, **extra_attrs) as s:
                # Zaznamenej volání
                s.set_attribute("function.name", fn.__qualname__)
                if args:
                    s.set_attribute("function.args_count", len(args))
                if kwargs:
                    s.set_attribute("function.kwargs",
                                     json.dumps(list(kwargs.keys())))

                try:
                    result = fn(*args, **kwargs)
                    s.set_attribute("function.success", True)
                    return result
                except Exception as e:
                    s.set_attribute("function.error", str(e))
                    s.add_event("exception", type=type(e).__name__, message=str(e))
                    raise

        @wraps(fn)
        async def async_wrapper(*args, **kwargs):
            with span(span_jmeno, **extra_attrs) as s:
                s.set_attribute("function.name", fn.__qualname__)
                try:
                    result = await fn(*args, **kwargs)
                    s.set_attribute("function.success", True)
                    return result
                except Exception as e:
                    s.set_attribute("function.error", str(e))
                    raise

        import asyncio
        return async_wrapper if asyncio.iscoroutinefunction(fn) else wrapper

    return dekorator

# Demo
@traced("service.autentizace", layer="auth")
def over_token(token: str) -> bool:
    time.sleep(0.001)
    return len(token) > 10

@traced("service.db_query", layer="db")
def nacti_studenta(student_id: int) -> dict:
    time.sleep(0.003)
    if student_id > 100:
        raise LookupError(f"Student {student_id} nenalezen")
    return {"id": student_id, "jmeno": "Míša", "body": 87.5}

@traced("service.cache_update", layer="cache")
def aktualizuj_cache(key: str, value: dict):
    time.sleep(0.001)

@traced("api.zpracuj_pozadavek", layer="api")
def zpracuj_pozadavek(student_id: int, token: str):
    platny = over_token(token)
    if not platny:
        raise PermissionError("Neplatný token")
    student = nacti_studenta(student_id)
    aktualizuj_cache(f"student:{student_id}", student)
    return student

# Spusť s úspěchem
_dokoncene_spany.clear()
print("Trace pro úspěšný požadavek:")
try:
    vysledek = zpracuj_pozadavek(1, "platny-token-xyz")
    print(f"  Výsledek: {vysledek}")
except Exception as e:
    print(f"  Chyba: {e}")

for s in _dokoncene_spany:
    odsaz = "    " if s.parent_id else "  "
    ikona = "✓" if s.status == "OK" else "✗"
    print(f"  {odsaz}{ikona} [{s.trvani_ms:5.1f}ms] {s.jmeno}  "
          f"layer={s.atributy.get('layer', '?')}")

# Spusť s chybou
_dokoncene_spany.clear()
print("\nTrace pro chybový požadavek:")
try:
    zpracuj_pozadavek(999, "platny-token-xyz")
except LookupError as e:
    print(f"  Chyba: {e}")

for s in _dokoncene_spany:
    odsaz = "    " if s.parent_id else "  "
    ikona = "✓" if s.status == "OK" else "✗"
    print(f"  {odsaz}{ikona} [{s.trvani_ms:5.1f}ms] {s.jmeno}  {s.status[:50]}")


# 3. Prometheus /metrics endpoint pro FastAPI
print("\n=== 3. Prometheus metrics endpoint ===\n")

class PrometheusMetrics:
    """Jednoduchý Prometheus metrics registry."""

    def __init__(self, prefix: str = "app"):
        self.prefix   = prefix
        self.countery: dict[str, dict] = {}     # {metric: {labels: count}}
        self.gaugy:    dict[str, float] = {}    # {metric: value}
        self.histogramy: dict[str, list[float]] = {}  # {metric: [values]}

    def counter_inc(self, jmeno: str, labels: dict | None = None, hodnota: float = 1):
        klic = jmeno
        self.countery.setdefault(klic, defaultdict(float))
        label_klic = json.dumps(labels or {}, sort_keys=True)
        self.countery[klic][label_klic] += hodnota

    def gauge_set(self, jmeno: str, hodnota: float):
        self.gaugy[jmeno] = hodnota

    def histogram_obs(self, jmeno: str, hodnota: float):
        self.histogramy.setdefault(jmeno, [])
        self.histogramy[jmeno].append(hodnota)

    def generuj_text(self) -> str:
        """Generuje Prometheus text format."""
        radky = []

        for jmeno, labels_dict in self.countery.items():
            full = f"{self.prefix}_{jmeno}_total"
            radky.append(f"# TYPE {full} counter")
            for label_json, hodnota in labels_dict.items():
                labels = json.loads(label_json)
                lbl_str = ",".join(f'{k}="{v}"' for k, v in labels.items())
                radky.append(f'{full}{{{lbl_str}}} {hodnota}')

        for jmeno, hodnota in self.gaugy.items():
            full = f"{self.prefix}_{jmeno}"
            radky.append(f"# TYPE {full} gauge")
            radky.append(f"{full} {hodnota}")

        for jmeno, values in self.histogramy.items():
            full = f"{self.prefix}_{jmeno}"
            radky.append(f"# TYPE {full} histogram")
            if values:
                radky.append(f"{full}_count {len(values)}")
                radky.append(f"{full}_sum {sum(values):.3f}")
                for q in [0.5, 0.9, 0.99]:
                    idx = int(q * len(values))
                    radky.append(f'{full}{{quantile="{q}"}} {sorted(values)[idx]:.3f}')

        return "\n".join(radky)


# Simulace provozu
metrics = PrometheusMetrics(prefix="api")

for _ in range(100):
    metoda  = random.choice(["GET", "POST"])
    status  = random.choices([200, 404, 500], weights=[85, 10, 5])[0]
    latence = abs(random.gauss(50, 20))

    metrics.counter_inc("requests", {"method": metoda, "status": str(status)})
    metrics.histogram_obs("request_duration_ms", latence)

metrics.gauge_set("active_connections", random.randint(5, 50))
metrics.gauge_set("memory_mb", random.uniform(128, 512))

print("Prometheus /metrics výstup:\n")
print(metrics.generuj_text())

# FastAPI endpoint příklad
FASTAPI_METRICS_KOD = '''
# FastAPI /metrics endpoint
from fastapi import FastAPI, Response

app = FastAPI()
metrics = PrometheusMetrics(prefix="api")

@app.middleware("http")
async def track_metrics(request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    latence = (time.perf_counter() - start) * 1000
    metrics.counter_inc("requests", {
        "method": request.method,
        "path":   request.url.path,
        "status": str(response.status_code),
    })
    metrics.histogram_obs("request_duration_ms", latence)
    return response

@app.get("/metrics")
def get_metrics():
    return Response(
        content=metrics.generuj_text(),
        media_type="text/plain; version=0.0.4",
    )
'''
print(FASTAPI_METRICS_KOD)

print("=== Shrnutí ===")
print("  1. FastAPI auto-instrumentace – FastAPIInstrumentor.instrument_app()")
print("  2. @traced() dekorátor       – automatický span pro každou funkci")
print("  3. PrometheusMetrics         – counter/gauge/histogram, /metrics endpoint")
