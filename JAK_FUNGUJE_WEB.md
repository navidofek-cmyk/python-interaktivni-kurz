# Jak funguje web kurzu

## Co se stane když otevřeš prohlížeč

```
https://navidofek-cmyk.github.io/python-interaktivni-kurz/
```

Vidíš hotový web se všemi lekcemi – přehledně rozdělený do sekcí,
s barevnými kartami, syntaxovým zvýrazněním kódu a navigací.

---

## Kde web vzniká

Web **není** uložený přímo v repozitáři. Generuje ho Python.

```
Repozitář (GitHub)
│
├── 01_ahoj_svete.py      ← lekce jako Python soubory
├── 02_promenne.py
├── ...
├── 71_git.py
│
└── 34_generator_webu.py  ← tento skript web VYTVOŘÍ
```

Když spustíš:

```bash
python3 34_generator_webu.py
```

Vznikne složka `web/` s HTML stránkami:

```
web/
├── index.html            ← hlavní stránka se všemi lekcemi
└── lekce/
    ├── 01_ahoj_svete.html
    ├── 02_promenne.html
    └── ...
```

---

## Jak se web dostane na internet

O to se stará **GitHub Actions** – automatický robot na GitHubu.

### Krok za krokem:

```
Ty uděláš změnu (např. přidáš lekci)
        ↓
git push
        ↓
GitHub to uloží
        ↓
GitHub Actions se automaticky spustí
        ↓
  1. Naklonuje repozitář
  2. Nainstaluje Python 3.12
  3. Spustí: python3 34_generator_webu.py
  4. Vezme vygenerovaný web/
  5. Nasadí ho na GitHub Pages
        ↓
Web je živý na internetu (~1 minuta)
```

### Kde to nastavit:

Workflow je uložený v souboru `.github/workflows/pages.yml`.
GitHub ho automaticky najde a spustí při každém `git push`.

---

## Jak přidat novou lekci a dostat ji na web

```bash
# 1. Napiš novou lekci
nano 72_nova_lekce.py

# 2. Commitni ji
git add 72_nova_lekce.py
git commit -m "feat: lekce 72 – nové téma"

# 3. Pushni
git push
```

**To je vše.** Za ~1 minutu se web automaticky přegeneruje
a nová lekce se objeví na internetu.

---

## Shrnutí

| Co | Kde |
|----|-----|
| Zdrojové lekce | GitHub repozitář (`.py` soubory) |
| Generátor webu | `34_generator_webu.py` |
| Automatizace | `.github/workflows/pages.yml` |
| Živý web | `https://navidofek-cmyk.github.io/python-interaktivni-kurz/` |
| Lokální náhled | `python3 34_generator_webu.py` → otevři `web/index.html` |

---

## Proč web není přímo v gitu

Složka `web/` je v `.gitignore` – záměrně ji necommitujeme.

Důvod: každá lekce by byla v repozitáři dvakrát
(jednou jako `.py`, jednou jako `.html`). Generátor
vždy vytvoří aktuální verzi – není důvod archivovat mezivýsledek.
