"""Řešení – Lekce 106: Skills pro Claude Code

Toto je vzorové řešení úloh z lekce 106.
"""

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


# ── Pomocné třídy ze lekce ─────────────────────────────────

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
        vstup = user_input.lower()
        return any(
            trigger.lower().strip("/") in vstup or vstup.startswith(trigger.lower())
            for trigger in self.triggers
        )

    def system_prompt_addition(self) -> str:
        return f"[SKILL: {self.name}]\n{self.instrukce}\n[/SKILL]"


def parsuj_skill_md(obsah: str, soubor: Optional[Path] = None) -> Skill:
    """Parsuje SKILL.md soubor s YAML frontmatter. Vyhodí ValueError bez triggerů."""
    fm_match = re.match(r'^---\s*\n(.*?)\n---\s*\n', obsah, re.DOTALL)
    if not fm_match:
        raise ValueError("Chybí YAML frontmatter (--- ... ---)")

    fm_text = fm_match.group(1)
    instrukce = obsah[fm_match.end():].strip()

    fm: dict = {}
    current_list_key = None
    for radek in fm_text.split('\n'):
        if radek.strip().startswith('- '):
            if current_list_key:
                fm[current_list_key].append(radek.strip()[2:].strip().strip('"\''))
            continue
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

    # Validace: musí mít triggery
    triggery = fm.get('triggers', [])
    if not triggery:
        raise ValueError(
            f"Skill '{fm.get('name', '?')}' nemá žádné triggery. "
            "Přidej sekci 'triggers:' s alespoň jednou hodnotou."
        )

    return Skill(
        name=fm.get('name', 'unnamed'),
        description=fm.get('description', ''),
        triggers=triggery,
        instrukce=instrukce,
        version=fm.get('version', '1.0'),
        author=fm.get('author', ''),
        soubor=soubor,
    )


# ── Úloha 1 ────────────────────────────────────────────────
# Skill soubor explain-code.md pro vysvětlení kódu začátečníkům

EXPLAIN_CODE_MD = '''---
name: explain-code
description: Vysvětluje Python kód začátečníkům pomocí analogií bez jargonu
triggers:
  - "vysvětli"
  - "co dělá tento kód"
  - "co znamená"
  - "/explain"
version: 1.0
author: Python kurz
---

# Explain Code – Instrukce

## Cíl
Vysvětlit kód tak, aby mu rozuměl člověk bez programátorského základu.

## Pravidla
- Žádný technický jargon bez vysvětlení
- Pro každý koncept použij analogii ze skutečného světa
- Vysvětluj řádek po řádku nebo blok po bloku
- Pokud kód obsahuje chybu, upozorni na ni jednoduše

## Analogie ke konceptům
- Proměnná: "jako šanon s nálepkou – schránka s názvem"
- Funkce: "jako recept – postup který se dá opakovat"
- Smyčka: "jako montážní linka – opakuje stejnou práci"
- Podmínka: "jako semafor – rozhoduje co se stane dál"
- Seznam: "jako nákupní seznam – více věcí pohromadě"
- Třída: "jako šablona, podle které se vyrábějí objekty"

## Formát výstupu
1. Krátký popis co kód dělá (1–2 věty)
2. Vysvětlení po krocích s analogiemi
3. Co kód vrátí / vypíše

## Příklady
Vstup: `x = 5`
Výstup: "Vytvoříme šanon s nálepkou 'x' a vložíme do něj číslo 5."

Vstup: `for i in range(3): print(i)`
Výstup: "Spustíme montážní linku třikrát (0, 1, 2) a pokaždé vytiskneme číslo."
'''

print("── Úloha 1: explain-code skill ──")
skill_explain = parsuj_skill_md(EXPLAIN_CODE_MD, Path(".claude/skills/explain-code.md"))
print(f"Skill: {skill_explain.name}")
print(f"Triggery: {skill_explain.triggers}")
print(f"Popis: {skill_explain.description}")
print(f"Instrukce: {len(skill_explain.instrukce)} znaků")
print(f"Matches 'vysvětli tento kód': {skill_explain.matches('vysvětli tento kód')}")
print(f"Matches 'code review':       {skill_explain.matches('code review')}")


# ── Úloha 2 ────────────────────────────────────────────────
# SkillManager.konflikt_check() – najde skills se stejnými triggery

