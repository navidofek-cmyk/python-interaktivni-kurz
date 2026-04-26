"""
LEKCE 42: Design Patterns (návrhové vzory)
===========================================
Vzory = osvědčená řešení opakujících se problémů.
Nepíšeš je od nuly – rozpoznáš situaci a aplikuješ vzor.

CREATIONAL  – jak vytvářet objekty
  Singleton, Factory, Builder

STRUCTURAL  – jak skládat objekty dohromady
  Adapter, Decorator, Composite

BEHAVIORAL  – jak objekty spolupracují
  Observer, Strategy, Command, Iterator
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Callable
import copy

# ══════════════════════════════════════════════════════════════
# CREATIONAL
# ══════════════════════════════════════════════════════════════

print("=== CREATIONAL PATTERNS ===\n")

# ── Factory Method ───────────────────────────────────────────
print("--- Factory Method ---")

class Logger(ABC):
    @abstractmethod
    def log(self, zprava: str) -> None: ...

class ConsoleLogger(Logger):
    def log(self, zprava): print(f"  [CONSOLE] {zprava}")

class FileLogger(Logger):
    def __init__(self, soubor: str): self.soubor = soubor
    def log(self, zprava): print(f"  [FILE:{self.soubor}] {zprava}")

class NullLogger(Logger):
    def log(self, zprava): pass   # zahodí vše

def vytvor_logger(typ: str, **kwargs) -> Logger:
    """Factory – klient neví jakou třídu dostane."""
    match typ:
        case "console": return ConsoleLogger()
        case "file":    return FileLogger(kwargs.get("soubor", "app.log"))
        case "null":    return NullLogger()
        case _:         raise ValueError(f"Neznámý typ loggeru: {typ}")

for typ in ["console", "file", "null"]:
    log = vytvor_logger(typ, soubor="test.log")
    log.log(f"Zpráva přes {typ} logger")


# ── Builder ──────────────────────────────────────────────────
print("\n--- Builder ---")

@dataclass
class HttpRequest:
    url:     str
    metoda:  str        = "GET"
    hlavicky: dict      = field(default_factory=dict)
    params:  dict       = field(default_factory=dict)
    body:    str | None = None

class RequestBuilder:
    def __init__(self, url: str):
        self._req = HttpRequest(url)

    def metoda(self, m: str)             -> RequestBuilder:
        self._req.metoda = m; return self
    def hlavicka(self, k: str, v: str)  -> RequestBuilder:
        self._req.hlavicky[k] = v; return self
    def param(self, k: str, v: str)     -> RequestBuilder:
        self._req.params[k] = v; return self
    def body(self, data: str)            -> RequestBuilder:
        self._req.body = data; return self
    def build(self)                      -> HttpRequest:
        return copy.deepcopy(self._req)

req = (RequestBuilder("https://api.example.com/data")
       .metoda("POST")
       .hlavicka("Authorization", "Bearer token123")
       .hlavicka("Content-Type", "application/json")
       .param("verze", "2")
       .body('{"klic": "hodnota"}')
       .build())

print(f"  URL:     {req.url}")
print(f"  Metoda:  {req.metoda}")
print(f"  Hlavičky:{req.hlavicky}")
print(f"  Body:    {req.body}")


# ══════════════════════════════════════════════════════════════
# STRUCTURAL
# ══════════════════════════════════════════════════════════════

print("\n=== STRUCTURAL PATTERNS ===\n")

# ── Adapter ──────────────────────────────────────────────────
print("--- Adapter ---")

class StareLegacyAPI:
    """Starý kód který nemůžeš změnit."""
    def ziskej_data_xml(self) -> str:
        return "<user><name>Míša</name><age>15</age></user>"

class ModerniRozhrani(ABC):
    @abstractmethod
    def ziskej_uzivatele(self) -> dict: ...

import re

class LegacyAdapter(ModerniRozhrani):
    """Obalí starý kód do moderního rozhraní."""
    def __init__(self, stare: StareLegacyAPI):
        self._stare = stare

    def ziskej_uzivatele(self) -> dict:
        xml  = self._stare.ziskej_data_xml()
        jmeno = re.search(r"<name>(.*?)</name>", xml).group(1)
        vek   = re.search(r"<age>(.*?)</age>",   xml).group(1)
        return {"jmeno": jmeno, "vek": int(vek)}

adapter = LegacyAdapter(StareLegacyAPI())
print(f"  Moderní výstup: {adapter.ziskej_uzivatele()}")


# ── Composite ────────────────────────────────────────────────
print("\n--- Composite (strom souborů) ---")

class FsUzel(ABC):
    def __init__(self, nazev: str): self.nazev = nazev
    @abstractmethod
    def velikost(self) -> int: ...
    @abstractmethod
    def tiskni(self, odsazeni: str = "") -> None: ...

class Soubor(FsUzel):
    def __init__(self, nazev: str, vel: int):
        super().__init__(nazev); self.vel = vel
    def velikost(self): return self.vel
    def tiskni(self, o=""):
        print(f"{o}📄 {self.nazev} ({self.vel} B)")

class Adresar(FsUzel):
    def __init__(self, nazev: str):
        super().__init__(nazev); self.deti: list[FsUzel] = []
    def pridej(self, uzel: FsUzel) -> Adresar:
        self.deti.append(uzel); return self
    def velikost(self): return sum(d.velikost() for d in self.deti)
    def tiskni(self, o=""):
        print(f"{o}📁 {self.nazev}/ ({self.velikost()} B)")
        for d in self.deti: d.tiskni(o + "  ")

projekt = (Adresar("projekt")
    .pridej(Soubor("README.md", 1200))
    .pridej(Adresar("src")
        .pridej(Soubor("main.py", 3400))
        .pridej(Soubor("utils.py", 1800)))
    .pridej(Adresar("tests")
        .pridej(Soubor("test_main.py", 2100))))

projekt.tiskni()
print(f"  Celkem: {projekt.velikost()} B")


# ══════════════════════════════════════════════════════════════
# BEHAVIORAL
# ══════════════════════════════════════════════════════════════

print("\n=== BEHAVIORAL PATTERNS ===\n")

# ── Observer ─────────────────────────────────────────────────
print("--- Observer (Event System) ---")

class EventEmitter:
    def __init__(self):
        self._handlers: dict[str, list[Callable]] = {}

    def on(self, udalost: str, handler: Callable) -> None:
        self._handlers.setdefault(udalost, []).append(handler)

    def emit(self, udalost: str, **data) -> None:
        for h in self._handlers.get(udalost, []):
            h(**data)

    def off(self, udalost: str, handler: Callable) -> None:
        self._handlers.get(udalost, []).remove(handler)

class Obchod(EventEmitter):
    def __init__(self):
        super().__init__()
        self._kosik: list[str] = []

    def pridej_do_kosiku(self, produkt: str):
        self._kosik.append(produkt)
        self.emit("pridano", produkt=produkt, kosik=self._kosik)

    def nakup(self):
        self.emit("nakup", kosik=self._kosik[:])
        self._kosik.clear()

obchod = Obchod()
obchod.on("pridano", lambda produkt, kosik: print(f"  + přidán {produkt!r}, košík: {kosik}"))
obchod.on("nakup",   lambda kosik: print(f"  💳 Nakoupeno: {kosik}"))
obchod.on("nakup",   lambda kosik: print(f"  📧 Email: Vaše objednávka ({len(kosik)} položek) byla přijata."))

obchod.pridej_do_kosiku("meč")
obchod.pridej_do_kosiku("štít")
obchod.nakup()


# ── Strategy ─────────────────────────────────────────────────
print("\n--- Strategy ---")

type Tridici = Callable[[list], list]

def bubble(lst: list) -> list:
    s = lst[:]
    for i in range(len(s)):
        for j in range(len(s)-1-i):
            if s[j] > s[j+1]: s[j], s[j+1] = s[j+1], s[j]
    return s

class Tridic:
    def __init__(self, strategie: Tridici = sorted):
        self._strategie = strategie

    def zmen_strategii(self, strategie: Tridici) -> None:
        self._strategie = strategie

    def setrid(self, data: list) -> list:
        return self._strategie(data)

data = [5, 3, 8, 1, 9]
t = Tridic()
print(f"  sorted:   {t.setrid(data)}")
t.zmen_strategii(bubble)
print(f"  bubble:   {t.setrid(data)}")
t.zmen_strategii(lambda s: sorted(s, reverse=True))
print(f"  reversed: {t.setrid(data)}")


# ── Command ──────────────────────────────────────────────────
print("\n--- Command (Undo/Redo) ---")

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
        self.editor = editor; self.text = text; self.pozice = pozice
    def proved(self):
        t = self.editor._text
        self.editor._text = t[:self.pozice] + self.text + t[self.pozice:]
    def zpet(self):
        t = self.editor._text
        self.editor._text = t[:self.pozice] + t[self.pozice+len(self.text):]

editor = TextEditor()
editor.proved(Vloz(editor, "Ahoj", 0))
editor.proved(Vloz(editor, " světe", 4))
editor.proved(Vloz(editor, "!", 10))
print(f"  Text: {editor.text!r}")

editor.undo()
print(f"  Po undo: {editor.text!r}")
editor.undo()
print(f"  Po undo: {editor.text!r}")
editor.redo()
print(f"  Po redo: {editor.text!r}")

# TVOJE ÚLOHA:
# 1. Přidej do TextEditor příkaz Smaz(od, do) s undo.
# 2. Rozšiř EventEmitter o once(udalost, handler) – handler zavolán jen jednou.
# 3. Napiš vzor Chain of Responsibility pro zpracování HTTP requestu
#    (middleware: autentizace → logování → rate-limit → handler).
