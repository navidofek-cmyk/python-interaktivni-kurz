"""Reseni – Lekce 61: C Extensions"""

import ctypes
import ctypes.util
import struct
import sys
import time
import timeit


# 1. Fibonacci v C vs Python – porovnani rychlosti

print("=== Ukol 1: Fibonacci – Python vs ctypes (libc matematika) ===\n")


def fib_python(n: int) -> int:
    """Fibonacci v cilem Pythonu."""
    if n < 2:
        return n
    a, b = 0, 1
    for _ in range(n - 1):
        a, b = b, a + b
    return b


# ctypes: pouzijeme libc pro demonstraci C overhead
libc_name = ctypes.util.find_library("c")
if libc_name:
    libc = ctypes.CDLL(libc_name)
    libc.abs.restype = ctypes.c_int
    libc.abs.argtypes = [ctypes.c_int]
else:
    libc = None


def fib_ctypes_sim(n: int) -> int:
    """Fibonacci pouzivajici ctypes pro volani libc abs() (overhead demo)."""
    if n < 2:
        return n
    a, b = 0, 1
    for _ in range(n - 1):
        a, b = b, a + b
    # Volani libc.abs demonstruje ctypes overhead
    if libc:
        return libc.abs(b)   # abs(b) = b pro kladna cisla
    return b


N_FIB = 200
OPAK  = 50_000

t_py = timeit.timeit(lambda: fib_python(N_FIB),    number=OPAK)
t_ct = timeit.timeit(lambda: fib_ctypes_sim(N_FIB), number=OPAK)

print(f"fib({N_FIB}) x {OPAK:,} opakovani:")
print(f"  Python ciste:    {t_py*1000:.2f} ms")
print(f"  ctypes (s abs):  {t_ct*1000:.2f} ms")
print(f"  Poznamka: ctypes pridava overhead per-call ~ 1-5µs")
print(f"           Pro 'fib v C' by bylo potreba zkompilovat .so soubor")

# Ukazka Cython kodu ktery by byl rychlejsi
CYTHON_FIB = """\
# fib.pyx  (Cython zdrojovy kod)
# Kompilace: cython fib.pyx && gcc -shared -o fib.so fib.c -fPIC `python3-config --includes`
# nebo pres setup.py

def fib_cython(int n) -> int:
    cdef int a = 0, b = 1, i
    if n < 2:
        return n
    for i in range(n - 1):
        a, b = b, a + b
    return b

# Rychlost: ~10-50x rychlejsi nez Python (bez GIL overhead)
"""
print(f"\nCython fib (ukaz kodu):\n{CYTHON_FIB}")


# 2. Struct – binarni format pro ukládání dat

print("=== Ukol 2: Binarni format pomoci struct ===\n")


class BinarniDB:
    """Jednoduchy binarni soubor pro ukládání zaznamu."""

    # Format: magic(4B) + verze(2B) + pocet(4B) | zaznam: id(4B) + jmeno(20s) + vek(1B) + body(4f)
    MAGIC   = b"KDBF"
    VERZE   = 1
    HDR_FMT = "!4sHI"              # magic, verze, pocet zaznamu
    HDR_SZ  = struct.calcsize(HDR_FMT)
    REC_FMT = "!I20sBI"            # id, jmeno(20), vek, body*100 (int)
    REC_SZ  = struct.calcsize(REC_FMT)

    def __init__(self):
        self._zaznamy: list[dict] = []

    def pridej(self, id_: int, jmeno: str, vek: int, body: float) -> None:
        self._zaznamy.append({"id": id_, "jmeno": jmeno, "vek": vek, "body": body})

    def uloz(self, buffer: bytearray) -> bytes:
        """Serializuje vsechny zaznamy do bytes."""
        data = bytearray()
        # Header
        data += struct.pack(self.HDR_FMT, self.MAGIC, self.VERZE, len(self._zaznamy))
        # Zaznamy
        for z in self._zaznamy:
            jmeno_bytes = z["jmeno"].encode("utf-8")[:20].ljust(20, b"\x00")
            data += struct.pack(
                self.REC_FMT,
                z["id"],
                jmeno_bytes,
                z["vek"],
                int(z["body"] * 100),  # float jako int*100
            )
        return bytes(data)

    @classmethod
    def nacti(cls, data: bytes) -> "BinarniDB":
        """Deserializuje data z bytes."""
        db = cls()
        magic, verze, pocet = struct.unpack_from(cls.HDR_FMT, data, 0)
        assert magic == cls.MAGIC, f"Spatne magic: {magic}"
        assert verze == cls.VERZE, f"Nepodporovana verze: {verze}"
        offset = cls.HDR_SZ
        for _ in range(pocet):
            id_, jmeno_bytes, vek, body_int = struct.unpack_from(cls.REC_FMT, data, offset)
            jmeno = jmeno_bytes.rstrip(b"\x00").decode("utf-8")
            db.pridej(id_, jmeno, vek, body_int / 100.0)
            offset += cls.REC_SZ
        return db


# Test
db = BinarniDB()
db.pridej(1, "Misa",  15, 87.5)
db.pridej(2, "Tomas", 16, 92.0)
db.pridej(3, "Bara",  14, 78.3)

serizalizovano = db.uloz(bytearray())
print(f"Serializovano {len(db._zaznamy)} zaznamu do {len(serizalizovano)} B")
print(f"  Header: {len(db.HDR_FMT)} sloupce")
print(f"  Zaznam: {db.REC_SZ} B/zaznam (pevna velikost)")

nacten = BinarniDB.nacti(serizalizovano)
print("\nNacten zpet:")
for z in nacten._zaznamy:
    print(f"  id={z['id']} jmeno={z['jmeno']!r} vek={z['vek']} body={z['body']}")

# Porovnej s JSON
import json
json_data = json.dumps(db._zaznamy, ensure_ascii=False).encode()
print(f"\nSrovnani velikosti:")
print(f"  Binarni (struct): {len(serizalizovano)} B")
print(f"  JSON:             {len(json_data)} B")
print(f"  Uspora:           {(1 - len(serizalizovano)/len(json_data))*100:.0f}%")


# 3. ctypes.memmove / memset demo

print("\n=== Ukol 3: ctypes.memmove a memset ===\n")

# Vytvor buffer 16 bajtu
buf = (ctypes.c_char * 16)()
print(f"Prazdny buffer: {bytes(buf).hex()}")

# memset – nastav buffer na hodnotu 0xAB
ctypes.memset(buf, 0xAB, 16)
print(f"Po memset(0xAB): {bytes(buf).hex()}")

# memmove – zkopiruj prvnich 8 bajtu na pozici 8
src = (ctypes.c_char * 8)(*b"PYTHON!!")
ctypes.memmove(ctypes.addressof(buf) + 8, src, 8)
print(f"Po memmove:      {bytes(buf).hex()}  = '{bytes(buf).decode(errors='replace')}'")

# Praci s C polem pres ctypes
pole_c = (ctypes.c_int * 5)(1, 2, 3, 4, 5)
print(f"\nC pole: {list(pole_c)}")
ctypes.memmove(pole_c, (ctypes.c_int * 5)(10, 20, 30, 40, 50), ctypes.sizeof(pole_c))
print(f"Po memmove: {list(pole_c)}")
