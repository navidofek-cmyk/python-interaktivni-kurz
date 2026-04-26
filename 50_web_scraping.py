"""
LEKCE 50: Web Scraping
========================
Automatické stahování dat z webových stránek.
Python si přečte HTML stránku a vytáhne z ní data.

urllib  – vestavěný (lekce 41)
requests – pohodlnější HTTP klient  (pip install requests)
html.parser – vestavěný parser
BeautifulSoup – příjemnější API    (pip install beautifulsoup4)

Etika scrapingu:
  1. Zkontroluj robots.txt (napr.example.com/robots.txt)
  2. Nepřetěžuj server – přidej sleep mezi požadavky
  3. Respektuj Terms of Service
  4. Nepoužívej pro komerční účely bez svolení
"""

import urllib.request
import urllib.error
import html as html_module
import re
import time
import json
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse

# ══════════════════════════════════════════════════════════════
# ČÁST 1: Vestavěný html.parser
# ══════════════════════════════════════════════════════════════

print("=== Vestavěný HTMLParser ===\n")

class LinkParser(HTMLParser):
    """Extrahuje všechny <a href> z HTML."""
    def __init__(self, base_url=""):
        super().__init__()
        self.links: list[dict] = []
        self.base_url = base_url
        self._aktualni_text = ""

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            attrs_dict = dict(attrs)
            href = attrs_dict.get("href", "")
            if href and not href.startswith(("#", "javascript:")):
                full = urljoin(self.base_url, href)
                self.links.append({"href": full, "text": ""})

    def handle_data(self, data):
        self._aktualni_text = data.strip()

    def handle_endtag(self, tag):
        if tag == "a" and self.links:
            self.links[-1]["text"] = self._aktualni_text


class HeadingParser(HTMLParser):
    """Extrahuje nadpisy h1–h3."""
    def __init__(self):
        super().__init__()
        self.nadpisy: list[dict] = []
        self._aktualni = None

    def handle_starttag(self, tag, attrs):
        if tag in ("h1", "h2", "h3"):
            self._aktualni = {"uroven": tag, "text": ""}

    def handle_data(self, data):
        if self._aktualni:
            self._aktualni["text"] += data

    def handle_endtag(self, tag):
        if self._aktualni and tag == self._aktualni["uroven"]:
            self.nadpisy.append(self._aktualni)
            self._aktualni = None


# Demo na lokálním HTML
DEMO_HTML = """
<html><body>
<h1>Python kurz</h1>
<h2>Základy</h2>
<p>Naučíme se <a href="/lekce/01">print()</a> a
   <a href="/lekce/02">proměnné</a>.</p>
<h2>Algoritmy</h2>
<p>Viz <a href="https://example.com/alg">external</a>.</p>
<h3>Třídění</h3>
</body></html>
"""

lp = LinkParser(base_url="https://kurz.cz")
lp.feed(DEMO_HTML)
print("Linky:")
for l in lp.links:
    print(f"  {l['text']:<20} → {l['href']}")

hp = HeadingParser()
hp.feed(DEMO_HTML)
print("\nNadpisy:")
for n in hp.nadpisy:
    odsazeni = "  " * (int(n["uroven"][1]) - 1)
    print(f"  {odsazeni}{n['uroven']}: {n['text']}")


# ══════════════════════════════════════════════════════════════
# ČÁST 2: Scraping s urllib (bez závislostí)
# ══════════════════════════════════════════════════════════════

print("\n=== Scraping s urllib ===\n")

def stahni_html(url: str, timeout: int = 5) -> str | None:
    headers = {"User-Agent": "Python-kurz-scraper/1.0 (educational)"}
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read().decode("utf-8", errors="replace")
    except (urllib.error.URLError, urllib.error.HTTPError) as e:
        print(f"  Chyba: {e}")
        return None

def extrahuj_title(html: str) -> str:
    m = re.search(r"<title[^>]*>(.*?)</title>", html, re.IGNORECASE | re.DOTALL)
    return m.group(1).strip() if m else "(bez titulku)"

def extrahuj_meta_description(html: str) -> str:
    m = re.search(
        r'<meta[^>]*name=["\']description["\'][^>]*content=["\'](.*?)["\']',
        html, re.IGNORECASE
    )
    return m.group(1)[:100] if m else "(žádný popis)"

def extrahuj_linky(html: str, base: str) -> list[str]:
    return [
        urljoin(base, href)
        for href in re.findall(r'href=["\'](.*?)["\']', html)
        if href and not href.startswith(("#", "javascript:", "mailto:"))
    ]

