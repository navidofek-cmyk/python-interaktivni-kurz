"""Řešení – Lekce 103: RAG – Retrieval Augmented Generation

Toto je vzorové řešení úloh z lekce 103.
"""

import math
import random
from typing import NamedTuple


# ── Pomocné funkce ze lekce ────────────────────────────────

def simuluj_embedding(text: str, dim: int = 64) -> list[float]:
    seed = hash(text) % (2 ** 31)
    rng = random.Random(seed)
    vektor = [rng.gauss(0, 1) for _ in range(dim)]
    norma = math.sqrt(sum(x * x for x in vektor))
    return [x / norma for x in vektor]


def kosinus_podobnost(a: list[float], b: list[float]) -> float:
    skalar = sum(x * y for x, y in zip(a, b))
    norma_a = math.sqrt(sum(x * x for x in a))
    norma_b = math.sqrt(sum(y * y for y in b))
    if norma_a == 0 or norma_b == 0:
        return 0.0
    return skalar / (norma_a * norma_b)


class Dokument(NamedTuple):
    id: str
    text: str
    metadata: dict


# ── Úloha 1 ────────────────────────────────────────────────
# JednoduchaVektorovaDB s metodou odstran(id)

class JednoduchaVektorovaDB:
    """Minimální vektorová DB s podporou přidání, hledání a odstranění."""

    def __init__(self, dim: int = 64):
        self.dim = dim
        self.dokumenty: list[Dokument] = []
        self.embeddingy: list[list[float]] = []

    def pridej(self, dok: Dokument) -> None:
        self.dokumenty.append(dok)
        self.embeddingy.append(simuluj_embedding(dok.text, self.dim))

    def hledej(self, dotaz: str, top_k: int = 3) -> list[tuple[float, Dokument]]:
        dotaz_emb = simuluj_embedding(dotaz, self.dim)
        podobnosti = [
            (kosinus_podobnost(dotaz_emb, emb), dok)
            for emb, dok in zip(self.embeddingy, self.dokumenty)
        ]
        podobnosti.sort(key=lambda x: x[0], reverse=True)
        return podobnosti[:top_k]

    def odstran(self, id: str) -> bool:
        """
        Odstraní dokument a jeho embedding podle ID.
        Vrátí True pokud byl dokument nalezen a odstraněn.
        """
        for i, dok in enumerate(self.dokumenty):
            if dok.id == id:
                self.dokumenty.pop(i)
                self.embeddingy.pop(i)
                return True
        return False


print("── Úloha 1: JednoduchaVektorovaDB.odstran() ──")
db = JednoduchaVektorovaDB()
db.pridej(Dokument("d1", "Python je interpretovaný jazyk.", {"lekce": 1}))
db.pridej(Dokument("d2", "Třídy a OOP v Pythonu.", {"lekce": 22}))
db.pridej(Dokument("d3", "Asyncio a asynchronní programování.", {"lekce": 25}))

print(f"Před odstraněním: {len(db.dokumenty)} dokumentů")
ok = db.odstran("d2")
print(f"Odstraněn d2: {ok}")
print(f"Po odstranění: {len(db.dokumenty)} dokumentů – {[d.id for d in db.dokumenty]}")
ok = db.odstran("neexistuje")
print(f"Odstraněn neexistuje: {ok}")


# ── Úloha 2 ────────────────────────────────────────────────
# Vylepšená chunk_text() s parametrem separator

def chunk_text(
    text: str,
    velikost: int = 200,
    prekryv: int = 40,
    separator: str = "\n\n",
) -> list[str]:
    """
    Rozdělí text na chunky.
    Primárně dělí podle `separator` (odstavce).
    Pokud je odstavec delší než `velikost`, rozdělí ho na pevné chunky s překryvem.
    """
    chunky: list[str] = []

    # Rozdělit primárně podle separátoru
    odstavce = [o.strip() for o in text.split(separator) if o.strip()]

    for odstavec in odstavce:
        if len(odstavec) <= velikost:
            chunky.append(odstavec)
        else:
            # Odstavec je příliš dlouhý – rozděl na pevné chunky s překryvem
            start = 0
            while start < len(odstavec):
                konec = start + velikost
                chunk = odstavec[start:konec]
                if konec < len(odstavec):
                    posl_tecka = chunk.rfind(". ")
                    if posl_tecka > velikost // 2:
                        chunk = chunk[: posl_tecka + 1]
                        konec = start + posl_tecka + 1
                chunky.append(chunk.strip())
                start = konec - prekryv

    return [c for c in chunky if c]


