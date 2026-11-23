#!/usr/bin/env bash
# Run the full data pipeline (steps 1-5). Raw files are expected in data/raw/ (see data/README.md).
set -euo pipefail
cd "$(dirname "$0")/.."
python scripts/01_merge_sources.py
python scripts/02_deduplicate.py
python scripts/03_compute_descriptors.py
python scripts/04_resample_and_split.py
python scripts/05_export_splits.py
