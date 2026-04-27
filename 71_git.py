"""
LEKCE 71: Git – verzování kódu
================================
Git = distribuovaný systém pro správu verzí.
Sleduje změny, umožňuje spolupráci, chrání před ztrátou práce.

Tato lekce vytvoří dočasný git repozitář a spustí
skutečné git příkazy – uvidíš reálný výstup.

Koncepty:
  Working tree  – soubory na disku
  Index/Stage   – co jde do příštího commitu
  HEAD          – aktuální pozice (branch nebo commit)
  Object store  – databáze objektů (blob, tree, commit, tag)
"""

import subprocess
import tempfile
import os
import time
from pathlib import Path

# ══════════════════════════════════════════════════════════════
# Setup – dočasný repozitář
# ══════════════════════════════════════════════════════════════

REPO = Path(tempfile.mkdtemp(prefix="git_kurz_"))

def git(*args, cwd=None, check=True) -> str:
    r = subprocess.run(
        ["git", *args],
        cwd=str(cwd or REPO),
        capture_output=True, text=True,
    )
    if check and r.returncode != 0:
        return r.stderr.strip()
    return (r.stdout + r.stderr).strip()

def soubor(jmeno: str, obsah: str):
    (REPO / jmeno).write_text(obsah, encoding="utf-8")

def sekce(nazev: str):
    print(f"\n{'═'*55}")
    print(f"  {nazev}")
    print('═'*55)

def cmd(prikaz: str, *args, **kwargs) -> str:
    vysledek = git(*prikaz.split(), **kwargs)
    print(f"\n$ git {prikaz}")
    if vysledek:
        for radek in vysledek.splitlines()[:20]:
            print(f"  {radek}")
    return vysledek

# Konfigurace pro demo (bez ohledu na globální nastavení)
git("init", "-b", "main")
git("config", "user.name",  "Demo User")
git("config", "user.email", "demo@kurz.cz")
git("config", "core.autocrlf", "false")

print(f"Repozitář vytvořen: {REPO}\n")


# ══════════════════════════════════════════════════════════════
# ČÁST 1: Základní workflow
# ══════════════════════════════════════════════════════════════

sekce("1. Základní workflow")

soubor("README.md", "# Můj projekt\n\nPython kurz.\n")
soubor("main.py",   'print("Ahoj, světe!")\n')

cmd("status")
cmd("add README.md main.py")
cmd("status")
cmd("commit -m 'Initial commit: README a main.py'")
cmd("log --oneline")

# Druhá změna
soubor("main.py", 'def pozdrav(jmeno):\n    print(f"Ahoj, {jmeno}!")\n\npozdrav("Míša")\n')
soubor("utils.py", "def secti(a, b):\n    return a + b\n")

cmd("diff")           # změny NEJSOU ve stage
cmd("add -p main.py", check=False)   # interaktivní – přeskočíme
git("add", "main.py", "utils.py")
cmd("diff --staged")  # změny VE stage
cmd("commit -m 'Refactor: pozdrav jako funkce, přidán utils.py'")

cmd("log --oneline")


# ══════════════════════════════════════════════════════════════
# ČÁST 2: Branches – větve
# ══════════════════════════════════════════════════════════════

sekce("2. Větvení (branches)")

cmd("branch")                              # seznam větví
cmd("branch feature/login")               # vytvoř větev
cmd("checkout feature/login")             # přepni na ni
# nebo: git("switch", "-c", "feature/login2")  # moderní syntaxe

soubor("login.py", "def login(user, pw):\n    return user == 'admin'\n")
git("add", "login.py")
cmd("commit -m 'feat: základní login funkce'")

soubor("login.py", "def login(user, pw):\n    if not user or not pw:\n        return False\n    return user == 'admin' and pw == 'tajne'\n")
git("add", "login.py")
cmd("commit -m 'feat: validace prázdných vstupů v login'")

cmd("log --oneline --all --graph")        # přehled všech větví

# Mezitím změna na main
cmd("checkout main")
soubor("main.py", 'from utils import secti\n\ndef pozdrav(jmeno):\n    print(f"Ahoj, {jmeno}!")\n\npozdrav("Míša")\nprint(secti(3, 4))\n')
git("add", "main.py")
cmd("commit -m 'feat: použij secti z utils'")

