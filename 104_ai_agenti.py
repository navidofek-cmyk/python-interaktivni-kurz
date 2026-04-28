"""
LEKCE 104: Autonomní AI agenti
================================
Navazuje na lekci 74 (LLM API) a 103 (RAG).

Co je AI agent:
  LLM + nástroje (tools) + smyčka rozhodování.
  Agent sám rozhoduje KDY a JAKÝ nástroj použít.

Rozdíl od základního LLM volání:
  Základní: User → LLM → Odpověď  (jeden krok)
  Agent:    User → LLM → Akce → Výsledek → LLM → Akce → ... → Odpověď

ReAct pattern (Reason + Act):
  Thought: "Potřebuji zjistit počasí."
  Action:  get_weather(city="Praha")
  Obs:     "Praha: 18°C, slunečno"
  Thought: "Mám data, mohu odpovědět."
  Answer:  "V Praze je 18°C."

Spuštění: python3 104_ai_agenti.py
Nevyžaduje API klíč – celý ReAct loop je simulován.
"""

import os, json, re, time, textwrap, subprocess
from typing import Any, Callable
from dataclasses import dataclass, field

ANTHROPIC_KEY = os.getenv("ANTHROPIC_API_KEY", "")

# ══════════════════════════════════════════════════════════════════
# ČÁST 1: DEFINICE NÁSTROJŮ (TOOLS)
# ══════════════════════════════════════════════════════════════════

print("=" * 60)
print("ČÁST 1: Nástroje (Tools) – co agent umí dělat")
print("=" * 60)

@dataclass
class Tool:
    """Popis nástroje pro agenta."""
    name: str
    description: str
    parameters: dict[str, str]          # {jmeno: popis}
    func: Callable

    def to_schema(self) -> dict:
        """Formát pro Anthropic tool use API."""
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

# --- Implementace nástrojů ---

def get_weather(city: str) -> str:
    """Simuluje dotaz na počasí."""
    data = {
        "Praha": "18°C, slunečno, vlhkost 45%",
        "Brno":  "16°C, oblačno, vlhkost 60%",
        "Ostrava": "14°C, déšť, vlhkost 80%",
    }
    return data.get(city, f"Data pro '{city}' nedostupná.")

def search_web(query: str) -> str:
    """Simuluje webové vyhledávání."""
    results = {
        "python asyncio": "asyncio je knihovna pro asynchronní programování. Verze 3.4+.",
        "langchain rag": "LangChain RAG: RetrievalQA chain kombinuje retriever s LLM.",
        "mcp protocol": "MCP = Model Context Protocol. Standard pro nástroje AI modelů.",
    }
    q = query.lower()
    for k, v in results.items():
        if any(w in q for w in k.split()):
            return v
    return f"Výsledky pro '{query}': [simulovaná data nejsou k dispozici]"

def read_file(path: str) -> str:
    """Přečte soubor (skutečný)."""
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()[:500]  # max 500 znaků
    except FileNotFoundError:
        return f"Soubor '{path}' neexistuje."
    except Exception as e:
        return f"Chyba čtení: {e}"

def run_python(code: str) -> str:
    """Spustí Python kód v sandboxu a vrátí výstup."""
    # GUARDRAIL: Zakázané operace
    zakazane = ["import os", "import sys", "subprocess", "__import__",
                "open(", "exec(", "eval(", "shutil", "socket"]
    for z in zakazane:
        if z in code:
            return f"ODMÍTNUTO: Kód obsahuje zakázanou operaci '{z}'."
    try:
        result = subprocess.run(
            ["python3", "-c", code],
            capture_output=True, text=True, timeout=5
        )
        out = result.stdout or result.stderr
        return out[:300] if out else "(žádný výstup)"
    except subprocess.TimeoutExpired:
        return "TIMEOUT: Kód běžel déle než 5 sekund."
    except Exception as e:
        return f"Chyba spuštění: {e}"

