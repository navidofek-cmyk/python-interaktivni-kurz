"""
LEKCE 98: zoneinfo – správné časové zóny (Python 3.9+)
========================================================
Naučíš se pracovat s časovými zónami správně –
bez záludností naivních datetime objektů.

PROBLÉM: datetime bez zóny = "naivní" objekt
  → neví, kde na světě je, nelze porovnat s jiným
  → daylight saving time (DST) musíš řešit ručně
  → konverze mezi zónami = katastrofa

ŘEŠENÍ: zoneinfo (Python 3.9+)
  ZoneInfo("Europe/Prague") = plné IANA timezone databáze
  → automatický DST přechod
  → správná aritmetika přes zóny
  → žádné pytz hádanky

Instalace (databáze zón):
  Linux/Mac: vestavěná v OS
  Windows:   pip install tzdata
"""

from zoneinfo import ZoneInfo, available_timezones
from datetime import datetime, timedelta, timezone
import time

print("=== LEKCE 98: zoneinfo – časové zóny ===\n")

# ══════════════════════════════════════════════════════════════
# ČÁST 1: Naivní vs vědomý datetime
# ══════════════════════════════════════════════════════════════

print("── Část 1: Naivní vs vědomý (aware) datetime ──\n")

# Naivní – žádná informace o zóně
naive_dt = datetime(2024, 6, 15, 12, 0, 0)
print(f"  Naivní datetime:  {naive_dt}")
print(f"  tzinfo:           {naive_dt.tzinfo}  ← None = problém!")

# Vědomý – se zónou
prague_tz  = ZoneInfo("Europe/Prague")
aware_dt   = datetime(2024, 6, 15, 12, 0, 0, tzinfo=prague_tz)
print(f"  Vědomý datetime:  {aware_dt}")
print(f"  tzinfo:           {aware_dt.tzinfo}")
print(f"  UTC offset:       {aware_dt.utcoffset()}  (CEST = UTC+2)")
print(f"  Zkratka zóny:     {aware_dt.strftime('%Z')}")
print()

# Pokus o porovnání naivní vs vědomý → TypeError
print("  Porovnání naivní vs vědomý:")
try:
    _ = naive_dt < aware_dt
    print("  Porovnání OK (neočekávané!)")
except TypeError as e:
    print(f"  TypeError: {e}")
print()

# ══════════════════════════════════════════════════════════════
# ČÁST 2: Převod mezi časovými zónami
# ══════════════════════════════════════════════════════════════

print("── Část 2: Převod mezi zónami ──\n")

ZONY = {
    "Praha":       ZoneInfo("Europe/Prague"),
    "Londýn":      ZoneInfo("Europe/London"),
    "New York":    ZoneInfo("America/New_York"),
    "Los Angeles": ZoneInfo("America/Los_Angeles"),
    "Tokio":       ZoneInfo("Asia/Tokyo"),
    "Sydney":      ZoneInfo("Australia/Sydney"),
    "UTC":         ZoneInfo("UTC"),
}

# Schůzka v Praze – kdy to je jinde?
schuzka_praha = datetime(2024, 3, 20, 14, 30, tzinfo=ZoneInfo("Europe/Prague"))
print(f"  Schůzka v Praze: {schuzka_praha.strftime('%d.%m.%Y %H:%M %Z')}")
print()
print("  Totéž v jiných zónách:")
for mesto, zona in ZONY.items():
    lokalni = schuzka_praha.astimezone(zona)
    print(f"  {mesto:<15} {lokalni.strftime('%H:%M %Z (UTC%z)')}")
print()

# ══════════════════════════════════════════════════════════════
# ČÁST 3: DST – letní/zimní čas automaticky
# ══════════════════════════════════════════════════════════════

print("── Část 3: DST – letní/zimní čas ──\n")

prague = ZoneInfo("Europe/Prague")

# Zimní čas (CET = UTC+1)
zima = datetime(2024, 1, 15, 12, 0, tzinfo=prague)
# Letní čas (CEST = UTC+2)
leto = datetime(2024, 7, 15, 12, 0, tzinfo=prague)

