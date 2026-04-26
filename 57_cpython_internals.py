"""
LEKCE 57: CPython internals – jak Python opravdu funguje
=========================================================
CPython = referenční implementace Pythonu (ten co instaluješ).

Tok spuštění:
  zdrojový kód (.py)
    → Lexer (tokeny)
    → Parser (AST)
    → Kompilátor (bytecode .pyc)
    → Interpreter (CPython VM)

Moduly pro zkoumání:
  dis       – disassembler bytekódu
  ast       – abstraktní syntaktický strom
  sys       – info o interpreteru
  gc        – garbage collector
  inspect   – introspekce objektů
  ctypes    – přímý přístup k paměti
  opcode    – seznam operačních kódů
"""

import dis
import ast
import sys
import gc
import inspect
import struct
import time
from types import CodeType

# ══════════════════════════════════════════════════════════════
# ČÁST 1: AST – abstraktní syntaktický strom
# ══════════════════════════════════════════════════════════════

print("=== AST – abstraktní syntaktický strom ===\n")

kod = "x = 1 + 2 * 3"
strom = ast.parse(kod)

print(f"Kód: {kod!r}")
print(f"AST dump:\n{ast.dump(strom, indent=2)}\n")

# Procházení stromu
class VypisNavstev(ast.NodeVisitor):
    def visit_BinOp(self, node):
        op_name = type(node.op).__name__
        print(f"  BinOp: {op_name}")
        self.generic_visit(node)

    def visit_Constant(self, node):
        print(f"  Constant: {node.value!r}")

print("Uzly v AST:")
VypisNavstev().visit(strom)

# Transformace AST – auto-optimalizace
class NasobeniNaSoucet(ast.NodeTransformer):
    """Nahradí x*2 za x+x (akademická ukázka)."""
    def visit_BinOp(self, node):
        self.generic_visit(node)
        if (isinstance(node.op, ast.Mult)
                and isinstance(node.right, ast.Constant)
                and node.right.value == 2):
            return ast.BinOp(left=node.left, op=ast.Add(), right=node.left)
        return node

vstup = "y = x * 2"
strom2 = ast.parse(vstup)
upraveny = NasobeniNaSoucet().visit(strom2)
ast.fix_missing_locations(upraveny)
print(f"\nTransformace: {vstup!r} → {ast.unparse(upraveny)!r}")


# ══════════════════════════════════════════════════════════════
# ČÁST 2: Bytekód – dis modul
# ══════════════════════════════════════════════════════════════

print("\n=== Bytekód (dis) ===\n")

def faktorial(n):
    if n <= 1:
        return 1
    return n * faktorial(n - 1)

print(f"Bytekód faktorial():")
dis.dis(faktorial)

# Porovnání efektivity
def verze_a(lst):
    result = []
    for x in lst:
        result.append(x * 2)
    return result

def verze_b(lst):
    return [x * 2 for x in lst]

print(f"\nVerze A (for + append) – počet instrukcí:")
a_instr = list(dis.get_instructions(verze_a))
print(f"  {len(a_instr)} instrukcí")

print(f"Verze B (list comprehension) – počet instrukcí:")
b_instr = list(dis.get_instructions(verze_b))
print(f"  {len(b_instr)} instrukcí")

# Přístup k objektu kódu
kod_obj: CodeType = faktorial.__code__
print(f"\nAtributy __code__ faktorial():")
print(f"  co_name:      {kod_obj.co_name}")
print(f"  co_varnames:  {kod_obj.co_varnames}")
print(f"  co_consts:    {kod_obj.co_consts}")
print(f"  co_stacksize: {kod_obj.co_stacksize}")
print(f"  co_flags:     {kod_obj.co_flags:#010x}")


# ══════════════════════════════════════════════════════════════
# ČÁST 3: Garbage Collector
# ══════════════════════════════════════════════════════════════

print("\n=== Garbage Collector ===\n")

print(f"GC thresholds: {gc.get_threshold()}")
print(f"GC counts:     {gc.get_count()}")
print(f"GC enabled:    {gc.isenabled()}")

# Reference counting – základ správy paměti v CPython
import ctypes

def pocet_referenci(obj) -> int:
    return sys.getrefcount(obj) - 1  # -1 za dočasnou referenci v getrefcount

x = [1, 2, 3]
print(f"\nReference na seznam [1,2,3]: {pocet_referenci(x)}")
y = x
print(f"Po y = x: {pocet_referenci(x)}")
z = x
print(f"Po z = x: {pocet_referenci(x)}")
del z
print(f"Po del z: {pocet_referenci(x)}")