def calculate(expression: str) -> str:
    """Bezpečný kalkulátor pro matematické výrazy."""
    try:
        # Povolíme pouze čísla, operátory a závorky
        if not re.match(r'^[\d\s\+\-\*\/\(\)\.\,\^]+$', expression):
            return "Neplatný výraz (povoleny jen čísla a operátory)."
        result = eval(expression)  # noqa: S307 – záměrně omezený vstup
        return str(result)
    except Exception as e:
        return f"Chyba výpočtu: {e}"

# Registr nástrojů
TOOLS: dict[str, Tool] = {
    "get_weather": Tool(
        name="get_weather",
        description="Zjistí aktuální počasí ve městě.",
        parameters={"city": "Název města česky"},
        func=get_weather,
    ),
    "search_web": Tool(
        name="search_web",
        description="Vyhledá informace na internetu.",
        parameters={"query": "Hledaný výraz v angličtině nebo češtině"},
        func=search_web,
    ),
    "read_file": Tool(
        name="read_file",
        description="Přečte obsah souboru ze systému.",
        parameters={"path": "Absolutní nebo relativní cesta k souboru"},
        func=read_file,
    ),
    "run_python": Tool(
        name="run_python",
        description="Spustí krátký Python kód a vrátí výstup.",
        parameters={"code": "Python kód k spuštění"},
        func=run_python,
    ),
    "calculate": Tool(
        name="calculate",
        description="Vypočítá matematický výraz.",
        parameters={"expression": "Matematický výraz, např. '(3+5)*2'"},
        func=calculate,
    ),
}

print("\nDostupné nástroje:")
for name, tool in TOOLS.items():
    print(f"  {name:<15} – {tool.description}")

# ══════════════════════════════════════════════════════════════════
# ČÁST 2: REACT LOOP – SIMULACE
# ══════════════════════════════════════════════════════════════════

print("\n" + "=" * 60)
print("ČÁST 2: ReAct Loop – Simulace bez API")
print("=" * 60)

@dataclass
class AgentKrok:
    thought: str
    action: str | None = None
    action_input: dict = field(default_factory=dict)
    observation: str | None = None
    final_answer: str | None = None

def simuluj_react_loop(ukol: str, kroky: list[AgentKrok]) -> None:
    """Přehraje simulovaný ReAct loop pro demonstraci."""
    print(f"\nÚkol: {ukol!r}")
    print("-" * 50)
    for i, krok in enumerate(kroky, 1):
        print(f"\n[Krok {i}]")
        print(f"  Thought: {krok.thought}")
        if krok.action:
            print(f"  Action:  {krok.action}({krok.action_input})")
            time.sleep(0.3)
            # Skutečně zavolej tool
            if krok.action in TOOLS:
                obs = TOOLS[krok.action].func(**krok.action_input)
            else:
                obs = krok.observation or "(simulovaná obs)"
            print(f"  Obs:     {obs}")
        if krok.final_answer:
            print(f"\n  ✓ Odpověď: {krok.final_answer}")
            break

# Simulace 1: Počasí + výpočet
simuluj_react_loop(
    ukol="Jaké je počasí v Praze a kolik je 37*42?",
    kroky=[
        AgentKrok(
            thought="Potřebuji zjistit počasí v Praze a spočítat výraz.",
            action="get_weather",
            action_input={"city": "Praha"},
        ),
        AgentKrok(
            thought="Mám počasí. Teď spočítám výraz.",
            action="calculate",
            action_input={"expression": "37*42"},
        ),
        AgentKrok(
            thought="Mám obě odpovědi. Mohu odpovědět.",
            final_answer="V Praze je 18°C a slunečno. 37×42 = 1554.",
        ),
    ],
)

# Simulace 2: Spuštění kódu
simuluj_react_loop(
    ukol="Spočítej součet prvočísel do 50 v Pythonu.",
    kroky=[
        AgentKrok(
            thought="Napíšu Python kód pro výpočet prvočísel.",
            action="run_python",
            action_input={"code": "primes=[x for x in range(2,51) if all(x%d!=0 for d in range(2,x))]\nprint(sum(primes))"},
        ),
        AgentKrok(
            thought="Mám výsledek z kódu. Odpovídám.",
            final_answer="Součet prvočísel do 50 je 328.",
        ),
    ],
)

