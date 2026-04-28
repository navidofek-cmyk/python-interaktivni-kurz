"""
LEKCE 107: Evaluace LLM – jak měřit kvalitu
=============================================
pip install rouge-score  (volitelné, jinak simulace)

Proč evaluovat:
  "Funguje to dobře" nestačí v produkci.
  Potřebuješ čísla, které říkají:
  - Je nová verze promptu lepší než stará?
  - Zhoršila změna modelu výsledky?
  - Kde přesně model selhává?

Co se naučíš:
  - BLEU a ROUGE skóre (překlad, sumarizace)
  - LLM-as-judge: model hodnotí modely
  - Evals framework: sada testů výstupu
  - A/B test promptů
  - Regression testing

Spuštění: python3 107_llm_evaluace.py
Nevyžaduje API klíč – všechna skóre jsou simulována.
"""

import os, json, math, re, random, time, textwrap
from typing import Any
from dataclasses import dataclass, field

ANTHROPIC_KEY = os.getenv("ANTHROPIC_API_KEY", "")

random.seed(42)  # Reprodukovatelnost

# ══════════════════════════════════════════════════════════════════
# ČÁST 1: BLEU SKÓRE
# ══════════════════════════════════════════════════════════════════

print("=" * 60)
print("ČÁST 1: BLEU skóre – Bilingual Evaluation Understudy")
print("=" * 60)

print("""
BLEU měří překryv n-gramů mezi hypotézou a referencí.
  Původně pro strojový překlad (candidate vs. reference překlad).
  Dnes: hodnocení sumarizace, přepisu, parafrázování.

Rozsah: 0.0 (nic nesedí) → 1.0 (perfektní shoda)
Typické hodnoty:
  < 0.10  špatný výstup
  0.10–0.30  přijatelný
  > 0.40  dobrý (strojový překlad)
""")

def tokenizuj(text: str) -> list[str]:
    """Jednoduchá tokenizace na slova (lowercase)."""
    return re.findall(r'\w+', text.lower())

def ngrams(tokeny: list[str], n: int) -> list[tuple]:
    """Vytvoří n-gramy ze seznamu tokenů."""
    return [tuple(tokeny[i:i+n]) for i in range(len(tokeny) - n + 1)]

def bleu_score(hypothesis: str, reference: str, max_n: int = 4) -> dict[str, float]:
    """
    Zjednodušená implementace BLEU skóre.
    Reálná implementace: pip install nltk; nltk.translate.bleu_score
    """
    hyp_tok = tokenizuj(hypothesis)
    ref_tok = tokenizuj(reference)

    if not hyp_tok:
        return {"bleu": 0.0, "precisions": [], "brevity_penalty": 0.0}

    precisions = []
    for n in range(1, max_n + 1):
        hyp_ng = ngrams(hyp_tok, n)
        ref_ng = ngrams(ref_tok, n)

        if not hyp_ng:
            precisions.append(0.0)
            continue

        ref_counts: dict = {}
        for ng in ref_ng:
            ref_counts[ng] = ref_counts.get(ng, 0) + 1

        matches = 0
        for ng in hyp_ng:
            if ref_counts.get(ng, 0) > 0:
                matches += 1
                ref_counts[ng] -= 1

        precisions.append(matches / len(hyp_ng))

    # Brevity penalty (penalizace za krátké odpovědi)
    bp = min(1.0, math.exp(1 - len(ref_tok) / max(len(hyp_tok), 1)))

    # Geometrický průměr precizí
    valid = [p for p in precisions if p > 0]
    if not valid:
        bleu = 0.0
    else:
        log_avg = sum(math.log(p) for p in valid) / len(valid)
        bleu = bp * math.exp(log_avg)

    return {
        "bleu": round(bleu, 4),
        "precisions": [round(p, 4) for p in precisions],
        "brevity_penalty": round(bp, 4),
    }

