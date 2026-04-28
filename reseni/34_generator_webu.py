"""Řešení – Lekce 34: Generátor statického webu"""

# Lekce 34 sama o sobě JE generátorem webu – spustí se a vytvoří web/.
# Úlohy rozšiřují už existující funkce v originálním souboru.
# Toto řešení demonstruje klíčové koncepty a přidané funkce.

import ast
import html
import json
import re
import unicodedata
from pathlib import Path


# 1. Navigační tlačítka ← předchozí / → další
# (V originální lekci jsou již implementovány – toto řešení to demonstruje)

def ukazka_navigace(lekce: list[dict], index: int) -> dict:
    """Vrátí prev/next metadata pro danou lekci."""
    prev_l = lekce[index - 1] if index > 0 else None
    next_l = lekce[index + 1] if index < len(lekce) - 1 else None

    prev_html = (
        f'<a href="{prev_l["slug"]}.html">← {html.escape(prev_l["titul"])}</a>'
        if prev_l else ""
    )
    next_html = (
        f'<a href="{next_l["slug"]}.html">{html.escape(next_l["titul"])} →</a>'
        if next_l else ""
    )
    return {"prev": prev_html, "next": next_html}


# 2. Tmavý/světlý přepínač – JS kód (CSS proměnné přepínáme třídou na html)
# (Originál ho již obsahuje – ukážeme zkrácenou verzi logiky)

TOGGLE_JS = """
function toggleTheme() {
  const isLight = document.documentElement.classList.toggle("light");
  localStorage.setItem("theme", isLight ? "light" : "dark");
}
// Obnovení při načtení
if (localStorage.getItem("theme") === "light")
  document.documentElement.classList.add("light");
"""

print("=== Theme toggle JS ===")
print(TOGGLE_JS.strip())


# 3. Vyhledávací index – search.json + JS vyhledávání na straně klienta
# Vytvoříme search.json ze všech lekcí v adresáři

def ascii_stem(stem: str) -> str:
    norm = unicodedata.normalize("NFD", stem)
    return "".join(c for c in norm if unicodedata.category(c) != "Mn")


def nacti_lekci_meta(cesta: Path) -> dict | None:
    """Načte pouze metadata lekce (bez celého kódu) pro rychlý index."""
    try:
        kod = cesta.read_text(encoding="utf-8")
        strom = ast.parse(kod)
        docstring = ast.get_docstring(strom) or ""
    except (SyntaxError, OSError):
        return None

    radky = docstring.splitlines()
    titul = radky[0].strip() if radky else cesta.stem
    m = re.match(r"(\d+)_", cesta.stem)
    cislo = int(m.group(1)) if m else 0

    # Extrahuj klíčová slova z docstringu (jednoduchý přístup)
    klic_slova = re.findall(r"[A-Za-zÁ-ž]{4,}", docstring.lower())
    klic_slova = list(set(klic_slova))[:20]  # max 20

    return {
        "cislo": cislo,
        "titul": titul,
        "slug": ascii_stem(cesta.stem),
        "klic_slova": klic_slova,
    }


def generuj_search_json(adresar: Path, vystup: Path) -> None:
    """Vygeneruje search.json pro klientské vyhledávání."""
    soubory = sorted(adresar.glob("[0-9][0-9]_*.py"))
    lekce = []
    for s in soubory:
        meta = nacti_lekci_meta(s)
        if meta:
            lekce.append(meta)

    vystup.parent.mkdir(parents=True, exist_ok=True)
    with open(vystup, "w", encoding="utf-8") as f:
        json.dump(lekce, f, ensure_ascii=False, indent=2)
    print(f"  Vygenerováno {vystup} ({len(lekce)} lekcí)")


# 4. RSS feed – web/feed.xml
# RSS je jednoduchý XML formát – každá lekce je <item>

def generuj_rss(lekce_meta: list[dict], vystup: Path, base_url: str = "http://localhost:8080") -> None:
    """Vygeneruje RSS feed se seznamem lekcí."""
    items = ""
    for l in lekce_meta:
        items += f"""  <item>
    <title>Lekce {l['cislo']:02d}: {html.escape(l['titul'])}</title>
    <link>{base_url}/lekce/{l['slug']}.html</link>
    <description>Python kurz – lekce {l['cislo']}</description>
    <guid>{base_url}/lekce/{l['slug']}.html</guid>
  </item>\n"""

    rss = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
<channel>
  <title>Python kurz – interaktivní lekce</title>
  <link>{base_url}</link>
  <description>Interaktivní kurz Pythonu od print() po metaklasy</description>
{items}</channel>
</rss>"""

    vystup.write_text(rss, encoding="utf-8")
    print(f"  RSS feed: {vystup} ({len(lekce_meta)} položek)")


# ── Demo ──────────────────────────────────────────────────────────────────────

print("\n=== Demo: generuj_search_json ===")
zde = Path(__file__).parent.parent  # adresář interactive/

# Vygenerujeme search.json do web/
web_dir = zde / "web"
web_dir.mkdir(exist_ok=True)
generuj_search_json(zde, web_dir / "search.json")

# Načteme a ukážeme první 3 záznamy
with open(web_dir / "search.json", encoding="utf-8") as f:
    data = json.load(f)
print(f"\nPrvní 3 záznamy v search.json:")
for item in data[:3]:
    print(f"  {item['cislo']:02d}: {item['titul']}")

# RSS feed
print("\n=== Demo: generuj_rss ===")
generuj_rss(data[:5], web_dir / "feed.xml")

# Ukázka navigace
print("\n=== Demo: navigace ===")
if len(data) >= 3:
    nav = ukazka_navigace(data, 1)
    print(f"  prev: {nav['prev']}")
    print(f"  next: {nav['next']}")

print("\nDokončeno. Soubory v:", web_dir)
print("Spusť originální 34_generator_webu.py pro kompletní web s HTML stránkami.")