# ══════════════════════════════════════════════════════════════════
# ČÁST 3: REÁLNÝ AGENT S ANTHROPIC API (tool use)
# ══════════════════════════════════════════════════════════════════

print("\n" + "=" * 60)
print("ČÁST 3: Reálný agent s Anthropic API")
print("=" * 60)

def spust_agenta(ukol: str, max_kroky: int = 5) -> str:
    """
    Skutečný ReAct agent pomocí Anthropic tool use.
    Vyžaduje ANTHROPIC_API_KEY.
    """
    if not ANTHROPIC_KEY:
        return None

    import anthropic
    client = anthropic.Anthropic()

    messages = [{"role": "user", "content": ukol}]
    tool_schemas = [t.to_schema() for t in TOOLS.values()]
    system = (
        "Jsi pomocný asistent s přístupem k nástrojům. "
        "Používej nástroje k získání informací. "
        "Vždy odpověz česky."
    )

    for krok in range(max_kroky):
        print(f"\n  [Krok {krok+1}/{max_kroky}]")
        response = client.messages.create(
            model="claude-opus-4-7",
            max_tokens=1024,
            system=system,
            tools=tool_schemas,
            messages=messages,
        )

        # Zpracuj odpověď
        tool_uses = [b for b in response.content if b.type == "tool_use"]
        text_blocks = [b for b in response.content if b.type == "text"]

        if text_blocks:
            print(f"  Thought: {text_blocks[0].text[:100]}...")

        if response.stop_reason == "end_turn" or not tool_uses:
            final = " ".join(b.text for b in text_blocks)
            return final

        # Zavolej nástroje
        tool_results = []
        for tu in tool_uses:
            print(f"  Action: {tu.name}({tu.input})")
            if tu.name in TOOLS:
                result = TOOLS[tu.name].func(**tu.input)
            else:
                result = f"Nástroj '{tu.name}' neexistuje."
            print(f"  Obs: {result}")
            tool_results.append({
                "type": "tool_result",
                "tool_use_id": tu.id,
                "content": result,
            })

        # Přidej do historie
        messages.append({"role": "assistant", "content": response.content})
        messages.append({"role": "user", "content": tool_results})

    return "Agent nedokončil úkol v povoleném počtu kroků."

if ANTHROPIC_KEY:
    print("\nSpouštím reálného agenta...")
    result = spust_agenta("Zjisti počasí v Brně a spočítej 123 * 456.")
    print(f"\nFinální odpověď: {result}")
else:
    print("\nANTHROPIC_API_KEY není nastaven.")
    print("Co by se stalo při spuštění agenta:")
    print("  1. Client pošle úkol + seznam nástrojů modelu")
    print("  2. Model odpoví s tool_use bloky (které nástroje zavolat)")
    print("  3. Kód zavolá nástroje a výsledky vrátí modelu")
    print("  4. Model pokračuje nebo dá finální odpověď")
    print("  → Loop se opakuje max_kroky-krát")

# ══════════════════════════════════════════════════════════════════
# ČÁST 4: PAMĚŤ AGENTA
# ══════════════════════════════════════════════════════════════════

print("\n" + "=" * 60)
print("ČÁST 4: Paměť agenta")
print("=" * 60)

print("""
Typy paměti:

  SHORT-TERM (kontext okno)
  ─────────────────────────
  messages = [{"role": "user", ...}, {"role": "assistant", ...}, ...]
  → Celá konverzace je v API requestu
  → Limit: 200k tokenů (Claude), 128k (GPT-4)
  → Po resetování kontext zmizel

  LONG-TERM (vector store)
  ────────────────────────
  → Embeddingy minulých konverzací v ChromaDB / Pinecone
  → Při novém dotazu: retrieval relevantních vzpomínek
  → "Pamatuji si, že preferuješ krátké odpovědi"

  EPISODICKÁ (structured)
  ────────────────────────
  → JSON/SQLite databáze faktů o uživateli
  → {"jazyk": "Python", "uroven": "pokrocily", "projekty": [...]}
""")

