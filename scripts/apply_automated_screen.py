"""
Apply the DEC-012 automated semantic screen to a generated samples file,
post-hoc (mirrors the cross-family-duplicate-check pattern already used
elsewhere in this pipeline).

This does NOT set semantic_preservation -- it only fills in
automated_screen_similarity / automated_screen_fact_check /
automated_screen_label as advisory fields. Manual review (see
apply_semantic_review.py) remains the authority on semantic_preservation.

Usage:
    python apply_automated_screen.py data/generated/EXP-DATA-001-R2-sentence/samples.jsonl
"""

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "backend"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.services.sentence_segmenter import parse_document, segment_sentences  # noqa: E402

from semantic_screen import run_semantic_screen  # noqa: E402


def extract_span_pair(human_record: dict, record: dict) -> tuple[str, str] | None:
    if not record.get("modified_spans"):
        return None

    human_text = human_record["text"]

    if record["transformation_type"].startswith("sentence_"):
        doc = parse_document(human_text)
        sentences = segment_sentences(human_text, doc=doc)
        idx = record["intended_span_index"]
        if idx is None or idx >= len(sentences):
            return None
        original = sentences[idx].text
        starts = [s["char_start"] for s in record["modified_spans"]]
        ends = [s["char_end"] for s in record["modified_spans"]]
        rewritten = record["text"][min(starts) : max(ends)]
    else:  # paragraph_*
        # NOT reconstructed from modified_spans char offsets (that
        # truncates when the rewrite merges sentences -- see DEC-012's
        # "Known Issue" note), and NOT reconstructed by splitting both
        # texts on "\n\n" at the same paragraph index either: found
        # 2026-08-13 that this ALSO breaks when the model's replacement
        # text itself contains a blank-line break, which splits the
        # rewritten paragraph across more "\n\n"-paragraphs than the
        # original had, silently capturing only the first fragment (seed
        # 7AF7BFC4BF8D: extracted 95 of the actual 247 rewritten words).
        # Instead, use the splice invariant directly: everything before
        # and after the target paragraph is byte-identical between the
        # human and rewritten essay, by construction (only the target
        # paragraph's characters were ever replaced). Locating the
        # unchanged prefix/suffix and taking what's between them is exact
        # regardless of how the rewrite itself is internally formatted.
        human_paragraphs = human_text.split("\n\n")
        idx = record["intended_span_index"]
        if idx is None or idx >= len(human_paragraphs):
            return None
        original = human_paragraphs[idx]
        char_start = len("\n\n".join(human_paragraphs[:idx])) + (2 if idx > 0 else 0)
        char_end = char_start + len(original)
        prefix = human_text[:char_start]
        suffix = human_text[char_end:]
        new_text = record["text"]
        if not new_text.startswith(prefix) or not new_text.endswith(suffix):
            return None
        rewritten = new_text[len(prefix) : len(new_text) - len(suffix)] if suffix else new_text[len(prefix) :]
    return original, rewritten


def main() -> None:
    if len(sys.argv) != 2:
        print("Usage: python apply_automated_screen.py <samples.jsonl path>")
        sys.exit(1)

    samples_path = Path(sys.argv[1])
    records = [json.loads(line) for line in samples_path.read_text().splitlines() if line.strip()]
    by_family = {}
    for r in records:
        by_family.setdefault(r["family_id"], {})[r["transformation_type"]] = r

    screened = 0
    for fam, cats in by_family.items():
        human = cats.get("original")
        if human is None:
            continue
        for cat, record in cats.items():
            if cat == "original":
                continue
            pair = extract_span_pair(human, record)
            if pair is None:
                continue
            original, rewritten = pair
            result = run_semantic_screen(original, rewritten)
            record["automated_screen_similarity"] = round(result.embedding_similarity, 4)
            record["automated_screen_fact_check"] = result.fact_check
            record["automated_screen_label"] = result.screen_label
            screened += 1
            print(f"  {record['sample_id']}: sim={result.embedding_similarity:.3f} label={result.screen_label}")

    with open(samples_path, "w") as f:
        for record in records:
            f.write(json.dumps(record) + "\n")

    print(f"\nApplied automated screen to {screened} records in {samples_path}")


if __name__ == "__main__":
    main()
