"""
LEKCE 34: Generátor statického webu
======================================
Napíšeme vlastní static-site generator – program, který přečte
všechny lekce tohoto kurzu a vygeneruje z nich HTML stránky.

Naučíme se:
  pathlib.Path  – moderní práce se soubory a cestami
  ast           – parsování Python kódu (abstraktní syntaktický strom)
  textwrap      – zarovnávání textu
  html          – escapování pro bezpečné HTML
  string šablony – generování HTML přes f-strings

Výstup: adresář web/ s index.html a stránkou pro každou lekci.
Spusť a pak otevři web/index.html v prohlížeči.
"""

import ast
import html
import re
import textwrap
import unicodedata
from pathlib import Path
from urllib.parse import quote

# ══════════════════════════════════════════════════════════════
# ČÁST 1: pathlib – soubory jako objekty
# ══════════════════════════════════════════════════════════════

print("=== pathlib demo ===\n")

zde = Path(__file__).parent          # adresář tohoto souboru
print(f"Adresář skriptu: {zde}")
print(f"Jméno souboru:   {Path(__file__).name}")
print(f"Přípona:         {Path(__file__).suffix}")
print(f"Stem:            {Path(__file__).stem}")

# Glob – najdi všechny .py soubory odpovídající vzoru
lekce_soubory = sorted(zde.glob("[0-9][0-9]_*.py"))
print(f"\nNalezeno {len(lekce_soubory)} lekcí:")
for s in lekce_soubory[:5]:
    print(f"  {s.name}")
if len(lekce_soubory) > 5:
    print(f"  ... a {len(lekce_soubory)-5} dalších")


# ══════════════════════════════════════════════════════════════
# ČÁST 2: ast – čtení docstringů
# ══════════════════════════════════════════════════════════════

def ascii_stem(stem: str) -> str:
    """Převede 'podmínky' → 'podminky' pro bezpečné URL a názvy souborů."""
    norm = unicodedata.normalize("NFD", stem)
    return "".join(c for c in norm if unicodedata.category(c) != "Mn")

def nacti_lekci(cesta: Path) -> dict:
    """Přečte .py soubor a vytáhne metadata pomocí ast."""
    kod = cesta.read_text(encoding="utf-8")
    try:
        strom = ast.parse(kod)
        docstring = ast.get_docstring(strom) or ""
    except SyntaxError:
        docstring = ""

    # Titul = první řádek docstringu
    radky = docstring.splitlines()
    titul = radky[0].strip() if radky else cesta.stem

    # Obtížnost ze třetího řádku (===...)
    obtiznost = ""
    for r in radky:
        hvezdy = r.count("⭐")
        if hvezdy:
            obtiznost = "⭐" * hvezdy
            break

    # Číslo lekce z názvu souboru
    m = re.match(r"(\d+)_", cesta.stem)
    cislo = int(m.group(1)) if m else 0

    # Úlohy na konci souboru
    ulohy = []
    for radek in kod.splitlines():
        stripped = radek.strip()
        if stripped.startswith("# ") and stripped[2:3].isdigit() and ". " in stripped:
            ulohy.append(stripped[2:])

    return {
        "cislo":     cislo,
        "soubor":    cesta.name,
        "stem":      cesta.stem,
        "slug":      ascii_stem(cesta.stem),   # bez diakritiky – bezpečné URL
        "titul":     titul,
        "docstring": docstring,
        "obtiznost": obtiznost or "⭐",
        "ulohy":     ulohy,
        "kod":       kod,
    }


# ══════════════════════════════════════════════════════════════
# ČÁST 3: HTML šablony
# ══════════════════════════════════════════════════════════════

