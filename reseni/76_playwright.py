"""Řešení – Lekce 76: Playwright – webová automatizace a testování"""

# vyžaduje: pip install playwright && playwright install chromium

import asyncio
import textwrap
from pathlib import Path

# 1. Scraper cen z e-shopu (demo s example.com jako dummy)
print("=== 1. Scraper cen (demo – example.com) ===\n")

try:
    from playwright.async_api import async_playwright
    PLAYWRIGHT_OK = True
except ImportError:
    PLAYWRIGHT_OK = False
    print("Playwright není nainstalován.")
    print("Spusť: pip install playwright && playwright install chromium\n")


async def scrape_ceny(url: str = "https://example.com") -> list[dict]:
    """
    Scraper pro stránky s produkty.
    Na example.com nenajde ceny – demo ukazuje strukturu kódu.
    Nahraď URL reálným e-shopem.
    """
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (compatible; PythonBot/1.0)",
            locale="cs-CZ",
        )
        page = await context.new_page()

        # Zachycení síťových požadavků (demo)
        api_volani = []
        page.on("request", lambda req: api_volani.append(req.url)
                if "api" in req.url.lower() else None)

        await page.goto(url, wait_until="domcontentloaded")
        titulek = await page.title()

        # Zkus najít produkty (různé selektory pro různé e-shopy)
        produkty = []
        selektory = [
            ".product", ".item", "[data-product]",   # běžné e-shopy
            "article", ".card",                       # obecné
        ]

        for selektor in selektory:
            prvky = await page.query_selector_all(selektor)
            if prvky:
                for prvek in prvky[:5]:
                    nazev_el = await prvek.query_selector("h2, h3, .title, .name")
                    cena_el  = await prvek.query_selector(".price, .cena, [data-price]")
                    nazev = (await nazev_el.text_content()).strip() if nazev_el else ""
                    cena  = (await cena_el.text_content()).strip()  if cena_el  else ""
                    if nazev:
                        produkty.append({"nazev": nazev[:60], "cena": cena})
                break

        if not produkty:
            # Fallback: extrahuj všechny texty jako "produkty" pro demo
            h_tags = await page.query_selector_all("h1, h2")
            for h in h_tags[:3]:
                text = (await h.text_content()).strip()
                if text:
                    produkty.append({"nazev": text, "cena": "N/A (demo)"})

        print(f"  URL: {url}")
        print(f"  Titulek: {titulek}")
        print(f"  Nalezeno produktů: {len(produkty)}")
        for p in produkty[:3]:
            print(f"    {p['nazev'][:40]:<42} {p['cena']}")

        await browser.close()
        return produkty

if PLAYWRIGHT_OK:
    asyncio.run(scrape_ceny("https://example.com"))
else:
    print("Kód scraperu (spustitelný po instalaci):")
    print(textwrap.dedent("""\
        async def scrape_ceny(url):
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()
                await page.goto(url)
                produkty = []
                for prvek in await page.query_selector_all(".product"):
                    nazev = await prvek.query_selector(".name")
                    cena  = await prvek.query_selector(".price")
                    produkty.append({
                        "nazev": await nazev.text_content(),
                        "cena":  await cena.text_content(),
                    })
                return produkty
    """))


# 2. E2E test pro FastAPI aplikaci
print("\n=== 2. E2E test pro FastAPI (server + Playwright) ===\n")

FASTAPI_TEST_KOD = '''\
# test_api_e2e.py
# Spuštění: pytest test_api_e2e.py -v
# Vyžaduje: pip install fastapi uvicorn playwright pytest

import pytest
import subprocess
import time
import requests
from playwright.sync_api import Page, sync_playwright

# Fixture: spustí FastAPI server
@pytest.fixture(scope="session", autouse=True)
def api_server():
    """Spustí FastAPI server pro testy."""
    proc = subprocess.Popen(
        ["uvicorn", "main:app", "--port", "8001", "--host", "127.0.0.1"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    # Počkej na start
    for _ in range(20):
        try:
            requests.get("http://127.0.0.1:8001/", timeout=1)
            break
        except Exception:
            time.sleep(0.5)
    yield
    proc.terminate()

BASE_URL = "http://127.0.0.1:8001"

def test_hlavni_stranka(page: Page):
    """Test hlavní stránky."""
    page.goto(BASE_URL)
    expect(page).to_have_title(re.compile("FastAPI"))

def test_api_docs(page: Page):
    """Swagger UI je dostupné."""
    page.goto(f"{BASE_URL}/docs")
    expect(page.locator("h2")).to_contain_text("FastAPI")

def test_studenti_api(page: Page):
    """GET /studenti vrátí JSON seznam."""
    page.goto(f"{BASE_URL}/studenti")
    content = page.locator("pre, body").text_content()
    assert "[" in content or "{" in content   # JSON odpověď

# Alternativa: přímé API testy bez prohlížeče
def test_studenti_direct():
    resp = requests.get(f"{BASE_URL}/studenti")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)

def test_vytvor_studenta():
    resp = requests.post(f"{BASE_URL}/studenti",
        json={"jmeno": "Test Student", "vek": 20})
    assert resp.status_code in (200, 201)
    student = resp.json()
    assert student["jmeno"] == "Test Student"
'''
print(FASTAPI_TEST_KOD)


# 3. GitHub Actions konfigurace pro Playwright
print("\n=== 3. Playwright v GitHub Actions ===\n")

GH_ACTIONS = textwrap.dedent("""\
    # .github/workflows/playwright.yml
    name: Playwright E2E Tests

    on:
      push:
        branches: [main, develop]
      pull_request:
        branches: [main]

    jobs:
      e2e-tests:
        runs-on: ubuntu-latest
        timeout-minutes: 30

        steps:
          - uses: actions/checkout@v4

          - uses: actions/setup-python@v5
            with:
              python-version: "3.12"

          - name: Instalace závislostí
            run: |
              pip install playwright pytest pytest-playwright fastapi uvicorn requests
              playwright install chromium --with-deps   # <-- klíčový příkaz

          - name: Spuštění E2E testů
            run: pytest test_api_e2e.py -v --screenshot=on --video=on

          - name: Nahrání artefaktů při selhání
            if: failure()
            uses: actions/upload-artifact@v4
            with:
              name: playwright-report
              path: |
                test-results/
                screenshots/
""")
print(GH_ACTIONS)

print("Shrnutí:")
print("  1. scrape_ceny() – async scraper s Playwright (CSS selektory)")
print("  2. E2E test pro FastAPI – server fixture + Playwright assertions")
print("  3. GitHub Actions s 'playwright install --with-deps'")
