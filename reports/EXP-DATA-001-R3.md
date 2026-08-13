# EXP-DATA-001-R3 — Sentence-Light Larger Confirmation + Paragraph Claim-Survival Validation

**Date**: 2026-08-13
**Status**: Data-generation-pipeline validation. No detector training,
evaluation, or scaling occurred or is implied by this report.

## What this round changed, and why

Per the EXP-DATA-001-R2 review's approval with three separate next
steps, this round ran exactly two new experiments, kept strictly
separate, plus one design-only task:

1. **Sentence-light larger confirmation** — `sentence_light_controlled_v2`
   was the single most promising sub-mechanism found so far (R2: 9/10
   preserved, 0/10 changed on 10 seeds). This experiment asks only
   whether that holds on a larger, fresh sample (25 seeds), with every
   other variable (model, revision, temperature, context format,
   span-selection, QC, screen) held identical to R2.
2. **Paragraph claim-survival validation** — R2 found paragraph-level
   rewrites can drop a claim while passing length-ratio QC. This
   experiment adds a new screening layer (DEC-013) targeting exactly
   that failure mode, and validates it on 12 fresh seeds using the
   SAME, unchanged paragraph generation mechanism as R2 (no redesign).
3. **Sentence-moderate: design only** — three candidate replacement
   instructions were drafted (`scripts/sentence_moderate_redesign_candidates.py`),
   none tested, no winner chosen. No new generation was run for this
   category in R3.

EXP-DATA-001, R1, R1-confirmation, and R2's sample files and reports
remain untouched, per explicit instruction.

---

## A. Sentence-light larger confirmation

25 fresh PERSUADE seeds (excluding all 43 seed IDs used across every
prior generation experiment), `human` + `sentence_light_controlled_v2`
only = 50 records. Same model (Qwen2.5-1.5B-Instruct), same revision,
same temperature (0.6) / top_p (0.95), same
`generate_sentence_transform_with_paragraph_context` mechanism, same QC,
same DEC-012 screen as EXP-DATA-001-R2.

**Structural QC**: 23/25 (92%) passed cleanly. 2/25 flagged by
`modification_scope_drift` — both later judged `preserved` on manual
review. One of the two flags is a genuine, disclosed segmentation-
interaction artifact: a sentence segmenter edge case bundled a letter
salutation ("Dear Principal,") into the first "sentence" (no
terminating punctuation after the salutation), and the model's light
edit of the opinion clause dropped the salutation, shrinking the span
enough to trip the length-ratio check (see failure-analysis.md
Failure 10).

**Semantic preservation (manual review, all 25 reviewed)**:

| | preserved | questionable | changed |
|---|---|---|---|
| n | 22 (88%) | 2 (8%) | 1 (4%) |

The one `"changed"` sample (`F18ABB1A8920`) is a numeric substitution —
the essay's stated C-average threshold changed from "70 or above" to
"80 or above" in the rewrite — the same failure class as the "one C"/
"two Cs" case from EXP-DATA-001-R1-confirmation. It was correctly caught
by the DEC-012 screen (`needs_review`, fact-check flagged the 70/80
mismatch).

The two `"questionable"` samples: one softened an unconditional causal
claim into a conditional one ("could lower your average" →
"could lower your average **if it significantly impacts your
performance**"); the other made an implicit claim explicit (arguably
inferable from paragraph context, but not stated in the target sentence
itself). Neither is a clear number/entity/position change; both are
flagged for visibility, not treated as confirmed drift.

**Conclusion**: the promising EXP-DATA-001-R2 result (9/10 preserved,
0/10 changed) holds at ~2.5x the sample size, with a small, real,
non-zero drift rate now visible that the smaller sample didn't surface
(4% vs. the earlier apparent 0%). This is a *more* trustworthy number
than R2's, not a worse one — larger samples are expected to surface rare
failure modes a smaller sample misses.

---

## B. Paragraph claim-survival validation

12 fresh PERSUADE seeds (excluding all 68 seed IDs used across every
prior generation experiment, including this round's own sentence-light
batch), `human` + `paragraph_light_controlled` + `paragraph_moderate_controlled`
= 36 records. **Unchanged generation mechanism** — same instructions,
same temperatures (light 0.5 / moderate 0.7) as EXP-DATA-001-R2-paragraph
— this experiment tests the new DEC-013 screening layer against fresh
data, not a redesigned mechanism.

**Structural QC**: light 11/12 passed (1 flagged,
`modification_scope_drift`); moderate 12/12 passed.

**Semantic preservation (manual review, all 24 reviewed), light and
moderate reported separately**:

