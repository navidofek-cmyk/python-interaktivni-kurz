"""Řešení – Lekce 91: Scrapy – web scraping framework"""

# vyžaduje: pip install scrapy parsel

import re
import json
import sqlite3
import textwrap
from pathlib import Path

# 1. Spider pro lekce kurzu
print("=== 1. Spider pro lekce kurzu ===\n")

KURZ_SPIDER_KOD = '''\
import scrapy
import json
from pathlib import Path

class LekceItem(scrapy.Item):
    cislo    = scrapy.Field()
    titulek  = scrapy.Field()
    url      = scrapy.Field()
    sekce    = scrapy.Field()
    ulohy    = scrapy.Field()   # seznam úloh z "TVOJE ÚLOHA"

class PythonKurzSpider(scrapy.Spider):
    name         = "python_kurz"
    start_urls   = ["https://navidofek-cmyk.github.io/python-interaktivni-kurz/"]
    custom_settings = {
        "DOWNLOAD_DELAY":          0.5,
        "CONCURRENT_REQUESTS":     4,
        "ROBOTSTXT_OBEY":          True,
        "USER_AGENT":              "Python-kurz-spider/1.0",
        "FEEDS": {
            "lekce.json": {"format": "json", "encoding": "utf8", "indent": 2}
        },
        "ITEM_PIPELINES": {
            "myproject.pipelines.ValidacniPipeline": 100,
            "myproject.pipelines.SQLitePipeline":    200,
        },
    }

    def parse(self, response):
        """Parsuje index stránku – seznam všech lekcí."""
        # Hledej karty lekcí
        for karta in response.css(".lesson-card, .card, article"):
            odkaz = karta.css("a::attr(href)").get("")
            if not odkaz:
                continue

            yield LekceItem(
                cislo   = karta.css(".lesson-number, .num::text").get("").strip(),
                titulek = karta.css("h2::text, h3::text, .title::text").get("").strip(),
                url     = response.urljoin(odkaz),
                sekce   = karta.css(".section, .category::text").get("").strip(),
                ulohy   = [],
            )

            # Přejdi na detail stránky lekce
            yield response.follow(
                odkaz,
                callback=self.parse_lekce,
                cb_kwargs={"url": response.urljoin(odkaz)},
            )

    def parse_lekce(self, response, url: str):
        """Parsuje detail lekce – extrahuje úlohy z 'TVOJE ÚLOHA' sekce."""
        # Hledej sekci s úlohami (typicky v <code> nebo <pre> tagách)
        titulek = response.css("h1::text, h2::text").get("").strip()
        kod     = response.css("code::text, pre::text").getall()

        # Extrakce úloh
        ulohy = []
        for blok in kod:
            if "TVOJE ÚLOHA" in blok or "TVOJE ÚLOHA" in blok:
                radky = blok.splitlines()
                for radek in radky:
                    if re.match(r"^#\\s+\\d+\\.", radek):
                        uloha = re.sub(r"^#\\s+\\d+\\.\\s*", "", radek).strip()
                        if uloha:
                            ulohy.append(uloha)

        yield LekceItem(
            cislo   = re.search(r"(\\d+)", url).group(1) if re.search(r"(\\d+)", url) else "",
            titulek = titulek,
            url     = url,
            sekce   = "",
            ulohy   = ulohy,
        )
'''
print(KURZ_SPIDER_KOD)

# Testování parsování (bez skutečného Scrapy crawlingu)
print("\n  Testování parsování (offline):\n")