CSS = """
:root {
  --bg: #0d1117; --surface: #161b22; --border: #30363d;
  --text: #e6edf3; --muted: #8b949e; --accent: #58a6ff;
  --green: #3fb950; --yellow: #d29922; --red: #f85149;
  --code-bg: #1c2128;
}
* { box-sizing: border-box; margin: 0; padding: 0; }
body { background: var(--bg); color: var(--text);
       font-family: 'Segoe UI', system-ui, sans-serif;
       line-height: 1.6; }
a { color: var(--accent); text-decoration: none; }
a:hover { text-decoration: underline; }

header { background: var(--surface); border-bottom: 1px solid var(--border);
         padding: 1rem 2rem; display: flex; align-items: center; gap: 1rem; }
header h1 { font-size: 1.4rem; }
header .badge { background: var(--accent); color: #000;
                padding: .2rem .6rem; border-radius: 999px;
                font-size: .75rem; font-weight: 700; }

main { max-width: 960px; margin: 2rem auto; padding: 0 1.5rem; }

/* INDEX */
.grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px,1fr));
        gap: 1rem; margin-top: 1.5rem; }
.card { background: var(--surface); border: 1px solid var(--border);
        border-radius: 8px; padding: 1rem 1.2rem;
        transition: border-color .2s, transform .15s;
        display: flex; flex-direction: column; gap: .3rem; }
.card:hover { border-color: var(--accent); transform: translateY(-2px); text-decoration: none; }
.card .num { color: var(--muted); font-size: .75rem; }
.card-title { font-size: .95rem; font-weight: 600; color: var(--text); }
.card .stars { font-size: .85rem; margin-top: auto; }
/* SEKCE */
.sekce { margin: 2.5rem 0; }
.sekce-header { display: flex; align-items: center; gap: .8rem;
                margin-bottom: 1rem; }
.sekce-icon { font-size: 1.6rem; line-height: 1; }
.sekce-info h2 { font-size: 1.15rem; margin: 0; }
.sekce-info p  { color: var(--muted); font-size: .85rem; margin: .15rem 0 0; }
.sekce-badge { margin-left: auto; background: var(--border);
               color: var(--muted); font-size: .75rem;
               padding: .2rem .6rem; border-radius: 999px; white-space: nowrap; }

/* LEKCE */
.lekce-header { margin-bottom: 1.5rem; }
.lekce-header h1 { font-size: 1.8rem; margin-bottom: .5rem; }
.meta { color: var(--muted); font-size: .9rem; display: flex; gap: 1rem; }

.docstring { background: var(--surface); border-left: 3px solid var(--accent);
             padding: 1rem 1.2rem; border-radius: 0 6px 6px 0;
             margin-bottom: 1.5rem; white-space: pre-wrap;
             font-size: .92rem; color: var(--muted); }

pre.kod { background: var(--code-bg); border: 1px solid var(--border);
          border-radius: 8px; padding: 1.2rem; overflow-x: auto;
          font-family: 'Cascadia Code', 'Fira Code', monospace;
          font-size: .88rem; line-height: 1.5; }

/* Jednoduché barvení syntaxe */
.kw  { color: #ff7b72; }   /* keywords */
.st  { color: #a5d6ff; }   /* strings */
.cm  { color: #8b949e; font-style: italic; }  /* comments */
.fn  { color: #d2a8ff; }   /* def/class names */
.nb  { color: #79c0ff; }   /* builtins */
.nm  { color: #ffa657; }   /* numbers */

.ulohy { background: var(--surface); border: 1px solid var(--border);
         border-radius: 8px; padding: 1rem 1.2rem; margin-top: 1.5rem; }
.ulohy h3 { margin-bottom: .6rem; color: var(--green); }
.ulohy li { margin-left: 1.2rem; margin-bottom: .3rem; }

nav.zpet { margin-bottom: 1.5rem; }
footer { text-align: center; color: var(--muted); font-size: .8rem;
         padding: 2rem; border-top: 1px solid var(--border); margin-top: 3rem; }
"""

