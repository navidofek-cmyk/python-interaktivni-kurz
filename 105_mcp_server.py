"""
LEKCE 105: MCP – Model Context Protocol
=========================================
pip install mcp  (volitelné pro spuštění serveru)

Co je MCP:
  Otevřený standard (Anthropic, 2024) pro připojení AI modelů
  k externím nástrojům, datům a službám.

  Proč MCP a ne vlastní tool use:
  → Standardizované rozhraní – jeden server, mnoho klientů
  → Claude Desktop, Claude Code, IDE pluginy – všechny podporují MCP
  → Komunita: stovky hotových MCP serverů

Typy MCP primitiv:
  Tools     – funkce které model může zavolat (get_weather, run_sql)
  Resources – data k přečtení (soubor, DB tabulka, API endpoint)
  Prompts   – předdefinované šablony pro common use-cases

Architektura:
  Host (Claude Desktop/Code) ←→ MCP Client ←→ MCP Server (tvůj kód)

Spuštění lekce: python3 105_mcp_server.py
Spuštění serveru: python3 105_mcp_server.py --server
"""

import os, json, sys, math, datetime, textwrap
from pathlib import Path

ANTHROPIC_KEY = os.getenv("ANTHROPIC_API_KEY", "")

# ══════════════════════════════════════════════════════════════════
# ČÁST 1: MCP ZÁKLADY – TEORIE
# ══════════════════════════════════════════════════════════════════

print("=" * 60)
print("ČÁST 1: MCP – Model Context Protocol, teorie")
print("=" * 60)

print("""
MCP komunikační flow:
  1. Server se spustí (stdio transport)
  2. Host (Claude) se připojí a pošle initialize request
  3. Server vrátí capabilities (co umí)
  4. Claude volá tools/resources podle potřeby

Transport:
  stdio   – stdin/stdout (lokální server, nejjednodušší)
  HTTP    – síťový přístup, více klientů
  SSE     – Server-Sent Events (streaming)

Konfigurace v Claude Desktop (claude_desktop_config.json):
  {
    "mcpServers": {
      "muj-server": {
        "command": "python3",
        "args": ["/cesta/k/105_mcp_server.py", "--server"]
      }
    }
  }
""")

# ══════════════════════════════════════════════════════════════════
# ČÁST 2: DEFINICE TOOLS PRO MCP SERVER
# ══════════════════════════════════════════════════════════════════

print("=" * 60)
print("ČÁST 2: Implementace MCP Tools")
print("=" * 60)

# Tyto funkce budou registrovány jako MCP tools
# Simulujeme je i bez MCP knihovny

def mcp_get_weather(city: str) -> dict:
    """
    MCP Tool: get_weather
    Vrátí aktuální počasí pro dané město.
    """
    pocasi_data = {
        "Praha":   {"teplota": 18, "popis": "slunečno", "vlhkost": 45, "vir": "Severní"},
        "Brno":    {"teplota": 16, "popis": "oblačno",  "vlhkost": 60, "vir": "Jihozápadní"},
        "Ostrava": {"teplota": 14, "popis": "déšť",     "vlhkost": 80, "vir": "Východní"},
        "Plzeň":   {"teplota": 17, "popis": "mlha",     "vlhkost": 72, "vir": "Západní"},
    }
    if city not in pocasi_data:
        return {"error": f"Město '{city}' nenalezeno. Dostupná: {list(pocasi_data.keys())}"}

    data = pocasi_data[city]
    return {
        "misto": city,
        "teplota_celsius": data["teplota"],
        "popis": data["popis"],
        "vlhkost_procent": data["vlhkost"],
        "vir": data["vir"],
        "aktualizovano": datetime.datetime.now().isoformat(),
    }

