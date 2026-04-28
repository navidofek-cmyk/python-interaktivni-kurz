"""Reseni – Lekce 48: Logging"""

import logging
import logging.handlers
import os
import sys
import smtplib
from pathlib import Path
from email.mime.text import MIMEText
from functools import wraps
from typing import Callable, Any


# 1. Dekorator @loguj_volani ktery loguje vstupni argumenty a vystup

print("=== Ukol 1: @loguj_volani dekorator ===\n")

log = logging.getLogger("reseni_48")
log.setLevel(logging.DEBUG)
log.propagate = False
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(logging.Formatter("%(levelname)-8s | %(message)s"))
log.addHandler(handler)


def loguj_volani(logger: logging.Logger | None = None) -> Callable:
    """Dekorator ktery loguje vstupni argumenty a navratovou hodnotu."""
    def dekorator(fn: Callable) -> Callable:
        _log = logger or logging.getLogger(fn.__module__)

        @wraps(fn)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            args_str = ", ".join(
                [repr(a) for a in args] +
                [f"{k}={v!r}" for k, v in kwargs.items()]
            )
            _log.debug(f"VOLAM {fn.__name__}({args_str})")
            try:
                vysledek = fn(*args, **kwargs)
                _log.debug(f"VRACIM {fn.__name__} -> {vysledek!r}")
                return vysledek
            except Exception as e:
                _log.error(f"VYJIMKA v {fn.__name__}: {type(e).__name__}: {e}")
                raise
        return wrapper
    return dekorator


@loguj_volani(logger=log)
def secti(a: int, b: int) -> int:
    return a + b


@loguj_volani(logger=log)
def vydel(a: float, b: float) -> float:
    if b == 0:
        raise ZeroDivisionError("Nelze delit nulou")
    return a / b


@loguj_volani(logger=log)
def pozdrav(jmeno: str, pozdrav_text: str = "Ahoj") -> str:
    return f"{pozdrav_text}, {jmeno}!"


secti(3, 4)
pozdrav("Misa", pozdrav_text="Hello")
try:
    vydel(10, 0)
except ZeroDivisionError:
    pass


# 2. Ruzne log levely pro ruzna prostredi (DEV/PROD)

print("\n=== Ukol 2: Log levely dle prostredi ===\n")


def nastavit_logging(prostredi: str | None = None) -> logging.Logger:
    """Nastavi log level dle ENV promenne PYTHON_ENV."""
    env = prostredi or os.environ.get("PYTHON_ENV", "dev").lower()

    level_mapa = {
        "dev":        logging.DEBUG,
        "development": logging.DEBUG,
        "test":       logging.INFO,
        "staging":    logging.WARNING,
        "prod":       logging.WARNING,
        "production": logging.WARNING,
    }
    level = level_mapa.get(env, logging.INFO)

    aplikacni_log = logging.getLogger(f"app.{env}")
    aplikacni_log.setLevel(level)
    aplikacni_log.propagate = False
    h = logging.StreamHandler(sys.stdout)
    h.setFormatter(logging.Formatter(f"[{env.upper()}] %(levelname)-8s %(message)s"))
    aplikacni_log.handlers.clear()
    aplikacni_log.addHandler(h)
    return aplikacni_log


for env in ["dev", "prod"]:
    env_log = nastavit_logging(env)
    print(f"Prostredi: {env.upper()}")
    env_log.debug("DEBUG zprava (dev only)")
    env_log.info("INFO zprava")
    env_log.warning("WARNING zprava")
    print()


# 3. SMTPHandler pro ERROR logy (pripraven, ale nevysilame)

print("=== Ukol 3: SMTPHandler pro emaily ===\n")


def vytvor_smtp_handler(
    mailhost: str = "smtp.gmail.com",
    port: int = 587,
    fromaddr: str = "app@example.com",
    toaddrs: list[str] | None = None,
    subject: str = "[ERROR] Aplikace hlasi chybu",
    credentials: tuple[str, str] | None = None,
) -> logging.handlers.SMTPHandler:
    """Vytvori SMTPHandler ktery posila ERROR+ logy emailem.

    Pouziti v produkci:
        handler = vytvor_smtp_handler(
            mailhost="smtp.gmail.com",
            fromaddr="app@firma.cz",
            toaddrs=["ops@firma.cz"],
            credentials=("uzivatel", "heslo"),
        )
        logger.addHandler(handler)
    """
    smtp_handler = logging.handlers.SMTPHandler(
        mailhost=(mailhost, port),
        fromaddr=fromaddr,
        toaddrs=toaddrs or ["admin@example.com"],
        subject=subject,
        credentials=credentials,
        secure=(),   # TLS
    )
    smtp_handler.setLevel(logging.ERROR)
    smtp_handler.setFormatter(logging.Formatter(
        "%(asctime)s\n%(levelname)s: %(message)s\n\n%(pathname)s:%(lineno)d"
    ))
    return smtp_handler


# Ukaz konfiguraci bez skutecneho odeslani
smtp_h = vytvor_smtp_handler()
print(f"SMTPHandler nakonfigurovan:")
print(f"  mailhost:  smtp.gmail.com:587")
print(f"  fromaddr:  app@example.com")
print(f"  toaddrs:   ['admin@example.com']")
print(f"  level:     ERROR+")
print(f"  (Pro skutecne odesilani pridat credentials a pridat handler k loggeru)")

# Cleanup
for f in ["app.log", "app_rot.log", "konfig.log"]:
    Path(f).unlink(missing_ok=True)