print(f"  Zima (leden):  {zima.strftime('%H:%M %Z')} = UTC offset {zima.utcoffset()}")
print(f"  Léto (červen): {leto.strftime('%H:%M %Z')} = UTC offset {leto.utcoffset()}")
print(f"  DST v létě:    {leto.dst()}")
print(f"  DST v zimě:    {zima.dst()}")
print()

# Přechod na letní čas 2024: 31.3. ve 2:00 → 3:00
# fold = 0 → interpret 2:30 jako CEST (po přechodu)
# fold = 1 → interpret 2:30 jako CET (před přechodem)
prechod_pred = datetime(2024, 3, 31, 1, 59, tzinfo=prague)
prechod_po   = datetime(2024, 3, 31, 3,  0, tzinfo=prague)

print(f"  Těsně před přechodem: {prechod_pred.strftime('%H:%M %Z')} (UTC{prechod_pred.utcoffset()})")
print(f"  Těsně po přechodu:    {prechod_po.strftime('%H:%M %Z')} (UTC{prechod_po.utcoffset()})")
print(f"  Rozdíl (ve skutečnosti 1 hod): {prechod_po - prechod_pred}")
print()

# ══════════════════════════════════════════════════════════════
# ČÁST 4: Aktuální čas ve více zónách
# ══════════════════════════════════════════════════════════════

print("── Část 4: Aktuální čas ve světě ──\n")

# datetime.now() s zónou = správně
ted_utc   = datetime.now(tz=ZoneInfo("UTC"))
print(f"  Aktuální UTC: {ted_utc.strftime('%Y-%m-%d %H:%M:%S %Z')}")
print()
print("  Světové hodiny:")
for mesto, zona in ZONY.items():
    lokalni = ted_utc.astimezone(zona)
    print(f"  {mesto:<15} {lokalni.strftime('%H:%M:%S %Z')}")
print()

# ══════════════════════════════════════════════════════════════
# ČÁST 5: Aritmetika přes DST přechod
# ══════════════════════════════════════════════════════════════

print("── Část 5: Aritmetika přes DST přechod ──\n")

# Přidání 24 hodin přes přechod na letní čas
pred_prechodem = datetime(2024, 3, 30, 12, 0, tzinfo=prague)
za_24_hodin    = pred_prechodem + timedelta(hours=24)
za_1_den       = pred_prechodem + timedelta(days=1)

print(f"  Začátek:       {pred_prechodem.strftime('%d.%m %H:%M %Z')}")
print(f"  + 24 hodin:    {za_24_hodin.strftime('%d.%m %H:%M %Z')}")
print(f"  + 1 den:       {za_1_den.strftime('%d.%m %H:%M %Z')}")
print()
print("  Poznámka: timedelta(hours=24) ≠ timedelta(days=1) přes DST!")
print(f"  hours=24: {za_24_hodin.strftime('%H:%M %Z')}  days=1: {za_1_den.strftime('%H:%M %Z')}")
print()

# ══════════════════════════════════════════════════════════════
# ČÁST 6: Porovnání s pytz (starší přístup)
# ══════════════════════════════════════════════════════════════

print("── Část 6: zoneinfo vs pytz ──\n")

print("  PYTZ (starý přístup) – záludnosti:")
print("  ┌─ pytz.timezone('Europe/Prague').localize(dt)  # ne dt.replace()")
print("  │  dt.replace(tzinfo=pytz_zone)  = ŠPATNĚ (nerespektuje DST offset)")
print("  └─ convert_tz = pytz_zone.normalize(dt.astimezone(pytz_zone))")
print()
print("  ZONEINFO (nový přístup, Python 3.9+) – čistší API:")
print("  ┌─ datetime(2024, 6, 15, 12, 0, tzinfo=ZoneInfo('Europe/Prague'))")
print("  │  dt.replace(tzinfo=ZoneInfo(...))  = OK (zoneinfo to umí)")
print("  └─ dt.astimezone(ZoneInfo('America/New_York'))  = přímý převod")
print()

# Dostupné zóny
vsechny_zony = available_timezones()
print(f"  Počet dostupných IANA zón: {len(vsechny_zony)}")
evropske = sorted(z for z in vsechny_zony if z.startswith("Europe/"))
print(f"  Evropské zóny ({len(evropske)}):")
for z in evropske[:10]:
    print(f"    {z}")
