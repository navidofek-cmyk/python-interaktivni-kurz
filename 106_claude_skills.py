"""
LEKCE 106: SKILL.md – Skills pro Claude Code
==============================================
Nevyžaduje pip install.

Co je skill:
  Soubor s instrukcemi který Claude Code načte a použije
  při práci v tvém projektu. Skills rozšiřují co Claude umí.

Kde žijí skills:
  .claude/skills/        ← globální (pro všechny projekty)
  projekt/.claude/skills/ ← projektové (jen pro tento projekt)

Kdy Claude skill načte (progressive disclosure):
  Uživatel napíše: /code-review nebo "udělej code review"
  → Claude najde skill soubor a řídí se jeho instrukcemi

Formát skill souboru:
  ---
  name: code-review
  description: Dělá code review Python kódu
  triggers: ["code review", "zreviduj kód", "/review"]
  ---
  # Instrukce
  ...

Spuštění: python3 106_claude_skills.py
"""

import os, json, re, textwrap
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional

# ══════════════════════════════════════════════════════════════════
# ČÁST 1: FORMÁT SKILL.md
# ══════════════════════════════════════════════════════════════════

print("=" * 60)
print("ČÁST 1: Formát SKILL.md souboru")
print("=" * 60)

print("""
Skill soubor je Markdown soubor s YAML frontmatter.

Struktura:
─────────────────────────────────
---
name: nazev-skillu
description: Krátký popis co skill dělá (1 věta)
triggers:
  - "přesná fráze která skill spustí"
  - "/slash-command"
version: 1.0
author: Tvoje jméno
---

# Instrukce pro Claude

## Co dělat
- Bod 1
- Bod 2

## Co nedělat
- Nezakazuj nic důležitého

## Formát výstupu
Popis požadovaného výstupu.

## Příklady
<příklad vstupu>
→ <příklad výstupu>
─────────────────────────────────

Best practices:
  • Stručnost: skill by měl být < 200 řádků
  • Jednoznačnost: každá instrukce má jeden výklad
  • Příklady: ukaž co chceš, ne jen popiš
  • Triggery: specifické frázování = méně false positives
""")

# ══════════════════════════════════════════════════════════════════
# ČÁST 2: PARSER SKILL.MD
# ══════════════════════════════════════════════════════════════════

print("=" * 60)
print("ČÁST 2: Parser SKILL.md souborů")
print("=" * 60)

@dataclass
class Skill:
    name: str
    description: str
    triggers: list[str]
    instrukce: str
    version: str = "1.0"
    author: str = ""
    soubor: Optional[Path] = None

    def matches(self, user_input: str) -> bool:
        """Zkontroluje, zda uživatelský vstup aktivuje skill."""
        vstup = user_input.lower()
        return any(
            trigger.lower().strip("/") in vstup or vstup.startswith(trigger.lower())
            for trigger in self.triggers
        )

    def system_prompt_addition(self) -> str:
        """Vrátí část system promptu pro tento skill."""
        return f"""
[SKILL: {self.name}]
{self.instrukce}
[/SKILL]
""".strip()

def parsuj_skill_md(obsah: str, soubor: Optional[Path] = None) -> Skill:
    """Parsuje SKILL.md soubor s YAML frontmatter."""
    # Extrahuj frontmatter
    fm_match = re.match(r'^---\s*\n(.*?)\n---\s*\n', obsah, re.DOTALL)
    if not fm_match:
        raise ValueError("Chybí YAML frontmatter (--- ... ---)")

    fm_text = fm_match.group(1)
    instrukce = obsah[fm_match.end():].strip()

    # Jednoduchý YAML parser (bez závislosti)
    fm = {}
    current_list_key = None
    for radek in fm_text.split('\n'):
        # Seznam
        if radek.strip().startswith('- '):
            if current_list_key:
                fm[current_list_key].append(radek.strip()[2:].strip().strip('"\''))
            continue
        # Klíč: hodnota
        if ':' in radek:
            k, _, v = radek.partition(':')
            k = k.strip()
            v = v.strip().strip('"\'')
            if v:
                fm[k] = v
                current_list_key = None
            else:
                fm[k] = []
                current_list_key = k

    return Skill(
        name=fm.get('name', 'unnamed'),
        description=fm.get('description', ''),
        triggers=fm.get('triggers', []),
        instrukce=instrukce,
        version=fm.get('version', '1.0'),
        author=fm.get('author', ''),
        soubor=soubor,
    )