# Demonstrace
print("--- BLEU příklady ---")
priklady = [
    {
        "name": "Perfektní shoda",
        "hyp": "Python je skvělý programovací jazyk pro začátečníky",
        "ref": "Python je skvělý programovací jazyk pro začátečníky",
    },
    {
        "name": "Částečná shoda",
        "hyp": "Python je dobrý jazyk pro programátory",
        "ref": "Python je skvělý programovací jazyk pro začátečníky",
    },
    {
        "name": "Žádná shoda",
        "hyp": "Dnes je hezké počasí v Praze",
        "ref": "Python je skvělý programovací jazyk pro začátečníky",
    },
]

for p in priklady:
    result = bleu_score(p["hyp"], p["ref"])
    print(f"\n  {p['name']}:")
    print(f"  Hyp: {p['hyp']!r}")
    print(f"  Ref: {p['ref']!r}")
    print(f"  BLEU: {result['bleu']:.4f}  |  1-grams: {result['precisions'][0]:.2f}  2-grams: {result['precisions'][1]:.2f}")

# ══════════════════════════════════════════════════════════════════
# ČÁST 2: ROUGE SKÓRE
# ══════════════════════════════════════════════════════════════════

print("\n" + "=" * 60)
print("ČÁST 2: ROUGE skóre – Recall-Oriented Understudy for Gisting")
print("=" * 60)

print("""
ROUGE měří jak moc reference je "pokryta" hypotézou.
Vhodné pro sumarizaci: zachytil souhrn klíčové informace?

  ROUGE-1: shoda unigramů (slov)
  ROUGE-2: shoda bigramů (dvojic slov)
  ROUGE-L: nejdelší společná subsequence
""")

def rouge_n(hypothesis: str, reference: str, n: int = 1) -> dict[str, float]:
    """ROUGE-N: precision, recall, F1."""
    hyp_ng = ngrams(tokenizuj(hypothesis), n)
    ref_ng = ngrams(tokenizuj(reference), n)

    if not ref_ng:
        return {"precision": 0.0, "recall": 0.0, "f1": 0.0}

    ref_counts: dict = {}
    for ng in ref_ng:
        ref_counts[ng] = ref_counts.get(ng, 0) + 1

    matches = 0
    for ng in hyp_ng:
        if ref_counts.get(ng, 0) > 0:
            matches += 1
            ref_counts[ng] -= 1

    precision = matches / len(hyp_ng) if hyp_ng else 0.0
    recall    = matches / len(ref_ng)
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0

    return {
        "precision": round(precision, 4),
        "recall":    round(recall, 4),
        "f1":        round(f1, 4),
    }

# Příklad: hodnocení sumarizace
reference_text = """
Python je vysokoúrovňový interpretovaný programovací jazyk.
Byl vytvořen Guidem van Rossumem a poprvé vydán v roce 1991.
Python klade důraz na čitelnost kódu a jednoduchost syntaxe.
Je používán v datové vědě, webovém vývoji a automatizaci.
"""

souhrn_a = "Python je programovací jazyk vytvořený v roce 1991. Je populární v datové vědě."
souhrn_b = "Python: vysokoúrovňový jazyk, čitelný, používaný v datové vědě a webu."

print("\n--- ROUGE porovnání dvou souhrnů ---")
print(f"Reference: {reference_text.strip()[:100]}...")
print(f"\nSouhrn A: {souhrn_a!r}")
print(f"Souhrn B: {souhrn_b!r}")

for popis, souhrn in [("Souhrn A", souhrn_a), ("Souhrn B", souhrn_b)]:
    r1 = rouge_n(souhrn, reference_text, n=1)
    r2 = rouge_n(souhrn, reference_text, n=2)
    print(f"\n  {popis}:")
    print(f"    ROUGE-1: P={r1['precision']:.3f} R={r1['recall']:.3f} F1={r1['f1']:.3f}")
    print(f"    ROUGE-2: P={r2['precision']:.3f} R={r2['recall']:.3f} F1={r2['f1']:.3f}")

# ══════════════════════════════════════════════════════════════════
# ČÁST 3: LLM-AS-JUDGE
# ══════════════════════════════════════════════════════════════════

print("\n" + "=" * 60)
print("ČÁST 3: LLM-as-Judge – model hodnotí modely")
print("=" * 60)

