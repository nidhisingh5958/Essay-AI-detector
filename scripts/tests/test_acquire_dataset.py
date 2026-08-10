"""
Tests for the license-verification safety gate in acquire_dataset.py.

These tests never touch the real Kaggle API or network -- they use a
fake API object, since the point being tested is the pipeline's own
logic ("refuse to download on a license mismatch or missing dataset"),
not Kaggle's service itself. No Kaggle credentials are required to run
these.
"""

from dataclasses import dataclass

import pytest

from acquire_dataset import LicenseVerificationError, acquire, verify_license
from dataset_sources import DatasetSource


@dataclass
class FakeKaggleDataset:
    ref: str
    license_name: str


class FakeKaggleApi:
    def __init__(self, datasets, fail_on_download=False):
        self._datasets = datasets
        self.downloaded = []
        self.fail_on_download = fail_on_download

    def dataset_list(self, search=None):
        return self._datasets

    def dataset_download_files(self, ref, path, unzip=True):
        if self.fail_on_download:
            raise AssertionError("dataset_download_files should not have been called")
        self.downloaded.append((ref, path, unzip))


SOURCE = DatasetSource(
    name="test_source",
    kaggle_ref="someowner/some-dataset",
    expected_licenses=("CC BY-NC-SA 4.0", "CC BY 4.0"),
    decision_record="docs/decisions/DEC-009-human-dataset-source.md",
    notes="test fixture",
)


def test_verify_license_passes_when_license_matches():
    api = FakeKaggleApi([FakeKaggleDataset(ref="someowner/some-dataset", license_name="CC BY 4.0")])
    result = verify_license(api, SOURCE)
    assert result == "CC BY 4.0"


def test_verify_license_raises_on_license_mismatch():
    api = FakeKaggleApi(
        [FakeKaggleDataset(ref="someowner/some-dataset", license_name="All Rights Reserved")]
    )
    with pytest.raises(LicenseVerificationError, match="All Rights Reserved"):
        verify_license(api, SOURCE)


def test_verify_license_raises_when_dataset_ref_not_found():
    api = FakeKaggleApi([FakeKaggleDataset(ref="someone/different-dataset", license_name="CC BY 4.0")])
    with pytest.raises(LicenseVerificationError, match="Could not find"):
        verify_license(api, SOURCE)


def test_acquire_does_not_download_when_license_mismatches(tmp_path, monkeypatch):
    import acquire_dataset

    monkeypatch.setattr(acquire_dataset, "DATA_DIR", tmp_path)

    api = FakeKaggleApi(
        [FakeKaggleDataset(ref="someowner/some-dataset", license_name="All Rights Reserved")],
        fail_on_download=True,
    )

    with pytest.raises(LicenseVerificationError):
        acquire(SOURCE, api=api)

    assert api.downloaded == []
    assert not (tmp_path / "test_source" / "ACQUISITION_MANIFEST.json").exists()


def test_acquire_downloads_and_writes_manifest_when_license_matches(tmp_path, monkeypatch):
    import acquire_dataset

    monkeypatch.setattr(acquire_dataset, "DATA_DIR", tmp_path)

    api = FakeKaggleApi([FakeKaggleDataset(ref="someowner/some-dataset", license_name="CC BY 4.0")])

    dest = acquire(SOURCE, api=api)

    assert api.downloaded == [("someowner/some-dataset", str(dest), True)]
    manifest_path = dest / "ACQUISITION_MANIFEST.json"
    assert manifest_path.exists()

    import json

    manifest = json.loads(manifest_path.read_text())
    assert manifest["source_name"] == "test_source"
    assert manifest["verified_license"] == "CC BY 4.0"
    assert manifest["kaggle_ref"] == "someowner/some-dataset"
