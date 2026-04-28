"""Řešení – Lekce 105: MCP – Model Context Protocol

Toto je vzorové řešení úloh z lekce 105.
"""

import json
import re
from pathlib import Path
from typing import Any


# ── Úloha 1 ────────────────────────────────────────────────
# MCP tool calculate(expression) – bezpečné vyhodnocení výrazu

def mcp_calculate(expression: str) -> dict:
    """
    MCP Tool: calculate
    Bezpečně vyhodnotí matematický výraz a vrátí výsledek jako JSON.
    Povoleny: čísla, +, -, *, /, (, ), ., **, // a základní math funkce.
    """
    # Whitelist povolených vzorů
    if not re.match(r'^[\d\s\+\-\*\/\(\)\.\,\%\*\*\/\/]+$', expression):
        return {
            "success": False,
            "error": f"Nepovolené znaky ve výrazu: {expression!r}",
            "result": None,
        }

    try:
        # eval je bezpečný protože vstup prošel whitelistem
        result = eval(expression)  # noqa: S307
        return {
            "success": True,
            "expression": expression,
            "result": result,
            "result_type": type(result).__name__,
        }
    except ZeroDivisionError:
        return {"success": False, "error": "Dělení nulou.", "result": None}
    except Exception as e:
        return {"success": False, "error": str(e), "result": None}


print("── Úloha 1: mcp_calculate() ──")
priklady = ["(3 + 5) * 2", "100 / 4", "2 ** 10", "10 % 3", "1 / 0", "import os"]
for vyr in priklady:
    r = mcp_calculate(vyr)
    if r["success"]:
        print(f"  {vyr!r:20} = {r['result']} ({r['result_type']})")
    else:
        print(f"  {vyr!r:20} → CHYBA: {r['error']}")


# ── Úloha 2 ────────────────────────────────────────────────
# Resource db://kurz/lekce/{cislo} – prvních 20 řádků ze souboru

BASE_DIR = Path("/home/ivand/projects/learning_python/interactive")


def nacti_lekci_resource(cislo: int) -> dict:
    """
    MCP Resource: db://kurz/lekce/{cislo}
    Vrátí obsah konkrétní lekce (prvních 20 řádků ze souboru).
    """
    uri = f"db://kurz/lekce/{cislo}"

    # Najdi soubor lekce
    soubory = list(BASE_DIR.glob(f"{cislo:02d}_*.py"))
    if not soubory:
        return {
            "uri": uri,
            "error": f"Lekce {cislo:02d} nebyla nalezena v {BASE_DIR}",
        }

    soubor = soubory[0]
    try:
        radky = soubor.read_text(encoding="utf-8").splitlines()[:20]
        return {
            "uri": uri,
            "mimeType": "text/x-python",
            "soubor": soubor.name,
            "text": "\n".join(radky),
            "celkem_radku_nacteno": len(radky),
        }
    except Exception as e:
        return {"uri": uri, "error": str(e)}


print("\n── Úloha 2: nacti_lekci_resource() ──")
for cislo in [1, 102, 999]:
    r = nacti_lekci_resource(cislo)
    if "error" in r:
        print(f"  Lekce {cislo:03d}: CHYBA – {r['error']}")
    else:
        prvni_radky = r["text"].split("\n")[:3]
        print(f"  Lekce {cislo:03d}: {r['soubor']} – první řádky:")
        for radek in prvni_radky:
            print(f"    {radek}")


# ── Úloha 3 ────────────────────────────────────────────────
# MCPResourceManager.refresh(uri) – invalidace cache a znovunačtení

class MCPResourceManager:
    """MCP resource manager s cachí a podporou refresh."""

    def __init__(self):
        self._resources: dict[str, dict] = {}
        self._cache: dict[str, str] = {}

    def registruj(
        self,
        uri: str,
        name: str,
        description: str,
        mime_type: str,
        loader,
    ) -> None:
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
        """Čte resource, využívá cache."""
        if uri not in self._resources:
            return {"error": f"Resource '{uri}' nenalezen."}

        # Cache hit
        if uri in self._cache:
            return {
                "uri": uri,
                "mimeType": self._resources[uri]["mimeType"],
                "text": self._cache[uri],
                "z_cache": True,
            }

        # Cache miss – načti a ulož
        resource = self._resources[uri]
        try:
            content = resource["loader"]()
            self._cache[uri] = content
            return {
                "uri": uri,
                "mimeType": resource["mimeType"],
                "text": content,
                "z_cache": False,
            }
        except Exception as e:
            return {"error": str(e)}

    def refresh(self, uri: str) -> dict:
        """
        Vymaže cache pro daný URI a znovu načte resource.
        Vhodné pro dynamická data která se mění.
        """
        if uri not in self._resources:
            return {"error": f"Resource '{uri}' nenalezen."}

        # Invalidace cache
        self._cache.pop(uri, None)

        # Znovunačtení
        result = self.read_resource(uri)
        result["refreshed"] = True
        return result


print("\n── Úloha 3: MCPResourceManager.refresh() ──")
_pocitadlo = {"n": 0}

def dynamicky_loader() -> str:
    _pocitadlo["n"] += 1
    return json.dumps({"verze": _pocitadlo["n"], "cas": "simulovano"})


rm = MCPResourceManager()
rm.registruj(
    uri="db://kurz/statistiky",
    name="Statistiky kurzu",
    description="Dynamické statistiky – mění se s každým voláním",
    mime_type="application/json",
    loader=dynamicky_loader,
)

# První čtení – cache miss
r1 = rm.read_resource("db://kurz/statistiky")
print(f"  1. čtení (z_cache={r1['z_cache']}): {r1['text']}")

# Druhé čtení – cache hit, stejná data
r2 = rm.read_resource("db://kurz/statistiky")
print(f"  2. čtení (z_cache={r2['z_cache']}): {r2['text']}")

# Refresh – invalidace + nové načtení
r3 = rm.refresh("db://kurz/statistiky")
print(f"  Po refresh (refreshed={r3['refreshed']}): {r3['text']}")

# Opět čtení – z nové cache
r4 = rm.read_resource("db://kurz/statistiky")
print(f"  Po refresh čtení (z_cache={r4['z_cache']}): {r4['text']}")

# Chybný URI
err = rm.refresh("db://neexistuje")
print(f"  Chybný URI: {err}")


# ── Úloha 4 (BONUS) – připomínka ───────────────────────────
print("\n── Úloha 4 (BONUS): Spuštění MCP serveru ──")
print("Nainstaluj: pip install mcp")
print("Spusť:      python3 105_mcp_server.py --server")
print("Testuj:     npx @modelcontextprotocol/inspector python3 105_mcp_server.py --server")
print()
print("Hotový MCP server s tools get_weather, search_docs, run_python, calculate")
print("je implementován v lekci 105_mcp_server.py (sekce ČÁST 4).")
