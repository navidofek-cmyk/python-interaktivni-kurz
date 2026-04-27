# 🐍 Python – Interaktivní kurz

Kurz Pythonu od úplných základů po pokročilá témata.
Každá lekce je jeden `.py` soubor – spustíš ho, přečteš, vyzkouší a splníš úlohy na konci.

**🌐 Živý web:** [navidofek-cmyk.github.io/python-interaktivni-kurz](https://navidofek-cmyk.github.io/python-interaktivni-kurz/)

---

## Jak začít

```bash
git clone https://github.com/navidofek-cmyk/python-interaktivni-kurz.git
cd python-interaktivni-kurz
python3 01_ahoj_svete.py
```

Potřebuješ Python 3.11+:

```bash
python3 --version
```

---

## Lekce

| Sekce | Lekce | Témata |
|-------|-------|--------|
| 🐣 Základy | 01–08 | print, proměnné, input, podmínky, cykly, seznamy, funkce |
| 🎮 První projekty | 09–10 | Kvíz, textová hra Had |
| 📦 Datové struktury | 11–14 | Texty, slovníky, soubory, Turtle grafika |
| 🎨 Grafické projekty | 15–16 | Dobrodružná hra, Chytání hvězd |
| 🔬 Věda a sarkasmus | 17–21 | Černá díra, domácí úkoly, lednicka, spánek, detektiv |
| 🏗️ OOP | 22–24 | Třídy, dědičnost, magic methods |
| ⚙️ Pokročilé vzory | 25–27 | Async, dekorátory, generátory |
| 📰 Novinky z docs | 28–30 | match/case, dataclasses, ExceptionGroup |
| 🔩 Internals & nástroje | 31–34 | __slots__, descriptory, Protocol, metaklasy, generátor webu |
| 🧮 Algoritmy | 35–38 | Rekurze, třídění, grafy BFS/DFS/Dijkstra, DP |
| 🚀 Profesionální Python | 39–45 | Testování, SQLite, REST API, design patterns, concurrency, výkon, packaging |
| 🔧 Nástroje a ekosystém | 46–52 | Regex, FP, logging, CLI, scraping, Pydantic, kód kvalita |
| 📊 Datová věda | 53–56 | NumPy, Pandas, Matplotlib, FastAPI |
| 🌐 Distribuované systémy | 57–65 | CPython, SQLAlchemy, Celery, Docker, WebSockets, Redis, GraphQL, Kafka |
| ⚙️ Produkce & DevOps | 66–71 | gRPC, mikroslužby, security, Kubernetes, MLOps, Git |

---

## Jak funguje živý web

Tento repozitář neobsahuje hotové HTML soubory.
Web se **generuje z lekcí** pokaždé znovu – automaticky.

```
.py soubory (lekce)
      │
      │  python3 34_generator_webu.py
      ↓
  web/index.html + web/lekce/*.html
      │
      │  GitHub Actions (automaticky po každém git push)
      ↓
  https://navidofek-cmyk.github.io/python-interaktivni-kurz/
```

### Přidat lekci → web se aktualizuje sám

```bash
# 1. Napiš lekci
nano 72_nova_lekce.py

# 2. Commitni a pushni
git add 72_nova_lekce.py
git commit -m "feat: lekce 72"
git push

# Za ~1 minutu je nová lekce živá na webu.
```

GitHub Actions workflow (`.github/workflows/pages.yml`) se spustí automaticky,
spustí generátor a nasadí výsledek na GitHub Pages.

### Lokální náhled

```bash
python3 34_generator_webu.py
# Otevři web/index.html dvojklikem – bez serveru funguje
```

---

## Struktura repozitáře

```
.
├── 01_ahoj_svete.py          # lekce (každá = samostatný soubor)
├── ...
├── 71_git.py
├── 34_generator_webu.py      # čte .py soubory → generuje HTML
├── POSTUP.md                 # přehled lekcí s obtížností
├── CHANGELOG.md              # historie změn
├── JAK_FUNGUJE_WEB.md        # detailnější popis pipeline
└── .github/
    └── workflows/
        ├── ci.yml            # syntax check + testy při každém push
        └── pages.yml         # generuj web + nasaď na GitHub Pages
```

`web/` se negeneruje do gitu – vzniká za běhu.

---

## Testy

```bash
python3 -m pytest 39_testovani.py -v
```

CI (`.github/workflows/ci.yml`) spouští testy automaticky při každém push.

---

## Přispívání

Našel jsi chybu nebo máš nápad na lekci?
Otevři [Issue](https://github.com/navidofek-cmyk/python-interaktivni-kurz/issues).

---

Vytvořeno s Pythonem 🐍
