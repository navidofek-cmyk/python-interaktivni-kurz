"""Řešení – Lekce 75: LLM v CI/CD pipeline"""

# vyžaduje: pip install anthropic

import os
import sys
import json
import hashlib
import subprocess
import textwrap
from pathlib import Path

ANTHROPIC_KEY = os.getenv("ANTHROPIC_API_KEY", "")


# Sdílené helper funkce (z originální lekce)
def git(*args) -> str:
    r = subprocess.run(["git"] + list(args), capture_output=True, text=True)
    return r.stdout.strip()

def ziskej_diff(base: str = "HEAD~1", head: str = "HEAD",
                max_radku: int = 400) -> str:
    diff = git("diff", f"{base}..{head}", "--unified=3",
               "--diff-filter=ACMR", "--", "*.py")
    radky = diff.splitlines()
    if len(radky) > max_radku:
        radky = radky[:max_radku]
        radky.append(f"\n... (diff zkrácen na {max_radku} řádků)")
    return "\n".join(radky)

def ziskej_commity(base: str = "HEAD~5") -> str:
    return git("log", f"{base}..HEAD", "--oneline", "--no-merges")


# 1. Akce "test_gen" – Claude navrhne unit testy pro změněné funkce
print("=== 1. test_gen – generování unit testů ===\n")

def claude_test_gen(diff: str) -> str:
    """Claude navrhne unit testy pro změněné Python funkce."""
    if not ANTHROPIC_KEY:
        # Simulace bez API klíče
        return textwrap.dedent("""\
            ## Navrhované testy

            ```python
            import pytest

            def test_secti_zakladni():
                assert secti(2, 3) == 5

            def test_secti_zaporne():
                assert secti(-1, 1) == 0

            def test_secti_nula():
                assert secti(0, 0) == 0

            def test_secti_velka_cisla():
                assert secti(1_000_000, 2_000_000) == 3_000_000
            ```

            [Simulace – nastav ANTHROPIC_API_KEY pro reálné testy]
        """)

    import anthropic
    client = anthropic.Anthropic()
    zprava = client.messages.create(
        model="claude-opus-4-7",
        max_tokens=1024,
        system="""\
Jsi Python expert. Z git diffu extrahuj nové/změněné funkce a navrhni
pytest unit testy které pokryjí:
- Základní případ (happy path)
- Hraniční hodnoty (0, None, prázdný seznam)
- Chybové stavy (výjimky)
- Edge cases

Odpověz pouze kódem v ```python bloku.
Piš stručně, max 20 testů.""",
        messages=[{
            "role": "user",
            "content": f"Git diff:\n```diff\n{diff}\n```\n\nNapiš pytest testy.",
        }],
    )
    return zprava.content[0].text

# Ukázkový diff pro generování testů
TEST_DIFF = """\
+def secti(a: int, b: int) -> int:
+    \"\"\"Sečte dvě čísla.\"\"\"
+    return a + b
+
+def vydel(a: float, b: float) -> float:
+    \"\"\"Vydělí a / b. Vyvolá ValueError pro b=0.\"\"\"
+    if b == 0:
+        raise ValueError("Dělení nulou není povoleno")
+    return a / b
"""

print("Vstupní diff:")
print(TEST_DIFF)
print("Navrhnuté testy:")
print(claude_test_gen(TEST_DIFF))


# 2. Threshold: rozdělení velkého diffu na části
print("\n=== 2. Rozdělení velkého diffu (> 500 řádků) ===\n")

def rozded_diff_na_casti(diff: str, max_radku: int = 500) -> list[str]:
    """Rozdělí velký diff na části podle souborů."""
    radky = diff.splitlines()
    if len(radky) <= max_radku:
        return [diff]

    casti = []
    aktualni_cast = []
    aktualni_soubor = None

    for radek in radky:
        if radek.startswith("diff --git"):
            if aktualni_cast and len(aktualni_cast) >= max_radku // 4:
                casti.append("\n".join(aktualni_cast))
                aktualni_cast = []
            aktualni_soubor = radek
        aktualni_cast.append(radek)

        if len(aktualni_cast) >= max_radku:
            casti.append("\n".join(aktualni_cast))
            aktualni_cast = []

    if aktualni_cast:
        casti.append("\n".join(aktualni_cast))

    return casti if casti else [diff]

