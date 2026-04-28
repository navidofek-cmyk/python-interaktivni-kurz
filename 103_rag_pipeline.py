"""
LEKCE 103: RAG – Retrieval Augmented Generation
=================================================
pip install numpy  (volitelné: langchain openai chromadb)

Co je RAG a proč ho potřebuješ:
  - LLM má kontextové okno (omezená paměť na jedno volání)
  - Nedokáže si zapamatovat firemní dokumenty, novou dokumentaci atd.
  - Řešení: PŘED dotazem najdi relevantní dokumenty a vlož je do kontextu

Průběh RAG pipeline:
  1. INDEXOVÁNÍ: Dokumenty → chunky → embeddingy → vektorová DB
  2. RETRIEVAL:  Dotaz → embedding → kosinová podobnost → top-k chunků
  3. GENEROVÁNÍ: Dotaz + chunky → LLM → odpověď

Spuštění: python3 103_rag_pipeline.py
Nevyžaduje API klíč – embeddingy jsou simulovány.
"""

import os, json, math, random, textwrap, time
from typing import NamedTuple

OPENAI_KEY    = os.getenv("OPENAI_API_KEY", "")
ANTHROPIC_KEY = os.getenv("ANTHROPIC_API_KEY", "")

# ══════════════════════════════════════════════════════════════════
# ČÁST 1: CO JE EMBEDDING – TEORIE
# ══════════════════════════════════════════════════════════════════

print("=" * 60)
print("ČÁST 1: Embeddingy – text jako vektor čísel")
print("=" * 60)

print("""
Co je embedding:
  Text → seznam čísel (vektor) v N-dimenzionálním prostoru.
  Podobné texty mají podobné vektory (malá vzdálenost).

  "Pes štěká"   → [0.82, -0.14,  0.33, ...]   ┐ blízko u sebe
  "Pes vyjí"    → [0.79, -0.11,  0.31, ...]   ┘
  "Akcie klesly"→ [-0.22, 0.71, -0.44, ...]     daleko

Dimenze:
  text-embedding-3-small  (OpenAI)  → 1536 dimenzí
  text-embedding-3-large  (OpenAI)  → 3072 dimenzí
  nomic-embed-text        (lokální) → 768 dimenzí
""")

# ══════════════════════════════════════════════════════════════════
# ČÁST 2: KOSINOVÁ PODOBNOST
# ══════════════════════════════════════════════════════════════════

print("=" * 60)
print("ČÁST 2: Kosinová podobnost – jak hledáme relevantní dokumenty")
print("=" * 60)

def kosinus_podobnost(a: list[float], b: list[float]) -> float:
    """
    Kosinová podobnost dvou vektorů.
    Výsledek: 1.0 = identické směr, 0.0 = kolmé, -1.0 = opačné.
    """
    skalar = sum(x * y for x, y in zip(a, b))
    norma_a = math.sqrt(sum(x * x for x in a))
    norma_b = math.sqrt(sum(y * y for y in b))
    if norma_a == 0 or norma_b == 0:
        return 0.0
    return skalar / (norma_a * norma_b)

# Demonstrace na malých vektorech (3D místo 1536D)
print("\n--- Kosinová podobnost na příkladu (3D vektory) ---")
vektory = {
    "Pes štěká":     [0.82, -0.14,  0.33],
    "Pes vyjí":      [0.79, -0.11,  0.31],
    "Kočka mňouká":  [0.61, -0.09,  0.42],
    "Akcie klesly":  [-0.22, 0.71, -0.44],
    "Bitcoin roste": [-0.18, 0.69, -0.51],
}

dotaz_vektor = [0.80, -0.12, 0.35]  # reprezentuje "zvíře dělá zvuk"
print(f"\nDotaz (vektor): {dotaz_vektor}")
print("Podobnost s dokumenty:")
vysledky = []
for text, vektor in vektory.items():
    sim = kosinus_podobnost(dotaz_vektor, vektor)
    vysledky.append((sim, text))
    print(f"  {sim:.3f}  {text}")

vysledky.sort(reverse=True)
print(f"\nNejrelevantnější: {vysledky[0][1]!r} (skóre {vysledky[0][0]:.3f})")

# ══════════════════════════════════════════════════════════════════
# ČÁST 3: SIMULACE EMBEDDINGŮ (bez API)
# ══════════════════════════════════════════════════════════════════

