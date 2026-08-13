# DEC-012 — Automated Semantic-Preservation Screening Signal

## Status
Accepted **as an automated semantic-risk screening / triage tool** —
explicitly **NOT** a semantic safety gate. Calibrated against real data,
not invented thresholds. **Reframed 2026-08-13 (post-R3 strategic
review) — see "Reframing" immediately below for why the "safety gate"
framing used in earlier versions of this document is retired.**

## Reframing (2026-08-13, post-R3 strategic review): triage, not a safety gate

Earlier versions of this decision (and of `decision-summary.md`,
`project-status.md`) described this screen's calibration result as a
**"safety property"** — "0 changed samples mislabeled likely_preserved."
That framing is retired as of this update. It was accurate for what had
been tested at the time, but "safety property" implies a guarantee this
screen was never shown to provide in general, only within the specific
failure mode (numeric/entity substitution) tested so far.
EXP-DATA-001-R3 showed the framing was misleading going forward: **2 of
3 real `"changed"` paragraph samples were labeled `likely_preserved`**
by this screen. Stated plainly, for the record:

- **What remains true**: numeric/entity substitutions are well detected
  — 0 missed across calibration (0/8), EXP-DATA-001-R2 out-of-sample
  (0/5), and EXP-DATA-001-R3 sentence-light (0/1). This is a real,
  repeated, useful result.
- **What is now a documented, known blind spot, not a hypothetical
  one**: **meaning reversal** (a structurally-similar, fluent rewrite
  that states the opposite of the original) is not detected — 2/2 such
  cases in EXP-DATA-001-R3 were missed.
- **What is also a documented, known blind spot**: **claim omission**
  merged inside a garbled, multi-claim sentence is not reliably detected
  by either this screen or DEC-013's coverage signal — 1 case in
  EXP-DATA-001-R3 was missed by both.
- **What is also documented**: `"questionable"`-tier drift can pass this
  screen — observed in calibration (1/4) and in EXP-DATA-001-R2's
  out-of-sample validation (2/4); not the primary finding of R3, but not
  resolved by R3 either.

**This screen's role going forward is triage — prioritizing which
samples most need human attention — never a substitute for reviewing
every sample that will enter a high-confidence dataset.** See DEC-011's
"Strategic Decision" section: every sample entering the primary mixed
dataset must independently pass human semantic review regardless of
this screen's label.

## Date
2026-08-13

## Context

EXP-DATA-001-R1-confirmation found that structural QC (length ratio,
resegmentation) does not catch semantic drift: 4 sentence-level samples
passed every automated structural check while a manual reviewer judged
them `"changed"` (e.g. "at least one C" rewritten as "two Cs"; a specific
grievance replaced by an unrelated generic sentence). See
[reports/EXP-DATA-001-R1-confirmation.md](../../reports/EXP-DATA-001-R1-confirmation.md)
and [DEC-011](DEC-011-mixed-text-generation.md).

Manual review alone doesn't scale, but per explicit instruction and
DEC-004's precedent, **no model may set final semantic-preservation
ground truth** — that would just relocate the same LLM/model-as-judge
problem to a different part of the pipeline. What's needed is a
screening signal: something automated that prioritizes which samples
need human attention, without ever being trusted on its own.

## Problem

What automated signal(s), if any, should screen for semantic drift
before/alongside human review, and how should its threshold(s) be set?

## Alternatives Considered

### Alternative A: Embedding-based semantic similarity alone
Cosine similarity between sentence-embedding vectors of the original and
rewritten span.

Advantages: cheap, fast, well-established technique for paraphrase
detection; catches "completely different topic/claim" drift reliably
(verified: unrelated-sentence pairs score <0.3 in this project's own
tests).

Disadvantages: **does not reliably catch small factual substitutions
inside an otherwise structurally-similar sentence.** Verified directly:
"Students should have at least one C..." vs "...at least two Cs..."
(the actual confirmation-round failure case) scores 0.87 similarity in
isolation — high enough that almost any reasonable threshold would have
called it "preserved." Embedding similarity is not sensitive to number/
entity substitution when the surrounding sentence structure barely
changes.

### Alternative B: NLI/entailment-style comparison
Use a natural-language-inference model to check whether the original and
rewritten spans mutually entail each other (a common paraphrase-detection
technique).

Advantages: more linguistically principled than raw embedding distance;
specifically trained to detect contradiction, which factual substitution
often is.

