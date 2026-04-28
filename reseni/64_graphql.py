"""Reseni – Lekce 64: GraphQL"""

# Strawberry vyžaduje: pip install strawberry-graphql

import json
import textwrap
from typing import Any

try:
    import strawberry
    from strawberry import Schema
    GQL_OK = True
except ImportError:
    print("strawberry-graphql neni nainstalovano: pip install strawberry-graphql")
    GQL_OK = False


# Demo data
PREDMETY_DB: dict[int, dict] = {
    1: {"id": 1, "nazev": "Python",     "lektor": "Novak"},
    2: {"id": 2, "nazev": "Matematika", "lektor": "Dvorak"},
    3: {"id": 3, "nazev": "Databaze",   "lektor": "Novak"},
}

STUDENTI_DB: dict[int, dict] = {
    1: {"id": 1, "jmeno": "Misa",  "vek": 15, "predmet_id": 1, "body": [87.5, 91.0, 85.0]},
    2: {"id": 2, "jmeno": "Tomas", "vek": 16, "predmet_id": 2, "body": [92.0, 88.5]},
    3: {"id": 3, "jmeno": "Bara",  "vek": 14, "predmet_id": 1, "body": [78.3, 82.0, 79.5]},
    4: {"id": 4, "jmeno": "Ondra", "vek": 17, "predmet_id": 3, "body": [95.1, 93.0]},
}


if GQL_OK:
    @strawberry.type
    class Predmet:
        id:     int
        nazev:  str
        lektor: str | None = None

    @strawberry.input
    class StudentInput:
        jmeno:     str
        vek:       int
        predmet_id: int

    @strawberry.type
    class Student:
        id:    int
        jmeno: str
        vek:   int
        body:  list[float]

        @strawberry.field
        def predmet(self) -> Predmet | None:
            data = PREDMETY_DB.get(self._predmet_id)  # type: ignore[attr-defined]
            if data:
                return Predmet(**data)
            return None

        @strawberry.field
        def prumerne_body(self) -> float:
            if not self.body:
                return 0.0
            return round(sum(self.body) / len(self.body), 2)

    def student_z_db(d: dict) -> Student:
        s = Student(id=d["id"], jmeno=d["jmeno"], vek=d["vek"], body=d["body"])
        s._predmet_id = d["predmet_id"]  # type: ignore[attr-defined]
        return s

    @strawberry.type
    class Query:
        @strawberry.field
        def studenti(self, min_vek: int | None = None) -> list[Student]:
            data = list(STUDENTI_DB.values())
            if min_vek is not None:
                data = [s for s in data if s["vek"] >= min_vek]
            return [student_z_db(s) for s in data]

        @strawberry.field
        def student(self, id: int) -> Student | None:
            d = STUDENTI_DB.get(id)
            return student_z_db(d) if d else None

        @strawberry.field
        def predmety(self) -> list[Predmet]:
            return [Predmet(**p) for p in PREDMETY_DB.values()]

        # Ukol 1: Subscription placeholder (pro full WS support je potreba ASGI)
        # Ukazka subscribtion je v komentari nize

    _next_id = max(STUDENTI_DB) + 1

    @strawberry.type
    class Mutation:
        @strawberry.mutation
        def vytvor_studenta(self, vstup: StudentInput) -> Student:
            global _next_id
            novy = {
                "id":         _next_id,
                "jmeno":      vstup.jmeno,
                "vek":        vstup.vek,
                "predmet_id": vstup.predmet_id,
                "body":       [],
            }
            STUDENTI_DB[_next_id] = novy
            _next_id += 1
            return student_z_db(novy)

        @strawberry.mutation
        def smaz_studenta(self, id: int) -> bool:
            if id in STUDENTI_DB:
                del STUDENTI_DB[id]
                return True
            return False

    # Ukol 2: DataLoader pro reseni N+1 (pseudokod)
    # V produkci pouzit strawberry.dataloader
    _predmety_batch_cache: dict[int, Predmet] = {}

    def batch_load_predmety(ids: list[int]) -> list[Predmet | None]:
        """DataLoader batch funkce – nacte vsechny predmety jednim dotazem."""
        return [
            Predmet(**PREDMETY_DB[id_]) if id_ in PREDMETY_DB else None
            for id_ in ids
        ]

    schema = Schema(query=Query, mutation=Mutation)

    print("=== GraphQL dotazy ===\n")

    dotazy = [
        # Zakladni seznam
        "{ studenti { jmeno vek prumerneBody } }",
        # S predmetem (nested)
        "{ student(id: 1) { jmeno predmet { nazev lektor } } }",
        # S filtrem
        "{ studenti(minVek: 15) { jmeno vek } }",
        # Mutation
        'mutation { vytvorStudenta(vstup: {jmeno: "Pavel", vek: 18, predmetId: 2}) { id jmeno } }',
        # Smazání
        "mutation { smazStudenta(id: 5) }",
        # Predmety
        "{ predmety { id nazev lektor } }",
    ]

    for dotaz in dotazy:
        vysledek = schema.execute_sync(dotaz)
        print(f"  Dotaz: {dotaz[:70]}")
        if vysledek.errors:
            print(f"  Chyba: {vysledek.errors[0]}\n")
        else:
            print(f"  → {json.dumps(vysledek.data, ensure_ascii=False)}\n")


