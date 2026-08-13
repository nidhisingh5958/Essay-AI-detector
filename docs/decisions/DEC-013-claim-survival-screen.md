# DEC-013 — Paragraph-Level Claim-Survival Screening Signal

## Status
Accepted **as an automated semantic-risk screening / triage tool** —
same reframing as DEC-012, explicitly NOT a semantic safety gate (see
DEC-012's "Reframing" section for the shared rationale). **Updated
2026-08-13 with EXP-DATA-001-R3's real validation results** (see
"Validation Results" below): the
sentence-coverage signal caught 1 real, confirmed true-positive claim
omission and correctly stayed silent on faithful paraphrases, but missed
2 of 3 "changed" paragraph samples this round — the coverage signal is
tuned for a *dropped* claim, and neither observed miss was a dropped
claim (one was a stated-priority reversal, the other a claim drop
combined with a location/mechanism flip that the coverage signal's
per-sentence best-match approach did not register as low enough
similarity). Still not a ground-truth substitute; still requires full
human review regardless of label.

## Date
2026-08-13

## Context

EXP-DATA-001-R2 found a paragraph-level failure mode DEC-012's screen
was not designed for: **claim omission that survives length-ratio QC**.
A paragraph rewrite can drop an entire original sentence's claim while
expanding elsewhere, landing inside the accepted length-ratio bounds
(seed `DB12BA4206B8`, both light and moderate — see DEC-011's
"Category-Specific Conclusions"). DEC-012's whole-span embedding
similarity is computed once per paragraph pair; it is an *average*, and
survives even when one internal sentence's content genuinely vanishes,
because the surrounding unchanged sentences dominate the score. A
sentence-level signal was needed specifically for this failure mode.

## Problem

What automated signal, if any, should screen paragraph-level rewrites
specifically for dropped claims (as opposed to changed claims, which
DEC-012 already screens for), without becoming a second ground-truth
judge?

## Alternatives Considered

### Alternative A: Lower the DEC-012 whole-paragraph similarity threshold
Advantages: no new code.
Disadvantages: doesn't address the actual mechanism of the failure — a
paragraph that drops one sentence's claim while faithfully paraphrasing
the rest can still score a high *average* similarity. Lowering the
threshold to catch this would also flag many faithful paraphrases,
without any evidence it would catch the actual omission case (see
Evidence: DEC-012's own whole-paragraph similarity was not the tool that
caught the original DB12BA4206B8 case — manual review was). Rejected.

### Alternative B: Per-sentence coverage via embedding best-match (chosen, combined with C)
For each sentence in the original paragraph, find its best-matching
sentence in the rewritten paragraph by embedding cosine similarity (same
`all-MiniLM-L6-v2` model as DEC-012, no new dependency). A low best-match
score means no sentence in the rewrite reads like a paraphrase of that
original sentence.

Advantages: directly targets the failure mechanism (a specific original
sentence with no counterpart), not an aggregate score that can average
the problem away; reuses the existing embedding model.

Disadvantages: computationally more expensive than one whole-paragraph
comparison (O(n×m) sentence pairs); a genuinely reordered-but-faithful
rewrite could in principle still find a best match for every sentence,
so this doesn't catch every possible omission strategy (e.g. a claim
distributed across multiple merged sentences with no single best match
above threshold for any one piece) — an acknowledged, undemonstrated gap.

### Alternative C: Aggregate fact preservation on the whole paragraph pair (chosen, combined with B)
Reuse `semantic_screen.check_fact_preservation` directly on the full
original vs. full rewritten paragraph (not per-sentence).

Advantages: catches a dropped/changed number or name even when
resegmentation shifts exactly where it lands; no new code beyond what
DEC-012 already built.

Disadvantages: same false-positive behavior already documented in
DEC-012 (spaCy NER over-tagging ordinary phrases as quantity-like
entities) — and this project's own testing while building this screen
found this is **worse for paragraph-level, time-of-day text than
previously documented**: phrases like "later in the evening" / "at
night" are tagged as TIME entities, and even a fully faithful rewrite
that merely rewords a time reference will flag. See Evidence.

### Alternative D: NLI/entailment per sentence pair
Advantages: more linguistically principled, could distinguish
"dropped" from "merged into a paraphrase" more precisely than a
similarity threshold.
Disadvantages: same objection as DEC-012's Alternative B — a second
model class, its own calibration burden, for a benefit not yet shown
necessary given B+C's performance is still unvalidated in either
direction. **Deferred, not rejected**, exactly as in DEC-012.

## Decision

**Alternatives B + C combined**, implemented in
`scripts/claim_survival_screen.py`:
- `sentence_coverage(original, rewritten, threshold)` — per-original-
  sentence best-match embedding similarity against all rewritten
  sentences (Alternative B).
