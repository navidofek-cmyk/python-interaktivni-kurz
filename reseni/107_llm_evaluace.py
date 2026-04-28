"""Řešení – Lekce 107: Evaluace LLM – jak měřit kvalitu

Toto je vzorové řešení úloh z lekce 107.
"""

import json
import math
import re
import random
import statistics
from dataclasses import dataclass, field
from pathlib import Path

random.seed(42)


# ── Pomocné funkce ze lekce ────────────────────────────────

def tokenizuj(text: str) -> list[str]:
    return re.findall(r'\w+', text.lower())


def ngrams(tokeny: list[str], n: int) -> list[tuple]:
    return [tuple(tokeny[i:i+n]) for i in range(len(tokeny) - n + 1)]


# ── Úloha 1 ────────────────────────────────────────────────
# EvalCase s kontrolou regex vzoru

@dataclass
class EvalCase:
    """Jeden testovací případ – rozšířen o regex validaci."""
    id: str
    otazka: str
    ocekavany_format: str       # "json", "kod", "text"
    klic_slova: list[str]
    zakazana_slova: list[str] = field(default_factory=list)
    min_delka: int = 10
    max_delka: int = 2000
    ocekavany_vzor: str = ""    # Regex který musí odpověď obsahovat


@dataclass
class EvalVysledek:
    eval_id: str
    uspesny: bool
    skore: float
    duvody_selhani: list[str]


def run_eval(case: EvalCase, odpoved: str) -> EvalVysledek:
    """Spustí eval na jedné odpovědi, včetně regex kontroly."""
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
        m = re.search(r'\{.*\}', odpoved, re.DOTALL)
        try:
            json.loads((m.group() if m else odpoved))
            skore_body += 1
        except json.JSONDecodeError:
            duvody_selhani.append("Odpověď neobsahuje validní JSON")
    elif case.ocekavany_format == "kod":
        if "```" in odpoved or "def " in odpoved or "class " in odpoved:
            skore_body += 1
        else:
            duvody_selhani.append("Odpověď neobsahuje kód")
    else:
        skore_body += 1

    # Regex vzor (nová kontrola)
    if case.ocekavany_vzor:
        max_body += 1
        if re.search(case.ocekavany_vzor, odpoved, re.IGNORECASE | re.DOTALL):
            skore_body += 1
        else:
            duvody_selhani.append(f"Odpověď neodpovídá vzoru: {case.ocekavany_vzor!r}")

    skore = skore_body / max_body if max_body > 0 else 0.0
    return EvalVysledek(
        eval_id=case.id,
        uspesny=len(duvody_selhani) == 0,
        skore=round(skore, 3),
        duvody_selhani=duvody_selhani,
    )


print("── Úloha 1: EvalCase s ocekavany_vzor ──")

case_s_vzorem = EvalCase(
    id="E_REG",
    otazka="Uveď příklad list comprehension v Pythonu",
    ocekavany_format="kod",
    klic_slova=["list", "for"],
    ocekavany_vzor=r'\[.+for.+in.+\]',  # Musí obsahovat list comprehension syntaxi
    min_delka=20,
)

odpoved_dobra = "[x*2 for x in range(10)]  # list comprehension\n```python\nresult = [x for x in range(5)]\n```"
odpoved_spatna = "List comprehension je rychlý způsob vytvoření seznamu."

for label, odp in [("Dobrá", odpoved_dobra), ("Špatná", odpoved_spatna)]:
    vysl = run_eval(case_s_vzorem, odp)
    print(f"  {label}: uspesny={vysl.uspesny}, skore={vysl.skore}, selhani={vysl.duvody_selhani}")


# ── Úloha 2 ────────────────────────────────────────────────
# EvalSuite.run_all() – spustí všechny evaly a vrátí JSON report

class EvalSuite:
    """Sada eval testů s metodou run_all()."""

    def __init__(self, nazev: str = "Eval Suite"):
        self.nazev = nazev
        self.cases: list[EvalCase] = []

    def pridej(self, case: EvalCase) -> None:
        self.cases.append(case)

    def run_all(self, odpovedi_dict: dict[str, str]) -> dict:
        """
        Spustí všechny evaly a vrátí souhrnný report jako dict (JSON serializovatelný).
        odpovedi_dict: {eval_id: odpoved}
        """
        vysledky = []
        for case in self.cases:
            odpoved = odpovedi_dict.get(case.id, "")
            vysledek = run_eval(case, odpoved)
            vysledky.append({
                "id": vysledek.eval_id,
                "otazka": case.otazka,
                "uspesny": vysledek.uspesny,
                "skore": vysledek.skore,
                "selhani": vysledek.duvody_selhani,
            })

        uspesne = sum(1 for v in vysledky if v["uspesny"])
        prumer_skore = sum(v["skore"] for v in vysledky) / len(vysledky) if vysledky else 0.0

        return {
            "nazev": self.nazev,
            "celkem": len(vysledky),
            "uspesne": uspesne,
            "neuspesne": len(vysledky) - uspesne,
            "prumer_skore": round(prumer_skore, 3),
            "pass_rate": round(uspesne / len(vysledky), 3) if vysledky else 0.0,
            "vysledky": vysledky,
        }


