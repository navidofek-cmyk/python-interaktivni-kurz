"""Reseni – Lekce 54: Pandas"""

try:
    import pandas as pd
    import numpy as np
    PANDAS_OK = True
except ImportError:
    print("Pandas neni nainstalovano: pip install pandas numpy")
    PANDAS_OK = False

if not PANDAS_OK:
    exit()

import io
from pathlib import Path

# Demo data
df = pd.DataFrame({
    "jmeno":   ["Misa", "Tomas", "Bara", "Ondra", "Klara", "Petr",
                 "Jana", "Pavel", "Lucie", "Adam"],
    "vek":     [15, 16, 14, 17, 15, 16, 14, 17, 15, 16],
    "body":    [87.5, 92.0, 78.3, 95.1, 65.0, 88.7, 71.2, 90.5, 82.1, 76.4],
    "predmet": ["mat", "fyz", "mat", "inf", "bio", "fyz",
                "mat", "inf", "bio", "fyz"],
    "aktivni": [True, True, False, True, True, False,
                True, True, False, True],
    "mesic":   [1, 1, 2, 2, 1, 3, 3, 2, 1, 3],
})


# 1. Funkce top_n(df, sloupec, n) → n nejlepsich radku

print("=== Ukol 1: top_n() funkce ===\n")


def top_n(data: pd.DataFrame, sloupec: str, n: int = 5) -> pd.DataFrame:
    """Vrati n radku s nejvyssimi hodnotami ve sloupci."""
    return data.nlargest(n, sloupec).reset_index(drop=True)


print("Top 3 studenti dle bodu:")
top = top_n(df, "body", 3)
print(top[["jmeno", "body", "predmet"]])

print("\nTop 4 studenti dle veku:")
top_vek = top_n(df, "vek", 4)
print(top_vek[["jmeno", "vek"]])


# 2. Korelacni matice ciselnych sloupcu

print("\n=== Ukol 2: Korelacni matice ===\n")

num_df = df[["vek", "body", "mesic"]].copy()
korelace = num_df.corr().round(3)

print("Korelacni matice:")
print(korelace)
print(f"\nNejsilnejsi korelace (abs):")
# Horni trojuhelnik bez diagonaly
for i in range(len(korelace)):
    for j in range(i+1, len(korelace)):
        r = korelace.iloc[i, j]
        s1 = korelace.columns[i]
        s2 = korelace.columns[j]
        print(f"  {s1} ↔ {s2}: r={r:+.3f}")


# 3. Pivot tabulka bodu dle mesice a predmetu

print("\n=== Ukol 3: Pivot tabulka ===\n")

pivot = df.pivot_table(
    values="body",
    index="mesic",
    columns="predmet",
    aggfunc="mean",
).round(1)

print("Prumerne body dle mesice (radky) a predmetu (sloupce):")
print(pivot.to_string())

# S fill_value pro chybejici kombinace
pivot_filled = df.pivot_table(
    values="body",
    index="mesic",
    columns="predmet",
    aggfunc=["mean", "count"],
    fill_value=0,
).round(1)
print("\nPocet studentu v kazde kombinaci:")
print(pivot_filled["count"].to_string())


# Bonus: Analyza dat (simulace Eurostatu)

print("\n=== Bonus: Analyza dat (simulace) ===\n")

CSV_DATA = """rok,zeme,hdp_mld,nezamestnanost_pct
2020,CZ,226.2,2.6
2021,CZ,246.6,2.8
2022,CZ,282.0,2.3
2023,CZ,295.1,2.6
2020,SK,96.8,6.7
2021,SK,105.8,6.9
2022,SK,119.7,5.8
2023,SK,124.2,5.2
2020,PL,595.9,3.2
2021,PL,679.4,3.4
2022,PL,757.5,2.9
2023,PL,811.2,2.8
"""

ekonomika = pd.read_csv(io.StringIO(CSV_DATA))

print("Nactena data:")
print(ekonomika)

print("\nPrumerny rust HDP (%/rok) dle zeme:")
for zeme, skupina in ekonomika.groupby("zeme"):
    rust = skupina["hdp_mld"].pct_change().mean() * 100
    print(f"  {zeme}: {rust:.1f}% rocne")

print("\nNejnizsi nezamestnanost v datasetu:")
nejlepsi = ekonomika.loc[ekonomika["nezamestnanost_pct"].idxmin()]
print(f"  {nejlepsi['zeme']} v roce {nejlepsi['rok']}: {nejlepsi['nezamestnanost_pct']}%")