print("""
BLEU/ROUGE mají limity:
  - Závisí na přesném slovním matchingu
  - Neměří faktickou správnost
  - Nerozumí nuancím jazyka

LLM-as-judge:
  Jiný (nebo stejný) model hodnotí odpovědi.
  Výhody: Zachytí smysl, ne jen slova
  Nevýhody: Drahý, pomalejší, může být zaujatý
""")

@dataclass
class HodnoceniLLM:
    skore: float          # 1-10
    zduvodneni: str
    silne_stranky: list[str]
    slabiny: list[str]
    doporuceni: str

def llm_judge_prompt(otazka: str, odpoved: str) -> str:
    """Prompt pro LLM-as-judge."""
    return f"""Jsi objektivní hodnotitel kvality LLM odpovědí.

Otázka: {otazka}

Odpověď k hodnocení:
{odpoved}

Ohodnoť odpověď na škále 1-10 podle těchto kritérií:
- Správnost (40%): Je odpověď fakticky správná?
- Úplnost (30%): Pokrývá odpověď vše co otázka žádá?
- Jasnost (20%): Je odpověď srozumitelná a dobře strukturovaná?
- Stručnost (10%): Je přiměřeně dlouhá (ne příliš krátká ani dlouhá)?

Vrať JSON s klíči: skore (float 1-10), zduvodneni (string),
silne_stranky (list), slabiny (list), doporuceni (string).
Vrať POUZE JSON, žádný text kolem."""

def hodnotit_llm(otazka: str, odpoved: str) -> HodnoceniLLM:
    """Zavolá LLM nebo vrátí simulaci."""
    if ANTHROPIC_KEY:
        import anthropic
        client = anthropic.Anthropic()
        msg = client.messages.create(
            model="claude-opus-4-7",
            max_tokens=512,
            messages=[{"role": "user", "content": llm_judge_prompt(otazka, odpoved)}]
        )
        raw = msg.content[0].text
        match = re.search(r'\{.*\}', raw, re.DOTALL)
        if match:
            data = json.loads(match.group())
            return HodnoceniLLM(**{k: data[k] for k in HodnoceniLLM.__dataclass_fields__})

    # Simulace (deterministická podle délky odpovědi)
    delka_score = min(10, max(1, len(odpoved.split()) / 20))
    strukturovanost = 1.5 if any(c in odpoved for c in ["```", "**", "\n-", "\n1."]) else 0
    skore = round(min(10, delka_score + strukturovanost + random.uniform(-0.5, 0.5)), 1)

    return HodnoceniLLM(
        skore=skore,
        zduvodneni=f"[SIMULACE] Odpověď má {len(odpoved.split())} slov.",
        silne_stranky=["Relevantní odpověď", "Dobrá délka"] if len(odpoved) > 100 else ["Stručnost"],
        slabiny=["Chybí příklady"] if "```" not in odpoved else [],
        doporuceni="Přidej kódový příklad." if "```" not in odpoved else "Výborná odpověď.",
    )

# Testování
testovaci_dvojice = [
    {
        "otazka": "Co je Python dekorátor?",
        "odpoved_a": "Dekorátor je věc v Pythonu.",
        "odpoved_b": (
            "Dekorátor je funkce, která obalí jinou funkci a rozšíří její chování "
            "bez změny jejího kódu.\n\n"
            "```python\n"
            "def muj_dekorator(func):\n"
            "    def wrapper(*args, **kwargs):\n"
            "        print('Před volání')\n"
            "        result = func(*args, **kwargs)\n"
            "        print('Po volání')\n"
            "        return result\n"
            "    return wrapper\n"
            "\n"
            "@muj_dekorator\n"
            "def pozdrav():\n"
            "    print('Ahoj!')\n"
            "```"
        ),
    }
]

