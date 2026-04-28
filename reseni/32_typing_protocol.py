"""Řešení – Lekce 32: Typing – Protocol, TypedDict, TypeVar, Generic"""

from __future__ import annotations
from typing import Protocol, runtime_checkable, TypedDict, Required, NotRequired, TypeVar, Generic
import json
import pickle


# 1. Protocol Serizovatelny + implementace bez dědičnosti
# Structural subtyping: stačí mít správné metody, žádné explicitní dědění
# Výhoda: lze přidat serializaci ke stávajícím třídám bez změny hierarchie

@runtime_checkable
class Serizovatelny(Protocol):
    """Objekt, který umí serializovat sám sebe do bytes a zpět."""
    def uloz(self) -> bytes: ...

    @classmethod
    def nacti(cls, data: bytes) -> "Serizovatelny": ...


class JsonSerizovatelny:
    """Implementuje Serizovatelny přes JSON – bez dědičnosti z Protocol."""

    def __init__(self, data: dict):
        self.data = data

    def uloz(self) -> bytes:
        return json.dumps(self.data, ensure_ascii=False).encode("utf-8")

    @classmethod
    def nacti(cls, data: bytes) -> "JsonSerizovatelny":
        return cls(json.loads(data.decode("utf-8")))

    def __repr__(self):
        return f"JsonSerizovatelny({self.data})"


class PickleSerizovatelny:
    """Implementuje Serizovatelny přes pickle – binární formát."""

    def __init__(self, hodnota):
        self.hodnota = hodnota

    def uloz(self) -> bytes:
        return pickle.dumps(self.hodnota)

    @classmethod
    def nacti(cls, data: bytes) -> "PickleSerizovatelny":
        return cls(pickle.loads(data))

    def __repr__(self):
        return f"PickleSerizovatelny({self.hodnota!r})"


print("=== Protocol Serizovatelny ===\n")

j = JsonSerizovatelny({"jmeno": "Míša", "vek": 15})
p = PickleSerizovatelny([1, 2, 3, "ahoj"])

print(f"JSON isinstance check: {isinstance(j, Serizovatelny)}")
print(f"Pickle isinstance check: {isinstance(p, Serizovatelny)}")

for obj in [j, p]:
    bajty = obj.uloz()
    obnoveny = type(obj).nacti(bajty)
    print(f"\n{type(obj).__name__}:")
    print(f"  Uloženo: {len(bajty)} bajtů")
    print(f"  Obnoveno: {obnoveny}")


# 2. Generická třída Fronta[T] – FIFO (first in, first out)
# Na rozdíl od Stack[T] (LIFO), fronta odebírá z přední strany
# Generic[T] umožňuje typovači ověřit homogenitu prvků

T = TypeVar("T")


class Fronta(Generic[T]):
    """FIFO fronta parametrizovaná typem."""

    def __init__(self) -> None:
        self._prvky: list[T] = []

    def vloz(self, prvek: T) -> None:
        """Přidá prvek na konec fronty."""
        self._prvky.append(prvek)

    def odeber(self) -> T:
        """Odebere a vrátí prvek z přední strany fronty."""
        if not self._prvky:
            raise IndexError("Fronta je prázdná")
        return self._prvky.pop(0)

    def nahlednik(self) -> T:
        """Vrátí první prvek bez odebrání."""
        if not self._prvky:
            raise IndexError("Fronta je prázdná")
        return self._prvky[0]

    def je_prazdna(self) -> bool:
        return len(self._prvky) == 0

    def __len__(self) -> int:
        return len(self._prvky)

    def __repr__(self) -> str:
        return f"Fronta({self._prvky})"


print("\n=== Generická Fronta[T] ===\n")

# Fronta celých čísel
int_fronta: Fronta[int] = Fronta()
for n in [10, 20, 30, 40]:
    int_fronta.vloz(n)
print(f"Fronta čísel: {int_fronta}")
print(f"Odebráno: {int_fronta.odeber()}")  # 10 (FIFO)
print(f"Odebráno: {int_fronta.odeber()}")  # 20
print(f"Zbývá: {int_fronta}")

# Fronta řetězců
str_fronta: Fronta[str] = Fronta()
for s in ["první", "druhý", "třetí"]:
    str_fronta.vloz(s)
print(f"\nFronta řetězců: {str_fronta}")
print(f"Nahlédnutí (bez odebrání): {str_fronta.nahlednik()}")
print(f"Délka: {len(str_fronta)}")


# 3. TypedDict pro konfiguraci databáze
# TypedDict dává slovníku pevnou strukturu – IDE a typovač ověří klíče

class DbConfig(TypedDict):
    host: str
    port: int
    user: str
    password: str
    db_name: str
    ssl: NotRequired[bool]  # volitelné


def pripoj(config: DbConfig) -> str:
    """Sestaví connection string z konfigurace."""
    ssl_part = "?ssl=true" if config.get("ssl") else ""
    return (f"postgresql://{config['user']}:{config['password']}"
            f"@{config['host']}:{config['port']}"
            f"/{config['db_name']}{ssl_part}")


print("\n=== TypedDict DbConfig ===\n")

vyvoj: DbConfig = {
    "host": "localhost",
    "port": 5432,
    "user": "dev",
    "password": "devpass",
    "db_name": "myapp_dev",
}

produkce: DbConfig = {
    "host": "db.production.example.com",
    "port": 5432,
    "user": "app",
    "password": "s3cr3t",
    "db_name": "myapp",
    "ssl": True,
}

print(f"Vývoj:    {pripoj(vyvoj)}")
print(f"Produkce: {pripoj(produkce)}")
