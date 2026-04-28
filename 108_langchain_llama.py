"""
LEKCE 108: LangChain a LlamaIndex
===================================
pip install langchain langchain-openai langchain-anthropic
pip install llama-index llama-index-llms-anthropic

Proč frameworky:
  Raw API je OK pro jednoduché use-cases.
  LangChain/LlamaIndex řeší:
    - Chaining: skládání kroků do pipeline
    - Memory: správa konverzační historie
    - Retrieval: hotový RAG pipeline
    - Caching: neplatit za stejné dotazy dvakrát
    - Retry: automatické opakování při chybě

Kdy co:
  LangChain    → komplexní chains, agenti, integrace
  LlamaIndex   → dokumenty, indexy, query engine
  Raw API      → jednoduchá volání, plná kontrola

Spuštění: python3 108_langchain_llama.py
Graceful demo bez API klíče.
"""

import os, json, time, textwrap, hashlib
from typing import Any, Optional
from dataclasses import dataclass, field
from functools import wraps

OPENAI_KEY    = os.getenv("OPENAI_API_KEY", "")
ANTHROPIC_KEY = os.getenv("ANTHROPIC_API_KEY", "")

# ══════════════════════════════════════════════════════════════════
# ČÁST 1: LANGCHAIN – ZÁKLADY
# ══════════════════════════════════════════════════════════════════

print("=" * 60)
print("ČÁST 1: LangChain – Chains a LCEL")
print("=" * 60)

print("""
LangChain Expression Language (LCEL):
  Řetězení pomocí pipe operátoru (|)

  prompt | model | output_parser

  Každý krok:
    Přijme vstup (dict nebo string)
    Vrátí výstup (dict nebo string)
    Může být paralelní (RunnableParallel)
""")

# Demonstrace LCEL pattern bez závislosti
class FakeRunnable:
    """Simuluje LCEL Runnable pro demonstraci."""

    def __init__(self, name: str, transform=None):
        self.name = name
        self._transform = transform or (lambda x: x)

    def invoke(self, vstup: Any) -> Any:
        return self._transform(vstup)

    def __or__(self, other: "FakeRunnable") -> "FakeChain":
        return FakeChain([self, other])

class FakeChain:
    """Simuluje LCEL chain."""

    def __init__(self, steps: list):
        self.steps = steps

    def __or__(self, other) -> "FakeChain":
        return FakeChain(self.steps + [other])

    def invoke(self, vstup: Any) -> Any:
        result = vstup
        for step in self.steps:
            print(f"    [Chain] {step.name}: {str(vstup)[:40]} → ...", end="")
            result = step.invoke(result)
            print(f" {str(result)[:40]}")
            vstup = result
        return result

# Simulace LCEL pipeline
prompt_template = FakeRunnable(
    "PromptTemplate",
    lambda x: f"Vysvětli {x['tema']} pro {x['uroven']} programátory v {x['jazyk']}."
)

chat_model = FakeRunnable(
    "ChatModel (simulace)",
    lambda x: f"[SIMULACE] Odpověď na: {x[:60]}..."
)

str_parser = FakeRunnable(
    "StrOutputParser",
    lambda x: x.strip()
)

chain = prompt_template | chat_model | str_parser

print("\n--- LCEL Chain demonstrace ---")
print("chain = prompt_template | chat_model | str_parser")
print("\nchain.invoke({'tema': 'dekorátory', 'uroven': 'začínající', 'jazyk': 'češtině'}):")
result = chain.invoke({"tema": "dekorátory", "uroven": "začínající", "jazyk": "češtině"})
print(f"\nVýsledek: {result}")

# ══════════════════════════════════════════════════════════════════
# ČÁST 2: SKUTEČNÝ LANGCHAIN KÓD
# ══════════════════════════════════════════════════════════════════

print("\n" + "=" * 60)
print("ČÁST 2: Skutečný LangChain kód")
print("=" * 60)