def mcp_search_docs(query: str, max_results: int = 3) -> dict:
    """
    MCP Tool: search_docs
    Vyhledá v dokumentaci kurzu relevantní lekce.
    """
    # Simulace indexu dokumentace
    lekce_index = {
        "třídy": [22, 23, 24, 29],
        "class": [22, 23, 24, 29],
        "async": [25, 43, 59],
        "databáze": [40, 58, 63],
        "sqlite": [40],
        "sql": [40, 58],
        "api": [41, 74, 102, 103],
        "llm": [74, 102, 103, 104],
        "numpy": [53],
        "pandas": [54],
        "test": [39, 87, 107],
        "web": [34, 50, 56, 76],
        "decorátor": [26],
        "decorator": [26],
        "rag": [103],
        "agent": [104],
        "mcp": [105],
        "prompt": [102],
    }

    nalezene = set()
    query_slova = query.lower().split()
    for slovo in query_slova:
        for klic, lekce_list in lekce_index.items():
            if slovo in klic or klic in slovo:
                nalezene.update(lekce_list)

    serazene = sorted(nalezene)[:max_results]

    if not serazene:
        return {"query": query, "results": [], "total": 0}

    vysledky = []
    popisy = {
        22: "Lekce 22: Třídy – základy OOP",
        23: "Lekce 23: Dědičnost a polymorfismus",
        24: "Lekce 24: Magic methods (__str__, __repr__, ...)",
        25: "Lekce 25: Async/await – asyncio",
        26: "Lekce 26: Dekorátory a kontextové manažery",
        29: "Lekce 29: Dataclasses",
        39: "Lekce 39: Testování – pytest",
        40: "Lekce 40: Databáze SQLite",
        41: "Lekce 41: Síť a REST API",
        43: "Lekce 43: Concurrency – threading, multiprocessing",
        53: "Lekce 53: NumPy – pole a maticové operace",
        54: "Lekce 54: Pandas – datové analýzy",
        56: "Lekce 56: FastAPI – webový framework",
        58: "Lekce 58: SQLAlchemy – ORM",
        59: "Lekce 59: Celery – fronta úloh",
        63: "Lekce 63: Redis – in-memory databáze",
        74: "Lekce 74: LLM API – Claude a OpenAI",
        76: "Lekce 76: Playwright – testování webu",
        87: "Lekce 87: Hypothesis – property-based testing",
        102: "Lekce 102: Prompt Engineering",
        103: "Lekce 103: RAG pipeline",
        104: "Lekce 104: AI agenti",
        105: "Lekce 105: MCP protokol",
        107: "Lekce 107: Evaluace LLM",
    }

    for c in serazene:
        vysledky.append({
            "cislo": c,
            "nazev": popisy.get(c, f"Lekce {c}"),
            "soubor": f"{c:02d}_*.py",
        })

    return {"query": query, "results": vysledky, "total": len(nalezene)}

def mcp_run_python(code: str) -> dict:
    """
    MCP Tool: run_python
    Bezpečně spustí Python kód a vrátí výstup.
    """
    import subprocess, re

    # Guardrails
    zakazane_vzory = [
        r'import\s+os',
        r'import\s+sys',
        r'import\s+subprocess',
        r'__import__',
        r'open\s*\(',
        r'exec\s*\(',
        r'shutil',
        r'socket',
        r'requests',
    ]
    for vzor in zakazane_vzory:
        if re.search(vzor, code):
            return {
                "success": False,
                "error": f"Zakázaný vzor v kódu: {vzor}",
                "output": None,
            }

    try:
        result = subprocess.run(
            ["python3", "-c", code],
            capture_output=True, text=True, timeout=5
        )
        return {
            "success": result.returncode == 0,
            "output": result.stdout[:500] if result.stdout else None,
            "error": result.stderr[:200] if result.stderr else None,
            "returncode": result.returncode,
        }
    except subprocess.TimeoutExpired:
        return {"success": False, "error": "Timeout (5s)", "output": None}

