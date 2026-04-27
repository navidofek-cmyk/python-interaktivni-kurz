# Python – Interaktivní kurz · Kontext pro Claude Code

## Co je tento projekt

Interaktivní Python kurz – 83 lekcí od `print("Ahoj")` po AWS boto3, OpenCV a LLM API.
Každá lekce = jeden `.py` soubor. Spuštěním získáš výstup + úlohy.

Web se generuje automaticky: `python3 34_generator_webu.py` → `web/index.html`.
Po každém `git push` GitHub Actions web přegeneruje a nasadí na GitHub Pages.

## Struktura

```
01–08   Základy (print, proměnné, podmínky, cykly, funkce)
09–10   První projekty (kvíz, had)
11–34   Datové struktury, OOP, pokročilé vzory, generátor webu
35–38   Algoritmy (rekurze, třídění, grafy, DP)
39–45   Profesionální Python (testy, DB, API, design patterns)
46–52   Nástroje (regex, logging, CLI, scraping, Pydantic)
53–56   Datová věda (NumPy, Pandas, Matplotlib, FastAPI)
57–65   Distribuované systémy (CPython, Redis, Kafka, WebSockets)
66–71   Produkce (gRPC, mikroslužby, security, K8s, MLOps, Git)
72–75   Novinky a AI (Python 3.13, uv, Claude API, CI/CD)
76–83   Praktické nástroje (Playwright, PDF, email, Pygame, OpenCV, NLP, AWS)
```

## Formát lekce (ZÁVAZNÝ)

```python
"""
LEKCE XX: Název
================
Popis co se naučíš (2-4 věty).
"""

# ... kód s print výstupy ...

# TVOJE ÚLOHA:
# 1. První úloha
# 2. Druhá úloha
# 3. Třetí úloha
```

Pravidla:
- Každá lekce musí jít spustit: `python3 XX_jmeno.py`
- Žádné externí závislosti pro základní spuštění (nebo graceful fallback)
- Číslo lekce = 2 cifry (01, 02, ..., 83, 84...)
- Jméno souboru bez diakritiky (ascii_stem)
- Výstup musí být čitelný a demonstrovat téma
- Sekce `# TVOJE ÚLOHA:` vždy na konci

## Přidání nové lekce

1. Zkontroluj POSTUP.md – jaké číslo je volné
2. Vytvoř soubor `NN_tema.py` ve správném formátu
3. Přidej sekci do POSTUP.md
4. Aktualizuj `SEKCE` v `34_generator_webu.py` pokud je to nová sekce
5. Aktualizuj badge v README.md (`lekc%C3%AD-NN-blue`)
6. Spusť `python3 34_generator_webu.py` a ověř výstup
7. `git add`, `git commit -m "feat: lekce NN – téma"`, `git push`

## Generátor webu – klíčové funkce

- `nacti_lekci(cesta)` – parsuje .py, vrátí dict s metadaty
- `ascii_stem(stem)` – odstraní diakritiku z názvu souboru
- `zvyrazni_python(kod)` – syntax highlighting přes regex
- `odstran_ulohy_z_kodu(kod)` – vystřihne sekci TVOJE ÚLOHA z code bloku
- `generuj_index(lekce, vystup)` – hlavní stránka se sekcemi
- `generuj_lekci(l, vystup, prev, next)` – stránka jednotlivé lekce

## Technické poznámky

- Web funguje bez serveru (double-click na web/index.html)
- Progress tracker: dvouklik na kartu = označení jako hotová (localStorage)
- Vyhledávání: live search přes JSON index všech lekcí
- Světlé téma: tlačítko ☀️ v headeru, uloží se do localStorage
- GitHub Pages: source = GitHub Actions (moto workflow `pages.yml`)
- Soubory s diakritikou v názvech jsou automaticky přejmenovány

## Stav repozitáře (2026-04-27)

- 83 lekcí, 16 sekcí
- GitHub Pages live: https://navidofek-cmyk.github.io/python-interaktivni-kurz/
- CI: syntax check + testy + coverage + Pages deploy
- Dependabot: weekly updates