langchain_kod = '''
# pip install langchain langchain-anthropic langchain-openai

from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser, JsonOutputParser
from langchain_core.runnables import RunnableParallel, RunnablePassthrough

# --- Základní chain ---
llm = ChatAnthropic(model="claude-opus-4-7", max_tokens=512)

prompt = ChatPromptTemplate.from_messages([
    ("system", "Jsi Python expert. Odpovídej česky."),
    ("human", "{otazka}"),
])

chain = prompt | llm | StrOutputParser()

# Jednoduchá odpověď
odpoved = chain.invoke({"otazka": "Co je list comprehension?"})
print(odpoved)

# --- Streaming ---
for chunk in chain.stream({"otazka": "Vysvětli generátory"}):
    print(chunk, end="", flush=True)

# --- Paralelní volání ---
parallel_chain = RunnableParallel(
    kratka_odpoved=(prompt | llm | StrOutputParser()),
    json_odpoved=(
        ChatPromptTemplate.from_messages([
            ("human", "Vrať JSON s klíči 'tema' a 'obtiznost': {otazka}")
        ]) | llm | JsonOutputParser()
    ),
)

result = parallel_chain.invoke({"otazka": "async/await"})
# result = {"kratka_odpoved": "...", "json_odpoved": {"tema": "...", "obtiznost": ...}}

# --- Memory (konverzační) ---
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory

history = ChatMessageHistory()

chain_s_pameti = RunnableWithMessageHistory(
    prompt | llm | StrOutputParser(),
    lambda session_id: history,
    input_messages_key="otazka",
    history_messages_key="history",
)

chain_s_pameti.invoke(
    {"otazka": "Jmenuji se Ivan."},
    config={"configurable": {"session_id": "session1"}},
)
# → model si pamatuje jméno v dalších zprávách
'''

print(langchain_kod)

if ANTHROPIC_KEY:
    print("ANTHROPIC_API_KEY nastaven – výše uvedený kód by fungoval.")
    try:
        from langchain_anthropic import ChatAnthropic
        from langchain_core.prompts import ChatPromptTemplate
        from langchain_core.output_parsers import StrOutputParser

        llm = ChatAnthropic(model="claude-opus-4-7", max_tokens=128)
        prompt = ChatPromptTemplate.from_messages([
            ("system", "Odpovídej česky, max 1 věta."),
            ("human", "{otazka}"),
        ])
        chain_real = prompt | llm | StrOutputParser()
        ans = chain_real.invoke({"otazka": "Co je Python?"})
        print(f"\nReálná odpověď: {ans}")
    except ImportError:
        print("  → Nainstaluj: pip install langchain langchain-anthropic")

# ══════════════════════════════════════════════════════════════════
# ČÁST 3: LLAMAINDEX – DOKUMENTY A INDEXY
# ══════════════════════════════════════════════════════════════════

print("\n" + "=" * 60)
print("ČÁST 3: LlamaIndex – dokumenty a query engine")
print("=" * 60)

print("""
LlamaIndex (dříve GPT Index):
  Zaměřen na RAG nad dokumenty.
  Klíčové koncepty:
    Document   – vstupní dokument (text, PDF, web)
    Index      – zpracované dokumenty (VectorStoreIndex, ...)
    Node       – chunk dokumentu s metadaty
    QueryEngine – rozhraní pro dotazy nad indexem
    Retriever  – vybírá relevantní nodes
""")

llamaindex_kod = '''
# pip install llama-index llama-index-llms-anthropic

from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, Settings
from llama_index.llms.anthropic import Anthropic
from llama_index.embeddings.openai import OpenAIEmbedding

# Konfigurace
Settings.llm = Anthropic(model="claude-opus-4-7")
Settings.embed_model = OpenAIEmbedding(model="text-embedding-3-small")
Settings.chunk_size = 512
Settings.chunk_overlap = 50

# Načtení dokumentů z adresáře (PDF, TXT, MD, ...)
documents = SimpleDirectoryReader("./dokumenty").load_data()

# Indexování (embeddingy + uložení)
index = VectorStoreIndex.from_documents(documents)

# Dotaz
query_engine = index.as_query_engine(similarity_top_k=4)
response = query_engine.query("Co je prompt engineering?")
print(response.response)
print("Zdroje:", [n.metadata for n in response.source_nodes])

# Uložení indexu na disk
index.storage_context.persist("./index_storage")

# Načtení uloženého indexu
from llama_index.core import StorageContext, load_index_from_storage
storage = StorageContext.from_defaults(persist_dir="./index_storage")
loaded_index = load_index_from_storage(storage)
'''

