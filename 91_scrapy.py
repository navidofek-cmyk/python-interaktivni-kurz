"""
LEKCE 91: Scrapy – web scraping framework
==========================================
pip install scrapy

Scrapy = průmyslový web scraping framework.
Selenium/Playwright = ovládá prohlížeč (JS stránky).
Scrapy = čistý HTTP, rychlý, škálovatelný (stovky stránek/sec).

Architektura:
  Spider  → definuje co stáhnout a jak parsovat
  Item    → datový model výsledku
  Pipeline→ zpracování (uložení do DB, čištění dat)
  Middleware → interceptory (User-Agent, proxy, rate limit)

Kdy Scrapy, kdy Playwright:
  Scrapy    → statické HTML, rychlost, velké projekty
  Playwright→ JavaScript rendered, přihlášení, interakce
"""

import textwrap
import subprocess
import sys
from pathlib import Path

# ══════════════════════════════════════════════════════════════
# ČÁST 1: Scrapy bez projektu – inline spider
# ══════════════════════════════════════════════════════════════

print("=== Scrapy základy ===\n")

try:
    import scrapy
    from scrapy.crawler import CrawlerProcess
    from scrapy.http import HtmlResponse
    from scrapy import Item, Field
    from scrapy.item import DictItem
    SCRAPY_OK = True
    print(f"Scrapy {scrapy.__version__} dostupný\n")
except ImportError:
    print("Scrapy není nainstalováno: pip install scrapy\n")
    SCRAPY_OK = False

# Kód pro referenci i bez Scrapy
print("=== Spider kód ===\n")
print(textwrap.dedent("""\
  import scrapy

  # Item = datový model
  class LekceItem(scrapy.Item):
      cislo   = scrapy.Field()
      titulek = scrapy.Field()
      url     = scrapy.Field()
      obtiznost = scrapy.Field()

  # Spider = co stáhnout, jak parsovat
  class PythonKurzSpider(scrapy.Spider):
      name         = "python_kurz"
      start_urls   = ["https://navidofek-cmyk.github.io/python-interaktivni-kurz/"]
      custom_settings = {
          "DOWNLOAD_DELAY":          0.5,   # zdvořilost – 0.5s mezi požadavky
          "CONCURRENT_REQUESTS":     4,
          "ROBOTSTXT_OBEY":          True,
          "USER_AGENT": "Python-kurz-scraper/1.0 (+https://github.com/...)",
          "FEEDS": {"lekce.json": {"format": "json", "encoding": "utf8"}},
      }

      def parse(self, response):
          # Parsuj seznam lekcí z index stránky
          for karta in response.css(".card"):
              yield LekceItem(
                  cislo    = karta.css(".num::text").get("").strip(),
                  titulek  = karta.css(".card-title::text").get("").strip(),
                  url      = response.urljoin(karta.attrib["href"]),
                  obtiznost= karta.css(".stars::text").get("").strip(),
              )
              # Následuj odkaz na detail lekce
              yield response.follow(karta.attrib["href"],
                                     callback=self.parse_lekce)

      def parse_lekce(self, response):
          yield {
              "url":     response.url,
              "titulek": response.css("h1::text").get(""),
              "kod":     response.css("code::text").getall(),
          }

  # Spuštění
  from scrapy.crawler import CrawlerProcess
  process = CrawlerProcess()
  process.crawl(PythonKurzSpider)
  process.start()
"""))

# ══════════════════════════════════════════════════════════════
# ČÁST 2: Parsování HTML bez Scrapy (requests + parsel)
# ══════════════════════════════════════════════════════════════

print("\n=== parsel – CSS/XPath selektor (vestavěný v Scrapy) ===\n")

try:
    from parsel import Selector

    HTML = """
    <html><body>
    <div class="produkt" data-id="1">
      <h2 class="nazev">Python kurz</h2>
      <span class="cena">2 999 Kč</span>
      <div class="hodnoceni">⭐⭐⭐⭐⭐ (142 recenzí)</div>
      <ul class="tagy">
        <li>python</li><li>programování</li><li>kurz</li>
      </ul>
    </div>
    <div class="produkt" data-id="2">
      <h2 class="nazev">NumPy kniha</h2>
      <span class="cena">599 Kč</span>
      <div class="hodnoceni">⭐⭐⭐⭐ (37 recenzí)</div>
      <ul class="tagy"><li>python</li><li>datová věda</li></ul>
    </div>
    </body></html>
    """

    sel = Selector(text=HTML)

    print("CSS selektory:")
    for produkt in sel.css("div.produkt"):
        nazev  = produkt.css("h2.nazev::text").get()
        cena   = produkt.css("span.cena::text").get()
        tagy   = produkt.css("ul.tagy li::text").getall()
        pid    = produkt.attrib["data-id"]
        print(f"  [{pid}] {nazev:<20} {cena:<12} tagy={tagy}")

    print("\nXPath selektory:")
    for produkt in sel.xpath("//div[@class='produkt']"):
        hodnoceni = produkt.xpath(".//div[@class='hodnoceni']/text()").get("")
        hvezdicky = hodnoceni.count("⭐")
        print(f"  {hvezdicky}★  {hodnoceni.strip()[:40]}")

    print("\nKombinované CSS + regex:")
    import re
    for produkt in sel.css("div.produkt"):
        cena_text = produkt.css("span.cena::text").get("")
        cena_num  = re.search(r"[\d\s]+", cena_text)
        if cena_num:
            print(f"  Cena číselně: {cena_num.group().strip()} Kč")