print("\n── Úloha 2: EvalSuite.run_all() ──")

suite = EvalSuite("Chatbot Eval Suite")
suite.pridej(EvalCase(
    id="E001",
    otazka="Vysvětli list comprehension",
    ocekavany_format="kod",
    klic_slova=["list", "comprehension", "for"],
    zakazana_slova=["nevím"],
    min_delka=50,
))
suite.pridej(EvalCase(
    id="E002",
    otazka="Vrať JSON s informacemi o Pythonu",
    ocekavany_format="json",
    klic_slova=["python"],
    min_delka=10,
))
suite.pridej(EvalCase(
    id="E003",
    otazka="Co je async/await?",
    ocekavany_format="text",
    klic_slova=["async", "await", "asyncio"],
    zakazana_slova=["nerozumím"],
    min_delka=30,
))

dobra_odpovedi = {
    "E001": "[x for x in range(10) if x % 2 == 0]\n```python\nresult = [x*2 for x in range(5)]\n```",
    "E002": '{"jazyk": "python", "verze": "3.12"}',
    "E003": "async/await je syntaxe pro asynchronní programování. asyncio.run() spustí coroutine.",
}

report = suite.run_all(dobra_odpovedi)
print(f"Pass rate: {report['pass_rate']:.0%}  |  Průměr skóre: {report['prumer_skore']}")
print(f"Úspěšné: {report['uspesne']}/{report['celkem']}")
print(json.dumps(report, ensure_ascii=False, indent=2)[:400] + "\n  ...")


# ── Úloha 3 ────────────────────────────────────────────────
# ABTestVysledek s p-hodnotou (Welchův t-test)

@dataclass
class ABTestVysledek:
    prompt_a_name: str
    prompt_b_name: str
    n_testu: int
    skore_a: list[float]
    skore_b: list[float]

    @property
    def prumer_a(self) -> float:
        return statistics.mean(self.skore_a)

    @property
    def prumer_b(self) -> float:
        return statistics.mean(self.skore_b)

    @property
    def vitez(self) -> str:
        if self.p_hodnota() > 0.05:
            return "NEROZHODNĚ (není statisticky signifikantní)"
        if abs(self.prumer_a - self.prumer_b) < 0.05:
            return "NEROZHODNĚ"
        return self.prompt_a_name if self.prumer_a > self.prumer_b else self.prompt_b_name

    def p_hodnota(self) -> float:
        """
        Welchův t-test (přibližný).
        Vrátí p-hodnotu. Pokud p > 0.05, výsledek není statisticky signifikantní.
        """
        n_a = len(self.skore_a)
        n_b = len(self.skore_b)
        if n_a < 2 or n_b < 2:
            return 1.0  # nelze spočítat

        mean_a = statistics.mean(self.skore_a)
        mean_b = statistics.mean(self.skore_b)
        var_a = statistics.variance(self.skore_a)
        var_b = statistics.variance(self.skore_b)

        se_a = var_a / n_a
        se_b = var_b / n_b
        se_total = se_a + se_b

        if se_total == 0:
            return 0.0 if mean_a != mean_b else 1.0

        t_stat = abs(mean_a - mean_b) / math.sqrt(se_total)

        # Welchovy stupně volnosti
        df_num = se_total ** 2
        df_den = (se_a ** 2) / (n_a - 1) + (se_b ** 2) / (n_b - 1)
        df = df_num / df_den if df_den > 0 else 1.0

        # Přibližná p-hodnota přes normální distribuci (zjednodušení)
        # Pro malá df je méně přesné – v produkci použij scipy.stats.ttest_ind
        z = t_stat / math.sqrt(1 + t_stat ** 2 / df)  # přibližná konverze
        p = 2 * (1 - _normal_cdf(abs(z)))
        return round(p, 4)

    def report(self) -> str:
        p = self.p_hodnota()
        signif = "ANO" if p <= 0.05 else "NE"
        return (
            f"A/B Test: {self.prompt_a_name} vs {self.prompt_b_name}\n"
            f"  N testů:       {self.n_testu}\n"
            f"  Průměr A:      {self.prumer_a:.3f}\n"
            f"  Průměr B:      {self.prumer_b:.3f}\n"
            f"  Δ:             {abs(self.prumer_a - self.prumer_b):.3f}\n"
            f"  p-hodnota:     {p:.4f}  (signifikantní: {signif})\n"
            f"  Vítěz:         {self.vitez}"
        )


def _normal_cdf(x: float) -> float:
    """Přibližná CDF normálního rozdělení (Abramowitz & Stegun)."""
    t = 1.0 / (1.0 + 0.2316419 * abs(x))
    poly = t * (0.319381530 + t * (-0.356563782 + t * (1.781477937 + t * (-1.821255978 + t * 1.330274429))))
    pdf = math.exp(-0.5 * x * x) / math.sqrt(2 * math.pi)
    return 1.0 - pdf * poly if x >= 0 else pdf * poly


