"""
LEKCE 46: Regulární výrazy
============================
Regex = minijazyk pro popis vzorů v textu.
Jeden řádek regexu nahradí desítky řádků if/split/strip kódu.

Základní znaky:
  .       libovolný znak (kromě \n)
  ^       začátek řetězce
  $       konec řetězce
  *       0 nebo více opakování
  +       1 nebo více opakování
  ?       0 nebo 1 opakování
  {n,m}   n až m opakování
  [abc]   jeden ze znaků a, b, c
  [^abc]  cokoli KROMĚ a, b, c
  (...)   skupina (capture group)
  |       nebo
  \\d      číslice [0-9]
  \\w      slovo [a-zA-Z0-9_]
  \\s      mezera/tab/newline
  \\b      hranice slova
"""

import re

# ══════════════════════════════════════════════════════════════
# ČÁST 1: ZÁKLADNÍ FUNKCE
# ══════════════════════════════════════════════════════════════

print("=== Základní funkce ===\n")

text = "Python 3.12 byl vydán v říjnu 2023. Python 2.7 skončil 2020."

# search – najde první výskyt kdekoliv v textu
m = re.search(r"\d+\.\d+", text)
print(f"search (první verze):  {m.group()}")

# findall – vrátí všechny výskyty jako seznam
verze = re.findall(r"\d+\.\d+", text)
print(f"findall (verze):       {verze}")

leta = re.findall(r"\b20\d{2}\b", text)
print(f"findall (roky):        {leta}")

# match – pouze od začátku řetězce
print(f"match 'Python':        {bool(re.match(r'Python', text))}")
print(f"match 'vydán':         {bool(re.match(r'vydán', text))}")

# fullmatch – celý řetězec musí odpovídat
print(f"fullmatch IP:          {bool(re.fullmatch(r'\\d+\\.\\d+\\.\\d+\\.\\d+', '192.168.1.1'))}")

# sub – nahrazení
anonymizovano = re.sub(r"\b20\d{2}\b", "XXXX", text)
print(f"sub (roky):            {anonymizovano}")

# split – rozdělení podle vzoru
vety = re.split(r"[.!?]+\s*", "Ahoj! Jak se máš? Dobře. Díky.")
print(f"split:                 {vety}")


# ══════════════════════════════════════════════════════════════
# ČÁST 2: SKUPINY (CAPTURE GROUPS)
# ══════════════════════════════════════════════════════════════

print("\n=== Skupiny ===\n")

# Pojmenované skupiny (?P<jmeno>...)
datum_vzor = re.compile(
    r"(?P<den>\d{1,2})\.(?P<mesic>\d{1,2})\.(?P<rok>\d{4})"
)

data = ["15.3.2024", "1.12.2023", "31.1.2025"]
for d in data:
    m = datum_vzor.fullmatch(d)
    if m:
        print(f"  {d} → den={m['den']}, měsíc={m['mesic']}, rok={m['rok']}")

# Backreference – odkaz na skupinu v samotném vzoru
palindrom_vzor = re.compile(r"(\w)\w\1")   # \1 = stejný znak jako skupina 1
slova = ["aba", "abc", "ana", "python", "oto", "eve"]
print(f"\nSlova kde 1. a 3. písmeno jsou stejné:")
print(f"  {[s for s in slova if palindrom_vzor.fullmatch(s)]}")

# Nepachytující skupiny (?:...)
email_vzor = re.compile(r"[\w.+-]+@(?:[\w-]+\.)+[a-z]{2,}")
emaily = ["user@example.com", "spatne@", "ok@sub.domain.cz", "no-at-sign"]
print(f"\nValidní emaily:")
for e in emaily:
    ok = bool(email_vzor.fullmatch(e))
    print(f"  {'✓' if ok else '✗'} {e}")


# ══════════════════════════════════════════════════════════════
# ČÁST 3: FLAGY A KOMPILACE
# ══════════════════════════════════════════════════════════════

print("\n=== Flagy ===\n")

text2 = """Jméno: Jan Novák
Email: jan@example.com
Telefon: +420 777 123 456
Adresa: Hlavní 1, Praha"""

# IGNORECASE – ignoruj velikost
print("Hledám 'jméno' bez ohledu na velikost:")
m = re.search(r"jméno:\s*(.+)", text2, re.IGNORECASE)
print(f"  {m.group(1) if m else 'nenalezeno'}")

# MULTILINE – ^ a $ platí pro každý řádek
klice = re.findall(r"^\w+(?=:)", text2, re.MULTILINE)
print(f"\nKlíče (začátek každého řádku): {klice}")