# Cyklické reference
print("\nCyklická reference:")

class Uzel:
    def __init__(self, hodnota):
        self.hodnota = hodnota
        self.dalsi = None
    def __del__(self):
        pass  # zavolá se při smazání

gc.collect()  # vyčisti před testem
pred = len(gc.garbage)

a = Uzel(1)
b = Uzel(2)
a.dalsi = b   # a → b
b.dalsi = a   # b → a  ← cyklus!

del a, b      # ref count neklesne na 0 kvůli cyklu
collected = gc.collect()
print(f"  gc.collect() sebral {collected} objektů z cyklů")

# Slabé reference
import weakref

class Tezky:
    def __init__(self, data):
        self.data = data

obj = Tezky("velká data")
slaby = weakref.ref(obj)
print(f"\nSlabá reference:")
print(f"  slaby() = {slaby()}")  # vrátí objekt
del obj
print(f"  po del obj: slaby() = {slaby()}")  # vrátí None


# ══════════════════════════════════════════════════════════════
# ČÁST 4: Inspect – introspekce
# ══════════════════════════════════════════════════════════════

print("\n=== inspect – introspekce ===\n")

class Priklad:
    """Ukázková třída pro introspekci."""

    def __init__(self, x: int, y: int = 0) -> None:
        self.x = x
        self.y = y

    def secti(self, z: float = 1.0) -> float:
        """Sečte x, y a z."""
        return self.x + self.y + z

    @classmethod
    def z_retezce(cls, s: str) -> "Priklad":
        a, b = map(int, s.split(","))
        return cls(a, b)

    @staticmethod
    def verze() -> str:
        return "1.0"

p = Priklad(3, 4)

print(f"Metody třídy Priklad:")
for jmeno, obj in inspect.getmembers(Priklad, predicate=inspect.isfunction):
    sig = inspect.signature(obj)
    print(f"  {jmeno}{sig}")

print(f"\nSignatura Priklad.secti:")
sig = inspect.signature(Priklad.secti)
for param_name, param in sig.parameters.items():
    print(f"  {param_name}: {param.annotation}  default={param.default}")

print(f"\nZdroj secti():")
print(textwrap.indent(inspect.getsource(Priklad.secti), "  "))

import textwrap

# Zjisti MRO (Method Resolution Order)
class A: pass
class B(A): pass
class C(A): pass
class D(B, C): pass

print(f"\nMRO pro D(B, C):")
for cls in D.__mro__:
    print(f"  {cls.__name__}")


# ══════════════════════════════════════════════════════════════
# ČÁST 5: sys – interpreter info
# ══════════════════════════════════════════════════════════════

print("\n=== sys – interpreter info ===\n")

print(f"Python verze:    {sys.version}")
print(f"Platform:        {sys.platform}")
print(f"Max int:         {sys.maxsize:,}")
print(f"Float info:      min={sys.float_info.min:.2e}  max={sys.float_info.max:.2e}")
print(f"Recursion limit: {sys.getrecursionlimit()}")
print(f"Byteorder:       {sys.byteorder}")

# Velikosti objektů v paměti
print(f"\nVelikosti objektů:")
for obj, label in [
    (None,        "None"),
    (True,        "bool"),
    (42,          "int(42)"),
    (42.0,        "float"),
    ("hello",     "str('hello')"),
    ([1,2,3],     "list[3]"),
    ({1,2,3},     "set{3}"),
    ({"a":1},     "dict{1}"),
    (lambda: None,"lambda"),
]:
    print(f"  {label:<20} {sys.getsizeof(obj):>6} B")

# Zajímavost: malá celá čísla jsou cached
print(f"\nMalá čísla jsou cached (id je stejné):")
a, b = 100, 100
print(f"  100 is 100: {a is b}  (id: {id(a)} == {id(b)})")
c, d = 1000, 1000
print(f"  1000 is 1000: {c is d}  (id: {id(c)} != {id(d)})")

# TVOJE ÚLOHA:
# 1. Napiš AST transformer který automaticky přidá type hints None → Optional.
# 2. Pomocí dis zjisti proč je 'x in set' rychlejší než 'x in list'.
# 3. Napiš profiler pomocí sys.setprofile() který loguje každé volání funkce.
# 4. Porovnej velikost objektu s __slots__ vs bez (sys.getsizeof).