Disadvantages: requires downloading and maintaining a second, different
model class beyond what this project already uses; adds real complexity
(3-way entailment/neutral/contradiction output needs its own calibration)
for a benefit that, on inspection, substantially overlaps with what
Alternative C (below) catches more cheaply and more interpretably for
the *specific* failure modes actually observed in this project's data
(numeric/entity substitution). **Deferred, not rejected outright** — if
Alternative C's fact-based check proves insufficient at larger scale
(e.g. drift that changes a causal relationship or the author's stated
position without touching any number or named entity), NLI is the
natural next signal to add.

### Alternative C: Entity/number preservation check
Extract numbers and named entities (via the same spaCy pipeline already
used for segmentation, DEC-005 — no new model) from both spans; flag if
the original's numbers/entities are missing or changed in the rewrite.

Advantages: directly, cheaply, and interpretably catches the exact
failure mode already observed in real data ("one C" → "two Cs"); no new
model dependency; output is a plain, auditable list of what
changed/vanished, not an opaque score.

Disadvantages: **real false-positive rate** — spaCy's NER on short spans
sometimes tags ordinary phrases ("regular hours", "school hours") as
quantity-like entities, flagging faithful paraphrases as suspicious (see
Evidence). Also a real false-negative risk in principle: a genuinely
altered claim that happens to preserve all its numbers/entities (e.g. a
changed causal relationship with no numbers involved) would not be
flagged by this check alone.

### Alternative D (chosen): Combine B... (rather: combine A + C), fact-flag always escalates to review
Use embedding similarity (Alternative A) for broad "different
claim/topic" drift, plus the fact-preservation check (Alternative C) for
precise numeric/entity substitution, combined so that **a fact-check flag
always escalates to human review regardless of how similar the
embeddings look** — directly closing Alternative A's blind spot rather
than averaging the two signals into one number that could still miss the
"one C"/"two Cs" case.

## Decision

Implement `scripts/semantic_screen.py`:
- `embedding_similarity(original, rewritten)` — cosine similarity via
  `sentence-transformers`' `all-MiniLM-L6-v2` (a small, standard,
  CPU-fast paraphrase-similarity model — new dependency, justified below).
- `check_fact_preservation(original, rewritten)` — numbers/entities via
  the existing spaCy pipeline (no new model).
- `classify_screen_label(...)` — pure decision logic combining both into
  `likely_preserved` / `needs_review` / `likely_changed`. A fact-check
  flag always forces `needs_review`, regardless of similarity score.

**Thresholds calibrated against real data, not invented**: run against
all 35 EXP-DATA-001-R1-confirmation samples with a resolvable span pair
and an existing manual label
(`scripts/calibrate_semantic_screen.py`). Chosen:
`preserved_threshold=0.75`, `review_band=0.35` (so `<0.40` = likely
changed, `[0.40, 0.75)` = needs review, `>=0.75` = likely preserved,
unless fact-flagged).

## Why

At these calibrated values, **0 of 8 real `"changed"`-labeled samples
would have been classified `likely_preserved`** — the property that
actually matters for a screening tool (never give false confidence to a
bad sample). This came at a real cost: only 6 of 23 `"preserved"`
samples were confidently auto-passed; the other 17 fell into
`needs_review` despite being fine. That's an accepted trade-off for a
*screen*, not a *classifier* — see Trade-offs.

## Evidence

`scripts/calibrate_semantic_screen.py` output (2026-08-13), 35 samples
with resolvable spans and manual labels:
- `changed` (n=8): similarities `[0.11, 0.16, 0.22, 0.24, 0.35, 0.43,
  0.63, 0.63]` — the two highest (0.43, 0.63) were both caught by the
  fact-check flag (missing "one"/"at least one" numbers, or a missing
  named entity), not by similarity alone.
- `preserved` (n=23): similarities `[0.44, 0.51, 0.57, 0.63, 0.64, 0.65,
  0.65, 0.73, 0.75, ..., 0.98]` — substantial overlap with the
  `changed` range at the low end, confirming embedding similarity alone
  cannot cleanly separate the classes.
- `questionable` (n=4): similarities `[0.45, 0.68, 0.70, 0.84]` — one
  (0.84, not fact-flagged) would be classified `likely_preserved`, a
  **known, documented miss** (see Trade-offs).

**Known false positives** (fact-check flags a faithful paraphrase):
observed directly — "school hours" vs "regular hours" and similar
near-synonym phrases were tagged as mismatched quantity-like entities by
spaCy's NER on short spans. This inflates the `needs_review` rate but
never causes a false `likely_preserved`.

