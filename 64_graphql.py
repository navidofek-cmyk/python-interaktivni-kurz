"""
LEKCE 64: GraphQL – flexibilní API
=====================================
pip install strawberry-graphql

REST: /users/1, /users/1/posts, /users/1/friends → 3 requesty
GraphQL: jeden request → přesně ta data která chceš

GraphQL výhody:
  - Klient si určuje co chce (žádné over/under-fetching)
  - Silně typované schéma (SDL – Schema Definition Language)
  - Introspekce – klient ví co API umí
  - Subscriptions – real-time přes WebSocket

Nevýhody:
  - Složitější caching
  - N+1 problem (řeší DataLoader)
  - Over-engineering pro jednoduché API

strawberry = moderní GQL framework (dekorátory + type hints)
"""

try:
    import strawberry
    from strawberry import Schema, field, type as gql_type, mutation
    from strawberry.scalars import JSON
    GQL_OK = True
except ImportError:
    print("strawberry-graphql není nainstalováno: pip install strawberry-graphql")
    GQL_OK = False

from dataclasses import dataclass, field as dc_field
from typing import Optional
import json

# ══════════════════════════════════════════════════════════════
# ČÁST 1: GraphQL bez strawberry – ruční implementace
# ══════════════════════════════════════════════════════════════

print("=== Základní GraphQL koncepty (ruční implementace) ===\n")

# Data
STUDENTI = {
    1: {"id": 1, "jmeno": "Míša",  "vek": 15, "predmet_id": 1},
    2: {"id": 2, "jmeno": "Tomáš", "vek": 16, "predmet_id": 2},
    3: {"id": 3, "jmeno": "Bára",  "vek": 14, "predmet_id": 1},
}
PREDMETY = {
    1: {"id": 1, "nazev": "Matematika", "lektor": "Novák"},
    2: {"id": 2, "nazev": "Fyzika",     "lektor": "Dvořák"},
}
ZAPISY = [
    {"student_id": 1, "predmet_id": 1, "body": 87.5},
    {"student_id": 1, "predmet_id": 2, "body": 92.0},
    {"student_id": 2, "predmet_id": 2, "body": 78.3},
    {"student_id": 3, "predmet_id": 1, "body": 95.1},
]

class GraphQLEngine:
    """Velmi zjednodušená GQL simulace."""

    def __init__(self):
        self.resolvers: dict = {}

    def resolver(self, typ: str, pole: str):
        def dec(fn):
            self.resolvers[f"{typ}.{pole}"] = fn
            return fn
        return dec

    def execute(self, dotaz: dict) -> dict:
        """Spustí GQL dotaz."""
        vysledek = {}
        for pole, args in dotaz.items():
            klic = f"Query.{pole}"
            if klic in self.resolvers:
                if isinstance(args, dict):
                    data = self.resolvers[klic](**args.get("args", {}))
                    if "fields" in args:
                        data = self._filter(data, args["fields"])
                else:
                    data = self.resolvers[klic]()
                vysledek[pole] = data
        return {"data": vysledek}

    def _filter(self, data, fields: list):
        """Vrátí jen požadovaná pole."""
        if isinstance(data, list):
            return [self._filter(item, fields) for item in data]
        if isinstance(data, dict):
            return {k: v for k, v in data.items() if k in fields}
        return data

engine = GraphQLEngine()

@engine.resolver("Query", "student")
def resolve_student(id: int) -> dict | None:
    s = STUDENTI.get(id)
    if s:
        p = PREDMETY.get(s["predmet_id"])
        return {**s, "predmet": p}
    return None

@engine.resolver("Query", "studenti")
def resolve_studenti() -> list[dict]:
    return [{**s, "predmet": PREDMETY.get(s["predmet_id"])} for s in STUDENTI.values()]

@engine.resolver("Query", "predmety")
def resolve_predmety() -> list[dict]:
    return list(PREDMETY.values())

# Různé dotazy – ukázka flexibility
dotazy = [
    # Chci jen jméno a věk
    {"studenti": {"fields": ["jmeno", "vek"]}},
    # Chci studenta 1 včetně jeho předmětu
    {"student": {"args": {"id": 1}, "fields": ["jmeno", "predmet"]}},
    # Chci jen předměty
    {"predmety": {"fields": ["nazev", "lektor"]}},
]

for dotaz in dotazy:
    vysledek = engine.execute(dotaz)
    print(f"  Dotaz: {json.dumps(dotaz)}")
    print(f"  → {json.dumps(vysledek['data'])}\n")


# ══════════════════════════════════════════════════════════════
# ČÁST 2: Strawberry – produkční GQL
# ══════════════════════════════════════════════════════════════

