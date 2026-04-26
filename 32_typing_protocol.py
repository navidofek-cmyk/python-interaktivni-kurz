"""
LEKCE 32: Typing – Protocol, TypedDict, TypeVar, Generic
==========================================================
Z dokumentace: typing modul, PEP 544 (Protocol), PEP 589 (TypedDict),
PEP 695 (nová syntaxe type parametrů, Python 3.12).

Python je dynamicky typovaný, ale type hints + mypy/pyright
chytí chyby dřív, než program spustíš.

PROTOCOL   = "duck typing" formalizovaný.
             Třída splňuje Protocol, pokud má správné metody –
             bez dědičnosti (structural subtyping).

TYPEDDICT  = slovník se známými klíči a jejich typy.

TYPEVAR    = placeholder pro "nějaký typ" v generických funkcích.

GENERIC    = třída parametrizovaná typem (jako list[int]).
"""

from __future__ import annotations
from typing import (
    Protocol, runtime_checkable,
    TypedDict, Required, NotRequired,
    TypeVar, Generic,
    overload, Final, Literal,
    TYPE_CHECKING,
)
from dataclasses import dataclass
import sys

# ══════════════════════════════════════════════════════════════
# ČÁST 1: PROTOCOL – duck typing s ověřením
# ══════════════════════════════════════════════════════════════

print("=== Protocol ===\n")

@runtime_checkable   # umožní isinstance() kontrolu
class Kreslitelny(Protocol):
    def kresli(self) -> str: ...
    def presun(self, x: float, y: float) -> None: ...

@runtime_checkable
class Ukladatelny(Protocol):
    def uloz(self) -> dict: ...
    @classmethod
    def nacti(cls, data: dict) -> Ukladatelny: ...

# Tyto třídy NEDĚDÍ z Protocol – jen implementují správné metody
class Kruh:
    def __init__(self, x, y, r):
        self.x, self.y, self.r = x, y, r

    def kresli(self) -> str:
        return f"○ Kruh na ({self.x},{self.y}) r={self.r}"

    def presun(self, x, y):
        self.x, self.y = x, y

    def uloz(self):
        return {"typ": "kruh", "x": self.x, "y": self.y, "r": self.r}

    @classmethod
    def nacti(cls, data):
        return cls(data["x"], data["y"], data["r"])

class Ctverec:
    def __init__(self, x, y, strana):
        self.x, self.y, self.strana = x, y, strana

    def kresli(self) -> str:
        return f"□ Čtverec na ({self.x},{self.y}) a={self.strana}"

    def presun(self, x, y):
        self.x, self.y = x, y

def vykresli_vse(tvary: list[Kreslitelny]) -> None:
    for t in tvary:
        print(" ", t.kresli())

def uloz_vse(tvary: list[Ukladatelny]) -> list[dict]:
    return [t.uloz() for t in tvary]

k = Kruh(0, 0, 5)
c = Ctverec(10, 10, 4)

print("isinstance check:")
print(f"  Kruh je Kreslitelny?   {isinstance(k, Kreslitelny)}")
print(f"  Ctverec je Kreslitelny? {isinstance(c, Kreslitelny)}")
print(f"  Ctverec je Ukladatelny? {isinstance(c, Ukladatelny)}")  # False – nemá uloz

print("\nKreslení:")
vykresli_vse([k, c])

k.presun(3, 4)
print(f"\nPo přesunu: {k.kresli()}")
print(f"Uloženo: {uloz_vse([k])}")

# ── Protocol pro comparable (jako v std knihovně) ─────────────

class SupportsLessThan(Protocol):
    def __lt__(self, other) -> bool: ...

def minimum(seq: list[SupportsLessThan]) -> SupportsLessThan:
    vysledek = seq[0]
    for x in seq[1:]:
        if x < vysledek:
            vysledek = x
    return vysledek

print(f"\nminimum([3,1,4,1,5]) = {minimum([3,1,4,1,5])}")
print(f"minimum(['b','a','c']) = {minimum(['b','a','c'])}")


# ══════════════════════════════════════════════════════════════
# ČÁST 2: TypedDict
# ══════════════════════════════════════════════════════════════

print("\n=== TypedDict ===\n")

class Uzivatel(TypedDict):
    jmeno:    str
    email:    str
    vek:      int
    bio:      NotRequired[str]   # volitelné (Python 3.11+)

class ApiOdpoved(TypedDict):
    status:   Literal["ok", "error"]   # jen tyto dvě hodnoty
    data:     Required[list]
    zprava:   NotRequired[str]

def vytvor_uzivatele(jmeno: str, email: str, vek: int) -> Uzivatel:
    return {"jmeno": jmeno, "email": email, "vek": vek}

def zpracuj_odpoved(odpoved: ApiOdpoved) -> None:
    if odpoved["status"] == "ok":
        print(f"  OK: {len(odpoved['data'])} záznamů")
    else:
        print(f"  Chyba: {odpoved.get('zprava', 'neznámá')}")

