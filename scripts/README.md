# Dataset Acquisition Scripts

Reproducible acquisition pipeline for the human-writing sources selected
in [DEC-009](../docs/decisions/DEC-009-human-dataset-source.md): PERSUADE
2.0 and the ELLIPSE Corpus. See
[docs/dataset-source-comparison.md](../docs/dataset-source-comparison.md)
for why these two and not others.

## What this does, and doesn't, do

`acquire_dataset.py` **verifies the live Kaggle license metadata against
what DEC-009 recorded before downloading anything**, and refuses to
proceed (raising `LicenseVerificationError`) if the dataset can't be
found or its license doesn't match. This isn't a formality — DEC-009
found a real discrepancy between two sources describing PERSUADE's
license differently, and this check is how that gets caught again if it
recurs, instead of trusting research notes forever.

It does not yet clean, deduplicate, or split the data — those are
separate, not-yet-written scripts, to be added once acquisition itself is
confirmed working end-to-end.

## Setup

1. Create a Kaggle account if you don't have one:
   https://www.kaggle.com/account/login
2. Generate an API token: https://www.kaggle.com/settings/api →
   "Create New Token" → downloads `kaggle.json`.
3. Place it at `~/.kaggle/kaggle.json` (or set the `KAGGLE_USERNAME` /
   `KAGGLE_KEY` environment variables instead).
4. From the `backend/` virtualenv (these scripts currently share it
   rather than getting a second one — see `backend/requirements.txt`):
   ```bash
   source ../backend/.venv/bin/activate
   python acquire_dataset.py --source persuade_2.0
   # or: --source ellipse_corpus / --source all (default)
   ```

Downloaded files land in `data/raw/<source_name>/` (gitignored — see the
repository root `.gitignore`), alongside an `ACQUISITION_MANIFEST.json`
recording the exact Kaggle ref and verified license string for
reproducibility.

## Testing

```bash
source ../backend/.venv/bin/activate
cd scripts && python -m pytest
```

These tests use a fake Kaggle API object and need no credentials — they
test this pipeline's own refuse-on-mismatch logic, not Kaggle's service.

## Known open item

The Kaggle dataset refs in `dataset_sources.py` were found via web
research, not independently confirmed by an actual authenticated API
call yet (no credentials were available in the environment this was
built in). The first real run of this script **is** that confirmation —
if a ref is wrong or stale, it will fail loudly (`LicenseVerificationError`
listing "Could not find..."), not silently download the wrong thing.
