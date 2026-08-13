# EXP-DATA-001-R2 — Semantic-Preservation Gate Design + Validation

> Status: **executed for real**, 2026-08-13. Two separate, parallel
> experiments, kept apart per instruction: paragraph-level re-validation
> on fresh seeds (unchanged mechanism) and sentence-level validation of a
> redesigned mechanism (paragraph context + controlled temperature +
> automated semantic screen). This report evaluates the **data
> generation pipeline only**. No detector was trained, run, or evaluated.
> No detection accuracy/precision/recall/F1 is reported or implied
> anywhere below. Prior findings
> ([EXP-DATA-001](EXP-DATA-001.md), [EXP-DATA-001-R1](EXP-DATA-001-R1.md),
> [EXP-DATA-001-R1-confirmation](EXP-DATA-001-R1-confirmation.md)) are
> preserved, not overwritten.

## What this round changed, and why

1. **Semantic-preservation gate designed** ([DEC-012](../docs/decisions/DEC-012-semantic-preservation-screen.md)):
   embedding similarity (`sentence-transformers`/`all-MiniLM-L6-v2`) +
   entity/number preservation check (spaCy), combined so a fact-check
   flag always escalates to review regardless of similarity. Thresholds
   calibrated against the 35 already-reviewed
   EXP-DATA-001-R1-confirmation samples with resolvable spans — not
   invented. This is a **screen**, not ground truth: human review remains
   authoritative.
2. **Sentence-level context redesign**: the model now sees the **full
   paragraph** containing the target sentence (not just one sentence
   before/after), explicitly instructed to modify only the target
   sentence. Splice mechanism and ground-truth guarantee unchanged.
3. **Confound removed**: temperature and top_p are now **identical**
   between light and moderate (0.6 / 0.95 both), closing the gap that
   made EXP-DATA-001-R1-confirmation's light-vs-moderate comparison
   uninterpretable (that round used 0.5 for light, 0.7 for moderate).
4. **Regime C untouched**, not retested — out of scope per instruction.

## 1. Paragraph-level results (fresh seeds, unchanged mechanism)

10 fresh seeds (excluded: all 23 seeds from every prior experiment),
`paragraph_light_controlled` + `paragraph_moderate_controlled` = 20
generated + 10 human = 30 records.

| Metric | Light | Moderate |
|---|---|---|
| QC passed | 9/10 | 9/10 |
| Resegmentation OK | 9/10 | 9/10 |
| Length ratio range | 0.86–1.33 | 0.81–1.56 |
| Semantic: preserved | 7/9 reviewed | 6/9 reviewed |
| Semantic: questionable | 1/9 | 2/9 |
| Semantic: changed | 1/9 | 1/9 |
| Cross-family duplicates | 0 | 0 |
| Leakage/self-reference | 0 | 0 |

**Combined semantic preservation: 13/18 preserved (72%), 3/18
questionable (17%), 2/18 changed (11%).** Lower than
EXP-DATA-001-R1-confirmation's paragraph result (90% preserved) on this
fresh sample — real, honest variance across different seed essays, not a
regression in the mechanism (unchanged from that round). Both `changed`
samples (same seed, `DB12BA4206B8`, both light and moderate) dropped the
paragraph's opening claim/framing entirely while preserving the rest —
a real content-omission failure mode, not previously seen this clearly.

## 2. Sentence-level results (fresh seeds, context + controlled temp)

10 different fresh seeds (excluded: the same 23 plus the 10 used above —
33 total), `sentence_light_controlled_v2` + `sentence_moderate_controlled_v2`
= 20 generated + 10 human = 30 records.

| Metric | Light | Moderate |
|---|---|---|
| QC passed | 9/10 | 9/10 |
| Resegmentation OK | 10/10 | 9/10 |
| Length ratio range | 0.65–1.05 | 0.58–1.96 |
| Semantic: preserved | 9/10 reviewed | 6/9 reviewed |
| Semantic: questionable | 1/10 | 0/9 |
| Semantic: changed | 0/10 | 3/9 |
| Cross-family duplicates | 0 | 0 |
| Leakage/self-reference | 0 | 0 |

**Combined semantic preservation: 15/19 preserved (79%), 1/19
questionable (5%), 3/19 changed (16%).** A dramatic improvement over
EXP-DATA-001-R1-confirmation's sentence-level result (33% preserved, 47%
changed) on the *previous* mechanism. See Section 6 for why this can't
be attributed to context alone with full certainty, and Section 7 for
the light-vs-moderate breakdown specifically.

## 3. Semantic-drift findings

**Structural QC also improved sharply**, not just semantic preservation:
resegmentation success went from 7/10 and 8/10 (confirmation round) to
10/10 and 9/10 (this round) for light/moderate respectively. More context
appears to help the model produce output that fits back into the
original sentence structure, not just output that means the same thing.