print("\nKód pro LlamaIndex RAG nad adresářem dokumentů:")
print(llamaindex_kod)

# ══════════════════════════════════════════════════════════════════
# ČÁST 4: CACHING A RETRY
# ══════════════════════════════════════════════════════════════════

print("\n" + "=" * 60)
print("ČÁST 4: Caching a Retry – produkční kód")
print("=" * 60)

# Implementace cachování (funguje bez závislostí)
class LLMCache:
    """
    Jednoduchý in-memory cache pro LLM odpovědi.
    V produkci: Redis, SQLite nebo langchain SQLiteCache.
    """

    def __init__(self, max_items: int = 1000):
        self._cache: dict[str, tuple[str, float]] = {}
        self._max_items = max_items
        self._hits = 0
        self._misses = 0

    def _klic(self, prompt: str, model: str, temperature: float) -> str:
        """Vytvoří klíč pro cache."""
        data = f"{model}:{temperature}:{prompt}"
        return hashlib.sha256(data.encode()).hexdigest()[:16]

    def get(self, prompt: str, model: str = "claude-opus-4-7", temperature: float = 0.0) -> Optional[str]:
        klic = self._klic(prompt, model, temperature)
        if klic in self._cache:
            self._hits += 1
            return self._cache[klic][0]
        self._misses += 1
        return None

    def set(self, prompt: str, odpoved: str, model: str = "claude-opus-4-7", temperature: float = 0.0) -> None:
        if len(self._cache) >= self._max_items:
            # LRU-like: odstraň nejstarší
            nejstarsi = min(self._cache.items(), key=lambda x: x[1][1])
            del self._cache[nejstarsi[0]]
        klic = self._klic(prompt, model, temperature)
        self._cache[klic] = (odpoved, time.time())

    def stats(self) -> dict:
        total = self._hits + self._misses
        return {
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": round(self._hits / total, 3) if total > 0 else 0.0,
            "cached_items": len(self._cache),
        }

cache = LLMCache()

def llm_s_cache(prompt: str, model: str = "claude-opus-4-7") -> tuple[str, bool]:
    """Zavolá LLM s cachováním. Vrátí (odpověď, cache_hit)."""
    cached = cache.get(prompt, model)
    if cached:
        return cached, True

    # Simulace volání API
    time.sleep(0.1)
    odpoved = f"[Odpověď na: {prompt[:40]}...]"
    cache.set(prompt, odpoved, model)
    return odpoved, False

print("\n--- Cache demonstrace ---")
prompty = [
    "Co je Python?",
    "Jak funguje async/await?",
    "Co je Python?",           # cache hit
    "Co je list comprehension?",
    "Co je Python?",           # cache hit
]

for prompt in prompty:
    resp, hit = llm_s_cache(prompt)
    status = "CACHE HIT" if hit else "API CALL"
    print(f"  [{status}] {prompt!r}")

print(f"\nCache statistiky: {cache.stats()}")