# Veřejné stránky pro demo
urls = [
    "https://python.org",
    "https://pypi.org",
]

for url in urls:
    print(f"Stahuji {url}...")
    html = stahni_html(url)
    if html:
        print(f"  Titulek: {html_module.unescape(extrahuj_title(html))}")
        print(f"  Popis:   {extrahuj_meta_description(html)[:80]}")
        linky = extrahuj_linky(html, url)
        same_domain = [l for l in linky if urlparse(l).netloc == urlparse(url).netloc]
        print(f"  Linky:   {len(linky)} celkem, {len(same_domain)} stejná doména")
    time.sleep(1)  # etiketa – nespamuj server


# ══════════════════════════════════════════════════════════════
# ČÁST 3: Parsování strukturovaných dat
# ══════════════════════════════════════════════════════════════

print("\n=== JSON API scraping ===\n")

def nacti_json(url: str) -> dict | list | None:
    try:
        with urllib.request.urlopen(url, timeout=5) as r:
            return json.loads(r.read())
    except Exception as e:
        print(f"  Chyba: {e}")
        return None

# JSONPlaceholder – veřejné API
print("GitHub API – Python repos:")
data = nacti_json("https://api.github.com/search/repositories?q=language:python&sort=stars&per_page=5")
if data and "items" in data:
    for repo in data["items"][:5]:
        print(f"  ⭐ {repo['stargazers_count']:>7,} | {repo['full_name']:<40} | {repo['description'] or '':.50}")

print("\nHacker News – top stories:")
ids = nacti_json("https://hacker-news.firebaseio.com/v0/topstories.json")
if ids:
    for id_ in ids[:3]:
        story = nacti_json(f"https://hacker-news.firebaseio.com/v0/item/{id_}.json")
        if story:
            print(f"  [{story.get('score',0):4d} bodů] {story.get('title',''):.70}")
        time.sleep(0.2)


# ══════════════════════════════════════════════════════════════
# ČÁST 4: Robots.txt parser
# ══════════════════════════════════════════════════════════════

print("\n=== Robots.txt – etiketa ===\n")

from urllib.robotparser import RobotFileParser

def zkontroluj_robots(web: str, cesta: str) -> bool:
    rp = RobotFileParser()
    rp.set_url(f"{web}/robots.txt")
    try:
        rp.read()
        smi = rp.can_fetch("*", f"{web}{cesta}")
        print(f"  {web}{cesta} → {'✓ povoleno' if smi else '✗ zakázáno'}")
        return smi
    except Exception as e:
        print(f"  Nelze přečíst robots.txt: {e}")
        return True

zkontroluj_robots("https://python.org",  "/")
zkontroluj_robots("https://python.org",  "/search")
zkontroluj_robots("https://pypi.org",    "/")


# ══════════════════════════════════════════════════════════════
# ČÁST 5: Crawler – procházení více stránek
# ══════════════════════════════════════════════════════════════

print("\n=== Mini crawler ===\n")

from collections import deque

def crawl(start_url: str, max_stranek: int = 5, delay: float = 0.5) -> dict:
    """Projde web do šířky, vrátí mapu URL → titulek."""
    fronta    = deque([start_url])
    navstiveno = {start_url}
    vysledky  = {}
    domena    = urlparse(start_url).netloc

    while fronta and len(vysledky) < max_stranek:
        url = fronta.popleft()
        print(f"  Stahuji [{len(vysledky)+1}/{max_stranek}]: {url[:70]}")

        html = stahni_html(url)
        if not html:
            continue

        titulek = html_module.unescape(extrahuj_title(html))
        vysledky[url] = titulek

        for link in extrahuj_linky(html, url):
            if (link not in navstiveno
                    and urlparse(link).netloc == domena
                    and urlparse(link).scheme in ("http", "https")):
                navstiveno.add(link)
                fronta.append(link)

        time.sleep(delay)

    return vysledky

vysledky = crawl("https://python.org", max_stranek=4)
print(f"\nNalezené stránky:")
for url, titulek in vysledky.items():
    print(f"  {titulek[:50]:<52} {url[:60]}")

# TVOJE ÚLOHA:
# 1. Přidej ukládání výsledků do CSV souboru (csv modul).
# 2. Rozšiř crawler aby sledoval hloubku (BFS vrstva po vrstvě).
# 3. Přidej extrakci všech obrázků (src z <img>) ze stránky.
# 4. Napiš scraper který stáhne seznam Python balíčků z PyPI /simple/.