| | preserved | questionable | changed |
|---|---|---|---|
| light (n=12) | 9 (75%) | 1 (8%) | 2 (17%) |
| moderate (n=12) | 8 (67%) | 3 (25%) | 1 (8%) |

Compared to EXP-DATA-001-R2's paragraph batch (72% preserved combined),
this round's raw preservation rate is similar-to-slightly-lower, but the
more important finding is qualitative: **the 3 `"changed"` samples this
round include two failure types not previously seen this clearly** —

- **Stated-priority reversal** (`1F8012FFBEBE`, light): the original
  says students "don't really care [about tutoring] because we don't
  want to lose our sport" (motivated by *keeping* their sport
  privilege); the rewrite says "We don't mind losing our sport; it's
  more important that we maintain our academic focus" — the *opposite*
  stated priority. Notably, the **moderate** rewrite of the same
  original paragraph got this right (correctly preserved the
  sport-motivated framing) — the light rewrite is the one that inverted
  it, a useful reminder that "moderate" is not uniformly worse than
  "light" for every failure type.
- **Claim drop merged with a location/mechanism flip**
  (`62AA2FDC41C6`, light): a standalone "more focused" claim
  disappears, and a separate claim about texting "AT school" preventing
  sleepiness becomes a garbled claim about access "OUTSIDE of school"
  reducing distraction — two distinct claims compressed into one
  confused sentence.