# DOTALL – . zachytí i newline
blok = re.search(r"Jan.+Praha", text2, re.DOTALL)
print(f"\nDOTALL (přes více řádků): {blok.group()!r}" if blok else "")

# VERBOSE – čitelný regex s komentáři
telefon_vzor = re.compile(r"""
    (?:\+420\s*)?   # Volitelná česká předvolba
    \d{3}           # 3 číslice
    [\s-]?          # volitelný oddělovač
    \d{3}           # 3 číslice
    [\s-]?          # volitelný oddělovač
    \d{3}           # 3 číslice
""", re.VERBOSE)

telefony = ["+420 777 123 456", "777123456", "777-123-456", "12345"]
print(f"\nValidní telefony:")
for t in telefony:
    ok = bool(telefon_vzor.fullmatch(t))
    print(f"  {'✓' if ok else '✗'} {t}")


# ══════════════════════════════════════════════════════════════
# ČÁST 4: LOOKAHEAD / LOOKBEHIND
# ══════════════════════════════════════════════════════════════

print("\n=== Lookahead / Lookbehind ===\n")

ceny = "Cena: 299 Kč, sleva: 50 Kč, celkem: 249 Kč"

# Pozitivní lookahead (?=...) – čísla PŘED " Kč"
cisla_kc = re.findall(r"\d+(?=\s*Kč)", ceny)
print(f"Čísla před 'Kč': {cisla_kc}")

# Pozitivní lookbehind (?<=...) – čísla PO "sleva: "
po_sleva = re.findall(r"(?<=sleva:\s)\d+", ceny)
print(f"Čísla po 'sleva:': {po_sleva}")

# Negativní lookahead (?!...) – slova která NEJSOU followed by číslem
text3 = "python3 java js python ruby2"
slova_bez_cisla = re.findall(r"\b[a-z]+(?!\d)\b", text3)
print(f"Slova bez číslice za sebou: {slova_bez_cisla}")


# ══════════════════════════════════════════════════════════════
# ČÁST 5: PRAKTICKÉ UKÁZKY
# ══════════════════════════════════════════════════════════════

print("\n=== Praktické ukázky ===\n")

# Parser logů
LOG = """
2024-01-15 08:23:11 INFO  Server started on port 8080
2024-01-15 08:23:45 DEBUG Request: GET /api/users
2024-01-15 08:23:45 INFO  Response: 200 OK (45ms)
2024-01-15 08:24:01 ERROR Database connection failed: timeout
2024-01-15 08:24:02 WARN  Retrying connection (attempt 1/3)
"""

log_vzor = re.compile(
    r"(?P<datum>\d{4}-\d{2}-\d{2})\s+"
    r"(?P<cas>\d{2}:\d{2}:\d{2})\s+"
    r"(?P<level>INFO|DEBUG|ERROR|WARN)\s+"
    r"(?P<zprava>.+)"
)

print("Parsované logy:")
for radek in LOG.strip().splitlines():
    m = log_vzor.match(radek)
    if m:
        ikona = {"INFO": "ℹ", "DEBUG": "🔍", "ERROR": "❌", "WARN": "⚠"}
        print(f"  {ikona.get(m['level'],'?')} [{m['cas']}] {m['zprava']}")

# Extrakce dat z HTML (hrubé – pro produkci použij BeautifulSoup)
html = '<a href="/page1">Stránka 1</a> <a href="https://example.com">External</a>'
linky = re.findall(r'href="([^"]+)"', html)
print(f"\nLinky z HTML: {linky}")

# Validace hesla
def validuj_heslo(heslo: str) -> list[str]:
    chyby = []
    if len(heslo) < 8:
        chyby.append("Příliš krátké (min. 8 znaků)")
    if not re.search(r"[A-Z]", heslo):
        chyby.append("Chybí velké písmeno")
    if not re.search(r"[a-z]", heslo):
        chyby.append("Chybí malé písmeno")
    if not re.search(r"\d", heslo):
        chyby.append("Chybí číslice")
    if not re.search(r"[!@#$%^&*]", heslo):
        chyby.append("Chybí speciální znak (!@#$%^&*)")
    return chyby

print("\nValidace hesel:")
for heslo in ["abc", "heslo123", "Heslo123!", "S1lne@Heslo"]:
    chyby = validuj_heslo(heslo)
    stav  = "✓" if not chyby else f"✗ ({', '.join(chyby)})"
    print(f"  {heslo!r:20} {stav}")

# TVOJE ÚLOHA:
# 1. Napiš regex pro české PSČ (5 číslic, ev. s mezerou: "110 00").
# 2. Napiš funkci maskuj_kartu(cislo) → "4111 **** **** 1111".
# 3. Parsuj CSV řádek správně (zachová hodnoty v uvozovkách s čárkou uvnitř).
