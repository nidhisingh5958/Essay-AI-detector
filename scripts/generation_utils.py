"""
Pure, testable helper functions for EXP-DATA-001 (and later, full-scale
generation). Kept separate from qwen_generate.py and run_exp_data_001.py
so the logic that matters most for correctness -- length budgeting,
sentence alignment/diffing, seed selection, split assignment, QC checks
-- can be unit tested against small fixtures without loading a model or
touching the real corpus.
"""

import difflib
import random
import re
from collections import Counter

# Empirically measured on Qwen2.5-1.5B-Instruct's tokenizer against
# sample English sentences during the Phase 5C/5D smoke test: ~1.06
# tokens/word on plain text. Budgeted higher here deliberately -- essay
# text has more punctuation/contractions than the smoke-test sample, and
# under-budgeting silently truncates content, which is worse than
# generating a bit more than needed and truncating afterward.
TOKENS_PER_WORD_BUDGET = 1.6
GENERATION_TOKEN_OVERHEAD = 20


def budget_max_new_tokens(target_words: int) -> int:
    """How many tokens to allow the model to generate, given a target
    word count. Deliberately generous -- see truncate_to_word_budget for
    the actual length-control mechanism (Section 5 of
    generation-methodology.md's finding: phrased length requests alone
    don't reliably constrain output)."""
    return int(target_words * TOKENS_PER_WORD_BUDGET) + GENERATION_TOKEN_OVERHEAD


def truncate_to_word_budget(text: str, sentence_end_chars: list[int], target_words: int, max_over_ratio: float = 1.15) -> str:
    """Truncate `text` to the longest prefix of sentences (using the
    given sentence end-character offsets, in order) whose cumulative word
    count doesn't exceed target_words * max_over_ratio. Always keeps at
    least one sentence, even if that one sentence alone exceeds the
    budget -- never returns an empty string for non-empty input."""
    if not sentence_end_chars:
        return text

    limit = target_words * max_over_ratio
    best_end = sentence_end_chars[0]
    for end in sentence_end_chars:
        word_count = len(text[:end].split())
        if word_count <= limit:
            best_end = end
        else:
            break
    return text[:best_end]


def align_and_diff_sentences(original_sentences: list[str], candidate_sentences: list[str]) -> dict:
    """Compare two sentence lists position-by-position (DEC-011: whole-
    essay-instruction-plus-diff categories). Only aligns when sentence
    counts match exactly -- anything else is reported as structure_drift
    rather than guessed at, per the explicit instruction not to invent
    alignment when it isn't confident.

    Returns:
        {
          "structure_drift": bool,
          "pairs": [(original_sentence, candidate_sentence, similarity_ratio), ...],
        }
    similarity_ratio is difflib.SequenceMatcher's ratio() in [0, 1];
    1.0 means identical text. `autojunk=False` is passed explicitly --
    SequenceMatcher's default `autojunk=True` treats characters as
    "popular" (and excludes them from matching) once a sequence exceeds
    200 characters, which can badly understate similarity for longer
    sentences with no actual relationship to how similar the text is.
    Found while building near_duplicate_pairs_scoped (EXP-DATA-001-R1
    confirmation round) -- see that function's docstring and
    scripts/tests/test_generation_utils.py for a worked example of how
    large the distortion can be (>0.6 ratio difference on a
    single-word change in a ~200-character string).
    """
    if len(original_sentences) != len(candidate_sentences):
        return {"structure_drift": True, "pairs": []}

    pairs = []
    for orig, cand in zip(original_sentences, candidate_sentences):
        ratio = difflib.SequenceMatcher(None, orig, cand, autojunk=False).ratio()
        pairs.append((orig, cand, ratio))
    return {"structure_drift": False, "pairs": pairs}


def modified_sentence_indices(diff_result: dict, similarity_threshold: float) -> list[int]:
    """Given align_and_diff_sentences' output and a similarity threshold,
    return indices of sentences judged AI-touched (similarity below the
    threshold). Threshold is a parameter, not hardcoded here -- this
    pilot's whole point is to observe real similarity distributions
    before fixing that number in DEC-011."""
    return [i for i, (_, _, ratio) in enumerate(diff_result["pairs"]) if ratio < similarity_threshold]