def mcp_list_files(directory: str = ".") -> dict:
    """
    MCP Tool: list_files
    Vypíše soubory v adresáři.
    """
    try:
        p = Path(directory).resolve()
        # Bezpečnostní omezení – pouze povolené adresáře
        povolene = [Path("/home/ivand/projects"), Path("/tmp")]
        if not any(str(p).startswith(str(povol)) for povol in povolene):
            return {"error": f"Přístup k '{p}' není povolen."}

        soubory = [
            {
                "jmeno": f.name,
                "typ": "soubor" if f.is_file() else "adresar",
                "velikost": f.stat().st_size if f.is_file() else None,
            }
            for f in sorted(p.iterdir())[:20]
        ]
        return {"adresar": str(p), "soubory": soubory, "celkem": len(soubory)}
    except Exception as e:
        return {"error": str(e)}

# Demonstrace tools
print("\n--- Ukázka MCP Tools ---")

print("\nmcp_get_weather('Praha'):")
result = mcp_get_weather("Praha")
print(json.dumps(result, ensure_ascii=False, indent=2))

print("\nmcp_search_docs('async api'):")
result = mcp_search_docs("async api")
print(json.dumps(result, ensure_ascii=False, indent=2))

print("\nmcp_run_python('print(sum(range(10)))'):")
result = mcp_run_python("print(sum(range(10)))")
print(json.dumps(result, ensure_ascii=False, indent=2))

print("\nmcp_run_python('import os; print(os.getcwd())')  # zakázáno:")
result = mcp_run_python("import os; print(os.getcwd())")
print(json.dumps(result, ensure_ascii=False, indent=2))

# ══════════════════════════════════════════════════════════════════
# ČÁST 3: MCP RESOURCES
# ══════════════════════════════════════════════════════════════════

print("\n" + "=" * 60)
print("ČÁST 3: MCP Resources – data jako kontext")
print("=" * 60)

print("""
Resources jsou read-only data která model může přečíst.
Na rozdíl od Tools (akce), Resources jsou jako "soubory ke čtení".

Příklady resources:
  file:///home/user/projekt/README.md
  db://localhost/users/schema
  api://weather.example.com/current

V MCP protokolu:
  list_resources()    → vrátí seznam dostupných resources
  read_resource(uri)  → vrátí obsah resource
""")

# Simulace resource systému
class MCPResourceManager:
    """Simulace MCP resource manageru."""

    def __init__(self):
        self._resources: dict[str, dict] = {}

    def registruj(self, uri: str, name: str, description: str, mime_type: str, loader) -> None:
        self._resources[uri] = {
            "uri": uri,
            "name": name,
            "description": description,
            "mimeType": mime_type,
            "loader": loader,
        }

    def list_resources(self) -> list[dict]:
        return [
            {k: v for k, v in r.items() if k != "loader"}
            for r in self._resources.values()
        ]

    def read_resource(self, uri: str) -> dict:
        if uri not in self._resources:
            return {"error": f"Resource '{uri}' nenalezen."}
        resource = self._resources[uri]
        try:
            content = resource["loader"]()
            return {
                "uri": uri,
                "mimeType": resource["mimeType"],
                "text": content,
            }
        except Exception as e:
            return {"error": str(e)}

rm = MCPResourceManager()

# Registrace resources
rm.registruj(
    uri="file:///kurz/lekce_seznam.json",
    name="Seznam lekcí kurzu",
    description="Kompletní seznam všech lekcí Python kurzu",
    mime_type="application/json",
    loader=lambda: json.dumps([
        {"cislo": i, "soubor": f"{i:02d}_lekce.py"}
        for i in [1, 2, 22, 25, 40, 53, 74, 102, 103, 104, 105]
    ], ensure_ascii=False),
)

rm.registruj(
    uri="file:///kurz/README.md",
    name="README kurzu",
    description="Úvodní dokumentace Python kurzu",
    mime_type="text/markdown",
    loader=lambda: "# Python kurz\n\nInteraktivní Python lekce pro všechny úrovně.\n\n## Jak začít\n1. Spusť `python3 01_ahoj_svete.py`",
)

