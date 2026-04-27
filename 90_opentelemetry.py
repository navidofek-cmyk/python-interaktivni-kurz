"""
LEKCE 90: OpenTelemetry – observabilita
==========================================
pip install opentelemetry-api opentelemetry-sdk

Observabilita = schopnost porozumět co se děje uvnitř systému.
Tři pilíře: Traces, Metrics, Logs

OpenTelemetry (OTel) = open-source standard pro všechny tři.
Vendor-neutral: exportuj do Jaeger, Prometheus, Datadog, Grafana...

Traces  – průchod požadavku systémem (span A → span B → span C)
Metrics – čísla v čase (latence, počet požadavků, chybovost)
Logs    – strukturované záznamy událostí
"""

print("=== OpenTelemetry – observabilita ===\n")

try:
    from opentelemetry import trace, metrics
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import (
        SimpleSpanProcessor, ConsoleSpanExporter, BatchSpanProcessor,
    )
    from opentelemetry.sdk.metrics import MeterProvider
    from opentelemetry.sdk.metrics.export import (
        ConsoleMetricExporter, PeriodicExportingMetricReader,
    )
    from opentelemetry.trace import Status, StatusCode
    from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator
    OTEL_OK = True
except ImportError:
    print("OpenTelemetry není nainstalováno:")
    print("  pip install opentelemetry-api opentelemetry-sdk")
    OTEL_OK = False

import time
import random
import json
import threading
from functools import wraps
from contextlib import contextmanager
from collections import defaultdict, deque
from datetime import datetime

# ══════════════════════════════════════════════════════════════
# ČÁST 1: Traces – sledování průchodu požadavku
# ══════════════════════════════════════════════════════════════

if OTEL_OK:
    print("--- Traces ---\n")

    # Nastav TracerProvider s Console exportérem
    provider = TracerProvider()
    provider.add_span_processor(SimpleSpanProcessor(ConsoleSpanExporter()))
    trace.set_tracer_provider(provider)

    tracer = trace.get_tracer("python-kurz", "1.0.0")

    # Simulace HTTP požadavku přes vrstvený systém
    def zpracuj_pozadavek(uzivatel_id: int):
        with tracer.start_as_current_span(
            "HTTP GET /api/studenti/{id}",
            attributes={
                "http.method":      "GET",
                "http.url":         f"/api/studenti/{uzivatel_id}",
                "http.user_agent":  "Python/3.12",
                "user.id":          uzivatel_id,
            },
        ) as root_span:
            try:
                # Autentizace
                with tracer.start_as_current_span("auth.verify_token") as auth_span:
                    time.sleep(0.002)
                    token_platny = random.random() > 0.1
                    auth_span.set_attribute("auth.valid", token_platny)
                    if not token_platny:
                        raise PermissionError("Neplatný token")

                # DB dotaz
                with tracer.start_as_current_span("db.query") as db_span:
                    db_span.set_attribute("db.system", "postgresql")
                    db_span.set_attribute("db.statement",
                        f"SELECT * FROM studenti WHERE id = {uzivatel_id}")
                    time.sleep(random.uniform(0.005, 0.02))
                    if uzivatel_id > 100:
                        raise LookupError(f"Student {uzivatel_id} nenalezen")

                # Cache write
                with tracer.start_as_current_span("cache.set"):
                    time.sleep(0.001)

                root_span.set_attribute("http.status_code", 200)
                root_span.set_status(Status(StatusCode.OK))
                return {"id": uzivatel_id, "jmeno": "Míša"}

            except PermissionError as e:
                root_span.set_attribute("http.status_code", 401)
                root_span.set_status(Status(StatusCode.ERROR, str(e)))
                root_span.record_exception(e)
                raise
            except LookupError as e:
                root_span.set_attribute("http.status_code", 404)
                root_span.set_status(Status(StatusCode.ERROR, str(e)))
                raise

    print("Trace pro úspěšný požadavek:")
    try:
        zpracuj_pozadavek(1)
    except Exception:
        pass

    print("\nTrace pro chybový požadavek (student 999):")
    try:
        zpracuj_pozadavek(999)
    except Exception:
        pass


# ══════════════════════════════════════════════════════════════
# ČÁST 2: Metrics – čísla v čase
# ══════════════════════════════════════════════════════════════

