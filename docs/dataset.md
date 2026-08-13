# Primary Dataset Construction Plan

**Status: DESIGN ONLY. Not executed.** Per explicit instruction, this
document specifies how the first primary benchmark dataset will be
built once authorized — no generation for this dataset has started.
Everything below is a proposal for review, not a completed action.

See [final-decision-guide.md](final-decision-guide.md) for a one-page
summary of what's in/out and why, and
[DEC-011](decisions/DEC-011-mixed-text-generation.md)'s "Strategic
Decision" section for the full reasoning this plan implements.

## 1. Included categories

| Category | Label | Mechanism | Evidence basis |
|---|---|---|---|
| Human original | `human` | Unmodified PERSUADE 2.0 essay | N/A — ground truth by definition |
| Fully AI-generated | `machine` | `full_ai` (whole-essay generation, same prompt/target length) | EXP-DATA-001: 10/10 QC-clean once the `check_instruction_leakage` false-positive bug is accounted for (the 3 flagged samples were confirmed false positives, not real leakage) |
| Controlled sentence-light AI-assisted | `ai_assisted` | `sentence_light_controlled_v2` (surgical single-sentence splice, full-paragraph context, light-copy-edit instruction) | EXP-DATA-001-R2 (9/10 preserved, 0/10 changed) + EXP-DATA-001-R3 (22/25 preserved, 1/25 changed at 2.5x scale) — see DEC-011 |