# Ukázka short-term paměti
class AgentSPameti:
    """Agent s konverzační pamětí."""

    def __init__(self, max_zprav: int = 20):
        self.zpravy: list[dict] = []
        self.max_zprav = max_zprav
        self.fakty: dict[str, Any] = {}  # long-term simulace

    def zapamatuj_si(self, klic: str, hodnota: Any) -> None:
        """Uloží fakt do dlouhodobé paměti."""
        self.fakty[klic] = hodnota
        print(f"  [Paměť] Uloženo: {klic} = {hodnota!r}")

    def vzpomen_si(self, klic: str) -> Any:
        """Získá fakt z dlouhodobé paměti."""
        return self.fakty.get(klic)

    def pridej_zpravu(self, role: str, obsah: str) -> None:
        self.zpravy.append({"role": role, "content": obsah})
        # Sliding window – zachovej jen posledních N zpráv
        if len(self.zpravy) > self.max_zprav:
            self.zpravy = self.zpravy[-self.max_zprav:]

    def system_prompt(self) -> str:
        fakty_str = "\n".join(f"- {k}: {v}" for k, v in self.fakty.items())
        return f"Jsi pomocný asistent. Fakta o uživateli:\n{fakty_str}"

agent = AgentSPameti()
agent.zapamatuj_si("jmeno", "Ivane")
agent.zapamatuj_si("uroven", "pokrocily Python programátor")
agent.zapamatuj_si("preferovany_jazyk", "Python")
agent.pridej_zpravu("user", "Ahoj!")
agent.pridej_zpravu("assistant", "Ahoj Ivane! Jak mohu pomoci?")
print(f"\nSystem prompt (s pamětí):\n{agent.system_prompt()}")
print(f"Počet zpráv v kontextu: {len(agent.zpravy)}")

# ══════════════════════════════════════════════════════════════════
# ČÁST 5: MULTI-AGENT SYSTÉM
# ══════════════════════════════════════════════════════════════════

print("\n" + "=" * 60)
print("ČÁST 5: Multi-agent systém – orchestrátor + specialisti")
print("=" * 60)

print("""
Architektura:

  Uživatel
     ↓
  Orchestrátor (router)
  ├── Code Agent    → píše, opravuje, testuje kód
  ├── Research Agent → vyhledává informace
  ├── Writer Agent  → píše dokumentaci, emaily
  └── Math Agent    → počítá, řeší rovnice

Orchestrátor:
  1. Pochopí úkol
  2. Rozhodne který specialista ho zvládne
  3. Deleguje a sbírá výsledky
  4. Kombinuje finální odpověď
""")

@dataclass
class SpecialistAgent:
    name: str
    specializace: list[str]
    system: str

    def zvladne(self, ukol: str) -> float:
        """Vrátí skóre 0-1 jak dobře zvládne úkol."""
        score = sum(1 for s in self.specializace if s.lower() in ukol.lower())
        return min(1.0, score / max(len(self.specializace), 1))

agenti = [
    SpecialistAgent("CodeAgent",     ["kód", "python", "oprav", "napíš funkci", "bug"], "Jsi expert na Python kód."),
    SpecialistAgent("ResearchAgent", ["co je", "vysvětli", "jak funguje", "proč"], "Jsi výzkumný asistent."),
    SpecialistAgent("MathAgent",     ["spočítej", "výpočet", "rovnice", "číslo"], "Jsi matematický asistent."),
    SpecialistAgent("WriterAgent",   ["napiš text", "dokumentace", "email", "shrnutí"], "Jsi pisatel."),
]

def routing(ukol: str) -> SpecialistAgent:
    """Vybere nejlepšího agenta pro úkol."""
    scored = [(a.zvladne(ukol), a) for a in agenti]
    scored.sort(key=lambda x: x[0], reverse=True)
    return scored[0][1]

testovaci_ukoly = [
    "Oprav bug v tomto Python kódu",
    "Co je rekurzivní funkce?",
    "Spočítej výpočet plochy kruhu r=5",
    "Napiš email kolegovi o schůzce",
]

print("Routing ukázka:")
for ukol in testovaci_ukoly:
    agent = routing(ukol)
    print(f"  {repr(ukol)[:40]:<42} → {agent.name}")

