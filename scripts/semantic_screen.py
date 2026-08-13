"""
Automated semantic-preservation SCREENING signals (DEC-012).

These are advisory screening signals used to prioritize human review --
never a substitute for it, and never written as final
`semantic_preservation` ground truth. An automated model deciding
"preserved" vs "changed" on its own would just relocate the same
LLM/model-as-ground-truth-judge problem DEC-004 rules out for detection
itself. See DEC-012 for what each signal can and cannot detect, false
positive/negative behavior, and how the thresholds here were calibrated
against the 40 manually-reviewed EXP-DATA-001-R1-confirmation samples
(not invented).
"""

import sys
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))
from app.services.sentence_segmenter import get_nlp  # noqa: E402

NUMBER_ENTITY_LABELS = {"CARDINAL", "ORDINAL", "QUANTITY", "PERCENT", "MONEY", "DATE", "TIME"}
NAME_ENTITY_LABELS = {"PERSON", "ORG", "GPE", "NORP", "FAC", "LOC", "EVENT"}

# Calibrated against the 40 manually-reviewed EXP-DATA-001-R1-confirmation
# samples (35 with a resolvable span pair) -- see
# scripts/calibrate_semantic_screen.py and DEC-012 for the actual
# distribution these were chosen from. At these values: 0/8 "changed"
# ground-truth samples would have been labeled "likely_preserved" (the
# safety property this screen is calibrated for); 1/4 "questionable"
# samples slipped through as "likely_preserved" in the calibration set (a
# known, documented miss -- see DEC-012); only 6/23 "preserved" samples
# get confident auto-pass, the rest correctly fall into "needs_review" --
# conservative by design.
#
# Re-verified out-of-sample on EXP-DATA-001-R2 (37 reviewed samples
# across the separate sentence and paragraph batches combined): 0/5
# "changed" samples labeled "likely_preserved" (safety property held);
# 2/4 "questionable" samples slipped through as "likely_preserved" --
# see DEC-012's "Out-of-Sample Validation" section for the exact sample
# IDs and full numbers.
DEFAULT_SIMILARITY_PRESERVED_THRESHOLD = 0.75
DEFAULT_SIMILARITY_REVIEW_BAND = 0.35


@lru_cache(maxsize=1)
def _load_embedding_model():
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer("all-MiniLM-L6-v2")


def extract_facts(text: str) -> dict:
    """Extract numbers and named entities from `text` using the shared
    spaCy pipeline (same one used for segmentation, DEC-005) -- not a
    second model. Returns normalized (lowercased) sets of numbers and
    names found."""
    doc = get_nlp()(text)
    numbers = set()
    names = set()
    for ent in doc.ents:
        norm = ent.text.lower().strip()
        if not norm:
            continue
        if ent.label_ in NUMBER_ENTITY_LABELS:
            numbers.add(norm)
        elif ent.label_ in NAME_ENTITY_LABELS:
            names.add(norm)
    for token in doc:
        if token.like_num:
            numbers.add(token.text.lower())
    return {"numbers": numbers, "names": names}


def check_fact_preservation(original: str, rewritten: str) -> dict:
    """Compare numbers/entities between an original span and its
    rewrite. This is a SCREENING check, not proof: a faithful paraphrase
    can legitimately drop a redundant number ("false positive" flag), and
    a genuinely altered claim might happen to share all its numbers with
    the original ("false negative" -- undetected). See DEC-012."""
    orig_facts = extract_facts(original)
    new_facts = extract_facts(rewritten)

    missing_numbers = orig_facts["numbers"] - new_facts["numbers"]
    missing_names = orig_facts["names"] - new_facts["names"]
    added_numbers = new_facts["numbers"] - orig_facts["numbers"]

    return {
        "flagged": bool(missing_numbers or missing_names or added_numbers),
        "missing_numbers": sorted(missing_numbers),
        "missing_names": sorted(missing_names),
        "added_numbers": sorted(added_numbers),
    }


def embedding_similarity(original: str, rewritten: str) -> float:
    """Cosine similarity between sentence-embedding vectors of the two
    spans. Catches "different claim/topic entirely" drift well; does NOT
    reliably catch small factual substitutions inside an otherwise
    structurally-similar sentence (e.g. "one C" -> "two Cs" scores ~0.87
    -- see DEC-012's calibration notes). That's exactly why this signal
    is combined with check_fact_preservation, not used alone."""
    model = _load_embedding_model()
    emb = model.encode([original, rewritten])
    a, b = emb[0], emb[1]
    denom = np.linalg.norm(a) * np.linalg.norm(b)
    if denom == 0:
        return 0.0
    return float(np.dot(a, b) / denom)


@dataclass(frozen=True)
class SemanticScreenResult:
    embedding_similarity: float
    fact_check: dict
    screen_label: str  # "likely_preserved" / "needs_review" / "likely_changed"


def classify_screen_label(
    similarity: float,
    fact_flagged: bool,
    preserved_threshold: float = DEFAULT_SIMILARITY_PRESERVED_THRESHOLD,
    review_band: float = DEFAULT_SIMILARITY_REVIEW_BAND,
) -> str:
    """Pure classification logic (separated from the model calls above
    so it's unit-testable without loading the embedding model)."""
    if fact_flagged:
        # A numeric/entity mismatch always escalates to review, regardless
        # of how similar the embeddings look -- this is precisely the
        # case embedding similarity alone misses (DEC-012).
        return "needs_review"
    if similarity >= preserved_threshold:
        return "likely_preserved"
    if similarity >= preserved_threshold - review_band:
        return "needs_review"
    return "likely_changed"


def run_semantic_screen(
    original: str,
    rewritten: str,
    preserved_threshold: float = DEFAULT_SIMILARITY_PRESERVED_THRESHOLD,
    review_band: float = DEFAULT_SIMILARITY_REVIEW_BAND,
) -> SemanticScreenResult:
    """Run both screening signals and combine them into an advisory
    label. `screen_label` is a SCREEN, not ground truth -- "likely_
    preserved" samples still were spot-checked in this project's
    validation rounds, and "needs_review"/"likely_changed" samples always
    go to human review before any dataset use, per DEC-012."""
    sim = embedding_similarity(original, rewritten)
    fact_result = check_fact_preservation(original, rewritten)
    label = classify_screen_label(sim, fact_result["flagged"], preserved_threshold, review_band)
    return SemanticScreenResult(embedding_similarity=sim, fact_check=fact_result, screen_label=label)