def select_seed_essays(records: list[dict], n: int, min_words: int, max_words: int, min_sentences: int, min_paragraphs: int, rng_seed: int) -> list[str]:
    """Select `n` candidate seed essay IDs from `records` (each a dict
    with at least id/word_count/sentence_count/paragraph_count keys),
    filtered to a workable size/structure range and sampled
    deterministically. Returns essay IDs, not the records themselves, so
    callers stay in control of what "essay id" means for their data."""
    candidates = [
        r["id"]
        for r in records
        if min_words <= r["word_count"] <= max_words
        and r["sentence_count"] >= min_sentences
        and r["paragraph_count"] >= min_paragraphs
    ]
    if len(candidates) < n:
        raise ValueError(f"Only {len(candidates)} candidates meet the filters; need {n}.")
    rng = random.Random(rng_seed)
    return sorted(rng.sample(candidates, n))


def assign_family_splits(seed_ids: list[str], ratios: tuple[float, float, float] = (0.7, 0.15, 0.15), rng_seed: int = 42) -> dict[str, str]:
    """Assign each seed essay id to train/validation/test *before* any
    generation happens (DEC-011's hard leakage invariant). Deterministic
    given the same seed_ids + rng_seed, so re-running produces the same
    assignment."""
    assert abs(sum(ratios) - 1.0) < 1e-9, "split ratios must sum to 1.0"
    rng = random.Random(rng_seed)
    shuffled = list(seed_ids)
    rng.shuffle(shuffled)

    n = len(shuffled)
    n_train = round(n * ratios[0])
    n_val = round(n * ratios[1])

    assignment = {}
    for i, sid in enumerate(shuffled):
        if i < n_train:
            assignment[sid] = "train"
        elif i < n_train + n_val:
            assignment[sid] = "validation"
        else:
            assignment[sid] = "test"
    return assignment


def pick_rewrite_sentence_index(sentences: list[str], min_words: int = 8, max_words: int = 40, rng_seed: int = 0) -> int | None:
    """Pick one sentence index suitable for a surgical single-sentence
    rewrite (not degenerately short/long). Returns None if nothing
    qualifies -- callers must treat that as "skip this seed for this
    category," not silently pick an unsuitable sentence."""
    candidates = [i for i, s in enumerate(sentences) if min_words <= len(s.split()) <= max_words]
    if not candidates:
        return None
    return random.Random(rng_seed).choice(candidates)


def pick_rewrite_paragraph_index(paragraphs: list[str], min_words: int = 15, rng_seed: int = 0) -> int | None:
    """Pick one paragraph index suitable for a surgical paragraph
    rewrite. Returns None if no paragraph is long enough to be a
    meaningful rewrite target."""
    candidates = [i for i, p in enumerate(paragraphs) if len(p.split()) >= min_words]
    if not candidates:
        return None
    return random.Random(rng_seed).choice(candidates)


_WHITESPACE_RE = re.compile(r"\s+")


def check_empty_output(text: str) -> bool:
    """True if the output is empty/failed."""
    return not text or not text.strip()


def check_length_bounds(word_count: int, min_words: int, max_words: int) -> bool:
    """True if word_count is within [min_words, max_words] (a failure
    check -- catches truncated or runaway generations, not the length-
    matching *target* tolerance, which is a separate, softer concern)."""
    return min_words <= word_count <= max_words


def check_instruction_leakage(meta_instruction: str, output: str, min_overlap_words: int = 6) -> bool:
    """True if a run of `min_overlap_words` consecutive words from the
    META-instructional wrapper appears verbatim in the output -- a
    cheap, specific signal of the model echoing its own meta-instructions
    ("Write a ... essay ... Return only the essay, with no preamble...")
    rather than producing the requested content.

    CALLERS MUST PASS ONLY THE META/WRAPPER LANGUAGE HERE -- never the
    source prompt text, the target sentence/paragraph, or any other
    topic content the output is *expected* to legitimately reference.
    EXP-DATA-001 found the previous version of this check (which compared
    against the whole formatted instruction, including embedded prompt
    text) produced false positives whenever a generated essay discussed
    its own assigned topic using similar wording to the prompt -- that is
    correct, on-topic behavior, not leakage. See DEC-011's "Pilot
    Findings" and `scripts/tests/test_generation_utils.py`'s regression
    test for the preserved failure case.
    """
    instr_words = _WHITESPACE_RE.sub(" ", meta_instruction.lower()).split()
    out_norm = _WHITESPACE_RE.sub(" ", output.lower())
    if len(instr_words) < min_overlap_words:
        return False
    for i in range(len(instr_words) - min_overlap_words + 1):
        chunk = " ".join(instr_words[i : i + min_overlap_words])
        if chunk in out_norm:
            return True
    return False


