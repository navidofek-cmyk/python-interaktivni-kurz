"""Řešení – Lekce 81: NLP – zpracování přirozeného jazyka"""

import re
import math
from collections import Counter

# Sdílené pomocné funkce
def tokenizuj(text: str) -> list[str]:
    text = text.lower()
    text = re.sub(r"[^\w\s]", "", text)
    return text.split()

STOP_CZ = {"a", "v", "na", "pro", "se", "je", "byl", "jsou",
            "byla", "bylo", "i", "o", "z", "do", "s", "k",
            "to", "ten", "ta", "tato", "tento", "jako", "ale",
            "nebo", "pro", "po", "při", "ze", "ve", "ke", "co",
            "by", "si", "ho", "mu", "mi", "nám", "vám", "ni"}

STOP_EN = {"a", "an", "the", "is", "are", "was", "were", "be",
           "been", "being", "have", "has", "had", "do", "does",
           "did", "will", "would", "could", "should", "may",
           "might", "must", "can", "of", "in", "to", "for",
           "on", "at", "by", "with", "from", "as", "into",
           "and", "or", "but", "not", "no", "it", "its",
           "this", "that", "these", "those", "i", "you", "he",
           "she", "we", "they", "my", "your", "his", "her"}


# 1. Funkce klic_slova(text, n=5)
print("=== 1. klic_slova(text, n=5) – TF-IDF klíčová slova ===\n")

def klic_slova(text: str, n: int = 5,
               jazyk: str = "cs") -> list[tuple[str, float]]:
    """
    Vrátí n nejdůležitějších slov v textu pomocí TF-IDF.

    Funguje i pro jednoduché jednoduché texty (bez kolekce dokumentů).
    V takovém případě používá TF + délku slova jako heuristiku.

    Vrátí: [(slovo, skore), ...] seřazené od nejdůležitějšího
    """
    stop = STOP_CZ if jazyk == "cs" else STOP_EN

    # Tokenizace a čištění
    slova = tokenizuj(text)
    slova = [s for s in slova if s not in stop and len(s) > 2]

    if not slova:
        return []

    # TF – frekvence slova v textu
    tf = Counter(slova)
    celkem = len(slova)

    # Heuristika pro single-document TF-IDF:
    # IDF = log(celkem_slov / frekvence) – řídká slova jsou důležitější
    skore = {}
    for slovo, pocet in tf.items():
        tf_val  = pocet / celkem
        idf_val = math.log(celkem / pocet + 1)   # +1 pro hladkost
        # Bonus za délku (delší slova jsou obvykle substantivnější)
        delka_bonus = min(len(slovo) / 10, 1.0)
        skore[slovo] = tf_val * idf_val * (1 + delka_bonus)

    # Seřaď a vrať top-n
    return sorted(skore.items(), key=lambda x: -x[1])[:n]

# Testovací texty
TEXTY = {
    "Python": """
        Python je interpretovaný programovací jazyk vysoké úrovně.
        Byl navržen Guido van Rossumem a poprvé vydán v roce 1991.
        Python klade důraz na čitelnost kódu a jednoduchost.
        Používá se pro webový vývoj, datovou vědu a automatizaci.
        Komunitní podpora Pythonu je obrovská.
    """,
    "Databáze": """
        SQLite je lehká embedded relační databáze.
        PostgreSQL je výkonná serverová databáze s ACID zárukami.
        Databáze ukládá data do tabulek s relacemi mezi nimi.
        Dotazovací jazyk SQL umožňuje efektivní manipulaci s daty.
    """,
    "Machine Learning": """
        Strojové učení je oblast umělé inteligence.
        Algoritmy se učí z dat bez explicitního programování.
        Neuronové sítě napodobují funkci lidského mozku.
        Deep learning používá vícevrstvé neuronové sítě.
    """,
}

for titulek, text in TEXTY.items():
    slova = klic_slova(text, n=5)
    print(f"  Klíčová slova pro '{titulek}':")
    for slovo, skore_val in slova:
        print(f"    {slovo:<20} {skore_val:.4f}")
    print()


