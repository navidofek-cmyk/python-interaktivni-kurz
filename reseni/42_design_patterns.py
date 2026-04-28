"""Reseni – Lekce 42: Design Patterns"""

from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Callable


# 1. Pridat do TextEditor prikaz Smaz(od, do) s undo

class Prikaz(ABC):
    @abstractmethod
    def proved(self) -> None: ...
    @abstractmethod
    def zpet(self) -> None: ...


@dataclass
class TextEditor:
    _text: str = ""
    _historie: list[Prikaz] = field(default_factory=list)
    _redo_zasobnik: list[Prikaz] = field(default_factory=list)

    @property
    def text(self): return self._text

    def proved(self, prikaz: Prikaz) -> None:
        prikaz.proved()
        self._historie.append(prikaz)
        self._redo_zasobnik.clear()

    def undo(self) -> None:
        if self._historie:
            p = self._historie.pop()
            p.zpet()
            self._redo_zasobnik.append(p)

    def redo(self) -> None:
        if self._redo_zasobnik:
            p = self._redo_zasobnik.pop()
            p.proved()
            self._historie.append(p)


class Vloz(Prikaz):
    def __init__(self, editor: TextEditor, text: str, pozice: int):
        self.editor = editor
        self.text = text
        self.pozice = pozice

    def proved(self):
        t = self.editor._text
        self.editor._text = t[:self.pozice] + self.text + t[self.pozice:]

    def zpet(self):
        t = self.editor._text
        self.editor._text = t[:self.pozice] + t[self.pozice + len(self.text):]


class Smaz(Prikaz):
    """Ukol 1: Smaze znaky od pozice 'od' do 'do' (exkluzivni), podporuje undo."""

    def __init__(self, editor: TextEditor, od: int, do: int):
        self.editor = editor
        self.od = od
        self.do = do
        self._smazany_text: str = ""   # ulozeno pro undo

    def proved(self):
        t = self.editor._text
        self._smazany_text = t[self.od:self.do]
        self.editor._text = t[:self.od] + t[self.do:]

    def zpet(self):
        t = self.editor._text
        self.editor._text = t[:self.od] + self._smazany_text + t[self.od:]


print("=== Ukol 1: Smaz prikaz s undo ===\n")

editor = TextEditor()
editor.proved(Vloz(editor, "Ahoj svete!", 0))
print(f"Zakladni text: {editor.text!r}")

editor.proved(Smaz(editor, 5, 11))   # smaze " svete"
print(f"Po Smaz(5,11): {editor.text!r}")

editor.undo()
print(f"Po undo:       {editor.text!r}")

editor.redo()
print(f"Po redo:       {editor.text!r}")


# 2. Rozsirit EventEmitter o once(udalost, handler)

print("\n=== Ukol 2: EventEmitter.once() ===\n")


class EventEmitter:
    def __init__(self):
        self._handlers: dict[str, list[Callable]] = {}
        self._once_handlers: dict[str, list[Callable]] = {}

    def on(self, udalost: str, handler: Callable) -> None:
        self._handlers.setdefault(udalost, []).append(handler)

    def once(self, udalost: str, handler: Callable) -> None:
        """Ukol 2: Handler zavolany jen jednou, pak odstranen."""
        self._once_handlers.setdefault(udalost, []).append(handler)

    def emit(self, udalost: str, **data) -> None:
        for h in self._handlers.get(udalost, []):
            h(**data)
        # Jednorate handlery – spust a smaz
        jednorazove = self._once_handlers.pop(udalost, [])
        for h in jednorazove:
            h(**data)

    def off(self, udalost: str, handler: Callable) -> None:
        self._handlers.get(udalost, []).remove(handler)


emitter = EventEmitter()
pocitadlo = {"n": 0}

emitter.once("pozdrav", lambda **kw: pocitadlo.update({"n": pocitadlo["n"] + 1}))
emitter.once("pozdrav", lambda **kw: print(f"  once handler: {kw}"))

