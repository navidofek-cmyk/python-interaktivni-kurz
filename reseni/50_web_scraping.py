"""Reseni – Lekce 50: Web Scraping"""

import urllib.request
import urllib.error
import urllib.robotparser
import csv
import re
import time
import json
import io
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse
from collections import deque
from pathlib import Path


# Pomocne funkce ze zdrojove lekce
def stahni_html(url: str, timeout: int = 5) -> str | None:
    headers = {"User-Agent": "Python-kurz-scraper/1.0 (educational)"}
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read().decode("utf-8", errors="replace")
    except Exception:
        return None


def extrahuj_linky(html: str, base: str) -> list[str]:
    return [
        urljoin(base, href)
        for href in re.findall(r'href=["\'](.*?)["\']', html)
        if href and not href.startswith(("#", "javascript:", "mailto:"))
    ]


def extrahuj_title(html: str) -> str:
    m = re.search(r"<title[^>]*>(.*?)</title>", html, re.IGNORECASE | re.DOTALL)
    return m.group(1).strip() if m else "(bez titulku)"


# 1. Ulozeni vysledku crawlu do CSV souboru

print("=== Ukol 1: Ulozeni do CSV ===\n")


def crawl_do_csv(
    start_url: str,
    csv_soubor: str,
    max_stranek: int = 4,
    delay: float = 0.5,
) -> list[dict]:
    """Projde web a vysledky ulozi do CSV."""
    fronta    = deque([start_url])
    navstiveno = {start_url}
    vysledky  = []
    domena    = urlparse(start_url).netloc

    while fronta and len(vysledky) < max_stranek:
        url = fronta.popleft()
        print(f"  [{len(vysledky)+1}/{max_stranek}] {url[:70]}")

        html = stahni_html(url)
        if not html:
            continue

        titulek = extrahuj_title(html)
        import html as html_module
        titulek = html_module.unescape(titulek)
        pocet_znaku = len(html)
        pocet_linku = len(extrahuj_linky(html, url))

        zaznam = {
            "url": url,
            "titulek": titulek,
            "znaky": pocet_znaku,
            "linky": pocet_linku,
        }
        vysledky.append(zaznam)

        for link in extrahuj_linky(html, url):
            if (link not in navstiveno
                    and urlparse(link).netloc == domena
                    and urlparse(link).scheme in ("http", "https")):
                navstiveno.add(link)
                fronta.append(link)

        time.sleep(delay)

    # Zapis do CSV
    if vysledky:
        with open(csv_soubor, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["url", "titulek", "znaky", "linky"])
            writer.writeheader()
            writer.writerows(vysledky)
        print(f"\n  Ulozeno {len(vysledky)} zaznamu do {csv_soubor}")

    return vysledky


vysledky = crawl_do_csv("https://python.org", "crawl_vysledky.csv", max_stranek=3)
if vysledky:
    print("\n  Prvni zaznam z CSV:")
    with open("crawl_vysledky.csv", encoding="utf-8") as f:
        for i, radek in enumerate(csv.DictReader(f)):
            if i == 0:
                print(f"    titulek: {radek['titulek'][:50]}")
                print(f"    znaky:   {radek['znaky']}")
                break
Path("crawl_vysledky.csv").unlink(missing_ok=True)


# 2. Crawler se sledovanim hloubky (BFS vrstva po vrstve)

print("\n=== Ukol 2: Crawler s hloubkou ===\n")