# 2. Sentiment recenzí z reálného datasetu (demo s příklady)
print("=== 2. Sentiment analýza recenzí ===\n")

POZITIVNI = {"skvělý", "výborný", "báječný", "super", "perfektní",
              "dobrý", "great", "excellent", "good", "amazing", "love",
              "best", "fantastic", "wonderful", "awesome", "perfect",
              "brilliant", "outstanding", "recommend", "helpful", "clear",
              "easy", "fast", "beautiful", "elegant", "intuitive"}
NEGATIVNI = {"špatný", "hrozný", "ošklivý", "příšerný", "terrible",
              "bad", "awful", "horrible", "worst", "hate", "poor",
              "disgusting", "failure", "broken", "useless", "difficult",
              "confusing", "slow", "buggy", "crash", "error", "broken"}

def sentiment_rozsirenyi(text: str) -> dict:
    """Rozšířená sentiment analýza s negacemi."""
    slova = re.sub(r"[^\w\s]", "", text.lower()).split()
    pos, neg = 0, 0
    negace_okno = 0   # počítá slova po negaci

    NEGACE = {"not", "no", "never", "bez", "není", "ne", "žádný", "nikdy"}

    for slovo in slova:
        if slovo in NEGACE:
            negace_okno = 3   # příštích 3 slov jsou negovaná
            continue
        efekt = -1 if negace_okno > 0 else 1
        if slovo in POZITIVNI:
            pos += efekt * 1
        elif slovo in NEGATIVNI:
            neg += efekt * 1
        if negace_okno > 0:
            negace_okno -= 1

    net   = pos - neg
    celkem = len(slova)
    skore  = net / max(celkem, 1)
    label  = "pozitivní" if skore > 0.01 else "negativní" if skore < -0.01 else "neutrální"
    return {"label": label, "skore": round(skore, 3), "pos": pos, "neg": neg, "slova": celkem}

# Demo dataset recenzí (jako Kaggle Amazon Reviews)
RECENZE = [
    ("Python Crash Course",     "Excellent book! Clear explanations and great examples. Highly recommend!"),
    ("Learn Python Fast",       "Terrible book. Confusing and full of errors. Worst purchase ever."),
    ("Python Cookbook",         "Good reference book. Not perfect but helpful for intermediate programmers."),
    ("Automate the Boring Stuff","Amazing book! Best Python book I've read. Love the practical examples."),
    ("Python Anti-Patterns",    "Not bad, not great. Some useful tips but nothing outstanding."),
    ("Python for Data Science", "No clear structure. Broken code examples. Awful reading experience."),
    ("Fluent Python",           "Brilliant! Outstanding depth. The best Python book for advanced devs."),
    ("Python Tutorial",         "Slow and boring. Not easy to follow. Poor explanations throughout."),
]

print(f"  {'Recenze':<30} {'Sentiment':<12} {'Skóre':>7}  {'+'}/{'-'}")
print(f"  {'─'*30}  {'─'*12}  {'─'*7}  {'─'*5}")
for nazev, text in RECENZE:
    s = sentiment_rozsirenyi(text)
    ikona = "😊" if s["label"] == "pozitivní" else "😞" if s["label"] == "negativní" else "😐"
    print(f"  {nazev:<30} {ikona} {s['label']:<10} {s['skore']:>+7.3f}  {s['pos']}/{s['neg']}")

pocty = Counter(sentiment_rozsirenyi(t)["label"] for _, t in RECENZE)
print(f"\n  Shrnutí: {pocty}")


# 3. spaCy NER – extrakce osob a organizací z novinového článku
print("\n=== 3. spaCy NER – osoby a organizace ===\n")

try:
    import spacy
    SPACY_OK = True
except ImportError:
    SPACY_OK = False
    print("spaCy není nainstalováno: pip install spacy")
    print("python -m spacy download en_core_web_sm\n")