rm.registruj(
    uri="db://kurz/statistiky",
    name="Statistiky kurzu",
    description="Počet lekcí, témat a cvičení",
    mime_type="application/json",
    loader=lambda: json.dumps({
        "celkem_lekcí": 108,
        "témata": ["základy", "OOP", "async", "databáze", "web", "AI"],
        "cvičení_na_lekci": "3-4",
    }, ensure_ascii=False),
)

print("Dostupné resources:")
for r in rm.list_resources():
    print(f"  {r['uri']}")
    print(f"    → {r['description']}")

print("\nČtení resource:")
data = rm.read_resource("db://kurz/statistiky")
print(f"URI: {data['uri']}")
print(f"Content: {data['text']}")

# ══════════════════════════════════════════════════════════════════
# ČÁST 4: MCP SERVER – SKUTEČNÝ KÓD
# ══════════════════════════════════════════════════════════════════

print("\n" + "=" * 60)
print("ČÁST 4: Skutečný MCP server (pip install mcp)")
print("=" * 60)

mcp_server_code = '''
# Spusť jako: python3 105_mcp_server.py --server
# Přidej do claude_desktop_config.json

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types
import asyncio, json, datetime

app = Server("python-kurz-server")

@app.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="get_weather",
            description="Zjistí počasí ve městě",
            inputSchema={
                "type": "object",
                "properties": {"city": {"type": "string", "description": "Název města"}},
                "required": ["city"],
            },
        ),
        types.Tool(
            name="search_docs",
            description="Vyhledá v dokumentaci kurzu",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Hledaný výraz"},
                    "max_results": {"type": "integer", "default": 3},
                },
                "required": ["query"],
            },
        ),
        types.Tool(
            name="run_python",
            description="Spustí Python kód v sandboxu",
            inputSchema={
                "type": "object",
                "properties": {"code": {"type": "string", "description": "Python kód"}},
                "required": ["code"],
            },
        ),
    ]

@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    if name == "get_weather":
        result = mcp_get_weather(arguments["city"])
    elif name == "search_docs":
        result = mcp_search_docs(arguments["query"], arguments.get("max_results", 3))
    elif name == "run_python":
        result = mcp_run_python(arguments["code"])
    else:
        result = {"error": f"Neznámý tool: {name}"}

    return [types.TextContent(type="text", text=json.dumps(result, ensure_ascii=False))]

@app.list_resources()
async def list_resources() -> list[types.Resource]:
    return [
        types.Resource(
            uri="file:///kurz/README.md",
            name="README kurzu",
            mimeType="text/markdown",
        )
    ]

@app.read_resource()
async def read_resource(uri: str) -> str:
    return "# Python kurz\\n\\nInteraktivní Python lekce."

if __name__ == "__main__":
    asyncio.run(stdio_server(app))
'''

print("\nKód MCP serveru (vyžaduje: pip install mcp):")
print(mcp_server_code)

