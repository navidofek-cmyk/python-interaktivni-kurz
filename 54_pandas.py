"""
LEKCE 54: Pandas – datová analýza
===================================
pip install pandas

Pandas = práce s tabulkovými daty v Pythonu.
DataFrame = tabulka (jako Excel, ale v kódu).
Series = jeden sloupec.

Kde pandas září:
  - Čtení CSV, Excel, JSON, SQL
  - Filtrování, řazení, agregace
  - Pivot tabulky, groupby
  - Čistění dat (chybějící hodnoty, duplikáty)
  - Časové řady
"""

try:
    import pandas as pd
    import numpy as np
    PANDAS_OK = True
except ImportError:
    print("Pandas není nainstalováno: pip install pandas numpy")
    PANDAS_OK = False

import io
from pathlib import Path

if not PANDAS_OK:
    exit()

# ══════════════════════════════════════════════════════════════
# ČÁST 1: VYTVÁŘENÍ DATAFRAME
# ══════════════════════════════════════════════════════════════

print("=== Vytváření DataFrame ===\n")

# Ze slovníku
df = pd.DataFrame({
    "jmeno":    ["Míša", "Tomáš", "Bára", "Ondra", "Klára", "Petr"],
    "vek":      [15, 16, 14, 17, 15, 16],
    "body":     [87.5, 92.0, 78.3, 95.1, 65.0, 88.7],
    "predmet":  ["mat", "fyz", "mat", "inf", "bio", "fyz"],
    "aktivni":  [True, True, False, True, True, False],
})

print(df)
print(f"\nshape: {df.shape}  (řádky × sloupce)")
print(f"dtypes:\n{df.dtypes}")
print(f"\ndf.describe():\n{df.describe().round(2)}")


# ══════════════════════════════════════════════════════════════
# ČÁST 2: VÝBĚR A FILTROVÁNÍ
# ══════════════════════════════════════════════════════════════

print("\n=== Výběr a filtrování ===\n")

# Výběr sloupce
print("Sloupec 'jmeno':")
print(f"  {df['jmeno'].tolist()}")

# Výběr více sloupců
print(f"\nVýběr sloupců jmeno+body:\n{df[['jmeno', 'body']]}")

# Filtrování řádků
aktivni = df[df["aktivni"] == True]
print(f"\nAktivní studenti ({len(aktivni)}):")
print(aktivni[["jmeno", "body"]])

# Složená podmínka
dobre_body = df[(df["body"] >= 85) & (df["vek"] <= 16)]
print(f"\n85+ bodů a věk ≤16:\n{dobre_body[['jmeno', 'vek', 'body']]}")

# .query() – čitelnější syntax
print(f"\nquery('body > 80 and aktivni'):")
print(df.query("body > 80 and aktivni")[["jmeno", "body"]])


# ══════════════════════════════════════════════════════════════
# ČÁST 3: AGREGACE A GROUPBY
# ══════════════════════════════════════════════════════════════

print("\n=== GroupBy a agregace ===\n")

# Průměr bodů podle předmětu
print("Průměr bodů podle předmětu:")
print(df.groupby("predmet")["body"].mean().round(1))

# Více agregací najednou
print("\nStatistiky podle předmětu:")
print(df.groupby("predmet")["body"].agg(["mean", "min", "max", "count"]).round(1))

# Pivot tabulka
df2 = pd.DataFrame({
    "student": ["Míša"]*3 + ["Tomáš"]*3,
    "mesic":   ["Led","Uno","Bře"]*2,
    "body":    [80, 85, 90, 70, 75, 88],
})
pivot = df2.pivot_table(values="body", index="student", columns="mesic", aggfunc="mean")
print(f"\nPivot tabulka:\n{pivot}")


# ══════════════════════════════════════════════════════════════
# ČÁST 4: ČTENÍ A ZÁPIS DAT
# ══════════════════════════════════════════════════════════════

print("\n=== Čtení a zápis ===\n")