# ══════════════════════════════════════════════════════════════════
# ČÁST 3: DEFINICE SKILLS
# ══════════════════════════════════════════════════════════════════

print("\n" + "=" * 60)
print("ČÁST 3: Kompletní skill soubory")
print("=" * 60)

# --- Skill 1: Code Review ---
CODE_REVIEW_MD = '''---
name: code-review
description: Provádí důkladné code review Python kódu
triggers:
  - "code review"
  - "zreviduj kód"
  - "review"
  - "/review"
version: 1.0
author: Python kurz
---

# Code Review – Instrukce

## Co kontrolovat (v tomto pořadí)
1. **Správnost**: Dělá kód to, co má?
2. **Bezpečnost**: SQL injection, path traversal, neošetřené vstupy?
3. **Výkon**: Zbytečné smyčky, O(n²) kde stačí O(n)?
4. **Čitelnost**: Jasné názvy, docstringy, type hinty?
5. **Testy**: Je kód testovatelný? Chybí unit testy?

## Formát výstupu
```
## Code Review

**Celkové hodnocení**: ✓ Dobrý / ⚠ Potřebuje úpravy / ✗ Závažné problémy

### Závažné problémy (blokující)
- [řádek X] Popis problému → Navrhované řešení

### Menší problémy (doporučení)
- [řádek X] Popis → Řešení

### Co je dobře
- Pozitivní věci

### Navrhovaný kód
```python
# opravená verze
```
```

## Pravidla
- Vždy uveď číslo řádku
- Vysvětli PROČ je to problém, ne jen co
- Navrhni konkrétní opravu
- Max 5 komentářů v sekci "menší problémy" (prioritizuj)
- Pokud kód vyžaduje context (import, volající funkce), zeptej se
'''

# --- Skill 2: Generování testů ---
GENERATE_TESTS_MD = '''---
name: generate-tests
description: Generuje pytest unit testy pro Python funkce
triggers:
  - "generuj testy"
  - "napiš testy"
  - "create tests"
  - "/tests"
version: 1.0
author: Python kurz
---

# Generování testů – Instrukce

## Strategie testování
1. **Happy path**: Normální vstup → očekávaný výstup
2. **Edge cases**: Prázdný vstup, nula, None, prázdný list
3. **Error cases**: Neplatný typ, out-of-range, výjimky

## Formát výstupu
```python
import pytest
from modul import funkce  # přizpůsob importu

class TestNazevFunkce:
    """Testy pro funkce_nazev."""

    def test_zakladni_pripad(self):
        """Popis co testujeme."""
        assert funkce(vstup) == ocekavany_vystup

    def test_edge_case_prazdny(self):
        assert funkce([]) == []

    @pytest.mark.parametrize("vstup,ocekavany", [
        (1, 1),
        (2, 4),
        (3, 9),
    ])
    def test_vice_hodnot(self, vstup, ocekavany):
        assert funkce(vstup) == ocekavany

    def test_vyjimka(self):
        with pytest.raises(ValueError):
            funkce(-1)
```

## Pravidla
- Jeden test = jedna věc testována
- Názvy testů: `test_co_kdyz_vstup_je_X`
- Vždy přidej docstring k test třídě
- Použij @pytest.mark.parametrize pro více vstupů
- Mock external dependencies (API, soubory, DB)
- Cílová coverage: 80%+ pro kritické funkce
'''

