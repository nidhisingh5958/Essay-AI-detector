# DEC-006 — Phase 3 Feature Scope and Computation Methods

## Status
Provisional

## Date
2026-08-10

## Context

Section 6 of the project brief lists five candidate feature categories
(language-model, sentence rhythm, vocabulary, repetition, linguistic/
structural) and explicitly warns: "Do not blindly add dozens of features.
Investigate which features actually provide useful signal." Genuinely
investigating signal requires comparing feature distributions between
known-human and known-AI text — which requires the dataset from Phase 5,
which doesn't exist yet. Phase 3 (this phase) only has code, no data.

## Problem

Two problems, addressed together:

1. Which specific features, within the brief's categories, should be
   implemented now, given no dataset yet exists to validate them against?
2. What should the computation method be for each (e.g., how is "rare
   word" defined; how is dependency complexity measured)?

## Alternatives Considered

### For "when to write feature code": 

**Alternative A — Wait for Phase 5 (dataset) before writing any feature
code**, so every feature is chosen with real signal evidence from the
start.
Advantages: never writes a feature that later gets deleted for lacking
signal.
Disadvantages: blocks all forward progress on Phases 3–4, and the dataset
scripts in Phase 5 themselves need *some* feature extraction machinery to
compute dataset statistics and build reference distributions against —
there's a circular dependency. The brief's own phase ordering (Phase 3
before Phase 5) implies feature extraction code is expected to exist
before the dataset does.

**Alternative B — Implement a deliberately small, literature-grounded
initial feature set per category now (this phase), explicitly marked
provisional, and prune/extend it empirically once Phase 5's dataset and
EXP-002 exist.**
Advantages: unblocks Phases 4–5; each feature is still individually
justified (not arbitrary) even without a labeled dataset, because each
is a standard, well-established measure in the computational-linguistics/
stylometry literature (e.g. type-token ratio, dependency-tree depth) —
plausible candidates, not guesses.
Disadvantages: some implemented features may turn out to carry no signal
and get dropped later (an accepted, documented cost — see Revisit When).

### For "how to define rare words":

**Alternative A — spaCy lexeme probability (`token.prob`)**
Advantages: no extra dependency.
Disadvantages: `en_core_web_sm` does not ship real lexeme probabilities
(they're zeroed out in the small model to save size) — this would
silently produce meaningless values, which is worse than an honest
missing feature.

**Alternative B — `wordfreq` library's Zipf-scale word frequency**
Advantages: purpose-built for this (returns a word's frequency on a
standard log scale, 1–8, calibrated across large corpora); actively
maintained; pure-Python with small bundled data; the Zipf scale itself is
an established convention in psycholinguistics for "how common is this
word," not something invented for this project.
Disadvantages: adds one new dependency (`wordfreq`).

**Decision for this sub-problem:** Alternative B. A word is counted as
"rare" if `zipf_frequency(word, "en") < 3.0` — the conventional
low-frequency cutoff on the Zipf scale (roughly: words rarer than ~1 per
million tokens). This is an operational *definition* of "rare," not a
detection threshold — it does not by itself classify anything as AI or
human; it only feeds one input feature into scoring, which is calibrated
separately in Phase 6.

### For "how to measure syntactic complexity":

Chosen: maximum dependency-tree depth per sentence, computed from spaCy's
existing dependency parse (already computed for sentence segmentation,
DEC-005 — no extra cost). Simpler alternatives considered and rejected:
raw sentence length alone (already captured separately as a rhythm
feature — would be redundant) and clause count via conjunction counting
(cruder proxy, dependency depth more directly reflects nesting/
subordination).

## Decision

Implement, in `backend/app/services/feature_extractor.py`:

**Sentence-level:** word count, character count, punctuation count,
average word length, POS ratios (noun/verb/adjective/adverb/pronoun),
maximum dependency-tree depth.

**Essay-level:** sentence-length mean/std/coefficient-of-variation,
short/medium/long sentence-length distribution, type-token ratio, moving-
average type-token ratio (window-based, robust to essay length), rare-word
ratio (via `wordfreq`, threshold above), repeated-bigram ratio,
repeated-trigram ratio, repeated-sentence-opening ratio.

Explicitly deferred to later phases (not implemented now): local-LM-
derived features (perplexity, log-probability — Phase 4, per
[DEC-004](DEC-004-no-llm-classifier.md)); any feature requiring the
dataset (reference-distribution comparison, Phase 5/6).

## Why

This set covers every category in Section 6 except the LM-instrument one
(explicitly Phase 4's job), uses only well-established, literature-backed
computations, and reuses the existing spaCy parse from segmentation
(DEC-005) rather than introducing new parsing cost. It is intentionally
not exhaustive — e.g., it does not yet include function-word distribution
or clause-boundary detection, which can be added later if EXP-002 (Phase
5/6) suggests the current set is insufficient.

## Evidence

None yet — by construction, since no dataset exists. This decision is
explicitly **Provisional**: it fixes the starting feature set to unblock
Phases 4–5, not a final, evidence-validated set.

## Trade-offs

Some of these features may show no real human/AI signal once measured and
will need to be dropped (Section 6: "Only retain features that
demonstrate useful signal"). Building them now, before that evidence
exists, is accepted as the cost of not blocking the whole project on
Phase 5 first.

## Consequences

Positive:
- Phases 4 (LM instrumentation) and 5 (dataset statistics) have concrete
  feature-vector machinery to build on.
- Every sentence-level feature is computed from the same spaCy parse used
  for segmentation — no duplicate parsing.

Negative:
- This feature set is not yet validated and must not be presented as
  "the detector's features" in any evaluation claim until EXP-002 (Phase
  5/6) actually measures their signal.

## Revisit When

Once Phase 5 produces a labeled dataset: run EXP-002 to measure each
feature's actual separation between human/AI/mixed classes. Drop any
feature that shows no discriminative signal; this decision's status
should be updated to **Superseded** at that point, pointing to whichever
decision records the validated final feature set.

## Implementation

`backend/app/services/feature_extractor.py`

## Tests / Experiments

`backend/tests/test_feature_extractor.py`. Signal-validation experiment
(EXP-002) not yet run — see Revisit When.