- Reuses `semantic_screen.check_fact_preservation` on the full paragraph
  pair (Alternative C).
- `classify_claim_survival_label(...)` — pure decision logic combining
  both into exactly **two** states: `no_omission_signal` /
  `possible_omission_flagged`. Deliberately not three states like
  DEC-012's screen (`likely_preserved`/`needs_review`/`likely_changed`):
  this screen has no calibration evidence yet to justify a confident
  "likely_changed"-equivalent call, so it only flags for review or
  doesn't — it does not claim confidence it hasn't earned.

`scripts/apply_claim_survival_screen.py` applies this post-hoc to
paragraph_* categories only, same pattern as
`apply_automated_screen.py`.

## Why

Because the failure mode is specifically about a *particular original
sentence* having no counterpart, a per-sentence signal is the direct fit
— an aggregate signal (DEC-012's whole-paragraph similarity) is provably
the wrong tool for this specific failure by construction, not just by
observation.

## Evidence

**Threshold, disclosed as preliminary, not invented from a full
calibration set**: `DEFAULT_SENTENCE_COVERAGE_THRESHOLD = 0.45`, chosen
conservatively — below the 0.63–0.73 range of genuine same-claim
paraphrase best-match similarities measured directly against this
project's own real paragraph data (`DB12BA4206B8`'s human vs. light-
controlled paragraph pair, EXP-DATA-001-R2). Unlike DEC-012's threshold
(calibrated against 35 samples spanning both classes), **this threshold
has not been validated against any confirmed true-positive omission
case** — no real paragraph pair with a definite dropped sentence exists
in this project's data yet. This is stated plainly, not hidden: the
number is a reasoned starting point, not a fitted value.

**A real, disclosed measurement problem was found and fixed while
building this screen**: testing this signal against `DB12BA4206B8`
(the one real sample manually labeled `"changed"` for claim omission)
initially appeared to reproduce a coverage drop — but investigation
found this was an artifact of `extract_span_pair`'s paragraph-level text
reconstruction, which truncated the rewritten paragraph when sentences
merged (see DEC-012's "Out-of-Sample Validation" section for the full
description and fix). After fixing that extraction bug, re-testing
against `DB12BA4206B8` with the corrected full-paragraph text shows
**no coverage drop** (all four original sentences score 0.63–0.73
against their best rewrite match) — i.e. on direct re-inspection, this
specific historical sample's "prisoners and volunteers" claim reads as
preserved in the text currently on disk, not dropped. The
`DB12BA4206B8` record itself was **not modified** (frozen, per
instruction). Net honest conclusion: **this screen has not yet been
tested against any known-good true-positive case** — the fresh
EXP-DATA-001-R3 paragraph claim-survival experiment is designed
specifically to provide that test.

**Known false-positive behavior, found directly while writing this
screen's tests**: the fact-check component (Alternative C) flags
ordinary time-of-day rewording ("until 9pm" → "until 9 at night",
"later in the evening" → "at night") because spaCy tags these as TIME
entities. This is the same class of issue documented in DEC-012 (numeric/
quantity-like phrase false positives) but was found here to extend more
broadly to temporal phrasing. See
`scripts/tests/test_claim_survival_screen.py::test_run_claim_survival_screen_fact_check_false_positive_on_reworded_time_phrase`.

## Validation Results (EXP-DATA-001-R3, 2026-08-13)

12 fresh seeds, `paragraph_light_controlled`/`paragraph_moderate_controlled`
(24 records), light and moderate reported separately throughout:

- **Light**: 9/12 preserved, 2/12 changed, 1/12 questionable.
- **Moderate**: 8/12 preserved, 1/12 changed, 3/12 questionable.

**What the sentence-coverage signal correctly caught**: 1 genuine claim
drop (`62AA2FDC41C6__paragraph_moderate_controlled` — the "more focused"
claim disappears with no counterpart in the rewrite) — a real
true-positive, `dropped_sentences=1`, matching the manual review finding
exactly.

**What it missed** (2 of the 3 `"changed"` samples this round):
- `1F8012FFBEBE__paragraph_light_controlled` — a stated-priority
  *reversal*, not a dropped claim; every original sentence still has a
  plausible best-match rewritten sentence (the reversal is a meaning
  flip within a structurally similar sentence, the same class of failure
  DEC-012 already documented at the whole-span level for numeric
  substitution — this screen has no mechanism for detecting a reversal
  when both original and rewritten sentences are otherwise fluent
  paraphrases of each other).