**Drift patterns actually observed this round** (mapped to the
[protocol](../docs/generation-methodology.md#12-semantic-preservation-review-protocol)):
- **Introducing claims not in the original**: sentence-moderate
  `1DD5B206DC55` turned a descriptive observation ("everyone sees things
  differently") into prescriptive advice about achieving objectives.
- **Complete topic substitution**: sentence-moderate `2221985D49BD`
  replaced a sentence about emotional support with one about online
  learning platforms — no relationship to the original.
- **Reversing who an action concerns**: sentence-moderate `6641EA903719`
  flipped a complaint from "principal shouldn't assign all students" to
  "peers disagree only the principal should be assigned" — a real
  causal/agent reversal.
- **Claim omission at paragraph level**: `DB12BA4206B8` (both light and
  moderate) dropped an opening rhetorical claim entirely while keeping
  the rest — the first clean example of *paragraph*-level claim removal
  observed in this project's experiments so far.
- **Specificity loss** (questionable, not full drift): `BCEF4D5FF6AB`
  genericized "B average" to "average performance," losing a concrete
  grade reference.

## 4. Automated semantic-screen behavior

Across both batches combined (37 screened samples: 19 sentence + 18
paragraph):

**Safety property held on fresh, out-of-sample data**: **0 of 5** samples
manually judged `"changed"` were labeled `likely_preserved` by the screen
(3 sentence, 2 paragraph) — consistent with the calibration set's 0/8.
This is the property the screen exists to guarantee, and it replicated
on data it wasn't calibrated on.

**Known limitation confirmed, not newly discovered**: 2 of 4
`"questionable"` samples this round were labeled `likely_preserved`
(`E83EAE114F13` sentence-light, `BCEF4D5FF6AB` paragraph-moderate) —
consistent with DEC-012's documented gap. The screen does not reliably
catch subtle framing/specificity shifts, only either gross topic
divergence (low embedding similarity) or number/entity substitution
(fact-check).

**Conservative as designed**: many `"preserved"` samples were still
labeled `needs_review` rather than `likely_preserved` (e.g. 6 of 10
sentence-light `preserved` samples) — the screen reduces but does not
eliminate review workload, exactly as documented in DEC-012.

## 5. Human-review findings

Review followed the documented protocol
([generation-methodology.md §12](../docs/generation-methodology.md#12-semantic-preservation-review-protocol))
directly — meaning categories (numbers/entities/causal relationships/
position/claims/severity/agent/experience) vs. non-drift (style,
grammar). One reviewer (the agent operating this pipeline), same
limitation as prior rounds: **no independent second rater**, no
inter-rater reliability figure. This remains a real limitation of the
review's rigor, not resolved by this round.

## 6. Effect of additional context

**Cannot be isolated as the sole cause of the improvement** — this
round changed context *and* fixed the temperature confound
simultaneously relative to EXP-DATA-001-R1-confirmation. What can be
said: the improvement is large (33%→79% sentence-level preservation,
7/10→10/10 and 8/10→9/10 resegmentation success) and consistent across
both structural and semantic measures, which is more than a temperature
change alone would plausibly explain (temperature affects sampling
randomness, not systematically whether the model edits sentences it was
told not to touch). The most defensible claim: **context is very likely
a major contributor, but a clean isolation experiment (same temperature,
context varied alone) has not been run and would be needed to state this
with full confidence.**

## 7. Controlled light-vs-moderate comparison

With temperature/top_p/context/QC held constant, a real, direct
difference emerged: **sentence-level `moderate` produced 3× the
semantic-drift rate of `light`** (3/9 vs 0/10 changed). This is the
opposite pattern from EXP-DATA-001-R1-confirmation (where `light` had
*more* structural failures) and, with the confound now removed, points
to a genuine property of the instructions themselves: "moderately
reword... for clarity and flow" appears to license more substantive
rewriting than "lightly copy-edit," and that latitude is what produces
drift, not an artifact of sampling temperature. Paragraph-level showed a
smaller, less clear-cut version of the same pattern (1/9 vs 1/9 changed,
1/9 vs 2/9 questionable — moderate slightly worse but not dramatically).

## 8. Remaining failure modes

- Sentence-moderate can still substitute an entirely different claim or
  reverse who an action concerns, even with full paragraph context and
  an explicit "modify only this sentence" instruction.
- Paragraph-level can drop an entire sub-claim while otherwise reading as
  a faithful paraphrase — a failure mode structural QC (length ratio) does
  not catch, since dropping one sentence's claim while expanding wording
  elsewhere can still land inside the length-ratio bounds.
- The automated screen still has a documented blind spot for subtle
  framing/specificity shifts (`questionable`-tier drift).
- One sentence-moderate sample was still rejected by structural QC
  (`modification_scope_drift` + `splice_resegmentation_mismatch`) even
  with the redesigned mechanism — the failure rate dropped, not to zero.

## 9. Is paragraph-level generation ready for scale?

**Not yet — still promising, but this round's fresh sample (72%
preserved) is materially lower than the first batch's (90%), which is
exactly why "requires further validation" rather than "ready" is the
right call.** The claim-omission failure mode (Section 3) is new,
concrete evidence to design around before scaling — e.g., a check for
whether major claims/entities from the original paragraph survive
somewhere in the rewrite, not just an overall length/similarity check.

## 10. Is sentence-level generation ready for scale?

**Not as a single uniform category — but the evidence now supports a
split recommendation between light and moderate specifically**:
- `sentence_light_controlled_v2`: 9/10 preserved, 0/10 changed. This
  specific configuration (paragraph context, light instruction, temp
  0.6) looks close to ready for a further, larger validation round.
- `sentence_moderate_controlled_v2`: 6/9 preserved, 3/9 changed (33%).
  Still not ready — the moderate instruction itself, not temperature or
  context, now looks like the primary driver of remaining drift (Section
  7), which suggests the next fix is instruction redesign for this
  specific category, not more context or more QC.

## Explicit non-findings

No detector was involved in producing or judging any sample. No
detection accuracy, precision, recall, or generalization claim is made.
Neither the paragraph-level nor sentence-level mechanism is declared
production-ready by this report.