print("\n" + "=" * 60)
print("ČÁST 3: Simulace embeddingů (deterministická)")
print("=" * 60)

def simuluj_embedding(text: str, dim: int = 64) -> list[float]:
    """
    Deterministická simulace embeddingu.
    Reálný embedding: OpenAI / local model.
    Tato funkce: hash textu → seed → pseudo-náhodný vektor.
    POZOR: Tato simulace NEREFLEKTUJE sémantiku.
    """
    seed = hash(text) % (2**31)
    rng = random.Random(seed)
    vektor = [rng.gauss(0, 1) for _ in range(dim)]
    # Normalizace (unit vector)
    norma = math.sqrt(sum(x*x for x in vektor))
    return [x / norma for x in vektor]

print("\nUkázka simulovaného embeddingu (prvních 8 dimenzí z 64):")
text = "Python je skvělý programovací jazyk"
emb = simuluj_embedding(text)
print(f"  {text!r}")
print(f"  → [{', '.join(f'{x:.3f}' for x in emb[:8])}, ...]")
print(f"  Norma vektoru: {math.sqrt(sum(x*x for x in emb)):.4f} (≈1.0 = normalizováno)")

print("\n--- Reálné API (OpenAI embeddings) ---")
if OPENAI_KEY:
    print("API klíč nalezen – voláme OpenAI...")
    try:
        from openai import OpenAI
        client = OpenAI()
        response = client.embeddings.create(
            input=text,
            model="text-embedding-3-small"
        )
        real_emb = response.data[0].embedding
        print(f"  Reálný embedding: dim={len(real_emb)}, první 4: {real_emb[:4]}")
    except Exception as e:
        print(f"  Chyba: {e}")
else:
    print("  OPENAI_API_KEY není nastaven.")
    print("  Co by se stalo:")
    print("    from openai import OpenAI")
    print("    client = OpenAI()")
    print("    resp = client.embeddings.create(input=text, model='text-embedding-3-small')")
    print("    embedding = resp.data[0].embedding  # list[float], len=1536")

# ══════════════════════════════════════════════════════════════════
# ČÁST 4: JEDNODUCHÝ RAG BEZ FRAMEWORKU
# ══════════════════════════════════════════════════════════════════

print("\n" + "=" * 60)
print("ČÁST 4: Jednoduchý RAG pipeline (numpy-free, bez frameworku)")
print("=" * 60)

class Dokument(NamedTuple):
    id: str
    text: str
    metadata: dict

class JednoduchaVektorovaDB:
    """Minimální vektorová DB – jen pro demonstraci."""

    def __init__(self, dim: int = 64):
        self.dim = dim
        self.dokumenty: list[Dokument] = []
        self.embeddingy: list[list[float]] = []

    def pridej(self, dok: Dokument) -> None:
        """Přidá dokument a vypočítá jeho embedding."""
        self.dokumenty.append(dok)
        self.embeddingy.append(simuluj_embedding(dok.text, self.dim))

    def hledej(self, dotaz: str, top_k: int = 3) -> list[tuple[float, Dokument]]:
        """Vrátí top_k nejrelevantnějších dokumentů."""
        dotaz_emb = simuluj_embedding(dotaz, self.dim)
        podobnosti = [
            (kosinus_podobnost(dotaz_emb, emb), dok)
            for emb, dok in zip(self.embeddingy, self.dokumenty)
        ]
        podobnosti.sort(key=lambda x: x[0], reverse=True)
        return podobnosti[:top_k]

# Vytvoříme znalostní bázi (dokumentace kurzu)
print("\n--- Indexování dokumentů kurzu ---")
dokumenty_kurzu = [
    Dokument("l01", "Python je interpretovaný programovací jazyk s dynamickým typováním.", {"lekce": 1}),
    Dokument("l22", "Třídy v Pythonu: class Jmeno: definuje třídu. __init__ je konstruktor.", {"lekce": 22}),
    Dokument("l25", "Async/await umožňuje asynchronní programování. asyncio.run() spustí coroutine.", {"lekce": 25}),
    Dokument("l40", "SQLite: sqlite3.connect('db.sqlite') vytvoří databázi. cursor.execute() spustí SQL.", {"lekce": 40}),
    Dokument("l53", "NumPy: pole vytvoříme přes np.array(). Vektorizované operace jsou rychlé.", {"lekce": 53}),
    Dokument("l74", "LLM API: anthropic.Anthropic() vytvoří klienta. messages.create() zavolá model.", {"lekce": 74}),
    Dokument("l88", "PyTorch: torch.Tensor je základní datová struktura. nn.Module definuje model.", {"lekce": 88}),
    Dokument("l102","Prompt engineering: few-shot prompty obsahují příklady. CoT = přemýšlej krok za krokem.", {"lekce": 102}),
]