def ab_test(prompt_a_name: str, prompt_b_name: str, n: int = 10) -> ABTestVysledek:
    skore_a = [max(0, min(1, random.gauss(0.62, 0.12))) for _ in range(n)]
    skore_b = [max(0, min(1, random.gauss(0.77, 0.10))) for _ in range(n)]
    return ABTestVysledek(prompt_a_name, prompt_b_name, n, skore_a, skore_b)


print("\n── Úloha 3: ABTestVysledek s p-hodnotou ──")
vysledek = ab_test("Zero-shot", "Few-shot", n=20)
print(vysledek.report())


# ── Úloha 4 (BONUS) ────────────────────────────────────────
# eval_chatbot() – 5 eval cases, spuštění, uložení, regression test

def eval_chatbot(
    vystup_soubor: str = "/tmp/eval_results.json",
    predchozi_soubor: str | None = None,
) -> dict:
    """
    a) Definuje 5 eval cases pro chatbot
    b) Spustí je (simulace)
    c) Uloží výsledky do JSON
    d) Porovná s předchozím spuštěním (regression test)
    """
    suite = EvalSuite("Chatbot Eval Suite v2")
    suite.pridej(EvalCase(
        id="C001",
        otazka="Co je list comprehension?",
        ocekavany_format="kod",
        klic_slova=["list", "comprehension", "for"],
        min_delka=50,
        ocekavany_vzor=r'\[.+for.+in',
    ))
    suite.pridej(EvalCase(
        id="C002",
        otazka="Vrať JSON s klíči jazyk, verze, populárnost",
        ocekavany_format="json",
        klic_slova=["jazyk", "verze"],
        min_delka=20,
    ))
    suite.pridej(EvalCase(
        id="C003",
        otazka="Vysvětli async/await",
        ocekavany_format="text",
        klic_slova=["async", "await"],
        zakazana_slova=["nevím"],
        min_delka=30,
    ))
    suite.pridej(EvalCase(
        id="C004",
        otazka="Napiš funkci pro výpočet faktoriálu",
        ocekavany_format="kod",
        klic_slova=["faktorial", "def", "return"],
        min_delka=40,
        ocekavany_vzor=r'def faktorial',
    ))
    suite.pridej(EvalCase(
        id="C005",
        otazka="Co je decorator pattern?",
        ocekavany_format="text",
        klic_slova=["dekorátor", "funkce"],
        min_delka=30,
    ))

    # Simulace odpovědí
    sim_odpovedi = {
        "C001": "[x**2 for x in range(10) if x % 2 == 0]\n```python\nresult = [x for x in lst]\n```",
        "C002": '{"jazyk": "Python", "verze": "3.12", "popularnost": "velmi vysoká"}',
        "C003": "async def f(): ... await asyncio.sleep(1). asyncio.run() spustí coroutine.",
        "C004": "def faktorial(n):\n    if n <= 1:\n        return 1\n    return n * faktorial(n-1)",
        "C005": "Dekorátor je funkce, která obalí jinou funkci a rozšíří její chování.",
    }

    report = suite.run_all(sim_odpovedi)
    report["timestamp"] = "2026-04-28T10:00:00"

    # c) Ulož výsledky
    Path(vystup_soubor).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"  Výsledky uloženy: {vystup_soubor}")

    # d) Regression test
    regrese_info: dict = {}
    if predchozi_soubor and Path(predchozi_soubor).exists():
        predchozi = json.loads(Path(predchozi_soubor).read_text(encoding="utf-8"))
        predchozi_skore = {v["id"]: v["skore"] for v in predchozi.get("vysledky", [])}
        nove_skore = {v["id"]: v["skore"] for v in report["vysledky"]}

        threshold = 0.05
        regrese: dict = {}
        zlepseni: dict = {}
        for eid, nove in nove_skore.items():
            stare = predchozi_skore.get(eid, 0.0)
            delta = nove - stare
            if delta < -threshold:
                regrese[eid] = {"stare": stare, "nove": nove, "delta": round(delta, 3)}
            elif delta > threshold:
                zlepseni[eid] = {"stare": stare, "nove": nove, "delta": round(delta, 3)}

        regrese_info = {
            "ok": len(regrese) == 0,
            "regrese": regrese,
            "zlepseni": zlepseni,
        }
        report["regression"] = regrese_info

    return report


print("\n── Úloha 4 (BONUS): eval_chatbot() ──")
vysledek = eval_chatbot(vystup_soubor="/tmp/eval_results.json")
print(f"Celkem: {vysledek['celkem']}  |  Úspěšné: {vysledek['uspesne']}  |  Pass rate: {vysledek['pass_rate']:.0%}")
print(f"Průměr skóre: {vysledek['prumer_skore']}")
print("Výsledky jednotlivých testů:")
for v in vysledek["vysledky"]:
    sym = "✓" if v["uspesny"] else "✗"
    print(f"  {sym} {v['id']}: skóre={v['skore']:.2f}  {v['otazka'][:40]}...")
    for d in v["selhani"]:
        print(f"      → {d}")