cmd("log --oneline --all --graph")


# ══════════════════════════════════════════════════════════════
# ČÁST 3: Merge vs Rebase
# ══════════════════════════════════════════════════════════════

sekce("3. Merge vs Rebase")

# MERGE – zachová historii, vytvoří merge commit
cmd("merge feature/login --no-ff -m 'Merge feature/login do main'")
cmd("log --oneline --graph")

# REBASE – přepíše historii, lineární log
cmd("branch feature/search")
cmd("checkout feature/search")
soubor("search.py", "def hledej(seznam, klic):\n    return [x for x in seznam if klic in str(x)]\n")
git("add", "search.py")
cmd("commit -m 'feat: funkce hledej'")

cmd("checkout main")
soubor("config.py", "DEBUG = False\nVERZE = '1.0.0'\n")
git("add", "config.py")
cmd("commit -m 'config: přidán config.py'")

cmd("checkout feature/search")
print("\n  Rebase feature/search na main:")
cmd("rebase main")
cmd("checkout main")
cmd("merge feature/search --ff-only")    # fast-forward, žádný merge commit
cmd("log --oneline --graph")


# ══════════════════════════════════════════════════════════════
# ČÁST 4: Stash, cherry-pick, bisect
# ══════════════════════════════════════════════════════════════

sekce("4. Pokročilé příkazy")

# STASH – ulož rozdělanou práci
soubor("wip.py", "# TODO: toto není hotové\n")
git("add", "wip.py")
soubor("main.py", (REPO / "main.py").read_text() + "# TODO\n")

cmd("status")
cmd("stash push -m 'rozdělaná práce na WIP'")
cmd("status")          # čisté
cmd("stash list")
cmd("stash pop")       # obnov
cmd("status")

# Vyčisti stash artefakty
git("checkout", "main.py")
git("rm", "--cached", "wip.py", check=False)
(REPO / "wip.py").unlink(missing_ok=True)

# CHERRY-PICK – vezmi konkrétní commit z jiné větve
cmd("branch hotfix")
cmd("checkout hotfix")
soubor("fix.py", "# Oprava bezpečnostní chyby\ndef sanitize(x): return str(x)\n")
git("add", "fix.py")
cmd("commit -m 'fix: sanitize vstupů (CVE-2024-1234)'")

fix_hash = git("log", "--format=%H", "-1").strip()[:7]
cmd("checkout main")
cmd(f"cherry-pick {fix_hash}")
cmd("log --oneline -5")

# TAG – označení verze
cmd("tag -a v1.0.0 -m 'První stabilní verze'")
cmd("tag")
cmd("show v1.0.0 --stat")


# ══════════════════════════════════════════════════════════════
# ČÁST 5: Git internals – jak Git funguje uvnitř
# ══════════════════════════════════════════════════════════════

sekce("5. Git internals – objekty")

print("""
  Git ukládá data jako 4 typy objektů (SHA-1 hash):
    blob   – obsah souboru
    tree   – adresář (seznam blobů a stromů)
    commit – snapshot + rodič + autor + zpráva
    tag    – pojmenovaný odkaz na commit
""")

# Zobraz objekt HEAD commitu
head_hash = git("rev-parse", "HEAD")
print(f"\n  HEAD = {head_hash[:7]}...")
cmd(f"cat-file -t {head_hash[:7]}")     # typ objektu
cmd(f"cat-file -p {head_hash[:7]}")     # obsah commitu

# Tree
tree_hash = git("rev-parse", "HEAD^{tree}")
cmd(f"cat-file -p {tree_hash[:7]}")

# Jak Git hash funguje
import hashlib
obsah = b"Ahoj, Git!"
git_objekt = b"blob " + str(len(obsah)).encode() + b"\x00" + obsah
sha = hashlib.sha1(git_objekt).hexdigest()
print(f"\n  Manual SHA-1 blob hash pro {obsah!r}:")
print(f"  echo -e 'blob 10\\0Ahoj, Git!' | sha1sum")
print(f"  = {sha}")

# Refs
print("\n  Refs (references = pojmenované ukazatele na commity):")
cmd("show-ref --heads --tags")


# ══════════════════════════════════════════════════════════════
# ČÁST 6: Git hooks
# ══════════════════════════════════════════════════════════════