db = JednoduchaVektorovaDB(dim=64)
for dok in dokumenty_kurzu:
    db.pridej(dok)
    print(f"  Indexováno: lekce {dok.metadata['lekce']:>3} – {dok.text[:50]}...")

# Retrieval
print("\n--- Retrieval: hledáme relevantní dokumenty ---")
dotazy = [
    "Jak vytvořit třídu v Pythonu?",
    "Co je asyncio?",
    "Jak volat LLM model?",
]

for dotaz in dotazy:
    print(f"\nDotaz: {dotaz!r}")
    vysledky = db.hledej(dotaz, top_k=2)
    for skore, dok in vysledky:
        print(f"  {skore:.3f} | L{dok.metadata['lekce']:>3} | {dok.text[:60]}...")

# RAG generování
print("\n--- RAG: Dotaz + kontext → odpověď ---")

def rag_odpoved(dotaz: str, db: JednoduchaVektorovaDB, top_k: int = 3) -> str:
    """Celý RAG pipeline: retrieval + generování."""
    # 1. Retrieval
    relevantni = db.hledej(dotaz, top_k=top_k)

    # 2. Sestavení kontextu
    kontext_casti = []
    for skore, dok in relevantni:
        kontext_casti.append(f"[Lekce {dok.metadata['lekce']}, relevance {skore:.2f}]\n{dok.text}")
    kontext = "\n\n".join(kontext_casti)

    # 3. Prompt s kontextem
    prompt = f"""Odpověz na otázku POUZE na základě poskytnutého kontextu.
Pokud kontext neobsahuje odpověď, řekni to.

KONTEXT:
{kontext}

OTÁZKA: {dotaz}

ODPOVĚĎ:"""

    # 4. Generování (simulace)
    if ANTHROPIC_KEY:
        import anthropic
        client = anthropic.Anthropic()
        msg = client.messages.create(
            model="claude-opus-4-7",
            max_tokens=256,
            messages=[{"role": "user", "content": prompt}]
        )
        return msg.content[0].text
    else:
        # Simulace: vrátíme informaci z nejrelevantnějšího dokumentu
        best_dok = relevantni[0][1]
        return f"[SIMULACE] Na základě lekce {best_dok.metadata['lekce']}: {best_dok.text}"

dotaz_test = "Jak zavolám LLM model z Pythonu?"
print(f"\nDotaz: {dotaz_test!r}")
odpoved = rag_odpoved(dotaz_test, db)
print(f"Odpověď: {odpoved}")

# ══════════════════════════════════════════════════════════════════
# ČÁST 5: CHUNKING – ROZDĚLENÍ DOKUMENTŮ
# ══════════════════════════════════════════════════════════════════

print("\n" + "=" * 60)
print("ČÁST 5: Chunking – jak správně dělit dokumenty")
print("=" * 60)

def chunk_text(text: str, velikost: int = 200, prekryv: int = 40) -> list[str]:
    """
    Rozdělí text na chunky s překryvem.
    Překryv zajistí, že kontext na hranicích chunků není ztracen.
    """
    chunky = []
    start = 0
    while start < len(text):
        konec = start + velikost
        chunk = text[start:konec]
        # Zaokrouhli na konec věty pokud možno
        if konec < len(text):
            posl_tecka = chunk.rfind('. ')
            if posl_tecka > velikost // 2:
                chunk = chunk[:posl_tecka + 1]
                konec = start + posl_tecka + 1
        chunky.append(chunk.strip())
        start = konec - prekryv
    return [c for c in chunky if c]

