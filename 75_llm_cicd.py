"""
LEKCE 75: LLM v CI/CD pipeline
================================
Praktické použití Claude v GitHub Actions:

  PR review    – Claude zkontroluje každý pull request
  PR summary   – automatický popis změn z git diff
  Test gen     – navrhne chybějící testy
  Changelog    – vygeneruje release notes z commitů
  Security     – hledá bezpečnostní problémy

Princip:
  git diff → Python skript → Claude API → výstup do PR komentáře

Spuštění lokálně (simulace CI):
  ANTHROPIC_API_KEY=sk-ant-... python3 75_llm_cicd.py

Spuštění v GitHub Actions:
  viz .github/workflows/ soubory generované níže
"""

import os
import sys
import json
import subprocess
import textwrap
from pathlib import Path

ANTHROPIC_KEY = os.getenv("ANTHROPIC_API_KEY", "")

# ══════════════════════════════════════════════════════════════
# ČÁST 1: Pomocné funkce pro práci s gitem
# ══════════════════════════════════════════════════════════════

def git(*args) -> str:
    """Spustí git příkaz a vrátí výstup."""
    r = subprocess.run(["git"] + list(args), capture_output=True, text=True)
    return r.stdout.strip()

def ziskej_diff(base: str = "HEAD~1", head: str = "HEAD",
                max_radku: int = 400) -> str:
    """Vrátí git diff omezený na max_radku řádků."""
    diff = git("diff", f"{base}..{head}", "--unified=3",
               "--diff-filter=ACMR",        # jen změněné soubory (ne smazané)
               "--", "*.py", "*.ts", "*.js", "*.go", "*.rs")
    radky = diff.splitlines()
    if len(radky) > max_radku:
        radky = radky[:max_radku]
        radky.append(f"\n... (diff zkrácen na {max_radku} řádků)")
    return "\n".join(radky)

def ziskej_commity(base: str = "HEAD~5") -> str:
    """Vrátí posledních N commit zpráv."""
    return git("log", f"{base}..HEAD", "--oneline", "--no-merges")

def ziskej_zmenene_soubory() -> list[str]:
    """Vrátí seznam změněných souborů."""
    vystup = git("diff", "--name-only", "HEAD~1..HEAD")
    return [s for s in vystup.splitlines() if s]


# ══════════════════════════════════════════════════════════════
# ČÁST 2: Claude reviewer
# ══════════════════════════════════════════════════════════════

def claude_review(diff: str, typ: str = "review") -> str:
    """Pošle diff do Claude a vrátí analýzu."""
    if not ANTHROPIC_KEY:
        return "[Simulace – nastav ANTHROPIC_API_KEY pro reálný výstup]"

    import anthropic
    client = anthropic.Anthropic()

    PROMPTY = {
        "review": """\
Jsi zkušený senior Python vývojář provádějící code review.
Analyzuj tento git diff a vrať strukturovanou zpětnou vazbu.

Formát odpovědi (markdown):
## Shrnutí
Jedna věta co se změnilo.

## ✅ Co je dobré
- Silné stránky změny

## ⚠️ Problémy
- Každý problém na zvláštním řádku s vysvětlením

## 🔴 Bezpečnostní rizika
- Bezpečnostní problémy (SQL injection, secrets v kódu, atd.)
- Pokud žádné: "Žádná bezpečnostní rizika nalezena."

## 💡 Návrhy na zlepšení
- Konkrétní doporučení

Buď stručný. Zaměř se na důležité věci, ne na styl.""",

        "summary": """\
Jsi asistent který generuje popis pull requestu.
Z git diffu vytvoř stručný a jasný popis změn pro vývojáře.

Formát (markdown):
## Co se změnilo
Stručný popis (2-3 věty).

## Typ změny
[ ] Bug fix  [ ] Nová funkce  [ ] Refactoring  [ ] Dokumentace  [ ] CI/CD

## Jak testovat
Kroky jak ověřit změnu.

Piš česky, technicky přesně.""",

        "security": """\
Jsi bezpečnostní auditor. Prohledej tento kód na:
- Hardcoded secrets (API klíče, hesla, tokeny)
- SQL injection
- Command injection (os.system, subprocess bez shell=False)
- Path traversal
- Insecure deserialization
- XSS v šablonách
- Otevřená spojení bez timeoutu

Pro každý nález: soubor:řádek, závažnost (HIGH/MEDIUM/LOW), popis, jak opravit.
Pokud nic nenajdeš: "Žádné bezpečnostní problémy nenalezeny." """,
    }

    zprava = client.messages.create(
        model="claude-opus-4-7",
        max_tokens=1024,
        system=PROMPTY.get(typ, PROMPTY["review"]),
        messages=[{
            "role": "user",
            "content": f"Git diff:\n```diff\n{diff}\n```",
        }],
    )
    return zprava.content[0].text


