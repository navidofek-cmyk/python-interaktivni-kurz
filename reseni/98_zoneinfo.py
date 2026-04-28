"""Řešení – Lekce 98: zoneinfo – správné časové zóny

Toto je vzorové řešení úloh z lekce 98.
"""

from zoneinfo import ZoneInfo
from datetime import datetime, timedelta

# ── Úloha 1 ────────────────────────────────────────────────
# cas_do_udalosti(dt_udalost, zona) – lidsky čitelný čas do/od události.

def cas_do_udalosti(dt_udalost: datetime, zona: str = "UTC") -> str:
    """
    Vrátí lidsky čitelný čas do/od události.
    dt_udalost musí být vědomý datetime nebo bude přiřazena zona.
    """
    if dt_udalost.tzinfo is None:
        dt_udalost = dt_udalost.replace(tzinfo=ZoneInfo(zona))

    now_utc = datetime.now(tz=ZoneInfo("UTC"))
    udalost_utc = dt_udalost.astimezone(ZoneInfo("UTC"))
    delta = udalost_utc - now_utc
    sekundy = int(delta.total_seconds())

    if abs(sekundy) < 60:
        return "probíhá nyní"

    minuly = sekundy < 0
    abs_sek = abs(sekundy)
    minuty = abs_sek // 60
    hodiny = minuty // 60
    dny = hodiny // 24

    if dny >= 2:
        text = f"za {dny} dny" if not minuly else f"před {dny} dny"
    elif dny == 1:
        text = "za 1 den" if not minuly else "před 1 dnem"
    elif hodiny >= 1:
        zbyle_min = minuty % 60
        if zbyle_min > 0:
            t = f"za {hodiny} hod {zbyle_min} min" if not minuly else f"skončilo před {hodiny} hod {zbyle_min} min"
        else:
            t = f"za {hodiny} hodin" if not minuly else f"skončilo před {hodiny} hodinami"
        return t
    else:
        t = f"za {minuty} minut" if not minuly else f"skončilo před {minuty} minutami"
        return t

    return text


now = datetime.now(tz=ZoneInfo("UTC"))
print("Úloha 1 – cas_do_udalosti():")
testy = [
    ("za 30 sekund",     now + timedelta(seconds=30)),
    ("za 25 minut",      now + timedelta(minutes=25)),
    ("za 3 hod 10 min",  now + timedelta(hours=3, minutes=10)),
    ("za 2 dny",         now + timedelta(days=2)),
    ("před 10 min",      now - timedelta(minutes=10)),
    ("před 2 hodinami",  now - timedelta(hours=2)),
]
for popis, dt in testy:
    print(f"  {popis:<20} → {cas_do_udalosti(dt)}")
print()


# ── Úloha 2 ────────────────────────────────────────────────
# najdi_nejlepsi_cas_schuzky(ucastnici, od, do) – UTC časy,
# kdy mají všichni pracovní dobu současně (dnes).

def najdi_nejlepsi_cas_schuzky(
    ucastnici: dict[str, str],
    od: int = 9,
    do: int = 17,
    datum: datetime | None = None,
) -> list[datetime]:
    """
    Vrátí seznam UTC hodin (po celých hodinách), kdy mají všichni
    pracovní dobu od 'od' do 'do' ve svých zónách současně.
    """
    if datum is None:
        datum = datetime.now(tz=ZoneInfo("UTC")).replace(
            hour=0, minute=0, second=0, microsecond=0
        )

    vysledky = []
    # Projdeme každou hodinu v daném dni (UTC)
    for hodina in range(24):
        utc_dt = datum.replace(hour=hodina)
        vsichni_pracuji = True
        for jmeno, zona_str in ucastnici.items():
            lokalni = utc_dt.astimezone(ZoneInfo(zona_str))
            if not (od <= lokalni.hour < do):
                vsichni_pracuji = False
                break
        if vsichni_pracuji:
            vysledky.append(utc_dt)
    return vysledky


ucastnici = {
    "Alice (Praha)":    "Europe/Prague",
    "Bob (Londýn)":     "Europe/London",
    "Carol (New York)": "America/New_York",
}

print("Úloha 2 – najdi_nejlepsi_cas_schuzky():")
# Použijeme pevné datum kvůli DST
testovaci_datum = datetime(2024, 6, 15, 0, 0, tzinfo=ZoneInfo("UTC"))
casy = najdi_nejlepsi_cas_schuzky(ucastnici, od=9, do=17, datum=testovaci_datum)
if casy:
    print(f"  Společná pracovní doba (9-17 v místních zónách) – {len(casy)} hodin:")
    for utc_cas in casy:
        radek = f"  UTC {utc_cas.strftime('%H:%M')} = "
        casti = []
        for jmeno, zona_str in ucastnici.items():
            lok = utc_cas.astimezone(ZoneInfo(zona_str))
            casti.append(f"{jmeno.split('(')[0].strip()} {lok.strftime('%H:%M %Z')}")
        print(radek + " | ".join(casti))