except ImportError:
    print("  parsel není dostupný: pip install parsel")
    print("  (součást scrapy instalace)")


# ══════════════════════════════════════════════════════════════
# ČÁST 3: Item Pipeline
# ══════════════════════════════════════════════════════════════

print("\n=== Item Pipeline ===\n")
print(textwrap.dedent("""\
  # pipelines.py – zpracování každého scraped itemu

  import sqlite3
  from itemadapter import ItemAdapter

  class ValidacniPipeline:
      \"\"\"Zahodí itemy bez povinných polí.\"\"\"
      POVINNE = ["nazev", "cena", "url"]

      def process_item(self, item, spider):
          adapter = ItemAdapter(item)
          for pole in self.POVINNE:
              if not adapter.get(pole):
                  raise scrapy.exceptions.DropItem(f"Chybí {pole}")
          return item

  class CisteniCenPipeline:
      \"\"\"Parsuje cenu na číslo.\"\"\"
      def process_item(self, item, spider):
          cena_raw = item.get("cena", "0")
          item["cena_kc"] = int(''.join(filter(str.isdigit, cena_raw)))
          return item

  class SQLitePipeline:
      \"\"\"Ukládá do SQLite.\"\"\"
      def open_spider(self, spider):
          self.conn = sqlite3.connect("produkty.db")
          self.conn.execute(
              "CREATE TABLE IF NOT EXISTS produkty "
              "(nazev TEXT, cena_kc INT, url TEXT UNIQUE)"
          )

      def process_item(self, item, spider):
          self.conn.execute(
              "INSERT OR REPLACE INTO produkty VALUES (?,?,?)",
              (item["nazev"], item.get("cena_kc", 0), item["url"])
          )
          self.conn.commit()
          return item

      def close_spider(self, spider):
          self.conn.close()

  # settings.py
  ITEM_PIPELINES = {
      "myproject.pipelines.ValidacniPipeline": 100,   # číslo = pořadí
      "myproject.pipelines.CisteniCenPipeline": 200,
      "myproject.pipelines.SQLitePipeline": 300,
  }
"""))

# ══════════════════════════════════════════════════════════════
# ČÁST 4: Scrapy projekt – struktura
# ══════════════════════════════════════════════════════════════

print("\n=== Scrapy projekt ===\n")
print(textwrap.dedent("""\
  # Vytvoření projektu:
  scrapy startproject muj_scraper
  cd muj_scraper

  # Struktura:
  muj_scraper/
  ├── scrapy.cfg
  └── muj_scraper/
      ├── settings.py     ← konfigurace
      ├── items.py        ← datové modely
      ├── pipelines.py    ← zpracování dat
      ├── middlewares.py  ← interceptory
      └── spiders/
          └── kurz.py     ← spider(y)

  # Spuštění:
  scrapy crawl python_kurz                   # spusť spider
  scrapy crawl python_kurz -o lekce.json     # exportuj JSON
  scrapy crawl python_kurz -o lekce.csv      # exportuj CSV
  scrapy shell "https://example.com"         # interaktivní shell
  scrapy bench                               # benchmark rychlosti

  # Scrapy shell – debug selektory:
  >>> response.css("h1::text").get()
  >>> response.xpath("//a/@href").getall()
  >>> fetch("https://example.com/page2")
"""))

if SCRAPY_OK:
    print("=== Scrapy dostupný – testujeme parsování ===\n")
    # Simuluj response parsování
    html = b"""<html><body>
    <article><h2><a href="/l/01">Lekce 01: Ahoj</a></h2><span class="stars">⭐</span></article>
    <article><h2><a href="/l/02">Lekce 02: Proměnné</a></h2><span class="stars">⭐</span></article>
    </body></html>"""
    from scrapy.http import HtmlResponse
    response = HtmlResponse(url="http://test.com", body=html)
    for art in response.css("article"):
        print(f"  {art.css('h2 a::text').get()} → {art.css('h2 a::attr(href)').get()}")

print("""
=== Scrapy vs alternativy ===

  Scrapy     → velké projekty, pipeline, distribuovaný (Scrapyd)
  requests   → jednoduché stránky, žádný framework
  httpx      → async HTTP, jako requests ale async
  Playwright → JS stránky, interakce
  Selenium   → legacy, pomalejší než Playwright
  Beautiful Soup → parsování HTML, spolupracuje s requests
""")

# TVOJE ÚLOHA:
# 1. Napiš spider který prochází všechny lekce kurzu a sbírá titulky.
# 2. Přidej middleware pro rotaci User-Agent hlaviček.
# 3. Ulož výsledky do SQLite přes pipeline (kombinuj s lekcí 40).