# Ukol 1: Subscription (SDL + produkční kod)

print("=== Ukol 1: Subscription pro real-time notifikace ===\n")

SUBSCRIPTION_EXAMPLE = """\
# vyžaduje: strawberry-graphql[debug-server] nebo ASGI server

import strawberry
import asyncio
from strawberry import Schema
from strawberry.subscriptions import GRAPHQL_TRANSPORT_WS_PROTOCOL
from typing import AsyncGenerator

@strawberry.type
class Subscription:
    @strawberry.subscription
    async def nova_zprava(self, mistnost: str = "general") -> AsyncGenerator[str, None]:
        \"\"\"Real-time stream zprav z chatovaci mistnosti.\"\"\"
        for i in range(5):
            await asyncio.sleep(1)
            yield f"Zprava {i} v mistnosti {mistnost!r}"

schema = Schema(query=Query, subscription=Subscription)

# Spusteni s ASGI:
# from strawberry.asgi import GraphQL
# app = GraphQL(schema)
# uvicorn main:app
"""

print(SUBSCRIPTION_EXAMPLE)


# Ukol 3: Paginace (cursor-based)

print("=== Ukol 3: Paginace s cursor ===\n")

PAGINACE_EXAMPLE = """\
import base64
import strawberry

@strawberry.type
class PageInfo:
    has_next_page:  bool
    end_cursor:     str | None = None

@strawberry.type
class StudentEdge:
    node:   Student
    cursor: str

@strawberry.type
class StudentConnection:
    edges:     list[StudentEdge]
    page_info: PageInfo

def encode_cursor(id_: int) -> str:
    return base64.b64encode(f"Student:{id_}".encode()).decode()

def decode_cursor(cursor: str) -> int:
    decoded = base64.b64decode(cursor).decode()
    return int(decoded.split(":")[1])

@strawberry.type
class QueryPaginovana:
    @strawberry.field
    def studenti(
        self,
        first:  int = 10,
        after:  str | None = None,
    ) -> StudentConnection:
        vsichni = sorted(STUDENTI_DB.values(), key=lambda s: s["id"])
        if after:
            after_id = decode_cursor(after)
            vsichni = [s for s in vsichni if s["id"] > after_id]
        stranka = vsichni[:first]
        ma_dalsi = len(vsichni) > first
        edges = [
            StudentEdge(
                node=student_z_db(s),
                cursor=encode_cursor(s["id"]),
            )
            for s in stranka
        ]
        return StudentConnection(
            edges=edges,
            page_info=PageInfo(
                has_next_page=ma_dalsi,
                end_cursor=edges[-1].cursor if edges else None,
            ),
        )

# GraphQL dotaz:
# query {
#   studenti(first: 2) {
#     edges { node { jmeno } cursor }
#     pageInfo { hasNextPage endCursor }
#   }
# }
"""

print(PAGINACE_EXAMPLE)

if not GQL_OK:
    print("\nPro spusteni nainstaluj: pip install strawberry-graphql")
