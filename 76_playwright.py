"""
LEKCE 76: Playwright – webová automatizace a testování
========================================================
pip install playwright
playwright install chromium

Playwright = moderní nástroj pro ovládání prohlížeče.
Selenium je starší alternativa, Playwright je rychlejší a spolehlivější.

Použití:
  - End-to-end testování webových aplikací
  - Web scraping stránek vyžadujících JavaScript
  - Automatizace opakujících se úkolů v prohlížeči
  - Screenshot a PDF generování

Playwright podporuje: Chromium, Firefox, WebKit (Safari)
"""

import subprocess
import sys
import asyncio
import textwrap
from pathlib import Path

# ── Zkontroluj dostupnost ─────────────────────────────────────
def playwright_dostupny() -> bool:
    try:
        import playwright
        return True
    except ImportError:
        return False

if not playwright_dostupny():
    print("Playwright není nainstalován.")
    print("Spusť: pip install playwright && playwright install chromium")
    print("\nUkazuji kód – po instalaci spusť znovu.\n")

# ══════════════════════════════════════════════════════════════
# ČÁST 1: SYNCHRONNÍ API (jednodušší)
# ══════════════════════════════════════════════════════════════

print("=== Playwright – synchronní API ===\n")

SYNC_KOD = '''\
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    # Spusť prohlížeč (headless=True = bez okna)
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()

    # Otevři stránku
    page.goto("https://example.com")
    print(page.title())                   # "Example Domain"

    # Čtení textu
    heading = page.locator("h1").text_content()
    print(heading)                        # "Example Domain"

    # Screenshot
    page.screenshot(path="screenshot.png")

    # PDF (jen Chromium)
    page.pdf(path="stranka.pdf")

    browser.close()
'''
print(SYNC_KOD)

# ══════════════════════════════════════════════════════════════
# ČÁST 2: ASYNC API (doporučeno pro scraping)
# ══════════════════════════════════════════════════════════════

print("=== Async Playwright ===\n")

ASYNC_SCRAPING = '''\
from playwright.async_api import async_playwright
import asyncio

async def scrape_github_trending():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        # Nastav user agent (vypadáš jako normální prohlížeč)
        await page.set_extra_http_headers({
            "User-Agent": "Mozilla/5.0 (compatible; PythonBot/1.0)"
        })

        await page.goto("https://github.com/trending/python")

        # Počkej na načtení obsahu
        await page.wait_for_selector("article.Box-row")

        # Extrahuj repozitáře
        repos = await page.query_selector_all("article.Box-row")
        vysledky = []

        for repo in repos[:5]:
            nazev_el = await repo.query_selector("h2 a")
            popis_el = await repo.query_selector("p.col-9")

            if nazev_el:
                nazev = (await nazev_el.text_content()).strip().replace("\\n", "").strip()
                popis = ""
                if popis_el:
                    popis = (await popis_el.text_content()).strip()
                vysledky.append({"repo": nazev, "popis": popis[:60]})

        await browser.close()
        return vysledky

# repos = asyncio.run(scrape_github_trending())
# for r in repos:
#     print(f"  {r[\'repo\']}: {r[\'popis\']}")
'''
print(ASYNC_SCRAPING)

# ══════════════════════════════════════════════════════════════
# ČÁST 3: E2E TESTOVÁNÍ
# ══════════════════════════════════════════════════════════════

print("=== E2E testování ===\n")

E2E_TEST = '''\
# test_web.py – spusť: pytest test_web.py
import pytest
from playwright.sync_api import Page, expect

@pytest.fixture(scope="session")
def browser_context_args():
    return {"viewport": {"width": 1280, "height": 720}}

def test_titulka(page: Page):
    page.goto("https://example.com")
    expect(page).to_have_title("Example Domain")

def test_odkaz_existuje(page: Page):
    page.goto("https://example.com")
    odkaz = page.get_by_text("More information")
    expect(odkaz).to_be_visible()

def test_prihlaseni(page: Page):
    page.goto("https://my-app.example.com/login")

    # Vyplň formulář
    page.fill("#email",    "test@example.com")
    page.fill("#password", "tajneheslo")
    page.click("button[type=submit]")

    # Počkej na přesměrování
    page.wait_for_url("**/dashboard")
    expect(page.locator("h1")).to_contain_text("Vítej")

def test_formular(page: Page):
    page.goto("https://my-app.example.com/form")

    page.fill("[name=jmeno]", "Míša")
    page.select_option("[name=predmet]", "python")
    page.check("[name=souhlas]")
    page.click("text=Odeslat")

    # Ověř potvrzení
    expect(page.locator(".success-message")).to_be_visible()
    expect(page.locator(".success-message")).to_contain_text("Odesláno")

# Spuštění: pytest test_web.py --browser chromium -v
# Spuštění s viditelným prohlížečem: pytest test_web.py --headed
# Screenshot při selhání: pytest test_web.py --screenshot on
'''
print(E2E_TEST)