SEKCE = [
    {
        "rozsah": range(1, 9),
        "nazev":  "Základy",
        "ikona":  "🐣",
        "popis":  "print, proměnné, input, počítání, podmínky, cykly, seznamy, funkce",
        "barva":  "#3fb950",
    },
    {
        "rozsah": range(9, 11),
        "nazev":  "První projekty",
        "ikona":  "🎮",
        "popis":  "Kvíz se skóre a textová hra Had – první větší programy",
        "barva":  "#58a6ff",
    },
    {
        "rozsah": range(11, 15),
        "nazev":  "Datové struktury a soubory",
        "ikona":  "📦",
        "popis":  "Textové metody, slovníky, čtení a zápis souborů, Turtle grafika",
        "barva":  "#d2a8ff",
    },
    {
        "rozsah": range(15, 17),
        "nazev":  "Grafické projekty",
        "ikona":  "🎨",
        "popis":  "Dobrodružná textová hra a grafická hra Chytání hvězd",
        "barva":  "#ffa657",
    },
    {
        "rozsah": range(17, 22),
        "nazev":  "Věda a sarkasmus",
        "ikona":  "🔬",
        "popis":  "Výpočet černé díry, statistika úkolů, lednicka, spánek, detektiv",
        "barva":  "#ff7b72",
    },
    {
        "rozsah": range(22, 25),
        "nazev":  "OOP – třídy",
        "ikona":  "🏗️",
        "popis":  "Třídy, dědičnost, magic methods – základ objektového programování",
        "barva":  "#58a6ff",
    },
    {
        "rozsah": range(25, 28),
        "nazev":  "Pokročilé vzory",
        "ikona":  "⚙️",
        "popis":  "Async/await, dekorátory, context managery, generátory, itertools",
        "barva":  "#d29922",
    },
    {
        "rozsah": range(28, 31),
        "nazev":  "Novinky z dokumentace",
        "ikona":  "📰",
        "popis":  "match/case, walrus :=, @dataclass, ExceptionGroup, except* (3.10–3.12)",
        "barva":  "#3fb950",
    },
    {
        "rozsah": range(31, 35),
        "nazev":  "Internals & nástroje",
        "ikona":  "🔩",
        "popis":  "__slots__, descriptory, Protocol, TypedDict, metaklasy, generátor webu",
        "barva":  "#a5d6ff",
    },
    {
        "rozsah": range(35, 39),
        "nazev":  "Algoritmy",
        "ikona":  "🧮",
        "popis":  "Rekurze, třídící algoritmy, BFS/DFS/Dijkstra, dynamické programování",
        "barva":  "#ff7b72",
    },
    {
        "rozsah": range(39, 46),
        "nazev":  "Profesionální Python",
        "ikona":  "🚀",
        "popis":  "Testování, SQLite, REST API, design patterns, concurrency, výkon, packaging",
        "barva":  "#d2a8ff",
    },
    {
        "rozsah": range(46, 53),
        "nazev":  "Nástroje a ekosystém",
        "ikona":  "🔧",
        "popis":  "Regex, funkcionální programování, logging, CLI, web scraping, Pydantic, kód kvalita",
        "barva":  "#3fb950",
    },
    {
        "rozsah": range(53, 58),
        "nazev":  "Datová věda a frameworky",
        "ikona":  "📊",
        "popis":  "NumPy, Pandas, Matplotlib, FastAPI – reálné použití Pythonu",
        "barva":  "#ffa657",
    },
    {
        "rozsah": range(57, 62),
        "nazev":  "Pokročilé internals",
        "ikona":  "🔬",
        "popis":  "CPython bytekód, AST, garbage collector, SQLAlchemy ORM, Celery, Docker, C extensions",
        "barva":  "#a5d6ff",
    },
    {
        "rozsah": range(62, 67),
        "nazev":  "Distribuované systémy",
        "ikona":  "🌐",
        "popis":  "WebSockets, Redis, GraphQL, Kafka – real-time a škálovatelné architektury",
        "barva":  "#d29922",
    },
    {
        "rozsah": range(66, 71),
        "nazev":  "Produkce & DevOps",
        "ikona":  "⚙️",
        "popis":  "gRPC, mikroslužby, security, Kubernetes, MLOps",
        "barva":  "#ff7b72",
    },
]

def sekce_pro(cislo: int) -> str:
    for s in SEKCE:
        if cislo in s["rozsah"]:
            return s["nazev"]
    return "Ostatní"


