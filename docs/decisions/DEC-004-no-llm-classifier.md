# DEC-004 — Language Models Are an Instrument, Never the Classifier

## Status
Accepted

## Date
2026-08-10

## Context

The most common naive way to build an "AI detector" is: send the essay to
a large language model and ask "is this AI-written?" This is explicitly
rejected by the project brief (Sections 2 and 43), and independently, it
is a poor design for an explainable, evaluable system: the verdict comes
from an opaque model call, there is no measurable feature behind it, it
cannot be calibrated against a reference distribution, and it cannot be
evaluated with reproducible metrics — a different phrasing of the prompt
or a model version change silently changes results.

## Problem

How should any language model be used in this system, if not to classify?

## Alternatives Considered

### Alternative A: LLM-as-classifier ("Is this essay AI-written? Answer
with a percentage.")
Advantages:
- Trivial to implement, no feature engineering required.

Disadvantages:
- Not explainable: no measurable feature backs the number.
- Not reproducible: sensitive to prompt wording and model version.
- Cannot show sentence-level evidence honestly (would require asking the
  LLM to fabricate a rationale after the fact, i.e. fake explainability —
  explicitly disallowed, Section 19).
- Cannot be calibrated against a reference distribution.
- Explicitly rejected by the project brief.

### Alternative B: Remote LLM API used only for token-probability
extraction (e.g. via an API that exposes logprobs)
Advantages:
- Larger models than what runs locally, potentially better-calibrated
  probabilities.

Disadvantages:
- Introduces a paid external dependency and a network requirement,
  contradicting Section 3 ("run locally without requiring a paid external
  API," "prefer local inference").
- Nondeterministic availability/versioning outside our control.

### Alternative C: Local causal LM used purely as an instrument
(token log-probabilities, perplexity, predictability/burstiness), feeding
our own feature-based scoring system.
Advantages:
- Runs fully locally, no API cost or network dependency.
- Produces genuinely measurable, numeric features (log-prob, perplexity)
  that can be compared against reference distributions and shown to the
  user as evidence.
- The final classification is produced by our own scoring/calibration
  code, which is inspectable and testable — not a black-box verdict.

Disadvantages:
- A small local model (e.g. distilgpt2) is weaker than a large hosted
  model, so its probability estimates are noisier. This is a real
  limitation to document (docs/methodology.md, docs/failure-analysis.md),
  not to hide.

### Alternative D: No language model at all — purely handcrafted
linguistic/statistical features (sentence rhythm, vocabulary, repetition,
POS patterns).
Advantages:
- Fully local, fully interpretable, no model-loading cost.

Disadvantages:
- Discards a category of signal (predictability/perplexity) that the
  brief explicitly asks us to investigate (Section 6A) and that prior AI-
  text-detection literature treats as informative. Rejecting it outright
  without testing it would be a decision made without evidence, which the
  brief also disallows (Section 27).

## Decision

Use a small local causal language model strictly as a feature-extraction
instrument (log-probabilities, perplexity, burstiness). All classification,
scoring, and explanation generation is done by our own code against
reference distributions built from our dataset. No LLM (local or remote)
is ever asked to produce a verdict, a percentage, or a natural-language
explanation of why a sentence was flagged.

## Why

This is the only alternative that satisfies all real constraints
simultaneously: local/no paid API (Section 3), explainability with
measurable evidence (Sections 5, 19), and not discarding a plausibly
useful signal without testing it (Section 27). Alternative D remains a
fallback: if the local LM's signal turns out not to be useful once
measured (Phase 4/5 experiments), the architecture already supports
scoring without it, since it's one feature group among several (Section
6).

## Evidence

**Updated 2026-08-15 — EXP-003A executed** (see
[EXP-003.md](../experiments/EXP-003.md) §0 for how this project's two
experiment-numbering schemes reconcile; [reports/EXP-003A.md](../../reports/EXP-003A.md)
for full results). On the human-vs-full_ai task (298 essays,
PRIMARY-DATASET-v1): stylometric-only features reached 100% validation
accuracy; the combined (stylometric + LM) model also reached 100%; every
ablation removing LM features stayed at 100%. **The LM feature group
showed no measurable improvement over linguistic-only features — the
condition this decision's "Revisit When" names, below, has been met
once.** This does not by itself mean the LM feature group should be
dropped project-wide: EXP-003B (human vs. `ai_assisted`, a much harder,
single-sentence-edit task where whole-essay stylometric signal may be
far weaker) has not yet run, and is the more realistic test of whether
predictability-based features matter.