def crawl_s_hloubkou(
    start_url: str,
    max_hloubka: int = 2,
    max_stranek: int = 6,
    delay: float = 0.5,
) -> dict:
    """BFS crawler ktery sleduje hloubku vrstev."""
    # fronta obsahuje (url, hloubka)
    fronta: deque[tuple[str, int]] = deque([(start_url, 0)])
    navstiveno = {start_url}
    vysledky: dict[str, dict] = {}
    domena = urlparse(start_url).netloc

    while fronta and len(vysledky) < max_stranek:
        url, hloubka = fronta.popleft()

        if hloubka > max_hloubka:
            continue

        print(f"  [hloubka={hloubka}] {url[:60]}")
        html = stahni_html(url)
        if not html:
            continue

        import html as html_m
        titulek = html_m.unescape(extrahuj_title(html))
        vysledky[url] = {"titulek": titulek, "hloubka": hloubka}

        if hloubka < max_hloubka:
            for link in extrahuj_linky(html, url):
                if (link not in navstiveno
                        and urlparse(link).netloc == domena
                        and urlparse(link).scheme in ("http", "https")):
                    navstiveno.add(link)
                    fronta.append((link, hloubka + 1))

        time.sleep(delay)

    return vysledky


vysledky_h = crawl_s_hloubkou("https://python.org", max_hloubka=1, max_stranek=4)
print(f"\n  Nalezeno {len(vysledky_h)} stranek (max hloubka 1)")
for url, info in list(vysledky_h.items())[:2]:
    print(f"    hloubka={info['hloubka']} {info['titulek'][:40]}")


# 3. Extrakce obrazku (src z <img>)

print("\n=== Ukol 3: Extrakce obrazku z HTML ===\n")


class ImgParser(HTMLParser):
    """Extrahuje src z vsech <img> tagu."""
    def __init__(self, base_url: str = ""):
        super().__init__()
        self.obrazky: list[dict] = []
        self.base_url = base_url

    def handle_starttag(self, tag: str, attrs: list[tuple]) -> None:
        if tag == "img":
            attrs_dict = dict(attrs)
            src = attrs_dict.get("src", "")
            alt = attrs_dict.get("alt", "")
            if src:
                full_src = urljoin(self.base_url, src)
                self.obrazky.append({"src": full_src, "alt": alt})


DEMO_HTML = """
<html><body>
<img src="/images/logo.png" alt="Logo">
<img src="https://cdn.example.com/banner.jpg" alt="Banner">
<img src="/static/python.svg">
<p>Neobrazek</p>
<img src="pic.gif" alt="Animace">
</body></html>
"""

img_parser = ImgParser(base_url="https://kurz.cz")
img_parser.feed(DEMO_HTML)
print(f"Nalezeno {len(img_parser.obrazky)} obrazku:")
for img in img_parser.obrazky:
    alt = f" (alt={img['alt']!r})" if img['alt'] else ""
    print(f"  {img['src']}{alt}")

# Extrakce ze skutecne stranky
html = stahni_html("https://python.org")
if html:
    parser = ImgParser(base_url="https://python.org")
    parser.feed(html)
    print(f"\npython.org – nalezeno {len(parser.obrazky)} obrazku:")
    for img in parser.obrazky[:5]:
        print(f"  {img['src'][:80]}")


# 4. Scraper PyPI /simple/

print("\n=== Ukol 4: PyPI /simple/ balicky ===\n")


def stahni_pypi_balicky(limit: int = 20) -> list[str]:
    """Stahne seznam Python balicku z PyPI /simple/."""
    try:
        req = urllib.request.Request(
            "https://pypi.org/simple/",
            headers={
                "User-Agent": "Python-kurz/1.0",
                "Accept": "application/vnd.pypi.simple.v1+json",
            },
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
            return [p["name"] for p in data.get("projects", [])[:limit]]
    except Exception as e:
        # Zaloha – parsovani HTML
        try:
            req2 = urllib.request.Request(
                "https://pypi.org/simple/",
                headers={"User-Agent": "Python-kurz/1.0"},
            )
            with urllib.request.urlopen(req2, timeout=10) as resp2:
                html2 = resp2.read().decode()
                return re.findall(r'<a[^>]*>([^<]+)</a>', html2)[:limit]
        except Exception as e2:
            print(f"  Chyba: {e2}")
            return []


balicky = stahni_pypi_balicky(limit=15)
print(f"Prvnich {len(balicky)} balicku na PyPI:")
for b in balicky[:10]:
    print(f"  {b}")
if len(balicky) > 10:
    print(f"  ... (+{len(balicky)-10} dalsi)")