try:
    from parsel import Selector

    TESTOVACI_HTML = b"""
    <html><body>
    <div class="lesson-card">
        <span class="num">01</span>
        <h2><a href="/lekce/01_ahoj_svete">Ahoj, světe!</a></h2>
        <span class="section">Základy</span>
    </div>
    <div class="lesson-card">
        <span class="num">02</span>
        <h2><a href="/lekce/02_promenne">Proměnné a typy</a></h2>
        <span class="section">Základy</span>
    </div>
    <div class="lesson-card">
        <span class="num">83</span>
        <h2><a href="/lekce/83_aws_boto3">AWS boto3</a></h2>
        <span class="section">Pokročilé</span>
    </div>
    </body></html>
    """

    sel = Selector(body=TESTOVACI_HTML)
    lekce_list = []

    for karta in sel.css(".lesson-card"):
        cislo   = karta.css(".num::text").get("").strip()
        titulek = karta.css("h2 a::text").get("").strip()
        odkaz   = karta.css("h2 a::attr(href)").get("").strip()
        sekce   = karta.css(".section::text").get("").strip()
        lekce_list.append({
            "cislo":   cislo,
            "titulek": titulek,
            "url":     f"https://example.com{odkaz}",
            "sekce":   sekce,
        })
        print(f"  [{cislo:>3}] {titulek:<30} sekce={sekce}")

    print(f"\n  Celkem nalezeno: {len(lekce_list)} lekcí")

except ImportError:
    print("  parsel není dostupný (součást Scrapy): pip install scrapy")


# 2. Middleware pro rotaci User-Agent hlaviček
print("\n=== 2. User-Agent rotace middleware ===\n")

UA_MIDDLEWARE_KOD = '''\
# middlewares.py

import random
from scrapy import signals

# Databáze User-Agent řetězců
USER_AGENTS = [
    # Chrome
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    # Firefox
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0",
    # Safari
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
    # Linux
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
]

class RotacniUserAgentMiddleware:
    """Náhodně rotuje User-Agent pro každý request."""

    @classmethod
    def from_crawler(cls, crawler):
        middleware = cls()
        crawler.signals.connect(middleware.spider_opened, signal=signals.spider_opened)
        return middleware

    def spider_opened(self, spider):
        spider.logger.info("RotacniUserAgentMiddleware aktivován")

    def process_request(self, request, spider):
        ua = random.choice(USER_AGENTS)
        request.headers["User-Agent"] = ua
        spider.logger.debug(f"UA: {ua[:50]}...")
        return None  # pokračuj v pipeline

    def process_response(self, request, response, spider):
        # Zkontroluj zda nás neblokují
        if response.status == 403:
            spider.logger.warning(f"403 Forbidden na {request.url} – zkusím znovu")
            return request  # retry
        if response.status == 429:
            spider.logger.warning("429 Too Many Requests – čekám...")
            import time; time.sleep(5)
            return request  # retry
        return response


# settings.py – aktivace middleware
DOWNLOADER_MIDDLEWARES = {
    "scrapy.downloadermiddlewares.useragent.UserAgentMiddleware": None,  # vypni výchozí
    "myproject.middlewares.RotacniUserAgentMiddleware": 400,
}
'''
print(UA_MIDDLEWARE_KOD)

# Demo rotace
print("  Demo rotace UA:\n")
UA_LIST = [
    "Mozilla/5.0 Chrome/120",
    "Mozilla/5.0 Firefox/121",
    "Mozilla/5.0 Safari/605",
]
for i in range(5):
    ua = UA_LIST[i % len(UA_LIST)]
    print(f"  Request {i+1}: {ua}")


# 3. Pipeline: uložení do SQLite
print("\n=== 3. SQLite Pipeline ===\n")

