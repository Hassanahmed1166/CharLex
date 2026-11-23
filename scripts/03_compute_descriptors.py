"""Step 3: add the fourteen Stream II descriptors to the cleaned corpus (Section 4.2).

Rewrites <data>/phishing_merged_abcd_dedup.csv with 14 extra columns.
"""
import argparse
import sys
from multiprocessing import Pool
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from charlex.descriptors import FEATURE_NAMES, FLOAT_FEATURES, extract_descriptors  # noqa: E402

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="data/processed")
    a = ap.parse_args()
    f_in = Path(a.data) / "phishing_merged_abcd_dedup.csv"
    d = pd.read_csv(f_in, keep_default_na=False)[["URL", "Label", "Source"]]
    with Pool() as p:
        rows = p.map(extract_descriptors, d.URL.tolist(), chunksize=20000)
    f = pd.DataFrame(rows, columns=FEATURE_NAMES)
    for c in FEATURE_NAMES:
        if c not in FLOAT_FEATURES:
            f[c] = f[c].astype(int)
    out = pd.concat([d, f], axis=1)
    assert len(out) == len(d)
    out.to_csv(f_in, index=False, encoding="utf-8")
    print("done", out.shape)
