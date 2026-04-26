"""
LEKCE 48: Logging – správné zaznamenávání
==========================================
print() je pro lidi. logging je pro programy.

Proč logging místo print:
  - Úrovně (DEBUG/INFO/WARNING/ERROR/CRITICAL)
  - Vypnutí bez mazání kódu (level=WARNING skryje DEBUG+INFO)
  - Výstup do souboru, sítě, databáze současně
  - Automatický timestamp, jméno modulu, číslo řádku
  - Rotace souborů (aby log nevyrostl do nekonečna)
"""

import logging
import logging.handlers
import sys
from pathlib import Path

# ══════════════════════════════════════════════════════════════
# ČÁST 1: ZÁKLADY
# ══════════════════════════════════════════════════════════════

print("=== Základní konfigurace ===\n")

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%H:%M:%S",
    stream=sys.stdout,
)

log = logging.getLogger("kurz")

log.debug("Toto vidíš jen při ladění")
log.info("Server se spouští")
log.warning("Disk je z 90 % plný")
log.error("Nelze se připojit k databázi")
log.critical("Kritická chyba – vypínám")

# Hierarchie loggerů
log_db  = logging.getLogger("kurz.databaze")
log_api = logging.getLogger("kurz.api")

log_db.info("Dotaz SELECT * FROM studenti")
log_api.warning("Rate limit překročen pro IP 1.2.3.4")


# ══════════════════════════════════════════════════════════════
# ČÁST 2: HANDLERY – kam logy posílat
# ══════════════════════════════════════════════════════════════

print("\n=== Handlery ===\n")

# Vytvoř čistý logger (bez basicConfig)
logger = logging.getLogger("app")
logger.setLevel(logging.DEBUG)
logger.propagate = False   # nevysílej do root loggeru

# Handler 1: konzole (jen WARNING+)
konzole = logging.StreamHandler(sys.stdout)
konzole.setLevel(logging.WARNING)
konzole.setFormatter(logging.Formatter(
    "%(levelname)s: %(message)s"
))

# Handler 2: soubor (vše od DEBUG)
soubor_handler = logging.FileHandler("app.log", encoding="utf-8")
soubor_handler.setLevel(logging.DEBUG)
soubor_handler.setFormatter(logging.Formatter(
    "%(asctime)s | %(levelname)-8s | %(funcName)s:%(lineno)d | %(message)s"
))

# Handler 3: rotující soubor (max 1 MB, 3 zálohy)
rot_handler = logging.handlers.RotatingFileHandler(
    "app_rot.log",
    maxBytes=1_000_000,
    backupCount=3,
    encoding="utf-8",
)
rot_handler.setLevel(logging.INFO)

logger.addHandler(konzole)
logger.addHandler(soubor_handler)
logger.addHandler(rot_handler)

logger.debug("Toto jde jen do souboru")
logger.info("Server spuštěn na portu 8080")
logger.warning("Neočekávaný parametr v požadavku")
logger.error("Chyba zpracování požadavku")

print("  Logy zapsány do app.log a app_rot.log")


# ══════════════════════════════════════════════════════════════
# ČÁST 3: STRUKTUROVANÉ LOGOVÁNÍ
# ══════════════════════════════════════════════════════════════

print("\n=== Strukturované logování ===\n")

class JsonFormatter(logging.Formatter):
    """Formátuje logy jako JSON – snadno parsovatelné."""
    import json as _json

    def format(self, record: logging.LogRecord) -> str:
        data = {
            "cas":     self.formatTime(record, "%Y-%m-%dT%H:%M:%S"),
            "level":   record.levelname,
            "logger":  record.name,
            "zprava":  record.getMessage(),
            "modul":   record.module,
            "radek":   record.lineno,
        }
        if record.exc_info:
            data["vyjimka"] = self.formatException(record.exc_info)
        if hasattr(record, "extra"):
            data.update(record.extra)
        return self._json.dumps(data, ensure_ascii=False)

json_logger = logging.getLogger("json_demo")
json_logger.setLevel(logging.DEBUG)
json_logger.propagate = False

