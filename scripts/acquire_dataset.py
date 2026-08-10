"""
Reproducible acquisition pipeline for the human-writing dataset sources
selected in DEC-009 (docs/decisions/DEC-009-human-dataset-source.md).

Usage:
    python acquire_dataset.py [--source persuade_2.0|ellipse_corpus|all]

Requires Kaggle API credentials (~/.kaggle/kaggle.json or the
KAGGLE_USERNAME/KAGGLE_KEY environment variables). This script refuses to
download anything whose live Kaggle license metadata doesn't match what
DEC-009 recorded -- per the project's explicit requirement to never
download or commit a dataset whose licensing/provenance has not been
established. It does not silently proceed on a mismatch or a missing
dataset; it raises and stops.
"""

import argparse
import json
from pathlib import Path

from dataset_sources import ALL_SOURCES, DatasetSource

DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "raw"


class LicenseVerificationError(RuntimeError):
    """Raised when a source's live license doesn't match DEC-009, or the
    dataset can't be found at all. Acquisition must stop, not proceed."""


def get_kaggle_api():
    """Imported lazily so this module -- and the license-check logic in
    particular -- can be unit tested without the `kaggle` package needing
    valid credentials at import time (KaggleApi() reads credentials on
    construction/authenticate())."""
    from kaggle.api.kaggle_api_extended import KaggleApi

    api = KaggleApi()
    api.authenticate()
    return api


def verify_license(api, source: DatasetSource) -> str:
    """Fetch live Kaggle metadata for `source` and assert its license
    matches one of `source.expected_licenses` (DEC-009). Returns the
    actual license string found, so callers can record it."""
    search_term = source.kaggle_ref.split("/")[-1]
    matches = api.dataset_list(search=search_term)
    dataset = next((d for d in matches if d.ref == source.kaggle_ref), None)

    if dataset is None:
        raise LicenseVerificationError(
            f"Could not find Kaggle dataset '{source.kaggle_ref}'. The ref "
            f"recorded in scripts/dataset_sources.py (from research cited "
            f"in {source.decision_record}) may be stale or wrong -- update "
            f"it and the decision record before retrying. Refusing to "
            f"guess at an alternative ref."
        )

    actual_license = dataset.license_name
    if actual_license not in source.expected_licenses:
        raise LicenseVerificationError(
            f"Dataset '{source.kaggle_ref}' reports license "
            f"'{actual_license}', which is not one of "
            f"{source.expected_licenses} recorded in "
            f"{source.decision_record}. Refusing to download. If this "
            f"license is actually acceptable, update the decision record "
            f"first and explain why -- do not just widen the expected-"
            f"license list to make the check pass."
        )

    return actual_license


def acquire(source: DatasetSource, api=None) -> Path:
    """Verify the license, then download `source` into data/raw/<name>/.
    License verification always runs first; download is never attempted
    if it fails."""
    api = api or get_kaggle_api()
    actual_license = verify_license(api, source)

    dest = DATA_DIR / source.name
    dest.mkdir(parents=True, exist_ok=True)
    api.dataset_download_files(source.kaggle_ref, path=str(dest), unzip=True)

    manifest = {
        "source_name": source.name,
        "kaggle_ref": source.kaggle_ref,
        "verified_license": actual_license,
        "decision_record": source.decision_record,
    }
    (dest / "ACQUISITION_MANIFEST.json").write_text(json.dumps(manifest, indent=2))
    return dest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source",
        choices=[s.name for s in ALL_SOURCES] + ["all"],
        default="all",
        help="Which configured source to acquire (default: all)",
    )
    args = parser.parse_args()

    sources = (
        ALL_SOURCES if args.source == "all" else [s for s in ALL_SOURCES if s.name == args.source]
    )

    api = get_kaggle_api()
    for source in sources:
        print(f"Verifying license for {source.name} ({source.kaggle_ref})...")
        dest = acquire(source, api=api)
        print(f"  OK -- license verified, downloaded to {dest}")


if __name__ == "__main__":
    main()