print("\n--- LLM-as-Judge demonstrace ---")
for test in testovaci_dvojice:
    print(f"\nOtázka: {test['otazka']!r}")
    for label, odpoved in [("Odpověď A (špatná)", test["odpoved_a"]), ("Odpověď B (dobrá)", test["odpoved_b"])]:
        hodnoceni = hodnotit_llm(test["otazka"], odpoved)
        print(f"\n  {label} ({len(odpoved.split())} slov):")
        print(f"  Skóre: {hodnoceni.skore}/10")
        print(f"  Silné: {hodnoceni.silne_stranky}")
        print(f"  Slabiny: {hodnoceni.slabiny}")
        print(f"  Doporučení: {hodnoceni.doporuceni}")

# ══════════════════════════════════════════════════════════════════
# ČÁST 4: EVALS FRAMEWORK
# ══════════════════════════════════════════════════════════════════

print("\n" + "=" * 60)
print("ČÁST 4: Evals Framework – sada testů")
print("=" * 60)

@dataclass
class EvalCase:
    """Jeden testovací případ."""
    id: str
    otazka: str
    ocekavany_format: str       # "json", "kod", "text"
    klic_slova: list[str]       # musí být v odpovědi
    zakazana_slova: list[str] = field(default_factory=list)
    min_delka: int = 10
    max_delka: int = 2000

@dataclass
class EvalVysledek:
    eval_id: str
    uspesny: bool
    skore: float
    duvody_selhani: list[str]

def run_eval(case: EvalCase, odpoved: str) -> EvalVysledek:
    """Spustí eval na jedné odpovědi."""
    duvody_selhani = []
    skore_body = 0
    max_body = 0

    # Délka
    max_body += 2
    if case.min_delka <= len(odpoved) <= case.max_delka:
        skore_body += 2
    else:
        duvody_selhani.append(f"Délka {len(odpoved)} mimo rozsah [{case.min_delka}, {case.max_delka}]")

    # Klíčová slova
    max_body += len(case.klic_slova)
    for kw in case.klic_slova:
        if kw.lower() in odpoved.lower():
            skore_body += 1
        else:
            duvody_selhani.append(f"Chybí klíčové slovo: {kw!r}")

    # Zakázaná slova
    max_body += len(case.zakazana_slova)
    for zw in case.zakazana_slova:
        if zw.lower() not in odpoved.lower():
            skore_body += 1
        else:
            duvody_selhani.append(f"Nalezeno zakázané slovo: {zw!r}")

    # Formát
    max_body += 1
    if case.ocekavany_format == "json":
        try:
            json.loads(odpoved)
            skore_body += 1
        except json.JSONDecodeError:
            # Zkus extrahovat JSON
            match = re.search(r'\{.*\}', odpoved, re.DOTALL)
            if match:
                try:
                    json.loads(match.group())
                    skore_body += 1
                except:
                    duvody_selhani.append("Odpověď neobsahuje validní JSON")
            else:
                duvody_selhani.append("Odpověď neobsahuje JSON")
    elif case.ocekavany_format == "kod":
        if "```" in odpoved or "def " in odpoved or "class " in odpoved:
            skore_body += 1
        else:
            duvody_selhani.append("Odpověď neobsahuje kód")
    else:
        skore_body += 1  # text je vždy OK

    skore = skore_body / max_body if max_body > 0 else 0.0
    return EvalVysledek(
        eval_id=case.id,
        uspesny=len(duvody_selhani) == 0,
        skore=round(skore, 3),
        duvody_selhani=duvody_selhani,
    )

# Eval suite pro chatbota z lekce 74
eval_suite = [
    EvalCase(
        id="E001",
        otazka="Vysvětli co je list comprehension",
        ocekavany_format="kod",
        klic_slova=["list", "comprehension", "for"],
        zakazana_slova=["nevím", "neznám"],
        min_delka=50,
    ),
    EvalCase(
        id="E002",
        otazka="Vrať JSON s informacemi o Pythonu",
        ocekavany_format="json",
        klic_slova=["python"],
        min_delka=10,
    ),
    EvalCase(
        id="E003",
        otazka="Co je async/await?",
        ocekavany_format="text",
        klic_slova=["async", "await", "asyncio"],
        zakazana_slova=["nerozumím"],
        min_delka=30,
    ),
]

