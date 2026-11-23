"""Step 5: write the four split files used to train and evaluate the model.

<data>/splits/train.csv, val.csv, test.csv : rows of phishing_abc_resampled_split.csv
<data>/splits/ood.csv                      : StealthPhisher (source d) rows of the cleaned corpus
Columns: URL, the 14 descriptors, Label, Source.

The Synthetic flag is not written; a synthetic training row can be recognized
because its descriptors differ from those recomputed from its URL.
"""
import argparse
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from charlex.descriptors import FEATURE_NAMES as FEATS  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--data", default="data/processed")
a = ap.parse_args()
D = Path(a.data); S = D / "splits"; S.mkdir(parents=True, exist_ok=True)
cols = ["URL"] + FEATS + ["Label", "Source"]

r = pd.read_csv(D / "phishing_abc_resampled_split.csv", keep_default_na=False)
for sp in ["train", "val", "test"]:
    x = r[r.Split == sp][cols]
    x.to_csv(S / f"{sp}.csv", index=False, encoding="utf-8")
    print(sp, len(x))
c = pd.read_csv(D / "phishing_merged_abcd_dedup.csv", keep_default_na=False)
o = c[c.Source == "d"][cols]
o.to_csv(S / "ood.csv", index=False, encoding="utf-8")
print("ood", len(o))