_AI_SELF_REFERENCE_PHRASES = (
    "as an ai",
    "as an artificial intelligence",
    "as a language model",
    "as an ai language model",
    "i am an ai",
    "i'm an ai",
    "i do not have personal experiences",
    "i don't have personal experiences",
    "i don't have personal feelings",
    "as a large language model",
)


def check_ai_self_reference(output: str) -> bool:
    """True if the output contains a phrase where the model reveals
    itself as an AI (e.g. 'as an AI language model, I don't have
    personal experiences...') -- a distinct failure mode from
    instruction-wrapper leakage (check_instruction_leakage) or a
    generation preamble (check_instruction_artifacts). Searches anywhere
    in the text, not just the start, since this kind of self-reference
    often appears mid-essay as a caveat rather than as an opening line."""
    normalized = _WHITESPACE_RE.sub(" ", output.lower())
    return any(phrase in normalized for phrase in _AI_SELF_REFERENCE_PHRASES)


def check_excessive_repetition(words: list[str], n: int = 3, ratio_ceiling: float = 0.3) -> tuple[bool, float]:
    """Reimplements the same repeated-n-gram-ratio definition as
    backend/app/services/feature_extractor.py's `_repeated_ngram_ratio`
    (Phase 3), applied here as a generation-failure QC check rather than
    a detector feature -- same measurement, different purpose. Returns
    (flagged, ratio)."""
    if len(words) < n:
        return False, 0.0
    ngrams = [tuple(words[i : i + n]) for i in range(len(words) - n + 1)]
    counts = Counter(ngrams)
    repeated = sum(c for c in counts.values() if c > 1)
    ratio = repeated / len(ngrams)
    return ratio > ratio_ceiling, ratio


def check_instruction_artifacts(output: str) -> bool:
    """True if the output starts with a common instruction-following
    preamble the model failed to omit (e.g. 'Sure, here's...'). AI
    self-reference ('as an AI...') is a separate check
    (check_ai_self_reference) since it can appear anywhere in the text,
    not just as an opening preamble."""
    artifacts = (
        "sure,",
        "sure!",
        "here is",
        "here's",
        "certainly",
        "of course",
    )
    normalized = output.strip().lower()
    return any(normalized.startswith(a) for a in artifacts)


def near_duplicate_pairs(texts: list[str], prefix_len: int = 80, suffix_len: int = 80) -> list[tuple[int, int]]:
    """Pairwise near-duplicate heuristic for a small list (pilot-scale --
    O(n^2) is fine at n=10). Two texts are flagged if their normalized
    prefix+suffix+length signature matches. Returns index pairs.

    NOTE: this flat version does not distinguish same-family from
    cross-family similarity, and EXP-DATA-001-R1 found that matters in
    practice -- a single-sentence surgical edit is naturally near-
    identical to its own human original and siblings, which this
    function correctly flags as "similar" but which isn't a real
    duplication problem. Kept for cases where family membership doesn't
    apply (e.g. comparing independently-generated `full_ai` samples
    against each other, where every one is its own family). For anything
    involving surgical-splice family members, use
    near_duplicate_pairs_scoped instead."""
    normalized = [_WHITESPACE_RE.sub(" ", t.strip().lower()) for t in texts]
    signatures = [(t[:prefix_len], t[-suffix_len:], len(t)) for t in normalized]
    pairs = []
    for i in range(len(signatures)):
        for j in range(i + 1, len(signatures)):
            if signatures[i] == signatures[j]:
                pairs.append((i, j))
    return pairs


# Similarity at/above this is treated as "near-identical" for cross-family
# duplicate detection -- a QC calibration parameter (like the repetition-
# ratio ceiling elsewhere in this file), not a ground-truth-determining
# threshold. Distinct from DEC-011's rejected sentence-attribution
# threshold: this doesn't decide which text is AI-authored, only whether
# two *outputs* are suspiciously alike.
NEAR_DUPLICATE_SIMILARITY_THRESHOLD = 0.9


