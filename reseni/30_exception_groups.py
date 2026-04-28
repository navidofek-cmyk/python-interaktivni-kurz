"""Řešení – Lekce 30: Exception Groups a except* (Python 3.11+)"""

import asyncio
import re


# 1. Validace telefonu v registračním formuláři
# Přidáme do stávající funkce validace telefonu (9 číslic)

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
        # 3. Přidáme tip na silné heslo
        e.add_note("Tip: Použij kombinaci písmen, číslic a speciálních znaků")
        chyby.append(e)

    vek = data.get("vek")
    if not isinstance(vek, int):
        chyby.append(TypeError(f"Věk musí být číslo, ne {type(vek).__name__}"))
    elif vek < 13:
        chyby.append(ValueError(f"Minimální věk je 13 let, zadáno: {vek}"))

    # 1. Validace telefonu – musí být přesně 9 číslic (může začínat +420)
    # re.fullmatch ověřuje celý řetězec, ne jen část
    telefon = data.get("telefon", "")
    telefon_cisla = re.sub(r"[\s\-\+]", "", telefon)  # odstraní mezery, pomlčky, +
    if telefon and not re.fullmatch(r"\d{9}", telefon_cisla):
        e = ValueError(f"Telefon musí mít 9 číslic, dostal: {telefon!r}")
        e.add_note(f"Číslic nalezeno: {len(telefon_cisla)}")
        chyby.append(e)

    if chyby:
        raise ExceptionGroup("Chyby registrace", chyby)
    return data


print("=== Validace formuláře s telefonem ===\n")

formulare = [
    {
        "jmeno": "Míša",
        "email": "misa@example.com",
        "heslo": "tajneheslo123",
        "vek": 15,
        "telefon": "603123456",      # správný
    },
    {
        "jmeno": "X",
        "email": "neplatny",
        "heslo": "123",
        "vek": "deset",
        "telefon": "12345",          # příliš krátký
    },
    {
        "jmeno": "Karel",
        "email": "k@k.cz",
        "heslo": "heslo123456",
        "vek": 25,
        "telefon": "+420 603 456 789",  # správný s předvolbou
    },
]

for f in formulare:
    print(f"Formulář: {f.get('jmeno', '?')}")
    try:
        validuj_registraci(f)
        print("  Validní!")
    except* ValueError as eg:
        for e in eg.exceptions:
            pozn = getattr(e, "__notes__", [])
            print(f"  ValueError: {e}"
                  + (f" | {'; '.join(pozn)}" if pozn else ""))
    except* TypeError as eg:
        for e in eg.exceptions:
            print(f"  TypeError:  {e}")
    print()


# 2. Async ping serverů s TaskGroup
# except* zachytí více ConnectionError a TimeoutError najednou

async def ping(server: str) -> str:
    await asyncio.sleep(0.05)
    if "down" in server:
        raise ConnectionError(f"Server {server} nedostupný")
    if "slow" in server:
        raise TimeoutError(f"Server {server} neodpověděl včas")
    return f"{server}: OK"


async def ping_servery(seznam: list[str]) -> tuple[list[str], list[Exception]]:
    """Pingne všechny servery, vrátí (uspesne, chybne)."""
    uspesne = []
    chybne = []

    async def zkus_ping(server):
        result = await ping(server)
        uspesne.append(result)

    try:
        async with asyncio.TaskGroup() as tg:
            for s in seznam:
                tg.create_task(zkus_ping(s))
    except* ConnectionError as eg:
        for e in eg.exceptions:
            chybne.append(e)
            print(f"  [ping] Chyba spojení: {e}")
    except* TimeoutError as eg:
        for e in eg.exceptions:
            chybne.append(e)
            print(f"  [ping] Timeout: {e}")

    return uspesne, chybne


print("=== Async ping serverů ===\n")

servery = [
    "web1.ok.cz",
    "web2.down.cz",
    "api.ok.cz",
    "db.slow.cz",
    "cdn.ok.cz",
]

uspesne, chybne = asyncio.run(ping_servery(servery))
print(f"\nÚspěšné ({len(uspesne)}): {uspesne}")
print(f"Chybné  ({len(chybne)}): {[str(e) for e in chybne]}")
