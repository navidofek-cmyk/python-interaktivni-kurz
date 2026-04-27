"""
LEKCE 81: NLP – zpracování přirozeného jazyka
================================================
pip install nltk spacy textblob
python -m spacy download cs_core_news_sm   # český model
python -m spacy download en_core_web_sm    # anglický model

NLP = Natural Language Processing.
Počítač analyzuje a rozumí lidskému textu.

Základní úkoly:
  Tokenizace    – rozdělení textu na slova/věty
  POS tagging   – určení slovních druhů
  NER           – pojmenované entity (osoby, místa, organizace)
  Sentiment     – pozitivní / negativní / neutrální
  Podobnost     – jak moc jsou dva texty podobné
"""

import re
import math
from collections import Counter

# ══════════════════════════════════════════════════════════════
# ČÁST 1: Základní NLP bez knihoven
# ══════════════════════════════════════════════════════════════

print("=== NLP bez knihoven – základ ===\n")

TEXT_CZ = """
Python je interpretovaný programovací jazyk vysoké úrovně.
Byl navržen Guido van Rossumem a poprvé vydán v roce 1991.
Python klade důraz na čitelnost kódu. Jazyk Python se používá
pro webový vývoj, datovou vědu, umělou inteligenci a automatizaci.
Anthropic vyvíjí Claude – jazykový model postavený na Pythonu.
"""

def tokenizuj(text: str) -> list[str]:
    """Jednoduchý tokenizer bez knihoven."""
    text = text.lower()
    text = re.sub(r"[^\w\s]", "", text)   # odstraň interpunkci
    return text.split()

def vety(text: str) -> list[str]:
    return [v.strip() for v in re.split(r"[.!?]+", text) if v.strip()]

def frekvence_slov(tokeny: list[str], stop_slova: set) -> dict:
    return {s: n for s, n in Counter(tokeny).most_common(20)
            if s not in stop_slova and len(s) > 2}

# Česká stop slova (zjednodušená)
STOP_CZ = {"a", "v", "na", "pro", "se", "je", "byl", "jsou",
            "byl", "byla", "bylo", "i", "o", "z", "do", "s", "k",
            "to", "ten", "ta", "tato", "tento", "byl", "jako"}

tokeny = tokenizuj(TEXT_CZ)
freq   = frekvence_slov(tokeny, STOP_CZ)
vety_  = vety(TEXT_CZ)

print(f"Text: {len(tokeny)} tokenů, {len(vety_)} vět")
print(f"\nTop 10 slov: {list(freq.items())[:10]}")
print(f"\nVěty:")
for i, v in enumerate(vety_[:3], 1):
    print(f"  {i}. {v[:80]}")


# ══════════════════════════════════════════════════════════════
# ČÁST 2: TF-IDF – důležitost slov v dokumentu
# ══════════════════════════════════════════════════════════════

print("\n=== TF-IDF (bez knihoven) ===\n")

dokumenty = [
    "Python je skvělý programovací jazyk pro datovou vědu",
    "Java je objektově orientovaný programovací jazyk",
    "Python se používá v datové vědě a strojovém učení",
    "JavaScript běží v prohlížeči a na serveru Node.js",
]

def spocti_tfidf(dokumenty: list[str]) -> list[dict]:
    """TF-IDF bez knihoven."""
    N = len(dokumenty)
    vsechny_tokeny = [set(d.lower().split()) for d in dokumenty]
    vysledky = []

    for doc_tokeny, doc in zip(vsechny_tokeny, dokumenty):
        slova = doc.lower().split()
        tf    = Counter(slova)
        tfidf = {}
        for slovo in set(slova):
            # TF = frekvence v dokumentu
            tf_val = tf[slovo] / len(slova)
            # IDF = log(N / počet dokumentů obsahujících slovo)
            df     = sum(1 for t in vsechny_tokeny if slovo in t)
            idf    = math.log(N / df)
            tfidf[slovo] = round(tf_val * idf, 4)
        vysledky.append(dict(sorted(tfidf.items(), key=lambda x: -x[1])[:5]))

    return vysledky

tfidf_vysledky = spocti_tfidf(dokumenty)
print("Klíčová slova (TF-IDF) pro každý dokument:")
for doc, skore in zip(dokumenty, tfidf_vysledky):
    print(f"\n  Doc: {doc[:50]}...")
    print(f"  Klíčová: {list(skore.keys())[:3]}")


# ══════════════════════════════════════════════════════════════
# ČÁST 3: Sentiment analýza (jednoduchá)
# ══════════════════════════════════════════════════════════════

