"""
LEKCE 61: C Extensions – Python ↔ C
=====================================
Kdy Python nestačí:
  - Kryptografické operace
  - Zpracování signálů / audio
  - Systémová volání
  - Integrace s legacy C/C++ knihovnami
  - Maximální výkon (kritické smyčky)

Způsoby volání C z Pythonu:
  ctypes      – vestavěný, volá sdílené knihovny (.so / .dll)
  cffi        – moderní alternativa k ctypes (pip install cffi)
  Cython      – Python → C kompilace (pip install cython)
  pybind11    – C++ bindings (pip install pybind11)
  ctypes.CDLL – přímý přístup k libc

Tato lekce: ctypes (žádná instalace) + cffi + Cython overview
"""

import ctypes
import ctypes.util
import struct
import sys
import time
from pathlib import Path

# ══════════════════════════════════════════════════════════════
# ČÁST 1: ctypes – volání C stdlib
# ══════════════════════════════════════════════════════════════

print("=== ctypes – volání C funkcí ===\n")

# Načti C standardní knihovnu
if sys.platform == "win32":
    libc = ctypes.CDLL("msvcrt")
else:
    libc_name = ctypes.util.find_library("c")
    libc = ctypes.CDLL(libc_name)

# printf
libc.printf(b"Hello z C printf: %d + %d = %d\n",
            ctypes.c_int(3), ctypes.c_int(4), ctypes.c_int(7))

# Matematické funkce z libm
if sys.platform != "win32":
    libm_name = ctypes.util.find_library("m")
    libm = ctypes.CDLL(libm_name)
    libm.sqrt.restype  = ctypes.c_double
    libm.sqrt.argtypes = [ctypes.c_double]
    libm.pow.restype   = ctypes.c_double
    libm.pow.argtypes  = [ctypes.c_double, ctypes.c_double]

    print(f"C sqrt(2.0) = {libm.sqrt(2.0):.6f}")
    print(f"C pow(2, 10) = {libm.pow(2.0, 10.0):.0f}")


# ── Struktury ────────────────────────────────────────────────

print("\n--- ctypes struktury ---")

class Bod(ctypes.Structure):
    _fields_ = [("x", ctypes.c_double),
                ("y", ctypes.c_double)]

    def vzdalenost(self, jiny: "Bod") -> float:
        return ((self.x - jiny.x)**2 + (self.y - jiny.y)**2)**0.5

    def __repr__(self):
        return f"Bod({self.x}, {self.y})"

a = Bod(0.0, 0.0)
b = Bod(3.0, 4.0)
print(f"  {a} → {b}: vzdálenost = {a.vzdalenost(b)}")
print(f"  Velikost v paměti: {ctypes.sizeof(Bod)} B  (2× double = 16 B)")

# Pole struktur
pole_bodu = (Bod * 3)(Bod(1, 2), Bod(3, 4), Bod(5, 6))
print(f"  Pole bodů: {[f'({p.x},{p.y})' for p in pole_bodu]}")


# ── Ukazatele ────────────────────────────────────────────────

print("\n--- Ukazatele (pointers) ---")

cislo = ctypes.c_int(42)
ukazatel = ctypes.pointer(cislo)
print(f"  Hodnota:  {cislo.value}")
print(f"  Ukazatel: {ukazatel}")
print(f"  Dereference: {ukazatel.contents.value}")

ukazatel.contents.value = 99
print(f"  Po změně přes ukazatel: {cislo.value}")

# byref – efektivnější pro předávání do funkcí
def c_add(a_ref, b_ref):
    """Simulace funkce která modifikuje hodnotu přes pointer."""
    a_ref._obj.value += b_ref._obj.value

x = ctypes.c_int(10)
y = ctypes.c_int(20)
c_add(ctypes.byref(x), ctypes.byref(y))
print(f"  Po c_add: x={x.value}")


# ══════════════════════════════════════════════════════════════
# ČÁST 2: Vlastní C extension (kompilace za běhu)
# ══════════════════════════════════════════════════════════════

print("\n=== Vlastní C kód kompilovaný za běhu ===\n")

import tempfile
import subprocess
import os

C_KOD = """\
#include <stdlib.h>
#include <math.h>

// Rychlé třídění (qsort z stdlib)
int porovnej_double(const void* a, const void* b) {
    double da = *(double*)a;
    double db = *(double*)b;
    return (da > db) - (da < db);
}

void quick_sort(double* pole, int n) {
    qsort(pole, n, sizeof(double), porovnej_double);
}

// Skalární součin (dot product)
double dot_product(double* a, double* b, int n) {
    double vysledek = 0.0;
    for (int i = 0; i < n; i++) {
        vysledek += a[i] * b[i];
    }
    return vysledek;
}

// Norma vektoru
double norma(double* v, int n) {
    double suma = 0.0;
    for (int i = 0; i < n; i++) {
        suma += v[i] * v[i];
    }
    return sqrt(suma);
}
"""

# Zkus zkompilovat
def zkompiluj_c(kod: str) -> ctypes.CDLL | None:
    with tempfile.TemporaryDirectory() as tmpdir:
        c_soubor = Path(tmpdir) / "ext.c"
        so_soubor = Path(tmpdir) / "ext.so"
        c_soubor.write_text(kod)

        # Přelož do sdílené knihovny
        r = subprocess.run(
            ["gcc", "-shared", "-fPIC", "-O2", "-o", str(so_soubor),
             str(c_soubor), "-lm"],
            capture_output=True, text=True
        )
        if r.returncode != 0:
            return None

        # Zkopíruj mimo tmpdir (jinak se smaže)
        import shutil
        cil = Path("/tmp/python_kurz_ext.so")
        shutil.copy(so_soubor, cil)
        return ctypes.CDLL(str(cil))