def zvyrazni_python(kod: str) -> str:
    """Syntax highlighting – každý regex přeskakuje již otagované části."""

    KEYWORDS = r"\b(def|class|return|import|from|if|elif|else|for|while|" \
               r"try|except|finally|with|as|pass|break|continue|yield|" \
               r"lambda|and|or|not|in|is|True|False|None|async|await|" \
               r"raise|del|global|nonlocal|assert|match|case)\b"
    BUILTINS = r"\b(print|input|len|range|type|isinstance|list|dict|set|" \
               r"tuple|str|int|float|bool|open|super|property|staticmethod|" \
               r"classmethod|enumerate|zip|map|filter|sorted|reversed|" \
               r"min|max|sum|abs|round|hasattr|getattr|setattr|vars)\b"

    # html.escape: & → &amp;  < → &lt;  > → &gt;  " → &quot;
    # Tedy: """  →  &quot;&quot;&quot;   a  '''  →  &#x27;&#x27;&#x27;
    escp = html.escape(kod)

    def sub_mimo_spany(vzor: str, nahrada: str, text: str, flags: int = 0) -> str:
        """Aplikuje re.sub jen na části textu které nejsou uvnitř <span>."""
        segmenty = re.split(r'(<span[^>]*>.*?</span>)', text, flags=re.DOTALL)
        vysledek = []
        for i, seg in enumerate(segmenty):
            if i % 2 == 0:  # sudé indexy = text mimo spany
                vysledek.append(re.sub(vzor, nahrada, seg, flags=flags))
            else:           # liché indexy = hotový span, beze změny
                vysledek.append(seg)
        return "".join(vysledek)

    # 1. Komentáře (první – mohou obsahovat cokoli)
    escp = sub_mimo_spany(r"(#[^\n]*)", r'<span class="cm">\1</span>', escp)

    # 2. Trojité uvozovky (docstringy)
    Q3 = r'(&quot;&quot;&quot;.*?&quot;&quot;&quot;)'
    A3 = r"(&#x27;&#x27;&#x27;.*?&#x27;&#x27;&#x27;)"
    escp = sub_mimo_spany(Q3, r'<span class="st">\1</span>', escp, re.DOTALL)
    escp = sub_mimo_spany(A3, r'<span class="st">\1</span>', escp, re.DOTALL)

    # 3. Jednořádkové řetězce
    Q1 = r'(&quot;[^&\n]*(?:&[^;\n]*;[^&\n]*)*&quot;)'
    A1 = r"(&#x27;[^&#\n]*(?:&#[^;\n]*;[^&#\n]*)*&#x27;)"
    escp = sub_mimo_spany(Q1, r'<span class="st">\1</span>', escp)
    escp = sub_mimo_spany(A1, r'<span class="st">\1</span>', escp)

    # 4. Čísla
    escp = sub_mimo_spany(
        r"\b(\d[\d_]*\.?\d*(?:[eE][+-]?\d+)?)\b",
        r'<span class="nm">\1</span>', escp
    )

    # 5. Builtins
    escp = sub_mimo_spany(BUILTINS, r'<span class="nb">\1</span>', escp)

    # 6. Keywords
    escp = sub_mimo_spany(KEYWORDS, r'<span class="kw">\1</span>', escp)

    # 7. def/class jméno (jen bezprostředně za kw spanem)
    escp = re.sub(
        r'(<span class="kw">(?:def|class)</span>)\s+(\w+)',
        r'\1 <span class="fn">\2</span>', escp
    )

    return escp


def generuj_index(lekce: list[dict], vystup: Path) -> None:
    # Seskup lekce do sekcí
    sekce_lekce: dict[str, list] = {}
    for l in lekce:
        sekce_lekce.setdefault(sekce_pro(l["cislo"]), []).append(l)

    bloky = ""
    for s in SEKCE:
        skupina = sekce_lekce.get(s["nazev"], [])
        if not skupina:
            continue

        karty = ""
        for l in skupina:
            karty += f"""    <a class="card" href="lekce/{l['slug']}.html">
      <div class="num">Lekce {l['cislo']:02d}</div>
      <div class="card-title">{html.escape(l['titul'])}</div>
      <div class="stars">{l['obtiznost']}</div>
    </a>\n"""

        bloky += f"""<div class="sekce">
  <div class="sekce-header" style="border-left:3px solid {s['barva']};padding-left:.8rem">
    <span class="sekce-icon">{s['ikona']}</span>
    <div class="sekce-info">
      <h2>{html.escape(s['nazev'])}</h2>
      <p>{html.escape(s['popis'])}</p>
    </div>
    <span class="sekce-badge">{len(skupina)} lekcí</span>
  </div>
  <div class="grid">
{karty}  </div>
</div>
"""

    stranky = f"""<!DOCTYPE html>
<html lang="cs">
<head>
  <meta charset="utf-8">
  <title>Python kurz – interaktivní lekce</title>
  <style>{CSS}</style>
</head>
<body>
<header>
  <h1>🐍 Python kurz</h1>
  <span class="badge">{len(lekce)} lekcí</span>
</header>
<main>
  <p style="color:var(--muted);margin-top:1rem">
    Interaktivní kurz Pythonu – od <code>print("Ahoj")</code>
    po metaklasy, async a generátory webu.
  </p>
  {bloky}
</main>
<footer>Vygenerováno Pythonem · lekce 34</footer>
</body>
</html>"""

    vystup.write_text(stranky, encoding="utf-8")


def odstran_ulohy_z_kodu(kod: str) -> str:
    """Vystřihne blok # TVOJE ÚLOHA: ... z kódu – zobrazí se jen v boxu."""
    radky = kod.splitlines()
    vysledek = []
    preskakuj = False
    for radek in radky:
        stripped = radek.strip()
        if stripped.startswith("# TVOJE ÚLOHA") or stripped.startswith("# ROZŠÍŘENÍ"):
            preskakuj = True
        if not preskakuj:
            vysledek.append(radek)
    return "\n".join(vysledek).rstrip()

