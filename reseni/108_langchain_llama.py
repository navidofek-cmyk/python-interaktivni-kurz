"""Řešení – Lekce 108: LangChain a LlamaIndex

Toto je vzorové řešení úloh z lekce 108.
"""

import hashlib
import random
import time
from dataclasses import dataclass, field
from functools import wraps
from typing import Optional


# ── Pomocné třídy ze lekce ─────────────────────────────────

class LLMCache:
    """In-memory cache pro LLM odpovědi."""

    def __init__(self, max_items: int = 1000):
        self._cache: dict[str, tuple[str, float]] = {}
        self._max_items = max_items
        self._hits = 0
        self._misses = 0

    def _klic(self, prompt: str, model: str, temperature: float) -> str:
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


# ── Úloha 1 ────────────────────────────────────────────────
# LLMCache.invalidate(prompt, model) – odstranění záznamu z cache

class LLMCacheRozsireny(LLMCache):
    """LLMCache rozšířený o metodu invalidate()."""

    def invalidate(
        self,
        prompt: str,
        model: str = "claude-opus-4-7",
        temperature: float = 0.0,
    ) -> bool:
        """
        Odstraní konkrétní záznam z cache.
        Vrátí True pokud byl záznam nalezen a odstraněn.
        Vhodné pro případ kdy víme, že odpověď je zastaralá.
        """
        klic = self._klic(prompt, model, temperature)
        if klic in self._cache:
            del self._cache[klic]
            return True
        return False


print("── Úloha 1: LLMCache.invalidate() ──")
cache = LLMCacheRozsireny()

# Naplníme cache
cache.set("Co je Python?", "Python je programovací jazyk.")
cache.set("Jak funguje async?", "async/await umožňuje asynchronní kód.")

print(f"Před invalidací: {cache.stats()['cached_items']} záznamů")

ok = cache.invalidate("Co je Python?")
print(f"Invalidace 'Co je Python?': {ok}")
print(f"Po invalidaci: {cache.stats()['cached_items']} záznamů")

# Znovu načteme – cache miss
cached = cache.get("Co je Python?")
print(f"Cache get po invalidaci: {cached!r}  (None = cache miss)")

ok_neexist = cache.invalidate("Neexistující dotaz")
print(f"Invalidace neexistujícího: {ok_neexist}")


# ── Úloha 2 ────────────────────────────────────────────────
# FakeVectorIndex s skórováním dokumentů

@dataclass
class FakeDocument:
    text: str
    metadata: dict = field(default_factory=dict)


@dataclass
class FakeResponse:
    response: str
    source_nodes: list


class FakeVectorIndex:
    """
    Simuluje VectorStoreIndex s skórováním dokumentů
    podle počtu shodných slov s dotazem.
    """

    def __init__(self, documents: list[FakeDocument]):
        self.documents = documents
        print(f"  Indexováno {len(documents)} dokumentů")

    def _skore(self, dotaz: str, doc: FakeDocument) -> int:
        """Vrátí počet shodných slov dotazu a textu dokumentu."""
        slova_dotazu = set(dotaz.lower().split())
        slova_textu = set(doc.text.lower().split())
        return len(slova_dotazu & slova_textu)

    def as_query_engine(self, similarity_top_k: int = 3) -> "FakeQueryEngine":
        return FakeQueryEngine(self.documents, similarity_top_k)


class FakeQueryEngine:
    def __init__(self, documents: list[FakeDocument], top_k: int = 3):
        self.documents = documents
        self.top_k = top_k

    def _skore(self, dotaz: str, doc: FakeDocument) -> int:
        slova_dotazu = set(dotaz.lower().split())
        slova_textu = set(doc.text.lower().split())
        return len(slova_dotazu & slova_textu)

    def query(self, q: str) -> FakeResponse:
        """Vrátí dokumenty seřazené podle skóre (počet shodných slov)."""
        scored = [(self._skore(q, d), d) for d in self.documents]
        scored.sort(key=lambda x: x[0], reverse=True)
        # Filtruj dokumenty se skóre > 0
        relevantni = [d for skore, d in scored if skore > 0][: self.top_k]

        if not relevantni:
            text = "Na tuto otázku nemám v dokumentech odpověď."
        else:
            best = relevantni[0]
            text = f"[SIMULACE RAG] {best.text[:120]}..."
        return FakeResponse(text, relevantni)


print("\n── Úloha 2: FakeVectorIndex se skórováním ──")

