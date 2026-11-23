"""Step 2: normalized-key de-duplication across all four sources (stages 2 and 3, Section 3.2).

Normalized key: lower case, leading http:// or https:// removed, leading www.
removed, trailing slashes removed. The key is used only for matching; kept rows
keep their original URL string.

Stage 2: every row whose key occurs with both labels is dropped.
Stage 3: rows whose key already occurred are dropped, keeping the first
         occurrence in source order a, b, c, d.

Outputs:
  phishing_merged_abcd_dedup.csv  cleaned corpus (URL, Label, Source)
  removed_rows_audit.csv          stage-2 rows (label conflicts)
  removed_duplicates_audit.csv    stage-3 rows, with the source that kept the URL
"""
import argparse
from pathlib import Path

import pandas as pd

ap = argparse.ArgumentParser()
ap.add_argument("--data", default="data/processed")
a = ap.parse_args()
D = Path(a.data)

d = pd.read_csv(D / "phishing_merged_abcd.csv", keep_default_na=False)
print("start", len(d))
d["key"] = (d.URL.str.lower().str.replace(r"^https?://", "", regex=True)
            .str.replace(r"^www\.", "", regex=True).str.rstrip("/"))

nl = d.groupby("key").Label.nunique()
conf = nl[nl > 1].index
isconf = d.key.isin(conf)
conf_rows = d[isconf].copy()
rest = d[~isconf]

dupmask = rest.duplicated("key", keep="first")        # file is sorted a, b, c, d
dups = rest[dupmask].copy()
first = rest[~dupmask].set_index("key")
dups["kept_source"] = dups.key.map(first.Source)
clean = rest[~dupmask].drop(columns=["key"])

kept_url = first.URL
dups["exact"] = dups.URL == dups.key.map(kept_url)
print(f"stage 2: {len(conf)} conflicting keys, {len(conf_rows)} rows removed")
print(f"stage 3: {len(dups)} rows removed ({int(dups.exact.sum())} exact, {int((~dups.exact).sum())} normalized-only)")
print("stage 3, removed source (rows) x source that kept the URL (columns):")
print(pd.crosstab(dups.Source, dups.kept_source, margins=True))
print("cleaned corpus:"); print(pd.crosstab(clean.Source, clean.Label, margins=True))

clean.to_csv(D / "phishing_merged_abcd_dedup.csv", index=False, encoding="utf-8")
conf_rows.assign(reason="conflicting_label")[["URL", "Label", "Source", "reason"]].to_csv(
    D / "removed_rows_audit.csv", index=False)
dups.assign(reason="duplicate")[["URL", "Label", "Source", "kept_source", "reason"]].to_csv(
    D / "removed_duplicates_audit.csv", index=False)