- **Narrator-identity swap** (`80664125F8D0`, moderate): the rewrite
  opens "As a teacher, I support..." then continues in a way that only
  makes sense if the narrator is a student ("I'm receiving a C in two of
  my classes, which means I won't be eligible to try out for the sports
  I wish to join") — internally incoherent, the model lost track of who
  is speaking (see failure-analysis.md Failure 11).

**A real extraction bug was found and fixed mid-review** (see DEC-012's
"Known Issue" and DEC-013's docstring): the helper that reconstructs
`(original, rewritten)` text pairs for screening initially mis-extracted
one sample (`7AF7BFC4BF8D`) as a severe, nearly-total omission — that
read was an artifact of the extraction, not the actual generated text.
After fixing the extraction (twice — first for `modified_spans`
truncation on sentence merges, then again for the model's own output
containing blank-line breaks), `7AF7BFC4BF8D`'s light rewrite was
correctly re-judged `preserved` and its moderate rewrite `questionable`
(a specific-experience swap: a "homeless student" example replaced with
a "family instability" example). This correction is recorded
transparently because it demonstrates why re-verifying automated
extraction matters before trusting conclusions built on top of it — see
§D and §E below for what this means for the automated screens
specifically.

**Conclusion**: paragraph-level claim-survival validation did not
improve confidence in the paragraph mechanism — it added evidence of a
failure type (meaning reversal) the mechanism can produce that neither
automated screen catches. See §D and §F.

---

## C. Moderate-sentence instruction alternatives

No new generation was run for `sentence_moderate_controlled_v2` this
round, per explicit instruction. Three candidate replacement
instructions were designed and documented in
`scripts/sentence_moderate_redesign_candidates.py` and DEC-011:

- **M1 (explicit checklist)**: replaces the current instruction's only
  preservation language — "preserving its meaning," vague and abstract
  — with an itemized checklist naming exactly what must not change
  (numbers/quantities, named entities, who-did-what, causal
  relationships, stated position/conclusion), while explicitly granting
  MORE stylistic restructuring latitude than the light instruction.
- **M2 (checklist + silent self-check)**: M1 plus an instruction to
  verify, before answering, that the same facts/numbers/names/conclusion
  are present — still returns only the final sentence, no visible
  reasoning.
- **M3 (checklist + negative example)**: M1 plus a concrete, generic
  example grounded in this project's own observed failures ("do not
  change 'at least one' to 'at least two'; do not replace a specific
  reason with a generic one").

**No winner was chosen** — per explicit instruction not to select based
on pass-rate against existing samples without new data. A future,
explicitly authorized experiment should test these against fresh seeds
under the same experimental-independence discipline already established
(same model/revision/temperature/context/span-selection/QC/screen,
varying only instruction wording).

---

## D. DEC-012 (and DEC-013) automated-screen behavior

**Sentence-light-R3 (25 samples)**: 20 `likely_preserved`, 5
`needs_review`, 0 `likely_changed`. The 1 real `"changed"` sample was
correctly flagged `needs_review` (0/1 changed mislabeled
`likely_preserved` — safety property held).

**Paragraph claim-survival-R3 (24 samples)**: DEC-012 screen — 14
`likely_preserved`, 10 `needs_review`. DEC-013 (claim-survival) screen —
16 `no_omission_signal`, 8 `possible_omission_flagged`.

**The safety property broke for the first time, on this batch**: of the
3 real `"changed"` paragraph samples, **2 were labeled `likely_preserved`
by DEC-012 and `no_omission_signal` by DEC-013** — the stated-priority
reversal (`1F8012FFBEBE` light) and the claim-drop-plus-location-flip
(`62AA2FDC41C6` light). Both score high embedding similarity and touch
no number/entity, so neither screen had anything to catch. The third
`"changed"` sample (`80664125F8D0` moderate, the narrator-identity swap)
*was* flagged by both screens — but for an unrelated, coincidental
reason (a fact-check false positive on date/frequency phrasing, "every
two days"/"this years"), not because either screen detected the
identity swap itself.

**What this confirms, precisely**: the safety property ("0 changed
mislabeled preserved") has now held across three separate validation
rounds (calibration: 0/8; R2 out-of-sample: 0/5; R3 sentence-light: 0/1)
for **numeric/entity substitution** specifically. It has never been
tested against — and has now failed on — **meaning reversal and
multi-claim compression**, which is exactly the theoretical gap DEC-012
named when it was written ("a claim change that alters no number or
named entity... not observed in this calibration set, but not proven
absent either"). NLI (DEC-012's previously-deferred Alternative B) is
now a live candidate for closing this gap; not implemented this round.

DEC-013's claim-survival screen did correctly catch one genuine claim
drop (`62AA2FDC41C6` moderate, `dropped_sentences=1`, matching manual
review exactly) — its intended failure mode. It has no mechanism for
reversal or merge-type drift, which is a different failure mode than the
one it was designed for.

---

## E. Remaining failure modes

- **Meaning reversal without a number/entity change** (new this round,
  paragraph-level) — not caught by either automated screen. The single
  most important open gap.
- **Multi-claim compression/garbling** (new this round, paragraph-level)
  — a model merging two original claims into one confused sentence can
  evade coverage-based detection because the merged sentence still
  shares enough vocabulary with both originals.
- **Narrator/persona identity drift under `moderate` instructions**
  (new this round, paragraph-level, single occurrence) — not
  investigated further, flagged for future attention if it recurs.
- **Sentence-moderate semantic drift** (carried over from R1-confirmation
  and R2, unchanged this round since no new moderate data was generated)
  — redesign drafted, not tested.
- **Sentence segmenter + salutation interaction** (new this round,
  sentence-level) — a correctly-caught QC edge case, not a silent
  failure, but worth tracking if letter-style essays are common at
  scale.
- **Fact-check false-positive rate on temporal phrasing** — confirmed
  again this round (e.g. "every two days"/"this years" mismatches);
  inflates `needs_review`/`possible_omission_flagged` rates without
  indicating real drift.
- **Two real extraction bugs found and fixed this round** in shared
  screening infrastructure (`extract_span_pair`) — both now fixed for
  future rounds; EXP-DATA-001-R2's frozen paragraph-level screen numbers
  predate the fix and should be read with that caveat (not retroactively
  recomputed).
- **Human review remains single-reviewer**, no inter-rater reliability
  figure exists across any round.

---

## F. Is each category ready for scale?

**Not combined into a single number — reported per category, as
instructed.**

- **`sentence_light_controlled_v2`**: **The strongest evidence of any
  single sub-mechanism in this project so far** — 88% preserved, 4%
  changed at n=25, with the one real drift case correctly caught by the
  DEC-012 screen. Promising enough to warrant continued confidence, but
  "ready for scale" is a decision for review, not a claim this report
  makes unilaterally — n=25 is still short of what a final dataset would
  need, and this project's discipline has consistently avoided declaring
  readiness without an explicit review checkpoint.
- **`sentence_moderate_controlled_v2`**: **Not ready.** Unchanged status
  from R2 (33% changed on the last tested batch) — no new data this
  round by design. Three redesign candidates drafted, untested.
- **`paragraph_light_controlled` / `paragraph_moderate_controlled`**:
  **Not ready, and this round's evidence is stronger against readiness,
  not weaker.** Raw preservation rates (75%/67%) are in the same range as
  R2, but this round surfaced a failure type (meaning reversal) that
  R2's 4/12 "passed but changed" finding at the sentence level already
  established as a real category of problem — now confirmed at the
  paragraph level too, and confirmed to evade both current automated
  screens. A reversal-sensitive signal (NLI) does not yet exist for this
  pipeline.

---

## Explicit non-findings

- This report makes no claim about detector accuracy, F1, or
  generalization — no detector exists.
- No success threshold was invented before observing results, for
  either experiment.
- The sentence-moderate redesign candidates are untested; none is
  recommended over another without data.
- `sentence_light_controlled_v2`'s n=25 result is evidence of promise,
  not a declaration of production-readiness — that determination is
  reserved for explicit review.
