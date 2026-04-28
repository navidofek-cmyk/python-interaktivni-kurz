"""Řešení – Lekce 29: @dataclass – třídy bez zbytečného kódu"""

from dataclasses import dataclass, field, asdict, astuple
import json
import math


# ── 1. Hrac s do_dict() a from_dict() ───────────────────────────────────────

@dataclass
class Hrac:
    jmeno: str
    hp: int = 100
    utok: int = 15
    inventar: list = field(default_factory=list)
    level: int = field(default=1, repr=False)

    def __post_init__(self):
        self.max_hp = self.hp

    @property
    def je_nazivu(self):
        return self.hp > 0

    def lec(self, mnozstvi: int = 20):
        self.hp = min(self.max_hp, self.hp + mnozstvi)

    # 1. Metody pro uložení a načtení ze souboru
    # asdict() převede @dataclass rekurzivně na dict – vhodné pro JSON
    def do_dict(self) -> dict:
        d = asdict(self)
        d["max_hp"] = self.max_hp  # přidáme vypočítaný atribut
        return d

    @classmethod
    def from_dict(cls, d: dict) -> "Hrac":
        # Odstraníme max_hp – __post_init__ ho znovu vypočítá
        d_bez_max = {k: v for k, v in d.items() if k != "max_hp"}
        return cls(**d_bez_max)


print("=== Hrac do_dict / from_dict ===")
h = Hrac("Míša", hp=90, inventar=["meč", "štít"])
h.hp = 70  # hráč byl zraněn

data = h.do_dict()
print(f"Uloženo: {json.dumps(data, ensure_ascii=False)}")

obnoveny = Hrac.from_dict(data)
print(f"Obnoveno: {obnoveny}")
print(f"  max_hp: {obnoveny.max_hp}, hp: {obnoveny.hp}")


# ── 2. Zbozi s nejdrazsi() ───────────────────────────────────────────────────

@dataclass
class Zbozi:
    nazev: str
    cena: float
    ks: int  # počet kusů na skladě

    @property
    def celkova_hodnota(self) -> float:
        return self.cena * self.ks


def nejdrazsi(seznam_zbozi: list[Zbozi]) -> Zbozi:
    """Vrátí nejdražší položku podle jednotkové ceny."""
    return max(seznam_zbozi, key=lambda z: z.cena)


print("\n=== Zbozi – nejdrazsi() ===")
sklad = [
    Zbozi("Jablko",      5.90,  100),
    Zbozi("Čokoláda",   29.90,   50),
    Zbozi("Notebook", 1599.00,    5),
    Zbozi("Pero",        3.50,  200),
]

for z in sklad:
    print(f"  {z.nazev:<15} {z.cena:>8.2f} Kč  × {z.ks} ks"
          f"  (hodnota skladu: {z.celkova_hodnota:.0f} Kč)")

nej = nejdrazsi(sklad)
print(f"\nNejdražší: {nej.nazev} za {nej.cena} Kč")


# ── 3. GeoPoint s vzdalenost() (Haversine formula) ──────────────────────────

@dataclass(frozen=True)
class GeoPoint:
    lat: float   # zeměpisná šířka
    lon: float   # zeměpisná délka

    def vzdalenost(self, other: "GeoPoint") -> float:
        """
        Haversine formula – vzdálenost dvou bodů na sféře.
        Vrátí vzdálenost v kilometrech.
        Poloměr Země: 6371 km.
        """
        R = 6371.0
        lat1, lon1 = math.radians(self.lat), math.radians(self.lon)
        lat2, lon2 = math.radians(other.lat), math.radians(other.lon)

        dlat = lat2 - lat1
        dlon = lon2 - lon1

        a = (math.sin(dlat / 2) ** 2
             + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        return R * c

    def __str__(self):
        return f"GeoPoint({self.lat:.4f}°N, {self.lon:.4f}°E)"


print("\n=== GeoPoint – Haversine vzdálenost ===")
praha = GeoPoint(50.0755, 14.4378)
brno = GeoPoint(49.1951, 16.6068)
new_york = GeoPoint(40.7128, -74.0060)

print(f"{praha} → {brno}")
print(f"  Vzdálenost Praha–Brno: {praha.vzdalenost(brno):.1f} km")
print(f"  (Skutečná vzdálenost silnicí: ~210 km, vzdušnou čarou: ~190 km)")

print(f"\n{praha} → New York")
print(f"  Vzdálenost Praha–New York: {praha.vzdalenost(new_york):.0f} km")
