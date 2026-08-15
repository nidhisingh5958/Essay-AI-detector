"""
Near-duplicate check for PRIMARY-DATASET-v1, optimized for n=450 (not
previously exercised at this scale -- the naive O(n^2) full
`difflib.SequenceMatcher(autojunk=False)` pass over ~101k pairs of
essay-length texts did not finish in a reasonable time, and a first
length-based pre-filter attempt didn't help either, since this
project's seeds are all drawn from one narrow 150-320-word band by
design -- length alone barely discriminates here).

This is a PERFORMANCE optimization only, not a methodology change:
`generation_utils.near_duplicate_pairs_scoped` itself is untouched and
remains the source of truth for the threshold/exact-match/same-vs-cross-
family logic and is what every prior experiment's reported numbers used.
The only addition here is a cheap CANDIDATE-FILTER stage before the
expensive comparison: compute a 5-word shingle set per document (a
one-time O(n) cost), then only run the real `SequenceMatcher.ratio()`
on pairs whose shingle-set Jaccard similarity already clears a loose
lower bound. Two near-duplicate character sequences necessarily share
most of their word shingles too, so this cannot produce a false
negative at any threshold below the loose bound used here -- it only
skips pairs that share almost no word-level content and therefore
cannot possibly reach the real 0.9 character-level threshold.
"""

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))

import difflib  # noqa: E402

from generation_utils import NEAR_DUPLICATE_SIMILARITY_THRESHOLD, _WHITESPACE_RE  # noqa: E402

SHINGLE_SIZE = 5
# Loose on purpose -- this only needs to avoid false negatives, not be a
# tight bound. Two texts sharing under 20% of their 5-word shingles
# cannot plausibly reach 0.9 character-level similarity.
SHINGLE_JACCARD_CANDIDATE_FLOOR = 0.2


def _shingles(text: str) -> frozenset:
    words = text.split()
    if len(words) < SHINGLE_SIZE:
        return frozenset({tuple(words)}) if words else frozenset()
    return frozenset(tuple(words[i : i + SHINGLE_SIZE]) for i in range(len(words) - SHINGLE_SIZE + 1))


def _jaccard(a: frozenset, b: frozenset) -> float:
    if not a and not b:
        return 1.0
    if not a or not b:
        return 0.0
    inter = len(a & b)
    union = len(a) + len(b) - inter
    return inter / union if union else 0.0


def near_duplicate_pairs_scoped_fast(
    items: list[tuple[str, str, str]],
    exact_prefix_len: int = 80,
    exact_suffix_len: int = 80,
    near_similarity_threshold: float = NEAR_DUPLICATE_SIMILARITY_THRESHOLD,
) -> dict:
    normalized = [(sid, fam, _WHITESPACE_RE.sub(" ", t.strip().lower())) for sid, fam, t in items]
    shingle_sets = [_shingles(t) for _, _, t in normalized]

    cross_family = []
    same_family = []
    skipped = 0
    compared = 0
    n = len(normalized)
    for i in range(n):
        sid_i, fam_i, text_i = normalized[i]
        shi = shingle_sets[i]
        for j in range(i + 1, n):
            sid_j, fam_j, text_j = normalized[j]

            exact_sig_match = (
                len(text_i) == len(text_j)
                and text_i[:exact_prefix_len] == text_j[:exact_prefix_len]
                and text_i[-exact_suffix_len:] == text_j[-exact_suffix_len:]
            )
            if exact_sig_match:
                similarity = 1.0
            else:
                if _jaccard(shi, shingle_sets[j]) < SHINGLE_JACCARD_CANDIDATE_FLOOR:
                    skipped += 1
                    continue
                compared += 1
                similarity = difflib.SequenceMatcher(None, text_i, text_j, autojunk=False).ratio()

            if exact_sig_match or similarity >= near_similarity_threshold:
                pair = (sid_i, sid_j, round(similarity, 3))
                (same_family if fam_i == fam_j else cross_family).append(pair)

    print(f"  (shingle pre-filter skipped {skipped} pairs, ran SequenceMatcher on {compared} pairs)")
    return {"cross_family": cross_family, "same_family": same_family}


def main() -> None:
    dataset_dir = sys.argv[1] if len(sys.argv) > 1 else "PRIMARY-DATASET-v1"
    samples_path = REPO_ROOT / "data" / "generated" / dataset_dir / "samples.jsonl"
    records = [json.loads(line) for line in samples_path.read_text().splitlines() if line.strip()]
    print(f"Loaded {len(records)} records from {samples_path}")

    items = [(r["sample_id"], r["family_id"], r["text"]) for r in records]
    result = near_duplicate_pairs_scoped_fast(items)

    print(f"\ncross_family duplicates: {len(result['cross_family'])}")
    for pair in result["cross_family"]:
        print(" ", pair)
    print(f"same_family matches: {len(result['same_family'])}")


if __name__ == "__main__":
    main()