# Retry s exponenciálním backoff
def retry_decorator(max_pokusy: int = 3, base_delay: float = 1.0, backoff: float = 2.0):
    """
    Dekorátor pro automatické opakování při chybě.
    Exponenciální backoff: 1s, 2s, 4s, ...
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for pokus in range(max_pokusy):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if pokus == max_pokusy - 1:
                        raise
                    delay = base_delay * (backoff ** pokus)
                    print(f"  Pokus {pokus+1} selhal: {e}. Čekám {delay:.1f}s...")
                    time.sleep(delay)
        return wrapper
    return decorator

@retry_decorator(max_pokusy=3, base_delay=0.5)
def robustni_llm_volani(prompt: str) -> str:
    """LLM volání s automatickým retry."""
    # Simulace: první volání selže
    if not hasattr(robustni_llm_volani, "_pokus"):
        robustni_llm_volani._pokus = 0
    robustni_llm_volani._pokus += 1

    if robustni_llm_volani._pokus == 1:
        raise ConnectionError("Rate limit exceeded (simulace)")

    return f"Odpověď (pokus {robustni_llm_volani._pokus}): {prompt[:30]}..."

print("\n--- Retry demonstrace ---")
try:
    result = robustni_llm_volani("Co je Python?")
    print(f"  Výsledek: {result}")
except Exception as e:
    print(f"  Selhalo po všech pokusech: {e}")

# LangChain cache konfigurace
langchain_cache_kod = '''
# LangChain vestavěný cache (produkce)
from langchain_community.cache import SQLiteCache
from langchain.globals import set_llm_cache

# SQLite cache (persistentní)
set_llm_cache(SQLiteCache(database_path=".langchain_cache.db"))

# Redis cache (distribuovaný)
from langchain_community.cache import RedisCache
import redis
set_llm_cache(RedisCache(redis_=redis.Redis(host="localhost")))

# Po nastavení: cache je transparentní
# První volání → API request + uložení
# Druhé stejné volání → přečte z cache
odpoved = llm.invoke("Co je Python?")   # API call
odpoved = llm.invoke("Co je Python?")   # cache hit!
'''

print("\n--- LangChain cache konfigurace ---")
print(langchain_cache_kod)

# ══════════════════════════════════════════════════════════════════
# ČÁST 5: RAG NAD PDF S LLAMAINDEX
# ══════════════════════════════════════════════════════════════════

print("\n" + "=" * 60)
print("ČÁST 5: Praktický příklad – RAG nad dokumenty kurzu")
print("=" * 60)

# Simulace LlamaIndex RAG (bez závislostí)
class FakeDocument:
    def __init__(self, text: str, metadata: dict = None):
        self.text = text
        self.metadata = metadata or {}

class FakeVectorIndex:
    """Simuluje LlamaIndex VectorStoreIndex."""

    def __init__(self, documents: list[FakeDocument]):
        self.documents = documents
        print(f"  Indexováno {len(documents)} dokumentů")

    def as_query_engine(self):
        return FakeQueryEngine(self.documents)

class FakeQueryEngine:
    """Simuluje LlamaIndex QueryEngine."""

    def __init__(self, documents: list[FakeDocument]):
        self.documents = documents

    def query(self, q: str) -> "FakeResponse":
        # Jednoduchý keyword match
        relevantni = [
            d for d in self.documents
            if any(w.lower() in d.text.lower() for w in q.split())
        ][:3]
        if not relevantni:
            text = "Na tuto otázku nemám v dokumentech odpověď."
        else:
            text = f"[SIMULACE RAG] Nalezeno v {len(relevantni)} dokumentech: {relevantni[0].text[:100]}..."
        return FakeResponse(text, relevantni)

@dataclass
class FakeResponse:
    response: str
    source_nodes: list

print("\n--- Simulace LlamaIndex RAG ---")

# Dokumenty (části lekcí kurzu)
documents = [
    FakeDocument(
        "Lekce 74: LLM API. Anthropic klient: anthropic.Anthropic(). "
        "Volání: client.messages.create(model=..., messages=[...])",
        {"lekce": 74, "tema": "LLM API"}
    ),
    FakeDocument(
        "Lekce 102: Prompt engineering. Zero-shot: přímá otázka. "
        "Few-shot: příklady v promptu. CoT: přemýšlej krok za krokem.",
        {"lekce": 102, "tema": "Prompt Engineering"}
    ),
    FakeDocument(
        "Lekce 103: RAG pipeline. Embeddings převádějí text na vektor. "
        "Kosinová podobnost měří vzdálenost vektorů.",
        {"lekce": 103, "tema": "RAG"}
    ),
    FakeDocument(
        "Lekce 25: Async/await. asyncio.run() spustí coroutine. "
        "await čeká na výsledek bez blokování event loop.",
        {"lekce": 25, "tema": "Async"}
    ),
]

index = FakeVectorIndex(documents)
engine = index.as_query_engine()

dotazy = [
    "Jak zavolám Anthropic API?",
    "Co je CoT?",
    "Jak funguje async?",
]

for dotaz in dotazy:
    response = engine.query(dotaz)
    print(f"\n  Dotaz: {dotaz!r}")
    print(f"  Odpověď: {response.response[:100]}...")
    if response.source_nodes:
        lekce = [d.metadata.get('lekce') for d in response.source_nodes]
        print(f"  Zdroje: Lekce {lekce}")

# ══════════════════════════════════════════════════════════════════
# ČÁST 6: KDY CO POUŽÍT
# ══════════════════════════════════════════════════════════════════

print("\n" + "=" * 60)
print("ČÁST 6: Kdy LangChain, kdy LlamaIndex, kdy Raw API")
print("=" * 60)

print("""
┌─────────────────┬──────────────────────────────────────────────┐
│ Situace         │ Doporučení                                   │
├─────────────────┼──────────────────────────────────────────────┤
│ Jednoduchý chat │ Raw API (anthropic / openai)                 │
│ RAG nad PDF     │ LlamaIndex (SimpleDirectoryReader + Index)   │
│ Komplexní agent │ LangChain (chains, tools, memory)            │
│ RAG s custom DB │ LangChain + ChromaDB / Pinecone              │
│ Produkce        │ Raw API + vlastní cache/retry                │
│ Rychlý prototyp │ LangChain (hodně hotového)                   │
│ Čitelný kód     │ Raw API (méně magie)                         │
│ Mnoho dokumentů │ LlamaIndex (optimalizované indexy)           │
└─────────────────┴──────────────────────────────────────────────┘