# Pokus o skutečné spuštění pokud je --server flag
if "--server" in sys.argv:
    print("\nSpouštím MCP server...")
    try:
        from mcp.server import Server
        from mcp.server.stdio import stdio_server
        from mcp import types
        import asyncio

        app = Server("python-kurz-server")

        @app.list_tools()
        async def list_tools_handler():
            return [
                types.Tool(
                    name="get_weather",
                    description="Zjistí počasí ve městě",
                    inputSchema={
                        "type": "object",
                        "properties": {"city": {"type": "string"}},
                        "required": ["city"],
                    },
                ),
                types.Tool(
                    name="search_docs",
                    description="Vyhledá v dokumentaci kurzu",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "query": {"type": "string"},
                            "max_results": {"type": "integer", "default": 3},
                        },
                        "required": ["query"],
                    },
                ),
                types.Tool(
                    name="run_python",
                    description="Spustí Python kód v sandboxu",
                    inputSchema={
                        "type": "object",
                        "properties": {"code": {"type": "string"}},
                        "required": ["code"],
                    },
                ),
            ]

        @app.call_tool()
        async def call_tool_handler(name: str, arguments: dict):
            if name == "get_weather":
                result = mcp_get_weather(arguments["city"])
            elif name == "search_docs":
                result = mcp_search_docs(arguments["query"], arguments.get("max_results", 3))
            elif name == "run_python":
                result = mcp_run_python(arguments["code"])
            else:
                result = {"error": f"Neznámý tool: {name}"}
            return [types.TextContent(type="text", text=json.dumps(result, ensure_ascii=False))]

        asyncio.run(stdio_server(app))

    except ImportError:
        print("MCP knihovna není nainstalována. Spusť: pip install mcp")
        sys.exit(1)
    sys.exit(0)

# ══════════════════════════════════════════════════════════════════
# ČÁST 5: KONFIGURACE A TESTOVÁNÍ
# ══════════════════════════════════════════════════════════════════

print("\n" + "=" * 60)
print("ČÁST 5: Konfigurace Claude Desktop / Claude Code")
print("=" * 60)

config_path_desktop = Path.home() / ".config" / "Claude" / "claude_desktop_config.json"
config_path_code = Path.cwd() / ".claude" / "settings.json"

print(f"\nclaude_desktop_config.json: {config_path_desktop}")
config_priklad = {
    "mcpServers": {
        "python-kurz": {
            "command": "python3",
            "args": [str(Path.cwd() / "105_mcp_server.py"), "--server"],
            "env": {}
        }
    }
}
print(json.dumps(config_priklad, indent=2))

print(f"\nPro Claude Code (settings.json): {config_path_code}")
print("Přidej do .claude/settings.json:")
print(json.dumps({
    "mcpServers": {
        "python-kurz": {
            "command": "python3",
            "args": ["105_mcp_server.py", "--server"]
        }
    }
}, indent=2))

print("\n--- Testování bez Claude ---")
print("Můžeš server otestovat přes stdin/stdout protokol.")
print("Nebo použij MCP Inspector: npx @modelcontextprotocol/inspector python3 105_mcp_server.py --server")

# SHRNUTÍ
print("\n" + "=" * 60)
print("SHRNUTÍ")
print("=" * 60)
print("""
  MCP primitiva:
    Tools     – akce (get_weather, run_python)
    Resources – read-only data (soubory, DB)
    Prompts   – šablony (v pokročilých use-cases)

  Transport:
    stdio → lokální server (nejjednodušší)
    HTTP  → vzdálený server

  Spuštění: python3 105_mcp_server.py --server
  Konfigurace: claude_desktop_config.json nebo .claude/settings.json
""")

# ══════════════════════════════════════════════════════════════════
# TVOJE ÚLOHA
# ══════════════════════════════════════════════════════════════════
print("""
╔══════════════════════════════════════════════════════════════╗
║  TVOJE ÚLOHA                                                 ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  1. Přidej MCP tool `calculate(expression)` který bezpečně  ║
║     vyhodnotí matematický výraz a vrátí výsledek jako JSON. ║
║                                                              ║
║  2. Přidej resource `db://kurz/lekce/{cislo}` který vrátí   ║
║     obsah konkrétní lekce (prvních 20 řádků ze souboru).   ║
║                                                              ║
║  3. Přidej do MCPResourceManager metodu `refresh(uri)` která ║
║     vymaže cache a znovu načte resource (pro dynamická data).║
║                                                              ║
║  4. BONUS: Nainstaluj `pip install mcp` a spusť server:      ║
║     python3 105_mcp_server.py --server                      ║
║     Testuj přes MCP Inspector nebo nastav v Claude Desktop. ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
""")