def near_duplicate_pairs_scoped(
    items: list[tuple[str, str, str]],
    exact_prefix_len: int = 80,
    exact_suffix_len: int = 80,
    near_similarity_threshold: float = NEAR_DUPLICATE_SIMILARITY_THRESHOLD,
) -> dict:
    """Family-aware near-duplicate detection.

    `items` is a list of (sample_id, family_id, text).

    Same-family similarity is EXPECTED, not suspicious: every sample
    derived from one seed essay necessarily shares almost all of its text
    with the original and with its siblings (a single-sentence surgical
    edit changes a few dozen words out of a few hundred). Flagging that
    as "duplication" is noise -- exactly what happened in
    EXP-DATA-001-R1's flat near_duplicate_pairs check.

    The real detection target is CROSS-family similarity: two samples
    derived from *different* seed essays ending up near-identical would
    indicate a genuine problem (e.g. the generation model collapsing
    distinct prompts into similar output).

    Returns:
        {
          "cross_family": [(sample_id_i, sample_id_j, similarity), ...],
          "same_family": [(sample_id_i, sample_id_j, similarity), ...],
        }
    Only pairs at/above the near-duplicate threshold (or an exact
    prefix/suffix/length signature match) appear in either list.
    `cross_family` is the list to actually act on; `same_family` is
    informational only and must never be treated as a defect.
    """
    normalized = [(sid, fam, _WHITESPACE_RE.sub(" ", t.strip().lower())) for sid, fam, t in items]

    cross_family = []
    same_family = []
    for i in range(len(normalized)):
        sid_i, fam_i, text_i = normalized[i]
        for j in range(i + 1, len(normalized)):
            sid_j, fam_j, text_j = normalized[j]

            exact_sig_match = (
                len(text_i) == len(text_j)
                and text_i[:exact_prefix_len] == text_j[:exact_prefix_len]
                and text_i[-exact_suffix_len:] == text_j[-exact_suffix_len:]
            )
            similarity = (
                1.0 if exact_sig_match else difflib.SequenceMatcher(None, text_i, text_j, autojunk=False).ratio()
            )

            if exact_sig_match or similarity >= near_similarity_threshold:
                pair = (sid_i, sid_j, round(similarity, 3))
                (same_family if fam_i == fam_j else cross_family).append(pair)

    return {"cross_family": cross_family, "same_family": same_family}


# Semantic preservation: does a controlled rewrite change the writing
# form/style without silently changing the author's underlying meaning or
# claims? This is a provenance/QC field, not a ground-truth-determining
# one -- Regime A/B's "this span is AI-authored" label is already exact
# by construction (we chose the span). Semantic preservation instead
# tracks whether the transformation was a *faithful* light/moderate edit,
# which matters for how trustworthy the resulting mixed sample is as a
# realistic simulation of "AI touched this part without changing what
# the student was saying."
#
# Deliberately NOT computed by any model call in this pipeline -- doing
# so would mean asking a language model to judge another language
# model's output, i.e. exactly the LLM-as-ground-truth-judge pattern this
# project avoids everywhere else (DEC-004). Values are assigned by manual
# human review (see reports/EXP-DATA-001-R1-confirmation.md) and recorded
# per sample; `not_yet_reviewed` is the only value this codebase ever
# sets automatically.
SEMANTIC_PRESERVATION_VALUES = ("not_yet_reviewed", "preserved", "questionable", "changed")


def validate_semantic_preservation(value: str) -> bool:
    """True if `value` is one of the recognized semantic_preservation
    values. Used to catch typos/invalid values before they're written
    into a sample record, not to judge the value itself."""
    return value in SEMANTIC_PRESERVATION_VALUES


def find_family_split_violations(records: list[dict]) -> list[dict]:
    """Hard leakage invariant (DEC-011 Section 13): every sample derived
    from one seed essay (same family_id) must share exactly one split.
    Returns a list of {"family_id": ..., "splits": {...}} for any family
    that does NOT -- empty list means the invariant holds. Meant to run
    as a real check against a generated samples.jsonl, not just trusted
    by construction, since `split` is passed by the caller at each
    generation call site and a refactor could silently break this."""
    splits_by_family: dict[str, set[str]] = {}
    for record in records:
        splits_by_family.setdefault(record["family_id"], set()).add(record["split"])

    violations = []
    for family_id, splits in splits_by_family.items():
        if len(splits) > 1:
            violations.append({"family_id": family_id, "splits": sorted(splits)})
    return violations