emitter.emit("pozdrav", text="Ahoj!")
emitter.emit("pozdrav", text="Ahoj znovu!")   # once handlery se uz nezavolaji

print(f"  Once handler zavolany {pocitadlo['n']}× (ocekavano 1)")


# 3. Chain of Responsibility – HTTP middleware pipeline

print("\n=== Ukol 3: Chain of Responsibility (HTTP middleware) ===\n")


@dataclass
class Request:
    metoda: str
    cesta: str
    hlavicky: dict = field(default_factory=dict)
    uzivatel: str | None = None


@dataclass
class Response:
    kod: int
    telo: str


class Middleware(ABC):
    def __init__(self):
        self._dalsi: Middleware | None = None

    def chain(self, dalsi: "Middleware") -> "Middleware":
        self._dalsi = dalsi
        return dalsi

    @abstractmethod
    def handle(self, req: Request) -> Response: ...

    def _predej(self, req: Request) -> Response:
        if self._dalsi:
            return self._dalsi.handle(req)
        return Response(404, "Zadny handler")


class AutentizaceMiddleware(Middleware):
    """Kontroluje API klic v hlavickach."""
    PLATNE_KLICE = {"tajne", "api-key-456"}

    def handle(self, req: Request) -> Response:
        klic = req.hlavicky.get("X-Api-Key", "")
        if klic not in self.PLATNE_KLICE:
            return Response(401, "Neautorizovano")
        req.uzivatel = f"user-{klic[:3]}"
        print(f"  [Auth] Uzivatel {req.uzivatel!r} overeni OK")
        return self._predej(req)


class LogovaniMiddleware(Middleware):
    """Loguje kazdy prichozi request."""

    def handle(self, req: Request) -> Response:
        print(f"  [Log] {req.metoda} {req.cesta} (uzivatel={req.uzivatel})")
        resp = self._predej(req)
        print(f"  [Log] Odpoved: {resp.kod}")
        return resp


class RateLimitMiddleware(Middleware):
    """Omezi pocet pozadavku na 3 na session."""
    _pocitadla: dict[str, int] = {}
    LIMIT = 3

    def handle(self, req: Request) -> Response:
        klic = req.uzivatel or "anon"
        self._pocitadla[klic] = self._pocitadla.get(klic, 0) + 1
        pocet = self._pocitadla[klic]
        if pocet > self.LIMIT:
            print(f"  [RateLimit] {klic} prekrocil limit ({pocet}>{self.LIMIT})")
            return Response(429, "Prilis mnoho pozadavku")
        print(f"  [RateLimit] {klic}: {pocet}/{self.LIMIT}")
        return self._predej(req)


class FinalnHandler(Middleware):
    """Samotny handler – vrati odpoved."""

    def handle(self, req: Request) -> Response:
        print(f"  [Handler] Zpracovavam {req.cesta}")
        return Response(200, f"OK: {req.cesta}")


# Sestaveni pipeline
auth     = AutentizaceMiddleware()
logging_ = LogovaniMiddleware()
rate     = RateLimitMiddleware()
handler  = FinalnHandler()

auth.chain(logging_).chain(rate).chain(handler)

# Testovaci pozadavky
pozadavky = [
    Request("GET", "/api/data", {"X-Api-Key": "tajne"}),
    Request("GET", "/api/data", {"X-Api-Key": "tajne"}),
    Request("POST", "/api/vytvor", {"X-Api-Key": "tajne"}),
    Request("GET", "/api/extra", {"X-Api-Key": "tajne"}),   # rate limit
    Request("GET", "/api/bez-klice"),                        # 401
]

for i, req in enumerate(pozadavky, 1):
    print(f"\nPozadavek {i}: {req.metoda} {req.cesta}")
    resp = auth.handle(req)
    print(f"  => {resp.kod}: {resp.telo}")