lib = zkompiluj_c(C_KOD)

if lib:
    print("  ✓ C kód zkompilován\n")

    # Nastav typy
    lib.quick_sort.argtypes = [ctypes.POINTER(ctypes.c_double), ctypes.c_int]
    lib.quick_sort.restype  = None
    lib.dot_product.argtypes = [ctypes.POINTER(ctypes.c_double),
                                  ctypes.POINTER(ctypes.c_double), ctypes.c_int]
    lib.dot_product.restype  = ctypes.c_double
    lib.norma.argtypes = [ctypes.POINTER(ctypes.c_double), ctypes.c_int]
    lib.norma.restype  = ctypes.c_double

    # qsort
    import random
    data = [random.uniform(-10, 10) for _ in range(10)]
    print(f"  Před sort: {[round(x,2) for x in data]}")
    c_pole = (ctypes.c_double * len(data))(*data)
    lib.quick_sort(c_pole, len(data))
    print(f"  Po sort:   {[round(c_pole[i],2) for i in range(len(data))]}")

    # dot product
    a = [1.0, 2.0, 3.0]
    b = [4.0, 5.0, 6.0]
    ca = (ctypes.c_double * 3)(*a)
    cb = (ctypes.c_double * 3)(*b)
    dot = lib.dot_product(ca, cb, 3)
    print(f"\n  dot([1,2,3], [4,5,6]) = {dot:.1f}  (= 1×4 + 2×5 + 3×6 = 32)")

    # Výkon: Python vs C qsort
    N = 100_000
    data_velke = [random.random() for _ in range(N)]
    c_velke = (ctypes.c_double * N)(*data_velke)

    t0 = time.perf_counter()
    sorted(data_velke)
    t_python = time.perf_counter() - t0

    t0 = time.perf_counter()
    lib.quick_sort(c_velke, N)
    t_c = time.perf_counter() - t0

    print(f"\n  Třídění {N:_} čísel:")
    print(f"  Python sorted(): {t_python*1000:.1f} ms")
    print(f"  C qsort:         {t_c*1000:.1f} ms")

    Path("/tmp/python_kurz_ext.so").unlink(missing_ok=True)
else:
    print("  gcc nedostupný – přeskakuji kompilaci C kódu")


# ══════════════════════════════════════════════════════════════
# ČÁST 3: Struct – binární protokoly
# ══════════════════════════════════════════════════════════════

print("\n=== struct – binární data ===\n")

# Packet formát: header (magic 4B, version 2B, length 4B) + data
MAGIC = b"PKTS"

def zabal_packet(data: bytes, verze: int = 1) -> bytes:
    header = struct.pack(">4sHI", MAGIC, verze, len(data))
    return header + data

def rozbal_packet(raw: bytes) -> tuple[int, bytes]:
    header_size = struct.calcsize(">4sHI")
    magic, verze, delka = struct.unpack(">4sHI", raw[:header_size])
    assert magic == MAGIC, f"Špatné magic bytes: {magic}"
    return verze, raw[header_size:header_size + delka]

zprava = b"Hello, binary world!"
packet = zabal_packet(zprava, verze=2)
print(f"  Zpráva:  {zprava}")
print(f"  Packet:  {packet.hex()}")
print(f"  Délka:   {len(packet)} B (10B header + {len(zprava)}B data)")

verze, rozbalena = rozbal_packet(packet)
print(f"  Rozbaleno: verze={verze}, data={rozbalena}")

# Různé datové typy ve struct
fmt = "!BHHIQ f d 4s"  # network byte order (big-endian)
hodnoty = (255, 1000, 65535, 2**31, 2**62, 3.14, 2.718281828, b"TEST")
packed = struct.pack(fmt, *hodnoty)
print(f"\n  Zabaleno {len(hodnoty)} hodnot do {len(packed)} B")
unpacked = struct.unpack(fmt, packed)
print(f"  Rozbaleno: {unpacked}")


# ══════════════════════════════════════════════════════════════
# ČÁST 4: Přehled alternativ
# ══════════════════════════════════════════════════════════════

print("""
=== Kdy co použít ===

  ctypes      → volání existující .so/.dll, žádná instalace
                přímý přístup k C stdlib (malloc, memcpy...)

  cffi        → modernější API než ctypes, lepší pro komplexní C API
                pip install cffi

  Cython      → Python kód zkompilovaný do C → 10–100× rychlejší
                pip install cython
                Píšeš .pyx soubory s type hints → generuje .c → kompiluje

  pybind11    → C++ ↔ Python bindings, moderní C++11
                pip install pybind11

  SWIG        → automatické wrappery pro C/C++/Fortran

  numpy.ctypeslib → integrace ctypes s NumPy poli

Typický use-case:
  Python prototyp → profiluj → optimalizuj bottleneck v Cython/C
""")

# TVOJE ÚLOHA:
# 1. Napiš C funkci fibonacci(n) a porovnej rychlost s Python verzí.
# 2. Pomocí struct implementuj jednoduchý binární formát pro ukládání dat.
# 3. Prozkoumej ctypes.memmove/memset pro práci s raw pamětí.