json_handler = logging.StreamHandler(sys.stdout)
json_handler.setFormatter(JsonFormatter())
json_logger.addHandler(json_handler)

json_logger.info("Požadavek zpracován")

# LoggerAdapter pro přidání kontextu ke každé zprávě
class RequestAdapter(logging.LoggerAdapter):
    def process(self, msg, kwargs):
        return f"[req={self.extra['request_id']}] {msg}", kwargs

req_log = RequestAdapter(json_logger, {"request_id": "abc-123"})
req_log.info("Uživatel přihlášen")
req_log.warning("Pokus o přístup k /admin")


# ══════════════════════════════════════════════════════════════
# ČÁST 4: LOGOVÁNÍ VÝJIMEK
# ══════════════════════════════════════════════════════════════

print("\n=== Logování výjimek ===\n")

app_log = logging.getLogger("vyjimky")
app_log.setLevel(logging.DEBUG)
app_log.propagate = False
app_log.addHandler(logging.StreamHandler(sys.stdout))

def bezpecne_deleni(a, b):
    try:
        return a / b
    except ZeroDivisionError:
        app_log.exception("Dělení nulou: %s / %s", a, b)
        # .exception() = .error() + traceback automaticky
        return None

def zpracuj_data(data: list):
    vysledky = []
    for i, x in enumerate(data):
        try:
            vysledky.append(10 / x)
        except (ZeroDivisionError, TypeError) as e:
            app_log.warning("Přeskakuji prvek [%d]=%r: %s", i, x, e)
    return vysledky

bezpecne_deleni(10, 0)
print(f"\n  Výsledky: {zpracuj_data([2, 0, 5, 'a', 1])}")


# ══════════════════════════════════════════════════════════════
# ČÁST 5: KONFIGURACE PŘES DICT
# ══════════════════════════════════════════════════════════════

print("\n=== Konfigurace přes dictConfig ===\n")

import logging.config

LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {
            "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
        },
        "kratky": {
            "format": "%(levelname)s: %(message)s"
        },
    },
    "handlers": {
        "konzole": {
            "class": "logging.StreamHandler",
            "level": "INFO",
            "formatter": "kratky",
            "stream": "ext://sys.stdout",
        },
        "soubor": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "DEBUG",
            "formatter": "standard",
            "filename": "konfig.log",
            "maxBytes": 10_000,
            "backupCount": 2,
            "encoding": "utf-8",
        },
    },
    "loggers": {
        "moje_app": {
            "level": "DEBUG",
            "handlers": ["konzole", "soubor"],
            "propagate": False,
        },
        "moje_app.databaze": {
            "level": "WARNING",   # přepíše rodičovský level
        },
    },
}

logging.config.dictConfig(LOGGING_CONFIG)
mlog = logging.getLogger("moje_app")
mlog.debug("Toto jde jen do souboru")
mlog.info("Aplikace spuštěna")
mlog.warning("Varování")

db_log = logging.getLogger("moje_app.databaze")
db_log.debug("Tento DEBUG se nezobrazí (level=WARNING)")
db_log.warning("DB varování")

print("  dictConfig funguje!")

# Úklid
for f in ["app.log", "app_rot.log", "konfig.log"]:
    Path(f).unlink(missing_ok=True)

print("""
=== Doporučený postup ===

  # V každém modulu:
  import logging
  log = logging.getLogger(__name__)   # jméno = název modulu

  # Na začátku programu (jednou):
  logging.basicConfig(level=logging.INFO)
  # nebo načti z konfiguračního souboru / env proměnné

  # V kódu:
  log.debug("Detailní ladění")
  log.info("Normální provoz")
  log.warning("Něco podezřelého")
  log.error("Chyba, ale pokračujeme")
  log.critical("Fatální, pravděpodobně ukončíme")
  log.exception("Chyba + traceback (jen v except bloku)")
""")

# TVOJE ÚLOHA:
# 1. Přidej dekorátor @loguj_volani který loguje vstupní argumenty a výstup funkce.
# 2. Nastav různé log levely pro různá prostředí (DEV=DEBUG, PROD=WARNING) přes env.
# 3. Napiš handler který posílá ERROR logy na email (SMTPHandler).