# ══════════════════════════════════════════════════════════════
# ČÁST 4: POKROČILÉ FUNKCE
# ══════════════════════════════════════════════════════════════

print("=== Pokročilé funkce ===\n")

POKROCILE = '''\
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(
        # Emuluj mobilní zařízení
        **p.devices["iPhone 13"],
        # Nastav jazyk a timezone
        locale="cs-CZ",
        timezone_id="Europe/Prague",
    )
    page = context.new_page()

    # ── Zachycení síťových požadavků ──────────────────────────
    api_volani = []

    def on_request(request):
        if "api" in request.url:
            api_volani.append({"url": request.url, "metoda": request.method})

    page.on("request", on_request)
    page.goto("https://my-app.example.com")
    print(f"API volání: {api_volani}")

    # ── Mock API odpovědi ──────────────────────────────────────
    page.route("**/api/users", lambda route: route.fulfill(
        status=200,
        content_type="application/json",
        body=\'[{"id": 1, "name": "Test User"}]\',
    ))

    # ── Čekání na podmínky ────────────────────────────────────
    page.goto("https://my-app.example.com/loading")
    page.wait_for_selector(".loaded", timeout=10_000)   # max 10 sekund
    page.wait_for_load_state("networkidle")              # čekej dokud není ticho

    # ── Spuštění vlastního JS ─────────────────────────────────
    vysledek = page.evaluate("""
        () => ({
            url: window.location.href,
            cookies: document.cookie,
            localStorage: Object.keys(localStorage),
        })
    """)
    print(vysledek)

    # ── Drag & Drop ───────────────────────────────────────────
    page.drag_and_drop("#source", "#target")

    # ── Upload souboru ────────────────────────────────────────
    page.set_input_files("input[type=file]", "data.csv")

    browser.close()
'''
print(POKROCILE)

# ══════════════════════════════════════════════════════════════
# ČÁST 5: Skutečný spustitelný demo (pokud Playwright dostupný)
# ══════════════════════════════════════════════════════════════

if playwright_dostupny():
    print("=== Spouštím live demo ===\n")

    async def demo():
        from playwright.async_api import async_playwright

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page    = await browser.new_page()

            await page.goto("https://example.com")
            titulek = await page.title()
            nadpis  = await page.locator("h1").text_content()
            odstavec = await page.locator("p").first.text_content()

            print(f"  URL:     {page.url}")
            print(f"  Titulek: {titulek}")
            print(f"  H1:      {nadpis}")
            print(f"  Obsah:   {odstavec[:80]}...")

            # Screenshot
            await page.screenshot(path="demo_screenshot.png")
            print(f"  Screenshot uložen: demo_screenshot.png")

            await browser.close()

    asyncio.run(demo())
    Path("demo_screenshot.png").unlink(missing_ok=True)
else:
    print("  [Demo přeskočen – Playwright není nainstalován]")

print("""
=== Playwright vs Selenium ===

              Playwright    Selenium
  Rychlost    ●●●●●         ●●●
  Auto-wait   ✓ (built-in)  ✗ (ruční)
  Async       ✓             ✗
  Network mock ✓            ✗
  Multi-tab   ✓             ✗
  Mobile emu  ✓             ~
  Instalace   pip + 1 cmd   pip + driver

Doporučení: Playwright pro nové projekty, Selenium pro legacy.
""")

# TVOJE ÚLOHA:
# 1. Napiš scraper který stáhne ceny z e-shopu (použij example.com jako dummy).
# 2. Napiš E2E test pro lekci 56 (FastAPI) – spusť server a testuj /studenti.
# 3. Přidej Playwright do GitHub Actions CI (playwright install --with-deps).
