# Methodology

> Status: **executed, 2026-08-15.** Sections 3–4 below (feature
> engineering, LM instrumentation) describe implemented, unchanged-since-
> Phase-4 code. What was "reserved structure" below at the time of
> writing is now implemented: reference distributions/scoring/
> calibration (EXP-003A/B/C's frozen logistic regression models, see
> [production-detector.md](production-detector.md)), sentence/passage-
> level analysis (EXP-003B/B-R1's sentence-localization model, see
> [evidence-mapping.md](evidence-mapping.md)), uncertainty handling (the
> `inconclusive` essay state, reserved strictly for missing-evidence
> conditions — see evidence-mapping.md §"Essay-level result states"),
> and evaluation methodology (all six experiment reports — see
> [decision-summary.md](decision-summary.md) for the quick-reference
> summary of each). **The core finding this section anticipated was
> confirmed empirically, repeatedly**: stylometric features (§3) carry
> essentially all of the measured signal; the LM-derived features (§4)
> have not demonstrated incremental value across four independent
> experimental designs (EXP-003A, EXP-003B-R1, EXP-003C, GEN-001) — see
> [decisions/DEC-004-no-llm-classifier.md](decisions/DEC-004-no-llm-classifier.md)'s
> Evidence section for the full, updated record. This section's own
> content (§3/§4) is not rewritten below — it already correctly
> described what the system measures; only the status header and the
> "remaining planned sections" list at the bottom are updated to reflect
> what has since been built.

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
perplexity = AI" — applies fully here, and is now directly evidenced,
not just anticipated: EXP-003A (2026-08-15,
[reports/EXP-003A.md](../reports/EXP-003A.md)) found this feature
category added no measurable improvement over Phase 3's stylometric
features on the human-vs-full_ai task — an LM-only model reached 79.5%
validation accuracy vs. stylometric-only's 100%, and adding these
features to the stylometric set changed nothing. Turning these numbers
into a classification requires comparing them against reference
distributions built from labeled data (Phase 5/6) — EXP-003A's frozen
logistic-regression fit is a first, narrow instance of this, not yet a
general reference distribution. Whether this feature category earns a
place in the eventual detector depends on EXP-003B's harder mixed-text
task (not yet run) — see DEC-004's "Revisit When."

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

## Where each originally-planned section ended up

| Planned section | Status | Where it actually lives |
|---|---|---|
| 1. Problem formulation | Done | [PRODUCT-AUDIT.md](PRODUCT-AUDIT.md) §4 ("Final product claim") — a calibrated statistical signal, explicitly not an authorship proof |
| 2. Hypotheses driving feature selection | Done, ongoing | [decisions/DEC-006-phase3-feature-scope.md](decisions/DEC-006-phase3-feature-scope.md) (starting hypotheses) + [decisions/DEC-014-exp003-feature-set-and-baselines.md](decisions/DEC-014-exp003-feature-set-and-baselines.md) (pre-registered feature groups) |
| 5. Reference-distribution construction | Done | EXP-003A's frozen train-split fit ([reports/EXP-003A.md](../reports/EXP-003A.md)); human-reference feature statistics specifically in `scripts/build_feature_reference_stats.py` / `backend/app/ml/feature_reference_stats.json` |
| 6. Scoring and calibration | Done | [production-detector.md](production-detector.md) — the frozen essay-level logistic regression + 0.47 threshold |
| 7. Sentence-level and passage-level analysis | Done | [reports/EXP-003B.md](../reports/EXP-003B.md), [reports/EXP-003B-R1.md](../reports/EXP-003B-R1.md), [evidence-mapping.md](evidence-mapping.md) (ranking, not per-sentence threshold) |
| 8. Mixed/AI-polished text handling | Investigated, found unreliable at essay level | [reports/EXP-003C.md](../reports/EXP-003C.md) (`ai_assisted` essay-level collapse) — not exposed as a production classifier; only sentence-level candidates are surfaced |
| 9. Uncertainty handling | Done | The `inconclusive` essay-level state (evidence-availability trigger only, never an invented score band) — [evidence-mapping.md](evidence-mapping.md) |
| 10. Evaluation methodology | Done | [decision-summary.md](decision-summary.md) (quick reference) and each `reports/EXP-*.md` / `reports/GEN-001.md` / `reports/FAIR-001.md` (full detail) |

Every choice above cites the specific `experiments/EXP-XXX/` (or
`GEN-001`/`FAIR-001`) run that justifies it, per
[decisions.md](decisions.md)'s traceability requirement — none were
decided from first-principles reasoning alone.