# CSV
csv_data = """jmeno,zeme,hdp_miliard,populace_mil
USA,Amerika,25462,335
Čína,Asie,17963,1412
Německo,Evropa,4072,84
Francie,Evropa,2778,68
Japonsko,Asie,4232,125
Česko,Evropa,290,11
"""

df_zeme = pd.read_csv(io.StringIO(csv_data))
print("Přečteno z CSV:")
print(df_zeme)

# Přidej vypočítaný sloupec
df_zeme["hdp_na_osobu_tis"] = (df_zeme["hdp_miliard"] / df_zeme["populace_mil"]).round(1)
print(f"\nHDP na osobu (tis. USD):")
print(df_zeme[["jmeno","hdp_na_osobu_tis"]].sort_values("hdp_na_osobu_tis", ascending=False))

# Ulož zpět do CSV
df_zeme.to_csv("zeme.csv", index=False, encoding="utf-8")
print(f"\nUloženo do zeme.csv")

# JSON
df.to_json("studenti.json", orient="records", force_ascii=False, indent=2)
df_nacti = pd.read_json("studenti.json")
print(f"JSON round-trip: {df_nacti.shape} = původní {df.shape} ✓")

for f in ["zeme.csv", "studenti.json"]:
    Path(f).unlink(missing_ok=True)


# ══════════════════════════════════════════════════════════════
# ČÁST 5: ČISTĚNÍ DAT
# ══════════════════════════════════════════════════════════════

print("\n=== Čistění dat ===\n")

df_spatny = pd.DataFrame({
    "jmeno":  ["Míša", None, "Bára", "Míša", "  Ondra  ", ""],
    "body":   [87, None, 78, 87, 95, 0],
    "email":  ["m@m.cz", "t@t.cz", "BARA@B.CZ", "m@m.cz", None, "x"],
})
print("Surová data:")
print(df_spatny)

# Chybějící hodnoty
print(f"\nChybějící hodnoty:\n{df_spatny.isnull().sum()}")

# Opravy
df_ciste = (
    df_spatny
    .dropna(subset=["jmeno"])               # smaž řádky bez jména
    .assign(
        jmeno=lambda x: x["jmeno"].str.strip(),  # ořeže mezery
        email=lambda x: x["email"].str.lower(),   # malá písmena
    )
    .loc[lambda x: x["jmeno"] != ""]        # odstraň prázdné jmena
    .drop_duplicates(subset=["jmeno"])       # smaž duplikáty
    .fillna({"body": 0, "email": "unknown@unknown.cz"})
    .reset_index(drop=True)
)

print("\nPo čistění:")
print(df_ciste)


# ══════════════════════════════════════════════════════════════
# ČÁST 6: ČASOVÉ ŘADY
# ══════════════════════════════════════════════════════════════

print("\n=== Časové řady ===\n")

datum_range = pd.date_range("2024-01-01", periods=30, freq="D")
np.random.seed(42)
ceny = pd.Series(
    100 + np.cumsum(np.random.randn(30) * 2),
    index=datum_range,
    name="cena"
)

print(f"Ceny (prvních 5):\n{ceny.head()}")
print(f"\nPo měsících (průměr):\n{ceny.resample('W').mean().round(2)}")

# Klouzavý průměr
klouzavy = ceny.rolling(window=7).mean()
print(f"\n7denní klouzavý průměr (posledních 5):\n{klouzavy.tail().round(2)}")

# Vizualizace v textu (mini sparkline)
print("\nSparkline:")
norm = (ceny - ceny.min()) / (ceny.max() - ceny.min())
znaky = "▁▂▃▄▅▆▇█"
print("  " + "".join(znaky[int(v * 7)] for v in norm))

# TVOJE ÚLOHA:
# 1. Stáhni CSV z Eurostatu nebo data.gov.cz a analyzuj ho.
# 2. Napiš funkci top_n(df, sloupec, n) která vrátí n nejlepších řádků.
# 3. Spočítej korelační matici číselných sloupců (df.corr()).
# 4. Vytvoř pivot tabulku bodů studentů podle měsíce a předmětu.
