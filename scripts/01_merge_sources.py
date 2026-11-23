"""Step 1: harmonize the four public datasets and apply stage-1 cleaning (Section 3.1-3.2).

Output: <out>/phishing_merged_abcd.csv with columns URL, Label, Source
  Label: 0 = legitimate, 1 = phishing
  Source: a = Kaggle, b = PhiUSIIL, c = Mendeley, d = StealthPhisher

Stage 1 (sources a-c only): drop blank rows, drop every copy of an exact URL
string that occurs with both labels, then drop exact duplicates keeping the
first occurrence in the order Kaggle, PhiUSIIL, Mendeley. StealthPhisher is
only stripped of exact duplicates of itself.
"""
import argparse
from pathlib import Path

import pandas as pd

ap = argparse.ArgumentParser()
ap.add_argument("--kaggle", default="data/raw/kaggle/phishing_site_urls.csv")
ap.add_argument("--phiusiil", default="data/raw/phiusiil/PhiUSIIL_Phishing_URL_Dataset.csv")
ap.add_argument("--mendeley-dir", default="data/raw/mendeley",
                help="folder with Webpages_Classification_train_data.csv and Webpages_Classification_test_data.csv")
ap.add_argument("--stealthphisher", default="data/raw/stealthphisher/StealthPhisher.csv")
ap.add_argument("--out", default="data/processed")
a = ap.parse_args()
out = Path(a.out); out.mkdir(parents=True, exist_ok=True)

parts = []


def add(df, src):
    df = df.rename(columns={df.columns[0]: "URL", df.columns[1]: "Label"})[["URL", "Label"]].copy()
    df["Source"] = src
    print(f"{src:15s} raw rows {len(df):>9,}")
    parts.append(df)


k = pd.read_csv(a.kaggle)
k["Label"] = k.Label.str.strip().str.lower().map({"good": 0, "bad": 1})
add(k, "Kaggle")

p = pd.read_csv(a.phiusiil, usecols=["URL", "label"], encoding="utf-8-sig")
p["label"] = 1 - p["label"]          # PhiUSIIL encodes legitimate as 1 -> invert
add(p, "PhiUSIIL")

md = Path(a.mendeley_dir)
m = pd.concat([pd.read_csv(md / f, usecols=["url", "label"])
               for f in ["Webpages_Classification_train_data.csv", "Webpages_Classification_test_data.csv"]])
m["label"] = m.label.str.strip().str.lower().map({"good": 0, "bad": 1})
add(m, "Mendeley")

st = pd.read_csv(a.stealthphisher, usecols=["URL", "Label"])
st["Label"] = st.Label.str.strip().str.lower().map({"legitimate": 0, "phishing": 1})
add(st, "StealthPhisher")

# ---- stage 1 on the in-distribution sources (a-c) ----
ind = pd.concat(parts[:3], ignore_index=True)
ind = ind.dropna(); ind["Label"] = ind.Label.astype(int); ind["URL"] = ind.URL.astype(str).str.strip()
ind = ind[ind.URL != ""]
nl = ind.groupby("URL").Label.nunique(); conf = set(nl[nl > 1].index)
ind = ind[~ind.URL.isin(conf)]                       # exact-string label conflicts: drop every copy
ind = ind.drop_duplicates("URL", keep="first")       # source order: Kaggle, PhiUSIIL, Mendeley
ood = st.dropna().copy(); ood["URL"] = ood.URL.astype(str).str.strip(); ood["Label"] = ood.Label.astype(int)
ood = ood.drop_duplicates("URL")
print("exact-string label conflicts:", len(conf))

ind = ind.sample(frac=1, random_state=42, ignore_index=True)   # shuffle within the pool (fixed seed)
ood = ood.assign(Source="StealthPhisher")[["URL", "Label", "Source"]]

code = {"Kaggle": "a", "PhiUSIIL": "b", "Mendeley": "c", "StealthPhisher": "d"}
df = pd.concat([ind, ood], ignore_index=True)
df["Source"] = df.Source.map(code)
df = df.sort_values("Source", kind="stable", ignore_index=True)
assert df.Source.notna().all() and set(df.Label.unique()) == {0, 1}
df.to_csv(out / "phishing_merged_abcd.csv", index=False, encoding="utf-8")
print("after stage 1:", len(df)); print(pd.crosstab(df.Source, df.Label, margins=True))