def generuj_lekci(l: dict, vystup: Path, prev_l=None, next_l=None) -> None:
    doc_html = html.escape(
        textwrap.dedent(l["docstring"]).strip()
    ) if l["docstring"] else ""

    ulohy_html = ""
    if l["ulohy"]:
        items = "\n".join(f"<li>{html.escape(u)}</li>" for u in l["ulohy"])
        ulohy_html = f'<div class="ulohy"><h3>Tvoje úlohy</h3><ul>{items}</ul></div>'

    kod_bez_uloh = odstran_ulohy_z_kodu(l["kod"])

    prev_html = (f'<a class="nav-btn" href="{prev_l["slug"]}.html">← {html.escape(prev_l["titul"])}</a>'
                 if prev_l else '<span></span>')
    next_html = (f'<a class="nav-btn" href="{next_l["slug"]}.html">{html.escape(next_l["titul"])} →</a>'
                 if next_l else '<span></span>')

    stranka = f"""<!DOCTYPE html>
<html lang="cs">
<head>
  <meta charset="utf-8">
  <title>Lekce {l['cislo']:02d}: {html.escape(l['titul'])}</title>
  <style>{CSS}
.page-nav {{ display:flex; justify-content:space-between; margin:1.5rem 0; gap:1rem; }}
.nav-btn {{ background:var(--surface); border:1px solid var(--border);
            padding:.5rem 1rem; border-radius:6px; font-size:.9rem; }}
.nav-btn:hover {{ border-color:var(--accent); text-decoration:none; }}
  </style>
</head>
<body>
<header>
  <h1>🐍 Python kurz</h1>
  <a href="../index.html">← Přehled</a>
</header>
<main>
  <div class="lekce-header">
    <h1>Lekce {l['cislo']:02d}: {html.escape(l['titul'])}</h1>
    <div class="meta">
      <span>{l['soubor']}</span>
      <span>{l['obtiznost']}</span>
    </div>
  </div>
  {'<div class="docstring">' + doc_html + '</div>' if doc_html else ''}
  <pre class="kod"><code>{zvyrazni_python(kod_bez_uloh)}</code></pre>
  {ulohy_html}
  <div class="page-nav">{prev_html}{next_html}</div>
</main>
<footer>Vygenerováno Pythonem · lekce 34</footer>
</body>
</html>"""

    vystup.write_text(stranka, encoding="utf-8")


# ══════════════════════════════════════════════════════════════
# ČÁST 4: Sestavení webu
# ══════════════════════════════════════════════════════════════

def sestav_web():
    print("\n=== Sestavuji web ===\n")

    web_dir   = zde / "web"
    lekce_dir = web_dir / "lekce"
    lekce_dir.mkdir(parents=True, exist_ok=True)

    # Načti všechny lekce
    soubory = sorted(zde.glob("[0-9][0-9]_*.py"))
    lekce   = [nacti_lekci(s) for s in soubory]
    print(f"Načteno {len(lekce)} lekcí.")

    # Index
    generuj_index(lekce, web_dir / "index.html")
    print(f"  ✓ web/index.html")

    # Smaž případné staré soubory s diakritikou v názvu
    for stary in lekce_dir.glob("*.html"):
        cist = ascii_stem(stary.stem) + stary.suffix
        if cist != stary.name:
            stary.unlink()

    # Jednotlivé lekce
    for i, l in enumerate(lekce):
        cil = lekce_dir / f"{l['slug']}.html"
        prev_l = lekce[i - 1] if i > 0 else None
        next_l = lekce[i + 1] if i < len(lekce) - 1 else None
        generuj_lekci(l, cil, prev_l, next_l)
        print(f"  ✓ web/lekce/{l['slug']}.html")

    print(f"\nHotovo! Otevři:")
    print(f"  {web_dir / 'index.html'}")
    print(f"\nNebo spusť lokální server:")
    print(f"  cd {web_dir} && python3 -m http.server 8080")
    print(f"  Pak jdi na: http://localhost:8080")

sestav_web()

# TVOJE ÚLOHA:
# 1. Přidej do každé lekce tlačítka "← předchozí" a "→ další".
# 2. Přidej do CSS tmavý/světlý přepínač (toggle přes JavaScript).
# 3. Přidej globální vyhledávání: skript který indexuje všechny lekce
#    do search.json a malý JS ho prohledá na straně klienta.
# 4. Přidej RSS feed (web/feed.xml) se seznamem lekcí.