- `62AA2FDC41C6__paragraph_light_controlled` — a claim drop merged
  together with a location/mechanism flip in the *same* rewritten
  sentence (the model compressed two original claims into one garbled
  sentence); the merged sentence still shares enough vocabulary with
  both original sentences to score above the coverage threshold for at
  least one of them, so no drop was registered.

**Also observed, a false-positive-by-coincidence**: the one severe
`"changed"` sample this round with a real content problem
(`80664125F8D0__paragraph_moderate_controlled`, a narrator-identity
swap — the essay's speaker flips from student to teacher mid-paragraph)
*was* flagged `possible_omission_flagged`, but only because the
fact-check component happened to catch an unrelated date-phrasing
mismatch ("every two days"/"this years") in the same paragraph — not
because either signal detected the identity swap. Recorded honestly:
this is a flag that happened to be right, not a signal that worked as
intended.

**Conclusion**: this screen, as designed, targets *coverage* gaps
(a claim disappearing entirely) and does this reasonably well when that
specific failure occurs cleanly. It has **no mechanism** for the two
failure types that actually dominated this round's real `"changed"`
samples — meaning/priority reversal, and claim-drop-merged-with-flip
inside a single garbled sentence. This is consistent with, and now
directly evidences, DEC-012's own theoretical gap (see DEC-012's
"Second Out-of-Sample Validation" section) — both screens share the same
blind spot: neither can detect a meaning change that preserves
vocabulary/structure closely enough to score high on cosine similarity.

## Trade-offs

Same core trade-off as DEC-012: conservative by design (flags more than
it needs to, to avoid missing a real omission), which means a real,
elevated `possible_omission_flagged` rate is expected and does not by
itself mean the paragraph mechanism is failing — every flagged and
unflagged sample alike still goes through full manual review during
validation. Additionally, and unlike DEC-012, this screen's threshold
carries genuinely less evidence behind it — it should be treated as
more provisional than DEC-012's until EXP-DATA-001-R3's manual review
results are compared against it.

## Consequences

Positive:
- Directly targets a failure mode (dropped sentence-level claims) no
  existing signal (structural QC or DEC-012's screen) is built to catch.
- Surfaced and fixed a real bug in shared extraction code
  (`extract_span_pair`) that also affects DEC-012's paragraph-level
  screening, benefiting both screens going forward.

Negative:
- Threshold is not yet calibrated against a real true-positive case —
  higher uncertainty than DEC-012's screen.
- Fact-check false-positive rate on temporal phrasing is real and will
  inflate `possible_omission_flagged` counts for essays that discuss
  times/schedules (common in school-policy argumentative essays, this
  project's actual corpus domain) — expected to be a substantial
  fraction of flags, not a rare edge case.
- Adds a second post-hoc apply script and two more advisory fields per
  paragraph record, increasing pipeline surface area.

## Revisit When

1. ~~EXP-DATA-001-R3's paragraph claim-survival experiment provides real
   manual-review outcomes to compare against this screen's flags~~ —
   **done, 2026-08-13**: see "Validation Results" above. The threshold
   itself was not shown wrong (the one clean coverage-drop case was
   caught correctly); the *concept* — coverage-only — was shown
   insufficient for reversal/merge-type drift. A future revision should
   consider a signal that compares CLAIM DIRECTION (e.g. sentiment/
   polarity of the matched pair), not just whether a match exists, to
   catch reversals — not designed here, flagged for future work.
2. If the temporal-phrase false-positive rate proves too disruptive at
   scale, consider excluding TIME-labeled entities from the fact-check
   component specifically for this screen (not for DEC-012's, unless the
   same evidence emerges there) — not done now because it would be an
   unevidenced threshold change made to reduce noise, which this
   project's discipline forbids without data.
3. Never: promote `no_omission_signal` to mean "confirmed preserved" —
   it means "no flag raised," not "checked and cleared." **Directly
   confirmed necessary, 2026-08-13**: two real `"changed"` paragraph
   samples this round were `no_omission_signal`.

## Implementation

`scripts/claim_survival_screen.py`, `scripts/apply_claim_survival_screen.py`.
Bug fix in `scripts/apply_automated_screen.py`'s `extract_span_pair`
(paragraph-level text reconstruction), which this screen's development
surfaced and which also benefits DEC-012.

## Tests / Experiments

`scripts/tests/test_claim_survival_screen.py` (11 tests: 4 pure
classification-logic tests, 7 real model-backed tests including the
`DB12BA4206B8` regression/documentation test and the time-phrase
false-positive test). `scripts/tests/test_apply_automated_screen.py` (3
tests covering the `extract_span_pair` bug fix). Validation:
EXP-DATA-001-R3 (paragraph claim-survival experiment, see
[reports/EXP-DATA-001-R3.md](../../reports/EXP-DATA-001-R3.md)).
