# Methodology

> Status: Phase 3 (linguistic features) and Phase 4 (LM instrumentation)
> are implemented (see [project-status.md](project-status.md)). The
> human corpus needed for Section 5 (reference distributions) has now
> been acquired, live-license-verified, and inspected — see
> [dataset.md](dataset.md) and
> [reports/dataset-inspection.md](../reports/dataset-inspection.md) — but
> no reference distribution, scoring, or calibration exists yet, so
> sections 5–10 below remain unwritten. Sections 3–4 are filled in; treat
> the rest as reserved structure, not implemented behavior.

## 3. Feature engineering (Phase 3 — implemented, provisional)

`backend/app/services/feature_extractor.py` computes, per sentence: word/
character/punctuation counts, average word length, POS ratios (noun,
verb, adjective, adverb, pronoun), and maximum dependency-tree depth. Per
essay: sentence-length mean/std/coefficient-of-variation, a short/medium/
long sentence-length distribution, type-token ratio, a windowed moving-
average type-token ratio, a rare-word ratio (via the `wordfreq` library's
Zipf-scale frequency data), and three repetition measures (repeated
bigrams, repeated trigrams, repeated sentence openings).

This is explicitly a **provisional** set (DEC-006): each feature is a
standard, literature-grounded stylometric measure, but none has been
tested yet against real human/AI-written text, because that requires the
Phase 5 dataset. **What the system measures** (the numbers above) is
therefore already true; **what the system infers** from them (whether any
of this indicates AI involvement) is not yet defined — that is Phase 6's
scoring/calibration work, informed by EXP-002 once Phase 5 exists.

## 4. Language-model instrumentation (Phase 4 — implemented, provisional)

`backend/app/services/language_model.py` loads a small local causal LM
(`distilgpt2`, [DEC-007](decisions/DEC-007-local-language-model-choice.md))
once per process and scores the whole normalized essay in a single
teacher-forced forward pass (chunked only if the essay exceeds the
model's 1024-token context window). Each token's log-probability is
attributed back to its containing sentence by character offset, per
[DEC-008](decisions/DEC-008-lm-scoring-method.md) — chosen over scoring
each sentence in isolation specifically so predictability is measured
*given the essay's actual preceding context*, not in a vacuum.

From this, per sentence: mean and median token log-probability,
log-probability variance, and perplexity (`exp(-mean_log_prob)`). Across
sentences: the change in mean log-probability from one sentence to the
next (Section 6A's "predictability burstiness" / "change in
predictability between neighboring sentences").

**What this does and does not tell us:** these are measurements of how
surprising a sequence of tokens is *to this specific small model*, not a
direct measurement of "AI-ness." A low perplexity sentence is one
distilgpt2 finds unsurprising — that could mean simple/formulaic phrasing
(human or AI), a topic the model's training data covered well, or genuine
machine generation. Section 6A's explicit warning — "Do not assume low
perplexity = AI" — applies fully here. Turning these numbers into a
classification requires comparing them against reference distributions
built from labeled data (Phase 5/6), which does not exist yet. As with
Phase 3's features, this feature category is provisional until EXP-003
measures its actual signal.

A sentence whose only tokens fall in a context-free position (only
possible for a very short first sentence of the whole essay) has no
scorable tokens; its LM features are reported as unavailable (`None`)
rather than a fabricated value — consistent with the project's
"insufficient evidence" principle (Section 8).

## Purpose of this document

Once implemented, this document must clearly separate:

- **What the system measures** — concrete, computed quantities (e.g.
  mean token log-probability, sentence-length coefficient of variation).
- **What the system infers** — a classification derived from comparing
  those measurements to reference distributions, with an explicit
  confidence/uncertainty level.

It must never claim that a measurement or inference *proves* authorship.
Writing style is evidence, not proof.

## Remaining planned sections (to be written in the phases noted)

1. Problem formulation — Phase 6 (what "detection" means here: a
   calibrated estimate over writing characteristics, not an authorship
   proof)
2. Hypotheses driving feature selection — ongoing (recorded per-feature in
   `experiments/`, not asserted here without an experiment behind it; see
   DEC-006 for the Phase 3 starting hypotheses)
5. Reference-distribution construction — Phase 5
6. Scoring and calibration — Phase 6
7. Sentence-level and passage-level analysis — Phase 7
8. Mixed/AI-polished text handling — Phase 7
9. Uncertainty handling ("insufficient evidence" as a valid output) —
   Phase 6
10. Evaluation methodology (metrics, splits, what counts as "correct") —
    Phase 10

Each of these sections will cite the specific `experiments/EXP-XXX/` run
that justifies the choice made, per [decisions.md](decisions.md)'s
traceability requirement — not written from first-principles reasoning
alone.
