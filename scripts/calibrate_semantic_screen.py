"""
Calibrate the automated semantic-preservation screen (DEC-012) against
the 40 manually-reviewed EXP-DATA-001-R1-confirmation samples.

This is the "do not invent a threshold before seeing the distribution"
step: it prints embedding-similarity and fact-check results grouped by
the REAL manual semantic_preservation labels already recorded for those
samples, so a threshold can be chosen from actual observed separation
rather than guessed.
"""

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "backend"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.services.sentence_segmenter import parse_document, segment_sentences  # noqa: E402
from app.services.text_normalizer import normalize_text  # noqa: E402

from semantic_screen import check_fact_preservation, embedding_similarity  # noqa: E402

SAMPLES_PATH = REPO_ROOT / "data" / "generated" / "EXP-DATA-001-R1-confirmation" / "samples.jsonl"


def extract_span_pair(human_record: dict, record: dict) -> tuple[str, str] | None:
    """Reconstruct (original_span_text, rewritten_span_text) for a
    confirmation-round record. Returns None if the sample was rejected
    before a span could be confirmed (nothing trustworthy to compare)."""
    if not record["modified_spans"]:
        return None

    human_text = human_record["text"]

    if record["transformation_type"].startswith("sentence_"):
        doc = parse_document(human_text)
        sentences = segment_sentences(human_text, doc=doc)
        idx = record["intended_span_index"]
        if idx is None or idx >= len(sentences):
            return None
        original = sentences[idx].text
    else:  # paragraph_*
        paragraphs = human_text.split("\n\n")
        idx = record["intended_span_index"]
        if idx is None or idx >= len(paragraphs):
            return None
        original = paragraphs[idx]

    starts = [s["char_start"] for s in record["modified_spans"]]
    ends = [s["char_end"] for s in record["modified_spans"]]
    rewritten = record["text"][min(starts) : max(ends)]
    return original, rewritten


def main() -> None:
    records = [json.loads(line) for line in SAMPLES_PATH.read_text().splitlines() if line.strip()]
    by_family = {}
    for r in records:
        by_family.setdefault(r["family_id"], {})[r["transformation_type"]] = r

    rows = []
    for fam, cats in by_family.items():
        human = cats["original"]
        for cat, record in cats.items():
            if cat == "original":
                continue
            if record["semantic_preservation"] in (None, "not_yet_reviewed"):
                continue
            pair = extract_span_pair(human, record)
            if pair is None:
                continue
            original, rewritten = pair
            sim = embedding_similarity(original, rewritten)
            fact = check_fact_preservation(original, rewritten)
            rows.append(
                {
                    "sample_id": record["sample_id"],
                    "category": cat,
                    "manual_label": record["semantic_preservation"],
                    "embedding_similarity": round(sim, 4),
                    "fact_flagged": fact["flagged"],
                    "fact_detail": fact,
                }
            )

    rows.sort(key=lambda r: (r["manual_label"], r["embedding_similarity"]))
    print(f"{'sample_id':<50} {'label':<13} {'sim':>6}  fact_flagged  detail")
    for row in rows:
        print(
            f"{row['sample_id']:<50} {row['manual_label']:<13} "
            f"{row['embedding_similarity']:>6.3f}  {str(row['fact_flagged']):<13} "
            f"{row['fact_detail'] if row['fact_flagged'] else ''}"
        )

    print("\n=== summary by manual label ===")
    from collections import defaultdict

    by_label = defaultdict(list)
    for row in rows:
        by_label[row["manual_label"]].append(row["embedding_similarity"])
    for label, sims in sorted(by_label.items()):
        sims_sorted = sorted(sims)
        print(f"{label}: n={len(sims_sorted)} sims={sims_sorted}")

    out_path = REPO_ROOT / "data" / "generated" / "semantic_screen_calibration.json"
    out_path.write_text(json.dumps(rows, indent=2))
    print(f"\nWrote {len(rows)} calibration rows to {out_path}")


if __name__ == "__main__":
    main()