# --- Skill 3: Refactoring ---
REFACTORING_MD = '''---
name: refactoring
description: Refaktoruje Python kód pro lepší čitelnost a výkon
triggers:
  - "refaktoruj"
  - "refactor"
  - "vylepši kód"
  - "/refactor"
version: 1.0
author: Python kurz
---

# Refactoring – Instrukce

## Prioritní refaktoringy
1. **Extrakce funkcí**: Funkce > 20 řádků → rozděl
2. **Pojmenování**: `x`, `tmp`, `data` → popisné názvy
3. **Type hinty**: Přidej ke všem parametrům a return hodnotám
4. **List comprehensions**: `for` smyčky → komprehenze kde to dává smysl
5. **Konstanty**: Magic numbers (`42`, `"admin"`) → pojmenované konstanty
6. **Dataclasses**: Dicts s pevnou strukturou → `@dataclass`
7. **f-strings**: `"Hello " + name` → `f"Hello {name}"`

## Formát výstupu
```
## Refactoring Report

### Před:
```python
# původní kód
```

### Po:
```python
# refaktorovaný kód
```

### Vysvětlení změn:
- Změna 1: proč
- Změna 2: proč

### Zachovaná funkčnost:
✓ Vstup/výstup je identický
✓ Chování při chybách je stejné
```

## Pravidla
- Zachovej původní rozhraní (signaturu funkcí)
- Neměň logiku, jen strukturu
- Přidej typy ale neměň je (str → int = chyba)
- Pokud si nejsi jistý – zeptej se, nerefaktoruj "naslepo"
- Navrhni testy které ověří zachování funkčnosti
'''

# Parsování a demonstrace
print("\nParsování skill souborů:")
skills_data = [
    ("code-review.md", CODE_REVIEW_MD),
    ("generate-tests.md", GENERATE_TESTS_MD),
    ("refactoring.md", REFACTORING_MD),
]

parsed_skills: list[Skill] = []
for nazev, obsah in skills_data:
    skill = parsuj_skill_md(obsah, Path(f".claude/skills/{nazev}"))
    parsed_skills.append(skill)
    print(f"\n  Skill: {skill.name}")
    print(f"    Popis: {skill.description}")
    print(f"    Triggery: {skill.triggers}")
    print(f"    Instrukce: {len(skill.instrukce)} znaků")

# ══════════════════════════════════════════════════════════════════
# ČÁST 4: SKILL MANAGER – ROUTING
# ══════════════════════════════════════════════════════════════════

print("\n" + "=" * 60)
print("ČÁST 4: Skill Manager – kdy který skill použít")
print("=" * 60)

class SkillManager:
    """Načítá a routuje skills pro Claude Code."""

    def __init__(self, skills_dir: Optional[Path] = None):
        self.skills: list[Skill] = []
        if skills_dir and skills_dir.exists():
            self._nactSoubory(skills_dir)

    def _nactSoubory(self, skills_dir: Path) -> None:
        for soubor in skills_dir.glob("*.md"):
            try:
                skill = parsuj_skill_md(soubor.read_text(encoding='utf-8'), soubor)
                self.skills.append(skill)
            except Exception as e:
                print(f"  Chyba parsování {soubor.name}: {e}")

    def pridej(self, skill: Skill) -> None:
        self.skills.append(skill)

    def najdi_skill(self, user_input: str) -> Optional[Skill]:
        """Vrátí první skill který odpovídá uživatelskému vstupu."""
        for skill in self.skills:
            if skill.matches(user_input):
                return skill
        return None

    def vsechny_triggery(self) -> dict[str, list[str]]:
        return {s.name: s.triggers for s in self.skills}

sm = SkillManager()
for skill in parsed_skills:
    sm.pridej(skill)

print("\nVšechny triggery:")
for name, triggers in sm.vsechny_triggery().items():
    print(f"  {name}: {triggers}")

# Test routingu
print("\nRouting testů:")
testovaci_vstupy = [
    "Prosím udělej code review tohoto souboru",
    "Napiš testy pro funkci factorial()",
    "/review main.py",
    "Refaktoruj tuto třídu",
    "/tests utils.py",
    "Jak se instaluje numpy?",  # bez matchujícího skillu
]

for vstup in testovaci_vstupy:
    skill = sm.najdi_skill(vstup)
    if skill:
        print(f"  ✓ {repr(vstup)[:45]:<47} → {skill.name}")
    else:
        print(f"  – {repr(vstup)[:45]:<47} → (žádný skill, normální odpověď)")