if GQL_OK:
    print("=== Strawberry GraphQL ===\n")

    @strawberry.type
    class Predmet:
        id:     int
        nazev:  str
        lektor: str

    @strawberry.type
    class Student:
        id:    int
        jmeno: str
        vek:   int

        @strawberry.field
        def predmet(self) -> Optional[Predmet]:
            pid = STUDENTI[self.id]["predmet_id"]
            p = PREDMETY.get(pid)
            return Predmet(**p) if p else None

        @strawberry.field
        def zapisy_body(self) -> list[float]:
            return [z["body"] for z in ZAPISY if z["student_id"] == self.id]

        @strawberry.field
        def prumerne_body(self) -> float:
            body = [z["body"] for z in ZAPISY if z["student_id"] == self.id]
            return sum(body) / len(body) if body else 0.0

    @strawberry.input
    class StudentInput:
        jmeno:      str
        vek:        int
        predmet_id: int

    @strawberry.type
    class Query:
        @strawberry.field
        def student(self, id: int) -> Optional[Student]:
            if id in STUDENTI:
                return Student(id=id, jmeno=STUDENTI[id]["jmeno"], vek=STUDENTI[id]["vek"])
            return None

        @strawberry.field
        def studenti(self, min_vek: int = 0) -> list[Student]:
            return [
                Student(id=s["id"], jmeno=s["jmeno"], vek=s["vek"])
                for s in STUDENTI.values()
                if s["vek"] >= min_vek
            ]

        @strawberry.field
        def predmety(self) -> list[Predmet]:
            return [Predmet(**p) for p in PREDMETY.values()]

    @strawberry.type
    class Mutation:
        @strawberry.mutation
        def vytvor_studenta(self, vstup: StudentInput) -> Student:
            novy_id = max(STUDENTI.keys()) + 1
            STUDENTI[novy_id] = {
                "id": novy_id,
                "jmeno": vstup.jmeno,
                "vek": vstup.vek,
                "predmet_id": vstup.predmet_id,
            }
            return Student(id=novy_id, jmeno=vstup.jmeno, vek=vstup.vek)

    schema = Schema(query=Query, mutation=Mutation)

    # Testovací dotazy
    gql_dotazy = [
        # Základní dotaz
        "{ studenti { jmeno vek } }",
        # Dotaz s argumentem
        "{ student(id: 1) { jmeno predmet { nazev lektor } prumerneTelo } }",
        # Nested dotaz
        "{ studenti(minVek: 15) { jmeno zapisy_body prumerneBody } }",
        # Mutation
        'mutation { vytvorStudenta(vstup: {jmeno: "Ondra", vek: 17, predmetId: 2}) { id jmeno } }',
    ]

    for dotaz in gql_dotazy:
        try:
            vysledek = schema.execute_sync(dotaz)
            if vysledek.errors:
                print(f"  Dotaz: {dotaz[:60]}...")
                print(f"  Chyba: {vysledek.errors[0]}\n")
            else:
                print(f"  Dotaz: {dotaz[:60]}...")
                print(f"  → {json.dumps(vysledek.data, ensure_ascii=False)}\n")
        except Exception as e:
            print(f"  Chyba: {e}\n")

else:
    print("=== Strawberry není dostupné – ukázka SDL schématu ===\n")
    SDL = '''
    type Student {
        id:     ID!
        jmeno:  String!
        vek:    Int!
        predmet: Predmet
        body:   [Float!]!
    }

    type Predmet {
        id:     ID!
        nazev:  String!
        lektor: String
    }

    input StudentInput {
        jmeno:     String!
        vek:       Int!
        predmetId: ID!
    }

    type Query {
        student(id: ID!): Student
        studenti(minVek: Int): [Student!]!
        predmety: [Predmet!]!
    }

    type Mutation {
        vytvorStudenta(vstup: StudentInput!): Student!
        smazStudenta(id: ID!): Boolean!
    }

    type Subscription {
        novaZprava(mistnost: String!): String!
    }
    '''
    print(textwrap.indent(SDL.strip(), "  "))


# ══════════════════════════════════════════════════════════════
# ČÁST 3: REST vs GraphQL srovnání
# ══════════════════════════════════════════════════════════════

import textwrap

print("""
=== REST vs GraphQL ===

Problém: Zobraz profil studenta s jeho předmětem a posledními 3 zápisy.

REST (over-fetching + 3 requesty):
  GET /api/studenti/1          → {id, jmeno, vek, email, adresa, ...}
  GET /api/studenti/1/predmet  → {id, nazev, lektor, kredity, ...}
  GET /api/studenti/1/zapisy?limit=3

GraphQL (1 request, přesná data):
  query {
    student(id: 1) {
      jmeno
      vek
      predmet { nazev }
      zapisy(limit: 3) { predmet { nazev } body datum }
    }
  }

Kdy REST, kdy GraphQL:
  REST     → jednoduché CRUD API, veřejné API, caching je klíčový
  GraphQL  → komplexní data, mobilní klienti (omezená šířka pásma),
             BFF (Backend for Frontend) pattern
""")

# TVOJE ÚLOHA:
# 1. Přidej do schématu Subscription pro real-time notifikace.
# 2. Implementuj DataLoader pro řešení N+1 problému.
# 3. Přidej paginaci (first: Int, after: String cursor) do studenti query.