# Simulované odpovědi (špatné a dobré)
simul_odpovedi = [
    {
        "E001": "[x for x in range(10) if x % 2 == 0]  # list comprehension v Pythonu – for smyčka v hranatých závorkách\n```python\nresult = [x*2 for x in range(5)]\n```",
        "E002": '{"jazyk": "python", "verze": "3.12", "typ": "interpretovany"}',
        "E003": "async/await je syntaxe pro asynchronní programování. asyncio.run() spustí coroutine. Await čeká na výsledek bez blokování threadu.",
    },
    {  # Špatné odpovědi
        "E001": "Nevím přesně co to je.",
        "E002": "Python je dobrý jazyk.",
        "E003": "Nerozumím tomu.",
    }
]

print("\n--- Eval Suite výsledky ---")
for i, odpovedi in enumerate(simul_odpovedi):
    label = "Dobré odpovědi" if i == 0 else "Špatné odpovědi"
    print(f"\n  [{label}]")
    celkove = []
    for case in eval_suite:
        odpoved = odpovedi.get(case.id, "")
        vysledek = run_eval(case, odpoved)
        celkove.append(vysledek.skore)
        status = "✓" if vysledek.uspesny else "✗"
        print(f"  {status} {case.id}: skóre={vysledek.skore:.2f}  {case.otazka[:35]}...")
        for d in vysledek.duvody_selhani:
            print(f"      → {d}")

    print(f"  Průměrné skóre: {sum(celkove)/len(celkove):.2f}")

# ══════════════════════════════════════════════════════════════════
# ČÁST 5: A/B TEST PROMPTŮ
# ══════════════════════════════════════════════════════════════════

print("\n" + "=" * 60)
print("ČÁST 5: A/B test – který prompt je lepší?")
print("=" * 60)

@dataclass
class ABTestVysledek:
    prompt_a_name: str
    prompt_b_name: str
    n_testů: int
    skore_a: list[float]
    skore_b: list[float]

    @property
    def prumer_a(self) -> float:
        return sum(self.skore_a) / len(self.skore_a)

    @property
    def prumer_b(self) -> float:
        return sum(self.skore_b) / len(self.skore_b)

    @property
    def vitez(self) -> str:
        if abs(self.prumer_a - self.prumer_b) < 0.05:
            return "NEROZHODNĚ"
        return self.prompt_a_name if self.prumer_a > self.prumer_b else self.prompt_b_name

    def report(self) -> str:
        return (
            f"A/B Test: {self.prompt_a_name} vs {self.prompt_b_name}\n"
            f"  N testů: {self.n_testů}\n"
            f"  Průměr A: {self.prumer_a:.3f}\n"
            f"  Průměr B: {self.prumer_b:.3f}\n"
            f"  Vítěz:    {self.vitez}\n"
            f"  Δ:        {abs(self.prumer_a - self.prumer_b):.3f}"
        )

def ab_test(prompt_a_name: str, prompt_b_name: str, n: int = 10) -> ABTestVysledek:
    """
    Simuluje A/B test dvou promptů.
    V produkci: volá oba prompty n-krát a hodnotí výstupy.
    """
    # Simulace: prompt B je o 15% lepší
    skore_a = [max(0, min(1, random.gauss(0.62, 0.12))) for _ in range(n)]
    skore_b = [max(0, min(1, random.gauss(0.77, 0.10))) for _ in range(n)]
    return ABTestVysledek(prompt_a_name, prompt_b_name, n, skore_a, skore_b)

print("\n--- Porovnání Zero-shot vs. Few-shot promptu ---")
vysledek = ab_test("Zero-shot", "Few-shot", n=20)
print(vysledek.report())

# ══════════════════════════════════════════════════════════════════
# ČÁST 6: REGRESSION TESTING
# ══════════════════════════════════════════════════════════════════

print("\n" + "=" * 60)
print("ČÁST 6: Regression Testing – nezhoršila nová verze výsledky?")
print("=" * 60)

