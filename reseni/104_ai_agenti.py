"""Řešení – Lekce 104: Autonomní AI agenti

Toto je vzorové řešení úloh z lekce 104.
"""

import os
import re
import subprocess
import time
from dataclasses import dataclass, field
from typing import Any, Callable


# ── Pomocné definice ze lekce ──────────────────────────────

@dataclass
class Tool:
    name: str
    description: str
    parameters: dict[str, str]
    func: Callable

    def to_schema(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": {
                "type": "object",
                "properties": {
                    k: {"type": "string", "description": v}
                    for k, v in self.parameters.items()
                },
                "required": list(self.parameters.keys()),
            },
        }


def get_weather(city: str) -> str:
    data = {"Praha": "18°C, slunečno", "Brno": "16°C, oblačno", "Ostrava": "14°C, déšť"}
    return data.get(city, f"Data pro '{city}' nedostupná.")


def run_python(code: str) -> str:
    zakazane = ["import os", "import sys", "subprocess", "__import__", "open(", "exec(", "eval("]
    for z in zakazane:
        if z in code:
            return f"ODMÍTNUTO: '{z}'."
    try:
        result = subprocess.run(["python3", "-c", code], capture_output=True, text=True, timeout=5)
        return (result.stdout or result.stderr)[:300] or "(žádný výstup)"
    except subprocess.TimeoutExpired:
        return "TIMEOUT"


def calculate(expression: str) -> str:
    try:
        if not re.match(r'^[\d\s\+\-\*\/\(\)\.\,\^]+$', expression):
            return "Neplatný výraz."
        return str(eval(expression))  # noqa: S307
    except Exception as e:
        return f"Chyba: {e}"


# ── Úloha 1 ────────────────────────────────────────────────
# write_file(path, content) – povoleno jen do /tmp/

def write_file(path: str, content: str) -> str:
    """
    Zapíše obsah do souboru.
    Guardrail: povoluje zápis POUZE do /tmp/.
    """
    import pathlib
    p = pathlib.Path(path).resolve()
    if not str(p).startswith("/tmp/"):
        return f"ODMÍTNUTO: Zápis mimo /tmp/ není povolen. ('{p}')"
    try:
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
        return f"Soubor '{p}' zapsán ({len(content)} znaků)."
    except Exception as e:
        return f"Chyba zápisu: {e}"


TOOLS: dict[str, Tool] = {
    "get_weather": Tool("get_weather", "Zjistí počasí.", {"city": "Název města"}, get_weather),
    "calculate":   Tool("calculate", "Vypočítá výraz.", {"expression": "Matematický výraz"}, calculate),
    "run_python":  Tool("run_python", "Spustí Python kód.", {"code": "Kód"}, run_python),
    "write_file":  Tool(
        "write_file",
        "Zapíše soubor do /tmp/.",
        {"path": "Cesta v /tmp/", "content": "Obsah souboru"},
        write_file,
    ),
}

print("── Úloha 1: write_file() ──")
print(write_file("/tmp/test_agent.txt", "Ahoj z agenta!\nDruhý řádek."))
print(write_file("/etc/passwd", "hack"))  # odmítnuto
print(write_file("/tmp/subdir/soubor.txt", "Obsah v podadresáři."))


# ── Úloha 2 ────────────────────────────────────────────────
# AgentSPameti.zapomen() a shrnuti_pameti()

@dataclass
class AgentSPameti:
    """Agent s konverzační a dlouhodobou pamětí."""

    max_zprav: int = 20
    zpravy: list[dict] = field(default_factory=list)
    fakty: dict[str, Any] = field(default_factory=dict)

    def zapamatuj_si(self, klic: str, hodnota: Any) -> None:
        self.fakty[klic] = hodnota

    def zapomen(self, klic: str) -> bool:
        """
        Odstraní fakt z dlouhodobé paměti.
        Vrátí True pokud klíč existoval.
        """
        if klic in self.fakty:
            del self.fakty[klic]
            return True
        return False

    def vzpomen_si(self, klic: str) -> Any:
        return self.fakty.get(klic)

    def shrnuti_pameti(self) -> list[str]:
        """
        Vrátí seznam uložených faktů jako čitelné řetězce.
        """
        return [f"{k}: {v!r}" for k, v in self.fakty.items()]

    def pridej_zpravu(self, role: str, obsah: str) -> None:
        self.zpravy.append({"role": role, "content": obsah})
        if len(self.zpravy) > self.max_zprav:
            self.zpravy = self.zpravy[-self.max_zprav:]

    def system_prompt(self) -> str:
        fakty_str = "\n".join(f"- {k}: {v}" for k, v in self.fakty.items())
        return f"Jsi pomocný asistent. Fakta o uživateli:\n{fakty_str}"


print("\n── Úloha 2: AgentSPameti.zapomen() a shrnuti_pameti() ──")
agent = AgentSPameti()
agent.zapamatuj_si("jmeno", "Ivan")
agent.zapamatuj_si("uroven", "pokrocily")
agent.zapamatuj_si("jazyk", "Python")

print(f"Paměť: {agent.shrnuti_pameti()}")
print(f"Zapomenut 'jazyk': {agent.zapomen('jazyk')}")
print(f"Zapomenut 'neexistuje': {agent.zapomen('neexistuje')}")
print(f"Paměť po zapomenutí: {agent.shrnuti_pameti()}")


# ── Úloha 3 ────────────────────────────────────────────────
# Vylepšený routing s GeneralistAgent jako zálohou

