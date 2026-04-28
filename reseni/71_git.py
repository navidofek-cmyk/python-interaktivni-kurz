"""Řešení – Lekce 71: Git – verzování kódu"""

import subprocess
import tempfile
import shutil
from pathlib import Path

REPO = Path(tempfile.mkdtemp(prefix="git_reseni_"))

def git(*args, cwd=None, check=False) -> str:
    r = subprocess.run(
        ["git", *args],
        cwd=str(cwd or REPO),
        capture_output=True, text=True,
    )
    return (r.stdout + r.stderr).strip()

def soubor(jmeno: str, obsah: str):
    (REPO / jmeno).write_text(obsah, encoding="utf-8")

# Inicializace
git("init", "-b", "main")
git("config", "user.name", "Demo User")
git("config", "user.email", "demo@kurz.cz")
git("config", "core.autocrlf", "false")
print(f"Repozitář: {REPO}\n")

# 1. Pre-commit hook – odmítne commit pokud soubor obsahuje "TODO"
print("=== 1. Pre-commit hook blokující TODO ===\n")

HOOK_DIR = REPO / ".git" / "hooks"
pre_commit = HOOK_DIR / "pre-commit"
pre_commit.write_text("""\
#!/bin/sh
# Odmítne commit pokud staged soubor obsahuje "TODO"
for f in $(git diff --cached --name-only); do
    if git show ":$f" 2>/dev/null | grep -q "TODO"; then
        echo "[hook] CHYBA: soubor $f obsahuje TODO!"
        echo "[hook] Odstraň TODO před commitem."
        exit 1
    fi
done
echo "[hook] OK – žádné TODO v staged souborech."
exit 0
""")
pre_commit.chmod(0o755)

# Test: commit bez TODO projde
soubor("hello.py", 'print("Ahoj")\n')
git("add", "hello.py")
r1 = subprocess.run(["git", "commit", "-m", "feat: hello bez TODO"],
                    cwd=str(REPO), capture_output=True, text=True)
print(f"Commit bez TODO: {(r1.stdout+r1.stderr).strip()}")

# Test: commit s TODO selže
soubor("wip.py", "# TODO: dodělat\ndef funkce(): pass\n")
git("add", "wip.py")
r2 = subprocess.run(["git", "commit", "-m", "feat: wip"],
                    cwd=str(REPO), capture_output=True, text=True)
print(f"Commit s TODO: {(r2.stdout+r2.stderr).strip()}")

# 2. Git alias: git lg = log --oneline --graph --all --decorate
print("\n=== 2. Alias git lg ===\n")

git("config", "alias.lg", "log --oneline --graph --all --decorate")
# Přidej pár commitů pro test
soubor("a.py", "x = 1\n")
git("add", "a.py")
git("commit", "-m", "feat: a.py")
soubor("b.py", "y = 2\n")
git("add", "b.py")
git("commit", "-m", "feat: b.py")

vystup_lg = git("lg")
print("git lg výstup:")
for radek in vystup_lg.splitlines()[:8]:
    print(f"  {radek}")
print("  (alias funguje – zkratka pro dekorovaný log)\n")

# 3. Git bisect – najde commit který "rozbil" test
print("=== 3. Git bisect ===\n")

# Vytvoř historii: commit 1-5 jsou "dobré", commit 6 zavedl bug
soubor("vypocet.py", "def vypocet(x): return x * 2\n")
git("add", "vypocet.py")
git("commit", "-m", "feat: vypocet v1")

for verze in range(2, 6):
    soubor("vypocet.py", f"def vypocet(x): return x * {verze}\n")
    git("add", "vypocet.py")
    git("commit", "-m", f"feat: vypocet v{verze}")

# Verze 6 = bug (vrací záporné číslo pro kladný vstup)
soubor("vypocet.py", "def vypocet(x): return -abs(x)\n")
git("add", "vypocet.py")
git("commit", "-m", "feat: vypocet v6 – BUG TADY")

# Bisect: find first bad commit
log_output = git("log", "--oneline")
commits = [line.split()[0] for line in log_output.splitlines()]
bad_hash  = commits[0]   # HEAD = v6 (bug)
good_hash = commits[-1]  # nejstarší = v1 (bez bugu)

print("Spuštění git bisect:")
print(f"  git bisect start")
print(f"  git bisect bad  {bad_hash}   # aktuální = špatný")
print(f"  git bisect good {good_hash}  # nejstarší = dobrý")
print()

# Simulace bisect skriptu
bisect_skript = REPO / "test_vypocet.sh"
bisect_skript.write_text("""\
#!/bin/sh
# Test: vypocet(5) musí vrátit kladné číslo
python3 -c "
import sys
sys.path.insert(0, '.')
from vypocet import vypocet
result = vypocet(5)
sys.exit(0 if result > 0 else 1)
"
""")
bisect_skript.chmod(0o755)

git("bisect", "start")
git("bisect", "bad", bad_hash)
git("bisect", "good", good_hash)
r_bisect = subprocess.run(
    ["git", "bisect", "run", str(bisect_skript)],
    cwd=str(REPO), capture_output=True, text=True
)
print("Bisect výstup (zkráceno):")
for radek in (r_bisect.stdout + r_bisect.stderr).splitlines()[-5:]:
    if radek.strip():
        print(f"  {radek}")
git("bisect", "reset")

# 4. Git worktree – dvě working copy současně
print("\n=== 4. Git worktree ===\n")

worktree_cesta = Path(tempfile.mkdtemp(prefix="git_worktree_"))
try:
    git("branch", "feature/worktree-demo")
    r_wt = subprocess.run(
        ["git", "worktree", "add", str(worktree_cesta), "feature/worktree-demo"],
        cwd=str(REPO), capture_output=True, text=True
    )
    print(f"Worktree vytvořen: {worktree_cesta}")
    print(f"  Původní repo:  {REPO}")
    print(f"  Worktree větev: feature/worktree-demo")

    # Práce ve worktree
    (worktree_cesta / "nova_funkce.py").write_text('def nova(): return 42\n')
    git("add", "nova_funkce.py", cwd=worktree_cesta)
    git("commit", "-m", "feat: nova funkce ve worktree", cwd=worktree_cesta)

    print("\n  Worktree list:")
    wt_list = git("worktree", "list")
    for radek in wt_list.splitlines():
        print(f"  {radek}")

    # Cleanup worktree
    git("worktree", "remove", str(worktree_cesta), "--force")
    print("\n  Worktree odstraněn.")
except Exception as e:
    print(f"  (worktree info: {e})")
finally:
    shutil.rmtree(worktree_cesta, ignore_errors=True)

shutil.rmtree(REPO, ignore_errors=True)
print(f"\nDočasný repozitář smazán.")
