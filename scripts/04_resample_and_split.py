"""Step 4: per-source undersampling, 70/15/15 split and training-only oversampling (Sections 3.4-3.5).

StealthPhisher (source d) is never touched here; it is the OOD test set.

1. Per source a-c, legitimate URLs are undersampled at random to at most
   1.2 per phishing URL; every phishing URL is kept.
2. 70/15/15 split stratified jointly by label x source, seed 42.
3. In the training set only, phishing rows are oversampled per source toward
   1:1 (cap 3x the original phishing count, K = 5) in the standardized
   descriptor space: ADASYN first, then Borderline-SMOTE, SMOTE, random
   oversampling if a sampler fails. A synthetic row takes the URL of its
   nearest real phishing neighbor from the same source (Fig. 5 of the paper).

Outputs: phishing_abc_resampled_split.csv (column Split = train/val/test,
Synthetic = 0/1) and resampling_summary.csv.
"""
import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from imblearn.over_sampling import ADASYN, SMOTE, BorderlineSMOTE, RandomOverSampler
from sklearn.model_selection import train_test_split
from sklearn.neighbors import NearestNeighbors
from sklearn.preprocessing import StandardScaler

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from charlex.descriptors import FEATURE_NAMES as FEATS  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--data", default="data/processed")
a = ap.parse_args()
D = Path(a.data)

SEED = 42; K = 5; CAP = 3.0; SKIP = 0.90; RATIO = 1.2

full = pd.read_csv(D / "phishing_merged_abcd_dedup.csv", keep_default_na=False)
df = full[full.Source.isin(["a", "b", "c"])].copy()
print("a/b/c input", len(df)); print(pd.crosstab(df.Source, df.Label))

# 1. per-source undersampling
parts = []
for s, g in df.groupby("Source"):
    gp = g[g.Label == 1]; gl = g[g.Label == 0]; n = int(len(gp) * RATIO)
    if len(gl) > n > 0:
        gl = gl.sample(n=n, random_state=SEED)
    parts.append(pd.concat([gl, gp]))
u = pd.concat(parts).sample(frac=1, random_state=SEED).reset_index(drop=True)
print("after undersampling", len(u)); print(pd.crosstab(u.Source, u.Label))

# 2. split
key = u.Label.astype(str) + "_" + u.Source
tr, tmp = train_test_split(u, test_size=0.30, stratify=key, random_state=SEED)
va, te = train_test_split(tmp, test_size=0.50, stratify=key.loc[tmp.index], random_state=SEED)
print("split", len(tr), len(va), len(te))

# 3. oversampling, training set only
scaler = StandardScaler(); Xn = scaler.fit_transform(tr[FEATS].values.astype(np.float32))
y = tr.Label.values; src = tr.Source.values; urls = tr.URL.values


def fallback(X, yy, strat):
    for name, sm in [("ADASYN", ADASYN(sampling_strategy=strat, n_neighbors=K, random_state=SEED)),
                     ("Borderline-SMOTE", BorderlineSMOTE(sampling_strategy=strat, k_neighbors=K, random_state=SEED)),
                     ("SMOTE", SMOTE(sampling_strategy=strat, k_neighbors=K, random_state=SEED)),
                     ("RandomOverSampler", RandomOverSampler(sampling_strategy=strat, random_state=SEED))]:
        try:
            Xr, yr = sm.fit_resample(X, yy)
            if len(yr) > len(yy):
                return Xr, yr, name
        except Exception as e:  # noqa: BLE001
            print("   ", name, "failed", str(e)[:80])
    return X, yy, "none"


syn = []; report = []
for s in sorted(np.unique(src)):
    idx = np.where(src == s)[0]; Xs, ys = Xn[idx], y[idx]; us = urls[idx]
    nl, npos = int((ys == 0).sum()), int((ys == 1).sum())
    if npos / nl >= SKIP or npos > nl:
        print(s, "skipped, phish/legit=%.2f" % (npos / nl)); report.append((s, npos, nl, 0, "skipped")); continue
    target = int(min(nl, CAP * npos)); Xr, yr, method = fallback(Xs, ys, min(1.0, target / nl))
    sf = Xr[len(ys):]; nsyn = len(yr) - len(ys)
    pl = np.where(ys == 1)[0]
    nn = NearestNeighbors(n_neighbors=1, n_jobs=-1).fit(Xs[pl]); _, near = nn.kneighbors(sf)
    raw = np.clip(scaler.inverse_transform(sf), 0, None)
    d = pd.DataFrame(raw, columns=FEATS)
    d.insert(0, "URL", us[pl[near.ravel()]]); d.insert(1, "Label", 1); d.insert(2, "Source", s)
    syn.append(d); report.append((s, npos, nl, nsyn, method))
    print(s, method, "+%d synthetic" % nsyn, "(%d distinct real URLs reused)" % d.URL.nunique())

sy = pd.concat(syn, ignore_index=True)
tr = tr.assign(Synthetic=0); sy["Synthetic"] = 1
train = pd.concat([tr, sy], ignore_index=True).sample(frac=1, random_state=SEED).reset_index(drop=True)
out = pd.concat([train.assign(Split="train"), va.assign(Synthetic=0, Split="val"),
                 te.assign(Synthetic=0, Split="test")], ignore_index=True)
out = out[["URL", "Label", "Source"] + FEATS + ["Split", "Synthetic"]]
for c in ["URL Length", "Dot Count", "Hyphen Count", "At Symbol", "Digit Count", "Question Mark", "Equals Count",
          "Ampersand Count", "IP Presence", "Suspicious Word Count", "Brand Hit Count"]:
    out[c] = out[c].astype(float)
    m = out.Synthetic == 0
    out[c] = out[c].where(~m, out[c].round())
out.to_csv(D / "phishing_abc_resampled_split.csv", index=False, encoding="utf-8")
print("written", len(out)); print(pd.crosstab([out.Split, out.Source], out.Label)); print(pd.crosstab(out.Split, out.Synthetic))
pd.DataFrame(report, columns=["Source", "TrainPhishBefore", "TrainLegit", "Synthetic", "Method"]).to_csv(
    D / "resampling_summary.csv", index=False)