NOVINOVY_CLANEK = """
Elon Musk, CEO of Tesla and SpaceX, announced yesterday that the company
will partner with Google to develop new artificial intelligence systems.
The deal was confirmed by Sundar Pichai, CEO of Alphabet Inc.
Apple CEO Tim Cook expressed interest in similar partnerships.
The announcement was made at the World Economic Forum in Davos, Switzerland.
Microsoft president Brad Smith called it "a historic moment for Silicon Valley."
The European Union's Margrethe Vestager expressed concerns about competition.
Meanwhile, Meta's Mark Zuckerberg declined to comment from his office in Menlo Park, California.
"""

def extrahuj_entity(text: str) -> dict[str, list[str]]:
    """
    Extrahuje pojmenované entity z textu.
    Bez spaCy – jednoduchá heuristika na základě regex + seznamů.
    """
    # Jednoduchá heuristika: entity začínají velkým písmenem
    # a nejsou na začátku věty
    vety   = re.split(r"[.!?]", text)
    osoby  = []
    org    = []
    mista  = []

    # Vzor pro osoby: "Jméno Příjmení"
    vzor_jmena = re.compile(r"\b([A-Z][a-z]+ [A-Z][a-z]+)\b")
    vzor_org   = re.compile(r"\b(Tesla|SpaceX|Google|Apple|Meta|Microsoft|"
                             r"Alphabet|Facebook|Amazon|OpenAI|Anthropic)\b")
    vzor_misto = re.compile(r"\b(Switzerland|California|Davos|Silicon Valley|"
                             r"Menlo Park|London|New York|Prague|Berlin)\b")

    for jmeno in vzor_jmena.findall(text):
        if jmeno not in osoby:
            osoby.append(jmeno)
    for o in vzor_org.findall(text):
        if o not in org:
            org.append(o)
    for m in vzor_misto.findall(text):
        if m not in mista:
            mista.append(m)

    return {"PERSON": osoby, "ORG": org, "GPE": mista}

if SPACY_OK:
    try:
        nlp = spacy.load("en_core_web_sm")
        doc = nlp(NOVINOVY_CLANEK.strip())

        entity_dict: dict[str, list[str]] = {}
        for ent in doc.ents:
            entity_dict.setdefault(ent.label_, [])
            if ent.text not in entity_dict[ent.label_]:
                entity_dict[ent.label_].append(ent.text)

        print("Extrahované entity (spaCy):")
        for label in ["PERSON", "ORG", "GPE", "LOC"]:
            if label in entity_dict:
                print(f"  {label:<8}: {', '.join(entity_dict[label][:5])}")

    except OSError:
        print("Model en_core_web_sm není stažen.")
        print("Spusť: python -m spacy download en_core_web_sm")
        print("\nFallback – jednoduchá heuristika:")
        entity_dict = extrahuj_entity(NOVINOVY_CLANEK)
        for label, hodnoty in entity_dict.items():
            print(f"  {label:<8}: {', '.join(hodnoty[:5])}")
else:
    print("Fallback – jednoduchá regex heuristika:")
    entity_dict = extrahuj_entity(NOVINOVY_CLANEK)
    for label, hodnoty in entity_dict.items():
        print(f"  {label:<8}: {', '.join(hodnoty[:5])}")

    print("\nPro plnou NER funkčnost:")
    print("  pip install spacy")
    print("  python -m spacy download en_core_web_sm")
    print("\n  Pak:")
    print("  import spacy")
    print("  nlp = spacy.load('en_core_web_sm')")
    print("  doc = nlp(clanek)")
    print("  osoby = [e.text for e in doc.ents if e.label_ == 'PERSON']")

print("\n=== Shrnutí ===")
print("  1. klic_slova()           – TF-IDF bez knihoven, bonus za délku slova")
print("  2. sentiment_rozsirenyi() – detekce negací (not/no/ne)")
print("  3. extrahuj_entity()      – spaCy NER nebo regex fallback")
