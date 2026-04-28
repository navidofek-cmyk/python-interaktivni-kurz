"""Reseni – Lekce 57: CPython internals"""

import dis
import ast
import sys
import gc
import inspect


# 1. AST transformer: automaticky pridat type hints None → Optional

print("=== Ukol 1: AST transformer None → Optional ===\n")


class NoneToOptionalTransformer(ast.NodeTransformer):
    """Transformuje anotace 'None' na 'Optional[...] | None' vzor.
    Konkretne: pokud return annotation je None, necha to.
    Pokud parametr ma annotation X a muze byt None, prida X | None.
    """

    def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.FunctionDef:
        # Zkontroluj navratovy typ
        if (node.returns and
                isinstance(node.returns, ast.Constant) and
                node.returns.value is None):
            # Uz je None – OK
            pass

        # Zpracuj parametry – pridej | None pokud chybi
        # (ukazka: pridame "| None" ke vsem anotovanym parametrum)
        for arg in node.args.args:
            if (arg.annotation and
                    not (isinstance(arg.annotation, ast.Constant) and
                         arg.annotation.value is None)):
                # Obal do Optional (BinOp X | None)
                arg.annotation = ast.BinOp(
                    left=arg.annotation,
                    op=ast.BitOr(),
                    right=ast.Constant(value=None),
                )

        self.generic_visit(node)
        return node


# Demonstrace na kratkem kodu
zdrojovy_kod = """\
def pozdrav(jmeno: str) -> str:
    return f"Ahoj, {jmeno}!"

def ziskej_vek(uzivatel: dict) -> int:
    return uzivatel.get("vek", 0)
"""

strom = ast.parse(zdrojovy_kod)
print("Puvodni AST (prvni funkce):")
for uzel in ast.walk(strom):
    if isinstance(uzel, ast.FunctionDef):
        print(f"  def {uzel.name}(")
        for arg in uzel.args.args:
            ann = ast.unparse(arg.annotation) if arg.annotation else "?"
            print(f"    {arg.arg}: {ann}")
        print(f"  ) -> {ast.unparse(uzel.returns) if uzel.returns else '?'}")

transformovany = NoneToOptionalTransformer().visit(strom)
ast.fix_missing_locations(transformovany)
print("\nPo transformaci (anotace s | None):")
for uzel in ast.walk(transformovany):
    if isinstance(uzel, ast.FunctionDef):
        print(f"  def {uzel.name}(")
        for arg in uzel.args.args:
            ann = ast.unparse(arg.annotation) if arg.annotation else "?"
            print(f"    {arg.arg}: {ann}")
        print(f"  ) -> {ast.unparse(uzel.returns) if uzel.returns else '?'}")


# 2. Prec je 'x in set' rychlejsi nez 'x in list' (bytecode analýza)

print("\n=== Ukol 2: x in set vs x in list (bytecode) ===\n")


def hledej_v_listu(x, lst):
    return x in lst


def hledej_v_setu(x, s):
    return x in s


print("Bytecode hledej_v_listu:")
dis.dis(hledej_v_listu)

print("\nBytecode hledej_v_setu:")
dis.dis(hledej_v_setu)

print("""
Vysvetleni proc set je rychlejsi:
  - Oba pouzivaji instrukci CONTAINS_OP
  - Rozdil je v DATOVE STRUKTURE, ne v bytecodu
  - List: lineárni prohledavani O(N) – kazdy prvek porovna
  - Set:  hash tabulka O(1) – spocita hash(x), najde bucket okamzite

  Bytecode je stejny, ale CPython vola ruzne __contains__ metody:
    list.__contains__ → prochazi jeden po druhem
    set.__contains__  → hash lookup (bucket v hash tabulce)
""")

import timeit
N = 10_000
lst = list(range(N))
s   = set(lst)
t_list = timeit.timeit(lambda: 9999 in lst, number=100_000)
t_set  = timeit.timeit(lambda: 9999 in s,   number=100_000)
print(f"  list lookup: {t_list:.3f}s")
print(f"  set lookup:  {t_set:.3f}s  ({t_list/t_set:.0f}x rychlejsi)")


# 3. Profiler pomoci sys.setprofile()

print("\n=== Ukol 3: Profiler pres sys.setprofile() ===\n")


class SimpleProfiler:
    """Jednoduchy profiler ktery loguje kazde volani funkce."""

    def __init__(self):
        self._zaznamy: list[dict] = []
        self._aktivni = False

    def _handler(self, frame, udalost: str, arg) -> None:
        if udalost in ("call", "return", "c_call", "c_return"):
            if udalost in ("call", "return"):
                fn_name = frame.f_code.co_name
                soubor  = frame.f_code.co_filename.split("/")[-1]
                self._zaznamy.append({
                    "udalost": udalost,
                    "funkce":  fn_name,
                    "soubor":  soubor,
                })

    def start(self) -> None:
        self._zaznamy.clear()
        self._aktivni = True
        sys.setprofile(self._handler)

    def stop(self) -> None:
        sys.setprofile(None)
        self._aktivni = False

    def tiskni_report(self, max_zaznamu: int = 15) -> None:
        print(f"  Celkem zaznamu: {len(self._zaznamy)}")
        volani: dict[str, int] = {}
        for z in self._zaznamy:
            if z["udalost"] == "call":
                klic = f"{z['soubor']}:{z['funkce']}"
                volani[klic] = volani.get(klic, 0) + 1
        print(f"\n  Nejcasteji volane funkce:")
        for fn, pocet in sorted(volani.items(), key=lambda x: -x[1])[:max_zaznamu]:
            print(f"    {pocet:4d}x  {fn}")


def testovana_funkce():
    """Funkce pro profilovani."""
    data = [i**2 for i in range(50)]
    return sum(data)


profiler = SimpleProfiler()
profiler.start()
for _ in range(5):
    testovana_funkce()
profiler.stop()
profiler.tiskni_report()


# 4. Porovnani velikosti objektu s __slots__ vs bez

print("\n=== Ukol 4: __slots__ vs bez – pameti ===\n")


class BezSlots:
    def __init__(self, x: int, y: int, z: int):
        self.x = x
        self.y = y
        self.z = z


class SeSlots:
    __slots__ = ("x", "y", "z")

    def __init__(self, x: int, y: int, z: int):
        self.x = x
        self.y = y
        self.z = z


bez = BezSlots(1, 2, 3)
se  = SeSlots(1, 2, 3)

# sys.getsizeof pocita jen primo objekt, ne __dict__
size_bez = sys.getsizeof(bez) + sys.getsizeof(bez.__dict__)
size_se  = sys.getsizeof(se)

print(f"  BezSlots instance: {sys.getsizeof(bez)} B (objekt)")
print(f"  BezSlots __dict__: {sys.getsizeof(bez.__dict__)} B")
print(f"  BezSlots celkem:   {size_bez} B")
print(f"  SeSlots instance:  {size_se} B (objekt, bez __dict__)")
print(f"  Uspore pameti:     {size_bez - size_se} B na instanci")
print(f"\n  Pri 100 000 instancich:")
print(f"    Bez __slots__: ~{(size_bez * 100_000) // 1024 // 1024} MB")
print(f"    Se __slots__:  ~{(size_se * 100_000) // 1024 // 1024} MB")