print("\n── Úloha 2: chunk_text() s parametrem separator ──")
text = (
    "Python je vysokoúrovňový jazyk. Byl vytvořen v roce 1991.\n\n"
    "Je používán v datové vědě a webovém vývoji.\n\n"
    "LangChain a LlamaIndex usnadňují práci s LLM modely. "
    "FastAPI je rychlý webový framework. "
    "NumPy a Pandas jsou populární knihovny pro datovou analýzu."
)
chunky = chunk_text(text, velikost=100, prekryv=20, separator="\n\n")
print(f"Počet chunků: {len(chunky)}")
for i, c in enumerate(chunky):
    print(f"  [{i+1}] ({len(c)} zn.) {c[:70]}...")


# ── Úloha 3 ────────────────────────────────────────────────
# hybrid_search() kombinující vektorové a BM25-like skóre

def bm25_skore(dotaz: str, text: str) -> float:
    """
    Zjednodušené BM25-like skóre: počet shodných slov / délka dotazu.
    """
    slova_dotazu = set(dotaz.lower().split())
    slova_textu = text.lower().split()
    shody = sum(1 for s in slova_textu if s in slova_dotazu)
    return shody / max(len(slova_dotazu), 1)


def hybrid_search(
    dotaz: str,
    db: JednoduchaVektorovaDB,
    alfa: float = 0.5,
    top_k: int = 3,
) -> list[tuple[float, Dokument]]:
    """
    Hybridní vyhledávání: kombinuje vektorové skóre (kosinová podobnost)
    a BM25-like skóre (počet shodných slov).

    alfa=1.0 → jen vektory
    alfa=0.0 → jen BM25
    """
    dotaz_emb = simuluj_embedding(dotaz, db.dim)

    vysledky = []
    for dok, emb in zip(db.dokumenty, db.embeddingy):
        v_skore = kosinus_podobnost(dotaz_emb, emb)
        b_skore = bm25_skore(dotaz, dok.text)
        kombinovane = alfa * v_skore + (1 - alfa) * b_skore
        vysledky.append((kombinovane, dok))

    vysledky.sort(key=lambda x: x[0], reverse=True)
    return vysledky[:top_k]


print("\n── Úloha 3: hybrid_search() ──")
db2 = JednoduchaVektorovaDB()
dokumenty = [
    Dokument("l22", "Třídy v Pythonu: class definuje třídu. __init__ je konstruktor.", {"lekce": 22}),
    Dokument("l25", "Asyncio: async/await. asyncio.run() spustí coroutinu.", {"lekce": 25}),
    Dokument("l74", "LLM API: anthropic.Anthropic() vytvoří klienta.", {"lekce": 74}),
    Dokument("l53", "NumPy: np.array() vytvoří pole. Vektorizované operace.", {"lekce": 53}),
]
for d in dokumenty:
    db2.pridej(d)

dotaz = "Jak vytvořím třídu?"
print(f"Dotaz: {dotaz!r}")
for alfa, label in [(1.0, "jen vektory"), (0.0, "jen BM25"), (0.5, "hybrid 50/50")]:
    vysl = hybrid_search(dotaz, db2, alfa=alfa, top_k=2)
    print(f"  alfa={alfa} ({label}):")
    for skore, dok in vysl:
        print(f"    {skore:.4f} | L{dok.metadata['lekce']} | {dok.text[:50]}...")


# ── Úloha 4 (BONUS) ────────────────────────────────────────
# RAG pipeline s citacemi (čísla lekcí v odpovědi)

def rag_s_citacemi(
    dotaz: str,
    db: JednoduchaVektorovaDB,
    top_k: int = 3,
) -> str:
    """
    RAG pipeline kde výsledná odpověď obsahuje citace lekcí [LXX].
    """
    relevantni = db.hledej(dotaz, top_k=top_k)

    # Sestavení odpovědi ze zjištěných chunků + citace
    casti = []
    for _skore, dok in relevantni:
        cislo = dok.metadata.get("lekce", "?")
        # Extrahuj klíčovou informaci (první věta) + přidej citaci
        prvni_veta = dok.text.split(".")[0].strip()
        casti.append(f"{prvni_veta} [L{cislo}].")

    if not casti:
        return "Nenašel jsem relevantní informace."

    return " ".join(casti)


print("\n── Úloha 4 (BONUS): RAG s citacemi ──")
odpoved = rag_s_citacemi("Jak zavolám LLM model?", db2)
print(f"Odpověď: {odpoved}")

odpoved2 = rag_s_citacemi("Jak vytvořit pole?", db2)
print(f"Odpověď: {odpoved2}")