def claude_changelog(commity: str) -> str:
    """Vygeneruje changelog z commit zpráv."""
    if not ANTHROPIC_KEY:
        return "[Simulace – nastav ANTHROPIC_API_KEY]"

    import anthropic
    client = anthropic.Anthropic()

    zprava = client.messages.create(
        model="claude-opus-4-7",
        max_tokens=512,
        system="""\
Generuješ CHANGELOG z git commit zpráv.
Seskup změny do kategorií: ✨ Nové funkce, 🐛 Opravy, ⚡ Výkon, 🔧 Interní.
Ignoruj merge commity a chore/docs commity.
Piš česky, krátce a jasně. Výstup je markdown.""",
        messages=[{
            "role": "user",
            "content": f"Commity:\n{commity}",
        }],
    )
    return zprava.content[0].text


# ══════════════════════════════════════════════════════════════
# ČÁST 3: GitHub PR komentář přes API
# ══════════════════════════════════════════════════════════════

def postni_pr_komentar(zprava: str, repo: str, pr_cislo: int,
                       token: str) -> bool:
    """Přidá komentář na GitHub PR."""
    import urllib.request

    url  = f"https://api.github.com/repos/{repo}/issues/{pr_cislo}/comments"
    data = json.dumps({"body": zprava}).encode()
    req  = urllib.request.Request(url, data=data, method="POST", headers={
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "Content-Type": "application/json",
        "X-GitHub-Api-Version": "2022-11-28",
    })
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return r.status == 201
    except Exception as e:
        print(f"Chyba při odesílání komentáře: {e}", file=sys.stderr)
        return False


# ══════════════════════════════════════════════════════════════
# ČÁST 4: Hlavní CI skript
# ══════════════════════════════════════════════════════════════

def main():
    """Hlavní logika – spouští se v CI/CD."""
    akce = os.getenv("CI_AKCE", "review")   # review / summary / security / changelog

    print(f"🤖 LLM CI/CD  |  akce={akce}")
    print("─" * 50)

    diff = ziskej_diff()
    if not diff.strip():
        print("Žádné změny v Python souborech.")
        sys.exit(0)

    soubory = ziskej_zmenene_soubory()
    print(f"Změněné soubory: {', '.join(soubory[:5])}")
    print(f"Diff: {len(diff.splitlines())} řádků\n")

    # Spusť analýzu
    if akce == "changelog":
        commity = ziskej_commity()
        vystup  = claude_changelog(commity)
    else:
        vystup = claude_review(diff, akce)

    print(vystup)

    # V CI prostředí: odešli komentář na PR
    github_token  = os.getenv("GITHUB_TOKEN", "")
    github_repo   = os.getenv("GITHUB_REPOSITORY", "")
    pr_cislo_str  = os.getenv("PR_NUMBER", "")

    if github_token and github_repo and pr_cislo_str:
        pr_cislo = int(pr_cislo_str)
        komentar = f"## 🤖 AI {akce.title()}\n\n{vystup}\n\n---\n*Generováno Claude claude-opus-4-7*"
        ok = postni_pr_komentar(komentar, github_repo, pr_cislo, github_token)
        print(f"\n{'✓ Komentář odeslán na PR #{pr_cislo}' if ok else '✗ Odeslání selhalo'}")

    # Selhání pipeline na bezpečnostní problémy
    if akce == "security" and "HIGH" in vystup:
        print("\n🔴 Nalezena HIGH bezpečnostní rizika – pipeline selhává!", file=sys.stderr)
        sys.exit(1)

    sys.exit(0)


if __name__ == "__main__":
    main()


# ══════════════════════════════════════════════════════════════
# ČÁST 5: Generuj GitHub Actions workflow soubory
# ══════════════════════════════════════════════════════════════

WORKFLOWS_DIR = Path(".github/workflows")
WORKFLOWS_DIR.mkdir(parents=True, exist_ok=True)

