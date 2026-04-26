# Python pro děti – Interaktivní postup

Každá lekce je jeden soubor. Spusť ho, přečti, vyzkoušej, splň úlohy.

## Jak spustit lekci

```bash
python3 01_ahoj_svete.py
```

---

## Lekce

| # | Soubor | Co se naučíš | Obtížnost |
|---|--------|--------------|-----------|
| 1 | `01_ahoj_svete.py` | `print()` – Python mluví | ⭐ |
| 2 | `02_promenne.py` | Proměnné – škatulky na data | ⭐ |
| 3 | `03_vstup_uzivatele.py` | `input()` – Python se ptá | ⭐ |
| 4 | `04_pocitani.py` | Matematika a kalkulačka | ⭐⭐ |
| 5 | `05_podmínky.py` | `if/elif/else` – rozhodování | ⭐⭐ |
| 6 | `06_cykly.py` | `for` a `while` – opakování | ⭐⭐ |
| 7 | `07_seznamy.py` | Seznamy – více věcí najednou | ⭐⭐⭐ |
| 8 | `08_funkce.py` | Funkce – vlastní příkazy | ⭐⭐⭐ |
| 9 | `09_projekt_kviz.py` | **PROJEKT:** Kvíz se skóre | ⭐⭐⭐ |
| 10 | `10_projekt_had.py` | **PROJEKT:** Textová hra Had | ⭐⭐⭐⭐ |
| 11 | `11_text.py` | Kouzla s textem, palindromy | ⭐⭐ |
| 12 | `12_slovniky.py` | Slovníky – překladač češtiny | ⭐⭐⭐ |
| 13 | `13_soubory.py` | Soubory – deník na disku | ⭐⭐⭐ |
| 14 | `14_turtle_grafika.py` | Grafika – kreslení želvou | ⭐⭐ |
| 15 | `15_projekt_textova_hra.py` | **PROJEKT:** Dobrodružná hra | ⭐⭐⭐⭐ |
| 16 | `16_projekt_turtle_hra.py` | **PROJEKT:** Chytání hvězd | ⭐⭐⭐⭐⭐ |
| 17 | `17_veda_a_vesmír.py` | Věda: `math`, výpočet černé díry | ⭐⭐⭐ |
| 18 | `18_proc_nedam_ukoly.py` | Statistiky domácích úkolů | ⭐⭐⭐ |
| 19 | `19_pruzkum_lednicka.py` | Vědecký průzkum ledničky | ⭐⭐⭐ |
| 20 | `20_spanek_vs_realita.py` | Spánkový deficit, `datetime` | ⭐⭐⭐ |
| 21 | `21_kdo_snel_svacinu.py` | Detektivní hra – logika a důkazy | ⭐⭐⭐⭐ |
| 22 | `22_tridy_zaklad.py` | Třídy: `__init__`, metody, objekty | ⭐⭐⭐ |
| 23 | `23_dedicnost.py` | Dědičnost, `super()`, override, polymorfismus | ⭐⭐⭐⭐ |
| 24 | `24_magic_methods.py` | Magic methods: `__add__`, `__len__`, `__iter__`… | ⭐⭐⭐⭐ |
| 25 | `25_async.py` | Async/await, `gather`, timeout, async generátor | ⭐⭐⭐⭐⭐ |
| 26 | `26_dekoratory_kontexty.py` | Dekorátory `@`, context managery `with` | ⭐⭐⭐⭐⭐ |
| 27 | `27_generatory_iteratory.py` | `yield`, iterátory, `itertools` | ⭐⭐⭐⭐⭐ |
| 28 | `28_match_walrus.py` | `match/case` (structural), walrus `:=` | ⭐⭐⭐⭐ |
| 29 | `29_dataclasses.py` | `@dataclass`, `frozen`, `order`, serializace | ⭐⭐⭐⭐ |
| 30 | `30_exception_groups.py` | `ExceptionGroup`, `except*`, `add_note` (3.11+) | ⭐⭐⭐⭐⭐ |
| 31 | `31_slots_descriptory.py` | `__slots__`, data/non-data descriptory, `property` | ⭐⭐⭐⭐⭐ |
| 32 | `32_typing_protocol.py` | `Protocol`, `TypedDict`, `TypeVar`, `Generic`, `Literal` | ⭐⭐⭐⭐⭐ |
| 33 | `33_metaclasses.py` | Metaklasy, `__init_subclass__`, `ABCMeta`, Singleton | ⭐⭐⭐⭐⭐ |
| 34 | `34_generator_webu.py` | **PROJEKT:** Generátor statického webu z lekcí | ⭐⭐⭐⭐⭐ |

## Spuštění webu

```bash
python3 34_generator_webu.py
cd web && python3 -m http.server 8080
# Otevři: http://localhost:8080
```

---

## Jak na to

1. **Spusť soubor** a přečti výstup.
2. **Přečti kód** – koukej co dělají jednotlivé řádky.
3. **Splň úlohy** – jsou dole v každém souboru jako komentáře.
4. **Hraj si** – změň věci, zkus co se stane. Rozbít to nelze!

## Tipy

- Chyba je v pořádku! Chybová hláška ti říká, co opravit.
- `#` na začátku řádku = komentář, Python ho ignoruje.
- Pokud nevíš, co příkaz dělá, zkus ho v terminálu: `python3`
- Chceš vědět víc? `help(print)` napíše nápovědu přímo v Pythonu.