**Updated 2026-08-15 — EXP-003B executed** (see
[reports/EXP-003B.md](../../reports/EXP-003B.md)). Result is **mixed,
not a clean answer either way**: at the essay level, every feature
group (including LM-only and combined) performed at chance — no signal
of any kind, so the stylometric-vs-LM question is not meaningfully
answerable there. At the **sentence-level localization** task, an
LM-derived feature (`lm_mean_token_count`) was the single largest-
magnitude coefficient in the combined model — but this specific
feature is arguably more a length/token-count proxy than a genuine
LM-instrument (perplexity/predictability) signal, and a proper
LM-only-vs-stylometric-only threshold-swept comparison at the sentence
level was **not run** (EXP-003B §11 — both baselines collapse
identically at the default 0.5 threshold given ~8% positive
prevalence, making that specific comparison uninformative as reported).
**Net conclusion: still open.** The LM feature group has not
demonstrated clear value in either experiment so far, but EXP-003B's
one suggestive signal (token-count) and its own disclosed gap (no
swept-threshold ablation at the sentence level) mean this is not yet a
confident "drop it" conclusion either — see Revisit When.

Before this: no experiment — this is a foundational constraint fixed
before any feature-quality measurement was possible. This decision
fixes *how* the LM may be used, not whether its output ends up
mattering — that question now has a first, partial answer above.

## Trade-offs

We give up the (illusory) simplicity of an LLM-as-judge approach, in
exchange for an implementation that requires real feature engineering,
reference-distribution construction, and calibration work before it
produces any classification at all.

## Consequences

Positive:
- Every number shown to the user is traceable to a computed feature.
- The system can be evaluated with standard metrics (precision/recall/F1)
  because its output is deterministic given fixed model weights and code,
  not a live LLM call.

Negative:
- More upfront engineering effort than an LLM-wrapper approach.
- Local model quality ceiling — documented as a limitation, revisited if
  evidence (EXP-003 and later) shows the signal is too weak to be useful.

## Revisit When

~~If EXP-003 shows local-LM-derived features (perplexity, log-prob
variance) provide no measurable improvement over linguistic-only
features on validation F1, in which case the LM feature group would be
dropped~~ — **partially triggered, 2026-08-15**: true for EXP-003A
(human vs. full_ai) specifically. **Not yet acted on**: whether to
actually drop the LM feature group is deferred until EXP-003B (human
vs. `ai_assisted`) also runs — a single-sentence edit inside an
otherwise-human essay is a materially different, harder detection
problem where whole-essay stylometric signal is expected to be much
weaker, and where a predictability-based signal (comparing one sentence
against its neighbors) is plausibly more relevant than it was for
whole-essay full_ai detection. **Never**: the local-only-instrument
principle itself (DEC-004's actual hard constraint) is not affected
either way — only whether the LM feature *group* stays in the
detector's feature set is in question, not whether an LM may ever be
used as a classifier.

**Updated 2026-08-15**: EXP-003B ran; result is inconclusive rather than
a clean trigger either direction (see Evidence above). **Next step, not
yet done**: a threshold-swept stylometric-only vs. LM-only comparison
at the sentence level specifically (EXP-003B's own disclosed gap) would
give a real answer where the current all-or-nothing 0.5-threshold
comparison could not. Until that exists, the LM feature group is
neither confirmed useful nor confirmed droppable at the sentence level
— status stays open, not resolved by assumption in either direction.

**Updated 2026-08-15 — EXP-003B-R1 executed** (see
[reports/EXP-003B-R1.md](../../reports/EXP-003B-R1.md)), specifically
to close the gap named above: a threshold-swept comparison isolating
length/count features from genuine LM predictability features. Result:
**LM-only localization (13.3% top-1 test accuracy) is the weakest of
five feature groups tested — notably worse than non-LM stylometric
features alone (40.0%)**, and `lm_mean_token_count` (EXP-003B's
top-magnitude coefficient) is now understood as a length/count effect,
not evidence the LM instrument's actual predictability signal is
useful. **This is a second, independent data point consistent with
DEC-004's standing skepticism, but is still not treated as conclusive**
(one specific feature-classification scheme, small sample, one
generation mechanism) — status remains open, not marked Rejected. The
LM feature group's most defensible current status:
plausible-but-unconfirmed-useless for AI-assistance detection at both
essay level (EXP-003A/B) and sentence level (EXP-003B-R1) on this
benchmark so far.

**Updated 2026-08-15 — EXP-003C executed** (see
[reports/EXP-003C.md](../../reports/EXP-003C.md)), a third,
independent design: three-class essay-level classification. Result:
**combined and stylometric-only feature groups are identical on
validation** (same accuracy 67.7%, same macro-F1 0.559, same chosen
regularization strength) — the LM group added literally zero
measurable difference here, not just a small one. This is now three
separate experimental designs (EXP-003A essay-level binary, EXP-003B-R1
sentence-level binary, EXP-003C essay-level three-class) all finding no
LM contribution. **Still not marked Rejected** — same standing caveats
apply (single generation mechanism, small samples, one feature-
classification scheme for the length/count split) — but the
consistency across three independent designs is itself now a notable
pattern, not just three individually-inconclusive data points taken in
isolation.

## Implementation

To be added in Phase 4: `backend/app/services/language_model.py`.

## Tests / Experiments

To be added: `experiments/EXP-003-token-probabilities/`.