# ── AI code review na každý PR ────────────────────────────────
(WORKFLOWS_DIR / "ai_review.yml").write_text(textwrap.dedent("""\
    name: AI Code Review

    on:
      pull_request:
        types: [opened, synchronize]
        paths: ["**.py", "**.ts", "**.js"]

    jobs:
      review:
        runs-on: ubuntu-latest
        permissions:
          pull-requests: write   # potřeba pro komentáře

        steps:
          - uses: actions/checkout@v4
            with:
              fetch-depth: 0     # celá git historie pro diff

          - uses: actions/setup-python@v5
            with:
              python-version: "3.12"

          - run: pip install anthropic

          - name: AI Review
            env:
              ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
              GITHUB_TOKEN:      ${{ secrets.GITHUB_TOKEN }}
              GITHUB_REPOSITORY: ${{ github.repository }}
              PR_NUMBER:         ${{ github.event.pull_request.number }}
              CI_AKCE:           review
            run: python3 75_llm_cicd.py

          - name: AI Security Scan
            env:
              ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
              GITHUB_TOKEN:      ${{ secrets.GITHUB_TOKEN }}
              GITHUB_REPOSITORY: ${{ github.repository }}
              PR_NUMBER:         ${{ github.event.pull_request.number }}
              CI_AKCE:           security
            run: python3 75_llm_cicd.py
            # security scan selže pipeline pokud najde HIGH rizika
"""))
print("✓ .github/workflows/ai_review.yml")

# ── Automatický changelog na release ─────────────────────────
(WORKFLOWS_DIR / "ai_changelog.yml").write_text(textwrap.dedent("""\
    name: AI Changelog

    on:
      push:
        tags: ["v*"]   # spustí se při tagu v1.0.0, v2.3.1 atd.

    jobs:
      changelog:
        runs-on: ubuntu-latest
        permissions:
          contents: write

        steps:
          - uses: actions/checkout@v4
            with:
              fetch-depth: 0

          - uses: actions/setup-python@v5
            with:
              python-version: "3.12"

          - run: pip install anthropic

          - name: Generuj changelog
            env:
              ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
              CI_AKCE: changelog
            run: |
              python3 75_llm_cicd.py > CHANGELOG_NEW.md
              cat CHANGELOG_NEW.md

          - name: Vytvoř GitHub Release
            uses: softprops/action-gh-release@v1
            with:
              body_path: CHANGELOG_NEW.md
            env:
              GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
"""))
print("✓ .github/workflows/ai_changelog.yml")

# ── PR summary – automatický popis PR ────────────────────────
(WORKFLOWS_DIR / "ai_pr_summary.yml").write_text(textwrap.dedent("""\
    name: AI PR Summary

    on:
      pull_request:
        types: [opened]   # jen při otevření nového PR

    jobs:
      summary:
        runs-on: ubuntu-latest
        permissions:
          pull-requests: write

        steps:
          - uses: actions/checkout@v4
            with:
              fetch-depth: 0

          - uses: actions/setup-python@v5
            with:
              python-version: "3.12"

          - run: pip install anthropic

          - name: Generuj popis PR
            env:
              ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
              GITHUB_TOKEN:      ${{ secrets.GITHUB_TOKEN }}
              GITHUB_REPOSITORY: ${{ github.repository }}
              PR_NUMBER:         ${{ github.event.pull_request.number }}
              CI_AKCE:           summary
            run: python3 75_llm_cicd.py
"""))
print("✓ .github/workflows/ai_pr_summary.yml")

print("""
=== Jak nasadit ===

1. Přidej API klíč do GitHub Secrets:
   Settings → Secrets → Actions → New secret
   Jméno: ANTHROPIC_API_KEY
   Hodnota: sk-ant-...

2. Commitni tyto soubory:
   git add .github/workflows/ 75_llm_cicd.py
   git commit -m "feat: AI code review v CI/CD"
   git push

3. Otevři pull request → Claude automaticky zkontroluje kód
   a přidá komentář s review.

=== Lokální testování ===

   ANTHROPIC_API_KEY=sk-ant-... CI_AKCE=review python3 75_llm_cicd.py
   ANTHROPIC_API_KEY=sk-ant-... CI_AKCE=security python3 75_llm_cicd.py
   ANTHROPIC_API_KEY=sk-ant-... CI_AKCE=changelog python3 75_llm_cicd.py
""")

# TVOJE ÚLOHA:
# 1. Přidej akci "test_gen" – Claude navrhne unit testy pro změněné funkce.
# 2. Nastav threshold: pokud diff > 500 řádků, rozděl na části a volej API víckrát.
# 3. Přidej caching výsledků (git commit hash jako klíč) – neplatí za stejný diff dvakrát.