documents = [
    FakeDocument("Lekce 74: LLM API. anthropic.Anthropic() vytvoří klienta.", {"lekce": 74}),
    FakeDocument("Lekce 102: Prompt engineering. Few-shot a chain-of-thought prompty.", {"lekce": 102}),
    FakeDocument("Lekce 103: RAG pipeline. Embeddingy a kosinová podobnost.", {"lekce": 103}),
    FakeDocument("Lekce 25: Async/await. asyncio.run() spustí coroutine.", {"lekce": 25}),
    FakeDocument("Lekce 53: NumPy. np.array() vytvoří pole pro maticové operace.", {"lekce": 53}),
]

index = FakeVectorIndex(documents)
engine = index.as_query_engine(similarity_top_k=2)

dotazy = [
    "Jak zavolám LLM API klienta?",
    "Co je few-shot prompt?",
    "Jak funguje async coroutine?",
]
for dotaz in dotazy:
    resp = engine.query(dotaz)
    lekce = [d.metadata.get("lekce") for d in resp.source_nodes]
    print(f"\n  Dotaz: {dotaz!r}")
    print(f"  Relevantní lekce (seřazené): {lekce}")
    print(f"  Odpověď: {resp.response[:90]}...")


# ── Úloha 3 ────────────────────────────────────────────────
# streaming_demo() – simulace streamingu znak po znaku

def streaming_demo(text: str, min_delay_ms: int = 10, max_delay_ms: int = 50) -> None:
    """
    Simuluje streaming LLM odpovědi: tiskne text znak po znaku
    s náhodným zpožděním 10–50 ms mezi znaky.
    Demonstruje UX výhodu streamingu oproti čekání na celou odpověď.
    """
    print("  [Streaming start]", end="", flush=True)
    for znak in text:
        print(znak, end="", flush=True)
        time.sleep(random.randint(min_delay_ms, max_delay_ms) / 1000)
    print("  [Streaming end]")


print("\n── Úloha 3: streaming_demo() ──")
print("Simulace streamingu (rychlá verze pro demo):")
ukazka_text = "Python je skvělý jazyk pro AI vývoj.\nKaždý token přichází postupně."
# Použij krátká zpoždění pro demo (5-15ms místo 10-50ms)
streaming_demo(ukazka_text, min_delay_ms=5, max_delay_ms=15)


# ── Úloha 4 (BONUS) ────────────────────────────────────────
# Reálný LCEL chain (s graceful fallback bez API klíče)

print("\n── Úloha 4 (BONUS): LCEL chain s ChatAnthropic ──")

import os
ANTHROPIC_KEY = os.getenv("ANTHROPIC_API_KEY", "")

PYTHON_OTAZKY = [
    "Co je list comprehension a kdy ho použít?",
    "Jaký je rozdíl mezi `is` a `==` v Pythonu?",
    "Vysvětli rozdíl mezi `*args` a `**kwargs`.",
]

if ANTHROPIC_KEY:
    try:
        from langchain_anthropic import ChatAnthropic
        from langchain_core.prompts import ChatPromptTemplate
        from langchain_core.output_parsers import StrOutputParser

        llm = ChatAnthropic(model="claude-opus-4-7", max_tokens=256)
        prompt = ChatPromptTemplate.from_messages([
            ("system", "Jsi Python expert. Odpovídej česky, stručně (max 3 věty)."),
            ("human", "{otazka}"),
        ])
        chain = prompt | llm | StrOutputParser()

        for otazka in PYTHON_OTAZKY:
            print(f"\n  Otázka: {otazka!r}")
            odpoved = chain.invoke({"otazka": otazka})
            print(f"  Odpověď: {odpoved[:200]}")

    except ImportError:
        print("  langchain-anthropic není nainstalován.")
        print("  Nainstaluj: pip install langchain langchain-anthropic")
else:
    print("  ANTHROPIC_API_KEY není nastaven – simulace:")
    # Simulace LCEL chain bez API
    simul_odpovedi = {
        PYTHON_OTAZKY[0]: "List comprehension je zkrácená syntaxe pro vytvoření seznamu: `[x*2 for x in range(5)]`. Používej ho pro jednoduché transformace; pro složitou logiku raději klasický for.",
        PYTHON_OTAZKY[1]: "`is` porovnává identitu objektů (stejná adresa v paměti), `==` porovnává hodnoty. Pro None a booleany používej `is`, jinak `==`.",
        PYTHON_OTAZKY[2]: "`*args` zachytí poziční argumenty jako tuple, `**kwargs` zachytí klíčové argumenty jako dict. Umožňují funkci přijmout libovolný počet parametrů.",
    }

    for otazka in PYTHON_OTAZKY:
        print(f"\n  Otázka: {otazka!r}")
        print(f"  [SIMULACE] {simul_odpovedi[otazka]}")

    print("\n  Pro reálné volání nastav ANTHROPIC_API_KEY a nainstaluj langchain-anthropic.")
