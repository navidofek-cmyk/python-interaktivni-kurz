# Jak přispívat

Díky za zájem! Příspěvky jsou vítány.

## Nahlásit chybu

Otevři [Issue](https://github.com/navidofek-cmyk/python-interaktivni-kurz/issues)
a vyplň šablonu. Uveď číslo lekce a co přesně nefunguje.

## Přidat nebo opravit lekci

```bash
# 1. Forkni repozitář na GitHubu (tlačítko Fork)

# 2. Naklonuj svůj fork
git clone https://github.com/TVOJE_JMENO/python-interaktivni-kurz.git
cd python-interaktivni-kurz

# 3. Vytvoř větev
git switch -c feat/lekce-72-nova-tema

# 4. Proveď změny, zkontroluj syntax
python3 -m py_compile 72_nova_tema.py

# 5. Commitni (používej konvenční commit zprávy)
git add 72_nova_tema.py
git commit -m "feat: lekce 72 – nové téma"

# 6. Pushni a otevři Pull Request
git push -u origin feat/lekce-72-nova-tema
```

## Formát lekce

Každý soubor musí mít:

```python
"""
LEKCE XX: Název
================
Krátký popis co se naučíš.
"""

# ... kód ...

# TVOJE ÚLOHA:
# 1. První úloha
# 2. Druhá úloha
# 3. Třetí úloha
```

## Commit zprávy (Conventional Commits)

```
feat:     nová lekce nebo funkce
fix:      oprava chyby
docs:     dokumentace (README, komentáře)
refactor: přepis bez změny chování
test:     přidání testů
chore:    CI, závislosti, konfigurace
```

## Co dělá CI automaticky

Při každém push GitHub Actions:
- Zkontroluje syntax všech `.py` souborů
- Spustí testy z lekce 39
- Vygeneruje web a nasadí ho na GitHub Pages