PIPELINE_KOD = '''\
# pipelines.py
import sqlite3
from itemadapter import ItemAdapter

class ValidacniPipeline:
    """Zahodí itemy bez povinných polí."""
    POVINNE = ["cislo", "titulek", "url"]

    def process_item(self, item, spider):
        adapter = ItemAdapter(item)
        for pole in self.POVINNE:
            if not adapter.get(pole):
                raise scrapy.exceptions.DropItem(f"Chybí povinné pole: {pole}")
        return item

class CisteniPipeline:
    """Normalizuje data."""
    def process_item(self, item, spider):
        adapter = ItemAdapter(item)
        # Normalizuj číslo
        cislo = adapter.get("cislo", "").strip().lstrip("0") or "0"
        adapter["cislo"] = int(cislo) if cislo.isdigit() else 0
        # Normalizuj titulek
        adapter["titulek"] = adapter.get("titulek", "").strip()
        return item

class SQLitePipeline:
    """Ukládá scraped data do SQLite databáze."""

    def open_spider(self, spider):
        self.conn = sqlite3.connect("lekce.db")
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS lekce (
                id      INTEGER PRIMARY KEY,
                cislo   INTEGER UNIQUE,
                titulek TEXT,
                url     TEXT,
                sekce   TEXT,
                ulohy   TEXT   -- JSON array
            )
        """)
        self.conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_sekce ON lekce (sekce)
        """)
        self.conn.commit()
        spider.logger.info("SQLite pipeline otevřena: lekce.db")

    def process_item(self, item, spider):
        adapter = ItemAdapter(item)
        import json
        self.conn.execute(
            "INSERT OR REPLACE INTO lekce (cislo, titulek, url, sekce, ulohy) "
            "VALUES (?, ?, ?, ?, ?)",
            (
                adapter.get("cislo"),
                adapter.get("titulek"),
                adapter.get("url"),
                adapter.get("sekce", ""),
                json.dumps(adapter.get("ulohy", []), ensure_ascii=False),
            )
        )
        self.conn.commit()
        return item

    def close_spider(self, spider):
        count = self.conn.execute("SELECT COUNT(*) FROM lekce").fetchone()[0]
        spider.logger.info(f"SQLite pipeline zavřena. Uloženo {count} lekcí.")
        self.conn.close()
'''
print(PIPELINE_KOD)

# Funkční demo SQLite pipeline (bez Scrapy)
print("\nFunkční demo (bez Scrapy):\n")

conn = sqlite3.connect(":memory:")
conn.execute("""
    CREATE TABLE lekce (
        id      INTEGER PRIMARY KEY,
        cislo   INTEGER UNIQUE,
        titulek TEXT,
        url     TEXT,
        sekce   TEXT,
        ulohy   TEXT
    )
""")

DEMO_LEKCE = [
    (1,  "Ahoj, světe!",         "http://example.com/01", "Základy",  "[]"),
    (83, "AWS boto3",             "http://example.com/83", "Pokročilé","[]"),
    (91, "Scrapy scraping",       "http://example.com/91", "Pokročilé",
     json.dumps(["Napiš spider", "Přidej middleware"])),
]

for cislo, titulek, url, sekce, ulohy in DEMO_LEKCE:
    conn.execute(
        "INSERT INTO lekce (cislo, titulek, url, sekce, ulohy) VALUES (?,?,?,?,?)",
        (cislo, titulek, url, sekce, ulohy)
    )
conn.commit()

print("  Uložené lekce:")
for row in conn.execute("SELECT cislo, titulek, sekce FROM lekce ORDER BY cislo"):
    print(f"    [{row[0]:>3}] {row[1]:<30} ({row[2]})")

pokrocile = conn.execute(
    "SELECT COUNT(*) FROM lekce WHERE sekce = 'Pokročilé'"
).fetchone()[0]
print(f"\n  Pokročilé lekce: {pokrocile}")

# Extrakce úloh
print("\n  Úlohy z lekcí:")
for row in conn.execute("SELECT cislo, titulek, ulohy FROM lekce WHERE ulohy != '[]'"):
    ulohy = json.loads(row[2])
    for i, uloha in enumerate(ulohy, 1):
        print(f"    Lekce {row[0]} – {i}. {uloha}")

conn.close()

print("\n=== Shrnutí ===")
print("  1. PythonKurzSpider   – CSS selektory, parse_lekce, extrakce úloh")
print("  2. RotacniUserAgentMiddleware – rotace z listiny, retry na 403/429")
print("  3. SQLitePipeline     – validace, čištění, INSERT OR REPLACE, index")
