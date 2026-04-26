# 🐍 Python – Interaktivní kurz

Kurz Pythonu od úplných základů po pokročilé téma.
Každá lekce je jeden `.py` soubor – spustíš ho, přečteš, vyzkouší a splníš úlohy na konci.

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
| 🔩 Internals | 31–34 | __slots__, descriptory, Protocol, metaklasy, generátor webu |
| 🧮 Algoritmy | 35–38 | Rekurze, třídění, grafy BFS/DFS/Dijkstra, DP |
| 🚀 Profesionální Python | 39–45 | Testování, SQLite, REST API, design patterns, concurrency, výkon, packaging |
| 🔧 Nástroje | 46–49 | Regex, funkcionální programování, logging, CLI |

## Jak začít

```bash
git clone https://github.com/navidofek-cmyk/python-interaktivni-kurz.git
cd python-interaktivni-kurz
python3 01_ahoj_svete.py
```

Potřebuješ Python 3.11+. Ověř verzi:

```bash
python3 --version
```

## Generátor webu

Kurz má vlastní statický web vygenerovaný Pythonem (lekce 34):

```bash
python3 34_generator_webu.py
# Otevři web/index.html
```

Web je také nasazený na [GitHub Pages](https://navidofek-cmyk.github.io/python-interaktivni-kurz/).

## Struktura

```
.
├── 01_ahoj_svete.py        # Každá lekce = samostatný soubor
├── ...
├── 45_packaging.py
├── 34_generator_webu.py    # Generuje web/ ze všech lekcí
├── POSTUP.md               # Přehled všech lekcí s obtížností
└── web/                    # Vygenerovaný web (není v gitu)
```

## Testování

Lekce 39 obsahuje testy (unittest). Spusť je:

```bash
python3 -m pytest 39_testovani.py -v
```

## Přispívání

Našel jsi chybu nebo máš nápad na lekci? Otevři [Issue](https://github.com/navidofek-cmyk/python-interaktivni-kurz/issues).

---

Vytvořeno s Pythonem 🐍
