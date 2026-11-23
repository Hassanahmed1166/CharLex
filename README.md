# CharLex: Phishing URL Detection Across Multiple Datasets

Data-preparation code for the paper

> **Phishing URL Detection Across Multiple Datasets Using Character-Level and Lexical Features**
> H. Ahmed, A. Fatima, A. Khan, S. Saremi, R. Shibl, M. Mirzaei (under review).

CharLex is a URL-only phishing detector with two input streams:
- **Stream I:** a character-level encoder (multi-scale CNN, BiLSTM and additive attention pooling).
- **Stream II:** fourteen lexical descriptors of the URL string.

The model is trained on three public datasets that were merged and de-duplicated. A fourth dataset (StealthPhisher) is held out as an out-of-distribution (OOD) test set.

This repository contains the scripts that rebuild the merged, de-duplicated and split corpus from the public source datasets, and the exact code of the fourteen descriptors. **No dataset files are included.** The source datasets are distributed under their own terms; download them from the links in [`data/README.md`](data/README.md).

## Repository layout

```
src/charlex/descriptors.py        the 14 Stream II descriptors (exact definitions used in the paper)
scripts/01_merge_sources.py       harmonize the four datasets; stage-1 cleaning
scripts/02_deduplicate.py         normalized-key de-duplication (stages 2-3) + audit files
scripts/03_compute_descriptors.py add the 14 descriptors
scripts/04_resample_and_split.py  per-source undersampling, 70/15/15 split, train-only oversampling
scripts/05_export_splits.py       write splits/{train,val,test,ood}.csv
scripts/run_pipeline.sh           steps 1-5 in order
data/README.md                    download links and expected file names
```

## Reproducing the data pipeline

```bash
pip install -r requirements.txt
# download the four datasets into data/raw/ (see data/README.md)
bash scripts/run_pipeline.sh          # writes data/processed/ and data/processed/splits/
```

The pipeline is deterministic (seed 42). Run on the raw files, it reproduces the following counts from the paper:

| Step | Rows |
|---|---|
| Merged raw | 2,683,824 |
| After stage 1 (exact duplicates, exact label conflicts, blanks) | 2,593,374 |
| After stage 2 (normalized label conflicts) | 2,592,698 |
| After stage 3 (normalized duplicates) | 2,365,980 |
| Undersampled in-distribution pool | 528,307 |
| Train / validation / test | 396,825 (27,011 synthetic) / 79,246 / 79,247 |
| OOD (StealthPhisher) | 195,633 |

We checked this by running the pipeline from the raw downloads. It reproduces every URL, label, source, split assignment and synthetic row exactly. The Shannon-entropy descriptor can differ in the last floating-point digit (below 1e-14), because Python's set iteration order changes the order of summation.

The pipeline also writes the cleaning audit files (`removed_rows_audit.csv`, `removed_duplicates_audit.csv`), which list every removed row with the stage and reason for its removal.

The labels are 0 = legitimate and 1 = phishing. The source codes are `a` Kaggle, `b` PhiUSIIL, `c` Mendeley, `d` StealthPhisher.

## Known issues (documented in the paper)

- **Descriptor 13 (maximum brand similarity)** uses `difflib`'s `quick_ratio` on the whole URL. It ignores character order and mostly tracks URL length.
- **Descriptors 12 and 14** both count `paypal` and `ebay`.
- **Synthetic training rows** pair interpolated descriptor values with the URL of a real neighbor.

The definitions are kept unchanged so that the published numbers can be reproduced.

## Citation

See [`CITATION.cff`](CITATION.cff). Please also cite the four source datasets (links in `data/README.md`).

## License

Code: MIT (see [`LICENSE`](LICENSE)).
