# Data

## Source datasets (download into `data/raw/`)

| Code | Dataset | Link | Expected file(s) |
|---|---|---|---|
| a | Kaggle Phishing Site URLs | https://www.kaggle.com/datasets/taruntiwarihp/phishing-site-urls | `raw/kaggle/phishing_site_urls.csv` |
| b | PhiUSIIL Phishing URL Dataset | https://archive.ics.uci.edu/dataset/967/phiusiil+phishing+url+dataset | `raw/phiusiil/PhiUSIIL_Phishing_URL_Dataset.csv` |
| c | Dataset of Malicious and Benign Webpages (Mendeley) | https://data.mendeley.com/datasets/gdx3pkwp47/2 | `raw/mendeley/Webpages_Classification_train_data.csv`, `raw/mendeley/Webpages_Classification_test_data.csv` |
| d | StealthPhisher | https://doi.org/10.17632/m2479kmybx.1 | `raw/stealthphisher/StealthPhisher.csv` |

Only the URL and label columns are used. PhiUSIIL labels legitimate URLs as 1, so its labels are inverted (`01_merge_sources.py`).

Other paths can be passed as arguments; run any script with `--help`.

## Files produced by the pipeline (`data/processed/`, not tracked by git)

| File | Content |
|---|---|
| `phishing_merged_abcd.csv` | four sources after stage 1 (URL, Label, Source) |
| `phishing_merged_abcd_dedup.csv` | cleaned corpus after stages 2-3, with the 14 descriptors |
| `removed_rows_audit.csv`, `removed_duplicates_audit.csv` | every row removed in stages 2 and 3 |
| `phishing_abc_resampled_split.csv` | undersampled, split and oversampled in-distribution data |
| `resampling_summary.csv` | oversampling method and counts per source |
| `splits/{train,val,test,ood}.csv` | training, validation, test and OOD sets |

No dataset files are included in this repository. The source datasets are distributed under their own terms; download them from the links above.