if len(evropske) > 10:
    print(f"    ... a {len(evropske) - 10} dalších")
print()

# ══════════════════════════════════════════════════════════════
# ČÁST 7: Praktický příklad – kalendářní aplikace
# ══════════════════════════════════════════════════════════════

print("── Část 7: Kalendář schůzek přes zóny ──\n")

class KalendarSchuzek:
    """Jednoduchý kalendář ukládající schůzky v UTC."""

    def __init__(self):
        self._schuzky: list[dict] = []

    def pridej(self, nazev: str, dt_local: datetime):
        """Přidá schůzku. dt_local musí být vědomý datetime."""
        if dt_local.tzinfo is None:
            raise ValueError("Schůzka musí mít časovou zónu!")
        dt_utc = dt_local.astimezone(ZoneInfo("UTC"))
        self._schuzky.append({"nazev": nazev, "utc": dt_utc})
        self._schuzky.sort(key=lambda s: s["utc"])

    def vypis(self, zona: ZoneInfo):
        """Vypíše všechny schůzky v dané zóně."""
        print(f"  Schůzky v zóně {zona.key}:")
        for s in self._schuzky:
            lok = s["utc"].astimezone(zona)
            print(f"    {lok.strftime('%d.%m %H:%M %Z'):<22} – {s['nazev']}")

    def dalsi(self) -> dict | None:
        now_utc = datetime.now(tz=ZoneInfo("UTC"))
        budouci = [s for s in self._schuzky if s["utc"] > now_utc]
        return budouci[0] if budouci else None

kalendar = KalendarSchuzek()
kalendar.pridej("Standup",        datetime(2025, 6, 2,  9,  0, tzinfo=ZoneInfo("Europe/Prague")))
kalendar.pridej("1:1 s šéfem",   datetime(2025, 6, 2, 14, 30, tzinfo=ZoneInfo("Europe/Prague")))
kalendar.pridej("Demo s klientem (NY)", datetime(2025, 6, 2, 16, 0, tzinfo=ZoneInfo("America/New_York")))
kalendar.pridej("Code review",   datetime(2025, 6, 3, 10, 0, tzinfo=ZoneInfo("Europe/London")))

kalendar.vypis(ZoneInfo("Europe/Prague"))
print()
kalendar.vypis(ZoneInfo("UTC"))
print()
kalendar.vypis(ZoneInfo("America/New_York"))
print()

# ══════════════════════════════════════════════════════════════
# TVOJE ÚLOHA:
# ══════════════════════════════════════════════════════════════
print("=" * 55)
print("TVOJE ÚLOHA:")
print("=" * 55)
print("""
1. Napiš funkci `cas_do_udalosti(dt_udalost: datetime,
   zona: str) -> str`, která vrátí lidsky čitelný čas
   do události: "za 3 hodiny 25 minut", "za 2 dny",
   "probíhá nyní", "skončilo před 10 minutami".
   Používej datetime.now(ZoneInfo("UTC")) jako referenci.

2. Napiš funkci `najdi_nejlepsi_cas_schuzky(
   ucastnici: dict[str, str], od: int, do: int) -> list`,
   kde klíč = jméno, hodnota = IANA zóna a od/do jsou
   pracovní hodiny (9, 17). Vrátí seznam UTC datetime,
   kdy mají všichni pracovní dobu současně (pro daný den).

3. Implementuj funkci `parse_datetime_s_zonou(text: str)
   -> datetime`, která zparsuje řetězce jako:
   "2024-06-15 14:30 Europe/Prague"
   "2024-06-15T14:30:00+02:00"
   "15.6.2024 14:30 CET"
   Vrátí vždy vědomý datetime v UTC.

4. Vytvoř WorldClock třídu s metodami: add_city(name,
   zona), tick() – vypíše aktuální čas ve všech městech,
   time_diff(city1, city2) – vrátí časový rozdíl v hodinách.
   Přidej aspoň 5 měst a vypiš rozdíly oproti Praze.
""")