# ══════════════════════════════════════════════════════════════════
# ČÁST 6: GUARDRAILS
# ══════════════════════════════════════════════════════════════════

print("\n" + "=" * 60)
print("ČÁST 6: Guardrails – jak omezit agenta")
print("=" * 60)

class GuardrailedAgent:
    """Agent s bezpečnostními omezeními."""

    ZAKAZANE_AKCE = {"delete_file", "send_email", "deploy_production", "drop_database"}
    MAX_KROKY = 10
    MAX_TOOL_CALLS_ZA_MINUTU = 20

    def __init__(self):
        self._kroky = 0
        self._tool_calls: list[float] = []

    def over_akci(self, nazev_nastroje: str, parametry: dict) -> tuple[bool, str]:
        """Ověří, zda je akce povolena."""
        # 1. Blacklist nástrojů
        if nazev_nastroje in self.ZAKAZANE_AKCE:
            return False, f"Nástroj '{nazev_nastroje}' je zakázán."

        # 2. Kontrola počtu kroků
        if self._kroky >= self.MAX_KROKY:
            return False, "Překročen maximální počet kroků."

        # 3. Rate limiting
        now = time.time()
        self._tool_calls = [t for t in self._tool_calls if now - t < 60]
        if len(self._tool_calls) >= self.MAX_TOOL_CALLS_ZA_MINUTU:
            return False, "Překročen rate limit (20 volání/minuta)."

        # 4. Kontrola parametrů (whitelist cest)
        if nazev_nastroje == "read_file":
            povolene_cesty = ["/home/ivand/projects", "/tmp"]
            cesta = parametry.get("path", "")
            if not any(cesta.startswith(p) for p in povolene_cesty):
                return False, f"Přístup k '{cesta}' není povolen."

        self._kroky += 1
        self._tool_calls.append(now)
        return True, "OK"

ga = GuardrailedAgent()
testy = [
    ("get_weather", {"city": "Praha"}),
    ("delete_file", {"path": "/etc/passwd"}),
    ("read_file", {"path": "/home/ivand/projects/learning_python/test.py"}),
    ("read_file", {"path": "/etc/shadow"}),
    ("calculate", {"expression": "2+2"}),
]

print("\nKontroly guardrails:")
for tool, params in testy:
    ok, zprava = ga.over_akci(tool, params)
    status = "✓ POVOLENO" if ok else "✗ ODMÍTNUTO"
    print(f"  {status} | {tool}({params}) → {zprava}")

# SHRNUTÍ
print("\n" + "=" * 60)
print("SHRNUTÍ")
print("=" * 60)
print("""
  ReAct:       Reason → Act → Observe → Reason → ...
  Tools:       Nástroje = Python funkce s JSON schématem
  Paměť:       Short-term (kontext) + Long-term (vector DB)
  Multi-agent: Orchestrátor deleguje na specializované agenty
  Guardrails:  Blacklist, rate limit, whitelist cest, max kroků
""")

# ══════════════════════════════════════════════════════════════════
# TVOJE ÚLOHA
# ══════════════════════════════════════════════════════════════════
print("""
╔══════════════════════════════════════════════════════════════╗
║  TVOJE ÚLOHA                                                 ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  1. Přidej nástroj `write_file(path, content)` do TOOLS.    ║
║     Guardrail: povoluj zápis POUZE do /tmp/.                 ║
║                                                              ║
║  2. Implementuj `AgentSPameti.zapomen(klic)` a              ║
║     `shrnuti_pameti()` která vrátí seznam uložených faktů.  ║
║                                                              ║
║  3. Vylepši routing funkci – pokud žádný agent nemá skóre   ║
║     > 0.3, vrať speciálního "GeneralistAgent" který zkusí   ║
║     vše zvládnout.                                           ║
║                                                              ║
║  4. BONUS: Implementuj `CodingAgent` který:                  ║
║     a) Přečte Python soubor (read_file)                      ║
║     b) Vygeneruje unit testy (simulace nebo LLM)             ║
║     c) Spustí testy (run_python)                             ║
║     d) Vrátí výsledek                                        ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
""")