Hlavní nevýhody frameworků:
  LangChain:   Breaking changes v API, složité debugování
  LlamaIndex:  Těžší customizace, mnoho abstrakcí
  Raw API:     Musíš implementovat vše ručně
""")

# SHRNUTÍ
print("=" * 60)
print("SHRNUTÍ")
print("=" * 60)
print("""
  LangChain:
    chain = prompt | llm | parser    (LCEL pipe)
    RunnableParallel pro paralelní kroky
    RunnableWithMessageHistory pro paměť

  LlamaIndex:
    VectorStoreIndex.from_documents(docs)
    index.as_query_engine().query("dotaz")

  Produkce:
    Cache (SQLite/Redis) → ušetří tokeny a peníze
    Retry + backoff → odolnost vůči rate limitům
    Streaming → lepší UX (token po tokenu)
""")

# ══════════════════════════════════════════════════════════════════
# TVOJE ÚLOHA
# ══════════════════════════════════════════════════════════════════
print("""
╔══════════════════════════════════════════════════════════════╗
║  TVOJE ÚLOHA                                                 ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  1. Přidej do LLMCache metodu `invalidate(prompt, model)`   ║
║     která odstraní konkrétní záznam z cache (pro případ     ║
║     kdy víme, že odpověď je zastaralá).                      ║
║                                                              ║
║  2. Vylepši FakeVectorIndex – přidej skórování dokumentů    ║
║     podle počtu shodných slov a vrať je seřazené.           ║
║                                                              ║
║  3. Implementuj `streaming_demo()` která simuluje streaming: ║
║     tiskne text znak po znaku s náhodným zpožděním 10-50ms. ║
║     To demonstruje UX výhodu streamingu.                     ║
║                                                              ║
║  4. BONUS: Nainstaluj langchain a langchain-anthropic a     ║
║     vytvoř reálný LCEL chain:                                ║
║     prompt | ChatAnthropic() | StrOutputParser()            ║
║     Otestuj s 3 různými otázkami o Pythonu.                  ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
""")