u = vytvor_uzivatele("Míša", "misa@example.com", 15)
u["bio"] = "Programátorka"   # NotRequired – lze přidat
print("Uživatel:", u)

zpracuj_odpoved({"status": "ok",    "data": [1, 2, 3]})
zpracuj_odpoved({"status": "error", "data": [], "zprava": "Neautorizováno"})

# TypedDict v reálném JSON API
import json

RAW_JSON = '''[
    {"jmeno": "Tomáš", "email": "t@t.cz", "vek": 25},
    {"jmeno": "Bára",  "email": "b@b.cz", "vek": 30, "bio": "Dev"}
]'''

uzivatele: list[Uzivatel] = json.loads(RAW_JSON)
for uz in uzivatele:
    bio = uz.get("bio", "—")
    print(f"  {uz['jmeno']:10} {uz['email']:20} {uz['vek']}  bio: {bio}")


# ══════════════════════════════════════════════════════════════
# ČÁST 3: TypeVar + Generic
# ══════════════════════════════════════════════════════════════

print("\n=== TypeVar a Generic ===\n")

T = TypeVar("T")
K = TypeVar("K")
V = TypeVar("V")

# Generická funkce – funguje pro libovolný typ
def prvni(seq: list[T]) -> T:
    return seq[0]

def posledni(seq: list[T]) -> T:
    return seq[-1]

print(f"prvni([1,2,3])       = {prvni([1,2,3])}")
print(f"prvni(['a','b','c']) = {prvni(['a','b','c'])}")
print(f"posledni([10,20,30]) = {posledni([10,20,30])}")

# Generická třída – vlastní Stack
class Stack(Generic[T]):
    def __init__(self) -> None:
        self._items: list[T] = []

    def push(self, item: T) -> None:
        self._items.append(item)

    def pop(self) -> T:
        if not self._items:
            raise IndexError("Stack je prázdný")
        return self._items.pop()

    def peek(self) -> T:
        return self._items[-1]

    def __len__(self) -> int:
        return len(self._items)

    def __repr__(self) -> str:
        return f"Stack({self._items})"

print("\n--- Generický Stack ---")
int_stack: Stack[int] = Stack()
int_stack.push(1)
int_stack.push(2)
int_stack.push(3)
print(int_stack)
print(f"pop: {int_stack.pop()}")
print(int_stack)

str_stack: Stack[str] = Stack()
str_stack.push("ahoj")
str_stack.push("světe")
print(str_stack)

# Python 3.12: nová syntaxe type[T] místo TypeVar
# (pokud máš 3.12+)
if sys.version_info >= (3, 12):
    exec("""
def prvni_312[T](seq: list[T]) -> T:
    return seq[0]
print(f"\\n3.12 syntax: prvni_312([42,43]) = {prvni_312([42,43])}")
""")


# ══════════════════════════════════════════════════════════════
# ČÁST 4: overload, Final, Literal
# ══════════════════════════════════════════════════════════════

print("\n=== overload, Final, Literal ===\n")

# overload – různé signatury pro stejnou funkci
@overload
def zdvoj(x: int) -> int: ...
@overload
def zdvoj(x: str) -> str: ...
@overload
def zdvoj(x: list) -> list: ...

def zdvoj(x):
    if isinstance(x, list):
        return x + x
    return x * 2

print(f"zdvoj(5)       = {zdvoj(5)}")
print(f"zdvoj('ab')    = {zdvoj('ab')}")
print(f"zdvoj([1,2])   = {zdvoj([1,2])}")

# Final – konstanta, nelze přepsat
MAX_POKUSU: Final = 3
VERZE:      Final[str] = "1.0.0"
print(f"\nMAX_POKUSU = {MAX_POKUSU}")

# Literal – jen konkrétní hodnoty
Smer = Literal["sever", "jih", "vychod", "zapad"]

def jdi(smer: Smer) -> str:
    return f"Jdeš na {smer}."

print(jdi("sever"))   # mypy/pyright ví, že jen tyto hodnoty jsou OK


# ── Praktické shrnutí ─────────────────────────────────────────
print("\n=== Kdy co použít ===")
print("""
  Protocol    → "tato třída musí umět X" bez dědičnosti
                (duck typing s ověřením typovačem)

  TypedDict   → slovník s pevnou strukturou (JSON API, konfigurace)

  TypeVar     → "tento typ je libovolný, ale konzistentní"
                (generické funkce a třídy)

  Generic[T]  → vlastní kontejnerová/generická třída

  overload    → funkce s více typy argumentů

  Final       → konstanta, kterou nelze přepsat

  Literal     → "jen tyto konkrétní hodnoty"
""")

# TVOJE ÚLOHA:
# 1. Napiš Protocol Serizovatelny s metodami uloz() -> bytes a nacti(bytes).
#    Implementuj ho pro třídy JSON a Pickle bez dědičnosti.
# 2. Napiš generickou třídu Fronta[T] (queue – FIFO, na rozdíl od Stack LIFO).
# 3. Napiš TypedDict pro konfiguraci databáze (host, port, user, password, db_name)
#    a funkci pripoj(config: DbConfig) -> str.