dlouhy_text = """
Python je vysokoúrovňový programovací jazyk. Byl vytvořen Guidem van Rossumem v roce 1991.
Je známý svou čitelností a jednoduchostí. Python se používá v datové vědě, webovém vývoji,
automatizaci a umělé inteligenci. Velkou výhodou je bohatá standardní knihovna.
NumPy, Pandas a Scikit-learn jsou populární knihovny pro data science.
FastAPI a Django jsou oblíbené frameworky pro webový vývoj.
LangChain a LlamaIndex usnadňují práci s LLM modely.
""".strip()

chunky = chunk_text(dlouhy_text, velikost=150, prekryv=30)
print(f"\nText ({len(dlouhy_text)} znaků) rozdělen na {len(chunky)} chunků:")
for i, chunk in enumerate(chunky):
    print(f"\n  Chunk {i+1} ({len(chunk)} znaků):")
    print(textwrap.indent(chunk, "    "))

# ══════════════════════════════════════════════════════════════════
# ČÁST 6: PRODUKČNÍ RAG – LANGCHAIN / CHROMADB (popis)
# ══════════════════════════════════════════════════════════════════

print("\n" + "=" * 60)
print("ČÁST 6: Produkční RAG s LangChain + ChromaDB")
print("=" * 60)

print("\nInstalace:")
print("  pip install langchain langchain-openai chromadb")

produkční_kod = '''
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import Chroma
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains import RetrievalQA

# 1. INDEXOVÁNÍ
splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
chunks = splitter.create_documents(moje_dokumenty)

embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
vectorstore = Chroma.from_documents(chunks, embeddings, persist_directory="./chroma_db")

# 2. RETRIEVAL + GENEROVÁNÍ
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
retriever = vectorstore.as_retriever(search_kwargs={"k": 4})

qa_chain = RetrievalQA.from_chain_type(
    llm=llm,
    retriever=retriever,
    return_source_documents=True,
)

result = qa_chain.invoke({"query": "Jak funguje async v Pythonu?"})
print(result["result"])
print([doc.metadata for doc in result["source_documents"]])
'''

print("\nProdukční kód (vyžaduje API klíče):")
print(produkční_kod)

if OPENAI_KEY:
    print("OPENAI_API_KEY je nastaven – výše uvedený kód by fungoval.")
else:
    print("Nastav OPENAI_API_KEY a výše uvedený kód spusť.")

# ══════════════════════════════════════════════════════════════════
# SHRNUTÍ
# ══════════════════════════════════════════════════════════════════

print("\n" + "=" * 60)
print("SHRNUTÍ: RAG Pipeline")
print("=" * 60)
print("""
  INDEXOVÁNÍ           RETRIEVAL              GENEROVÁNÍ
  ──────────           ─────────              ──────────
  Dokument             Dotaz uživatele        Prompt = dotaz
     ↓                    ↓                      + kontext
  Chunking             Embedding dotazu          ↓
     ↓                    ↓                   LLM model
  Embedding            Kosinová podobnost        ↓
     ↓                    ↓                   Odpověď
  Vektorová DB ────→  Top-k chunků ──────→   s citacemi

  Kdy RAG:    Velké množství dokumentů, aktuální data
  Kdy ne RAG: Malé množství textu (vlož přímo do kontextu)
""")

# ══════════════════════════════════════════════════════════════════
# TVOJE ÚLOHA
# ══════════════════════════════════════════════════════════════════
print("""
╔══════════════════════════════════════════════════════════════╗
║  TVOJE ÚLOHA                                                 ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  1. Přidej do JednoduchaVektorovaDB metodu `odstran(id)`    ║
║     která odstraní dokument a jeho embedding podle ID.      ║
║                                                              ║
║  2. Vylepši funkci `chunk_text()` – přidej parametr         ║
║     `separator` (default "\n\n"), který rozděluje text       ║
║     primárně podle odstavců, ne pevné délky.                ║
║                                                              ║
║  3. Implementuj `hybrid_search(dotaz, db, alfa=0.5)` který   ║
║     kombinuje vektorové skóre s BM25-like skóre (počet      ║
║     shodných slov). alfa=1.0 = jen vektory, 0.0 = jen BM25. ║
║                                                              ║
║  4. BONUS: Přidej do RAG pipeline "citace" – výsledná        ║
║     odpověď musí obsahovat čísla lekcí odkud čerpala.       ║
║     Např.: "Async používá asyncio [L25]."                    ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
""")