class SkillManager:
    """Načítá a routuje skills s detekcí konfliktů."""

    def __init__(self, skills_dir: Optional[Path] = None):
        self.skills: list[Skill] = []
        if skills_dir and skills_dir.exists():
            self._nacti_soubory(skills_dir)

    def _nacti_soubory(self, skills_dir: Path) -> None:
        for soubor in skills_dir.glob("*.md"):
            try:
                skill = parsuj_skill_md(soubor.read_text(encoding='utf-8'), soubor)
                self.skills.append(skill)
            except Exception as e:
                print(f"  Chyba parsování {soubor.name}: {e}")

    def pridej(self, skill: Skill) -> None:
        self.skills.append(skill)

    def najdi_skill(self, user_input: str) -> Optional[Skill]:
        for skill in self.skills:
            if skill.matches(user_input):
                return skill
        return None

    def vsechny_triggery(self) -> dict[str, list[str]]:
        return {s.name: s.triggers for s in self.skills}

    def konflikt_check(self) -> dict[str, list[str]]:
        """
        Najde triggery sdílené více skills.
        Vrátí dict: {trigger: [nazev_skillu1, nazev_skillu2, ...]}.
        Obsahuje pouze triggery kde je konflikt (> 1 skill).
        """
        trigger_skills: dict[str, list[str]] = {}

        for skill in self.skills:
            for trigger in skill.triggers:
                norm = trigger.lower().strip("/")
                if norm not in trigger_skills:
                    trigger_skills[norm] = []
                trigger_skills[norm].append(skill.name)

        # Vrať jen konfliktní
        return {t: names for t, names in trigger_skills.items() if len(names) > 1}


print("\n── Úloha 2: SkillManager.konflikt_check() ──")

# Skill s konfliktním triggerem
CONFLICTING_SKILL_MD = '''---
name: debug-code
description: Debuguje Python kód a hledá chyby
triggers:
  - "vysvětli"
  - "debug"
  - "/debug"
version: 1.0
author: Python kurz
---

# Debug instrukce
Hledej chyby v kódu. Vysvětli co je špatně.
'''

sm = SkillManager()
sm.pridej(skill_explain)
sm.pridej(parsuj_skill_md(CONFLICTING_SKILL_MD))

konflikty = sm.konflikt_check()
if konflikty:
    print("Nalezené konflikty triggerů:")
    for trigger, names in konflikty.items():
        print(f"  '{trigger}' → konfliktu mají: {names}")
else:
    print("Žádné konflikty.")


# ── Úloha 3 ────────────────────────────────────────────────
# parsuj_skill_md() validace: ValueError pokud chybí triggery

print("\n── Úloha 3: parsuj_skill_md() validace triggerů ──")

SKILL_BEZ_TRIGGERU = '''---
name: bez-triggeru
description: Skill bez triggerů – neplatný
version: 1.0
---

# Instrukce
Tento skill nemá triggery a měl by vyvolat ValueError.
'''

try:
    parsuj_skill_md(SKILL_BEZ_TRIGGERU)
    print("CHYBA: Měl vyvolat ValueError!")
except ValueError as e:
    print(f"OK: ValueError zachycen – {e}")

# Platný skill prochází bez chyby
try:
    platny = parsuj_skill_md(EXPLAIN_CODE_MD)
    print(f"OK: Platný skill '{platny.name}' prošel validací.")
except ValueError as e:
    print(f"CHYBA: {e}")


# ── Úloha 4 (BONUS) ────────────────────────────────────────
# skill_priorita() – skills seřazené podle počtu matchujících slov

def skill_priorita(user_input: str, skills: list[Skill]) -> list[tuple[int, Skill]]:
    """
    Vrátí skills seřazené podle počtu matchujících slov z user_input.
    Vrátí pouze skills kde alespoň jedno slovo matchuje.
    Format: [(pocet_shod, skill), ...]  – sestupně.
    """
    slova_vstupu = set(user_input.lower().split())

    scored: list[tuple[int, Skill]] = []
    for skill in skills:
        # Počet slov z triggerů které se vyskytují ve vstupu
        pocet = 0
        for trigger in skill.triggers:
            slova_triggeru = set(trigger.lower().strip("/").split())
            pocet += len(slova_vstupu & slova_triggeru)
        if pocet > 0:
            scored.append((pocet, skill))

    scored.sort(key=lambda x: x[0], reverse=True)
    return scored


print("\n── Úloha 4 (BONUS): skill_priorita() ──")

# Přidáme více skills do manageru
CODE_REVIEW_MD = '''---
name: code-review
description: Code review Python kódu
triggers:
  - "code review"
  - "zreviduj kód"
  - "review"
  - "/review"
version: 1.0
---

# Code Review instrukce
Zkontroluj kód na správnost, výkon a čitelnost.
'''

GENERATE_TESTS_MD = '''---
name: generate-tests
description: Generuje pytest unit testy
triggers:
  - "generuj testy"
  - "napiš testy"
  - "create tests"
  - "/tests"
version: 1.0
---

# Testy instrukce
Generuj pytest unit testy pro zadaný kód.
'''

vsechny_skills = [
    parsuj_skill_md(CODE_REVIEW_MD),
    parsuj_skill_md(GENERATE_TESTS_MD),
    skill_explain,
]

test_vstupy = [
    "prosím vysvětli kód a napiš testy",
    "zreviduj kód a vytvoř review",
    "co dělá tento kód vysvětli mi ho",
]

for vstup in test_vstupy:
    priorita = skill_priorita(vstup, vsechny_skills)
    print(f"\n  Vstup: {vstup!r}")
    for pocet, skill in priorita:
        print(f"    {pocet} shod → {skill.name}")
    if not priorita:
        print("    (žádný skill neodpovídá)")
