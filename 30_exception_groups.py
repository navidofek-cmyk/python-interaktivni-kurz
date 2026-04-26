"""
LEKCE 30: Exception Groups a except* (Python 3.11+)
=====================================================
Z dokumentace: PEP 654 – Exception Groups and except*

Normálně: jedna výjimka najednou.
ExceptionGroup: svazek více výjimek najednou.

Kdy to potřebuješ?
  - Async kód (asyncio.gather může selhat na více místech)
  - Paralelní zpracování
  - Validace formuláře (chceš VŠECHNY chyby, ne jen první)

Python 3.11 přidal:
  ExceptionGroup(zpráva, [výjimky])
  except* TypVyjimky as eg:   ← hvězdička!
"""

import asyncio

# ══════════════════════════════════════════════════════════════
# ČÁST 1: ZÁKLADY ExceptionGroup
# ══════════════════════════════════════════════════════════════

print("=== ExceptionGroup – základy ===\n")

# Vytvoření
eg = ExceptionGroup("Chyby při zpracování", [
    ValueError("Špatné číslo"),
    TypeError("Špatný typ"),
    KeyError("Chybí klíč"),
])
print(f"Skupina: {eg}")
print(f"Počet výjimek: {len(eg.exceptions)}")
for e in eg.exceptions:
    print(f"  {type(e).__name__}: {e}")


# ── except* – chytání podle typu ─────────────────────────────

print("\n=== except* – filtrování ===\n")

def zpracuj_data(data: list):
    chyby = []
    vysledky = []
    for x in data:
        try:
            if not isinstance(x, (int, float)):
                raise TypeError(f"{x!r} není číslo")
            if x < 0:
                raise ValueError(f"{x} je záporné")
            vysledky.append(x ** 0.5)
        except (TypeError, ValueError) as e:
            chyby.append(e)

    if chyby:
        raise ExceptionGroup("Chyby ve vstupu", chyby)
    return vysledky

try:
    vysledky = zpracuj_data([4, -1, "ahoj", 9, -4, True, 16])
except* ValueError as eg:
    print(f"Záporná čísla ({len(eg.exceptions)}x):")
    for e in eg.exceptions:
        print(f"  - {e}")
except* TypeError as eg:
    print(f"Špatné typy ({len(eg.exceptions)}x):")
    for e in eg.exceptions:
        print(f"  - {e}")

# Pozor: except* zachytí jen odpovídající typ, zbytek propadne dál.
# Obě větve mohou být aktivní najednou (na rozdíl od except)!

print()
try:
    zpracuj_data([4, -1, "ahoj", 9])
except* ValueError as eg:
    print(f"ValueError: {[str(e) for e in eg.exceptions]}")
except* TypeError as eg:
    print(f"TypeError:  {[str(e) for e in eg.exceptions]}")


# ══════════════════════════════════════════════════════════════
# ČÁST 2: ASYNC + ExceptionGroup
# ══════════════════════════════════════════════════════════════

print("\n=== Async: více selhání najednou ===\n")

async def stahni(url: str):
    await asyncio.sleep(0.1)
    if "chyba" in url:
        raise ConnectionError(f"Nelze se připojit: {url}")
    if "timeout" in url:
        raise TimeoutError(f"Timeout: {url}")
    return f"data z {url}"

async def stahni_vse(urls: list[str]):
    async with asyncio.TaskGroup() as tg:   # Python 3.11+
        ukoly = [tg.create_task(stahni(u)) for u in urls]
    return [u.result() for u in ukoly]

async def main():
    urls = [
        "https://ok1.cz",
        "https://chyba.cz",
        "https://ok2.cz",
        "https://timeout.cz",
        "https://ok3.cz",
    ]
    try:
        vysledky = await stahni_vse(urls)
        print("Vše OK:", vysledky)
    except* ConnectionError as eg:
        print(f"Chyby spojení ({len(eg.exceptions)}):")
        for e in eg.exceptions:
            print(f"  {e}")
    except* TimeoutError as eg:
        print(f"Timeouty ({len(eg.exceptions)}):")
        for e in eg.exceptions:
            print(f"  {e}")

asyncio.run(main())


# ══════════════════════════════════════════════════════════════
# ČÁST 3: PEP 678 – Exception Notes (také Python 3.11+)
# ══════════════════════════════════════════════════════════════

print("\n=== Exception Notes (add_note) ===\n")

def validuj_vek(vek):
    if not isinstance(vek, int):
        raise TypeError(f"Věk musí být int, ne {type(vek).__name__}")
    if vek < 0:
        e = ValueError(f"Věk nemůže být záporný: {vek}")
        e.add_note("Hint: věk je celé číslo od 0 do ~150")
        e.add_note(f"Dostali jsme: {vek!r}")
        raise e
    return vek

for testovaci in [25, -5, "deset"]:
    try:
        print(f"validuj_vek({testovaci!r}) = {validuj_vek(testovaci)}")
    except (ValueError, TypeError) as e:
        print(f"Chyba: {e}")
        if hasattr(e, "__notes__"):
            for note in e.__notes__:
                print(f"  Note: {note}")


# ══════════════════════════════════════════════════════════════
# ČÁST 4: Praktická validace formuláře
# ══════════════════════════════════════════════════════════════

print("\n=== Validace formuláře – všechny chyby najednou ===\n")

@dataclass_workaround := None  # jen placeholder

def validuj_registraci(data: dict) -> dict:
    chyby = []

    jmeno = data.get("jmeno", "")
    if len(jmeno) < 2:
        chyby.append(ValueError(f"Jméno příliš krátké: {jmeno!r}"))

    email = data.get("email", "")
    if "@" not in email:
        chyby.append(ValueError(f"Neplatný email: {email!r}"))

    heslo = data.get("heslo", "")
    if len(heslo) < 8:
        e = ValueError("Heslo příliš krátké (min. 8 znaků)")
        e.add_note(f"Délka hesla: {len(heslo)}")
        chyby.append(e)

    vek = data.get("vek")
    if not isinstance(vek, int):
        chyby.append(TypeError(f"Věk musí být číslo, ne {type(vek).__name__}"))
    elif vek < 13:
        chyby.append(ValueError(f"Minimální věk je 13 let, zadáno: {vek}"))

    if chyby:
        raise ExceptionGroup("Chyby registrace", chyby)
    return data

formulare = [
    {"jmeno": "Míša", "email": "misa@example.com", "heslo": "tajneheslo123", "vek": 15},
    {"jmeno": "X",    "email": "neplatny",          "heslo": "123",           "vek": "deset"},
]

for f in formulare:
    print(f"Formulář: {f}")
    try:
        validuj_registraci(f)
        print("  ✓ Validní!\n")
    except* ValueError as eg:
        for e in eg.exceptions:
            pozn = getattr(e, "__notes__", [])
            print(f"  ✗ ValueError: {e}"
                  + (f" ({'; '.join(pozn)})" if pozn else ""))
    except* TypeError as eg:
        for e in eg.exceptions:
            print(f"  ✗ TypeError:  {e}")
    print()

# TVOJE ÚLOHA:
# 1. Přidej validaci telefonu do formuláře (musí být 9 číslic).
# 2. Napiš async funkci ping_servery(seznam) s TaskGroup, která
#    vrátí úspěšné a zaloguje chybné přes except*.
# 3. Přidej add_note() k chybě hesla s tipem na silné heslo.