if OTEL_OK:
    print("\n--- Metrics ---\n")

    reader   = PeriodicExportingMetricReader(ConsoleMetricExporter(),
                                              export_interval_millis=5000)
    meter_provider = MeterProvider(metric_readers=[reader])
    metrics.set_meter_provider(meter_provider)
    meter = metrics.get_meter("python-kurz")

    # Counter – monotonně rostoucí
    pozadavky_celkem = meter.create_counter(
        "http.requests.total",
        unit="1",
        description="Celkový počet HTTP požadavků",
    )

    # Histogram – distribuce hodnot (latence)
    latence_histogram = meter.create_histogram(
        "http.request.duration",
        unit="ms",
        description="Latence HTTP požadavků",
    )

    # UpDownCounter – může klesat i stoupat
    aktivni_spojeni = meter.create_up_down_counter(
        "http.active_connections",
        description="Aktivní HTTP spojení",
    )

    # Gauge (observable) – aktuální hodnota
    def ziskej_pamet(_):
        import os, resource
        return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss

    meter.create_observable_gauge(
        "process.memory.rss",
        callbacks=[ziskej_pamet],
        unit="kB",
        description="RSS paměť procesu",
    )

    # Simuluj provoz
    for i in range(20):
        metoda  = random.choice(["GET", "POST", "PUT"])
        status  = random.choices([200, 404, 500], weights=[85, 10, 5])[0]
        latence = random.gauss(50, 20)

        pozadavky_celkem.add(1, {
            "http.method": metoda,
            "http.status": str(status),
        })
        latence_histogram.record(max(1, latence), {"http.method": metoda})

    aktivni_spojeni.add(5)
    aktivni_spojeni.add(-2)

    print("  Metriky zaznamenány (exportují se každých 5s do konzole)")


# ══════════════════════════════════════════════════════════════
# ČÁST 3: Vlastní OTel bez knihovny (princip)
# ══════════════════════════════════════════════════════════════

print("\n--- Vlastní trace systém (princip bez knihovny) ---\n")

import uuid

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

    def __repr__(self):
        return (f"Span({self.jmeno!r} trace={self.trace_id} "
                f"span={self.span_id} {self.trvani_ms:.1f}ms {self.status})")

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
        s.status = f"ERROR: {e}"
        raise
    finally:
        s.end()
        _aktivni_span.pop()
        _dokoncene_spany.append(s)

def tiskni_trace():
    for s in _dokoncene_spany:
        odsazeni = "  " if s.parent_id else ""
        ikona = "✓" if s.status == "OK" else "✗"
        print(f"  {odsazeni}{ikona} {s.jmeno} [{s.trvani_ms:.1f}ms]"
              f"  trace={s.trace_id}  span={s.span_id}")
        if s.atributy:
            print(f"    {s.atributy}")

# Demo
with span("objednavka.vytvor", user_id=42):
    with span("auth.verify"):
        time.sleep(0.002)

    with span("db.insert", table="objednavky"):
        time.sleep(0.008)

    with span("email.posli", to="uzivatel@example.com"):
        time.sleep(0.003)

    with span("cache.invalidate"):
        time.sleep(0.001)

tiskni_trace()

print("""
=== Kde OTel exportovat ===

  Jaeger    → distribuované traces, UI na localhost:16686
  Zipkin    → jednodušší traces
  Prometheus→ metrics scraping
  Grafana   → dashboardy pro vše
  Datadog   → komerční, plný stack
  Honeycomb → developer-friendly

  Lokálně (docker-compose):
    jaeger: jaegertracing/all-in-one
    otel collector: otel/opentelemetry-collector

  pip install:
    opentelemetry-exporter-jaeger
    opentelemetry-exporter-prometheus
    opentelemetry-instrumentation-fastapi  ← auto-instrumentace!
    opentelemetry-instrumentation-sqlalchemy
""")

# TVOJE ÚLOHA:
# 1. Přidej OTel auto-instrumentaci do FastAPI z lekce 56.
# 2. Napiš decorator @traced(jmeno) který obalí funkci do spanu.
# 3. Přidej Prometheus metrics endpoint /metrics do FastAPI.