else:
    print("  Žádný společný čas nenalezen.")
print()


# ── Úloha 3 ────────────────────────────────────────────────
# parse_datetime_s_zonou(text) – zparsuje různé formáty, vrátí UTC.

def parse_datetime_s_zonou(text: str) -> datetime:
    """
    Zparsuje řetězce:
      "2024-06-15 14:30 Europe/Prague"
      "2024-06-15T14:30:00+02:00"
      "15.6.2024 14:30 CET"
    Vrátí vědomý datetime v UTC.
    """
    text = text.strip()

    # Formát ISO s offset: "2024-06-15T14:30:00+02:00"
    try:
        dt = datetime.fromisoformat(text)
        return dt.astimezone(ZoneInfo("UTC"))
    except ValueError:
        pass

    # Formát "YYYY-MM-DD HH:MM IANA_ZONA"
    if " " in text:
        casti = text.rsplit(" ", 1)
        if len(casti) == 2:
            dt_str, zona_str = casti
            # Mapování zkratek na IANA zóny
            zkratky = {
                "CET":  "Europe/Paris",
                "CEST": "Europe/Paris",
                "UTC":  "UTC",
                "GMT":  "UTC",
                "EST":  "America/New_York",
                "PST":  "America/Los_Angeles",
            }
            zona_str = zkratky.get(zona_str, zona_str)
            try:
                zona = ZoneInfo(zona_str)
                # Zkusíme různé formáty datumu
                for fmt in ("%Y-%m-%d %H:%M", "%d.%m.%Y %H:%M", "%Y-%m-%d %H:%M:%S"):
                    try:
                        dt = datetime.strptime(dt_str, fmt).replace(tzinfo=zona)
                        return dt.astimezone(ZoneInfo("UTC"))
                    except ValueError:
                        continue
            except Exception:
                pass

    raise ValueError(f"Nepodporovaný formát: {text!r}")


print("Úloha 3 – parse_datetime_s_zonou():")
vstupy = [
    "2024-06-15 14:30 Europe/Prague",
    "2024-06-15T14:30:00+02:00",
    "15.6.2024 14:30 CET",
    "2024-06-15 09:00 America/New_York",
]
for s in vstupy:
    try:
        dt_utc = parse_datetime_s_zonou(s)
        print(f"  {s!r}")
        print(f"  → UTC: {dt_utc.strftime('%Y-%m-%d %H:%M:%S %Z')}")
    except ValueError as e:
        print(f"  CHYBA: {e}")
    print()


# ── Úloha 4 ────────────────────────────────────────────────
# WorldClock: add_city, tick, time_diff.

class WorldClock:
    """Světové hodiny – sleduje čas ve více městech."""

    def __init__(self):
        self._mesta: dict[str, ZoneInfo] = {}

    def add_city(self, name: str, zona: str) -> None:
        self._mesta[name] = ZoneInfo(zona)

    def tick(self) -> None:
        """Vypíše aktuální čas ve všech městech."""
        now_utc = datetime.now(tz=ZoneInfo("UTC"))
        print("  Aktuální čas:")
        for mesto, zona in self._mesta.items():
            lok = now_utc.astimezone(zona)
            print(f"    {mesto:<20} {lok.strftime('%H:%M:%S %Z (UTC%z)')}")

    def time_diff(self, city1: str, city2: str) -> float:
        """Vrátí časový rozdíl v hodinách (city1 − city2)."""
        now_utc = datetime.now(tz=ZoneInfo("UTC"))
        offset1 = now_utc.astimezone(self._mesta[city1]).utcoffset()
        offset2 = now_utc.astimezone(self._mesta[city2]).utcoffset()
        if offset1 is None or offset2 is None:
            return 0.0
        return (offset1 - offset2).total_seconds() / 3600


clock = WorldClock()
clock.add_city("Praha",       "Europe/Prague")
clock.add_city("Londýn",      "Europe/London")
clock.add_city("New York",    "America/New_York")
clock.add_city("Tokio",       "Asia/Tokyo")
clock.add_city("Los Angeles", "America/Los_Angeles")
clock.add_city("Sydney",      "Australia/Sydney")

print("Úloha 4 – WorldClock:")
clock.tick()
print()
print("  Rozdíly oproti Praze:")
for mesto in ["Londýn", "New York", "Tokio", "Los Angeles", "Sydney"]:
    diff = clock.time_diff("Praha", mesto)
    print(f"    Praha vs {mesto:<15} {diff:+.0f} hod")