print("\n=== Sentiment analýza ===\n")

POZITIVNI = {"skvělý", "výborný", "báječný", "super", "perfektní",
              "dobrý", "great", "excellent", "good", "amazing", "love",
              "best", "fantastic", "wonderful", "awesome", "perfect"}
NEGATIVNI = {"špatný", "hrozný", "ošklivý", "příšerný", "terrible",
              "bad", "awful", "horrible", "worst", "hate", "poor",
              "disgusting", "failure", "broken", "useless"}

def sentiment(text: str) -> dict:
    slova = re.sub(r"[^\w\s]", "", text.lower()).split()
    pos   = sum(1 for s in slova if s in POZITIVNI)
    neg   = sum(1 for s in slova if s in NEGATIVNI)
    skore = (pos - neg) / max(len(slova), 1)
    label = "pozitivní" if skore > 0.02 else "negativní" if skore < -0.02 else "neutrální"
    return {"label": label, "skore": round(skore, 3), "pos": pos, "neg": neg}

recenze = [
    "This is an absolutely amazing and excellent Python library!",
    "The worst documentation I've ever seen. Broken and useless.",
    "It works fine. Nothing special.",
    "Skvělý kurz, výborné vysvětlení!",
    "Hrozný příklad, špatný kód.",
]

for r in recenze:
    s = sentiment(r)
    ikona = "😊" if s["label"] == "pozitivní" else "😞" if s["label"] == "negativní" else "😐"
    print(f"  {ikona} {s['label']:12} ({s['skore']:+.3f})  {r[:50]}")


# ══════════════════════════════════════════════════════════════
# ČÁST 4: spaCy – průmyslový NLP
# ══════════════════════════════════════════════════════════════

print("\n=== spaCy ===\n")

try:
    import spacy
    SPACY_OK = True
except ImportError:
    SPACY_OK = False
    print("spaCy není nainstalováno: pip install spacy")
    print("python -m spacy download en_core_web_sm")

if SPACY_OK:
    try:
        nlp = spacy.load("en_core_web_sm")

        text_en = """
        Apple CEO Tim Cook announced that Python is used extensively
        at Apple headquarters in Cupertino, California.
        The company, founded by Steve Jobs in 1976, uses Python
        for machine learning and data analysis.
        """

        doc = nlp(text_en.strip())

        print("Pojmenované entity (NER):")
        for ent in doc.ents:
            print(f"  {ent.text:<25} → {ent.label_:10} ({spacy.explain(ent.label_)})")

        print("\nSlovní druhy (POS tagging) – prvních 10 slov:")
        for token in list(doc)[:10]:
            if not token.is_space:
                print(f"  {token.text:<15} {token.pos_:8} {token.lemma_}")

        print("\nZávislostní analýza (první věta):")
        prvni_veta = list(doc.sents)[0]
        for token in prvni_veta:
            if token.dep_ in ("nsubj", "dobj", "ROOT"):
                print(f"  {token.text:<15} {token.dep_:10} → {token.head.text}")

        # Podobnost dokumentů
        doc1 = nlp("Python is a programming language")
        doc2 = nlp("Python is used for data science")
        doc3 = nlp("I love cooking pasta")
        print(f"\nPodobnost doc1 × doc2: {doc1.similarity(doc2):.3f}")
        print(f"Podobnost doc1 × doc3: {doc1.similarity(doc3):.3f}")

    except OSError:
        print("  Model en_core_web_sm není stažen.")
        print("  Spusť: python -m spacy download en_core_web_sm")

print("""
=== Přehled NLP knihoven ===

  NLTK        → akademický, mnoho algoritmů, česká podpora
  spaCy       → rychlý, produkční, modely pro 60+ jazyků
  Transformers→ BERT, GPT, moderní deep learning NLP (pip install transformers)
  textblob    → jednoduchý sentiment a překlad
  gensim      → Word2Vec, topic modeling (LDA)

  Modely spaCy:
    cs_core_news_sm  – čeština (malý model)
    en_core_web_sm   – angličtina (malý)
    en_core_web_lg   – angličtina (velký, přesnější)
""")

# TVOJE ÚLOHA:
# 1. Napiš funkci klic_slova(text, n=5) která vrátí n nejdůležitějších slov.
# 2. Porovnej sentiment recenzí produktů z reálného datasetu (kaggle.com).
# 3. Použij spaCy NER na stažený novinový článek a extrahuj všechny osoby a organizace.