**Known false negatives**: (1) one `questionable` sample (embedding
similarity 0.84, no fact-flag) would screen as `likely_preserved`. (2)
By construction, a claim change that alters no number or named entity
(e.g. a changed causal relationship or reversed stance) could in
principle score high similarity and pass no fact flag — not observed in
this calibration set, but not proven absent either; this is exactly the
gap Alternative B (NLI) would target if it recurs.

## Out-of-Sample Validation (EXP-DATA-001-R2, 2026-08-13)

Per explicit review instruction, this screen's behavior must be
documented plainly and not have its claims expanded beyond observed
evidence. Restated precisely, with exact set sizes:

- **Calibration set: 35 samples** (EXP-DATA-001-R1-confirmation, with a
  resolvable span pair and an existing manual label) — used to choose
  `preserved_threshold=0.75`, `review_band=0.35`. See Evidence above.
- **Out-of-sample validation set: 37 samples** (EXP-DATA-001-R2, both the
  sentence and paragraph batches combined — 19 sentence-level + 18
  paragraph-level reviewed samples) — a genuinely separate batch, fresh
  seeds, generated and reviewed *after* the thresholds were fixed. The
  thresholds were **not** re-tuned against this set.
- **Result: 0/5 "changed" samples labeled `likely_preserved`** — the
  safety property held out-of-sample, not just on the calibration set.
  (`1DD5B206DC55__sentence_moderate_controlled_v2` →
  `likely_changed`; the other four → `needs_review`.)
- **Result: 2/4 "questionable" samples slipped through as
  `likely_preserved`** —
  `E83EAE114F13__sentence_light_controlled_v2` and
  `BCEF4D5FF6AB__paragraph_moderate_controlled`. This is the same known
  limitation observed in calibration (there, 1/4 slipped through), now
  confirmed to recur out-of-sample at a similar rate. **Correction to an
  earlier stated figure**: this project's code comments previously said
  "1/4" when referring to this out-of-sample batch — that was the
  calibration-set number, restated in the wrong place. The correct
  out-of-sample figure, verified directly against
  `data/generated/EXP-DATA-001-R2-{sentence,paragraph}/samples.jsonl`
  on 2026-08-13, is **2/4**. Fixed in `semantic_screen.py`'s comment.

**What this screen can detect** (validated, both in calibration and
out-of-sample): precise numeric/entity substitution inside an otherwise
structurally-similar rewrite, and broad "different claim/topic" drift
where the embedding similarity itself drops.

**What this screen cannot yet be trusted to detect** (disclosed
limitation, not a hidden gap): subtle, "questionable"-tier drift —
framing or specificity shifts that touch no number or named entity and
don't move the embedding similarity far enough to leave the
`likely_preserved` band. Both the calibration set and the out-of-sample
validation set show this same miss rate. **Requirement, not a
suggestion**: any sample this screen marks `likely_preserved` still
underwent full manual review in every validation round run so far — this
screen has never been used to skip human review, only to prioritize it.

## Second Out-of-Sample Validation (EXP-DATA-001-R3, 2026-08-13) — safety property broken for the first time

