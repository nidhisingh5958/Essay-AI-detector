"""
Automated claim-survival SCREENING signal for paragraph-level rewrites
(review item 5, 2026-08-13).

Targets the specific failure mode found in EXP-DATA-001-R2: a paragraph
rewrite can drop an entire original sentence's claim while still landing
inside length-ratio QC bounds (by being more verbose elsewhere) --
invisible to length/resegmentation checks. It is also not reliably
caught by the DEC-012 whole-span embedding-similarity screen, because
whole-paragraph similarity is an average and survives even when one
internal sentence's content vanishes -- the surrounding, unchanged
sentences dominate the score.

This is a SCREEN, not ground truth -- same DEC-004/DEC-012 constraint:
no automated signal in this pipeline may set final semantic_preservation.
Human review remains authoritative; see DEC-012 and
generation-methodology.md Section 12.

Two independent signals, combined so either one escalates to review:

1. Sentence coverage: for each sentence in the ORIGINAL paragraph, find
   its best-matching sentence in the REWRITTEN paragraph by embedding
   cosine similarity (same all-MiniLM-L6-v2 model as DEC-012). A low
   best-match score means no sentence in the rewrite reads like a
   paraphrase of that original sentence -- a signal (not proof) its
   claim was dropped rather than reworded.
2. Aggregate fact preservation: numbers/named entities across the WHOLE
   paragraph pair (reuses semantic_screen.check_fact_preservation) --
   catches a dropped/changed number or name even when it doesn't land on
   a specific sentence boundary (e.g. resegmentation shifted it).

CALIBRATION STATUS (honest, not invented): the sentence-coverage
threshold below is set conservatively -- below the full observed range
of genuine same-claim paraphrase similarities directly measured against
this project's own real paragraph data (0.63-0.73, computed against the
DB12BA4206B8 family from EXP-DATA-001-R2 -- see DEC-011's paragraph
claim-omission failure note).

Important, disclosed finding from that measurement: testing this signal
against that specific historical "changed" sample did NOT reproduce a
coverage drop -- all four original sentences scored 0.63-0.73 against
their best rewrite match, i.e. the "prisoners and volunteers" claim
reads as preserved in the text currently on disk, not dropped, on direct
re-inspection. This is flagged here, not hidden: either the prior manual
label predates the exact text now on disk, or that specific omission is
subtler than a full-sentence-level drop. The DB12BA4206B8 record itself
is frozen and was NOT modified to investigate this further, per explicit
instruction to preserve existing evidence. Net effect: this screen has
NOT been validated against any confirmed true-positive omission case --
that validation is exactly what the fresh paragraph claim-survival
experiment (EXP-DATA-001-R3) provides. Treat `possible_omission_flagged`
as "worth a human look," not as a confirmed detection.
"""

import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))
from app.services.sentence_segmenter import segment_sentences  # noqa: E402

from semantic_screen import _load_embedding_model, check_fact_preservation  # noqa: E402

# Conservative: below the full 0.63-0.73 range of genuine paraphrase
# best-match similarities observed in this project's real paragraph data
# (see module docstring). NOT yet validated against a true-positive
# omission case -- see EXP-DATA-001-R3 for that validation.
DEFAULT_SENTENCE_COVERAGE_THRESHOLD = 0.45


def _cosine(a: np.ndarray, b: np.ndarray) -> float:
    denom = np.linalg.norm(a) * np.linalg.norm(b)
    if denom == 0:
        return 0.0
    return float(np.dot(a, b) / denom)


def sentence_coverage(
    original: str,
    rewritten: str,
    threshold: float = DEFAULT_SENTENCE_COVERAGE_THRESHOLD,
) -> dict:
    """For each sentence in `original`, find its best-matching sentence in
    `rewritten` by embedding cosine similarity. Returns per-sentence best
    scores and which original sentences fell below `threshold` -- i.e.
    have no clear paraphrase counterpart anywhere in the rewrite."""
    orig_sents = [s.text for s in segment_sentences(original)]
    new_sents = [s.text for s in segment_sentences(rewritten)]
    if not orig_sents or not new_sents:
        return {"per_sentence": [], "dropped_sentences": [], "min_coverage_similarity": None}

    model = _load_embedding_model()
    orig_emb = model.encode(orig_sents)
    new_emb = model.encode(new_sents)

    per_sentence = []
    dropped = []
    for i, sent in enumerate(orig_sents):
        sims = [_cosine(orig_emb[i], new_emb[j]) for j in range(len(new_sents))]
        best_idx = int(np.argmax(sims))
        best_sim = sims[best_idx]
        entry = {
            "original_sentence": sent,
            "best_match": new_sents[best_idx],
            "similarity": round(float(best_sim), 4),
        }
        per_sentence.append(entry)
        if best_sim < threshold:
            dropped.append(entry)

    return {
        "per_sentence": per_sentence,
        "dropped_sentences": dropped,
        "min_coverage_similarity": round(min(e["similarity"] for e in per_sentence), 4),
    }


@dataclass(frozen=True)
class ClaimSurvivalResult:
    coverage: dict
    fact_check: dict
    screen_label: str  # "no_omission_signal" / "possible_omission_flagged"


def classify_claim_survival_label(coverage_dropped: bool, fact_flagged: bool) -> str:
    """Pure decision logic (unit-testable without loading the embedding
    model). Deliberately two states, not three: this screen has not been
    calibrated against a confirmed true-positive case, so it does not
    claim the confidence a "likely_changed"-style label would imply --
    it only flags for review or doesn't."""
    if coverage_dropped or fact_flagged:
        return "possible_omission_flagged"
    return "no_omission_signal"


def run_claim_survival_screen(
    original: str,
    rewritten: str,
    threshold: float = DEFAULT_SENTENCE_COVERAGE_THRESHOLD,
) -> ClaimSurvivalResult:
    """Run both screening signals and combine them into an advisory
    label. NOT ground truth -- see module docstring and DEC-012/DEC-011.
    `needs_review`-equivalent samples and `no_omission_signal` samples
    alike are still subject to full manual review during validation
    rounds; this only prioritizes attention."""
    coverage = sentence_coverage(original, rewritten, threshold)
    fact_result = check_fact_preservation(original, rewritten)
    label = classify_claim_survival_label(bool(coverage["dropped_sentences"]), fact_result["flagged"])
    return ClaimSurvivalResult(coverage=coverage, fact_check=fact_result, screen_label=label)
