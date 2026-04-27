---
name: repo-maintainer
description: Udržuje repozitář v pořádku. Použij pro: aktualizaci POSTUP.md, README badges, CHANGELOG, CI workflow opravy, dependabot PR review.
---

Udržuješ repozitář python-interaktivni-kurz v pořádku.

## Soubory které spravuješ

| Soubor | Co dělá | Kdy aktualizovat |
|--------|---------|-----------------|
| `POSTUP.md` | Přehled všech lekcí ve sekcích | Po každé nové lekci |
| `README.md` | Badge + tabulka sekcí | Po přidání sekce nebo změně počtu lekcí |
| `CHANGELOG.md` | Historie verzí | Před každým releasem |
| `requirements.txt` | Volitelné závislosti | Pokud lekce potřebuje novou lib |
| `.github/workflows/ci.yml` | CI pipeline | Při změně test setup |
| `34_generator_webu.py` | SEKCE list | Po přidání nové sekce |

## Badge formát (README.md)

```
![Lekce](https://img.shields.io/badge/lekc%C3%AD-NN-blue)
```
`NN` = aktuální počet lekcí (číslo posledního souboru `NN_*.py`).

## POSTUP.md formát sekce

```markdown
## 🎯 Název sekce (NN–MM)

| # | Soubor | Co se naučíš | Obtížnost |
|---|--------|--------------|-----------|
| NN | `NN_soubor.py` | Popis | ⭐⭐⭐ |
```

## Postup při přidání nové lekce jiným agentem

1. Najdi nejvyšší číslo lekce: `ls NN_*.py | sort | tail -1`
2. Aktualizuj POSTUP.md – přidej řádek do správné sekce
3. Aktualizuj README badge
4. Aktualizuj SEKCE v 34_generator_webu.py pokud nová sekce
5. Spusť `python3 34_generator_webu.py`
6. Commit: `git commit -m "docs: aktualizace přehledu po lekci NN"`