**Reported plainly, not softened.** EXP-DATA-001-R3's paragraph
claim-survival experiment (12 fresh seeds, `paragraph_light_controlled`/
`paragraph_moderate_controlled`) found **2 of 3 `"changed"` samples in
this batch were labeled `likely_preserved`** by this screen:
`1F8012FFBEBE__paragraph_light_controlled` (a motivation/priority
reversal: the rewrite states the *opposite* of what the student promised
to prioritize) and `62AA2FDC41C6__paragraph_light_controlled` (a dropped
claim plus a location flip, "texting done AT school" → "access...
OUTSIDE of school"). Both scored high embedding similarity with no
fact-check flag (no number or named entity was touched), so both cleared
the `likely_preserved` threshold cleanly. The third `"changed"` sample in
this batch (`80664125F8D0__paragraph_moderate_controlled`, a narrator-
identity swap — the essay's first-person narrator flips from student to
teacher mid-paragraph) *was* labeled `needs_review`, but for an unrelated
reason (a fact-check false positive on date/frequency phrasing, "every
two days"/"this years") — not because either signal detected the
identity swap itself.

**This is exactly the gap this decision's Evidence section already
named as theoretical and unconfirmed**: *"a claim change that alters no
number or named entity... could in principle score high similarity and
pass no fact flag — not observed in this calibration set, but not proven
absent either."* It is now observed, directly, on real data. The
sentence-level out-of-sample validation this same round
(EXP-DATA-001-R3-sentence-light, 25 fresh seeds) did *not* show this
failure — its one `"changed"` sample (a "70"→"80" numeric substitution)
was correctly caught via the fact-check component, consistent with every
prior round. **The safety property has held for every numeric/entity
substitution seen so far, across all three validation rounds. It has now
failed, specifically and only, for claim/causal/position reversals that
touch no number or entity** — a paragraph-level phenomenon not yet
observed at the sentence level, though absence-of-evidence there is not
evidence of absence.

**Consequence for this project's Final-Dataset Policy**: this result is
why human review of paragraph-level samples cannot be treated as
optional or skippable based on this screen's `likely_preserved` label —
that was already the stated rule (DEC-012's Trade-offs, DEC-013's
Consequences), and this round is direct, concrete evidence for why the
rule exists, not a hypothetical.

**Known issue found while building the related claim-survival screen
(2026-08-13, see [DEC-013](DEC-013-claim-survival-screen.md))**: the
`extract_span_pair` helper (`apply_automated_screen.py`) that supplies
this screen's `(original, rewritten)` input pair for paragraph_*
categories reconstructed `rewritten` from `modified_spans` character
offsets. When a rewrite merges two original sentences into one, the
resegmented `modified_spans` range can cover only *part* of the new
paragraph, silently truncating the text this screen actually compares.
Confirmed directly on `DB12BA4206B8__paragraph_light_controlled`: the
truncated extraction dropped the merged opening sentence entirely.
**Fixed 2026-08-13** for paragraph categories (now splits both texts by
paragraph index instead of reconstructing from offsets — splicing only
changes characters within one paragraph, so paragraph boundaries
elsewhere are unaffected by construction). **Not retroactively applied
to EXP-DATA-001-R2's already-reported `automated_screen_*` values** —
those are frozen, historical, per explicit instruction not to
regenerate prior evidence. This means the R2 paragraph batch's
already-reported screen numbers above should be read with this caveat:
some paragraph samples' screen inputs may have been truncated in a way
the numbers above don't reflect. The fix applies going forward, starting
with EXP-DATA-001-R3.

## Trade-offs

This screen is deliberately **conservative**: it minimizes false
`likely_preserved` at the cost of a high `needs_review` rate (17/23
genuinely-preserved samples still required human review in calibration).
That is the correct failure direction for a screening tool feeding into
dataset construction, but it means this signal **reduces**, rather than
eliminates, human review workload — it is not a replacement for it.

## Consequences

Positive:
- A concrete, calibrated-not-invented way to prioritize review effort.
- The specific failure mode already found in real data (numeric/entity
  substitution) is now caught with a documented, near-zero false-negative
  rate in this calibration set.

Negative:
- New dependency (`sentence-transformers`, ~80MB model download).
- Real, non-trivial false-positive rate on the fact-check component —
  must not be silently "fixed" by loosening it in a way that reopens the
  false-negative risk it exists to close.
- Does not address claim/stance/causal-relationship changes that don't
  touch a number or entity — an acknowledged gap, not a hidden one.

## Revisit When

1. If the sentence-level validation experiment (using this screen on a
   fresh sample) finds a similar or worse false-negative rate, the
   thresholds — or the decision to rely on embedding similarity + fact
   checks at all, rather than adding NLI (Alternative B) — should be
   revisited with that new evidence.
2. ~~If claim/stance-reversal drift (not caught by either current
   signal) is observed directly, escalate to Alternative B~~ —
   **triggered, 2026-08-13**: EXP-DATA-001-R3 observed exactly this (2
   paragraph-level samples, priority reversal and a claim-drop-plus-
   location-flip, neither touching a number or entity). NLI (Alternative
   B) is now a live candidate to evaluate, not just a deferred option —
   not implemented in this round per the explicit instruction not to
   scale or add new mechanisms beyond what was authorized; a future
   round should evaluate it against these two real failure cases plus
   the DB12BA4206B8-family cases.
3. Never: loosen the fact-check flag's escalation-to-review behavior
   just to reduce the `needs_review` rate — that would reopen the exact
   gap this decision closes.

## Implementation

`scripts/semantic_screen.py`, `scripts/calibrate_semantic_screen.py`.

## Tests / Experiments

`scripts/tests/test_semantic_screen.py` (11 tests: 7 pure classification-
logic tests, 4 real model-backed tests including a direct reproduction of
the "one C"/"two Cs" confirmation-round failure case). Calibration
evidence: `data/generated/semantic_screen_calibration.json` (generated
from real, already-reviewed data — not synthetic).