@dataclass
class RegressionTest:
    """Uchová baseline a porovná s novou verzí."""
    nazev: str
    baseline_skore: dict[str, float]  # {eval_id: skore}

    def porovnej(self, nove_skore: dict[str, float], threshold: float = 0.05) -> dict:
        """Porovná nové skóre s baseline."""
        regrese = {}
        zlepseni = {}

        for eval_id, nove in nove_skore.items():
            stare = self.baseline_skore.get(eval_id, 0.0)
            delta = nove - stare
            if delta < -threshold:
                regrese[eval_id] = {"stare": stare, "nove": nove, "delta": delta}
            elif delta > threshold:
                zlepseni[eval_id] = {"stare": stare, "nove": nove, "delta": delta}

        return {
            "regrese": regrese,
            "zlepseni": zlepseni,
            "ok": len(regrese) == 0,
        }

# Baseline z minulého spuštění
baseline = RegressionTest(
    nazev="claude-opus-4-7 + v1 prompt",
    baseline_skore={"E001": 0.85, "E002": 0.90, "E003": 0.80},
)

# Nové výsledky (simulace)
nove_skore_lepsi = {"E001": 0.90, "E002": 0.88, "E003": 0.85}
nove_skore_horsi = {"E001": 0.70, "E002": 0.85, "E003": 0.65}

for label, nove in [("Lepší verze promptu", nove_skore_lepsi), ("Horší verze promptu", nove_skore_horsi)]:
    vysledek = baseline.porovnej(nove)
    status = "✓ PROŠLO" if vysledek["ok"] else "✗ REGRESE"
    print(f"\n  {label}: {status}")
    if vysledek["regrese"]:
        print("  Regrese:")
        for eid, info in vysledek["regrese"].items():
            print(f"    {eid}: {info['stare']:.2f} → {info['nove']:.2f} (Δ{info['delta']:+.2f})")
    if vysledek["zlepseni"]:
        print("  Zlepšení:")
        for eid, info in vysledek["zlepseni"].items():
            print(f"    {eid}: {info['stare']:.2f} → {info['nove']:.2f} (Δ{info['delta']:+.2f})")

# SHRNUTÍ
print("\n" + "=" * 60)
print("SHRNUTÍ")
print("=" * 60)
print("""
  Metrika          Použití                          Limit
  ────────         ─────────────────────────────    ──────────────────────
  BLEU             Překlad, parafrázování           Závisí na word matchingu
  ROUGE            Sumarizace                       Nezachytí parafrázování
  LLM-as-Judge     Obecná kvalita, nuance           Drahý, pomalý, zaujatý
  Evals framework  Konkrétní požadavky (formát)     Nutno ručně definovat

  Best practice: kombinuj metriky!
    ROUGE pro recall + LLM-judge pro kvalitu + Evals pro formát
""")

# ══════════════════════════════════════════════════════════════════
# TVOJE ÚLOHA
# ══════════════════════════════════════════════════════════════════
print("""
╔══════════════════════════════════════════════════════════════╗
║  TVOJE ÚLOHA                                                 ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  1. Přidej do EvalCase kontrolu regex vzoru:                 ║
║     `ocekavany_vzor: str = ""`  – pokud je nastaven,        ║
║     odpověď musí obsahovat text matchující tento regex.      ║
║                                                              ║
║  2. Implementuj `EvalSuite.run_all(odpovedi_dict)` která     ║
║     spustí všechny evaly a vrátí souhrnný report jako JSON. ║
║                                                              ║
║  3. Přidej do ABTestVysledek výpočet p-hodnoty (jednoduché  ║
║     přiblížení: Welchův t-test). Pokud p > 0.05, výsledek  ║
║     není statisticky signifikantní.                          ║
║     Tip: import statistics; statistics.mean(), stdev()       ║
║                                                              ║
║  4. BONUS: Vytvoř `eval_chatbot()` funkci která:            ║
║     a) Definuje 5 eval cases pro chatbot z lekce 74          ║
║     b) Spustí je (simulace nebo reálné API)                  ║
║     c) Uloží výsledky do eval_results.json                   ║
║     d) Porovná s předchozím spuštěním (regression test)      ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
""")