# ══════════════════════════════════════════════════════════════════
# ČÁST 5: VYTVOŘENÍ SKILL SOUBORŮ
# ══════════════════════════════════════════════════════════════════

print("\n" + "=" * 60)
print("ČÁST 5: Vytvoření skill souborů v projektu")
print("=" * 60)

def vytvor_skills_strukturu(base_dir: Path) -> None:
    """Vytvoří .claude/skills/ adresář a soubory."""
    skills_dir = base_dir / ".claude" / "skills"
    skills_dir.mkdir(parents=True, exist_ok=True)

    soubory = [
        ("code-review.md", CODE_REVIEW_MD),
        ("generate-tests.md", GENERATE_TESTS_MD),
        ("refactoring.md", REFACTORING_MD),
    ]

    for nazev, obsah in soubory:
        cesta = skills_dir / nazev
        cesta.write_text(obsah.lstrip(), encoding='utf-8')
        print(f"  Vytvořen: {cesta}")

    print(f"\n  Skills jsou připraveny v: {skills_dir}")
    print("  Claude Code je automaticky načte při práci v projektu.")

projekt_dir = Path("/home/ivand/projects/learning_python/interactive")
print(f"\nVytvářím skills pro projekt: {projekt_dir}")
vytvor_skills_strukturu(projekt_dir)

# ══════════════════════════════════════════════════════════════════
# ČÁST 6: PROGRESSIVE DISCLOSURE
# ══════════════════════════════════════════════════════════════════

print("\n" + "=" * 60)
print("ČÁST 6: Progressive Disclosure – jak Claude skills načítá")
print("=" * 60)

print("""
Progressive disclosure = Claude nenačítá všechny skills naráz.
Načítá je na základě:
  1. Explicitní volání: uživatel napíše trigger
  2. Kontext: typ souboru, obsah konverzace
  3. CLAUDE.md: skills explicitně zmíněné v projektu

Proč ne "načti vše hned":
  → Skills zabírají tokeny v kontextovém okně
  → Příliš mnoho instrukcí = zmatenost, konflikty
  → Relevantní skill = lepší výsledek

Doporučená struktura CLAUDE.md:
─────────────────────────────────
# Projekt: Python kurz

## Dostupné skills
- `/review` → .claude/skills/code-review.md
- `/tests`  → .claude/skills/generate-tests.md
- `/refactor` → .claude/skills/refactoring.md

## Konvence
- Python 3.12+
- Type hinty povinné
- Tests: pytest
─────────────────────────────────
""")

# SHRNUTÍ
print("=" * 60)
print("SHRNUTÍ")
print("=" * 60)
print("""
  Skill soubory:
    Umístění:   .claude/skills/*.md
    Formát:     YAML frontmatter + Markdown instrukce
    Triggery:   Fráze nebo /slash-command

  Dobré skills:
    • Krátké (< 200 řádků)
    • Specifické triggery (méně false positives)
    • Příklady vstupu a výstupu
    • Jasný formát výstupu

  Soubory vytvořeny:
    .claude/skills/code-review.md
    .claude/skills/generate-tests.md
    .claude/skills/refactoring.md
""")

# ══════════════════════════════════════════════════════════════════
# TVOJE ÚLOHA
# ══════════════════════════════════════════════════════════════════
print("""
╔══════════════════════════════════════════════════════════════╗
║  TVOJE ÚLOHA                                                 ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  1. Napiš skill soubor `explain-code.md` pro vysvětlení     ║
║     kódu začátečníkům. Triggery: "vysvětli", "/explain".   ║
║     Instrukce: používej analogie, žádný jargon.             ║
║                                                              ║
║  2. Přidej do SkillManager metodu `konflikt_check()` která  ║
║     najde skills se stejnými triggery a upozorní na ně.     ║
║                                                              ║
║  3. Přidej do parsuju_skill_md() validaci: pokud skill      ║
║     nemá žádné triggery, vyhoď ValueError s popisem.        ║
║                                                              ║
║  4. BONUS: Implementuj `skill_priorita(user_input, skills)` ║
║     která vrátí skills seřazené podle počtu matchujících    ║
║     slov z user_input (lepší routing než první match).      ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
""")