sekce("6. Git hooks")

HOOK_DIR = REPO / ".git" / "hooks"

# Pre-commit hook – zkontroluje syntax
pre_commit = HOOK_DIR / "pre-commit"
pre_commit.write_text("""\
#!/bin/sh
# Spustí se před každým commitem
echo "  [hook] Kontroluji Python syntax..."
for f in $(git diff --cached --name-only | grep '\\.py$'); do
    python3 -m py_compile "$f" 2>&1
    if [ $? -ne 0 ]; then
        echo "  [hook] ✗ Syntax chyba v $f"
        exit 1
    fi
done
echo "  [hook] ✓ Syntax OK"
exit 0
""")
pre_commit.chmod(0o755)

# Commit-msg hook – vynucuje konvenční commit zprávy
commit_msg = HOOK_DIR / "commit-msg"
commit_msg.write_text("""\
#!/bin/sh
# Conventional Commits: feat|fix|docs|refactor|test|chore: zpráva
MSG=$(cat "$1")
PATTERN='^(feat|fix|docs|refactor|test|chore|perf|ci)(\\(.+\\))?: .+'
if ! echo "$MSG" | grep -qE "$PATTERN"; then
    echo "  [hook] ✗ Špatný formát commit zprávy!"
    echo "  Použij: feat|fix|docs|refactor|test|chore: zpráva"
    echo "  Tvá zpráva: $MSG"
    exit 1
fi
exit 0
""")
commit_msg.chmod(0o755)

print("  Hooks nastaveny: pre-commit, commit-msg")

# Test hook
soubor("nova_funkce.py", "def nova(): pass\n")
git("add", "nova_funkce.py")
r = subprocess.run(
    ["git", "commit", "-m", "feat: nová funkce"],
    cwd=str(REPO), capture_output=True, text=True
)
print(f"\n  $ git commit -m 'feat: nová funkce'")
print(f"  {(r.stdout+r.stderr).strip()}")

r2 = subprocess.run(
    ["git", "commit", "-m", "přidal jsem věc"],
    cwd=str(REPO), capture_output=True, text=True
)
print(f"\n  $ git commit -m 'přidal jsem věc'")
print(f"  {(r2.stdout+r2.stderr).strip()}")


# ══════════════════════════════════════════════════════════════
# ČÁST 7: Přehled příkazů a workflow
# ══════════════════════════════════════════════════════════════

cmd("log --oneline --graph --all")

print("""
=== Git cheat sheet ===

  Denní práce:
    git status                  # co je změněno
    git add -p                  # interaktivní staging
    git commit -m "feat: ..."   # commitni
    git log --oneline --graph   # přehled
    git diff HEAD~1             # porovnej s předchozím

  Větve:
    git switch -c nova-vetev    # vytvoř a přepni
    git switch main             # přepni zpět
    git merge feature --no-ff   # merge (zachová historii)
    git rebase main             # rebase (lineární)
    git branch -d stara         # smaž větev

  Spolupráce:
    git clone <url>             # klonuj
    git pull --rebase           # pull + rebase
    git push -u origin feature  # push nové větve
    git fetch --all             # stáhni bez merge

  Opravy:
    git commit --amend          # oprav poslední commit
    git revert HEAD             # undo commitem (bezpečné)
    git reset --soft HEAD~1     # undo commitu (zůstane ve stage)
    git stash / git stash pop   # odlož / obnov
    git bisect start/good/bad   # najdi commit s bugem

  Konvenční commity:
    feat:     nová funkce
    fix:      oprava bugu
    docs:     dokumentace
    refactor: přepis bez změny chování
    test:     přidání testů
    chore:    CI, buildy, závislosti
    perf:     výkon
""")

# Úklid
import shutil
shutil.rmtree(REPO, ignore_errors=True)
print(f"  (Dočasný repozitář {REPO.name} smazán)")

# TVOJE ÚLOHA:
# 1. Napiš pre-commit hook který odmítne commit pokud soubor obsahuje "TODO".
# 2. Vytvoř vlastní alias: git lg = log --oneline --graph --all --decorate.
# 3. Použij git bisect na nalezení commitu který "rozbil" test.
# 4. Zkus git worktree – dvě working copy stejného repa současně.