def claude_review_velky_diff(diff: str, typ: str = "review") -> str:
    """Zpracuje velký diff v částech a sloučí výsledky."""
    casti = rozded_diff_na_casti(diff, max_radku=300)
    print(f"  Diff rozdělen na {len(casti)} části")

    if len(casti) == 1:
        return f"[Simulace] Review pro diff {len(diff.splitlines())} řádků"

    vysledky = []
    for i, cast in enumerate(casti, 1):
        print(f"  Zpracovávám část {i}/{len(casti)} ({len(cast.splitlines())} řádků)...")
        if ANTHROPIC_KEY:
            import anthropic
            client = anthropic.Anthropic()
            r = client.messages.create(
                model="claude-opus-4-7",
                max_tokens=512,
                system="Stručné code review. Max 5 bullet pointů.",
                messages=[{"role": "user", "content": f"```diff\n{cast}\n```"}],
            )
            vysledky.append(f"### Část {i}\n{r.content[0].text}")
        else:
            vysledky.append(f"### Část {i}\n[Simulace části {i}]")

    return "\n\n".join(vysledky)

# Generuj velký testovací diff
velky_diff_radky = []
for i in range(600):
    velky_diff_radky.append(f"+    radek_{i:04d} = '{i}'")
velky_diff = "\n".join(velky_diff_radky)

print(f"Velký diff: {len(velky_diff.splitlines())} řádků")
vysledek = claude_review_velky_diff(velky_diff)
print(f"Výsledek: {vysledek[:200]}...")


# 3. Cache výsledků s git commit hash jako klíčem
print("\n=== 3. Cache výsledků (commit hash jako klíč) ===\n")

CACHE_DIR = Path(f"/tmp/ci_cache_{os.getpid()}")
CACHE_DIR.mkdir(exist_ok=True)

def ziskej_commit_hash() -> str:
    """Vrátí SHA aktuálního HEAD commitu (nebo mock)."""
    try:
        h = git("rev-parse", "HEAD")
        return h if h else hashlib.md5(b"mock").hexdigest()
    except Exception:
        return hashlib.md5(b"mock-commit").hexdigest()

def review_s_cache(diff: str, typ: str = "review") -> tuple[str, bool]:
    """Vrátí (výsledek, z_cache). Cachuje podle hash(diff) + typ."""
    klic   = hashlib.sha256(f"{diff}{typ}".encode()).hexdigest()[:16]
    soubor = CACHE_DIR / f"{klic}.json"

    if soubor.exists():
        data = json.loads(soubor.read_text())
        return data["vysledek"], True

    # Zavolej API (nebo simulaci)
    vysledek = f"[Review výsledek pro {klic[:8]}...]"
    if ANTHROPIC_KEY:
        vysledek = claude_review_velky_diff(diff, typ)

    soubor.write_text(json.dumps({"vysledek": vysledek, "klic": klic}))
    return vysledek, False

# Test cache
diff_test = "+def funkce(): return 42\n"
r1, z_cache1 = review_s_cache(diff_test, "review")
r2, z_cache2 = review_s_cache(diff_test, "review")  # stejný diff = cache HIT
r3, z_cache3 = review_s_cache("+def jina(): return 0\n", "review")  # jiný diff

print(f"  1. volání: z_cache={z_cache1}  výsledek: {r1[:40]}...")
print(f"  2. volání: z_cache={z_cache2}  (stejný diff – ušetřeno API volání)")
print(f"  3. volání: z_cache={z_cache3}  (nový diff)")

# Úklid
import shutil
shutil.rmtree(CACHE_DIR, ignore_errors=True)

print("\n=== Shrnutí ===")
print("  1. claude_test_gen()    – automatické generování unit testů z diffu")
print("  2. rozded_diff_na_casti() – rozdělení >500 řádků na zpracovatelné části")
print("  3. review_s_cache()     – SHA hash diffu jako klíč, 0 duplicitních API volání")