**Excluded from this dataset** (per DEC-011's Strategic Decision, not
deleted or hidden — see §6 below and failure-analysis.md):
`sentence_moderate_controlled_v2` ("insufficient semantic reliability
for primary dataset construction"), `paragraph_light_controlled` /
`paragraph_moderate_controlled` ("promising structural mechanism but
insufficient semantic reliability for primary dataset construction").

## 2. Proposed size (adjustable pending review)

**150 fresh family (seed) essays** — a number chosen to balance three
constraints, stated explicitly rather than picked arbitrarily:

1. **Pool availability**: PERSUADE 2.0's `Independent`-task subset has
   4,177 essays in this project's eligible word-count range
   (150–320 words). 80 have already been used across every prior
   generation experiment (EXP-DATA-001 through R3) and must be excluded
   from this pool — see §3 — leaving 4,097 available. 150 is a small
   fraction of that (3.7%), leaving ample headroom for later dataset
   revisions or a held-out generalization set without re-touching this
   pool.
2. **Generation throughput**: each family requires 2 generation calls
   (`full_ai` + `sentence_light_controlled_v2`; `human` is free) on
   Qwen2.5-1.5B-Instruct, CPU-bound. Observed throughput from
   EXP-DATA-001-R2/R3 (comparable per-call cost) is roughly 1–2 minutes
   per call. 150 families × 2 calls ≈ 300 calls ≈ 5–10 hours of
   generation wall-clock time — a real, bounded cost, not
   "thousands of samples."
3. **Manual semantic-review capacity**: every `sentence_light_controlled_v2`
   sample requires mandatory human semantic review (DEC-011's Strategic
   Decision) by the single reviewer this pipeline currently has (see
   §5, and the standing "one reviewer, no inter-rater reliability"
   limitation). EXP-DATA-001-R3 reviewed 25 sentence-level samples in
   one session; 150 is a 6x increase in review volume for this
   category alone — large but tractable across a few sessions, not an
   unreviewable firehose. `full_ai` samples do not require semantic
   review (there is no "original" to preserve against — see §5).

150 is a **proposal**, not a constraint of the tooling — the same
scripts support any N. If review determines a different size is more
appropriate (smaller for a faster first pass, larger for a more
statistically robust benchmark), only `N_SEEDS` and the exclusion set
change.

### Expected output composition (based on observed rates, not guaranteed)

| | Generated | Expected after QC + semantic review |
|---|---|---|
| `human` | 150 | 150 (no generation, no attrition) |
| `full_ai` (`machine`) | 150 | ~150 (EXP-DATA-001 saw 0 real QC failures; some small attrition possible on fresh seeds, not assumed to be exactly 0) |
| `sentence_light_controlled_v2` (`ai_assisted`) | 150 | **~132 (88%) enter the high-confidence dataset as `preserved`**; ~12 (8%) questionable and ~6 (4%) changed are set aside — see §7, not discarded |

**These are projections from EXP-DATA-001-R3's observed rates (88%/8%/4%
on n=25), not promises.** The actual post-review counts will be
reported honestly once the review is done, exactly as every prior round
in this project has been reported — including if the rate differs from
this projection, the same way EXP-DATA-001-R3's paragraph batch showed
real, disclosed variance from EXP-DATA-001-R2's.

## 3. Family construction

Unchanged from the methodology already validated across five prior
experiments (generation-methodology.md §1, DEC-011): each human seed
essay `S` is one **family**. Every sample derived from `S` —
`S` itself, `S.full_ai`, `S.sentence_light_controlled_v2` — shares
`family_id = S.id`.

**Seed pool**: `load_candidate_records()` filtered to `task ==
"Independent"`, word count in `[150, 320]`, minus the 80 seed IDs
already used across EXP-DATA-001 / R1 / R1-confirmation / R2-paragraph /
R2-sentence / R3-sentence-light / R3-paragraph-claim-survival (exact ID
list maintained the same way as every prior round's `EXCLUDED_SEED_IDS`
— hardcoded, asserted, never silently recomputed). This keeps the
primary dataset's essays disjoint from every essay this project's
methodology decisions were validated against, avoiding any risk that
the dataset is subtly shaped by which essays were repeatedly
hand-reviewed during methodology development.

`select_seed_essays()` (existing, unchanged) applies the same
`min_sentences=5, min_paragraphs=2` filters used throughout, so every
seed is structurally eligible for both `full_ai`'s length-matching and
`sentence_light_controlled_v2`'s span-selection.

## 4. Split assignment (leakage-safe, family-level)

Unchanged hard invariant (DEC-011 §"Leakage invariant", already
enforced and tested throughout): **split assignment happens at the
family level, before any generation** — `assign_family_splits()`
(existing, default ratios 70/15/15) assigns each of the 150 seed IDs to
train/validation/test **first**; every sample later derived from a seed
inherits that seed's split. A seed essay and all its derived samples
(human original, full_ai, sentence-light) always land in the same
split — never split across train and test.

Proposed ratios: **70% train / 15% validation / 15% test** at the
family level (105 / ~22 / ~23 families) — the existing default, used
without modification since no evidence from this project's experiments
suggests a different ratio is needed at this stage. Revisit if Phase 6
(scoring/calibration) or Phase 10 (evaluation) surfaces a specific need
for a different split shape (e.g. a larger held-out test set for a
generalization claim).

## 5. Semantic-review protocol (mandatory, not sampled)

Per DEC-011's Strategic Decision and the review's explicit instruction
("human review is the final label authority"):

```
Automated screening (DEC-012)
        |
        v
risk triage (prioritizes review order, does not decide)
        |
        v
human semantic review (generation-methodology.md Section 12 protocol)
        |
        v
final ground truth (semantic_preservation field)
```

- **`sentence_light_controlled_v2`**: **every** generated sample gets
  full manual review against the documented drift protocol (numbers,
  entities, causal relationships, position, claims added/removed,
  severity/degree, agent, specific-experience swaps = drift; style or
  grammar alone = not drift) — not a sample, not a subset triaged by
  the automated screen. The DEC-012 screen's `automated_screen_label`
  is still computed and stored (useful for prioritizing review order and
  as a documented data point), but it never substitutes for review, and
  a `likely_preserved` label does not exempt a sample from review. This
  is a direct, deliberate response to EXP-DATA-001-R3's finding that the
  screen can miss real drift (2/3 changed paragraph samples this round)
  — the same risk applies in principle to sentence-level samples even
  though it wasn't observed there this round.
- **`full_ai`**: no semantic-preservation review — there is no "original
  span" a full generation is supposed to preserve. Structural QC
  (`check_instruction_leakage`, `check_ai_self_reference`, length
  budget, near-duplicate scoping) is the complete quality gate for this
  category, consistent with EXP-DATA-001's validated treatment of it.
- **`human`**: no review needed — unmodified source text.

Only samples with `semantic_preservation == "preserved"` enter the
high-confidence primary dataset in the `ai_assisted` category. This is
stated as a hard rule, not a guideline: **`"questionable"` and
`"changed"` samples are excluded from the primary dataset's positive
ground truth, full stop** — see §7.

## 6. Deduplication

Reuses `near_duplicate_pairs_scoped()` (existing, family-aware,
validated across every prior round — 0 cross-family false positives to
date): run across the full generated batch after generation, separating
`cross_family` (a real anomaly — two different seed essays producing
suspiciously similar output, would need investigation before inclusion)
from `same_family` (expected and informational — a sample is naturally
similar to its own human original by construction, never treated as
suspicious).

## 7. Rejected/questionable-sample handling

Per explicit instruction, **nothing generated is discarded**. Proposed
structure:

- `data/generated/PRIMARY-DATASET-v1/samples.jsonl` — the full, raw
  output of generation (all categories, all QC/review outcomes),
  exactly like every prior experiment's `samples.jsonl`. This is the
  single source of truth; nothing is deleted from it.
- `data/generated/PRIMARY-DATASET-v1/included_ids.json` (or equivalent
  manifest) — the exact `sample_id`s that meet the inclusion bar
  (`human` + `machine` that passed QC + `ai_assisted` judged
  `preserved`) — this is what a detector-training script would actually
  load as ground truth, computed as a filter over the full samples file,
  not a separate hand-copied dataset that can drift out of sync.
- **Rejected/questionable samples remain in the same `samples.jsonl`**,
  fully tagged with their `semantic_preservation`, `qc_status`,
  `automated_screen_*`, and `claim_survival_*` fields intact — available
  for failure analysis (extending `failure-analysis.md`'s existing
  pattern) and for a possible future "hard negative" or "known-ambiguous"
  evaluation set, but **never loaded as positive high-confidence
  ground truth** by the manifest above.

## 8. Train/validation/test separation — what this guarantees

Because split assignment happens at the family level before generation
(§4), and every derived sample inherits its seed's split:

- No seed essay's `human`, `full_ai`, or `sentence_light_controlled_v2`
  sample can appear in more than one split.
- A detector trained on `train` and evaluated on `test` never sees any
  text derived from a `test`-split essay during training, at any
  transformation level — the leakage invariant DEC-011 established and
  every prior experiment has verified programmatically (0 violations to
  date) continues to apply unchanged.

## 9. What this plan does not decide

Explicitly out of scope for this document, per the instruction to design
only what's needed to move to dataset construction, not further:

- Detector architecture, features, or training procedure (Phase 6+).
- Whether/how to incorporate ELLIPSE (fairness corpus, DEC-009) into
  this specific primary dataset vs. a separate fairness-evaluation set —
  not addressed here, deferred.
- Whether a future dataset revision adds `sentence_moderate_controlled_v2`
  or paragraph-level categories once their reliability issues are
  addressed (DEC-011's redesign candidates, DEC-012's NLI candidate) —
  those remain future work, not part of this plan.
- The exact 150 seed IDs and their split assignment — these are
  computed deterministically by the existing scripts once N and the
  RNG seed are fixed, not hand-picked, and are not generated until
  explicitly authorized.