@dataclass
class SpecialistAgent:
    name: str
    specializace: list[str]
    system: str

    def zvladne(self, ukol: str) -> float:
        score = sum(1 for s in self.specializace if s.lower() in ukol.lower())
        return min(1.0, score / max(len(self.specializace), 1))


AGENTI = [
    SpecialistAgent("CodeAgent",     ["kód", "python", "oprav", "napíš funkci", "bug", "funkce"], "Jsi Python expert."),
    SpecialistAgent("ResearchAgent", ["co je", "vysvětli", "jak funguje", "proč"], "Jsi výzkumný asistent."),
    SpecialistAgent("MathAgent",     ["spočítej", "výpočet", "rovnice", "číslo"], "Jsi matematický asistent."),
    SpecialistAgent("WriterAgent",   ["napiš text", "dokumentace", "email", "shrnutí"], "Jsi pisatel."),
]

GENERALISTA = SpecialistAgent("GeneralistAgent", [], "Jsi všeobecný asistent.")


def routing(ukol: str, threshold: float = 0.3) -> SpecialistAgent:
    """
    Vybere nejlepšího agenta.
    Pokud žádný agent nemá skóre > threshold, vrátí GeneralistAgent.
    """
    scored = [(a.zvladne(ukol), a) for a in AGENTI]
    scored.sort(key=lambda x: x[0], reverse=True)
    best_score, best_agent = scored[0]
    if best_score <= threshold:
        return GENERALISTA
    return best_agent


print("\n── Úloha 3: routing s GeneralistAgent ──")
ukoly = [
    "Oprav bug v Python kódu",
    "Co je rekurzivní funkce?",
    "Spočítej výpočet plochy kruhu",
    "Napiš email kolegovi",
    "Přeložit tuto větu do angličtiny",   # nízké skóre → generalista
    "Pomoc s nastavením VPN",              # nízké skóre → generalista
]
for ukol in ukoly:
    agent = routing(ukol)
    print(f"  {repr(ukol)[:42]:<44} → {agent.name}")


# ── Úloha 4 (BONUS) ────────────────────────────────────────
# CodingAgent: čtení souboru → generování testů → spuštění

def read_file(path: str) -> str:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()[:500]
    except FileNotFoundError:
        return f"Soubor '{path}' neexistuje."
    except Exception as e:
        return f"Chyba: {e}"


class CodingAgent:
    """
    Agent který:
    a) Přečte Python soubor
    b) Vygeneruje unit testy (simulace)
    c) Spustí testy
    d) Vrátí výsledek
    """

    def _generuj_testy(self, kod: str, soubor: str) -> str:
        """Simulace generování unit testů pro kód."""
        # Najdi definice funkcí
        funkce = re.findall(r'def (\w+)\(', kod)
        if not funkce:
            return "# Žádné funkce k testování nenalezeny\n"

        modul = soubor.replace(".py", "").replace("/", ".")
        testy = f"# Automaticky vygenerované testy\n"
        testy += f"# Pro soubor: {soubor}\n\n"

        for fn in funkce[:3]:  # Max 3 funkce
            testy += f"def test_{fn}_zakladni():\n"
            testy += f"    # Otestuje základní chování funkce {fn}\n"
            testy += f"    # TODO: Doplň vstup a očekávaný výstup\n"
            testy += f"    pass  # assert {fn}(...) == ...\n\n"

        return testy

    def _spust_testy(self, testy_kod: str) -> str:
        """Spustí testy a vrátí výsledek."""
        # Jednoduchý sanity check – testy s pouze 'pass' by prošly
        zakazane = ["import os", "import sys", "__import__", "open("]
        for z in zakazane:
            if z in testy_kod:
                return f"ODMÍTNUTO: kód testů obsahuje '{z}'"
        try:
            result = subprocess.run(
                ["python3", "-c", testy_kod + "\nprint('Testy OK')"],
                capture_output=True, text=True, timeout=5,
            )
            return result.stdout or result.stderr or "(žádný výstup)"
        except subprocess.TimeoutExpired:
            return "TIMEOUT"

    def zpracuj(self, soubor: str) -> dict[str, str]:
        """Hlavní metoda: přečte soubor, vygeneruje a spustí testy."""
        # a) Přečti soubor
        kod = read_file(soubor)
        if kod.startswith("Soubor") or kod.startswith("Chyba"):
            return {"chyba": kod}

        # b) Generuj testy
        testy = self._generuj_testy(kod, soubor)

        # c) Spusť testy
        vysledek = self._spust_testy(testy)

        return {
            "soubor": soubor,
            "funkce_nalezeny": re.findall(r'def (\w+)\(', kod),
            "vygenerovane_testy": testy,
            "vysledek": vysledek,
        }


print("\n── Úloha 4 (BONUS): CodingAgent ──")
# Vytvoř dočasný testovací soubor
import tempfile, pathlib

test_kod = '''\
def secti(a, b):
    return a + b

def faktorial(n):
    if n <= 1:
        return 1
    return n * faktorial(n - 1)
'''
with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False, encoding="utf-8") as f:
    f.write(test_kod)
    tmp_path = f.name

coding_agent = CodingAgent()
result = coding_agent.zpracuj(tmp_path)
print(f"Soubor: {result['soubor']}")
print(f"Funkce: {result['funkce_nalezeny']}")
print(f"Vygenerované testy:\n{result['vygenerovane_testy']}")
print(f"Výsledek spuštění: {result['vysledek'].strip()}")

# Úklid
pathlib.Path(tmp_path).unlink(missing_ok=True)
